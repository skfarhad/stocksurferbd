"""Parser/df tests for PriceData against inline DSE/CSE HTML snippets."""

import datetime

import pandas as pd
import pytest
from bs4 import BeautifulSoup

from stocksurferbd import PriceData


# --------------------------------------------------------------------------- #
# Date helpers / archive URL building (backward compatibility)
# --------------------------------------------------------------------------- #
def test_get_history_url_default_is_unchanged():
    # No dates -> endDate = today, NO startDate (preserves prior behaviour).
    url = PriceData().get_history_url()
    today = PriceData.get_date()
    assert url == (
        "https://www.dsebd.org/day_end_archive.php"
        f"?endDate={today}&archive=data"
    )
    assert "startDate" not in url


def test_get_history_url_with_range():
    url = PriceData().get_history_url(
        start_date="2026-06-01", end_date=datetime.date(2026, 6, 22)
    )
    assert "endDate=2026-06-22" in url
    assert "startDate=2026-06-01" in url


def test_get_history_url_end_only_has_no_start():
    url = PriceData().get_history_url(end_date="2026-06-22")
    assert "endDate=2026-06-22" in url
    assert "startDate" not in url


def test_fmt_date_variants():
    assert PriceData._fmt_date(None) is None
    assert PriceData._fmt_date(datetime.date(2026, 6, 22)) == "2026-06-22"
    assert PriceData._fmt_date(datetime.datetime(2026, 6, 22, 9, 30)) == "2026-06-22"
    assert PriceData._fmt_date("2026-06-22") == "2026-06-22"


# --------------------------------------------------------------------------- #
# Client-side date filter (used for CSE history)
# --------------------------------------------------------------------------- #
def _records():
    # Note: day is intentionally not zero-padded, like the CSE graph output.
    return [
        {"DATE": "2026-06-1", "VOLUME": 1},
        {"DATE": "2026-06-10", "VOLUME": 2},
        {"DATE": datetime.date(2026, 6, 20), "VOLUME": 3},
    ]


def test_filter_by_date_no_bounds_returns_all():
    recs = _records()
    assert PriceData._filter_by_date(recs) == recs


def test_filter_by_date_inclusive_bounds():
    out = PriceData._filter_by_date(
        _records(), start_date="2026-06-10", end_date="2026-06-20"
    )
    assert [r["VOLUME"] for r in out] == [2, 3]


def test_filter_by_date_one_sided():
    out = PriceData._filter_by_date(_records(), end_date="2026-06-10")
    assert [r["VOLUME"] for r in out] == [1, 2]


# --------------------------------------------------------------------------- #
# Current prices — DSE (no open price) vs CSE (has open price)
# --------------------------------------------------------------------------- #
DSE_CURRENT_HTML = """
<html><body>
  <h2 class="BodyHead topBodyHead">Latest Share Price On Jun 22, 2026 14:30</h2>
  <table class="table table-bordered background-white shares-table fixedHeader">
    <tr><th>#</th><th>CODE</th><th>LTP</th><th>HIGH</th><th>LOW</th>
        <th>CLOSEP</th><th>YCP</th><th>CHANGE</th><th>TRADE</th>
        <th>VALUE</th><th>VOLUME</th></tr>
    <tr><td>1</td><td>ACI</td><td>200.5</td><td>205.0</td><td>198.0</td>
        <td>201.0</td><td>199.0</td><td>1.00</td><td>1,234</td>
        <td>12.34</td><td>56,789</td></tr>
  </table>
</body></html>
"""

CSE_CURRENT_HTML = """
<html><body>
  <table id="dataTable">
    <tr><th>#</th><th>CODE</th><th>LTP</th><th>OPEN</th><th>HIGH</th>
        <th>LOW</th><th>YCP</th><th>TRADE</th><th>VALUE</th><th>VOLUME</th></tr>
    <tr><td>1</td><td>ACI</td><td>200.5</td><td>199.5</td><td>205.0</td>
        <td>198.0</td><td>199.0</td><td>1,234</td><td>12.34</td>
        <td>56,789</td></tr>
  </table>
</body></html>
"""


def test_parse_current_prices_dse_fields_no_open():
    soup = BeautifulSoup(DSE_CURRENT_HTML, "html.parser")
    records = PriceData().parse_current_prices_dse(soup)
    assert len(records) == 1
    row = records[0]
    # DSE live feed has no open price column.
    assert "OPENP" not in row and "OPEN" not in row
    assert row["TRADING_CODE"] == "ACI"
    assert row["LTP"] == 200.5
    assert row["VOLUME"] == 56789.0
    assert isinstance(row["DATE"], datetime.date)


def test_parse_current_prices_cse_has_open():
    soup = BeautifulSoup(CSE_CURRENT_HTML, "html.parser")
    records = PriceData().parse_current_prices_cse(soup)
    assert len(records) == 1
    row = records[0]
    assert row["OPEN"] == 199.5
    assert row["TRADING_CODE"] == "ACI"
    assert row["VOLUME"] == 56789.0


# --------------------------------------------------------------------------- #
# Day-end archive parsing (all instruments, with open price)
# --------------------------------------------------------------------------- #
DSE_DAY_END_HTML = """
<html><body>
  <table class="table table-bordered background-white shares-table fixedHeader">
    <thead><tr><th>#</th><th>DATE</th><th>CODE</th><th>LTP</th><th>HIGH</th>
        <th>LOW</th><th>OPENP</th><th>CLOSEP</th><th>YCP</th><th>TRADE</th>
        <th>VALUE</th><th>VOLUME</th></tr></thead>
    <tbody>
      <tr><td>1</td><td>2026-06-22</td><td>ACI</td><td>200.5</td><td>205.0</td>
          <td>198.0</td><td>199.5</td><td>201.0</td><td>199.0</td>
          <td>1,234</td><td>12.34</td><td>56,789</td></tr>
      <tr><td>2</td><td>2026-06-22</td><td>BEXIMCO</td><td>110.0</td><td>112.0</td>
          <td>108.0</td><td>109.0</td><td>111.0</td><td>108.5</td>
          <td>2,000</td><td>22.00</td><td>200,000</td></tr>
    </tbody>
  </table>
</body></html>
"""


def test_parse_day_end_archive_has_open_for_all():
    soup = BeautifulSoup(DSE_DAY_END_HTML, "html.parser")
    records = PriceData().parse_day_end_archive(soup)
    assert len(records) == 2
    assert {r["TRADING_CODE"] for r in records} == {"ACI", "BEXIMCO"}
    aci = next(r for r in records if r["TRADING_CODE"] == "ACI")
    assert aci["OPENP"] == 199.5
    assert aci["VOLUME"] == 56789.0


def test_parse_day_end_archive_missing_table_returns_empty():
    # Before market close / non-trading day: no table -> empty, not a crash.
    soup = BeautifulSoup("<html><body>no data yet</body></html>", "html.parser")
    assert PriceData().parse_day_end_archive(soup) == []


def test_parse_day_end_archive_table_without_tbody_returns_empty():
    html = ('<table class="table table-bordered background-white '
            'shares-table fixedHeader"><tr><th>DATE</th></tr></table>')
    soup = BeautifulSoup(html, "html.parser")
    assert PriceData().parse_day_end_archive(soup) == []


# --------------------------------------------------------------------------- #
# Market validation (must raise before any network call)
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("call", [
    lambda ld: ld.get_current_price_df(market="NYSE"),
    lambda ld: ld.get_price_history_df("ACI", market="NYSE"),
    lambda ld: ld.get_day_end_df(market="NYSE"),
])
def test_invalid_market_raises(call):
    with pytest.raises(IOError):
        call(PriceData())
