#!/usr/bin/env python

__author__ = "Sk Farhad"
__copyright__ = "Copyright (c) 2024 The Python Packaging Authority"


import pandas as pd
from stocksurferbd_pkg import FundamentalData
loader = FundamentalData()


def get_all_company_data():
    df = pd.read_csv('dsebd_current_data.csv')
    symbols = df['TRADING_CODE'].values.tolist()
    # print(symbols)
    for symbol in symbols:
        try:
            loader.save_company_data(symbol, path='company_info')
        except Exception as e:
            print(str(e))


get_all_company_data()
# loader.save_company_data('ACI')
