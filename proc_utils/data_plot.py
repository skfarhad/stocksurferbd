import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
import pandas as pd


def plot_values_acf(daily, monthly, info=None, filter_key='SalesQTY'):

    plt.figure(figsize=(18, 10), dpi=80)
    plt.subplot(211)
    plt.plot(daily['InvoiceDate'], daily[filter_key], 'ro')
    plt.xticks(rotation=70)
    plt.title('Total Purchases: ' + str(len(daily[filter_key])))
    plt.xlabel('dates')
    plt.ylabel('Daily Sales')
    plt.grid()

    plt.subplot(223)
    plt.plot(monthly['InvoicePeriod'], monthly[filter_key], 'ro-')
    plt.xticks(rotation=70)
    plt.xlabel('Months')
    plt.ylabel('Monthly Sales')
    plt.grid()

    plt.subplot(224)
    acf_data = np.array(monthly.loc[:, filter_key].values)
    acf_data = acf_data.astype(np.float)
    # print(acf_data)
    max_lag = len(acf_data) // 2
    plt.acorr(acf_data, maxlags=max_lag, usevlines=True, normed=True, lw=2)
    plt.xlabel('Lags')
    plt.xlim(0, max_lag)
    plt.ylabel(f'Autocorrelation(Montly {filter_key})')
    plt.grid()

    plt.show()
