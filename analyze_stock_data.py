import math
import os
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from model_utils.arima_utils import TSxARIMA
import time
import tensorflow as tf

import mplfinance as mplf
from scipy import stats
import talib as ta

os.environ['TF_FORCE_GPU_ALLOW_GROWTH'] = 'true'
tf.get_logger().setLevel('ERROR')


def clean_x(x):
    return x.lower().replace(
        ' ', ''
    ).replace(
        '-', ''
    ).replace(
        'n/a', ''
    ).replace(
        ',', ''
    )


def process_data(file_path='', data_len=720, train_len=40):
    # print(file_path)
    df = pd.read_csv(
        file_path,
        sep=r'\s*,\s*',
        header=0,
        encoding='ascii',
        engine='python',
    )
    # print(df.head())

    df['DATE'] = pd.to_datetime(df['DATE'])
    df.sort_values(by='DATE', inplace=True)
    df.reset_index(inplace=True)
    del df['index']
    return df


def process_data_mpl(file_path='', data_len=720, train_len=40):
    df = pd.read_csv(
        file_path,
        sep=r'\s*,\s*',
        header=0,
        encoding='ascii',
        engine='python',
    )
    # print(df.head())
    columns = ['DATE', 'CLOSEP', 'VOLUME', 'HIGH', 'LOW', 'OPENP']
    df = df[columns]
    df = df.rename(columns={
        'DATE': 'Date',
        'OPENP': 'Open',
        'CLOSEP': 'Close',
        'VOLUME': 'Volume',
        'HIGH': 'High',
        'LOW': 'Low'
    }, inplace=False)

    df['Volume'] = df.apply(lambda row: row['Volume']/1000, axis=1)
    df['Date'] = pd.to_datetime(df['Date'])
    df.sort_values(by='Date', inplace=True)
    df.reset_index(inplace=True)
    df.index = pd.DatetimeIndex(df['Date'])
    return df


def plot_stock_data(symbol, data):
    print('Symbol: ', symbol)
    close_p = data['CLOSEP']
    mu_close_p, std_close_p = round(close_p.mean(), 2), round(close_p.std(), 2)
    # print("CLOSEP(mu, sigma):", mu_close_p, std_close_p)
    volume = data['VALUE_MN']
    mu_volume_p, std_volume_p = round(volume.mean(), 2), round(volume.std(), 2)
    # print("VOLUME(mu, sigma):", mu_volume_p, std_volume_p)
    trade = data['TRADE']
    mu_trade_p, std_trade_p = round(trade.mean(), 2), round(trade.std(), 2)
    # print("TRADE(mu, sigma):", mu_trade_p, std_trade_p)
    s_dates = data['DATE']
    fig = plt.figure(figsize=(18, 7), dpi=80)
    plt.plot(s_dates, close_p, '--o')
    plt.bar(s_dates, trade)
    plt.xticks(rotation=70)
    plt.xlabel('Dates', fontsize=16)
    plt.ylabel('Stock Price of ' + symbol, fontsize=16)
    plt.grid()
    plt.show()


def visualize_data(symbols, data_n=360):
    for symbol in symbols:
        path = 'bd_stock_prices/' + symbol + '_stock_data.csv'
        data = process_data(path)
        data = data[-data_n:]
        plot_stock_data(symbol, data)


def candelstick_plot(symbol, data):
    print('Symbol: ', symbol)

    data["macd"], data["macd_signal"], data["macd_hist"] = ta.MACD(data['Close'])

    # macd panel
    colors = ['g' if v >= 0 else 'r' for v in data["macd_hist"]]
    macd_plot = mplf.make_addplot(data["macd"], panel=1, color='orange', title="MACD")
    macd_hist_plot = mplf.make_addplot(data["macd_hist"], type='bar', panel=1, color=colors)  # color='dimgray'
    macd_signal_plot = mplf.make_addplot(data["macd_signal"], panel=1, color='blue')

    # plot
    plots = [macd_plot, macd_signal_plot, macd_hist_plot]
    mplf.plot(
        data,
        type='candle',
        style='nightclouds',
        title='Chart for: ' + symbol,
        ylabel='Price (Tk)',
        figratio=(18, 7),
        volume=True,
        ylabel_lower='Volume(K)',
        mav=(5, 20, 45),
        addplot=plots,
        volume_panel=2,
        scale_padding={'left': 1, 'top': 1, 'right': 1, 'bottom': 1},
        panel_ratios=(1, 0.3, .3),
        xrotation=7.5,
        # tight_layout=True,
        # show_nontrading=True,
    )


def visualize_candlestick_data(symbols, data_n=360):
    for symbol in symbols:
        path = 'bd_stock_prices/' + symbol + '_stock_data.csv'
        data = process_data_mpl(path)
        data = data[data['Open'] > 0]
        data = data[data['High'] > 0]
        data = data[data['Close'] > 0]
        data = data[-data_n:]
        try:
            candelstick_plot(symbol, data)
        except Exception as e:
            print(str(e))


def analyze_dse_data_subset(symbols, data_n=360):
    path = 'bd_stock_prices'
    df = pd.DataFrame(columns=[
        'symbol',
        'avg_close_p',
        'std_close_p',
        'cov_close_p',
        'avg_trade',
        'std_trade',
        'avg_volume_mn',
        'std_volume_mn',
        'slope_close_p'
    ])
    for symbol in symbols:
        full_path = os.path.join(path, symbol + '_stock_data.csv')
        try:
            data_df = process_data(full_path)
            data_df = data_df[-data_n:]
            close_p = data_df['CLOSEP']
            avg_close_p, std_close_p = round(close_p.mean(), 2), round(close_p.std(), 2)
            volume = data_df['VALUE_MN']
            avg_volume, std_volume = round(volume.mean(), 2), round(volume.std(), 2)
            trade = data_df['TRADE']
            avg_trade, std_trade = round(trade.mean(), 2), round(trade.std(), 2)
            x_values = range(0, len(close_p))
            slope, y_c, r_val, p_val, std_err = stats.linregress(x_values, close_p)
            cov_close_p = std_close_p / avg_close_p
            # print(symbol, avg_close_p, avg_trade, avg_volume)
            df = df.append(
                {
                    'symbol': symbol,
                    'avg_close_p': avg_close_p,
                    'std_close_p': std_close_p,
                    'cov_close_p': cov_close_p,
                    'avg_trade': avg_trade,
                    'std_trade': std_trade,
                    'avg_volume_mn': avg_volume,
                    'std_volume_mn': std_volume,
                    'slope_close_p': slope,
                },
                ignore_index=True
            )
        except Exception as e:
            print(str(e))
    return df

