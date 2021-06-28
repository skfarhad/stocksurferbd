import time
import os

from selenium import webdriver
from bs4 import BeautifulSoup
import pandas as pd
import requests
import datetime


END_DATE = str(datetime.datetime.now().date())
DSE_COMPANY_URL = "http://dsebd.org/displayCompany.php?name="
CURRENT_PRICE_URL = 'https://www.dsebd.org/dseX_share.php'


def parse_float(str_val):
    new_val = str_val.replace(
        ',', ''
    ).replace('--', '0')
    return float(new_val)


def parse_int(str_val):
    new_val = str_val.replace(
        ',', ''
    ).replace('--', '0')
    return int(new_val)


def append_company(company_info, fin_interim_info, df_company, symbol):
    company_dict = {
        'symbol': symbol,
        'auth_capital': company_info['basic'][0][0],
        'trade_start': company_info['basic'][0][1],
        'paid_up_capital': company_info['basic'][1][0],
        'instrument_type': company_info['basic'][1][1],
        'face_value': company_info['basic'][2][0],
        'market_lot': company_info['basic'][2][1],
        'ltp': company_info['ltp'],
        'market_cap': company_info['market_cap'],
        'outstanding_share': company_info['basic'][3][0],
        'sector': company_info['basic'][3][1],
        'right_issue': company_info['dividend'][2][0],
        'year_end': company_info['dividend'][3][0],
        'reserve_w_oci': company_info['dividend'][4][0],
        'others_oci': company_info['dividend'][5][0],
        # 'present_st_loan',
        # 'present_lt_loan',
        'cash_dividend_p': company_info['dividend'][0][0].split(',')[0].split('%')[0] \
            if len(company_info['dividend'][0][0]) > 6 else '-',
        'cash_dividend_year': company_info['dividend'][0][0].split(',')[0].split('%')[1] \
            if len(company_info['dividend'][0][0]) > 6 else '-',
        'stock_dividend_p': company_info['dividend'][1][0].split(',')[0].split('%')[0] \
            if len(company_info['dividend'][1][0]) > 6 else '-',
        'stock_dividend_year': company_info['dividend'][1][0].split(',')[0].split('%')[1] \
            if len(company_info['dividend'][1][0]) > 6 else '-',
        'listing_year': company_info['other'][0][1],
        'market_category': company_info['other'][1][1],
        'sh_director': company_info['other'][3][1].split(' ')[0].split(':')[1],
        'sh_govt': company_info['other'][3][1].split(' ')[1].split(':')[1],
        'sh_inst': company_info['other'][3][1].split(' ')[2].split(':')[1],
        'sh_foreign': company_info['other'][3][1].split(' ')[3].split(':')[1],
        'sh_public': company_info['other'][3][1].split(' ')[4].split(':')[1],

        'turnover_q1': fin_interim_info['main'][4][1],
        'turnover_q2': fin_interim_info['main'][4][2],
        'turnover_q3': fin_interim_info['main'][4][4],
        'profit_cop_q1': fin_interim_info['main'][5][1],
        'profit_cop_q2': fin_interim_info['main'][5][2],
        'profit_cop_q3': fin_interim_info['main'][5][4],
        'profit_period_q1': fin_interim_info['main'][6][1],
        'profit_period_q2': fin_interim_info['main'][6][2],
        'profit_period_q3': fin_interim_info['main'][6][4],
        'tci_period_q1': fin_interim_info['main'][7][1],
        'tci_period_q2': fin_interim_info['main'][7][2],
        'tci_period_q3': fin_interim_info['main'][7][4],
        'eps_basic_q1': fin_interim_info['main'][9][1],
        'eps_basic_q2': fin_interim_info['main'][9][2],
        'eps_basic_q3': fin_interim_info['main'][9][4],
        'eps_diluted_q1': fin_interim_info['main'][10][1],
        'eps_diluted_q2': fin_interim_info['main'][10][2],
        'eps_diluted_q3': fin_interim_info['main'][10][4],
        'eps_cop_basic_q1': fin_interim_info['main'][12][1],
        'eps_cop_basic_q2': fin_interim_info['main'][12][2],
        'eps_cop_basic_q3': fin_interim_info['main'][12][4],
        'eps_cop_diluted_q1': fin_interim_info['main'][13][1],
        'eps_cop_diluted_q2': fin_interim_info['main'][13][2],
        'eps_cop_diluted_q3': fin_interim_info['main'][13][4],
        'price_period_q1': fin_interim_info['main'][14][1],
        'price_period_q2': fin_interim_info['main'][14][2],
        'price_period_q3': fin_interim_info['main'][14][4],
    }
    try:
        df_company = df_company.append(company_dict, ignore_index=True)
    except Exception as e:
        print(str(e))

    return df_company


def append_fin_perf(fin_perf_info, df_fin_perf, symbol):
    for eps, pe in zip(fin_perf_info['eps'][3:], fin_perf_info['pe'][4:]):
        i = 0
        if len(eps) > 13:
            i = 1

        eps_dict = {
            'symbol': symbol,
            'year': " ".join(eps[0:i+1]) if i else eps[0],
            'eps_original': eps[i + 1],
            'eps_restated': eps[i + 2],
            'eps_diluted': eps[i + 3],
            'eps_cop_original': eps[i + 4],
            'eps_cop_restated': eps[i + 5],
            'eps_cop_diluted': eps[i + 6],
            'nav_original': eps[i + 7],
            'nav_restated': eps[i + 8],
            'nav_diluted': eps[i + 9],
            'pco': eps[i + 10],
            'profit': eps[i + 11],
            'tci': eps[i + 12],

            'pe_original': pe[i + 1],
            'pe_restated': pe[i + 2],
            'pe_diluted': pe[i + 3],
            'pe_cop_original': pe[i + 4],
            'pe_cop_restated': pe[i + 5],
            'pe_cop_diluted': pe[i + 6],

            'dividend_p': pe[i + 7],
            'dividend_yield_p': pe[i + 8]
        }
        # print(eps_dict['year'])
        try:
            df_fin_perf = df_fin_perf.append(eps_dict, ignore_index=True)
        except Exception as e:
            print(str(e))

    return df_fin_perf


def pe_data_columns():
    return [
        'symbol',
        'pe_basic_audited',
        'pe_diluted_audited',
        'pe_basic_unaudited',
        'pe_diluted_unaudited',
    ]


def dividend_data_columns():
    return [
        'symbol',
        'year',
        'type',
        'percent',
    ]


def financial_perf_columns():
    return [
        'symbol',
        'year',
        'eps_original',
        'eps_restated',
        'eps_diluted',
        'eps_cop_original',
        'eps_cop_restated',
        'eps_cop_diluted',
        'nav_original',
        'nav_restated',
        'nav_diluted',
        'pco',
        'profit',
        'tci',

        'pe_original',
        'pe_restated',
        'pe_diluted',
        'pe_cop_original',
        'pe_cop_restated',
        'pe_cop_diluted',

        'dividend_p',
        'dividend_yield_p'
    ]


def parse_company_data_rows(soup, symbol, df_company, df_fin_perf):

    company_info = {}
    fin_perf_info = {}
    fin_interim_info = {}

    company_tables = soup.find_all(
        "table",
        attrs={
            "class": "table table-bordered background-white",
        }
    )
    count = 1
    for table in company_tables:
        # print(">>>>>>>>>Contents in table no: ", count)
        table_rows = table.find_all("tr")
        # print(table_rows)
        # if count not in (1, ):
        cur_list = []
        for row in table_rows:
            row_data = [" ".join(td.get_text().split()) for td in row.find_all("td")]
            cur_list.append(row_data)
        # print(cur_list)

        if count == 1:
            company_info.update({
                'ltp': cur_list[0][1],
                'market_cap': cur_list[6][1]
            })

        if count == 2:
            company_info.update({
                'basic': cur_list
            })
        elif count == 3:
            company_info.update({
                'dividend': cur_list
            })
        elif count == 10:
            company_info.update({
                'other': cur_list
            })

        elif count == 4:
            fin_interim_info.update({
                'main': cur_list
            })
        elif count == 5:
            fin_interim_info.update({
                'pe_audited': cur_list
            })
        elif count == 6:
            fin_interim_info.update({
                'pe_unaudited': cur_list
            })

        elif count == 7:
            fin_perf_info.update({
                'eps': cur_list
            })

        elif count == 8:
            fin_perf_info.update({
                'pe': cur_list
            })
        else:
            pass

        count += 1

    df_company = append_company(
        company_info=company_info,
        fin_interim_info=fin_interim_info,
        df_company=df_company,
        symbol=symbol
    )

    df_fin_perf = append_fin_perf(
        fin_perf_info=fin_perf_info,
        df_fin_perf=df_fin_perf,
        symbol=symbol
    )

    return df_company, df_fin_perf


def extract_company_data(symbol, df_company, df_fin_perf):
    full_url = DSE_COMPANY_URL + symbol
    # driver = webdriver.Chrome(executable_path="./chromedriver_linux64/chromedriver")
    # driver.get(page)
    target_page = requests.get(full_url, verify=False)
    bs_data = BeautifulSoup(target_page.text, 'html.parser')
    # print(bs_data)
    df_company, df_fin_perf = parse_company_data_rows(bs_data, symbol, df_company, df_fin_perf)
    return df_company, df_fin_perf


def get_all_company_data():
    df = pd.read_csv('dsebd_current_stock_data.csv')
    symbols = df['TRADING_CODE'].values
    df_company = pd.DataFrame()
    df_fin_perf = pd.DataFrame()
    count = 0
    for sym in symbols:
        print('Downloading ' + sym + " data.....")
        df_company, df_fin_perf = extract_company_data(sym, df_company, df_fin_perf)
        print('Downloading ' + sym + " Finished!")
        # if count > 10:
        #     break
        count += 1
    print('Data extraction finished')

    df_company.to_pickle('all_company.p')
    df_fin_perf.to_pickle('all_fin_perf.p')


get_all_company_data()

# extract_company_data('AMARNET')
