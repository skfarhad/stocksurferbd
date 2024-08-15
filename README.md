## Description
This is a Python library based on *beautifulsoup4*, *pandas* &
*mplfinance*.
<br> You may use it to download price history and fundamental information of companies from 
Dhaka Stock Exchange and Chittagong Stock Exchange.
<br>This can assist you to create further analyses 
based on fundamental and price history data. 
<br>Also create Candlestick charts to analyse the price history of stocks using 
this easy-to-use wrapper for mplfinance.
## Installation
```
pip install stocksurferbd

```
## Usage

#### Downloading historical price data of a single stock-

```python
from stocksurferbd import PriceData
loader = PriceData()

loader.save_history_csv(symbol='ACI', file_name='ACI_history.csv', market='DSE')
```

The above code will create a file named- `ACI_history.csv`. 
It'll contain historical price data for ACI Limited in Dhaka Stock Exchange (DSE).


There are 3 parameters for this method-

1. ```symbol``` : Provide stock symbol of the company as string.
2. ```file_name``` : Provide the name of the history data file as string. 
3. ```market```: Provide the market name as string from which you want to download the data. 
Probable values are ```'CSE'``` and ```'DSE'```


#### Downloading current market price data of all listed companies in DSE/CSE-
```python
from stocksurferbd import PriceData
loader = PriceData()

loader.save_current_csv(file_name='current_data.csv', market='DSE')
```
The above code will create a file named- `current_history.csv` in the current folder. 
It'll contain current price data for all symbols.

There are 2 parameters for this method-

1. ```file_name``` : Provide the name of the current price data file as string. 
2. ```market```: Provide the market name as string from which you want to download the data. 
Probable values ar ```'CSE'``` and ```'DSE'```

#### Downloading fundamental data for a list of companies available in DSE-

```python
from stocksurferbd import FundamentalData
loader = FundamentalData()

loader.save_company_data('ACI', path='company_info')

```
The above code will create two files named `ACI_company_data.csv` & 
`ACI_financial_data.csv` in the `company_info` folder relative to 
current directory. The file named `ACI_company_data.csv` contains 
the fundamental data of ACI Limited for the current year and
`ACI_financial_data.csv` contains year-wise fundamental data according to [DSE website](http://dsebd.org).

There are 2 parameters `save_company_data()` this method-

1. ```symbol``` : Provide stock symbol of the company as string.
2. ```path``` : Provide the name of the directory as string to save the company data. 

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
Stock broker trading panels. 

<br/>There are 2 parameters ```__init__()``` method of CandlestickPlot class-

1. ```csv_path``` : Provide the path of history csv file as string to generate plot
2. ```symbol``` : Provide stock symbol of the company as string.

<br/>There are also 3 parameters show_plot() method-

1. ```xtick_count``` : Provide an integer value. 
   It sets the count of how many recent data points needs to be plotted.
2. ```resample``` : Provide boolean ```True``` or ```False```. 
   Set ```True``` if you want to plot daily data aggregated by multiple days.
3. ```step```: Only Active when ```resample=True```. 
   Valid values are in the form- 
   ```'3D'``` and ```'7D'``` for 3 days plots and weekly plots respectively.

The following are some example images of Candlestick plots-

![Candlestick Plot](https://github.com/skfarhad/stocksurferbd/blob/master/price_plot_1d.png?raw=true)
<br><br>![Candlestick Plot 3days](https://github.com/skfarhad/stocksurferbd/blob/master/price_plot_3d.png?raw=true)



## If you want to contribute

Any contribution would be highly appreciated. Kindly go through the 
[guidelines for contributing](CONTRIBUTING.md).
