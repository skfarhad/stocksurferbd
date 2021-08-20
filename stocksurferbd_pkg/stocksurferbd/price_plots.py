#!/usr/bin/env python

__author__ = "Sk Farhad"
__copyright__ = "Copyright (c) 2021 The Python Packaging Authority"

import numpy as np
import pandas as pd
import mplfinance as mplf
from matplotlib import pyplot as plt
from scipy import stats
from pyti.bollinger_bands import upper_bollinger_band as bb_up
from pyti.bollinger_bands import middle_bollinger_band as bb_mid
from pyti.bollinger_bands import lower_bollinger_band as bb_low
from pyti.relative_strength_index import relative_strength_index as RSI
from tapy import Indicators


class CandlestickPlot(object):

    def __init__(self, csv_path, symbol):
        self.csv_path = csv_path
        self.data = None
        self.plots = []
        self.symbol = symbol
        self.color_up = 'limegreen'
        self.color_down = 'tomato'

    @staticmethod
    def get_macd(data, n_fast=10, n_slow=22, n_smooth=7):
        fast_ema = data.ewm(span=n_fast, min_periods=n_slow).mean()
        slow_ema = data.ewm(span=n_slow, min_periods=n_slow).mean()
        macd = pd.Series(fast_ema - slow_ema, name='macd')
        macd_sig = pd.Series(macd.ewm(span=n_smooth, min_periods=n_smooth).mean(), name='macd_sig')
        macd_hist = pd.Series(macd - macd_sig, name='macd_hist')

        return macd, macd_sig, macd_hist

    @staticmethod
    def get_n_short(data_len):
        return data_len // 3

    @staticmethod
    def get_weekly(df, step='3D'):
        agg_dict = {
            'Open': 'first',
            'High': 'max',
            'Low': 'min',
            'Close': 'last',
            'Trade': 'mean',
            'Volume': 'mean'
        }

        # resampled dataframe
        # 'W' means weekly aggregation
        df = df.resample(step).agg(agg_dict)
        return df

    def get_nc_style(self):
        color_up, color_down = self.color_up, self.color_down
        ncs = mplf.make_mpf_style(
            base_mpf_style='nightclouds',
            marketcolors={
                'candle': {'up': color_up, 'down': color_down},
                'edge': {'up': color_up, 'down': color_down},
                'wick': {'up': color_up, 'down': color_down},
                'ohlc': {'up': color_up, 'down': color_down},
                'volume': {'up': color_up, 'down': color_down},
                'vcdopcod': True,  # Volume Color Depends On Price Change On Day
                'alpha': 1.0,
            },
            mavcolors=['gray', 'sienna', 'darkslategray', 'purple'],
        )
        return ncs

    def process_data_mpl(self, resample=False, step='3D', vol_key='VOLUME'):
        df = pd.read_csv(
            self.csv_path,
            sep=r'\s*,\s*',
            header=0,
            encoding='ascii',
            engine='python',
        )
        # print(df.head())
        columns = ['DATE', 'CLOSEP', vol_key, 'HIGH', 'LOW', 'OPENP', 'TRADE']
        df = df[columns]
        df = df.rename(columns={
            'DATE': 'Date',
            'OPENP': 'Open',
            'CLOSEP': 'Close',
            vol_key: 'Volume',
            'TRADE': 'Trade',
            'HIGH': 'High',
            'LOW': 'Low'
        }, inplace=False)

        df = df[df['Open'] > 0]
        df = df[df['High'] > 0]
        df = df[df['Close'] > 0]

        df['Date'] = pd.to_datetime(df['Date'])
        if resample:
            df.index = pd.DatetimeIndex(df['Date'])
            df = self.get_weekly(df, step=step)
            df.reset_index(level=0, inplace=True)
            df.sort_values(by='Date', inplace=True)
            df.index = pd.DatetimeIndex(df['Date'])
            df.dropna(inplace=True)
        else:

            df.sort_values(by='Date', inplace=True)
            # df.reset_index(inplace=True)
            df.index = pd.DatetimeIndex(df['Date'])
        self.data = df
        return

    def add_bb_plots(self, period=20, panel=0):
        data, plots = self.data, self.plots
        data_cl = data['Close'].values.tolist()
        bb_u = bb_up(data_cl, period)
        bb_l = bb_low(data_cl, period)
        bb_m = bb_mid(data_cl, period)

        bb_m_plot = mplf.make_addplot(bb_m, panel=panel, color='cyan', width=1, alpha=0.5)
        bb_l_plot = mplf.make_addplot(bb_l, panel=panel, color='yellow', width=1, alpha=0.3)
        bb_u_plot = mplf.make_addplot(bb_u, panel=panel, color='yellow', width=1, alpha=0.3)
        plots.extend([
            bb_u_plot, bb_m_plot, bb_l_plot
        ])

    def add_macd_plots(self, panel=1):
        data, plots = self.data, self.plots
        color_up, color_down = self.color_up, self.color_down
        macd, macd_signal, macd_hist = self.get_macd(data['Close'])

        colors = [color_up if v >= 0 else color_down for v in macd_hist]
        macd_plot = mplf.make_addplot(
            macd, panel=panel, color='orange', width=1, ylabel='MACD',
            secondary_y=False,
            y_on_right=False
        )
        macd_hist_plot = mplf.make_addplot(
            macd_hist, type='bar', panel=panel, color=colors,
            secondary_y=False

        )
        macd_signal_plot = mplf.make_addplot(
            macd_signal, panel=panel, color='blue', width=1,
            secondary_y=False
        )

        plots.extend([
            macd_plot, macd_signal_plot, macd_hist_plot
        ])

    def add_rsi_plot(self, panel=0, timeperiod=10):
        data, plots = self.data, self.plots
        color_up, color_down = self.color_up, self.color_down
        n_data = len(data)
        rsi = RSI(data['Close'], period=timeperiod)

        line_rsi = mplf.make_addplot(
            rsi, panel=panel, color='gray', ylabel='RSI', width=1.5,
        )

        line_os = mplf.make_addplot(
            [70] * n_data, panel=panel,
            color=color_down, alpha=.5, linestyle='dashed', width=1.5,
            secondary_y=False
        )
        line_ob = mplf.make_addplot(
            [30] * n_data,
            panel=panel,
            color=color_up, alpha=.5, linestyle='dashed', width=1.5,
            secondary_y=False,
            ylabel='RSI'
        )

        plots.extend([
            line_os, line_rsi, line_ob
        ])

    def add_line_plots(self, panel=0):
        data, plots = self.data, self.plots
        data_n = len(data)
        n_short = self.get_n_short(data_n)
        data_short = data['Close'][-n_short:]
        x_tr = range(0, len(data_short))
        slope, y_tr, r_val, p_val, std_err = stats.linregress(x_tr, data_short)
        y_tr_value = slope * x_tr + y_tr
        y_tr_value = np.concatenate((
            [np.NaN] * (data_n - n_short), y_tr_value
        ))

        data_long = data['Close'][: (data_n - n_short)]
        x_tr2 = range(0, len(data_long))
        slope2, y_tr2, r_val, p_val, std_err = stats.linregress(x_tr2, data_long)
        y_tr_value2 = slope2 * x_tr2 + y_tr2
        y_tr_value2 = np.concatenate((
            y_tr_value2, [np.NaN] * n_short
        ))

        y_tr_plot = mplf.make_addplot(
            y_tr_value, panel=panel,
            color='coral', width=2, alpha=0.4, linestyle='dashed'
        )
        price_plot = mplf.make_addplot(
            data['Close'].rolling(window=5).mean(),
            panel=panel,
            color='white', width=1, alpha=0.5
        )
        y_tr_plot2 = mplf.make_addplot(
            y_tr_value2, panel=panel,
            color='coral', width=2, alpha=0.4, linestyle='dashed'
        )

        plots.extend([
            y_tr_plot, price_plot, y_tr_plot2
        ])

    def add_vol_plots(self, vol_panel=2):
        color_up, color_down = self.color_up, self.color_down
        data, plots = self.data, self.plots
        vol_colors = data.apply(
            lambda x: color_up if x['Close'] > x['Open'] else color_down,
            axis=1
        )
        volume_plot = mplf.make_addplot(
            data['Volume'],
            panel=vol_panel,
            color=vol_colors.values,
            type='bar',
            ylabel='Volume',
        )
        plots.append(volume_plot)

    def add_fractal_plot(self, panel=0):
        data, plots = self.data, self.plots
        color_up, color_down = self.color_up, self.color_down
        ind = Indicators(data)
        ind.fractals(column_name_high='fr_high', column_name_low='fr_low')
        data = ind.df
        data['fr_high'] = data.apply(lambda x: x['Close'] * 1.08 if x['fr_high'] else np.NaN, axis=1)
        data['fr_low'] = data.apply(lambda x: x['Close'] * 0.92 if x['fr_low'] else np.NaN, axis=1)

        fr_high_plot = mplf.make_addplot(
            data['fr_high'], panel=panel,
            color=color_down, width=1, type='step', alpha=.9,
            secondary_y=False,
        )
        fr_low_plot = mplf.make_addplot(
            data['fr_low'], panel=panel,
            color=color_up, width=1, type='step', alpha=.9,
            secondary_y=False,

        )
        plots.extend([fr_high_plot, fr_low_plot])

    def create_candlestick_chart(self, step='1D'):
        self.add_rsi_plot(panel=0)
        self.add_line_plots(panel=1)
        self.add_bb_plots(period=20, panel=1)
        # self.add_fractal_plot(panel=1)
        self.add_macd_plots(panel=2)
        self.add_vol_plots(vol_panel=3)
        custom_nc = self.get_nc_style()
        data_mpl = self.data[['Date', 'Open', 'Close', 'Volume', 'High', 'Low']]
        fig, axlist = mplf.plot(
            data_mpl,
            type='candle',
            main_panel=1,
            style=custom_nc,
            title=self.symbol + ': ' + step,
            ylabel='Price (Tk)',
            figratio=(18, 8),
            addplot=self.plots,
            scale_padding={'left': 1, 'top': 1, 'right': 1, 'bottom': 1},
            panel_ratios=(0.3, 1, 0.3, .3),
            xrotation=7.5,
            tight_layout=True,
            # show_nontrading=True,
            returnfig=True
        )

        return fig, axlist

    def show_plot(self, xtick_count=120, resample=False, step='1D'):
        self.process_data_mpl(resample=resample, step=step)
        self.data = self.data[-xtick_count:]
        if not resample:
            step = '1D'
        fig, axlist = self.create_candlestick_chart(step=step)
        plt.show()

    def get_candlestick_fig(self, xtick_count=120, resample=False, step='1D'):
        self.process_data_mpl(resample=resample, step=step)
        self.data = self.data[-xtick_count:]
        if not resample:
            step = '1D'
        fig, axlist = self.create_candlestick_chart(step=step)
        return fig, axlist

