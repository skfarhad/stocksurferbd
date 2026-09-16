#!/usr/bin/env python

__author__ = "Sk Farhad"
__copyright__ = "Copyright (c) 2024 The Python Packaging Authority"

"""Download the current CSE snapshot and the full CSE price archive.

CSE publishes one spreadsheet of *all* symbols per date range, so the archive
is pulled once with ``get_day_end_range_df`` and then split into one file per
symbol. Closed chunks are cached in ``CACHE_FOLDER`` for later runs.
"""

import os
import datetime

from stocksurferbd_pkg import PriceData


CUR_FILE_NAME = 'csebd_current_data.xlsx'
HISTORY_FOLDER = 'cse_history_data'
CACHE_FOLDER = 'cse_cache'


loader = PriceData(cache_dir=CACHE_FOLDER)


def fetch_all_stock_data():
    loader.save_current_data(file_name=CUR_FILE_NAME, market='CSE')
    os.makedirs(HISTORY_FOLDER, exist_ok=True)
    archive = loader.get_day_end_range_df(
        PriceData.CSE_EARLIEST_DATE, datetime.date.today(), market='CSE',
    )
    for symbol, frame in archive.groupby('TRADING_CODE'):
        print('Writing ' + symbol + " data.....")
        try:
            frame.reset_index(drop=True).to_excel(
                os.path.join(HISTORY_FOLDER, symbol + '_history_data.xlsx')
            )
        except Exception as e:
            print("ERROR: " + str(e))
    print('Data extraction finished')


if __name__ == "__main__":
    fetch_all_stock_data()
