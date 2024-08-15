#!/usr/bin/env python

__author__ = "Sk Farhad"
__copyright__ = "Copyright (c) 2024 The Python Packaging Authority"

import pandas as pd

from stocksurferbd_pkg import PriceData


CUR_FILE_NAME = 'csebd_current_data.csv'
HISTORY_FOLDER = 'dse_history_data'


loader = PriceData()


def fetch_all_stock_data():
    loader.save_current_csv(file_name=CUR_FILE_NAME, market='CSE')
    df = pd.read_csv(CUR_FILE_NAME)
    symbols = df['TRADING_CODE'].values
    for sym in symbols:
        print('Downloading ' + sym + " data.....")
        try:
            loader.save_history_csv(
                symbol=sym, csv_path='cse_history_data', file_name=sym + '_history_data.csv', market='CSE'
            )
            print('Downloading ' + sym + " Finished!")
        except Exception as e:
            print("ERROR: " + str(e))
    print('Data extraction finished')


if __name__ == "__main__":
    fetch_all_stock_data()
