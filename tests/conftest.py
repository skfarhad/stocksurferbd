import sys
from pathlib import Path

import pytest
from bs4 import BeautifulSoup

# Make the package importable when running pytest from the repo root.
PKG_ROOT = Path(__file__).resolve().parent.parent / "stocksurferbd_pkg"
if str(PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(PKG_ROOT))

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def _load_soup(name):
    html = (FIXTURES / name).read_text(encoding="utf-8")
    return BeautifulSoup(html, "html.parser")


@pytest.fixture
def company_soup():
    return _load_soup("dse_company_aci.html")


@pytest.fixture
def news_soup():
    return _load_soup("dse_news_aci.html")


@pytest.fixture
def market_stats_soup():
    return _load_soup("dse_market_statistics.html")


@pytest.fixture
def index_history_soup():
    return _load_soup("dse_index_history.html")


@pytest.fixture
def index_graph_text():
    return (FIXTURES / "dse_index_graph_cdset.html").read_text(encoding="utf-8")


@pytest.fixture
def home_indices_html():
    return (FIXTURES / "dse_home_indices.html").read_text(encoding="utf-8")


# --------------------------------------------------------------------------- #
# CSE fixtures
# --------------------------------------------------------------------------- #
@pytest.fixture
def cse_historicaldata_page_html():
    return (FIXTURES / "cse_historicaldata_page.html").read_text(encoding="utf-8")


@pytest.fixture
def cse_day_end_bytes():
    """Company day-end download for a single day (all symbols)."""
    return (FIXTURES / "cse_day_end_2026-09-15.xlsx").read_bytes()


@pytest.fixture
def cse_day_end_range_bytes():
    """Company day-end download for 2026-09-10..15, trimmed to 3 symbols."""
    return (FIXTURES / "cse_day_end_range.xlsx").read_bytes()


@pytest.fixture
def cse_current_soup():
    return _load_soup("cse_current_prices.html")


@pytest.fixture
def cse_company_details_html():
    return (FIXTURES / "cse_company_details_aci.html").read_text(encoding="utf-8")


@pytest.fixture
def cse_index_json():
    """Mapping index name -> raw JSON text of the live index summary."""
    return {
        name: (FIXTURES / f"cse_index_summary_{name}.json").read_text(encoding="utf-8")
        for name in ("CASPI", "CSE30", "CSCX", "CSE50", "CSI")
    }


@pytest.fixture
def cse_index_history_bytes():
    return (FIXTURES / "cse_index_history.xlsx").read_bytes()


# --------------------------------------------------------------------------- #
# CSE Shariah (CSI) fixtures
# --------------------------------------------------------------------------- #
@pytest.fixture
def cse_sectorindexdata_html():
    """Trimmed CSE indices page: CSE30/CSE50/CSCX/CASPI cut to 5 rows, CSI complete."""
    return (FIXTURES / "cse_sectorindexdata.html").read_text(encoding="utf-8")


@pytest.fixture
def cse_press_release_list_html():
    """Press-release listing: one non-Shariah item (#333), then #332 and #315."""
    return (FIXTURES / "cse_press_release_list.html").read_text(encoding="utf-8")


@pytest.fixture
def cse_press_release_332_html():
    """'CSE Shariah Index revised' of 2026-05-19: 3 added, 12 excluded, 103 of 383."""
    return (FIXTURES / "cse_press_release_332.html").read_text(encoding="utf-8")


@pytest.fixture
def cse_press_release_273_html():
    """'CSE Shariah Index revised' of 2024-11-13: no additions, 3 excluded, 123 of 384."""
    return (FIXTURES / "cse_press_release_273.html").read_text(encoding="utf-8")
