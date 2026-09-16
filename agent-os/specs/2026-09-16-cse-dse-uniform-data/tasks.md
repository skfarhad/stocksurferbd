# Task Breakdown: CSE/DSE Uniform Data

**Spec**: `2026-09-16-cse-dse-uniform-data`
**Status**: Ready for Implementation

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
- [ ] Add `StockSurferError`, `FetchError(StockSurferError)`, `ParseError(StockSurferError)` to `utils.py`; export from `__init__.py`.
- [ ] Do not change existing raises elsewhere (out of scope).

**1.2 CSRF-aware POST**
- [ ] Add `CSRF_FIELD_CSE = 'csrf_cse_token'` and `post_with_csrf(self, page_url, action_url, data)` to `HttpScraper`.
- [ ] GET `page_url` via `self.session`, regex the hidden input value, POST `data + token` to `action_url` with `Referer=page_url`; honour `verify`/`timeout`.
- [ ] Raise `ParseError` when no token; wrap `requests.RequestException` in `FetchError`.
- [ ] Add `read_xlsx_bytes(content, content_type)` helper: `ParseError` if content type is not a spreadsheet, else `pd.read_excel(BytesIO, engine='openpyxl')`.

**1.3 Fixtures (trimmed, committed)**
- [ ] `cse_day_end_2026-09-15.xlsx`: company download for `2026-09-15..2026-09-15` (all symbols, one day).
- [ ] `cse_day_end_range.xlsx`: company download `2026-09-10..2026-09-15` trimmed to 3 symbols (ACI, BRACBANK, 1JANATAMF) so the multi-day/symbol-filter tests stay small.
- [ ] `cse_current_prices.html`: live `#dataTable` page trimmed to the header row plus ~10 symbol rows (must include the 3 above and one with `YCP == 0`).
- [ ] `cse_company_details_aci.html`: company page trimmed to the "Current Market Information" block (contains the "Last Trade Date"/"Updated Date" label).
- [ ] `cse_index_summary_<IDX>.json` x5: responses of `load__index_summary/`.
- [ ] `cse_index_history.xlsx`: index download `2026-09-10..2026-09-15`.
- [ ] `cse_historicaldata_page.html`: trimmed page containing only the CSRF hidden input (for `post_with_csrf` tests).
- [ ] Add loader fixtures in `conftest.py` (`cse_day_end_bytes`, `cse_current_soup`, `cse_company_html`, `cse_index_json`, `cse_index_history_bytes`).

**1.4 Tests**
- [ ] `test_post_with_csrf_sends_token_and_referer` (mock `session.get`/`session.post`).
- [ ] `test_post_with_csrf_missing_token_raises`.
- [ ] `test_read_xlsx_bytes_rejects_html`.

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
- [ ] `VALID_MARKETS = ('DSE', 'CSE')`; use it in every market check.
- [ ] `HISTORY_COLUMNS` and `CURRENT_COLUMNS` (exact DSE order from the spec).
- [ ] `HISTORICAL_DATA_PAGE_CSE`, `DOWNLOAD_COMPANY_URL_CSE`, `COMPANY_DETAILS_URL_CSE`.
- [ ] `_CSE_HISTORY_COLUMN_MAP` (xlsx column -> canonical) and `CSE_DEFAULT_HISTORY_YEARS = 2`, `CSE_EARLIEST_DATE = '2015-11-24'`.

**2.2 Download -> canonical frame**
- [ ] `_cse_rows_to_history(df_xlsx) -> DataFrame[HISTORY_COLUMNS]`: rename, `DATE` to `YYYY-MM-DD` str, floats, `VALUE_MN = round(turnover / 1e6, 3)`, drop `company_name`, sort `DATE` desc then `TRADING_CODE` asc.
- [ ] `_cse_year_chunks(start, end) -> list[(from, to)]` calendar-year chunks clipped to the range.
- [ ] `_cse_day_end_frame(start, end)`: for each chunk, use `self._cse_chunk_cache` unless the chunk includes today; else `post_with_csrf` + `read_xlsx_bytes` + `_cse_rows_to_history`; concat; return empty frame with columns when nothing.

**2.3 Public methods**
- [ ] `get_price_history_df(..., market='CSE')`: default `start = today - 2 years`, `end = today`; frame filtered to `TRADING_CODE == symbol.strip().upper()`.
- [ ] `get_day_end_df(date, market='CSE')`: `_cse_day_end_frame(day, day)`; keep DSE branch unchanged.
- [ ] Remove `HISTORY_URL_CSE`, `parse_price_history_cse`, `_filter_by_date` and their tests (`test_filter_by_date_*`).
- [ ] Ensure DSE branches are byte-for-byte unchanged (run existing tests).

**2.4 Tests**
- [ ] `test_cse_history_matches_dse_schema` (columns, dtypes, newest first).
- [ ] `test_cse_history_field_mapping` (OPENP, YCP, VALUE_MN, LTP for a known row in the fixture).
- [ ] `test_cse_history_symbol_filter_and_range`.
- [ ] `test_cse_history_chunks_cached` (mock `post_with_csrf`, two symbols, assert call count == number of year chunks).
- [ ] `test_cse_day_end_all_symbols`, `test_cse_day_end_empty_range`.
- [ ] `test_invalid_market_raises` covers history, current, day-end.

**Acceptance Criteria**:
- AC-1, AC-2, AC-4, AC-5, AC-7, AC-8 from the spec.

---

### Task Group 3: PriceData CSE current prices

**Priority**: High
**Files**:
- `stocksurferbd_pkg/stocksurferbd/price_data_scraper.py`
- `tests/test_price_data.py`

#### Subtasks:

**3.1 Reshape the live table**
- [ ] `parse_current_prices_cse(soup, trading_date, close_by_code=None)` returns dicts keyed exactly by `CURRENT_COLUMNS`: drop `OPEN`, add `CLOSEP` (from `close_by_code[code]`, else `LTP`), compute `% CHANGE = round((LTP - YCP) / YCP * 100, 2)` with `0.0` when `YCP == 0`.
- [ ] `ParseError` when `#dataTable` is absent.

**3.2 Exchange trading date and close**
- [ ] `_cse_today_day_end()` -> `_cse_day_end_frame(today, today)` (uncached).
- [ ] `_cse_trading_date_fallback()` -> GET company page for a fixed liquid symbol, regex `(?:Last Trade|Updated) Date\s+(\d{1,2} \w+, \d{4})`, `parser.parse(...).date()`; last resort `today`.
- [ ] `get_current_price_df(market='CSE')`: if today's day-end frame is non-empty use its `DATE` and `CLOSEP` map; else fallback date and `CLOSEP = LTP`.

**3.3 Tests**
- [ ] `test_cse_current_matches_dse_schema`.
- [ ] `test_cse_current_closep_from_download` and fallback-to-LTP case.
- [ ] `test_cse_current_date_from_exchange` (assert not `datetime.date.today()` when fixture date differs).
- [ ] `test_cse_current_pct_change_zero_ycp`.
- [ ] Update the existing inline `CSE_CURRENT_HTML` test (`test_parse_current_prices_cse_has_open`) to the new contract.

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
- [ ] `VALID_MARKETS = ('DSE', 'CSE')`, `CSE_INDICES = ('CASPI', 'CSE30', 'CSCX', 'CSE50', 'CSI')`, `HOME_URL_CSE`, `INDEX_SUMMARY_URL_CSE`, `HISTORICAL_DATA_PAGE_CSE`, `DOWNLOAD_INDEX_URL_CSE`, `INDEX_CURRENT_COLUMNS`.
- [ ] `get_intraday_df` / `get_index_graph_df`: raise `IOError("Only 'DSE' is supported for ...")` for CSE with a message naming the alternative.

**4.2 Current indices**
- [ ] `parse_index_summary_cse(index, json_text) -> dict[INDEX_CURRENT_COLUMNS]`; `None` for null values (same `_num` semantics).
- [ ] `get_current_indices_df(market='CSE')`: one `post_with_csrf(HOME_URL_CSE, INDEX_SUMMARY_URL_CSE, {'selected_index': idx})` per index (token fetched once, reuse via a private `_post_with_token` variant or accept 5 page GETs; prefer fetching the token once).

**4.3 Index history**
- [ ] `parse_index_history_cse(df_xlsx) -> list[dict]` with `DATE` (`datetime.date`), `TOTAL_TRADE` (int), `TOTAL_VOLUME` (int), `VALUE_MN`, `MARKET_CAP_MN` (both `/1e6`), then `CASPI, CSE30, CSCX, CSE50, CSI`; newest first.
- [ ] `get_index_history_df(market='CSE', start_date, end_date)`: default `end = today`, `start = today - 30 days` (DSE default is a rolling ~30 days).

**4.4 Tests**
- [ ] `test_cse_current_indices` (5 rows, 4 columns, values from JSON fixtures).
- [ ] `test_cse_index_history` (columns, dtypes, newest first).
- [ ] `test_index_invalid_market` and CSE-unsupported methods raise.

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
- [ ] Replace the per-market schema tables under "Output data schema" with one table per method.
- [ ] Update the `PriceData` notes: CSE history depth (2015-11-24+, gaps before mid-2018), 2-year default, chunk cache, `get_day_end_df` for CSE, CLOSEP/DATE semantics for CSE current.
- [ ] `IndexData` section: list CSE indices, which methods support CSE, remove "DSE only" where no longer true.
- [ ] Keep "DSE only" notes for `FundamentalData` and `BlockTradeData`.

**5.2 Version and changelog**
- [ ] `setup.py` and `pyproject.toml` -> `1.3.0`.
- [ ] `CHANGELOG.md` `[1.3.0]` entry (Added / Changed / Breaking for CSE-only callers).

**5.3 Example script**
- [ ] `fetch_csebd_data.py`: `pd.read_excel`, use `HISTORY_FOLDER = 'cse_history_data'`, reuse the single `PriceData` instance so the year cache is hit.

**5.4 Roadmap**
- [ ] Mark CSE price/index parity as shipped; keep CSE fundamentals open.

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
- **Large downloads**: chunk by year, cache per instance, never cache a chunk that includes today.
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
