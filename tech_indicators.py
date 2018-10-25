from_symbol = 'BTC'
to_symbol = 'USD'
exchange = 'Bitstamp'
datetime_interval = 'day'

import requests
from datetime import datetime

import pandas as pd
import numpy as np


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

df.to_csv("trends.csv", index=True, sep=';')


def read_column(filename, header):
    column = pd.read_csv(filename, sep=';')
    return column[header]

column = read_column ('BTC_USD_Bitstamp_day_2018-10-25.csv','low')
print (column)

