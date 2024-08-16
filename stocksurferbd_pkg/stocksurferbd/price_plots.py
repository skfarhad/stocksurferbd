#!/usr/bin/env python

__author__ = "Sk Farhad"
__copyright__ = "Copyright (c) 2024 The Python Packaging Authority"

import numpy as np
import pandas as pd
import mplfinance as mplf
from matplotlib import pyplot as plt
from pyti.bollinger_bands import upper_bollinger_band as bb_up
from pyti.bollinger_bands import middle_bollinger_band as bb_mid
from pyti.bollinger_bands import lower_bollinger_band as bb_low
from pyti.relative_strength_index import relative_strength_index as RSI
from tapy import Indicators


class CandlestickPlot(object):

    def __init__(
        self,
        file_path,
        symbol,
        data_n=120,
        macd_fast=10,
        macd_slow=22,
        macd_smooth=7,
        rsi_period=10,
        bb_period=10,
    ):
        self.file_path = file_path
        self.data = None
        self.data_n = data_n
        self.plots = []
        self.symbol = symbol
        self.color_up = 'limegreen'
        self.color_down = 'tomato'
        self.macd_fast = macd_fast
        self.macd_slow = macd_slow
        self.macd_smooth = macd_smooth
        self.rsi_period = rsi_period
        self.bb_period = bb_period

    def get_macd(self, data):
        macd_n = self.data_n + max(self.macd_slow, self.macd_fast)
        macd_data = data[-macd_n:]
        fast_ema = macd_data.ewm(
            span=self.macd_fast, min_periods=self.macd_slow
        ).mean()
        slow_ema = macd_data.ewm(
            span=self.macd_slow, min_periods=self.macd_slow
        ).mean()
        macd = pd.Series(fast_ema - slow_ema, name='macd')
        macd_sig = pd.Series(
            macd.ewm(span=self.macd_smooth,min_periods=self.macd_smooth).mean(),
            name='macd_sig'
        )
        macd_hist = pd.Series(macd - macd_sig, name='macd_hist')

        return macd[-self.data_n:], macd_sig[-self.data_n:], macd_hist[-self.data_n:]

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
        df = pd.read_excel(self.file_path)
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

    def add_bb_plots(self, panel=0):
        data, plots = self.data, self.plots
        bb_n = self.data_n + self.bb_period
        bb_data = data[-bb_n:]
        data_cl = bb_data['Close'].values.tolist()
        bb_u = bb_up(data_cl, self.bb_period)[-self.data_n:]
        bb_l = bb_low(data_cl, self.bb_period)[-self.data_n:]
        bb_m = bb_mid(data_cl, self.bb_period)[-self.data_n:]

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

    def add_rsi_plot(self, panel=0):
        data, plots = self.data, self.plots
        rsi_n = self.data_n + self.rsi_period
        rsi_data = data[-rsi_n:]
        color_up, color_down = self.color_up, self.color_down
        rsi = RSI(rsi_data['Close'], period=self.rsi_period)[-self.data_n:]

        line_rsi = mplf.make_addplot(
            rsi, panel=panel, color='gray', ylabel='RSI', width=1.5,
        )

        line_os = mplf.make_addplot(
            [70] * self.data_n, panel=panel,
            color=color_down, alpha=.5, linestyle='dashed', width=1.5,
            secondary_y=False
        )
        line_ob = mplf.make_addplot(
            [30] * self.data_n,
            panel=panel,
            color=color_up, alpha=.5, linestyle='dashed', width=1.5,
            secondary_y=False,
            ylabel='RSI'
        )

        plots.extend([
            line_os, line_rsi, line_ob
        ])

    def add_vol_plots(self, vol_panel=2):
        color_up, color_down = self.color_up, self.color_down
        data, plots = self.data, self.plots
        vol_data = data[-self.data_n:]
        vol_colors = vol_data.apply(
            lambda x: color_up if x['Close'] > x['Open'] else color_down,
            axis=1
        )
        volume_plot = mplf.make_addplot(
            vol_data['Volume'],
            panel=vol_panel,
            color=vol_colors.values,
            type='bar',
            ylabel='Volume',
        )
        plots.append(volume_plot)

    def add_fractal_plot(self, panel=0):
        data, plots = self.data, self.plots
        color_up, color_down = self.color_up, self.color_down
        fr_data = data[-self.data_n:]
        ind = Indicators(fr_data)
        ind.fractals(column_name_high='fr_high', column_name_low='fr_low')
        fr_data = ind.df
        fr_data['fr_high'] = fr_data.apply(lambda x: x['Close'] * 1.08 if x['fr_high'] else np.nan, axis=1)
        fr_data['fr_low'] = fr_data.apply(lambda x: x['Close'] * 0.92 if x['fr_low'] else np.nan, axis=1)

        fr_high_plot = mplf.make_addplot(
            fr_data['fr_high'], panel=panel,
            color=color_down, width=1, type='step', alpha=.9,
            secondary_y=False,
        )
        fr_low_plot = mplf.make_addplot(
            fr_data['fr_low'], panel=panel,
            color=color_up, width=1, type='step', alpha=.9,
            secondary_y=False,

        )
        plots.extend([fr_high_plot, fr_low_plot])

    def create_candlestick_chart(self, step='1D'):
        self.add_rsi_plot(panel=0)
        self.add_bb_plots(panel=1)
        self.add_fractal_plot(panel=1)
        self.add_macd_plots(panel=2)
        self.add_vol_plots(vol_panel=3)
        custom_nc = self.get_nc_style()
        data_mpl = self.data[['Date', 'Open', 'Close', 'Volume', 'High', 'Low']][-self.data_n:]
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

    def show_plot(self, data_n=120, resample=False, step='1D'):
        self.process_data_mpl(resample=resample, step=step)
        self.data_n = data_n
        if not resample:
            step = '1D'
        fig, axlist = self.create_candlestick_chart(step=step)
        plt.show()

    def get_candlestick_fig(self, data_n=120, resample=False, step='1D'):
        self.process_data_mpl(resample=resample, step=step)
        self.data_n = data_n
        if not resample:
            step = '1D'
        fig, axlist = self.create_candlestick_chart(step=step)
        return fig, axlist
