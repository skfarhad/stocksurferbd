# stocksurferbd Tech Stack

> A small, dependency-light Python library. No web framework, database, or services. Versions are pinned in `requirements.txt` and `stocksurferbd_pkg/setup.py`.

---

## Runtime Dependencies

| Library | Version | Usage |
|---------|---------|-------|
| requests | 2.32.3 | Fetching DSE/CSE pages |
| beautifulsoup4 | 4.9.3 | Parsing tables out of page HTML |
| pandas | 2.2.2 | Tabular normalisation, Excel I/O |
| openpyxl | 3.1.5 | `.xlsx` writer engine for pandas |
| python-dateutil | (via requests stack) | Parsing dates from page text |
| matplotlib | 3.9.2 | Rendering backend |
| mplfinance | 0.12.x | Candlestick/volume plotting |
| pyti | 0.2.2 | Technical indicators for plots |
| tapy | 1.9.1 | Technical-analysis indicators for plots |

---

## Build & Publish

| Tool | Usage |
|------|-------|
| setuptools | `setup.py sdist bdist_wheel` |
| wheel | Build distributions |
| twine | Upload to PyPI |

```
python setup.py sdist bdist_wheel
twine upload dist/*
```

---

## Package Structure

```
stocksurferbd/                  # repo root
├── requirements.txt            # pinned runtime + build deps
├── README.md                   # usage docs (also the PyPI long description)
├── fetch_*.py, plot_*.py       # example/driver scripts
└── stocksurferbd_pkg/
    ├── setup.py                # packaging metadata
    └── stocksurferbd/          # the importable package
        ├── __init__.py         # exports PriceData, FundamentalData, CandlestickPlot
        ├── price_data_scraper.py
        ├── fundamental_data_scraper.py
        └── price_plots.py
```

---

## Public API

| Class | Methods |
|-------|---------|
| `PriceData` | `save_history_data`, `save_current_data` |
| `FundamentalData` | `save_company_data` |
| `CandlestickPlot` | `show_plot` |

---

## Constraints

- **Python**: `>=3.10`
- **No backend services**: the library runs locally; no DB, no server, no async runtime.
- **Public data only**: scrapes the same DSE/CSE pages a browser would.
- **Output**: `.xlsx` files (pandas + openpyxl) and `matplotlib`/`mplfinance` figures.
