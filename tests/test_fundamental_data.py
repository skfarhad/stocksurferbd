"""Parser tests for FundamentalData against saved DSE HTML fixtures."""

from stocksurferbd import FundamentalData


def test_parse_company_meta(company_soup):
    meta = FundamentalData.parse_company_meta(company_soup)
    assert meta["company_name"] == "Advanced Chemical Industries PLC"
    assert meta["website"] == "http://www.aci-bd.com"
    assert "Tejgaon" in meta["address"]
    assert meta["financial_statement_link"].startswith("http")
    assert meta["price_sensitive_info_link"].startswith("http")


def test_parse_company_meta_never_raises_on_blank():
    from bs4 import BeautifulSoup
    soup = BeautifulSoup("<html><body>nothing here</body></html>", "html.parser")
    meta = FundamentalData.parse_company_meta(soup)
    # Missing fields fall back to '-' instead of raising.
    assert meta["company_name"] == "-"
    assert meta["website"] == "-"


def test_append_company_backward_compatible(company_soup):
    dict_company, _ = FundamentalData.parse_company_data_rows(company_soup, "ACI")

    df_old = FundamentalData.append_company(
        dict_company["company_info"], dict_company["fin_interim_info"], "ACI"
    )
    meta = FundamentalData.parse_company_meta(company_soup)
    df_new = FundamentalData.append_company(
        dict_company["company_info"], dict_company["fin_interim_info"], "ACI", meta=meta
    )

    # Existing behaviour preserved, new columns purely additive at the end.
    assert df_old.columns[0] == "symbol"
    assert len(df_new.columns) == len(df_old.columns) + len(meta)
    assert list(df_new.columns[: len(df_old.columns)]) == list(df_old.columns)
    assert df_new.iloc[0]["company_name"] == "Advanced Chemical Industries PLC"


def test_parse_news_rows(news_soup):
    records = FundamentalData.parse_news_rows(news_soup, "ACI")
    assert len(records) == 79
    first = records[0]
    assert set(first.keys()) == {"symbol", "date", "title", "news"}
    assert first["symbol"] == "ACI"
    assert all(r["date"] for r in records)


def test_parse_news_rows_no_table():
    from bs4 import BeautifulSoup
    soup = BeautifulSoup("<html><body>no news</body></html>", "html.parser")
    assert FundamentalData.parse_news_rows(soup, "ACI") == []
