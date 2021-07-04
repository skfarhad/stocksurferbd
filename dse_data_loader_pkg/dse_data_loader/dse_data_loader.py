#!/usr/bin/env python

__author__ = "Sk Farhad"
__copyright__ = "Copyright (c) 2021 The Python Packaging Authority"


import os
import csv

import pandas as pd
from bs4 import BeautifulSoup
import requests
import datetime
from dateutil import parser
import urllib.parse as parse_url


class PriceData(object):

    HISTORY_URL = "https://www.dsebd.org/day_end_archive.php?endDate=<date>&archive=data"
    CURRENT_PRICE_URL = 'https://www.dsebd.org/dseX_share.php'

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
        return self.HISTORY_URL.replace('<date>', cur_date)

    def parse_historical_data_rows(self, soup):
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

    def parse_current_data_rows(self, soup):
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

    def save_history_csv(self, symbol, csv_path='', file_name='history_data.csv'):
        full_url = self.get_history_url() + "&inst=" + parse_url.quote(symbol)
        target_page = requests.get(full_url)
        bs_data = BeautifulSoup(target_page.text, 'html.parser')
        history_list = self. parse_historical_data_rows(bs_data)
        full_path = os.path.join(csv_path, file_name)
        self.save_csv(dict_list=history_list, csv_path=full_path)

    def save_current_csv(self, csv_path='', file_name='current_data.csv'):
        target_page = requests.get(self.CURRENT_PRICE_URL)
        bs_data = BeautifulSoup(target_page.text, 'html.parser')
        current_data = self.parse_current_data_rows(bs_data)
        full_path = os.path.join(csv_path, file_name)
        self.save_csv(dict_list=current_data, csv_path=full_path)


class FundamentalData(object):
    DSE_COMPANY_URL = "http://dsebd.org/displayCompany.php?name="
    CURRENT_PRICE_URL = 'https://www.dsebd.org/dseX_share.php'

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
    def append_company(company_info, fin_interim_info, df_company, symbol):
        company_dict = {
            'symbol': symbol,
            'auth_capital': company_info['basic'][0][0],
            'trade_start': company_info['basic'][0][1],
            'paid_up_capital': company_info['basic'][1][0],
            'instrument_type': company_info['basic'][1][1],
            'face_value': company_info['basic'][2][0],
            'market_lot': company_info['basic'][2][1],
            'ltp': company_info['ltp'],
            'market_cap': company_info['market_cap'],
            'outstanding_share': company_info['basic'][3][0],
            'sector': company_info['basic'][3][1],
            'right_issue': company_info['dividend'][2][0],
            'year_end': company_info['dividend'][3][0],
            'reserve_w_oci': company_info['dividend'][4][0],
            'others_oci': company_info['dividend'][5][0],
            # 'present_st_loan',
            # 'present_lt_loan',
            'cash_dividend_p': company_info['dividend'][0][0].split(',')[0].split('%')[0] \
                if len(company_info['dividend'][0][0]) > 6 else '-',
            'cash_dividend_year': company_info['dividend'][0][0].split(',')[0].split('%')[1] \
                if len(company_info['dividend'][0][0]) > 6 else '-',
            # 'stock_dividend_p': company_info['dividend'][1][0].split(',')[0].split('%')[0] \
            #     if len(company_info['dividend'][1][0]) > 6 else '-',
            # 'stock_dividend_year': company_info['dividend'][1][0].split(',')[0].split('%')[1] \
            #     if len(company_info['dividend'][1][0]) > 6 else '-',
            'listing_year': company_info['other'][0][1],
            'market_category': company_info['other'][1][1],
            'sh_director': company_info['other'][3][1].split(' ')[0].split(':')[1],
            'sh_govt': company_info['other'][3][1].split(' ')[1].split(':')[1],
            'sh_inst': company_info['other'][3][1].split(' ')[2].split(':')[1],
            'sh_foreign': company_info['other'][3][1].split(' ')[3].split(':')[1],
            'sh_public': company_info['other'][3][1].split(' ')[4].split(':')[1],

            'turnover_q1': fin_interim_info['main'][4][1],
            'turnover_q2': fin_interim_info['main'][4][2],
            'turnover_q3': fin_interim_info['main'][4][4],
            'profit_cop_q1': fin_interim_info['main'][5][1],
            'profit_cop_q2': fin_interim_info['main'][5][2],
            'profit_cop_q3': fin_interim_info['main'][5][4],
            'profit_period_q1': fin_interim_info['main'][6][1],
            'profit_period_q2': fin_interim_info['main'][6][2],
            'profit_period_q3': fin_interim_info['main'][6][4],
            'tci_period_q1': fin_interim_info['main'][7][1],
            'tci_period_q2': fin_interim_info['main'][7][2],
            'tci_period_q3': fin_interim_info['main'][7][4],
            'eps_basic_q1': fin_interim_info['main'][9][1],
            'eps_basic_q2': fin_interim_info['main'][9][2],
            'eps_basic_q3': fin_interim_info['main'][9][4],
            'eps_diluted_q1': fin_interim_info['main'][10][1],
            'eps_diluted_q2': fin_interim_info['main'][10][2],
            'eps_diluted_q3': fin_interim_info['main'][10][4],
            'eps_cop_basic_q1': fin_interim_info['main'][12][1],
            'eps_cop_basic_q2': fin_interim_info['main'][12][2],
            'eps_cop_basic_q3': fin_interim_info['main'][12][4],
            'eps_cop_diluted_q1': fin_interim_info['main'][13][1],
            'eps_cop_diluted_q2': fin_interim_info['main'][13][2],
            'eps_cop_diluted_q3': fin_interim_info['main'][13][4],
            'price_period_q1': fin_interim_info['main'][14][1],
            'price_period_q2': fin_interim_info['main'][14][2],
            'price_period_q3': fin_interim_info['main'][14][4],
        }
        try:
            df_company = df_company.append(company_dict, ignore_index=True)
        except Exception as e:
            print(str(e))

        return df_company

    @staticmethod
    def append_fin_perf(fin_perf_info, df_fin_perf, symbol):
        for eps, pe in zip(fin_perf_info['eps'][3:], fin_perf_info['pe'][4:]):
            i = 0
            if len(eps) > 13:
                i = 1

            eps_dict = {
                'symbol': symbol,
                'year': " ".join(eps[0:i + 1]) if i else eps[0],
                'eps_original': eps[i + 1],
                'eps_restated': eps[i + 2],
                'eps_diluted': eps[i + 3],
                'eps_cop_original': eps[i + 4],
                'eps_cop_restated': eps[i + 5],
                'eps_cop_diluted': eps[i + 6],
                'nav_original': eps[i + 7],
                'nav_restated': eps[i + 8],
                'nav_diluted': eps[i + 9],
                'pco': eps[i + 10],
                'profit': eps[i + 11],
                'tci': eps[i + 12],

                'pe_original': pe[i + 1],
                'pe_restated': pe[i + 2],
                'pe_diluted': pe[i + 3],
                'pe_cop_original': pe[i + 4],
                'pe_cop_restated': pe[i + 5],
                'pe_cop_diluted': pe[i + 6],

                'dividend_p': pe[i + 7],
                'dividend_yield_p': pe[i + 8]
            }
            # print(eps_dict['year'])
            try:
                df_fin_perf = df_fin_perf.append(eps_dict, ignore_index=True)
            except Exception as e:
                print(str(e))

        return df_fin_perf

    @staticmethod
    def parse_company_data_rows(soup, symbol):

        company_info = {}
        fin_perf_info = {}
        fin_interim_info = {}

        company_tables = soup.find_all(
            "table",
            attrs={
                "class": "table table-bordered background-white",
            }
        )
        count = 1
        for table in company_tables:
            # print(">>>>>>>>>Contents in table no: ", count)
            table_rows = table.find_all("tr")
            # print(table_rows)
            # if count not in (1, ):
            cur_list = []
            for row in table_rows:
                row_data = [" ".join(td.get_text().split()) for td in row.find_all("td")]
                cur_list.append(row_data)
            # print(cur_list)

            if count == 1:
                company_info.update({
                    'ltp': cur_list[0][1],
                    'market_cap': cur_list[6][1]
                })

            if count == 2:
                company_info.update({
                    'basic': cur_list
                })
            elif count == 3:
                company_info.update({
                    'dividend': cur_list
                })
            elif count == 10:
                company_info.update({
                    'other': cur_list
                })

            elif count == 4:
                fin_interim_info.update({
                    'main': cur_list
                })
            elif count == 5:
                fin_interim_info.update({
                    'pe_audited': cur_list
                })
            elif count == 6:
                fin_interim_info.update({
                    'pe_unaudited': cur_list
                })

            elif count == 7:
                fin_perf_info.update({
                    'eps': cur_list
                })

            elif count == 8:
                fin_perf_info.update({
                    'pe': cur_list
                })
            else:
                pass

            count += 1

        dict_company = {
            'company_info': company_info,
            'fin_interim_info': fin_interim_info,
            'symbol': symbol
        }

        dict_fin_perf = {
            'fin_perf_info': fin_perf_info,
            'symbol': symbol
        }

        return dict_company, dict_fin_perf

    def get_company_df(
        self, symbols,
        df_company=pd.DataFrame(),
        df_fin_perf=pd.DataFrame()
    ):
        if type(symbols) is not list:
            raise TypeError("Either list or tuple is allowed for 'symbols' parameter!")
        for symbol in symbols:
            full_url = self.DSE_COMPANY_URL + symbol
            target_page = requests.get(full_url, verify=False)
            page_html = BeautifulSoup(target_page.text, 'html.parser')
            dict_company, dict_fin_perf = self.parse_company_data_rows(
                page_html, symbol
            )
            df_company = self.append_company(
                company_info=dict_company['company_info'],
                fin_interim_info=dict_company['fin_interim_info'],
                df_company=df_company,
                symbol=symbol
            )
            df_fin_perf = self.append_fin_perf(
                fin_perf_info=dict_fin_perf['fin_perf_info'],
                df_fin_perf=df_fin_perf,
                symbol=symbol
            )
        return df_company, df_fin_perf

    def save_company_data(self, symbols, path=''):
        if type(symbols) is not list:
            raise TypeError("Either list or tuple is allowed for 'symbols' parameter!")
        company_df = pd.DataFrame()
        fin_df = pd.DataFrame()
        company_df, fin_df = self.get_company_df(symbols, company_df, fin_df)
        company_df.to_csv(os.path.join(path, 'company_data.csv'))
        fin_df.to_csv(os.path.join(path, 'financial_data.csv'))
