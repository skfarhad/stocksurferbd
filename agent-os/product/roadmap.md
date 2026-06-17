# Product Roadmap

**`stocksurferbd` is a published library (PyPI `0.1.3`). Core price, fundamentals, and candlestick plotting work today. The roadmap below widens data coverage and hardens the library.**

The library scrapes the public DSE/CSE websites, normalises the tables with `pandas`, and writes `.xlsx` files; it also plots candlesticks via `mplfinance`. Roadmap items are sequenced to broaden the data we expose before investing in packaging/quality polish.

---

## Shipped

1. [x] **Price history (DSE & CSE)** — `PriceData.save_history_data` — daily OHLCV for one symbol from the DSE day-end archive and the CSE 6-month graph data.
2. [x] **Current/live prices (DSE & CSE)** — `PriceData.save_current_data` — one snapshot of all listed symbols.
3. [x] **Company fundamentals (DSE)** — `FundamentalData.save_company_data` — basic info, dividend history, shareholding %, market category/sector, and interim EPS, written to `<symbol>_company_data.xlsx`.
4. [x] **Year-wise financial performance (DSE)** — EPS/NAV/PE/dividend history, written to `<symbol>_financial_data.xlsx`.
5. [x] **Candlestick plotting** — `CandlestickPlot.show_plot` — `mplfinance` wrapper with optional multi-day resampling.
6. [x] **Excel output** — all fetchers persist to `.xlsx` via `pandas` + `openpyxl`.

## Phase 1: Wider fundamental coverage

**Theme: capture the company-page fields we currently skip.**

7. [ ] **Company identity** — full company name, website URL, and registered address from the DSE company page (currently not captured).
8. [ ] **Price-sensitive information / news** — the disclosure/PSI links on the company page.
9. [ ] **Block / spot trades** — block-transaction data (open decision: confirm DSE exposes a scrapeable source).
10. [ ] **Circuit breaker bands** — per-symbol upper/lower circuit limits (the `cbul.php` source is already referenced but commented out).
11. [ ] **CSE fundamentals** — extend `FundamentalData` beyond DSE (currently DSE-only).

## Phase 2: Robustness & data quality

12. [ ] **Resilient parsing** — replace positional table indexing with header-aware lookups so layout changes degrade gracefully.
13. [ ] **Clear errors & retries** — typed exceptions per source, request timeouts, and retry/backoff on transient failures.
14. [ ] **Output options** — return `DataFrame` directly (not only `.xlsx`), and offer CSV/Parquet as alternatives.
15. [ ] **Configurable HTTP** — user-agent, timeout, and TLS-verification options on a session.

## Phase 3: Packaging & developer experience

16. [ ] **Test suite** — unit tests against saved HTML fixtures so parsing is verified without hitting the live sites.
17. [ ] **Type hints + linting** — full type annotations, `flake8`/`black` config, optional `mypy`.
18. [ ] **CI & release** — GitHub Actions for lint/test and automated PyPI publish (`build` + `twine`).
19. [ ] **Docs** — expand README/usage and add API reference for the three public classes.

---

## Prioritization

### Now (Phase 1)
The biggest gap is fundamental coverage — the DSE company page exposes company name, website, address, and PSI/news links that we parse past today. Capturing these is high value and low risk.

### Next (Phase 2)
Make the existing scrapers durable: header-aware parsing and proper error handling so a DSE/CSE layout tweak doesn't silently corrupt output.

### Later (Phase 3)
Tests, typing, and CI keep the library trustworthy as coverage grows.

## Open Decisions
- Whether DSE/CSE expose a stable, scrapeable source for block/spot trades and circuit-band data (gates Phase 1 §9–10).
- Whether to keep `.xlsx` as the default output or move to returning `DataFrame`s with optional file export (Phase 2 §14).
- How much CSE parity to commit to, given CSE's different page structure.
