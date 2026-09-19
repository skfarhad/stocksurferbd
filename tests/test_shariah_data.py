"""Parser and API tests for ShariahData against saved CSE HTML fixtures."""

import datetime

import pandas as pd
import pytest

from stocksurferbd import ShariahData, FetchError, ParseError


LIST_URL = ShariahData.SOURCES["CSE"]["list_url"]
REVISION_URL = ShariahData.SOURCES["CSE"]["revision_url"]
RELEASE_URL = "https://www.cse.com.bd/media/press_release/332"


def _fake_get(loader, pages, failing=()):
    """Patch ``loader._get`` to serve fixture text by URL (no network)."""
    class Resp:
        def __init__(self, text):
            self.text = text

        def raise_for_status(self):
            pass

    def fake(url):
        if url in failing:
            import requests
            raise requests.ConnectionError(f"offline: {url}")
        if url not in pages:
            raise AssertionError(f"unexpected URL fetched: {url}")
        return Resp(pages[url])

    loader._get = fake
    return loader


@pytest.fixture
def cse_loader(cse_sectorindexdata_html, cse_press_release_list_html,
               cse_press_release_332_html):
    return _fake_get(ShariahData(), {
        LIST_URL: cse_sectorindexdata_html,
        REVISION_URL: cse_press_release_list_html,
        RELEASE_URL: cse_press_release_332_html,
    })


# --------------------------------------------------------------------------- #
# Constituent table
# --------------------------------------------------------------------------- #
def test_parse_constituents_cse(cse_sectorindexdata_html):
    as_of, codes = ShariahData.parse_constituents_cse(cse_sectorindexdata_html)
    assert as_of == datetime.date(2026, 9, 19)
    assert len(codes) == 103
    assert codes[0] == "AAMRANET" and codes[-1] == "ZAHEENSPIN"
    assert len(set(codes)) == len(codes)
    assert all(c == c.upper() and c.strip() == c for c in codes)


def test_parse_constituents_cse_ignores_other_tables(cse_sectorindexdata_html):
    # The fixture also holds CSE30/CSE50/CSCX/CASPI tables (5 rows each) and a
    # sector table dated April 22, 2026; only the CSI table must be read.
    as_of, codes = ShariahData.parse_constituents_cse(cse_sectorindexdata_html)
    assert as_of == datetime.date(2026, 9, 19)
    assert "GP" not in codes                     # CASPI/CSCX member, not CSI
    # Selecting another index by title works the same way.
    _, cse30 = ShariahData.parse_constituents_cse(cse_sectorindexdata_html, index="CSE 30")
    assert len(cse30) == 5


def test_parse_constituents_cse_missing_table():
    with pytest.raises(ParseError):
        ShariahData.parse_constituents_cse("<html><table><tr><th>Other</th></tr></table></html>")


@pytest.mark.parametrize("title", [
    "CSI Share by Company Name",                     # no " on <date>"
    "CSI Share by Company Name on Someday Soon",     # unparseable date
])
def test_parse_constituents_cse_title_without_date(title):
    html = (f'<table><thead><tr><th>{title}</th></tr></thead>'
            '<tbody><tr><td>1</td><td>ABC</td></tr></tbody></table>')
    with pytest.raises(ParseError):
        ShariahData.parse_constituents_cse(html)


def test_parse_constituents_cse_empty_table():
    # Tables without a <th> are skipped; a titled table with no code rows fails.
    html = ('<table><tr><td>no header here</td></tr></table>'
            '<table><thead><tr><th>CSI Share by Company Name on May 1, 2026</th></tr>'
            '<tr><th>SL.</th><th>STOCK CODE</th></tr></thead>'
            '<tbody><tr><td>only one cell</td></tr></tbody></table>')
    with pytest.raises(ParseError, match="no rows"):
        ShariahData.parse_constituents_cse(html)


# --------------------------------------------------------------------------- #
# Press-release listing and body
# --------------------------------------------------------------------------- #
def test_find_latest_revision_url_cse(cse_press_release_list_html):
    # First item (#333) is not a Shariah release; #332 must be chosen over #315.
    assert ShariahData.find_latest_revision_url_cse(cse_press_release_list_html) == RELEASE_URL


def test_find_latest_revision_url_cse_none():
    assert ShariahData.find_latest_revision_url_cse(
        '<div class="media_list_title"><a href="x">Other news</a></div>'
    ) is None


def test_parse_revision_cse_332(cse_press_release_332_html):
    rev = ShariahData.parse_revision_cse(cse_press_release_332_html)
    assert rev["revised_date"] == datetime.date(2026, 5, 19)
    assert rev["effective_date"] == datetime.date(2026, 6, 3)
    assert rev["added"] == [
        "ASIATIC LABORATORIES LIMITED",
        "CVO PETROCHEMICAL REFINERY PLC",
        "SAIHAM TEXTILE MILLS LTD",
    ]
    assert len(rev["excluded"]) == 12
    assert "GRAMEENPHONE LIMITED" in rev["excluded"]
    assert rev["excluded"][-1] == "SAIHAM COTTON MILLS LTD"     # after ", and"
    assert len(rev["selected"]) == 103 == rev["selected_count"]
    assert rev["total_listed"] == 383
    assert rev["selected"][0] == "AAMRA NETWORKS LIMITED"
    assert rev["selected"][-1] == "ZAHEEN SPINNING PLC"        # footer stripped
    # Names containing "and" are not split.
    assert "DOREEN POWER GENERATIONS AND SYSTEMS LIMITED" in rev["excluded"]
    assert "TITAS GAS TRANSMISSION AND DISTRIBUTION PLC" in rev["selected"]


def test_parse_revision_cse_273_no_additions(cse_press_release_273_html):
    rev = ShariahData.parse_revision_cse(cse_press_release_273_html)
    assert rev["revised_date"] == datetime.date(2024, 11, 13)
    assert rev["effective_date"] == datetime.date(2024, 11, 25)
    assert rev["added"] == []
    assert rev["excluded"] == [
        "Heidelberg Cement Bangladesh Ltd",
        "Regent Textile Mills Limited",
        "Ratanpur Steel Re-Rolling Mills Limited",
    ]
    assert len(rev["selected"]) == 123 == rev["selected_count"]
    assert rev["total_listed"] == 384
    assert rev["selected"][0] == "aamra Networks Limited"       # "These are-aamra"


def test_parse_revision_cse_footer_without_for_detail():
    # Release #315 wording: no "For detail" line; the contact name follows the
    # list directly and must not become a company.
    html = ('<div class="media_list_short_details"><p>Dhaka, December 07, 2025: '
            'The new index will be effective from 18 December, 2025. '
            'The new 1 company which has been included is HEIDELBERG MATERIALS '
            'BANGLADESH PLC. On the other hand, 2 companies i.e., A LTD and B PLC '
            'were excluded from the previous list. In the revised CSE Shariah Index, '
            '3 listed companies out of 384 listed Companies have been selected. '
            'These are- KOHINOOR CHEMICAL CO. (BD) LTD, WALTON HI-TECH INDUSTRIES PLC, '
            'and ZAHEEN SPINNING PLC. Tania Begum Assistant Manager Chittagong Stock '
            'Exchange PLC Mobile: 01760745736</p></div>')
    rev = ShariahData.parse_revision_cse(html)
    assert rev["effective_date"] == datetime.date(2025, 12, 18)
    assert rev["added"] == ["HEIDELBERG MATERIALS BANGLADESH PLC"]
    assert rev["excluded"] == ["A LTD", "B PLC"]
    assert rev["selected"] == [
        "KOHINOOR CHEMICAL CO. (BD) LTD",
        "WALTON HI-TECH INDUSTRIES PLC",
        "ZAHEEN SPINNING PLC",
    ]


def test_parse_revision_cse_unmatched_wording_degrades():
    rev = ShariahData.parse_revision_cse(
        '<div class="media_list_short_details">Something else entirely.</div>'
    )
    assert rev["revised_date"] is None and rev["effective_date"] is None
    assert rev["added"] == [] and rev["excluded"] == [] and rev["selected"] == []
    assert rev["selected_count"] is None and rev["total_listed"] is None


def test_parse_revision_cse_missing_block():
    with pytest.raises(ParseError):
        ShariahData.parse_revision_cse("<html><body>no release here</body></html>")


def test_split_names():
    split = ShariahData._split_names
    assert split("A LTD., B PLC. and C LIMITED.") == ["A LTD", "B PLC", "C LIMITED"]
    assert split("A LTD, and B PLC") == ["A LTD", "B PLC"]
    assert split("X AND Y LIMITED") == ["X", "Y LIMITED"]      # single trailing pair
    assert split("") == []


# --------------------------------------------------------------------------- #
# Public API (HTTP monkeypatched)
# --------------------------------------------------------------------------- #
def test_get_shariah_list_df_cse(cse_loader):
    df = cse_loader.get_shariah_list_df()
    assert list(df.columns) == ShariahData.LIST_COLUMNS
    assert len(df) == 103
    assert (df["SOURCE"] == "CSE").all() and (df["INDEX"] == "CSI").all()
    assert df["TRADING_CODE"].iloc[0] == "AAMRANET"
    assert (df["AS_OF_DATE"] == datetime.date(2026, 9, 19)).all()
    assert (df["LIST_REVISED_DATE"] == datetime.date(2026, 5, 19)).all()
    assert (df["LIST_EFFECTIVE_DATE"] == datetime.date(2026, 6, 3)).all()


def test_get_shariah_list_df_source_case_insensitive(cse_loader):
    assert len(cse_loader.get_shariah_list_df(source="cse")) == 103


def test_get_shariah_list_df_cse_revision_unavailable(
        cse_sectorindexdata_html, capsys):
    loader = _fake_get(ShariahData(), {LIST_URL: cse_sectorindexdata_html},
                       failing=(REVISION_URL,))
    df = loader.get_shariah_list_df()
    assert len(df) == 103
    assert df["LIST_REVISED_DATE"].isna().all()
    assert df["LIST_EFFECTIVE_DATE"].isna().all()
    assert "Warning" in capsys.readouterr().out
    # The revision frame is empty but well-formed in the same situation.
    rev = loader.get_shariah_revision_df()
    assert rev.empty and list(rev.columns) == ShariahData.REVISION_COLUMNS


def test_get_shariah_list_df_cse_no_revision_item(cse_sectorindexdata_html, capsys):
    # Listing reachable but without a "Shariah Index revised" item: warn, keep list.
    loader = _fake_get(ShariahData(), {
        LIST_URL: cse_sectorindexdata_html,
        REVISION_URL: '<div class="media_list_title"><a href="x">Other news</a></div>',
    })
    df = loader.get_shariah_list_df()
    assert len(df) == 103 and df["LIST_REVISED_DATE"].isna().all()
    assert "Shariah Index revised" in capsys.readouterr().out


def test_get_shariah_list_df_cse_list_page_down(cse_sectorindexdata_html):
    loader = _fake_get(ShariahData(), {}, failing=(LIST_URL,))
    with pytest.raises(FetchError):
        loader.get_shariah_list_df()


def test_get_shariah_revision_df_cse(cse_loader):
    df = cse_loader.get_shariah_revision_df()
    assert list(df.columns) == ShariahData.REVISION_COLUMNS
    counts = df["CHANGE"].value_counts().to_dict()
    assert counts == {
        ShariahData.CHANGE_ADDED: 3,
        ShariahData.CHANGE_EXCLUDED: 12,
        ShariahData.CHANGE_SELECTED: 103,
    }
    assert df["CHANGE"].tolist()[:3] == [ShariahData.CHANGE_ADDED] * 3   # order kept
    assert (df["LIST_EFFECTIVE_DATE"] == datetime.date(2026, 6, 3)).all()


def test_get_shariah_list_info_cse(cse_loader):
    info = cse_loader.get_shariah_list_info()
    assert info["source"] == "CSE" and info["index"] == "CSI"
    assert "fetcher" not in info
    assert info["constituent_count"] == 103
    assert info["selected_count"] == 103 and info["total_listed"] == 383
    assert info["as_of_date"] == datetime.date(2026, 9, 19)
    assert info["list_revised_date"] == datetime.date(2026, 5, 19)
    assert info["list_effective_date"] == datetime.date(2026, 6, 3)
    assert len(info["added"]) == 3 and len(info["excluded"]) == 12
    assert info["revision_announcement_url"] == RELEASE_URL
    assert info["access"] == "free" and info["list_url"] == LIST_URL


def test_save_shariah_list_and_revision(cse_loader, tmp_path):
    cse_loader.save_shariah_list(file_path=str(tmp_path), file_name="list.xlsx")
    cse_loader.save_shariah_revision(file_path=str(tmp_path), file_name="rev.xlsx")
    saved = pd.read_excel(tmp_path / "list.xlsx")
    assert list(saved.columns) == ShariahData.LIST_COLUMNS and len(saved) == 103
    assert len(pd.read_excel(tmp_path / "rev.xlsx")) == 118


# --------------------------------------------------------------------------- #
# Registry
# --------------------------------------------------------------------------- #
def test_list_sources():
    df = ShariahData.list_sources()
    assert list(df.columns) == ShariahData.SOURCES_COLUMNS
    assert df["SOURCE"].tolist() == ["CSE", "DSE"]
    assert df["AVAILABLE"].tolist() == [True, False]
    assert df.set_index("SOURCE").loc["DSE", "ACCESS"] == "paid"


def test_unavailable_source_dse():
    with pytest.raises(IOError) as exc:
        ShariahData().get_shariah_list_df(source="DSE")
    msg = str(exc.value)
    assert "paid" in msg and "source='CSE'" in msg


@pytest.mark.parametrize("call", [
    lambda ld: ld.get_shariah_list_df(source="NYSE"),
    lambda ld: ld.get_shariah_revision_df(source="NYSE"),
    lambda ld: ld.get_shariah_list_info(source="NYSE"),
])
def test_unknown_source_raises(call):
    with pytest.raises(ValueError) as exc:
        call(ShariahData())
    assert "CSE, DSE" in str(exc.value)


def test_registry_entries_are_complete():
    required = {"market", "index", "list_url", "revision_url", "provider",
                "screening", "review_cycle", "access", "notes", "fetcher"}
    for name, entry in ShariahData.SOURCES.items():
        assert set(entry) == required, name
        if entry["fetcher"] is not None:
            assert callable(getattr(ShariahData, entry["fetcher"])), name
