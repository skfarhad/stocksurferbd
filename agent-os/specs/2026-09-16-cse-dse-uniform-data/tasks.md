# Task Breakdown: CSE/DSE Uniform Data

**Spec**: `2026-09-16-cse-dse-uniform-data`
**Status**: Implemented (2026-09-16) — pending `/run-tests` and manual smoke during a CSE session

DSE output is canonical and must not change. Every task below makes CSE
conform to it. Tests run offline against fixtures under `tests/fixtures/`;
run with `pytest tests/` from the repo root (see `tests/conftest.py`).

## Task List

### Task Group 1: HTTP plumbing and fixtures

**Priority**: High
**Files**:
- `stocksurferbd_pkg/stocksurferbd/utils.py`
- `tests/test_utils.py` (new)
- `tests/fixtures/cse_*` (new)
- `tests/conftest.py`

#### Subtasks:

**1.1 Exception hierarchy**
- [x] Add `StockSurferError`, `FetchError(StockSurferError)`, `ParseError(StockSurferError)` to `utils.py`; export from `__init__.py`.
- [x] Do not change existing raises elsewhere (out of scope).

**1.2 CSRF-aware POST**
- [x] Add `CSRF_FIELD_CSE = 'csrf_cse_token'` and `post_with_csrf(self, page_url, action_url, data)` to `HttpScraper`.
- [x] GET `page_url` via `self.session`, regex the hidden input value, POST `data + token` to `action_url` with `Referer=page_url`; honour `verify`/`timeout`.
- [x] Raise `ParseError` when no token; wrap `requests.RequestException` in `FetchError`.
- [x] Add `read_xlsx_bytes(content, content_type)` helper: `ParseError` if content type is not a spreadsheet, else `pd.read_excel(BytesIO, engine='openpyxl')`.

**1.3 Fixtures (trimmed, committed)**
- [x] `cse_day_end_2026-09-15.xlsx`: company download for `2026-09-15..2026-09-15` (all symbols, one day).
- [x] `cse_day_end_range.xlsx`: company download `2026-09-10..2026-09-15` trimmed to 3 symbols (ACI, BRACBANK, 1JANATAMF) so the multi-day/symbol-filter tests stay small.
- [x] `cse_current_prices.html`: live `#dataTable` page trimmed to the header row plus ~10 symbol rows (must include the 3 above and one with `YCP == 0`).
- [x] `cse_company_details_aci.html`: company page trimmed to the "Current Market Information" block (contains the "Last Trade Date"/"Updated Date" label).
- [x] `cse_index_summary_<IDX>.json` x5: responses of `load__index_summary/`.
- [x] `cse_index_history.xlsx`: index download `2026-09-10..2026-09-15`.
- [x] `cse_historicaldata_page.html`: trimmed page containing only the CSRF hidden input (for `post_with_csrf` tests).
- [x] Add loader fixtures in `conftest.py` (`cse_day_end_bytes`, `cse_current_soup`, `cse_company_html`, `cse_index_json`, `cse_index_history_bytes`).

**1.4 Tests**
- [x] `test_post_with_csrf_sends_token_and_referer` (mock `session.get`/`session.post`).
- [x] `test_post_with_csrf_missing_token_raises`.
- [x] `test_read_xlsx_bytes_rejects_html`.

**Acceptance Criteria**:
- `post_with_csrf` sends the token extracted from the page, reuses the session, and sets Referer.
- All fixture files load in tests; none exceeds ~150 KB.

---

### Task Group 2: PriceData CSE history and day-end

**Priority**: High
**Files**:
- `stocksurferbd_pkg/stocksurferbd/price_data_scraper.py`
- `tests/test_price_data.py`

#### Subtasks:

**2.1 Constants**
- [x] `VALID_MARKETS = ('DSE', 'CSE')`; use it in every market check.
- [x] `HISTORY_COLUMNS` and `CURRENT_COLUMNS` (exact DSE order from the spec).
- [x] `HISTORICAL_DATA_PAGE_CSE`, `DOWNLOAD_COMPANY_URL_CSE`, `COMPANY_DETAILS_URL_CSE`.
- [x] `_CSE_HISTORY_COLUMN_MAP` (xlsx column -> canonical), `CSE_EARLIEST_DATE = '2015-11-24'`, `CSE_CACHE_FILE_PATTERN = 'cse_day_end_{start}_{end}.pkl'`.
- [x] `PriceData.__init__(..., cache_dir=None)` passing the HTTP args through to `HttpScraper`; `self._cse_chunk_cache = {}`.

**2.2 Download -> canonical frame**
- [x] `_cse_rows_to_history(df_xlsx) -> DataFrame[HISTORY_COLUMNS]`: rename, `DATE` to `YYYY-MM-DD` str, floats, `VALUE_MN = round(turnover / 1e6, 3)`, drop `company_name`, sort `DATE` desc then `TRADING_CODE` asc.
- [x] `_cse_year_chunks(start, end) -> list[(from, to)]` calendar-year chunks clipped to the range.
- [x] `CSE_CHUNK_SIZES = ('year', 'month')`; `_cse_chunks(start, end, chunk)` returns calendar-year or calendar-month `(from, to)` pairs clipped to `CSE_EARLIEST_DATE..today`; a range entirely before the earliest date yields no chunks; invalid `chunk` -> `ValueError` naming the allowed values.
- [x] `_report_progress(progress, chunk_from, chunk_to, index, total)`: `True` -> print, `False` -> nothing, callable -> call. Only invoked for network chunks.
- [x] `_cse_day_end_frame(start, end, chunk='year', progress=True, use_cache=True)`: per chunk, resolve in order memory cache -> disk cache (`cache_dir`, closed chunks only) -> network (skip both cache reads and writes when `use_cache=False`) (`post_with_csrf` + `read_xlsx_bytes` + `_cse_rows_to_history`). Store in memory and, when `cache_dir` is set and the chunk is closed (`to < today`), on disk. Print one progress line per network chunk. Concat; return empty frame with columns when nothing.
- [x] `_cse_chunk_is_closed(chunk)` helper so the today-rule lives in one place.

**2.3 Public methods**
- [x] `get_price_history_df(..., market='CSE')`: default `start = CSE_EARLIEST_DATE`, `end = today` (full archive); frame filtered to `TRADING_CODE == symbol.strip().upper()`.
- [x] `get_day_end_range_df(start_date, end_date=None, market='DSE', symbols=None, chunk='year', progress=True, use_cache=True)`: CSE -> `_cse_day_end_frame(...)`; DSE -> loop calendar days over `parse_day_end_dse`, skip empty days, concat, report progress per day; both return `HISTORY_COLUMNS`, newest first. `symbols` normalised (`strip().upper()`) and applied after assembly. Validate `start_date` is required and `chunk` is allowed.
- [x] `save_day_end_range_data(file_path='', file_name='day_end_range.xlsx', market='DSE', start_date=None, end_date=None, **kwargs)` thin wrapper passing `kwargs` through.
- [x] `get_day_end_df(date, market='CSE')`: `_cse_day_end_frame(day, day)`; keep DSE branch unchanged.
- [x] Remove `HISTORY_URL_CSE`, `parse_price_history_cse`, `_filter_by_date` and their tests (`test_filter_by_date_*`).
- [x] Ensure DSE branches are byte-for-byte unchanged (run existing tests).

**2.4 Tests**
- [x] `test_cse_history_matches_dse_schema` (columns, dtypes, newest first).
- [x] `test_cse_history_field_mapping` (OPENP, YCP, VALUE_MN, LTP for a known row in the fixture).
- [x] `test_cse_history_symbol_filter_and_range`.
- [x] `test_cse_history_chunks_cached` (mock `post_with_csrf`, two symbols, assert call count == number of year chunks; the chunk containing today is fetched again on the second call).
- [x] `test_cse_history_default_is_full_archive` (no dates -> first chunk starts 2015-11-24, last ends today).
- [x] `test_cse_year_chunks_clipping` (range before 2015 -> no chunks; range straddling years -> correct boundaries).
- [x] `test_cse_disk_cache_roundtrip` (`tmp_path` as `cache_dir`: closed year written, current year not; second instance loads from disk with zero POSTs).
- [x] `test_day_end_range_cse` and `test_day_end_range_dse` (DSE mocked `_get` returning a table for 2 of 4 days; columns identical to `HISTORY_COLUMNS`).
- [x] `test_day_end_range_symbols_filter` (subset, case-insensitive, unknown code -> empty).
- [x] `test_day_end_range_month_chunks` (`chunk='month'` -> one POST per calendar month across a year boundary; `chunk='week'` -> `ValueError`).
- [x] `test_day_end_range_progress` (`progress=False` -> no output via `capsys`; callable -> one call per network chunk with `(from, to, index, total)`, none for cache hits).
- [x] `test_day_end_range_use_cache_false` (pre-populated cache ignored, POST issued, cache dict and `cache_dir` unchanged afterwards).
- [x] `test_cse_day_end_all_symbols`, `test_cse_day_end_empty_range`.
- [x] `test_invalid_market_raises` covers history, current, day-end.

**Acceptance Criteria**:
- AC-1, AC-2, AC-4, AC-5, AC-5b, AC-5c, AC-5d, AC-7, AC-8 from the spec.

---

### Task Group 3: PriceData CSE current prices

**Priority**: High
**Files**:
- `stocksurferbd_pkg/stocksurferbd/price_data_scraper.py`
- `tests/test_price_data.py`

#### Subtasks:

**3.1 Reshape the live table**
- [x] `parse_current_prices_cse(soup, trading_date, close_by_code=None)` returns dicts keyed exactly by `CURRENT_COLUMNS`: drop `OPEN`, add `CLOSEP` (from `close_by_code[code]`, else `LTP`), compute `% CHANGE = round(LTP - YCP, 2)` (absolute change, what DSE publishes under that name).
- [x] `ParseError` when `#dataTable` is absent.

**3.2 Exchange trading date and close**
- [x] `_cse_today_day_end()` -> `_cse_day_end_frame(today, today)` (uncached).
- [x] `_cse_trading_date_fallback()` -> GET company page for a fixed liquid symbol, regex `(?:Last Trade|Updated) Date\s+(\d{1,2} \w+, \d{4})`, `parser.parse(...).date()`; last resort `today`.
- [x] `get_current_price_df(market='CSE')`: if today's day-end frame is non-empty use its `DATE` and `CLOSEP` map; else fallback date and `CLOSEP = LTP`.

**3.3 Tests**
- [x] `test_cse_current_matches_dse_schema`.
- [x] `test_cse_current_closep_from_download` and fallback-to-LTP case.
- [x] `test_cse_current_date_from_exchange` (assert not `datetime.date.today()` when fixture date differs).
- [x] `test_cse_current_pct_change_zero_ycp`.
- [x] Update the existing inline `CSE_CURRENT_HTML` test (`test_parse_current_prices_cse_has_open`) to the new contract.

**Acceptance Criteria**:
- AC-3 from the spec.

---

### Task Group 4: IndexData CSE

**Priority**: Medium
**Files**:
- `stocksurferbd_pkg/stocksurferbd/index_data_scraper.py`
- `tests/test_index_data.py`

#### Subtasks:

**4.1 Constants and guards**
- [x] `VALID_MARKETS = ('DSE', 'CSE')`, `CSE_INDICES = ('CASPI', 'CSE30', 'CSCX', 'CSE50', 'CSI')`, `HOME_URL_CSE`, `INDEX_SUMMARY_URL_CSE`, `HISTORICAL_DATA_PAGE_CSE`, `DOWNLOAD_INDEX_URL_CSE`, `INDEX_CURRENT_COLUMNS`.
- [x] `get_intraday_df` / `get_index_graph_df`: raise `IOError("Only 'DSE' is supported for ...")` for CSE with a message naming the alternative.

**4.2 Current indices**
- [x] `parse_index_summary_cse(index, json_text) -> dict[INDEX_CURRENT_COLUMNS]`; `None` for null values (same `_num` semantics).
- [x] `get_current_indices_df(market='CSE')`: one `post_with_csrf(HOME_URL_CSE, INDEX_SUMMARY_URL_CSE, {'selected_index': idx})` per index (token fetched once, reuse via a private `_post_with_token` variant or accept 5 page GETs; prefer fetching the token once).

**4.3 Index history**
- [x] `parse_index_history_cse(df_xlsx) -> list[dict]` with `DATE` (`datetime.date`), `TOTAL_TRADE` (int), `TOTAL_VOLUME` (int), `VALUE_MN`, `MARKET_CAP_MN` (both `/1e6`), then `CASPI, CSE30, CSCX, CSE50, CSI`; newest first.
- [x] `get_index_history_df(market='CSE', start_date, end_date)`: default `end = today`, `start = today - 30 days` (DSE default is a rolling ~30 days).

**4.4 Tests**
- [x] `test_cse_current_indices` (5 rows, 4 columns, values from JSON fixtures).
- [x] `test_cse_index_history` (columns, dtypes, newest first).
- [x] `test_index_invalid_market` and CSE-unsupported methods raise.

**Acceptance Criteria**:
- AC-6 from the spec; DSE `IndexData` tests unchanged.

---

### Task Group 5: Docs, version, example script

**Priority**: Medium
**Files**:
- `README.md`, `CHANGELOG.md`
- `stocksurferbd_pkg/setup.py`, `stocksurferbd_pkg/pyproject.toml`
- `fetch_csebd_data.py`
- `agent-os/product/roadmap.md`

#### Subtasks:

**5.1 README**
- [x] Replace the per-market schema tables under "Output data schema" with one table per method.
- [x] Update the `PriceData` notes: CSE history depth (2015-11-24+, gaps before mid-2018), full-archive default vs DSE's server-side ~2-year window, year chunks + `cache_dir`, the cost table from the spec, `get_day_end_df` for CSE, CLOSEP/DATE semantics for CSE current.
- [x] Document `get_day_end_range_df` / `save_day_end_range_data` for both markets with the parameter table (`symbols`, `chunk`, `progress`, `use_cache`) and the recommended bulk pattern (pull once, split by `TRADING_CODE`).
- [x] `IndexData` section: list CSE indices, which methods support CSE, remove "DSE only" where no longer true.
- [x] Keep "DSE only" notes for `FundamentalData` and `BlockTradeData`.

**5.2 Version and changelog**
- [x] `setup.py` and `pyproject.toml` -> `1.3.0`.
- [x] `CHANGELOG.md` `[1.3.0]` entry (Added / Changed / Breaking for CSE-only callers).

**5.3 Example script**
- [x] `fetch_csebd_data.py`: `pd.read_excel`, `HISTORY_FOLDER = 'cse_history_data'`, `PriceData(cache_dir='cse_cache')`; fetch with one `get_day_end_range_df(CSE_EARLIEST_DATE, today, market='CSE', progress=True)` and write one `<SYM>_history_data.xlsx` per `TRADING_CODE` group instead of a per-symbol request loop.

**5.4 Roadmap**
- [x] Mark CSE price/index parity as shipped; keep CSE fundamentals open.

**Acceptance Criteria**:
- AC-11; `python -c "import stocksurferbd"` works; `pytest tests/` green.

---

## Execution Order

1. **HTTP plumbing and fixtures** (everything else depends on `post_with_csrf`, `read_xlsx_bytes`, fixtures)
2. **PriceData CSE history and day-end**
3. **PriceData CSE current prices** (uses the day-end frame from group 2)
4. **IndexData CSE** (independent of 2–3; can run in parallel after 1)
5. **Docs, version, example script**

---

## Key Implementation Notes

### Patterns to Follow
- Separate fetch / parse / assemble / save (`standards/python/coding.md`): parsers take bytes/soup/JSON and are testable offline; only `get_*` methods touch the network.
- Constants for every URL, column name and market code; no literals in branches.
- Guard `find(...)` results; raise `ParseError` with the symbol/market in the message.
- Numeric cells through `parse_float`/`parse_int`; decide explicitly on `0` vs missing (download rows with zero trades are genuine zeros, keep them).
- Every CSE frame is built with `pd.DataFrame(records, columns=CONST)`.

### Risk Mitigation
- **DSE regression**: never edit DSE branches; run the full suite after each group.
- **Large downloads**: the CSE source is all-symbols-per-range; there is no per-symbol OHLCV endpoint. Make stock-wise *calls* cheap instead: year chunks, memory cache per instance, optional `cache_dir` for closed years, never cache a chunk that includes today, sequential requests with progress output. Steer batch users to `get_day_end_range_df`.
- **Intraday availability of the company download is unverified** (session 10:00–14:30 BD). The join-with-fallback design works either way; confirm during execution and word the README accordingly.
- **CSE layout drift**: the xlsx column names are the contract; assert on them and raise `ParseError` naming missing columns.
- **CSRF**: token is per page load; always fetch it in the same session that posts.

---

## Dependencies

**External Dependencies:**
- `openpyxl==3.1.5` (already pinned; now also used for reading).
- Live CSE endpoints listed in the spec (for fixtures and smoke tests only).

**Internal Dependencies:**
- `HttpScraper.post_with_csrf` and `read_xlsx_bytes` (group 1) before groups 2–4.
- `_cse_day_end_frame` (group 2) before group 3.

---

## Session Notes (2026-09-16)

- All five task groups implemented; suite: 82 passed (38 pre-existing DSE tests untouched).
- Live smoke (after the CSE session): `get_day_end_range_df` Sep-2026 for ACI,
  `get_day_end_df('2026-09-15', 'CSE')` = 377 rows, `get_current_price_df('CSE')`
  = 387 rows with columns and dtypes identical to DSE; 48 rows carried a
  `CLOSEP` distinct from `LTP`; `DATE` came from the exchange download.
- Spec correction found during execution: DSE's `% CHANGE` column holds the
  absolute change `LTP - YCP` (97% of live rows), not a percentage; CSE now
  computes the same quantity.
- Cache files are named `cse_day_end_<from>_<to>.pkl` (not per year) so month
  and year chunks coexist.
- Still unverified: whether the CSE company download is populated **intraday**
  (all checks ran after 14:30 BD). The join-with-fallback design handles both
  cases; confirm during a session before wording the README more strongly.
