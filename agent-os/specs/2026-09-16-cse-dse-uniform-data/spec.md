# Feature Specification: CSE/DSE Uniform Data

**Status:** Implemented (2026-09-16); see `tasks.md` session notes

## Overview

### Objective
Make every CSE result returned by `stocksurferbd` (price history, current
prices, day-end, index data) come back in exactly the DSE shape, so a platform
already built on the DSE format consumes CSE data without any branching.

### Background
See `planning/raw-idea.md` and the gap analysis in `planning/requirements.md`.
The user's application consumes the DSE format today; that format is therefore
canonical and must not change. CSE currently:

- sources history from a 6-month chart endpoint whose third OHLC field is the
  *previous close*, which the parser writes to `OPENP` (verified 115/115 rows);
- writes `LTP`, `YCP`, `% CHANGE`, `TRADE`, `VALUE_MN` as literal zeros;
- names the live open `OPEN`, lacks `CLOSEP`/`% CHANGE`, and stamps `DATE`
  from the machine clock;
- raises for `get_day_end_df` and every `IndexData` method.

### CSE sources verified on 2026-09-16

| Endpoint | Method | Returns | Use |
|----------|--------|---------|-----|
| `market/data_download_company` | POST `from,to,csrf_cse_token` | xlsx: `trade_date, company_name, company_code, no_of_trades, volume, turnover, prev_close_price, close_price, open_price, last_traded_price, day_high, day_low`; all symbols; data from **2015-11-24** (gaps before mid-2018); 1 year = ~95k rows, 4.3 MB, ~21 s | **history, day-end, CLOSEP/DATE for current** |
| `market/current_price` | GET | HTML `#dataTable`: `STOCK CODE, LTP, OPEN, HIGH, LOW, YCP, TRADE, VALUE(MN), VOLUME`; no date | live current prices |
| `company/companydetails/<code>` | GET | "Last Trade Date"/"Updated Date" label + LTP/Open/Close/Prev Close | fallback trading date |
| `home/load__index_summary/` | POST `selected_index,csrf_cse_token` | JSON `{value, change, percentage_change}` for CASPI, CSE30, CSCX, CSE50, CSI | current indices |
| `market/data_download_index` | POST `from,to,csrf_cse_token` | xlsx: `trade_date, <idx>_value/_change/_percentage_change x5, turnover, volume, no_of_trades, market_capital, no_of_gainer, no_of_losser` | index history |
| `market/close_price` (Export) | POST | xlsx: closing price only, per symbol, 6 years | not used (no OHLCV) |
| `market/marketprice` | POST | HTML: volume/close/turnover/trades, keyword prefix match | not used |

Every POST needs the `csrf_cse_token` hidden field from the page plus the
session cookie and a `Referer`.

### Scope
- **In Scope**: `PriceData` (history, current, day-end) and `IndexData`
  (current snapshot, day-wise history) for `market='CSE'`; CSRF-aware POST
  helper in `HttpScraper`; offline fixtures and tests; README schema tables;
  `fetch_csebd_data.py` fix; version bump to 2.0.0.
- **Out of Scope**: `FundamentalData` / `BlockTradeData` for CSE; CSE intraday
  ticks and per-index graph history; SME/ATB/G-Sec boards; sector indices;
  any change to DSE output; a `MARKET` column.

---

## User Stories

| ID | As a... | I want to... | So that... |
|----|---------|--------------|------------|
| US-1 | Platform developer | call `get_price_history_df(sym, market='CSE')` and get the DSE columns with real values | my DSE ingestion code works for CSE unchanged |
| US-2 | Platform developer | call `get_current_price_df(market='CSE')` and get the DSE current-price columns | both markets load into one table |
| US-3 | Platform developer | call `get_day_end_df(date, market='CSE')` | I can backfill all CSE symbols per day like DSE |
| US-4 | Platform developer | pass a multi-year `start_date`/`end_date` for CSE | I am not silently capped at 6 months |
| US-5 | Platform developer | call `IndexData` methods with `market='CSE'` | index dashboards work for both exchanges |
| US-6 | Existing DSE user | see no change in DSE output or file layout | my application keeps working |

---

## Technical Design

### Architecture Overview
```
Public surface (identical frames for both markets):
  get_price_history_df(sym, market, start, end)     per symbol            (existing)
  get_day_end_df(date, market)                       all symbols, one day  (existing; CSE added)
  get_day_end_range_df(start, end, market)           all symbols, range    (NEW, both markets)
  get_current_price_df(market)                       live snapshot         (existing)

CSE engine (private):
  _cse_day_end_frame(start, end)                    # all symbols, canonical columns
    ├─ for each calendar-year chunk in [start, end] (clipped to CSE_EARLIEST_DATE..today):
    │     memory cache  -> disk cache (cache_dir, closed years only) ->
    │     post_with_csrf(HISTORICAL_DATA_PAGE_CSE, DOWNLOAD_COMPANY_URL_CSE, {from,to})
    │     -> read_xlsx_bytes -> _cse_rows_to_history(df); store in caches unless chunk includes today
    │     print progress: "CSE download 2019-01-01..2019-12-31 (3/11)"
    └─ concat, sort DATE desc, TRADING_CODE asc

get_price_history_df(sym, 'CSE')       -> _cse_day_end_frame(start or CSE_EARLIEST_DATE, end or today)
                                          .query(TRADING_CODE == sym)
get_day_end_df(date, 'CSE')            -> _cse_day_end_frame(date, date)
get_day_end_range_df(start, end, 'CSE')-> _cse_day_end_frame(start, end)
get_day_end_range_df(start, end, 'DSE')-> concat(get_day_end_df(d, 'DSE') for each calendar day; empty days skipped)
PriceData.get_current_price_df(market='CSE')       -> live #dataTable rows
                                                     + CLOSEP/DATE joined from _cse_day_end_frame(today, today)
                                                     (fallback: CLOSEP = LTP, DATE from company page, then today)
IndexData.get_current_indices_df(market='CSE')     -> 5x POST load__index_summary (JSON)
IndexData.get_index_history_df(market='CSE', ...)  -> POST data_download_index (xlsx)
```

### Canonical schemas (DSE, unchanged) and dtypes
Captured from live DSE calls on 2026-09-16; CSE must reproduce them exactly.

| Method | Columns | dtypes / order |
|--------|---------|----------------|
| `get_price_history_df` / `get_day_end_df` | `DATE, TRADING_CODE, LTP, HIGH, LOW, OPENP, CLOSEP, YCP, TRADE, VALUE_MN, VOLUME` | `DATE` str `YYYY-MM-DD`, `TRADING_CODE` str, all others float64; rows **newest first** |
| `get_current_price_df` | `DATE, TRADING_CODE, LTP, HIGH, LOW, CLOSEP, YCP, % CHANGE, TRADE, VALUE_MN, VOLUME` | `DATE` `datetime.date`, `TRADING_CODE` str, others float64; rows in exchange table order (alphabetical) |
| `get_current_indices_df` | `INDEX, POINTS, CHANGE, PCT_CHANGE` | one row per index |
| `get_index_history_df` | `DATE, TOTAL_TRADE, TOTAL_VOLUME, VALUE_MN, MARKET_CAP_MN, <one column per index>` | `DATE` `datetime.date`; newest first |

Column lists become class constants (`HISTORY_COLUMNS`, `CURRENT_COLUMNS`,
`INDEX_CURRENT_COLUMNS`, `_CSE_HISTORY_COLUMNS`) and every CSE builder ends
with `pd.DataFrame(records, columns=<CONST>)` so order is enforced.

### CSE field mapping

**Day-end download -> history schema**

| CSE xlsx column | Canonical | Transform |
|-----------------|-----------|-----------|
| `trade_date` | `DATE` | `YYYY-MM-DD` string |
| `company_code` | `TRADING_CODE` | as-is |
| `last_traded_price` | `LTP` | float |
| `day_high` / `day_low` | `HIGH` / `LOW` | float |
| `open_price` | `OPENP` | float |
| `close_price` | `CLOSEP` | float |
| `prev_close_price` | `YCP` | float |
| `no_of_trades` | `TRADE` | float |
| `turnover` | `VALUE_MN` | Taka / 1e6, round 3 dp (DSE publishes 3 dp) |
| `volume` | `VOLUME` | float |
| `company_name` | dropped | not in DSE schema |

Sort: `DATE` descending, then `TRADING_CODE` ascending.

**Live `#dataTable` -> current schema**

| Source | Canonical | Transform |
|--------|-----------|-----------|
| same-day download `trade_date`; fallback company page "Last Trade Date"/"Updated Date"; last resort today | `DATE` | `datetime.date` |
| `STOCK CODE` | `TRADING_CODE` | as-is |
| `LTP`, `HIGH`, `LOW`, `YCP`, `TRADE`, `VALUE(MN)`, `VOLUME` | same names | float via `parse_float` |
| same-day download `close_price` joined on code; fallback `LTP` | `CLOSEP` | float |
| computed | `% CHANGE` | `round(LTP - YCP, 2)`. **Verified live on 2026-09-16:** despite its name, DSE's `% CHANGE` column holds the absolute change (97% of 395 rows equal `LTP - YCP`; only 13% equal a true percentage), so CSE reproduces the same quantity. |
| `OPEN` | dropped | not in DSE schema |

**Index JSON -> current indices**: one POST per index in
`CSE_INDICES = ("CASPI", "CSE30", "CSCX", "CSE50", "CSI")`;
`value -> POINTS`, `change -> CHANGE`, `percentage_change -> PCT_CHANGE`.

**Index xlsx -> index history**: `trade_date -> DATE`,
`no_of_trades -> TOTAL_TRADE` (int), `volume -> TOTAL_VOLUME` (int),
`turnover / 1e6 -> VALUE_MN`, `market_capital / 1e6 -> MARKET_CAP_MN`,
`<idx>_value -> <IDX>` for the five indices. Newest first, like DSE.

### Date handling, defaults, chunking and cache
- **CSE history with no dates returns the full archive**: `start =
  CSE_EARLIEST_DATE = '2015-11-24'`, `end = today`. DSE's ~2-year no-date
  window is a DSE server limit and is deliberately not mirrored.
- **Chunks**: calendar years, clipped to the requested range and to
  `CSE_EARLIEST_DATE..today`. One POST per chunk (~95k rows / 4.3 MB / ~21 s
  for a full year). Downloads are sequential with a one-line progress print
  per chunk; no concurrency (CSE's server is slow and untested under load).
- **Memory cache**: `self._cse_chunk_cache: dict[(from, to), DataFrame]` on
  the `PriceData` instance. Any chunk whose `to >= today` is never cached.
- **Disk cache (optional)**: new constructor argument `cache_dir=None` on
  `PriceData`. When set, each *closed* year chunk is stored as
  `<cache_dir>/cse_day_end_<from>_<to>.pkl` (pandas pickle; no new dependency; month and year chunks get distinct files) and
  loaded before any network call. Closed years are immutable on the exchange
  side, so no expiry is needed. The current year is never written to disk.
- **Cost table** (documented in README):

  | Call | Requests | Time (approx.) |
  |------|----------|----------------|
  | first CSE symbol, no dates, cold | ~11 | 3-4 min |
  | any further symbol, same instance or `cache_dir` | 0-1 (current year) | seconds |
  | explicit short range (1 month) | 1 | ~3 s |
  | `get_day_end_range_df` full archive, all symbols | ~11 | 3-4 min, once |

- `_fmt_date` already normalises inputs; reuse it. Ranges entirely before
  2015-11-24 yield an empty frame with the canonical columns.

### `get_day_end_range_df` (new, both markets)
```python
def get_day_end_range_df(self, start_date, end_date=None, market='DSE',
                         symbols=None, chunk='year', progress=True,
                         use_cache=True):
    """History schema for ALL symbols (or `symbols`) over [start_date, end_date]."""
```

| Parameter | Default | Meaning |
|-----------|---------|---------|
| `start_date` | required | inclusive lower bound (`date`/`datetime`/parseable string) |
| `end_date` | `None` -> today | inclusive upper bound |
| `market` | `'DSE'` | `'DSE'` or `'CSE'`; validated against `VALID_MARKETS` |
| `symbols` | `None` -> all | iterable of trading codes; upper-cased and stripped; applied after download (the CSE source is all-symbols, so this saves memory and a caller-side filter, not bandwidth). Ignored by DSE only in the sense that DSE still fetches every day's full table. |
| `chunk` | `'year'` | `'year'` or `'month'` download granularity for CSE. Monthly = more, smaller requests (better retries, cheaper "last 3 months"). Validated against `CSE_CHUNK_SIZES = ('year', 'month')`; ignored for DSE (always per day). Cache keys include the chunk bounds, so year and month chunks never collide. |
| `progress` | `True` | `True` -> one `print` per network chunk; `False` -> silent; callable -> called as `progress(chunk_from, chunk_to, index, total)` per network chunk (cache hits do not report). |
| `use_cache` | `True` | `False` bypasses memory and disk caches for this call and does **not** write to them (use when the exchange restated a day). |

- CSE: `_cse_day_end_frame(start, end, chunk, progress, use_cache)` (the native shape of the source).
- DSE: iterate calendar days, call `parse_day_end_dse(day)`, skip empty days
  (weekends/holidays), concat. Documented as slower on DSE (one request per
  trading day).
- `save_day_end_range_data(file_path='', file_name='day_end_range.xlsx',
  market='DSE', start_date=None, end_date=None, **kwargs)` thin wrapper writing
  one xlsx; `kwargs` are passed through (`symbols`, `chunk`, `progress`,
  `use_cache`).
- `get_price_history_df(..., market='CSE')` reuses the same engine with the
  defaults (`chunk='year'`, `progress=True`, `use_cache=True`); its signature
  is unchanged so DSE callers see nothing new.
- Batch drivers (`fetch_csebd_data.py`) use it once and split by
  `TRADING_CODE` instead of calling `save_history_data` per symbol.

### HttpScraper changes (`utils.py`)
```python
CSRF_FIELD_CSE = 'csrf_cse_token'

def post_with_csrf(self, page_url, action_url, data):
    """GET page_url, extract the CSE CSRF token, POST data to action_url.

    Reuses self.session (cookie), sets Referer, honours verify/timeout.
    Raises ParseError if the token is absent, FetchError on HTTP failure.
    """
```
Also introduce the small exception hierarchy the standards call for
(`StockSurferError`, `FetchError`, `ParseError`) in `utils.py`; existing
`IOError`/`Exception` raises elsewhere are left as-is in this feature.

### Error handling
- Non-xlsx content type from a download endpoint -> `ParseError` with the
  first 200 chars of the body.
- Empty xlsx for a valid range -> empty DataFrame with canonical columns
  (matches DSE `get_day_end_df` on a non-trading day).
- Live table missing (`#dataTable` absent) -> `ParseError`.
- Unknown market -> existing `IOError('Invalid Stock Market! ...')`, now
  checked against `VALID_MARKETS`.

### Files touched
| File | Change |
|------|--------|
| `stocksurferbd_pkg/stocksurferbd/utils.py` | exceptions, `post_with_csrf`, `read_xlsx_bytes` |
| `stocksurferbd_pkg/stocksurferbd/price_data_scraper.py` | CSE URL constants, column constants, `cache_dir` ctor arg, `_cse_day_end_frame` (year chunks, memory + disk cache, progress), `get_day_end_range_df` + `save_day_end_range_data` (both markets), `parse_current_prices_cse` reshape, `get_day_end_df` CSE; remove chart-based `parse_price_history_cse`, `HISTORY_URL_CSE`, `_filter_by_date` |
| `stocksurferbd_pkg/stocksurferbd/index_data_scraper.py` | `CSE_INDICES`, CSE current + history, market guards |
| `stocksurferbd_pkg/setup.py`, `stocksurferbd_pkg/pyproject.toml` | version 2.0.0 |
| `CHANGELOG.md`, `README.md` | 2.0.0 entry; one schema table per method; CSE notes |
| `fetch_csebd_data.py` | `read_excel`; reuse one `PriceData` (cache) |
| `tests/fixtures/cse_*` | trimmed xlsx/HTML/JSON fixtures |
| `tests/conftest.py`, `tests/test_price_data.py`, `tests/test_index_data.py`, `tests/test_utils.py` | CSE tests |

---

## Acceptance Criteria

### Functional
- [ ] AC-1: CSE and DSE `get_price_history_df` return identical column lists and dtypes; CSE rows newest first.
- [ ] AC-2: CSE history `OPENP == open_price`, `YCP == prev_close_price`, `VALUE_MN == turnover/1e6`; no column is a constant zero.
- [ ] AC-3: CSE and DSE `get_current_price_df` return identical column lists; CSE `DATE` is the exchange trading date; `CLOSEP` comes from the download when available.
- [ ] AC-4: `get_day_end_df('2026-09-15', market='CSE')` returns >300 rows in the history schema.
- [ ] AC-5: CSE history for `2021-01-03..2021-01-07` returns 5 rows; no-date call spans from 2015-11-24 (or the symbol's first trade) to today.
- [ ] AC-5b: `get_day_end_range_df` returns the history schema for all symbols for both markets; the DSE variant skips non-trading days.
- [ ] AC-5d: `symbols` filters the result; `chunk='month'` issues one request per month; `progress=False` is silent and a callable is invoked once per network chunk with `(from, to, index, total)`; `use_cache=False` re-downloads and does not populate the caches; invalid `chunk` raises `ValueError`.
- [ ] AC-5c: with `cache_dir` set, a second `PriceData` instance serves closed years from disk with no network call (mocked session asserts zero POSTs for those chunks).
- [ ] AC-6: `get_current_indices_df(market='CSE')` returns 5 rows; `get_index_history_df(market='CSE', ...)` returns DSE leading columns plus `CASPI, CSE30, CSCX, CSE50, CSI`.
- [ ] AC-7: All pre-existing DSE tests pass without modification.
- [ ] AC-8: Looping `get_price_history_df` over 10 CSE symbols on one instance performs each year download once (call count asserted with a mocked session); the chunk containing today is never cached.

### Non-Functional
- [ ] AC-9: No CSE test hits the network; all parse from `tests/fixtures/`.
- [ ] AC-10: `verify`, `session`, `timeout` are honoured by every new request.
- [ ] AC-11: README shows one column set per method.

---

## Test Plan

### Unit Tests
| Test | Description | Location |
|------|-------------|----------|
| `test_post_with_csrf_sends_token_and_referer` | mocked session: token parsed from page, posted, Referer set | `tests/test_utils.py` |
| `test_post_with_csrf_missing_token_raises` | page without token -> `ParseError` | `tests/test_utils.py` |
| `test_cse_history_matches_dse_schema` | columns/dtypes equal `HISTORY_COLUMNS`; newest first | `tests/test_price_data.py` |
| `test_cse_history_field_mapping` | OPENP/YCP/VALUE_MN from xlsx fixture | `tests/test_price_data.py` |
| `test_cse_history_symbol_filter_and_range` | one symbol, date bounds inclusive | `tests/test_price_data.py` |
| `test_cse_history_chunks_cached` | two symbols, one download per year chunk; today's chunk re-fetched | `tests/test_price_data.py` |
| `test_cse_history_default_is_full_archive` | no dates -> chunks from 2015-11-24 to today | `tests/test_price_data.py` |
| `test_cse_disk_cache_roundtrip` | `cache_dir` writes closed years, second instance reads them, current year not written | `tests/test_price_data.py` |
| `test_day_end_range_cse` / `test_day_end_range_dse` | both markets, same columns; DSE skips empty days | `tests/test_price_data.py` |
| `test_day_end_range_symbols_filter` | `symbols=['ACI','BRACBANK']` -> only those codes, case-insensitive | `tests/test_price_data.py` |
| `test_day_end_range_month_chunks` | `chunk='month'` -> one POST per month; `chunk='week'` -> `ValueError` | `tests/test_price_data.py` |
| `test_day_end_range_progress` | `progress=False` prints nothing (capsys); callable receives `(from, to, i, n)` per network chunk only | `tests/test_price_data.py` |
| `test_day_end_range_use_cache_false` | cached chunk re-downloaded; caches untouched afterwards | `tests/test_price_data.py` |
| `test_cse_day_end_all_symbols` | one-day fixture -> all rows | `tests/test_price_data.py` |
| `test_cse_day_end_empty_range` | empty xlsx -> empty df with columns | `tests/test_price_data.py` |
| `test_cse_current_matches_dse_schema` | live HTML fixture; `% CHANGE` computed; `OPEN` dropped | `tests/test_price_data.py` |
| `test_cse_current_closep_from_download` | CLOSEP joined; fallback to LTP when missing | `tests/test_price_data.py` |
| `test_cse_current_date_from_exchange` | DATE from download/company page, not `datetime.now()` | `tests/test_price_data.py` |
| `test_cse_current_indices` | 5 JSON fixtures -> 4 columns, 5 rows | `tests/test_index_data.py` |
| `test_cse_index_history` | xlsx fixture -> leading DSE columns + index columns, newest first | `tests/test_index_data.py` |
| `test_invalid_market_*` | non-DSE/CSE -> `IOError` on every market-taking method | both |

### Test results (2026-09-16, `pytest tests/ --cov=stocksurferbd_pkg/stocksurferbd`)

82 passed, 0 failed (38 pre-existing tests unchanged). Coverage: total 72%;
`price_data_scraper.py` 84%, `index_data_scraper.py` 84%, `utils.py` 97%
(uncovered lines are live-network paths and DSE branches that predate this
feature). Planned scenarios map to the implemented tests as follows:

| Planned | Implemented in |
|---------|----------------|
| `test_cse_history_matches_dse_schema`, `test_cse_history_field_mapping` | `test_cse_download_to_history_matches_dse_schema`, `test_cse_download_to_history_field_mapping`, `test_cse_history_matches_dse_schema_and_filters_symbol` |
| `test_cse_history_symbol_filter_and_range` | `test_cse_history_matches_dse_schema_and_filters_symbol`, `test_cse_history_range_is_inclusive_after_chunk_download` |
| `test_cse_history_chunks_cached` | `test_cse_history_chunks_cached_per_instance` |
| `test_cse_day_end_all_symbols`, `test_cse_day_end_empty_range` | `test_cse_day_end_single_day`, `test_cse_day_end_empty_download` |
| `test_day_end_range_cse`, `test_day_end_range_dse`, `test_day_end_range_symbols_filter` | `test_day_end_range_cse_symbols_filter`, `test_day_end_range_dse_skips_empty_days` |
| `test_cse_current_closep_from_download`, `test_cse_current_date_from_exchange` | `test_cse_current_matches_dse_schema`, `test_get_current_price_df_cse_uses_exchange_date_and_closes`, `test_get_current_price_df_cse_falls_back_to_company_page_date` |
| `test_cse_current_indices`, `test_cse_index_history` | `test_parse_index_summary_cse`, `test_get_current_indices_df_cse`, `test_parse_index_history_cse`, `test_get_index_history_df_cse` |
| chunking, progress, use_cache, disk cache, month chunks | `test_cse_year_chunks_are_whole_years_clipped_to_archive`, `test_cse_month_chunks_cross_year_boundary`, `test_cse_chunks_before_archive_or_bad_size`, `test_cse_current_year_chunk_ends_today`, `test_day_end_range_month_chunks`, `test_day_end_range_progress`, `test_day_end_range_use_cache_false`, `test_cse_disk_cache_roundtrip` |
| utils | `tests/test_utils.py` (7 tests) |

Test files: `tests/test_utils.py`, `tests/test_price_data.py`,
`tests/test_index_data.py`; fixtures under `tests/fixtures/cse_*`.

### Integration (manual smoke, not CI)
Live calls for ACI history (default and 2021 range), day-end 2026-09-15,
current prices during and after the session, indices. Also verify whether the
company download is populated **intraday** (session 10:00–14:30 BD); either
way the join-with-fallback design holds, but the README wording depends on it.

---

## Rollout
- Version `1.2.0 -> 2.0.0`: public members were removed and CSE output columns
  changed, so semver calls for a major bump even though DSE is untouched.
- Changelog: CSE outputs now match DSE schemas; CSE history re-sourced (real
  open, LTP, YCP, trades, value; full archive from 2015-11-24 by default);
  new `get_day_end_range_df` / `save_day_end_range_data` for both markets;
  optional `cache_dir`; `get_day_end_df` and `IndexData` support CSE. Breaking for CSE-only callers relying on `OPEN` /
  `% CHANGE` in history. DSE unchanged.
