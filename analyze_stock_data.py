#!/usr/bin/env python

__author__ = "Sk Farhad"
__copyright__ = "Copyright (c) 2021 The Python Packaging Authority"

import os
import numpy as np
import pandas as pd
import mplfinance as mplf
from matplotlib.ticker import MultipleLocator
from scipy import stats
import talib as ta
from pyti.bollinger_bands import upper_bollinger_band as bb_up
from pyti.bollinger_bands import middle_bollinger_band as bb_mid
from pyti.bollinger_bands import lower_bollinger_band as bb_low
from tapy import Indicators


RISK_R = 32
HISTORY_FOLDER = 'dse_history_data'


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


def get_crossing(y_val, kpi_data):
    x_flag = None
    x_count = 0
    x_dist = 0

    for y_i, kpi_i in zip(y_val, kpi_data):
        x_dist += abs(y_i - kpi_i)
        if x_flag is None:
            x_flag = y_i > kpi_i
        else:
            c_flag = y_i > kpi_i
            if c_flag != x_flag:
                x_count += 1
                x_flag = c_flag

    x_dist_avg = x_dist / len(kpi_data)

    return x_count, x_dist_avg


def process_data(file_path=''):
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


def aggregate_history_data(symbols, data_n=90, n_short=RISK_R):
    path = HISTORY_FOLDER
    df = pd.DataFrame()
    for symbol in symbols:
        full_path = os.path.join(path, symbol + '_history_data.csv')
        try:
            data_df = process_data(full_path)
            data_df = data_df[-data_n:]
            n_long = (data_n - n_short)
            close_l = data_df['CLOSEP'][0:n_long]
            close_s = data_df['CLOSEP'][-n_short:]
            ltp = data_df['CLOSEP'][-1:].values[0]

            max_gain = ((max(close_s.values) - ltp) / ltp) * 100
            max_loss = ((ltp - min(close_s.values)) / ltp) * 100

            volume = data_df['VALUE_MN'][-n_short:]
            avg_volume = round(volume.mean(), 2)
            trade = data_df['TRADE'][-n_short:]
            avg_trade = round(trade.mean(), 2)

            x_l = range(0, n_long)
            slope_l, y_l, r_val, p_val, std_err = stats.linregress(x_l, close_l)
            # x_close, avg_x_dist = get_crossing(y_l, close_l.values)
            x_s = range(0, n_short)
            slope_s, y_s, r_val, p_val, std_err = stats.linregress(x_s, close_s)
            df = df.append(
                {
                    'symbol': symbol,
                    'ltp': ltp,
                    # 'x_close': x_close,
                    # 'avg_x_dist': avg_x_dist,
                    'max_gain': max_gain,
                    'max_loss': max_loss,
                    'avg_trade': avg_trade,
                    'avg_volume_mn': avg_volume,
                    'per_trade_k': (volume/trade).mean() * 1000,
                    'slope_s': slope_s,
                    'slope_l': slope_l,
                },
                ignore_index=True
            )
        except Exception as e:
            print(str(e))
    # print(df.head())
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
    columns = ['DATE', 'CLOSEP', 'VALUE_MN', 'HIGH', 'LOW', 'OPENP', 'TRADE']
    df = df[columns]
    df = df.rename(columns={
        'DATE': 'Date',
        'OPENP': 'Open',
        'CLOSEP': 'Close',
        'VALUE_MN': 'Volume',
        'TRADE': 'Trade',
        'HIGH': 'High',
        'LOW': 'Low'
    }, inplace=False)

    df = df[df['Open'] > 0]
    df = df[df['High'] > 0]
    df = df[df['Close'] > 0]

    # df['Volume'] = df.apply(lambda row: row['Volume'], axis=1)
    df['Date'] = pd.to_datetime(df['Date'])
    df.sort_values(by='Date', inplace=True)
    df.reset_index(inplace=True)
    df.index = pd.DatetimeIndex(df['Date'])
    return df


def candelstick_plot(symbol, data, purchased_at=False):
    ltp = data['Close'][-1:].values[0]
    max_p = max(data['Close'][-RISK_R:].values)
    gain = ((max_p - ltp)/ltp) * 100
    min_p = min(data['Close'][-RISK_R:].values)
    trade = data['Trade']
    loss = ((ltp - min_p)/ltp)*100
    print('-----------------------------------------------------')
    print('Symbol: ' + symbol + ', LTP: ' + str(ltp) +
        ', ' + str(RISK_R) + ' day % gain:loss- ' +
        str(round(gain, 2)) + ":" + str(round(loss, 2))
    )
    if purchased_at:
        print(
            'Purchased at: ' + str(purchased_at) +
            ', Current gain: ' + str(round(((ltp - purchased_at)/purchased_at) * 100, 2))
        )
    macd, macd_signal, macd_hist = ta.MACD(data['Close'])

    # macd panel
    color_up = 'limegreen'
    color_down = 'tomato'

    colors = [color_up if v >= 0 else color_down for v in macd_hist]
    macd_plot = mplf.make_addplot(
        macd, panel=1, color='orange', width=1, ylabel='MACD'
    )
    macd_hist_plot = mplf.make_addplot(macd_hist, type='bar', panel=1, color=colors)
    macd_signal_plot = mplf.make_addplot(macd_signal, panel=1, color='blue', width=1)

    data_cl = data['Close'].values.tolist()
    ma1, ma2 = 5, 20
    bb_u = bb_up(data_cl, ma2)
    bb_l = bb_low(data_cl, ma2)
    bb_m = bb_mid(data_cl, ma2)

    bb_m_plot = mplf.make_addplot(bb_m, panel=0, color='cyan', width=1, alpha=0.5)
    bb_l_plot = mplf.make_addplot(bb_l, panel=0, color='yellow', width=1, alpha=0.5)
    bb_u_plot = mplf.make_addplot(bb_u, panel=0, color='yellow', width=1, alpha=0.5)

    data_short = data['Close'][-RISK_R:]
    data_n = len(data)
    x_tr = range(0, len(data_short))
    slope, y_tr, r_val, p_val, std_err = stats.linregress(x_tr, data_short)
    y_tr_value = slope * x_tr + y_tr
    y_tr_value = np.concatenate((
        [np.NaN] * (data_n - RISK_R), y_tr_value
    ))

    data_long = data['Close'][: (data_n - RISK_R)]
    x_tr2 = range(0, len(data_long))
    slope2, y_tr2, r_val, p_val, std_err = stats.linregress(x_tr2, data_long)
    y_tr_value2 = slope2 * x_tr2 + y_tr2
    y_tr_value2 = np.concatenate((
        y_tr_value2, [np.NaN] * RISK_R
    ))

    y_tr_plot = mplf.make_addplot(
        y_tr_value, panel=0, color='coral', width=2, alpha=0.4, linestyle='dashed'
    )
    price_plot = mplf.make_addplot(data['Close'], panel=0, color='white', width=1, alpha=0.5)

    vol_colors = data.apply(lambda x: color_up if x['Close'] > x['Open'] else color_down, axis=1)
    volume_plot = mplf.make_addplot(
        data['Volume'], panel=2, color=vol_colors.values, type='bar', ylabel='Value(Mil)',
    )
    y_tr_plot2 = mplf.make_addplot(
        y_tr_value2, panel=0, color='coral', width=2, alpha=0.4, linestyle='dashed'
    )

    # trade_plot = mplf.make_addplot(trade.values, panel=2, color='gray', type='bar')

    # ind = Indicators(data)
    # ind.fractals(column_name_high='fr_high', column_name_low='fr_low')
    # data = ind.df
    # data['fr_high'] = data.apply(lambda x: x['Close'] if x['fr_high'] else 0, axis=1)
    # data['fr_low'] = data.apply(lambda x: x['Close'] if x['fr_low'] else 0, axis=1)
    #
    # print(data[['Date','Close', 'fr_high', 'fr_low']])
    #
    # fr_high_plot = mplf.make_addplot(data['fr_high'], panel=0, color='gray', width=1, linestyle='dashed')
    # fr_low_plot = mplf.make_addplot(data['fr_low'], panel=0, color='orange', width=1, linestyle='dashed')

    # plot
    plots = [
        price_plot,
        macd_plot, macd_signal_plot, macd_hist_plot,
        bb_u_plot, bb_m_plot, bb_l_plot,
        y_tr_plot,
        y_tr_plot2,
        volume_plot,
        # trade_plot,
        # fr_low_plot,
        # fr_high_plot
    ]

    if purchased_at:
        purchased_at_plot = mplf.make_addplot(
            [purchased_at] * data_n, panel=0, color='white', width=2, alpha=0.4, linestyle='dashed'
        )
        plots.append(purchased_at_plot)

    custom_nc = mplf.make_mpf_style(
        base_mpf_style='nightclouds',
        marketcolors={'candle': {'up': color_up, 'down': color_down},
                      'edge': {'up': color_up, 'down': color_down},
                      'wick': {'up': color_up, 'down': color_down},
                      'ohlc': {'up': color_up, 'down': color_down},
                      'volume': {'up': color_up, 'down': color_down},
                      'vcdopcod': True,  # Volume Color Depends On Price Change On Day
                      'alpha': 1.0,
                      },
        mavcolors=['gray', 'sienna', 'darkslategray', 'purple'],
    )

    mplf.plot(
        data[['Date', 'Open', 'Close', 'Volume', 'High', 'Low']],
        type='candle',
        style=custom_nc,
        title='Chart for: ' + symbol,
        ylabel='Price (Tk)',
        figratio=(18, 7),
        addplot=plots,
        # volume=True,
        # volume_panel=2,
        scale_padding={'left': 1, 'top': 1, 'right': 1, 'bottom': 1},
        panel_ratios=(1, 0.3, .3),
        xrotation=7.5,
        # tight_layout=True,
        # show_nontrading=True,
        # returnfig=True
    )
    # fig, axlist = mplf.plot()
    # axlist[0].xaxis.set_minor_locator(MultipleLocator(1))


def visualize_candlestick_data(symbols, data_n=360):
    for symbol in symbols:
        try:
            path = os.path.join(HISTORY_FOLDER, symbol + '_history_data.csv')
            data = process_data_mpl(path)
            data = data[data['Open'] > 0]
            data = data[data['High'] > 0]
            data = data[data['Close'] > 0]
            data = data[-data_n:]
            candelstick_plot(symbol, data)
        except Exception as e:
            print(str(e))


def visualize_candlestick_data_with_price(sym_w_prices, data_n=360):
    for symbol in sym_w_prices:
        try:
            path = os.path.join(HISTORY_FOLDER, symbol[0] + '_history_data.csv')
            data = process_data_mpl(path)
            data = data[data['Open'] > 0]
            data = data[data['High'] > 0]
            data = data[data['Close'] > 0]
            data = data[-data_n:]
            candelstick_plot(symbol[0], data, symbol[1])
        except Exception as e:
            print(str(e))


def visualize_candlestick_data_single(symbol, data_n=360):
    try:
        path = os.path.join(HISTORY_FOLDER, symbol + '_history_data.csv')
        data = process_data_mpl(path)
        data = data[-data_n:]
        candelstick_plot(symbol, data)
    except Exception as e:
        print(str(e))




