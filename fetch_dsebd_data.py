import time
import os

from selenium import webdriver
from bs4 import BeautifulSoup
import pandas as pd
import requests
import datetime


CUR_DATE = str(datetime.datetime.now().date())
STOCK_HISTORY_URL = f"""https://www.dsebd.org/day_end_archive.php?endDate={CUR_DATE}&archive=data"""
CURRENT_PRICE_URL = 'https://www.dsebd.org/dseX_share.php'


def parse_float(str_val):
    new_val = str_val.replace(
        ',', ''
    ).replace('--', '0')
    return float(new_val)


def parse_int(str_val):
    new_val = str_val.replace(
        ',', ''
    ).replace('--', '0')
    return int(new_val)


def parse_historical_data_rows(soup):
    df = pd.DataFrame()
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
            df = df.append(
                {
                    'DATE': row_data[1],
                    'TRADING_CODE': row_data[2],
                    'LTP': parse_float(row_data[3]),
                    'HIGH': parse_float(row_data[4]),
                    'LOW': parse_float(row_data[5]),
                    'OPENP': parse_float(row_data[6]),
                    'CLOSEP': parse_float(row_data[7]),
                    'YCP': parse_float(row_data[8]),
                    'TRADE': parse_int(row_data[9].replace(',', '')),
                    'VALUE_MN': parse_float(row_data[10]),
                    'VOLUME': parse_int(row_data[11].replace(',', '')),
                },
                ignore_index=True
            )
        except Exception as e:
            print(str(e))
    return df


def parse_current_data_rows(soup):
    df = pd.DataFrame()
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
        df = df.append(
            {
                'TRADING_CODE': td_values[1],
                'LTP': parse_float(td_values[2]),
                'HIGH': parse_float(td_values[3]),
                'LOW': parse_float(td_values[4]),
                'CLOSEP': parse_float(td_values[5]),
                'YCP': parse_float(td_values[6]),
                '% CHANGE': parse_float(td_values[7]),
                'TRADE': parse_int(td_values[8]),
                'VALUE_MN': parse_float(td_values[9]),
                'VOLUME': parse_int(td_values[10]),
            },
            ignore_index=True
        )
    return df


def extract_historical_data(symbol):
    full_url = STOCK_HISTORY_URL + "&inst=" + symbol
    # driver = webdriver.Chrome(executable_path="./chromedriver_linux64/chromedriver")
    # driver.get(page)
    target_page = requests.get(full_url)
    bs_data = BeautifulSoup(target_page.text, 'html.parser')
    df = parse_historical_data_rows(bs_data)
    # driver.close()
    path = os.path.join('bd_stock_prices', symbol + "_stock_data.csv")
    df.to_csv(path, index=False)


def append_historical_data(symbol, df_cur):
    csv_path = os.path.join('bd_stock_prices', symbol + "_stock_data.csv")
    df_history = pd.read_csv(
        csv_path,
        sep=r'\s*,\s*',
        header=0,
        encoding='ascii',
        engine='python',
    )
    dates = df_history['DATE'].values
    print(df_history.head())
    if CUR_DATE not in dates:
        cur_row = df_cur[df_cur['TRADING_CODE'] == symbol]
        df_history = df_history.append(
            {
                'DATE': CUR_DATE,
                'TRADING_CODE': symbol,
                'LTP': cur_row['LTP'].values[0],
                'HIGH': cur_row['HIGH'].values[0],
                'LOW': cur_row['LOW'].values[0],
                'CLOSEP': cur_row['CLOSEP'].values[0],
                'YCP': cur_row['YCP'].values[0],
                '% CHANGE': cur_row['% CHANGE'].values[0],
                'TRADE': cur_row['TRADE'].values[0],
                'VALUE_MN': cur_row['VALUE_MN'].values[0],
                'VOLUME': cur_row['VOLUME'].values[0],
            },
            ignore_index=True
        )
    print(df_history.head())

    # df_history.to_csv(csv_path, index=False)


def extract_current_data():
    # driver = webdriver.Chrome(executable_path="./chromedriver_linux64/chromedriver")
    # driver.get(page)
    target_page = requests.get(CURRENT_PRICE_URL)
    bs_data = BeautifulSoup(target_page.text, 'html.parser')
    df = parse_current_data_rows(bs_data)
    # driver.close()
    df.to_csv("dsebd_current_stock_data.csv", index=False)


def get_all_stock_data():
    extract_current_data()
    df = pd.read_csv('dsebd_current_stock_data.csv')
    symbols = df['TRADING_CODE'].values
    for sym in symbols:
        print('Downloading ' + sym + " data.....")
        extract_historical_data(sym)
        print('Downloading ' + sym + " Finished!")
    print('Data extraction finished')


def append_all_stock_data():
    extract_current_data()
    df_cur = pd.read_csv('dsebd_current_stock_data.csv')
    symbols = df_cur['TRADING_CODE'].values
    for sym in symbols:
        print('Appending ' + sym + " data.....")
        append_historical_data(sym, df_cur)
        print('Appending ' + sym + " Finished!")
        break
    print('Data extraction finished')


get_all_stock_data()
# append_all_stock_data()


