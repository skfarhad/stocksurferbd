#!/usr/bin/env python

__author__ = "Sk Farhad"
__copyright__ = "Copyright (c) 2021 The Python Packaging Authority"


import pandas as pd
from stocksurferbd_pkg import FundamentalData
loader = FundamentalData()


def get_all_company_data():
    df = pd.read_csv('dsebd_current_data.csv')
    symbols = list(df['TRADING_CODE'].values)
    # print(symbols)
    loader.save_company_data(symbols, path='company_info')


get_all_company_data()
# df_company, df_fin = loader.get_company_df(['ACI'])
# print(df_company.head())
# loader.save_company_data(['ACI'])
