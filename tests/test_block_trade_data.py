"""Parser tests for BlockTradeData against saved DSE HTML fixtures."""

import pandas as pd
import pytest

from stocksurferbd import BlockTradeData, FundamentalData


def test_parse_block_trades_dse(market_stats_soup):
    records = BlockTradeData.parse_block_trades_dse(market_stats_soup)
    assert len(records) == 54

    first = records[0]
    assert first["DATE"] == "2026-06-17"
    assert first["TRADING_CODE"] == "ACFL"
    assert first["MAX_PRICE"] == 24.50
    assert first["TRADES"] == 1
    assert first["QUANTITY"] == 75000

    # Codes with special characters must survive parsing.
    codes = [r["TRADING_CODE"] for r in records]
    assert "KAY&QUE" in codes


def test_block_trades_df_dtypes(market_stats_soup):
    records = BlockTradeData.parse_block_trades_dse(market_stats_soup)
    df = pd.DataFrame(records, columns=BlockTradeData.BLOCK_COLUMNS)
    assert df.shape == (54, 7)
    assert df["QUANTITY"].dtype == "int64"
    assert df["MAX_PRICE"].dtype == "float64"


def test_parse_block_trades_missing_section():
    from bs4 import BeautifulSoup
    soup = BeautifulSoup("<html><body>no block data</body></html>", "html.parser")
    with pytest.raises(Exception):
        BlockTradeData.parse_block_trades_dse(soup)


def test_block_trade_news_proxy(monkeypatch, news_soup):
    # Build the news DataFrame the way get_news_df would, from the fixture.
    records = FundamentalData.parse_news_rows(news_soup, "ACI")
    news_df = pd.DataFrame(records, columns=["symbol", "date", "title", "news"])

    monkeypatch.setattr(
        FundamentalData, "get_news_df", lambda self, symbol, years=2: news_df
    )

    block_news = BlockTradeData().get_block_trade_news_df("ACI", years=2)
    assert not block_news.empty
    assert len(block_news) < len(news_df)  # filtered down to block-related items
    haystack = (block_news["title"] + " " + block_news["news"]).str.lower()
    assert haystack.str.contains("block").all()


def test_invalid_market_raises():
    with pytest.raises(IOError):
        BlockTradeData().get_block_trades_df(market="NYSE")
