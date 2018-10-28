import requests
import csv

from datetime import datetime

import pandas as pd

from_symbol = 'BTC'
to_symbol = 'USD'
exchange = 'Bitstamp'
datetime_interval = 'day'

def get_filename(from_symbol, to_symbol, exchange, datetime_interval, download_date):
    return '%s_%s_%s_%s_%s.csv' % (from_symbol, to_symbol, exchange, datetime_interval, download_date)


def download_data(from_symbol, to_symbol, exchange, datetime_interval):
    supported_intervals = {'minute', 'hour', 'day'}
    assert datetime_interval in supported_intervals,\
        'datetime_interval should be one of %s' % supported_intervals

    print('Downloading %s trading data for %s %s from %s' %
          (datetime_interval, from_symbol, to_symbol, exchange))
    base_url = 'https://min-api.cryptocompare.com/data/histo'
    url = '%s%s' % (base_url, datetime_interval)

    params = {'fsym': from_symbol, 'tsym': to_symbol,
              'limit': 2000, 'aggregate': 1,
              'e': exchange}
    request = requests.get(url, params=params)
    data = request.json()
    return data


def convert_to_dataframe(data):
    df = pd.io.json.json_normalize(data, ['Data'])
    df['datetime'] = pd.to_datetime(df.time, unit='s')
    df = df[['datetime', 'low', 'high', 'open',
             'close', 'volumefrom', 'volumeto']]
    return df


def filter_empty_datapoints(df):
    indices = df[df.sum(axis=1) == 0].index
    print('Filtering %d empty datapoints' % indices.shape[0])
    df = df.drop(indices)
    return df


data = download_data(from_symbol, to_symbol, exchange, datetime_interval)
df = convert_to_dataframe(data)
df = filter_empty_datapoints(df)

current_datetime = datetime.now().date().isoformat()
filename = get_filename(from_symbol, to_symbol, exchange, datetime_interval, current_datetime)
print('Saving data to %s' % filename)
df.to_csv(filename, index=False, sep=';')



def read_dataset(filename):
    print('Reading data from %s' % filename)
    df = pd.read_csv(filename, sep=';')
    df.datetime = pd.to_datetime(df.datetime) # change type from object to datetime
    df = df.set_index('datetime')
    df = df.sort_index() # sort by datetime
    print(df.shape)
    return df

df = read_dataset(filename)

from stockstats import StockDataFrame
df = StockDataFrame.retype(df)
df['macd'] = df.get('macd') # calculate MACD
df['rsi_14'] = df.get('rsi_14')
df['wr_14'] = df.get('wr_14')
df['kdjk3'] = df.get('kdjk_3')
df['kdjd3'] = df.get('kdjd_3')
df['kdjj3'] = df.get('kdjj_3')
df['kdjk14'] = df.get('kdjk_14')
df['kdjd14'] = df.get('kdjd_14')
df['kdjj14'] = df.get('kdjj_14')
df['trix'] = df.get('trix')
df['adx'] = df.get('adx')
df['cci'] = df.get('cci')

#########################################

df['close_15_sma'] = df.get('close_15_sma')

df.to_csv("indicators.csv", index=True, sep=';')


def read_column(filename, header):
    column = pd.read_csv(filename, sep=';')
    return column[header]

def sma_trend(column, index):
    counter_rise = 0
    counter_fall = 0

    for i in range(4):
        if column[index] < column[index + 1]:
            counter_fall = 0
            counter_rise += 1
        elif column[index] > column[index + 1]:
            counter_rise = 0
            counter_fall += 1
        elif column[index] == column[index + 1]:
            counter_rise += 1
            counter_fall += 1
        index += 1
    if counter_rise == 4 and counter_fall != 4:
        return 1
    elif counter_fall == 4 and counter_rise != 4:
        return -1
    else:
        return 0

def close_trend(column_close, column_sma, index):
    close_leads = 0
    close_lags = 0

    for i in range(5):
        if column_close[index] < column_sma[index]:
            close_leads = 0
            close_lags += 1
        elif column_close[index] > column_sma[index]:
            close_lags = 0
            close_leads += 1
        elif column_close[index] == column_sma[index]:
            close_lags += 1
            close_leads += 1
        index += 1
    if close_leads == 5 and close_lags != 5:
        return 1
    elif close_lags == 5 and close_leads != 5:
        return -1
    else:
        return 0

def get_trends(closing_price, close_15_sma):
    result = []
    for index in range(len(closing_price)):
        if index == 0:
            index = 4
        if close_trend(closing_price, close_15_sma, index - 4) == 1 and sma_trend(close_15_sma, index - 4) == 1:
            result.append('up')
        elif close_trend(closing_price, close_15_sma, index - 4) == -1 and sma_trend(close_15_sma, index - 4) == -1:
            result.append('down')
        else:
            result.append('no')
    return result

close = read_column('indicators.csv', 'close')
close_15_sma = read_column('indicators.csv', 'close_15_sma')


close_vals = close.get_values()
close_15_sma_vals = close_15_sma.get_values()
trends = get_trends(close_vals, close_15_sma_vals)

def get_trading_signals(closing_price, trends):
    TR = []
    for i in range(len(trends)):
        cp = []
        for a in range(3):
            if i + a < len(trends):
                cp.append(closing_price[i + a])
        if trends[i] == "up":
            TR.append((closing_price[i] - min(cp))/(max(cp) - min(cp))* 0.5 + 0.5)
        else:
            TR.append((closing_price[i] - min(cp))/(max(cp) - min(cp))* 0.5)
    return TR

tradin_signals = get_trading_signals(close_vals, trends)

with open("trends.csv", "w", newline="") as csv_file:
    columns = ["Time series", "Closing price", "MA", "Trend", "Trading signal"]
    writer = csv.DictWriter(csv_file, fieldnames=columns, delimiter=";", lineterminator='\n')
    writer.writeheader()
    for i in range(len(trends)):
        line = {"Time series": i+1, "Closing price": close_vals[i], "MA": close_15_sma_vals[i], "Trend": trends[i], "Trading signal": tradin_signals[i]}
        writer.writerow(line)
