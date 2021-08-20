#!/usr/bin/env python

__author__ = "Sk Farhad"
__copyright__ = "Copyright (c) 2021 The Python Packaging Authority"


import os
import csv

from bs4 import BeautifulSoup
import requests
import datetime
from dateutil import parser
import urllib.parse as parse_url


class PriceData(object):

    HISTORY_URL_DSE = "https://www.dsebd.org/day_end_archive.php?endDate=<date>&archive=data"
    HISTORY_URL_CSE = "https://www.cse.com.bd/company/company_graph_6m/"
    CURRENT_PRICE_URL_DSE = 'https://www.dsebd.org/dseX_share.php'
    CURRENT_PRICE_URL_CSE = 'https://www.cse.com.bd/market/current_price'

    @staticmethod
    def get_date():
        return str(datetime.datetime.now().date())

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

    def get_history_url(self):
        cur_date = self.get_date()
        return self.HISTORY_URL_DSE.replace('<date>', cur_date)

    def parse_price_history_dse(self, soup):
        dict_list = []
        stock_table = soup.find(
            "table",
            attrs={
                "class": "table table-bordered background-white shares-table fixedHeader"
            }
        )
        table_rows = stock_table.find("tbody").find_all("tr")
        for row in table_rows:
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

    def parse_current_prices_dse(self, soup):
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
                "class": "table table-bordered background-white shares-table"
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
            })
        return dict_list

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
        resp = requests.get(
            full_url
        )

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

    def save_history_csv(self, symbol, csv_path='', file_name='history_data.csv', market='DSE'):
        if market == 'DSE':
            full_url = self.get_history_url() + "&inst=" + parse_url.quote(symbol)
            target_page = requests.get(full_url)
            bs_data = BeautifulSoup(target_page.text, 'html.parser')
            history_list = self. parse_price_history_dse(bs_data)
            full_path = os.path.join(csv_path, file_name)

        elif market == 'CSE':
            history_list = self.parse_price_history_cse(symbol)
            full_path = os.path.join(csv_path, file_name)
        else:
            raise IOError('Invalid Stock Market! Possible values are- CSE, DSE')
        self.save_csv(dict_list=history_list, csv_path=full_path)

    def save_current_csv(self, csv_path='', file_name='current_data.csv', market='DSE'):
        if market == 'DSE':
            target_page = requests.get(self.CURRENT_PRICE_URL_DSE)
            bs_data = BeautifulSoup(target_page.text, 'html.parser')
            current_data = self.parse_current_prices_dse(bs_data)
            full_path = os.path.join(csv_path, file_name)
        elif market == 'CSE':
            target_page = requests.get(self.CURRENT_PRICE_URL_CSE)
            bs_data = BeautifulSoup(target_page.text, 'html.parser')
            current_data = self.parse_current_prices_cse(bs_data)
            full_path = os.path.join(csv_path, file_name)
        else:
            raise IOError('Invalid Stock Market! Possible values are- CSE, DSE')
        self.save_csv(dict_list=current_data, csv_path=full_path)

