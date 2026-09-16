# Feature Requirements: CSE/DSE Uniform Data

## Overview
`stocksurferbd` fetches DSE and CSE data, but the CSE side is thin and does not
match the DSE shape. The user's application consumes the **DSE format**, so the
goal is to make every CSE result (price history, current prices, day-end, index
data) come back with the same columns, order, types and semantics as the DSE
equivalent, while leaving DSE output unchanged.

Gap analysis performed on 2026-09-16 against the live CSE site:

- CSE price history comes from a 6-month chart endpoint. Its `OPENP` column is
  actually the previous close (verified 115/115 rows), `YCP` is written as 0,
  and `LTP`, `% CHANGE`, `TRADE`, `VALUE_MN` are hard-coded 0.
- CSE current prices use `OPEN` (not `OPENP`), lack `CLOSEP` and `% CHANGE`,
  and stamp `DATE` with the machine clock instead of the exchange trading date.
- `get_day_end_df`, `IndexData`, `FundamentalData`, `BlockTradeData` all raise
  for `market='CSE'`.
- CSE publishes a POST/xlsx day-end download (`market/data_download_company`)
  with `trade_date, company_name, company_code, no_of_trades, volume, turnover,
  prev_close_price, close_price, open_price, last_traded_price, day_high,
  day_low`; data verified back to at least Jan 2021. This is a superset of the
  DSE day-end row.
- CSE indices: live JSON at `home/load__index_summary/` (value, change,
  percentage_change for CASPI, CSE30, CSCX, CSE50, CSI) and history xlsx at
  `market/data_download_index` (per-index value/change/pct plus turnover,
  volume, no_of_trades, market_capital, gainers, losers).
- All useful CSE endpoints are POSTs requiring a `csrf_cse_token` scraped from
  the page plus the session cookie.

## User Stories
- As a platform developer, I want `PriceData.get_price_history_df(sym, market='CSE')`
  to return exactly the DSE columns with real values, so that my DSE-based code
  works for CSE without branching.
- As a platform developer, I want `PriceData.get_current_price_df(market='CSE')`
  to return the DSE current-price columns, so that both markets load into the
  same table.
- As a platform developer, I want `PriceData.get_day_end_df(date, market='CSE')`
  to work, so that I can backfill all CSE symbols for a day the same way I do
  for DSE.
- As a platform developer, I want `IndexData` methods to accept `market='CSE'`
  and return the DSE-shaped frames, so that index dashboards work for both.
- As an existing DSE user, I want DSE output to stay byte-for-byte the same.

## Functional Requirements
1. **Canonical price-history schema (DSE):**
   `DATE, TRADING_CODE, LTP, HIGH, LOW, OPENP, CLOSEP, YCP, TRADE, VALUE_MN, VOLUME`.
   CSE history must return exactly these columns in this order, with real
   values from the CSE day-end download (no zero placeholders). Drop the extra
   CSE `% CHANGE` column.
2. **Canonical current-price schema (DSE):**
   `DATE, TRADING_CODE, LTP, HIGH, LOW, CLOSEP, YCP, % CHANGE, TRADE, VALUE_MN, VOLUME`.
   CSE current must return these columns in this order. `CLOSEP` for CSE live
   rows follows the DSE live-feed semantics (DSE publishes it as the running
   close; for CSE use LTP when the session is open). `% CHANGE` is computed as
   `(LTP - YCP) / YCP * 100` rounded to 2 dp, matching DSE's published value.
   The CSE `OPEN` column is dropped from the default output (DSE has none).
3. **Day-end for CSE:** `get_day_end_df(date, market='CSE')` returns the
   history schema for all symbols on that date, sourced from
   `data_download_company` with `from == to == date`.
4. **Real history depth:** CSE `start_date`/`end_date` are sent to the download
   endpoint natively; with no dates, default to the same window the current
   6-month behaviour gives (approx. 6 months) so callers see no regression.
5. **Value units:** CSE `turnover` is in Taka; convert to millions for
   `VALUE_MN` (2 dp). `TRADE` and `VOLUME` remain floats as in DSE rows.
6. **Trading date for CSE current prices:** derive from the exchange, not the
   machine clock (the company-details page or the latest day-end date), so a
   weekend/holiday call gets the last trading date like DSE does.
7. **`DATE` type parity:** whatever type DSE emits per method today, CSE emits
   the same (history: `YYYY-MM-DD` string; current: `datetime.date`).
8. **CSRF-aware POST helper** in `HttpScraper`: fetch page, extract
   `csrf_cse_token`, POST with session cookie and Referer.
9. **IndexData for CSE:**
   - `get_current_indices_df(market='CSE')` -> `INDEX, POINTS, CHANGE, PCT_CHANGE`
     for CASPI, CSE30, CSCX, CSE50, CSI via the JSON endpoint.
   - `get_index_history_df(market='CSE', start_date, end_date)` ->
     `DATE, TOTAL_TRADE, TOTAL_VOLUME, VALUE_MN, MARKET_CAP_MN` followed by one
     column per CSE index (`CASPI, CSE30, CSCX, CSE50, CSI`). The leading
     market-total columns match DSE exactly; index columns are necessarily
     market-specific, mirroring how DSE emits `DSEX, DSES, DS30, DGEN`.
   - `get_intraday_df` / `get_index_graph_df` keep raising a clear error for
     CSE (no source found).
10. **Excel/CSV writers unchanged.** `save_*` wrappers keep writing the same
    files; only the DataFrame content changes for CSE.
11. **README** documents a single schema per method rather than one per market,
    and lists CSE index names and the CSE history depth.
12. **Fix `fetch_csebd_data.py`** to read the xlsx it writes.

## Non-Functional Requirements
- Performance: one HTTP round-trip (plus one token fetch per session) per
  history/day-end call; the download for a 3-month all-symbol range is ~28k
  rows and parses in well under a second with pandas/openpyxl.
- Security: no credentials; CSRF token is public page state. `verify`,
  `session`, `timeout` options must keep working.
- Compatibility: DSE outputs unchanged (regression tests on existing fixtures).
  Existing CSE callers get the same column names as DSE; this is a deliberate
  breaking change for CSE-only callers and is called out in the changelog with
  a version bump (1.2.0).
- Dependencies: add `openpyxl` (already the pandas Excel engine used by
  `to_excel`) to install requirements explicitly.

## Acceptance Criteria
- [ ] `list(get_price_history_df('ACI', market='CSE').columns) == list(get_price_history_df('ACI', market='DSE').columns)`
- [ ] CSE history `OPENP` equals the exchange `open_price`, `YCP` equals
      `prev_close_price`, and no column is a constant zero placeholder.
- [ ] `list(get_current_price_df(market='CSE').columns) == list(get_current_price_df(market='DSE').columns)`
- [ ] `get_day_end_df('2026-09-15', market='CSE')` returns >300 rows with the
      history schema.
- [ ] `get_price_history_df('ACI', market='CSE', start_date='2021-01-03', end_date='2021-01-07')`
      returns 5 rows (data older than the 6-month chart window).
- [ ] `get_current_indices_df(market='CSE')` returns 5 rows with
      `INDEX, POINTS, CHANGE, PCT_CHANGE`.
- [ ] `get_index_history_df(market='CSE', start_date=..., end_date=...)`
      returns the DSE leading columns plus one column per CSE index.
- [ ] All existing DSE tests pass unchanged; new CSE parser tests run offline
      against saved fixtures (xlsx + HTML + JSON) under `tests/fixtures/`.
- [ ] README schema tables show one column set per method.

## Out of Scope
- `FundamentalData` and `BlockTradeData` for CSE (CSE has no EPS/NAV/dividend
  history or news page, and no block-trade page was found).
- CSE intraday index ticks and per-index graph history (no source found).
- CSE SME / ATB / G-Sec boards (separate pages; main board only, like DSE).
- Sector indices (CSE-only concept; can be a later addition).
- Adding a `MARKET` column (would change the DSE shape the application uses).

## Notes
DSE format is canonical because the user's application already consumes it.
