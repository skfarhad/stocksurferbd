#!/usr/bin/env python

__author__ = "Sk Farhad"
__copyright__ = "Copyright (c) 2021 The Python Packaging Authority"

import os
import pandas as pd
from bs4 import BeautifulSoup
import requests
from dateutil import parser
import json

class FundamentalData(object):
    DSE_COMPANY_URL = "https://dsebd.org/displayCompany.php?name="
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
    def append_company(company_info, fin_interim_info, symbol):
        company_dict = {
            'symbol': symbol,
            'auth_capital': company_info['basic'][0][0],
            'trade_start': company_info['basic'][0][1],
            'paid_up_capital': company_info['basic'][1][0],
            'instrument_type': company_info['basic'][1][1],
            'face_value': company_info['basic'][2][0],
            'market_lot': company_info['basic'][2][1],
            'ltp': company_info['ltp'],
            'last_agm_date': company_info['last_agm_date'],
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
                if '%' in company_info['dividend'][0][0] else '-',
            'cash_dividend_year': company_info['dividend'][0][0].split(',')[0].split('%')[1] \
                if '%' in company_info['dividend'][0][0] else '-',
            'stock_dividend_p': company_info['dividend'][1][0].split(',')[0].split('%')[0] \
                if '%' in company_info['dividend'][1][0] else '-',
            'stock_dividend_year': company_info['dividend'][1][0].split(',')[0].split('%')[1] \
                if '%' in company_info['dividend'][1][0] else '-',
            'listing_year': company_info['other'][0][1],
            'market_category': company_info['other'][1][1],
            'sh_director': company_info['other'][4][0].split(': ')[1],
            'sh_govt': company_info['other'][4][1].split(': ')[1],
            'sh_inst': company_info['other'][4][2].split(': ')[1],
            'sh_foreign': company_info['other'][4][3].split(': ')[1],
            'sh_public': company_info['other'][4][4].split(': ')[1],

            'eps_basic_q1': fin_interim_info['main'][5][1],
            'eps_basic_q2': fin_interim_info['main'][5][2],
            'eps_basic_hy': fin_interim_info['main'][5][3],
            'eps_basic_q3': fin_interim_info['main'][5][4],
            'eps_basic_9m': fin_interim_info['main'][5][5],
            'eps_basic_yr': fin_interim_info['main'][5][6],

            'eps_diluted_q1': fin_interim_info['main'][6][1],
            'eps_diluted_q2': fin_interim_info['main'][6][2],
            'eps_diluted_hy': fin_interim_info['main'][6][3],
            'eps_diluted_q3': fin_interim_info['main'][6][4],
            'eps_diluted_9m': fin_interim_info['main'][6][5],
            'eps_diluted_yr': fin_interim_info['main'][6][6],


            'eps_cop_basic_q1': fin_interim_info['main'][8][1],
            'eps_cop_basic_q2': fin_interim_info['main'][8][2],
            'eps_cop_basic_hy': fin_interim_info['main'][8][3],
            'eps_cop_basic_q3': fin_interim_info['main'][8][4],
            'eps_cop_basic_9m': fin_interim_info['main'][8][5],
            'eps_cop_basic_yr': fin_interim_info['main'][8][6],

            'eps_cop_diluted_q1': fin_interim_info['main'][9][1],
            'eps_cop_diluted_q2': fin_interim_info['main'][9][2],
            'eps_cop_diluted_hy': fin_interim_info['main'][9][3],
            'eps_cop_diluted_q3': fin_interim_info['main'][9][4],
            'eps_cop_diluted_9m': fin_interim_info['main'][9][5],
            'eps_cop_diluted_yr': fin_interim_info['main'][9][6],
        }
        df_company = pd.DataFrame(company_dict, index=[0])

        return df_company

    @staticmethod
    def append_fin_perf(fin_perf_info, symbol):
        data_list = []
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
            data_list.append(eps_dict)
        df_fin_perf = pd.DataFrame(
            data_list,
            columns=[
                'symbol', 'year',
                'eps_original',
                'eps_restated',
                'eps_diluted',
                'eps_cop_original',
                'eps_cop_restated',
                'eps_cop_diluted',
                'nav_original',
                'nav_restated',
                'nav_diluted',
                'pco',
                'profit',
                'tci',
                'pe_original',
                'pe_restated',
                'pe_diluted',
                'pe_cop_original',
                'pe_cop_restated',
                'pe_cop_diluted',
                'dividend_p',
                'dividend_yield_p'
            ]
        )

        return df_fin_perf

    @staticmethod
    def parse_company_data_rows(soup, symbol):

        company_info = {}
        fin_perf_info = {}
        fin_interim_info = {}
        agm_info = soup.find(
            "div",
            attrs={
                "class": "col-sm-6 pull-left"
            }
        )
        if agm_info is None:
            raise Exception(f"Data fetch error for: {symbol}")
        # print("AGM info: " + str(agm_info))
        date_txt = " ".join(agm_info.text.split('on:')[1].strip().split())
        try:
            last_agm_date = parser.parse(date_txt).date()
        except Exception as e:
            print(str(e))
            last_agm_date = 'None'

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
                    'market_cap': cur_list[6][1],
                    'last_agm_date': last_agm_date
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
                # print('fin interim main: ')
                for item in cur_list:
                    print(item)
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

    def get_company_df(self, symbol):
        df_company_all = pd.DataFrame()
        df_fin_perf_all = pd.DataFrame()
        full_url = self.DSE_COMPANY_URL + symbol
        # print("URL: " + full_url)
        target_page = requests.get(full_url)
        page_html = BeautifulSoup(target_page.text, 'html.parser')
        dict_company, dict_fin_perf = self.parse_company_data_rows(
            page_html, symbol
        )
        print("Fetching data for: ", symbol)
        df_company = self.append_company(
            company_info=dict_company['company_info'],
            fin_interim_info=dict_company['fin_interim_info'],
            symbol=symbol
        )
        df_company_all = pd.concat([df_company_all, df_company])
        df_fin_perf = self.append_fin_perf(
            fin_perf_info=dict_fin_perf['fin_perf_info'],
            symbol=symbol
        )
        df_fin_perf_all = pd.concat([df_fin_perf_all, df_fin_perf])
        print("Fetch complete!")
        return df_company_all, df_fin_perf_all

    def save_company_data(self, symbol, path=''):
        company_df, fin_df = self.get_company_df(symbol)
        company_df.to_csv(os.path.join(path, f'{symbol}_company_data.csv'), index=False)
        fin_df.to_csv(os.path.join(path, f'{symbol}_financial_data.csv'), index=False)
