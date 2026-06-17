# Tech Stack

> `stocksurferbd` is a small, dependency-light Python library. No web framework, database, or services — it scrapes the public DSE/CSE sites, normalises the data with `pandas`, writes `.xlsx`, and plots candlesticks with `mplfinance`. Versions are pinned in `requirements.txt` and `stocksurferbd_pkg/setup.py`.

## Runtime

| Component | Technology | Purpose |
|-----------|------------|---------|
| Language | Python 3.10+ | Core language (`python_requires=">=3.10"`) |
| HTTP | requests 2.32.3 | Fetching DSE/CSE pages |
| HTML parsing | beautifulsoup4 4.9.3 | Extracting tables from page HTML |
| Data | pandas 2.2.2 | Tabular normalisation and Excel I/O |
| Excel | openpyxl 3.1.5 | `.xlsx` writing engine for pandas |
| Dates | python-dateutil | Parsing dates from page text |
| Charts | matplotlib 3.9.2 | Rendering backend |
| Candlesticks | mplfinance 0.12.x | Candlestick/volume plotting wrapper |
| Indicators | pyti 0.2.2, tapy 1.9.1 | Technical-indicator overlays for plots |

## Package layout

| Path | Purpose |
|------|---------|
| `stocksurferbd_pkg/stocksurferbd/` | The importable package |
| `price_data_scraper.py` → `PriceData` | Price history + current/live prices (DSE/CSE) |
| `fundamental_data_scraper.py` → `FundamentalData` | Company + financial fundamentals (DSE) |
| `price_plots.py` → `CandlestickPlot` | mplfinance candlestick wrapper |
| `stocksurferbd_pkg/setup.py` | Packaging metadata (name, version, deps) |
| `fetch_*.py`, `plot_price_data.py` (repo root) | Example/driver scripts |

## Public API

| Class | Key methods |
|-------|-------------|
| `PriceData` | `save_history_data(symbol, file_name, market)`, `save_current_data(file_name, market)` |
| `FundamentalData` | `save_company_data(symbol, path)` |
| `CandlestickPlot` | `__init__(csv_path, symbol)`, `show_plot(data_n, resample, step)` |

## Data sources (public DSE/CSE pages)

| Source | URL pattern |
|--------|-------------|
| DSE day-end archive (history) | `dsebd.org/day_end_archive.php` |
| DSE live prices | `dsebd.org/latest_share_price_scroll_l.php` |
| DSE company fundamentals | `dsebd.org/displayCompany.php?name=<symbol>` |
| DSE circuit breaker (planned) | `dsebd.org/cbul.php` |
| CSE history | `cse.com.bd/company/company_graph_6m/` |
| CSE current price | `cse.com.bd/market/current_price` |

## Output

- **Excel** — `.xlsx` files written via `pandas.DataFrame.to_excel` (openpyxl engine).
- **Charts** — `matplotlib`/`mplfinance` figures shown interactively.

## Build & publish

| Tool | Purpose |
|------|---------|
| wheel | Building the distribution |
| twine | Uploading to PyPI |
| setuptools | `setup.py sdist bdist_wheel` |

```
python setup.py sdist bdist_wheel
twine upload dist/*
```

## Distribution

- **PyPI**: [`stocksurferbd`](https://pypi.org/project/stocksurferbd/)
- **Source**: https://github.com/skfarhad/stocksurferbd
- **License**: MIT
