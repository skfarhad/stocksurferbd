# Feature Specification: CSE/DSE Uniform Data

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

CSE publishes better sources than the ones we scrape: a POST/xlsx day-end
download per date range (`market/data_download_company`, verified back to
Jan 2021), an index-history download (`market/data_download_index`) and a live
index JSON endpoint (`home/load__index_summary/`). All POSTs need a
`csrf_cse_token` from the page plus the session cookie.

### Scope
- **In Scope**: `PriceData` (history, current, day-end) and `IndexData`
  (current snapshot, day-wise history) for `market='CSE'`; CSRF-aware POST
  helper in `HttpScraper`; offline fixtures and tests; README schema tables;
  `fetch_csebd_data.py` fix; version bump to 1.2.0.
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
PriceData.get_price_history_df(market='CSE')
  └─ _cse_day_end_records(start, end, symbol=None)
       ├─ HttpScraper.post_with_csrf(page_url, action_url, data)
       │     GET page -> extract csrf_cse_token -> POST (session cookie, Referer)
       ├─ pandas.read_excel(bytes)           # openpyxl engine
       └─ _cse_rows_to_dse_history(df)       # rename/convert to canonical schema

PriceData.get_day_end_df(date, market='CSE')      -> same path, start == end == date
PriceData.get_current_price_df(market='CSE')      -> existing dataTable scrape,
                                                    re-shaped to DSE columns,
                                                    DATE from exchange not clock
IndexData.get_current_indices_df(market='CSE')    -> POST load__index_summary per index (JSON)
IndexData.get_index_history_df(market='CSE', ...) -> POST data_download_index (xlsx)
```

### Canonical schemas (DSE, unchanged)

| Method | Columns |
|--------|---------|
| `get_price_history_df` / `get_day_end_df` | `DATE, TRADING_CODE, LTP, HIGH, LOW, OPENP, CLOSEP, YCP, TRADE, VALUE_MN, VOLUME` |
| `get_current_price_df` | `DATE, TRADING_CODE, LTP, HIGH, LOW, CLOSEP, YCP, % CHANGE, TRADE, VALUE_MN, VOLUME` |
| `get_current_indices_df` | `INDEX, POINTS, CHANGE, PCT_CHANGE` |
| `get_index_history_df` | `DATE, TOTAL_TRADE, TOTAL_VOLUME, VALUE_MN, MARKET_CAP_MN, <one column per index>` |

Column lists become module-level constants (e.g. `HISTORY_COLUMNS`,
`CURRENT_COLUMNS`) and every CSE builder ends with
`pd.DataFrame(records, columns=<CONST>)` so order is enforced, not incidental.

### CSE field mapping

**Day-end download -> history schema**

| CSE xlsx column | Canonical | Transform |
|-----------------|-----------|-----------|
| `trade_date` | `DATE` | `YYYY-MM-DD` string (DSE history emits strings) |
| `company_code` | `TRADING_CODE` | as-is |
| `last_traded_price` | `LTP` | float |
| `day_high` / `day_low` | `HIGH` / `LOW` | float |
| `open_price` | `OPENP` | float |
| `close_price` | `CLOSEP` | float |
| `prev_close_price` | `YCP` | float |
| `no_of_trades` | `TRADE` | float (DSE emits float) |
| `turnover` | `VALUE_MN` | Taka / 1e6, round 2 dp |
| `volume` | `VOLUME` | float |
| `company_name` | dropped | not in DSE schema |

Rows are sorted by `DATE` ascending then `TRADING_CODE` to match DSE ordering.

**Live `dataTable` -> current schema**

| CSE cell | Canonical | Transform |
|----------|-----------|-----------|
| exchange trading date | `DATE` | `datetime.date`; taken from the CSE company-details "Updated Date" of the first symbol, falling back to the latest `trade_date` in a 1-day day-end download; never the machine clock |
| `STOCK CODE` | `TRADING_CODE` | as-is |
| `LTP` | `LTP` | float |
| `HIGH` / `LOW` | `HIGH` / `LOW` | float |
| `LTP` | `CLOSEP` | DSE live feed publishes the running close; CSE's live table has none, so mirror `LTP` |
| `YCP` | `YCP` | float |
| computed | `% CHANGE` | `round((LTP - YCP) / YCP * 100, 2)`; `0.0` when `YCP == 0` |
| `TRADE`, `VALUE(MN)`, `VOLUME` | same | float |
| `OPEN` | dropped | not in DSE schema |

**Index JSON -> current indices**: one POST per index in
`("CASPI", "CSE30", "CSCX", "CSE50", "CSI")`; `value -> POINTS`,
`change -> CHANGE`, `percentage_change -> PCT_CHANGE`.

**Index xlsx -> index history**: `trade_date -> DATE` (`datetime.date`, as DSE),
`no_of_trades -> TOTAL_TRADE`, `volume -> TOTAL_VOLUME`,
`turnover/1e6 -> VALUE_MN`, `market_capital/1e6 -> MARKET_CAP_MN`,
`<idx>_value -> <IDX>` for the five indices.

### Date handling
- History with no dates: default `end = today`, `start = today - 183 days`
  so the default window matches the current 6-month behaviour.
- `_fmt_date` already normalises inputs; reuse it.
- The download endpoint accepts any range; large ranges are one request.

### HttpScraper changes (`utils.py`)
```python
CSRF_FIELD = 'csrf_cse_token'

def post_with_csrf(self, page_url, action_url, data, token_pattern=None):
    """GET page_url, extract the CSRF token, POST data to action_url."""
```
Sets `Referer` and reuses `self.session` so the cookie travels. Raises a clear
`ValueError` if no token is found. The existing `_get`/`_post` stay.

### Error handling (per `standards/global/error-handling`)
- Non-xlsx content type from a download endpoint -> raise with the first 200
  chars of the body (site returned an HTML error page).
- Empty download for a valid range -> return an empty DataFrame with the
  canonical columns (matches `get_day_end_df` DSE behaviour on non-trading days).
- Unknown market string -> existing `IOError('Invalid Stock Market! ...')`.

### Files touched
| File | Change |
|------|--------|
| `stocksurferbd_pkg/stocksurferbd/utils.py` | `post_with_csrf`, CSE URL constants |
| `stocksurferbd_pkg/stocksurferbd/price_data_scraper.py` | CSE day-end path, re-shaped current parser, column constants; remove chart-based `parse_price_history_cse` |
| `stocksurferbd_pkg/stocksurferbd/index_data_scraper.py` | CSE current + history |
| `stocksurferbd_pkg/setup.py`, `requirements.txt` | `openpyxl` explicit; version 1.2.0 |
| `README.md` | one schema table per method; CSE notes |
| `fetch_csebd_data.py` | `read_excel` |
| `tests/fixtures/cse_*` | saved xlsx/HTML/JSON |
| `tests/test_price_data.py`, `tests/test_index_data.py` | CSE tests |

---

## Acceptance Criteria

### Functional
- [ ] AC-1: CSE and DSE `get_price_history_df` return identical column lists and dtypes.
- [ ] AC-2: CSE history `OPENP == open_price`, `YCP == prev_close_price`; no column is a constant zero.
- [ ] AC-3: CSE and DSE `get_current_price_df` return identical column lists; CSE `DATE` is the exchange trading date.
- [ ] AC-4: `get_day_end_df('2026-09-15', market='CSE')` returns >300 rows in the history schema.
- [ ] AC-5: CSE history for `2021-01-03..2021-01-07` returns 5 rows.
- [ ] AC-6: `get_current_indices_df(market='CSE')` returns 5 rows; `get_index_history_df(market='CSE', ...)` returns DSE leading columns plus `CASPI, CSE30, CSCX, CSE50, CSI`.
- [ ] AC-7: All pre-existing DSE tests pass without modification.

### Non-Functional
- [ ] AC-8: No CSE test hits the network; all parse from `tests/fixtures/`.
- [ ] AC-9: `verify`, `session`, `timeout` are honoured by every new request.
- [ ] AC-10: README shows one column set per method.

---

## Test Plan

### Unit Tests
| Test | Description | Location |
|------|-------------|----------|
| `test_cse_history_matches_dse_schema` | column list/order equals `HISTORY_COLUMNS` | `tests/test_price_data.py` |
| `test_cse_history_field_mapping` | OPENP/YCP/VALUE_MN conversions from xlsx fixture | `tests/test_price_data.py` |
| `test_cse_day_end_all_symbols` | one-day fixture -> all rows, sorted | `tests/test_price_data.py` |
| `test_cse_current_matches_dse_schema` | reshaped live table; `% CHANGE` computed; `OPEN` dropped | `tests/test_price_data.py` |
| `test_cse_current_date_not_machine_clock` | DATE sourced from fixture, not `datetime.now()` | `tests/test_price_data.py` |
| `test_post_with_csrf_extracts_token` | token parsed and sent, Referer set (mocked session) | `tests/test_utils.py` |
| `test_cse_current_indices` | JSON fixtures -> 4 columns, 5 rows | `tests/test_index_data.py` |
| `test_cse_index_history` | xlsx fixture -> leading DSE columns + index columns | `tests/test_index_data.py` |
| `test_dse_outputs_unchanged` | existing tests, untouched | existing files |

### Integration Tests
| Test | Description |
|------|-------------|
| manual smoke (documented in tasks) | live calls for ACI history, day-end 2026-09-15, current, indices; not part of CI |

---

## Rollout
- Version bump `1.1.0 -> 1.2.0`.
- Changelog entry: CSE outputs now match DSE schemas (breaking for CSE-only
  callers relying on `OPEN` / `% CHANGE` in history); DSE unchanged.
