"""Parser tests for IndexData against saved DSE HTML/graph fixtures."""

import datetime

import pandas as pd
import pytest
from bs4 import BeautifulSoup

from stocksurferbd import IndexData


# --------------------------------------------------------------------------- #
# Day-wise history (DSEX / DSES / DS30 / DGEN)
# --------------------------------------------------------------------------- #
def test_parse_index_history(index_history_soup):
    records = IndexData.parse_index_history(index_history_soup)
    assert len(records) == 30

    first = records[0]
    assert set(first) == set(IndexData._HISTORY_COLUMNS)
    assert isinstance(first["DATE"], datetime.date)
    assert isinstance(first["DSEX"], float)
    # Dates should be descending (newest first), matching DSE's ordering.
    dates = [r["DATE"] for r in records]
    assert dates == sorted(dates, reverse=True)


def test_index_history_df_dtypes(index_history_soup):
    df = pd.DataFrame(IndexData.parse_index_history(index_history_soup))
    assert df.shape == (30, 9)
    assert df["DSEX"].dtype == "float64"
    # DGEN is legacy and blank in recent rows -> all missing.
    assert df["DGEN"].isna().all()


def test_parse_index_history_missing_table():
    soup = BeautifulSoup("<html><body>no table here</body></html>", "html.parser")
    with pytest.raises(ValueError):
        IndexData.parse_index_history(soup)


def test_find_history_table_skips_decoy():
    # A "record high" decoy table (Date but no DSEX header) must be ignored,
    # and the real day-wise table selected instead.
    html = """
    <html><body>
      <table><tr><th>Particulars</th><th>Values</th><th>Date</th></tr>
             <tr><td>DSEX Index</td><td>7367</td><td>10-10-2021</td></tr></table>
      <table>
        <tr><th>Date</th><th>Total Trade</th><th>Total Volume</th>
            <th>Total Value</th><th>Market Cap</th>
            <th>DSEX Index</th><th>DSES Index</th><th>DS30 Index</th>
            <th>DGEN Index</th></tr>
        <tr><td>18-06-2026</td><td>273343</td><td>438328313</td>
            <td>11972.115</td><td>6934408.044</td>
            <td>5661.38328</td><td>1150.46627</td><td>2143.12038</td>
            <td>-</td></tr>
      </table>
    </body></html>
    """
    records = IndexData.parse_index_history(BeautifulSoup(html, "html.parser"))
    assert len(records) == 1
    assert records[0]["DSEX"] == 5661.38328
    assert records[0]["DGEN"] is None


# --------------------------------------------------------------------------- #
# Graph history (CDSET / DS30 by month-count)
# --------------------------------------------------------------------------- #
def test_parse_index_graph_cdset(index_graph_text):
    records = IndexData.parse_index_graph(index_graph_text, "CDSET")
    assert len(records) > 0
    first = records[0]
    assert first["INDEX"] == "CDSET"
    assert isinstance(first["DATE"], datetime.date)
    assert isinstance(first["POINTS"], float)
    # Series is chronological (oldest first) in the graph payload.
    dates = [r["DATE"] for r in records]
    assert dates == sorted(dates)


def test_graph_rejects_unsupported_index():
    with pytest.raises(ValueError):
        IndexData().parse_index_graph_dse("DSEX", months=12)


# --------------------------------------------------------------------------- #
# Live snapshot (DSEX / DSES / DS30 / CDSET)
# --------------------------------------------------------------------------- #
def test_parse_current_indices(home_indices_html):
    records = IndexData.parse_current_indices(home_indices_html)
    by_name = {r["INDEX"]: r for r in records}

    # All four indices present, deduped to one row each.
    assert set(by_name) == set(IndexData.SUPPORTED_INDICES)
    assert len(records) == 4

    for name in ("DSEX", "DSES", "DS30"):
        assert isinstance(by_name[name]["POINTS"], float)
        assert by_name[name]["CHANGE"] is not None

    # CDSET comes from the intraday JS tail: point only, no change.
    assert isinstance(by_name["CDSET"]["POINTS"], float)
    assert by_name["CDSET"]["CHANGE"] is None


# --------------------------------------------------------------------------- #
# Intraday ticks (incl. CDSET)
# --------------------------------------------------------------------------- #
def test_parse_intraday_cdset(home_indices_html):
    records = IndexData.parse_intraday(home_indices_html, "CDSET")
    assert len(records) > 0
    first = records[0]
    assert first["INDEX"] == "CDSET"
    assert isinstance(first["POINTS"], float)
    # DATETIME is the raw "YYYY-MM-DD HH:MM" string from the JS series.
    assert len(first["DATETIME"]) == 16


def test_parse_intraday_unknown_index():
    with pytest.raises(ValueError):
        IndexData.parse_intraday("", "NOTANINDEX")


# --------------------------------------------------------------------------- #
# Market validation
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("call", [
    lambda ld: ld.get_index_history_df(market="NYSE"),
    lambda ld: ld.get_index_graph_df(market="NYSE"),
    lambda ld: ld.get_current_indices_df(market="NYSE"),
    lambda ld: ld.get_intraday_df(market="NYSE"),
])
def test_invalid_market_raises(call):
    with pytest.raises(IOError):
        call(IndexData())
