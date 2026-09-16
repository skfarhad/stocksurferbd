# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/), and the project follows
[Semantic Versioning](https://semver.org/).

## [1.3.0] - 2026-09-16

### Added
- **CSE output now matches the DSE schema exactly** (columns, order, dtypes,
  newest-first ordering) for `get_price_history_df`, `get_current_price_df`
  and `get_day_end_df`, so DSE-based code works for `market='CSE'` unchanged.
- **CSE price history is re-sourced** from the exchange's day-end download.
  `OPENP`, `LTP`, `YCP`, `TRADE` and `VALUE_MN` now carry real values (the
  old chart source put the *previous close* in `OPENP` and zeros in the rest)
  and the archive reaches back to **2015-11-24** instead of ~6 months. With no
  dates the full archive is returned.
- `get_day_end_df(date, market='CSE')` for all CSE symbols on one day.
- **`get_day_end_range_df` / `save_day_end_range_data`** (both markets): all
  symbols over a date range, with `symbols`, `chunk` (`'year'`/`'month'`),
  `progress` (bool or callback) and `use_cache` options. This is the efficient
  way to pull many CSE symbols.
- `PriceData(cache_dir=...)`: optional on-disk cache of closed CSE download
  chunks; chunks are also cached per instance, so a loop over symbols downloads
  each period once.
- **`IndexData` supports CSE**: `get_current_indices_df` / `get_index_history_df`
  for CASPI, CSE30, CSCX, CSE50 and CSI with the DSE frame shapes.
- `HttpScraper.post_with_csrf` / `get_csrf_token` and `read_xlsx_bytes`
  helpers; `StockSurferError`, `FetchError`, `ParseError` exceptions
  (exported from the package).
- Offline CSE fixtures and tests (`tests/fixtures/cse_*`).

### Changed
- CSE `get_current_price_df` takes `DATE` and `CLOSEP` from the exchange's
  same-day day-end download instead of the machine clock / a missing column;
  `% CHANGE` is computed as the absolute change `LTP - YCP`, which is what the
  DSE live feed publishes under that name.
- Market arguments are validated against `VALID_MARKETS` (case-insensitive) on
  every market-taking method.
- `fetch_csebd_data.py` pulls the CSE archive once with
  `get_day_end_range_df` and splits it per symbol.

### Removed (breaking for CSE-only callers)
- The CSE `OPEN` column in current prices and the `% CHANGE` column in CSE
  history; both markets now share the DSE columns.
- `PriceData.parse_price_history_cse`, `PriceData._filter_by_date` and
  `HISTORY_URL_CSE` (the 6-month chart scraper).

### Notes
- DSE output is unchanged.

## [1.2.0] - 2026-06-23

### Added
- **DataFrame accessors on `PriceData`**, bringing it in line with the other
  loaders (`FundamentalData`, `BlockTradeData`, `IndexData`):
  - `get_price_history_df(symbol, market, start_date=None, end_date=None)` —
    daily OHLCV for one symbol. New `start_date` / `end_date` bounds (default
    `start_date=None`, `end_date=today`) are sent to the DSE day-end archive
    natively and applied client-side for CSE. DSE history includes the open
    price (`OPENP`).
  - `get_current_price_df(market)` — snapshot of all listed symbols.
  - `get_day_end_df(date=None, market='DSE')` — day-end OHLCV for **all**
    instruments on a single day, sourced from the DSE day-end archive (so it
    **includes the open price**, unlike the live current feed). Returns an
    empty DataFrame before market close / on non-trading days.
- **Tests** — parser/df tests for `PriceData` with inline DSE/CSE HTML.

### Changed
- `save_history_data` / `save_current_data` are now thin wrappers over the new
  df methods (file output unchanged). `save_history_data` gained optional
  `start_date` / `end_date` parameters.
- `get_history_url` accepts optional `start_date` / `end_date`; called with no
  arguments it returns the previous URL unchanged (backward compatible).
- The day-end archive row parser was extracted to `parse_day_end_archive`
  (shared by history and day-end) and hardened to return `[]` when the table is
  absent, instead of raising `AttributeError`.

## [1.1.0] - 2026-06-20

### Added
- **Market index data** via the new `IndexData` class *(DSE only)*. Scrapes the
  aggregate index values (DSEX, DSES, DS30, DGEN, CDSET), complementing the
  per-company scrapers:
  - `get_index_history_df` / `save_index_history` — day-wise index table.
    Returns the rolling ~30 days by default, or the **full archive (~2010
    onward)** when `start_date` / `end_date` are supplied. Index availability
    varies by launch date (DSEX/DS30 from Jan 2013, DSES from Jan 2014, DGEN is
    legacy/pre-2013).
  - `get_index_graph_df` / `save_index_graph` — per-index daily close series by
    month-count. The only source of **CDSET history (back to ~2016)**; also
    serves DS30.
  - `get_current_indices_df` / `save_current_indices` — live snapshot of all
    four indices, including CDSET.
  - `get_intraday_df` / `save_intraday` — current-day per-minute ticks for any
    index, including CDSET.
- **Tests** — parser tests for `IndexData` with committed DSE HTML/graph
  fixtures.

### Changed
- `HttpScraper` gained a `_post` helper (used by the index archive endpoint).
- README expanded with `IndexData` usage, coverage table, and output schema.

### Notes
- Backward compatible: existing classes, methods, and signatures are unchanged.
- Index data is **DSE only**; CSE indices (e.g. CDSET on CSE) are not supported.

## [1.0.0] - 2026-06-17

### Added
- **Company identity & disclosure links** on `<symbol>_company_data.xlsx`:
  `company_name`, `website`, `address`, `financial_statement_link`,
  `price_sensitive_info_link`. *(DSE only)*
- **Company news feed** — `FundamentalData.get_news_df` / `save_news_data`,
  rolling N-year window (default 2). *(DSE only)*
- **Block trade data** via the new `BlockTradeData` class *(DSE only)*:
  - `get_block_trades_df` / `save_block_trade_data` — current-day block
    transactions for all symbols from the DSE market statistics page (DSE has
    no historical block-trade archive; run daily to build history).
  - `get_block_trade_news_df` / `save_block_trade_news_data` — per-company
    block-market related news as a historical proxy.
- **Configurable HTTP** — `verify`, `session`, and `timeout` arguments on all
  loaders (handles DSE's incomplete TLS chain in some environments).
- **Test suite** — pytest tests with committed DSE HTML fixtures.

### Changed
- Shared `parse_float` / `parse_int` helpers extracted to `utils.py`.
- README expanded with usage for the new methods and a full output-data schema.

### Fixed
- README CandlestickPlot example used the wrong keyword (`csv_path` →
  `file_path`).

### Notes
- Backward compatible: existing methods and signatures are unchanged; the new
  company columns are appended at the end of the existing file.
- Price history and current/live prices remain available for **both DSE and
  CSE**. Fundamentals, news, and block trades are **DSE only**.

[1.2.0]: https://github.com/skfarhad/stocksurferbd/releases/tag/v1.2.0
[1.1.0]: https://github.com/skfarhad/stocksurferbd/releases/tag/v1.1.0
[1.0.0]: https://github.com/skfarhad/stocksurferbd/releases/tag/v1.0.0
