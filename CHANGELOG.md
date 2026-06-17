# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/), and the project follows
[Semantic Versioning](https://semver.org/).

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

[1.0.0]: https://github.com/skfarhad/stocksurferbd/releases/tag/v1.0.0
