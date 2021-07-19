## Description
This is a Python library based on *beautifulsoup4*, *pandas* &
*mplfinance* to download price data and fundamental data of companies from  
Dhaka Stock Exchange.
<br/>This can assist you to create further analyses 
based on fundamental and price history data. 
<br/>Also create Candlestick charts to analyse price history of stocks using a simple wrapper for mplfinance.
## Installation
```
pip install dse-data-loader

```
## Usage

#### Downloading historical price data of a single stock-

```python
from stocksurferbd import PriceData
loader = PriceData()

loader.save_history_csv('ACI', file_name='ACI_history.csv')
```

The above code will create a file named- 'ACI_history.csv'. 
It'll contain historical price data for ACI Limited. 'ACI' is the stock symbol.


#### Downloading current price data of all listed companies in DSE-
```python
from stocksurferbd import PriceData
loader = PriceData()

loader.save_current_csv(file_name='current_data.csv')
```
The above code will create a file named- 'ACI_history.csv' in the current folder. 
It'll contain current price data for all symbols.

#### Downloading fundamental data for a list of companies available in DSE-

```python
from stocksurferbd import FundamentalData
loader = FundamentalData()

loader.save_company_data(['ACI', 'GP', 'WALTONHIL'], path='company_info')

```
The above code will create two files named 'company_data.csv' & 
'financial_data.csv' in the 'company_info' folder relative to 
current directory. The file named company_data.csv contains 
the fundamental data of ACI Limited, GP and Walton BD for the current year and
financial_data.csv contains year-wise fundamental data 
according to [DSE website](http://dsebd.org).


#### Create Candlestick charts for analyzing price history-

```python

from stocksurferbd import CandlestickPlot

cd_plot = CandlestickPlot(csv_path='ACI_history.csv', symbol='ACI')
cd_plot.show_plot(
    xtick_count=120, 
    resample=True, 
    step='3D'
)
```

The above code will create a Candlestick plot like the ones provided by 
Stock broker trading panels. There are 3 parameters-

1. ```xtick_count``` : Provide an integer value. 
   It sets the count of how many recent data points needs to be plotted.
2. ```resample``` : Provide boolean ```True``` or ```False```. 
   Set ```True``` if you want to plot daily data aggregated by multiple days.
3. ```step```: Only Active when ```resample=True```. 
   Valid values are in the form- 
   ```'3D'``` and ```'7D'``` for 3 days plots and weekly plots respectively.

The following are some example images of Candlestick plots-

![Candlestick Plot](https://github.com/skfarhad/stocksurferbd/blob/master/example_plot.jpg?raw=true)
<br><br>![Candlestick Plot 3days](https://github.com/skfarhad/stocksurferbd/blob/master/example_plot_3D.jpg?raw=true)

This is the minimal documentation. It'll be improved continuously (hopefully!). 
