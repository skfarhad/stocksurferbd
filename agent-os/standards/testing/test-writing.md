# Testing Standards

Testing patterns for `stocksurferbd`. The hard, breakage-prone part is **HTML parsing**, so the highest-value tests run the parsers against *saved HTML fixtures* — no live network needed.

---

## General Principles

- **Test the parsers, not the network.** Save real DSE/CSE pages once as fixtures and assert the parsers turn them into the expected rows/columns. This is what actually breaks when the sites change.
- **Don't hit live sites in tests.** Mock `requests.get` (or inject a session) so the suite is fast and deterministic, and doesn't depend on the exchange being up.
- **Test behaviour, not internals.** Assert on the returned `DataFrame`/`list[dict]` shape and values, not on private steps.
- **Cover the failure modes.** Missing table → clear `ParseError`; bad market code → `IOError`; `'--'`/empty cells normalised correctly.

---

## Suggested Layout

```
stocksurferbd_pkg/
└── stocksurferbd/
    ├── price_data_scraper.py
    ├── fundamental_data_scraper.py
    └── price_plots.py
tests/
├── conftest.py                  # shared fixtures, fixture-loading helpers
├── fixtures/
│   ├── dse_company_aci.html     # saved displayCompany.php page
│   ├── dse_current_prices.html  # saved latest_share_price page
│   ├── dse_history_aci.html
│   └── cse_current_prices.html
├── test_price_data.py
├── test_fundamental_data.py
└── test_price_plots.py
```

---

## Loading HTML Fixtures

```python
# conftest.py
import pytest
from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures"

@pytest.fixture
def dse_company_html():
    return (FIXTURES / "dse_company_aci.html").read_text(encoding="utf-8")
```

---

## Parser Tests (against fixtures)

```python
# test_fundamental_data.py
from bs4 import BeautifulSoup
from stocksurferbd import FundamentalData

def test_parses_company_rows(dse_company_html):
    soup = BeautifulSoup(dse_company_html, "html.parser")
    company, fin_perf = FundamentalData.parse_company_data_rows(soup, "ACI")

    assert company["symbol"] == "ACI"
    assert company["company_info"]["market_cap"]          # present, non-empty
    assert fin_perf["fin_perf_info"]                       # financial table parsed

def test_missing_table_raises_parse_error():
    soup = BeautifulSoup("<html><body>no tables</body></html>", "html.parser")
    with pytest.raises(Exception):                          # ParseError once introduced
        FundamentalData.parse_company_data_rows(soup, "ACI")
```

```python
# test_price_data.py
from stocksurferbd import PriceData

def test_invalid_market_raises():
    with pytest.raises(IOError):
        PriceData().save_current_data(market="NYSE")

def test_parse_float_handles_commas_and_dashes():
    assert PriceData.parse_float("1,234.50") == 1234.50
    assert PriceData.parse_float("--") == 0.0
```

---

## Mocking HTTP

Mock at the `requests` boundary so no real request is made:

```python
from unittest.mock import patch

def test_current_data_uses_dse_url(dse_current_html, tmp_path):
    with patch("stocksurferbd.price_data_scraper.requests.get") as mock_get:
        mock_get.return_value.text = dse_current_html
        PriceData().save_current_data(
            file_path=str(tmp_path), file_name="out.xlsx", market="DSE"
        )
        assert (tmp_path / "out.xlsx").exists()
```

(Better still: refactor fetching into an injectable helper/session so tests pass a fake instead of patching.)

---

## Plotting Tests

- Use a non-interactive matplotlib backend (`matplotlib.use("Agg")`) so tests don't open windows.
- Assert that `show_plot` runs without error on a small fixture DataFrame and respects `data_n` / `resample` / `step`; pixel-perfect image assertions aren't worth the maintenance.

---

## Running Tests

```bash
pip install -r requirements.txt pytest
pytest
pytest --cov=stocksurferbd        # if pytest-cov is installed
```

Refresh the HTML fixtures whenever the DSE/CSE pages change — a failing parser test is the early-warning that the live scraper is about to break.
