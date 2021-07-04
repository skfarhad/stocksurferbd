import os
import pandas as pd

from dse_data_loader import PriceData


CUR_FILE_NAME = 'dsebd_current_data.csv'
HISTORY_FOLDER = 'dse_history_data'


loader = PriceData()


def append_historical_data(symbol, df_cur):
    csv_path = os.path.join(HISTORY_FOLDER, symbol + "_stock_data.csv")
    df_history = pd.read_csv(
        csv_path,
        sep=r'\s*,\s*',
        header=0,
        encoding='ascii',
        engine='python',
    )
    dates = df_history['DATE'].values
    # print(df_history.head())
    if loader.get_date() not in dates:
        cur_row = df_cur[df_cur['TRADING_CODE'] == symbol]
        df_history = df_history.append(
            {
                'DATE': loader.get_date(),
                'TRADING_CODE': symbol,
                'LTP': cur_row['LTP'].values[0],
                'HIGH': cur_row['HIGH'].values[0],
                'LOW': cur_row['LOW'].values[0],
                'CLOSEP': cur_row['CLOSEP'].values[0],
                'YCP': cur_row['YCP'].values[0],
                'TRADE': cur_row['TRADE'].values[0],
                'VALUE_MN': cur_row['VALUE_MN'].values[0],
                'VOLUME': cur_row['VOLUME'].values[0],
            },
            ignore_index=True
        )
    df_history['DATE'] = pd.to_datetime(df_history['DATE'])
    df_history.sort_values(by='DATE', inplace=True)
    df_history.reset_index(inplace=True)
    del df_history['index']
    df_history.to_csv(csv_path, index=False)


def fetch_all_stock_data():
    loader.save_current_csv(file_name=CUR_FILE_NAME)
    df = pd.read_csv(CUR_FILE_NAME)
    symbols = df['TRADING_CODE'].values
    for sym in symbols:
        print('Downloading ' + sym + " data.....")
        try:
            loader.save_history_csv(
                sym, csv_path=HISTORY_FOLDER, file_name=sym + '_history_data.csv'
            )
            print('Downloading ' + sym + " Finished!")
        except Exception as e:
            print("ERROR: " + str(e))
    print('Data extraction finished')


def append_all_stock_data():
    loader.save_current_csv(file_name=CUR_FILE_NAME)
    df_cur = pd.read_csv(CUR_FILE_NAME)
    symbols = df_cur['TRADING_CODE'].values
    for sym in symbols:
        print('Appending ' + sym + " data.....")
        try:
            append_historical_data(sym, df_cur)
            print('Appending ' + sym + " Finished!")
        except Exception as e:
            print(sym + " ERROR: " + str(e))
    print('Data extraction finished')


# fetch_all_stock_data()
# append_all_stock_data()
loader.save_history_csv('ACI', file_name='ACI.csv')
