#!/usr/bin/env python

__author__ = "Sk Farhad"
__copyright__ = "Copyright (c) 2021 The Python Packaging Authority"

import pandas as pd

from stocksurferbd import FundamentalData, PriceData, CandlestickPlot

hist_loader = PriceData()
hist_loader.save_current_csv(file_name='current_data.csv', market='CSE')
cur_df = pd.read_csv('current_data.csv')


comp_loader = FundamentalData()
comp_loader.save_company_data([
    'ACI', 'GP', 'WALTONHIL'
])


symbol = 'ACI'
file_name = 'ACI_history.csv'
hist_loader.save_history_csv(symbol=symbol, file_name=file_name, market='CSE')

cd_plot = CandlestickPlot(csv_path=file_name, symbol=symbol)
cd_plot.show_plot(xtick_count=120, resample=True, step='3D')


