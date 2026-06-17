#!/usr/bin/env python

__author__ = "Sk Farhad"
__copyright__ = "Copyright (c) 2024 The Python Packaging Authority"

import os
import re

import pandas as pd
from bs4 import BeautifulSoup

from .fundamental_data_scraper import FundamentalData
from .utils import HttpScraper, parse_float, parse_int


class BlockTradeData(HttpScraper):
    """Block-transaction data for the Dhaka Stock Exchange (DSE).

    Two complementary sources:

    1. ``get_block_trades_df`` / ``save_block_trade_data`` - the *current day's*
       actual block transactions (all symbols) parsed from the DSE market
       statistics page. DSE does not publish a historical block-trade archive,
       so run this daily to accumulate history.
    2. ``get_block_trade_news_df`` / ``save_block_trade_news_data`` - a
       per-company historical proxy built from block-market related news
       (e.g. director/sponsor block-market buy declarations) over the last N
       years. These are disclosures, not raw trade tickets.
    """

    MARKET_STATS_URL_DSE = 'https://www.dsebd.org/market-statistics.php'
    BLOCK_KEYWORDS = ('block',)
    VALID_MARKETS = ('DSE',)

    BLOCK_COLUMNS = [
        'DATE', 'TRADING_CODE', 'MAX_PRICE', 'MIN_PRICE',
        'TRADES', 'QUANTITY', 'VALUE_MN',
    ]

    @staticmethod
    def parse_block_trades_dse(soup):
        """Parse the 'PRICES IN BLOCK TRANSACTIONS' section into records.

        The section is whitespace-aligned text with columns:
        Instr Code, Max Price, Min Price, Trades, Quantity, Value(In Mn).
        Returns a list of dicts keyed by ``BLOCK_COLUMNS``. An empty list is a
        valid result (a day with no block trades).
        """
        text = soup.get_text('\n')
        header = re.search(
            r'PRICES IN BLOCK TRANSACTIONS\s*:\s*([0-9-]+)', text
        )
        if header is None:
            raise Exception('Block transactions section not found on page')
        trade_date = header.group(1)

        records = []
        started = False
        for line in text[header.end():].splitlines():
            line = line.strip()
            if not line or line.startswith('='):
                continue
            if line.lower().startswith('instr'):
                started = True
                continue
            if not started:
                continue
            # A data row is: CODE max min trades quantity value. The code may
            # contain special chars (e.g. KAY&QUE); split the 5 numeric columns
            # off the right so the rest is the code. Non-matching lines (footer
            # text, stray separators) are skipped, not treated as table-end.
            parts = line.rsplit(None, 5)
            if len(parts) == 6 and all(re.match(r'^[0-9.,]+$', p) for p in parts[1:]):
                records.append({
                    'DATE': trade_date,
                    'TRADING_CODE': parts[0],
                    'MAX_PRICE': parse_float(parts[1]),
                    'MIN_PRICE': parse_float(parts[2]),
                    'TRADES': parse_int(parts[3]),
                    'QUANTITY': parse_int(parts[4]),
                    'VALUE_MN': parse_float(parts[5]),
                })
        if not started:
            print('Warning: block transactions column header not found; '
                  'page layout may have changed.')
        return records

    def get_block_trades_df(self, market='DSE', symbol=None):
        """Current-day block transactions for all symbols (or one ``symbol``)."""
        if market not in self.VALID_MARKETS:
            raise IOError('Invalid Stock Market! Possible values are- DSE')
        target_page = self._get(self.MARKET_STATS_URL_DSE)
        page_html = BeautifulSoup(target_page.text, 'html.parser')
        records = self.parse_block_trades_dse(page_html)
        df_block = pd.DataFrame(records, columns=self.BLOCK_COLUMNS)
        if symbol is not None and not df_block.empty:
            df_block = df_block[
                df_block['TRADING_CODE'] == symbol
            ].reset_index(drop=True)
        return df_block

    def save_block_trade_data(self, file_path='', file_name='block_trade_data.xlsx',
                              market='DSE', symbol=None):
        block_df = self.get_block_trades_df(market=market, symbol=symbol)
        block_df.to_excel(os.path.join(file_path, file_name), index=False)
        print("Block trade data download completed!")

    def get_block_trade_news_df(self, symbol, years=2):
        """Historical block-market related disclosures for a company.

        Filters the company news feed (last ``years`` years) down to items that
        mention block-market activity. Returns a DataFrame with the same columns
        as the news feed (symbol, date, title, news).
        """
        fundamental = FundamentalData(
            verify=self.verify, session=self.session, timeout=self.timeout
        )
        news_df = fundamental.get_news_df(symbol, years=years)
        if news_df.empty:
            return news_df
        haystack = (
            news_df['title'].fillna('') + ' ' + news_df['news'].fillna('')
        ).str.lower()
        mask = haystack.apply(
            lambda text: any(kw in text for kw in self.BLOCK_KEYWORDS)
        )
        return news_df[mask].reset_index(drop=True)

    def save_block_trade_news_data(self, symbol, path='', years=2):
        news_df = self.get_block_trade_news_df(symbol, years=years)
        if news_df.empty:
            print(f"No block trade news found for {symbol}.")
            return
        news_df.to_excel(
            os.path.join(path, f'{symbol}_block_trade_news.xlsx'), index=False
        )
        print(f"Block trade news download completed for {symbol}!")
