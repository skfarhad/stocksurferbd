## Description
This is a Python library based on *beautifulsoup4* and *pandas* 
to download price data and fundamental data of companies from  
Dhaka Stock Exchange.
<br/>This can assist you to create further analyses 
based on fundamental and price history data.
## Installation
```
pip install dse-data-loader

```
## Usage

#### Downloading historical price data of a single stock-

```
from dse_data_loader import PriceData
loader = PriceData()

loader.save_history_csv('ACI', file_name='ACI_history.csv')
```

The above code will create a file named- 'ACI_history.csv'. 
It'll contain historical price data for ACI Limited. 'ACI' is the stock symbol.


#### Downloading current price data of all listed companies in DSE-
```
from dse_data_loader import PriceData
loader = PriceData()

loader.save_current_csv(file_name='current_data.csv')
```
The above code will create a file named- 'ACI_history.csv' in the current folder. 
It'll contain current price data for all symbols.

#### Downloading fundamental data for a list of companies available in DSE-

```
from dse_data_loader import FundamentalData
loader = FundamentalData()

loader.save_company_data(['ACI', 'GP', 'WALTONHIL'], path='company_info')

```
The above code will create two files named 'company_data.csv' & 
'financial_data.csv' in the 'company_info' folder relative to 
current directory. The file named company_data.csv contains 
the fundamental data of ACI Limited, GP and Walton BD for the current year and
financial_data.csv contains year-wise fundamental data 
according to [DSE website](http://dsebd.org).

This is the minimal documentation. It'll be improved continuously (hopefully!). 
