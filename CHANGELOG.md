# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/), and the project follows
[Semantic Versioning](https://semver.org/).

## [2.1.0] - 2026-09-19

### Added
- **`ShariahData`**: the Shariah-compliant company list from a named source.
  `get_shariah_list_df` / `save_shariah_list` return one row per constituent
  with `SOURCE, INDEX, TRADING_CODE, AS_OF_DATE, LIST_REVISED_DATE,
  LIST_EFFECTIVE_DATE`; `get_shariah_revision_df` / `save_shariah_revision`
  return the latest revision (`ADDED` / `EXCLUDED` / `SELECTED` company
  names); `get_shariah_list_info` returns counts, dates and provenance.
- **Source registry `ShariahData.SOURCES`** with `list_sources()`. Each entry
  documents URLs, provider, screening methodology, review cycle and access
  status and names its fetcher, so a new source is a registry entry plus one
  fetcher. `CSE` (CSI constituents from the CSE indices page plus the latest
  "CSE Shariah Index revised" press release) is implemented. `DSE` (DSES) is
  registered as unavailable: DSE sells its constituent list, so requesting it
  raises with that explanation and points to `source='CSE'`.
- `fetch_shariah_list.py` example script; `ShariahData` and `IndexData` are
  now also importable from the `stocksurferbd_pkg` shim used by the examples.
- Offline CSE fixtures and 25 new tests (107 total).

## [2.0.0] - 2026-09-16

**CSE data now comes back in the same shape as DSE data.** Code written against
DSE output works for `market='CSE'` with no changes. DSE output is untouched.

### Breaking changes (CSE callers only)
- **CSE price history columns changed** to the DSE set. The CSE-only
  `% CHANGE` column is gone, and the column order now matches DSE:
  `DATE, TRADING_CODE, LTP, HIGH, LOW, OPENP, CLOSEP, YCP, TRADE, VALUE_MN, VOLUME`.
- **CSE current-price columns changed** to the DSE set. The CSE-only `OPEN`
  column is gone and `CLOSEP` / `% CHANGE` are now present:
  `DATE, TRADING_CODE, LTP, HIGH, LOW, CLOSEP, YCP, % CHANGE, TRADE, VALUE_MN, VOLUME`.
  For the open price use `get_price_history_df` or `get_day_end_df`.
- **`PriceData.parse_price_history_cse`, `PriceData._filter_by_date` and
  `PriceData.HISTORY_URL_CSE` were removed** along with the 6-month chart
  scraper they belonged to. Use `get_price_history_df(symbol, market='CSE')`.
- `% CHANGE` is the absolute change `LTP - YCP` for both markets. This is what
  the DSE live feed publishes under that name, verified against 395 live rows.

### Fixed
- **CSE `OPENP` was not the open price.** The old chart source put the
  *previous close* there (confirmed on 115 of 115 consecutive rows). CSE now
  reports the exchange's real open, and `YCP` carries the previous close.
- **CSE `LTP`, `YCP`, `% CHANGE`, `TRADE` and `VALUE_MN` were hard-coded
  zeros** in history rows. All five now carry real values.
- **CSE current-price `DATE` came from the machine clock**, so a weekend or
  holiday call produced a date the exchange never traded. It now comes from the
  exchange's own day-end data, falling back to the last trade date on the site.
- **CSE price history was capped at about 6 months.** It now reaches back to
  2015-11-24, the earliest date the exchange serves (with gaps before mid-2018).

### Added
- **`get_day_end_df(date, market='CSE')`** for all CSE symbols on one day.
- **`get_day_end_range_df` / `save_day_end_range_data`** (both markets): all
  symbols over a date range, with `symbols`, `chunk` (`'year'` or `'month'`),
  `progress` (bool or callback) and `use_cache` options. This is the efficient
  way to pull many CSE symbols, since CSE publishes one spreadsheet covering
  every symbol per date range.
- **`PriceData(cache_dir=...)`**: optional on-disk cache of closed CSE download
  chunks. Chunks are also cached per instance, so a loop over symbols downloads
  each period once instead of once per symbol.
- **`IndexData` supports CSE**: `get_current_indices_df` and
  `get_index_history_df` cover CASPI, CSE30, CSCX, CSE50 and CSI, returning the
  same frame shapes as the DSE equivalents.
- `HttpScraper.get_csrf_token` / `post_with_csrf` and `read_xlsx_bytes` helpers
  for the CSE form endpoints.
- `StockSurferError`, `FetchError` and `ParseError`, exported from the package.
- Offline CSE test fixtures and 44 new tests (82 total, up from 38).

### Changed
- Market arguments are validated against `VALID_MARKETS` case-insensitively on
  every market-taking method.
- `IndexData.get_index_graph_df` and `get_intraday_df` raise a message naming
  the CSE alternative, since CSE publishes no intraday or per-index graph data.
- `fetch_csebd_data.py` pulls the CSE archive once with `get_day_end_range_df`
  and splits it per symbol, instead of one request per symbol.

### Still DSE only
- `FundamentalData` (company data, financials, news) and `BlockTradeData`. CSE
  publishes no EPS/NAV/dividend history, no news feed and no block-trade page.
- `IndexData.get_index_graph_df` and `get_intraday_df`.

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
