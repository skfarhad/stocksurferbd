## Description
This is a Python library based on *beautifulsoup4* and *pandas* to 
download price data and fundamental data of companies from  Dhaka Stock Exchange.
<br/>This can assist you to create further analyses based on fundamental and price history data.
##Installation
```
pip install dse-data-loader

```
##Usage

Downloading fundamental data of a company-

```
from dse_data_loader import FundamentalData
loader = FundamentalData()

loader.save_company_data(['ACI'])

```
The above code will crete two files named 'company_data.csv' & 'financial_data.csv' in current folder.
The file named company_data.csv contains the fundamental data for current year
financial_data.csv contains year wise fundmental data according to [DSE website](http://dsebd.org).

Downloading historical price data of a stock-

```
from dse_data_loader import PriceData
loader = PriceData()

loader.save_history_csv('ACI', file_name='ACI_history.csv')
```

The above code will create a file named- 'ACI_history.csv'. 
It'll contain historical price data for ACI Limited. 'ACI' is the stock symbol.


Downloading current price data for all stocks-
```
from dse_data_loader import PriceData
loader = PriceData()

loader.save_current_csv(file_name='current_data.csv')
```
The above code will create a file named- 'ACI_history.csv'. It'll contain current price data for all symbols.

This is the minimal documentation. It'll be improved continuously (hopefully!). 
