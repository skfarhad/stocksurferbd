# Product Mission

**`stocksurferbd` — an open-source Python library for downloading Dhaka (DSE) and Chittagong (CSE) stock market data and plotting it. Published on [PyPI](https://pypi.org/project/stocksurferbd/).**

## Vision
Be the simplest, most reliable way for Bangladeshi investors, analysts, and developers to get DSE/CSE market data into Python — so anyone can build their own analysis without scraping the exchange websites by hand.

## Mission
The library wraps the public DSE and CSE websites behind a small, stable Python API. It turns the exchanges' HTML tables into clean `pandas` data and Excel files, and provides an easy candlestick charting helper on top of `mplfinance`. It is a **data-access and plotting toolkit**, not an analysis, scoring, or trading product — those are left to the user who consumes the data.

## Values
- **Small and focused** — three public classes (`PriceData`, `FundamentalData`, `CandlestickPlot`), no framework, no database, no server.
- **Public data only** — scrapes the same pages a browser would; respects the source sites.
- **Boring and dependable** — pinned dependencies, predictable Excel/`DataFrame` output, easy to install with one `pip install`.
- **Easy to start** — every feature is a few lines of code, documented with copy-paste examples in the README.

## Target Users
- **Retail and individual investors** in Bangladesh who want their own data instead of broker panels.
- **Analysts and researchers** building fundamental/technical studies of DSE/CSE listings.
- **Python developers** who need DSE/CSE price and fundamentals as a building block in a larger app or notebook.

## What the library does today
- **Price history** — daily OHLCV history for a single symbol (DSE day-end archive; CSE 6-month graph data).
- **Current/live prices** — one snapshot of all listed symbols for DSE or CSE.
- **Fundamentals** — per-company fundamentals and year-wise financial performance from the DSE company page (capital, face value, market lot, dividend history, shareholding %, EPS/NAV/PE).
- **Charting** — candlestick plots (optionally resampled to multi-day steps) via a thin wrapper over `mplfinance`.
- **Output** — everything saved as `.xlsx` via `pandas` + `openpyxl`; charts rendered with `matplotlib`.

## What it is not
- Not a trading bot, signal generator, or scoring engine.
- Not a hosted service or API — it is an importable library run locally.
- Not a guaranteed feed — it depends on the layout of the public DSE/CSE pages and breaks if those change.

## Success Metrics
- **Reliability** — fetchers keep working against the live DSE/CSE pages; breakage is caught and fixed quickly.
- **Coverage** — breadth of data fields exposed (price, fundamentals, and planned additions like company name/website/news/block trades).
- **Ease of use** — minimal lines of code per task; clear errors when a symbol or source is unavailable.
- **Adoption** — PyPI installs and GitHub usage.
