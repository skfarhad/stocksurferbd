# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/), and the project follows
[Semantic Versioning](https://semver.org/).

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

[1.1.0]: https://github.com/skfarhad/stocksurferbd/releases/tag/v1.1.0
[1.0.0]: https://github.com/skfarhad/stocksurferbd/releases/tag/v1.0.0
