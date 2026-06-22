#!/usr/bin/env python

__author__ = "Sk Farhad"
__copyright__ = "Copyright (c) 2021 The Python Packaging Authority"

import os
import csv

from bs4 import BeautifulSoup
import pandas as pd
import datetime
from dateutil import parser
import urllib.parse as parse_url

from .utils import HttpScraper


class PriceData(HttpScraper):
    HISTORY_URL_DSE = "https://www.dsebd.org/day_end_archive.php?endDate=<date>&archive=data"
    HISTORY_URL_CSE = "https://www.cse.com.bd/company/company_graph_6m/"
    CURRENT_PRICE_URL_DSE = 'https://www.dsebd.org/latest_share_price_scroll_l.php'
    CURRENT_PRICE_URL_CSE = 'https://www.cse.com.bd/market/current_price'
    CKT_BREAKER_URL_DSE = 'https://www.dsebd.org/cbul.php'

    @staticmethod
    def get_date():
        return str(datetime.datetime.now().date())

    @staticmethod
    def _fmt_date(value):
        """Normalise a date input to the ``YYYY-MM-DD`` the form expects.

        Accepts ``None`` (-> ``None``), ``date``/``datetime`` objects, or any
        parseable string.
        """
        if value is None:
            return None
        if isinstance(value, (datetime.date, datetime.datetime)):
            return value.strftime("%Y-%m-%d")
        return parser.parse(str(value)).strftime("%Y-%m-%d")

    @classmethod
    def _filter_by_date(cls, records, start_date=None, end_date=None):
        """Inclusive ``DATE`` range filter for sources without a date query.

        Used for CSE history, whose graph endpoint always returns a fixed
        window. ``records`` is a list of dicts with a ``DATE`` key; either
        bound may be ``None``.
        """
        start = cls._fmt_date(start_date)
        end = cls._fmt_date(end_date)
        if start is None and end is None:
            return records
        start_d = parser.parse(start).date() if start else None
        end_d = parser.parse(end).date() if end else None
        result = []
        for rec in records:
            value = rec['DATE']
            day = value if isinstance(value, datetime.date) \
                else parser.parse(str(value)).date()
            if start_d and day < start_d:
                continue
            if end_d and day > end_d:
                continue
            result.append(rec)
        return result

    @staticmethod
    def parse_float(str_val):
        new_val = str_val.replace(
            ',', ''
        ).replace('--', '0')
        return float(new_val)

    @staticmethod
    def parse_int(str_val):
        new_val = str_val.replace(
            ',', ''
        ).replace('--', '0')
        return int(new_val)

    @staticmethod
    def save_csv(dict_list, csv_path):
        keys = dict_list[0].keys()
        with open(csv_path, 'w+', newline='') as output_file:
            dict_writer = csv.DictWriter(output_file, keys)
            dict_writer.writeheader()
            dict_writer.writerows(dict_list)

    @staticmethod
    def save_excel(dict_list, csv_path):
        df = pd.DataFrame(dict_list)
        df.to_excel(csv_path)

    def get_history_url(self, start_date=None, end_date=None):
        """Build the DSE day-end archive URL.

        With no arguments this returns the historical default (``endDate`` =
        today, no ``startDate``), preserving the previous behaviour. Pass
        ``start_date`` and/or ``end_date`` (``date``/``datetime`` or any
        parseable string) to bound the range; a ``startDate`` is only added to
        the query when ``start_date`` is given.
        """
        end = self._fmt_date(end_date) or self.get_date()
        url = self.HISTORY_URL_DSE.replace('<date>', end)
        start = self._fmt_date(start_date)
        if start:
            url += "&startDate=" + start
        return url

    def parse_day_end_archive(self, soup):
        """Parse the DSE day-end archive table (shared by history & day-end).

        The archive serves the same column layout whether queried for one
        ``inst`` over a date range or for ``All Instrument`` on a single day.
        Returns ``[]`` when the table is absent (e.g. an unfinished/future date
        before market close, or a non-trading day) instead of raising.
        """
        stock_table = soup.find(
            "table",
            attrs={
                "class": "table table-bordered background-white shares-table fixedHeader"
            }
        )
        tbody = stock_table.find("tbody") if stock_table else None
        if tbody is None:
            return []
        dict_list = []
        for row in tbody.find_all("tr"):
            row_data = ["".join(td.get_text().split()) for td in row.find_all("td")]
            try:
                dict_list.append({
                    'DATE': row_data[1],
                    'TRADING_CODE': row_data[2],
                    'LTP': self.parse_float(row_data[3]),
                    'HIGH': self.parse_float(row_data[4]),
                    'LOW': self.parse_float(row_data[5]),
                    'OPENP': self.parse_float(row_data[6]),
                    'CLOSEP': self.parse_float(row_data[7]),
                    'YCP': self.parse_float(row_data[8]),
                    'TRADE': self.parse_float(row_data[9].replace(',', '')),
                    'VALUE_MN': self.parse_float(row_data[10]),
                    'VOLUME': self.parse_float(row_data[11].replace(',', '')),
                })
            except Exception as e:
                print(str(e))
        return dict_list

    def parse_price_history_dse(self, symbol, start_date=None, end_date=None):
        full_url = self.get_history_url(
            start_date=start_date, end_date=end_date
        ) + "&inst=" + parse_url.quote(symbol)
        target_page = self._get(full_url)
        return self.parse_day_end_archive(
            BeautifulSoup(target_page.text, 'html.parser')
        )

    def parse_day_end_dse(self, date=None):
        """All-instrument day-end rows for a single ``date`` (default today)."""
        day = self._fmt_date(date) or self.get_date()
        full_url = self.get_history_url(
            start_date=day, end_date=day
        ) + "&inst=" + parse_url.quote("All Instrument")
        target_page = self._get(full_url)
        return self.parse_day_end_archive(
            BeautifulSoup(target_page.text, 'html.parser')
        )

    def parse_current_prices_dse(self, soup, fp_dict=None):
        dict_list = []
        table_header = soup.find(
            'h2',
            attrs={
                'class': "BodyHead topBodyHead"
            }
        )
        # print(table_header)
        date_txt = " ".join(table_header.text.split(
            'On'
        )[1].split(
            'at'
        )[0].strip().split(

        ))
        latest_trading_date = parser.parse(date_txt).date()
        stock_table = soup.find(
            "table",
            attrs={
                "class": "table table-bordered background-white shares-table fixedHeader"
            }
        )
        table_rows = stock_table.find_all("tr")
        # print(type(table_rows))
        for row in table_rows:
            th_values = ["".join(th.get_text().split()) for th in row.find_all("th")]
            td_values = ["".join(td.get_text().split()) for td in row.find_all("td")]
            if len(th_values):
                # print(th_values)
                continue
            # print(td_values)
            dict_list.append({
                'DATE': latest_trading_date,
                'TRADING_CODE': td_values[1],
                'LTP': self.parse_float(td_values[2]),
                'HIGH': self.parse_float(td_values[3]),
                'LOW': self.parse_float(td_values[4]),
                'CLOSEP': self.parse_float(td_values[5]),
                'YCP': self.parse_float(td_values[6]),
                '% CHANGE': self.parse_float(td_values[7]),
                'TRADE': self.parse_float(td_values[8]),
                'VALUE_MN': self.parse_float(td_values[9]),
                'VOLUME': self.parse_float(td_values[10]),
                # 'PUB_FP': fp_dict[td_values[1]][0] if fp_dict else 0,
            })
        return dict_list

    def parse_floor_prices_dse(self, soup):
        fp_price_dict = {}
        price_table = soup.find(
            "table",
            attrs={
                "class": "table table-bordered background-white text-center"
            }
        )
        table_rows = price_table.find_all("tr")
        # print(type(table_rows))
        for row in table_rows:
            th_values = ["".join(th.get_text().split()) for th in row.find_all("th")]
            td_values = ["".join(td.get_text().split()) for td in row.find_all("td")]
            if len(th_values):
                # print(th_values)
                continue
            fp_price_dict.update({
                td_values[1]: (
                    self.parse_float(td_values[5]) if td_values[5] != '-' else 0,
                    self.parse_float(td_values[8]) if td_values[8] != '-' else 0
                )
            })
        return fp_price_dict

    def parse_current_prices_cse(self, soup):
        dict_list = []

        date_txt = str(datetime.datetime.now().date())
        latest_trading_date = parser.parse(date_txt).date()
        stock_table = soup.find(
            "table",
            attrs={
                "id": "dataTable"
            }
        )
        table_rows = stock_table.find_all("tr")
        # print(type(table_rows))
        for row in table_rows:
            th_values = ["".join(th.get_text().split()) for th in row.find_all("th")]
            td_values = ["".join(td.get_text().split()) for td in row.find_all("td")]
            if len(th_values):
                # print(th_values)
                continue
            dict_list.append({
                'DATE': latest_trading_date,
                'TRADING_CODE': td_values[1],
                'LTP': self.parse_float(td_values[2]),
                'OPEN': self.parse_float(td_values[3]),
                'HIGH': self.parse_float(td_values[4]),
                'LOW': self.parse_float(td_values[5]),
                'YCP': self.parse_float(td_values[6]),
                'TRADE': self.parse_float(td_values[7]),
                'VALUE_MN': self.parse_float(td_values[8]),
                'VOLUME': self.parse_float(td_values[9]),
            })
        return dict_list

    def parse_price_history_cse(self, symbol):
        full_url = self.HISTORY_URL_CSE + symbol
        resp = self._get(full_url)

        split1 = resp.text.split("volumeData.push([date, round(volume)]);")[1]
        split2 = split1.split("$(document).ready(function () {")[0]

        lines = split2.replace(
            "date = new Date(", ""
        ).replace(
            "ohlcData.push([date, ", ""
        ).replace(
            "volumeData.push([date, ", ""
        ).replace(
            "]);", ""
        ).replace(
            ");", ""
        ).replace(
            "\n\n\n", "\n"
        ).replace(
            "\n\n", "\n"
        ).replace(
            " ", ""
        ).lstrip().rstrip()

        records = lines.split("\n\n")
        dict_list = []

        for rec in records:
            items = rec.split("\n")
            date_comps = items[0].split(",")
            new_month = str(int(date_comps[1]) + 1)
            if len(new_month) < 2:
                new_month = "0" + new_month
            date_comps[1] = new_month
            date = "-".join(date_comps)
            volume = int(items[2])
            high, low, open_p, close_p = (float(x) for x in items[1].split(','))
            dict_list.append({
                'DATE': date,
                'TRADING_CODE': symbol,
                'LTP': 0,
                'OPENP': open_p,
                'HIGH': high,
                'LOW': low,
                'CLOSEP': close_p,
                'YCP': 0,
                '% CHANGE': 0,
                'TRADE': 0,
                'VALUE_MN': 0,
                'VOLUME': volume,
            })

        return dict_list

    def get_price_history_df(self, symbol, market='DSE', start_date=None, end_date=None):
        """Daily OHLCV history for one symbol as a DataFrame.

        With no dates, returns the source's default window (unchanged
        behaviour). Pass ``start_date`` and/or ``end_date`` (``date``/
        ``datetime`` or any parseable string) to bound the range. For DSE the
        bounds are sent to the day-end archive natively; for CSE, whose graph
        endpoint serves a fixed ~6-month window, they are applied client-side.

        DSE rows include the open price (``OPENP``); the CSE rows include
        ``OPENP`` as well.
        """
        if market == 'DSE':
            records = self.parse_price_history_dse(
                symbol, start_date=start_date, end_date=end_date
            )
        elif market == 'CSE':
            records = self._filter_by_date(
                self.parse_price_history_cse(symbol), start_date, end_date
            )
        else:
            raise IOError('Invalid Stock Market! Possible values are- CSE, DSE')
        return pd.DataFrame(records)

    def get_day_end_df(self, date=None, market='DSE'):
        """Day-end OHLCV for **all** instruments on a single ``date``.

        Sourced from the DSE day-end archive, so unlike
        :meth:`get_current_price_df` this **includes the open price**
        (``OPENP``). ``date`` defaults to today and accepts a ``date``/
        ``datetime`` or any parseable string.

        The archive is only populated after the session closes and end-of-day
        processing runs, so calling this for the current day **before market
        close** (or for a non-trading day) returns an **empty DataFrame** —
        use :meth:`get_current_price_df` for live intraday prices.
        """
        if market != 'DSE':
            raise IOError("Only 'DSE' is supported for day-end data.")
        return pd.DataFrame(self.parse_day_end_dse(date))

    def get_current_price_df(self, market='DSE'):
        """Snapshot of all listed symbols' latest prices as a DataFrame.

        Note: the DSE live feed does not publish an open price, so the DSE
        snapshot has no ``OPENP`` column. For DSE open prices use
        :meth:`get_price_history_df` (the day-end archive includes ``OPENP``).
        """
        if market == 'DSE':
            page = self._get(self.CURRENT_PRICE_URL_DSE)
            records = self.parse_current_prices_dse(
                BeautifulSoup(page.text, 'html.parser')
            )
        elif market == 'CSE':
            page = self._get(self.CURRENT_PRICE_URL_CSE)
            records = self.parse_current_prices_cse(
                BeautifulSoup(page.text, 'html.parser')
            )
        else:
            raise IOError('Invalid Stock Market! Possible values are- CSE, DSE')
        return pd.DataFrame(records)

    def save_history_data(self, symbol, file_path='', file_name='history_data.csv',
                          market='DSE', start_date=None, end_date=None):
        rows = self.get_price_history_df(
            symbol, market=market, start_date=start_date, end_date=end_date
        ).to_dict('records')
        self.save_excel(dict_list=rows, csv_path=os.path.join(file_path, file_name))

    def save_current_data(self, file_path='', file_name='dsebd_current_data.csv', market='DSE'):
        rows = self.get_current_price_df(market=market).to_dict('records')
        self.save_excel(dict_list=rows, csv_path=os.path.join(file_path, file_name))
