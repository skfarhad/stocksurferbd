#!/usr/bin/env python

__author__ = "Sk Farhad"
__copyright__ = "Copyright (c) 2021 The Python Packaging Authority"

import time
import os

# from selenium import webdriver
import pandas as pd
from dse_data_loader import FundamentalData
loader = FundamentalData()


def get_all_company_data():
    df = pd.read_csv('dsebd_current_stock_data.csv')
    symbols = df['TRADING_CODE'].values
    loader.save_company_data(symbols, path='company_info')


# get_all_company_data()
# df_company, df_fin = loader.get_company_df(['ACI'])
# print(df_company.head())

loader.save_company_data(['ACI'])
