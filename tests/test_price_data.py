"""Parser/df tests for PriceData against inline DSE HTML and saved CSE fixtures."""

import datetime
import io

import pandas as pd
import pytest
from bs4 import BeautifulSoup

from stocksurferbd import PriceData, ParseError


# --------------------------------------------------------------------------- #
# Date helpers / archive URL building (backward compatibility)
# --------------------------------------------------------------------------- #
def test_get_history_url_default_is_unchanged():
    # No dates -> endDate = today, NO startDate (preserves prior behaviour).
    url = PriceData().get_history_url()
    today = PriceData.get_date()
    assert url == (
        "https://old.dsebd.org/day_end_archive.php"
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


def test_parse_current_prices_cse_inline_matches_dse_columns():
    soup = BeautifulSoup(CSE_CURRENT_HTML, "html.parser")
    records = PriceData().parse_current_prices_cse(
        soup, trading_date=datetime.date(2026, 6, 22), close_by_code={"ACI": 200.0}
    )
    assert len(records) == 1
    row = records[0]
    assert list(row) == PriceData.CURRENT_COLUMNS
    assert "OPEN" not in row and "OPENP" not in row      # CSE-only column dropped
    assert row["CLOSEP"] == 200.0                        # from the day-end download
    assert row["% CHANGE"] == round(200.5 - 199.0, 2)    # absolute change, like DSE
    assert row["DATE"] == datetime.date(2026, 6, 22)


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
    lambda ld: ld.get_day_end_range_df("2026-01-01", market="NYSE"),
])
def test_invalid_market_raises(call):
    with pytest.raises(IOError):
        call(PriceData())


# --------------------------------------------------------------------------- #
# CSE: download -> canonical history frame
# --------------------------------------------------------------------------- #
class _Resp:
    def __init__(self, content):
        self.content = content
        self.headers = {"content-type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}


def _cse_loader(monkeypatch, chunk_bytes, **kwargs):
    """PriceData whose CSE downloads return ``chunk_bytes``; records POST ranges."""
    loader = PriceData(**kwargs)
    calls = []

    def fake_post(page_url, action_url, data, token=None):
        calls.append((data["from"], data["to"]))
        return _Resp(chunk_bytes)

    monkeypatch.setattr(loader, "post_with_csrf", fake_post)
    return loader, calls


def test_cse_download_to_history_matches_dse_schema(cse_day_end_range_bytes):
    df = PriceData.cse_download_to_history(pd.read_excel(io.BytesIO(cse_day_end_range_bytes)))
    assert list(df.columns) == PriceData.HISTORY_COLUMNS
    assert df["DATE"].map(type).eq(str).all()                 # DSE archive rows carry strings
    assert all(df[c].dtype == "float64" for c in PriceData.HISTORY_COLUMNS[2:])
    dates = df["DATE"].tolist()
    assert dates == sorted(dates, reverse=True)               # newest first, like DSE


def test_cse_download_to_history_field_mapping(cse_day_end_range_bytes):
    df = PriceData.cse_download_to_history(pd.read_excel(io.BytesIO(cse_day_end_range_bytes)))
    row = df[(df["TRADING_CODE"] == "BRACBANK") & (df["DATE"] == "2026-09-14")].iloc[0]
    # xlsx: prev_close 62.7, close 62.0, open 62.7, ltp 62.0, high 62.1, low 62.0,
    #       trades 8, volume 5650, turnover 350400 Taka
    assert row["OPENP"] == 62.7 and row["CLOSEP"] == 62.0 and row["YCP"] == 62.7
    assert row["LTP"] == 62.0 and row["HIGH"] == 62.1 and row["LOW"] == 62.0
    assert row["TRADE"] == 8.0 and row["VOLUME"] == 5650.0
    assert row["VALUE_MN"] == 0.35                             # Taka -> millions
    # No column is a constant zero placeholder any more.
    assert (df[["LTP", "YCP", "TRADE", "VALUE_MN"]] != 0).any().all()


def test_cse_download_to_history_missing_columns_raises():
    with pytest.raises(ParseError):
        PriceData.cse_download_to_history(pd.DataFrame({"trade_date": ["2026-01-01"]}))


def test_cse_download_to_history_empty():
    empty = pd.DataFrame(columns=list(PriceData._CSE_HISTORY_COLUMN_MAP))
    df = PriceData.cse_download_to_history(empty)
    assert df.empty and list(df.columns) == PriceData.HISTORY_COLUMNS


# --------------------------------------------------------------------------- #
# CSE: chunking
# --------------------------------------------------------------------------- #
def test_cse_year_chunks_are_whole_years_clipped_to_archive():
    chunks = PriceData._cse_chunks("2015-01-01", "2017-03-15", chunk="year")
    assert chunks == [
        (datetime.date(2015, 11, 24), datetime.date(2015, 12, 31)),
        (datetime.date(2016, 1, 1), datetime.date(2016, 12, 31)),
        (datetime.date(2017, 1, 1), datetime.date(2017, 12, 31)),
    ]


def test_cse_month_chunks_cross_year_boundary():
    chunks = PriceData._cse_chunks("2020-11-15", "2021-01-10", chunk="month")
    assert chunks == [
        (datetime.date(2020, 11, 1), datetime.date(2020, 11, 30)),
        (datetime.date(2020, 12, 1), datetime.date(2020, 12, 31)),
        (datetime.date(2021, 1, 1), datetime.date(2021, 1, 31)),
    ]


def test_cse_chunks_before_archive_or_bad_size():
    assert PriceData._cse_chunks("2010-01-01", "2014-12-31") == []
    with pytest.raises(ValueError):
        PriceData._cse_chunks("2020-01-01", "2020-12-31", chunk="week")


def test_cse_current_year_chunk_ends_today():
    today = datetime.date.today()
    (chunk,) = PriceData._cse_chunks(today.replace(month=1, day=1), today)
    assert chunk == (today.replace(month=1, day=1), today)
    assert not PriceData._cse_chunk_is_closed(chunk)


# --------------------------------------------------------------------------- #
# CSE: history / day-end / range via a mocked download
# --------------------------------------------------------------------------- #
def test_cse_history_matches_dse_schema_and_filters_symbol(monkeypatch, cse_day_end_range_bytes):
    loader, calls = _cse_loader(monkeypatch, cse_day_end_range_bytes)
    df = loader.get_price_history_df("aci", market="CSE", start_date="2026-09-10", end_date="2026-09-15")
    assert list(df.columns) == PriceData.HISTORY_COLUMNS
    assert set(df["TRADING_CODE"]) == {"ACI"}
    assert df["DATE"].tolist() == ["2026-09-15", "2026-09-14", "2026-09-13", "2026-09-10"]
    assert calls == [(f"{datetime.date.today().year}-01-01", str(datetime.date.today()))]


def test_cse_history_range_is_inclusive_after_chunk_download(monkeypatch, cse_day_end_range_bytes):
    loader, _ = _cse_loader(monkeypatch, cse_day_end_range_bytes)
    df = loader.get_price_history_df("ACI", market="CSE", start_date="2026-09-13", end_date="2026-09-14")
    assert df["DATE"].tolist() == ["2026-09-14", "2026-09-13"]


def test_cse_history_default_is_full_archive(monkeypatch, cse_day_end_range_bytes):
    loader, calls = _cse_loader(monkeypatch, cse_day_end_range_bytes)
    loader.get_price_history_df("ACI", market="CSE")
    today = datetime.date.today()
    assert calls[0] == ("2015-11-24", "2015-12-31")
    assert calls[-1] == (f"{today.year}-01-01", str(today))
    assert len(calls) == today.year - 2015 + 1


def test_cse_history_chunks_cached_per_instance(monkeypatch, cse_day_end_range_bytes):
    loader, calls = _cse_loader(monkeypatch, cse_day_end_range_bytes)
    loader.get_price_history_df("ACI", market="CSE", start_date="2024-01-01", end_date="2025-12-31")
    loader.get_price_history_df("BRACBANK", market="CSE", start_date="2024-01-01", end_date="2025-12-31")
    assert len(calls) == 2                                    # 2024 and 2025 fetched once
    # The chunk containing today is never cached, so it is fetched again.
    loader.get_day_end_range_df("2025-01-01", market="CSE", progress=False)
    loader.get_day_end_range_df("2025-01-01", market="CSE", progress=False)
    assert calls.count((f"{datetime.date.today().year}-01-01", str(datetime.date.today()))) == 2


def test_cse_disk_cache_roundtrip(monkeypatch, tmp_path, cse_day_end_range_bytes):
    loader, calls = _cse_loader(monkeypatch, cse_day_end_range_bytes, cache_dir=str(tmp_path))
    loader.get_day_end_range_df("2024-01-01", market="CSE", progress=False)
    files = sorted(p.name for p in tmp_path.iterdir())
    assert "cse_day_end_2024-01-01_2024-12-31.pkl" in files
    assert not any(str(datetime.date.today().year) + "-01-01_" in f for f in files)  # current year not written

    second, calls2 = _cse_loader(monkeypatch, cse_day_end_range_bytes, cache_dir=str(tmp_path))
    second.get_day_end_range_df("2024-01-01", end_date="2024-12-31", market="CSE", progress=False)
    assert calls2 == []                                       # served from disk, zero POSTs


def test_cse_day_end_single_day(monkeypatch, cse_day_end_bytes):
    loader, calls = _cse_loader(monkeypatch, cse_day_end_bytes)
    df = loader.get_day_end_df("2026-09-15", market="CSE")
    assert calls == [("2026-09-15", "2026-09-15")]           # one-day request, not a year chunk
    assert list(df.columns) == PriceData.HISTORY_COLUMNS
    assert len(df) > 300 and set(df["DATE"]) == {"2026-09-15"}


def test_cse_day_end_empty_download(monkeypatch):
    empty = pd.DataFrame(columns=list(PriceData._CSE_HISTORY_COLUMN_MAP))
    buf = io.BytesIO(); empty.to_excel(buf, index=False)
    loader, _ = _cse_loader(monkeypatch, buf.getvalue())
    df = loader.get_day_end_df("2026-09-12", market="CSE")
    assert df.empty and list(df.columns) == PriceData.HISTORY_COLUMNS


def test_day_end_range_cse_symbols_filter(monkeypatch, cse_day_end_range_bytes):
    loader, _ = _cse_loader(monkeypatch, cse_day_end_range_bytes)
    df = loader.get_day_end_range_df(
        "2026-09-10", "2026-09-15", market="CSE", symbols=["aci", "BRACBANK"], progress=False
    )
    assert set(df["TRADING_CODE"]) == {"ACI", "BRACBANK"}
    none = loader.get_day_end_range_df("2026-09-10", "2026-09-15", market="CSE", symbols=["NOPE"], progress=False)
    assert none.empty and list(none.columns) == PriceData.HISTORY_COLUMNS


def test_day_end_range_month_chunks(monkeypatch, cse_day_end_range_bytes):
    loader, calls = _cse_loader(monkeypatch, cse_day_end_range_bytes)
    loader.get_day_end_range_df("2025-11-15", "2026-01-10", market="CSE", chunk="month", progress=False)
    assert calls == [("2025-11-01", "2025-11-30"), ("2025-12-01", "2025-12-31"), ("2026-01-01", "2026-01-31")]
    with pytest.raises(ValueError):
        loader.get_day_end_range_df("2025-11-15", market="CSE", chunk="week")


def test_day_end_range_progress(monkeypatch, capsys, cse_day_end_range_bytes):
    loader, _ = _cse_loader(monkeypatch, cse_day_end_range_bytes)
    loader.get_day_end_range_df("2024-01-01", "2024-12-31", market="CSE", progress=False)
    assert capsys.readouterr().out == ""

    seen = []
    loader.get_day_end_range_df("2023-01-01", "2024-12-31", market="CSE", progress=lambda *a: seen.append(a))
    # 2024 is already cached -> only 2023 reports, and total counts network chunks only.
    assert seen == [(datetime.date(2023, 1, 1), datetime.date(2023, 12, 31), 1, 1)]

    loader.get_day_end_range_df("2022-01-01", "2022-12-31", market="CSE")
    assert "CSE download 2022-01-01..2022-12-31 (1/1)" in capsys.readouterr().out


def test_day_end_range_use_cache_false(monkeypatch, tmp_path, cse_day_end_range_bytes):
    loader, calls = _cse_loader(monkeypatch, cse_day_end_range_bytes, cache_dir=str(tmp_path))
    loader.get_day_end_range_df("2024-01-01", "2024-12-31", market="CSE", progress=False)
    loader.get_day_end_range_df("2024-01-01", "2024-12-31", market="CSE", progress=False, use_cache=False)
    assert len(calls) == 2                                    # cache bypassed -> downloaded again
    assert len(loader._cse_chunk_cache) == 1 and len(list(tmp_path.iterdir())) == 1


def test_day_end_range_requires_start_date():
    with pytest.raises(ValueError):
        PriceData().get_day_end_range_df(None, market="CSE")


def test_day_end_range_dse_skips_empty_days(monkeypatch):
    loader = PriceData()
    asked = []

    def fake_parse(day):
        asked.append(str(day))
        if str(day) == "2026-06-22":
            return PriceData().parse_day_end_archive(BeautifulSoup(DSE_DAY_END_HTML, "html.parser"))
        return []

    monkeypatch.setattr(loader, "parse_day_end_dse", fake_parse)
    df = loader.get_day_end_range_df("2026-06-20", "2026-06-22", market="DSE", progress=False, symbols=["ACI"])
    assert asked == ["2026-06-20", "2026-06-21", "2026-06-22"]
    assert list(df.columns) == PriceData.HISTORY_COLUMNS
    assert df["TRADING_CODE"].tolist() == ["ACI"]


# --------------------------------------------------------------------------- #
# CSE: current prices from the saved live page
# --------------------------------------------------------------------------- #
def test_cse_current_matches_dse_schema(cse_current_soup):
    records = PriceData().parse_current_prices_cse(
        cse_current_soup, trading_date=datetime.date(2026, 9, 16), close_by_code={"BRACBANK": 62.9}
    )
    df = pd.DataFrame(records, columns=PriceData.CURRENT_COLUMNS)
    assert list(df.columns) == PriceData.CURRENT_COLUMNS
    assert len(df) == 7 and df["TRADING_CODE"].iloc[0] == "1JANATAMF"
    brac = df[df["TRADING_CODE"] == "BRACBANK"].iloc[0]
    assert brac["CLOSEP"] == 62.9                             # joined from the day-end download
    assert brac["% CHANGE"] == round(63.2 - 62.0, 2)          # absolute change, like DSE
    gp = df[df["TRADING_CODE"] == "GP"].iloc[0]
    assert gp["CLOSEP"] == gp["LTP"] == 240.0                 # fallback when no close is known
    assert isinstance(df["DATE"].iloc[0], datetime.date)


def test_cse_current_missing_table_raises():
    soup = BeautifulSoup("<html><body>nothing</body></html>", "html.parser")
    with pytest.raises(ParseError):
        PriceData().parse_current_prices_cse(soup, trading_date=datetime.date(2026, 9, 16))


def test_cse_current_pct_change_zero_ycp():
    html = """<table id="dataTable"><tr><th>#</th></tr>
      <tr><td>1</td><td>NEWIPO</td><td>12.0</td><td>0</td><td>12.5</td><td>11.5</td>
          <td>0</td><td>10</td><td>0.12</td><td>10,000</td></tr></table>"""
    (row,) = PriceData().parse_current_prices_cse(BeautifulSoup(html, "html.parser"), datetime.date(2026, 9, 16))
    assert row["% CHANGE"] == 12.0 and row["YCP"] == 0.0 and row["VOLUME"] == 10000.0


def test_parse_trading_date_cse(cse_company_details_html):
    assert PriceData.parse_trading_date_cse(cse_company_details_html) == datetime.date(2026, 9, 16)
    assert PriceData.parse_trading_date_cse("<p>Last Trade Date 03 August, 2026</p>") == datetime.date(2026, 8, 3)
    assert PriceData.parse_trading_date_cse("<p>no date here</p>") is None


def test_get_current_price_df_cse_uses_exchange_date_and_closes(monkeypatch, cse_current_soup, cse_day_end_bytes):
    loader = PriceData()
    monkeypatch.setattr(loader, "_get", lambda url: type("R", (), {"text": str(cse_current_soup)})())
    monkeypatch.setattr(loader, "fetch_cse_day_end_chunk",
                        lambda s, e: PriceData.cse_download_to_history(pd.read_excel(io.BytesIO(cse_day_end_bytes))))
    df = loader.get_current_price_df(market="CSE")
    assert list(df.columns) == PriceData.CURRENT_COLUMNS
    assert df["DATE"].unique().tolist() == [datetime.date(2026, 9, 15)]   # from the download, not the clock
    brac = df[df["TRADING_CODE"] == "BRACBANK"].iloc[0]
    assert brac["CLOSEP"] == 62.0                             # close_price of BRACBANK on 2026-09-15


def test_get_current_price_df_cse_falls_back_to_company_page_date(monkeypatch, cse_current_soup, cse_company_details_html):
    loader = PriceData()
    pages = {PriceData.CURRENT_PRICE_URL_CSE: str(cse_current_soup),
             PriceData.COMPANY_DETAILS_URL_CSE + "ACI": cse_company_details_html}
    monkeypatch.setattr(loader, "_get", lambda url: type("R", (), {"text": pages[url]})())
    monkeypatch.setattr(loader, "fetch_cse_day_end_chunk",
                        lambda s, e: pd.DataFrame(columns=PriceData.HISTORY_COLUMNS))
    df = loader.get_current_price_df(market="CSE")
    assert df["DATE"].unique().tolist() == [datetime.date(2026, 9, 16)]
    assert (df["CLOSEP"] == df["LTP"]).all()
