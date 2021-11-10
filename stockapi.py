import pandas_datareader
import requests
import pandas as pd
import numpy as np
import os
from pathlib import Path
from datetime import datetime, timedelta
import pytz
from zipfile import ZipFile
import yfinance
from pandas_datareader import data
import matplotlib.pyplot as plt
import pandas as pd


INTRADAY_EXTENDED_URL = 'https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY_EXTENDED&interval=1min&slice=year1month1&apikey=D6T5YBJID9YYNA1D&symbol='
INTRADAY_URL = 'https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&interval=1min&apikey=D6T5YBJID9YYNA1D&symbol='


def get_from_vantage(symbol):
    ny_date = datetime.now(pytz.timezone('US/Eastern')).strftime("%Y%m%d")
    with requests.Session() as s:
        symbol_url = f'{INTRADAY_EXTENDED_URL}{symbol}'
        filename = os.path.join('c:\\', 'WORK', 'Pystock', 'us', f'{symbol.lower()}_{ny_date}.txt')
        my_file = Path(filename)
        if not my_file.is_file():
            detailled_history = pd.read_csv(symbol_url)
            #print (detailled_history["time"])
            #print (type(detailled_history))
            detailled_history["datetime"] = pd.to_datetime(detailled_history["time"])
            detailled_history["datetime"] = detailled_history["datetime"].dt.strftime('%Y%m%d%H%M%S')  # '%Y%m%d%H%M%s'
            detailled_history['date'] = detailled_history['datetime'].str[:8]
            detailled_history = detailled_history[::-1]
            detailled_history = detailled_history.drop(['high', 'open', 'low'], axis=1)

            detailled_history.to_csv(filename, index_label=False )
        else:
            detailled_history = pd.read_csv(filename)
    return (detailled_history)

def get_from_yahoo2 (symbol):
    print ("___________________ yahoo ______________________")
    detailled_history = yfinance.download(tickers=symbol, period="1d", interval="1m")
    print (f'detailled_history\n {detailled_history}')

    detailled_history = detailled_history.reset_index()
    detailled_history["datetime"] = pd.to_datetime(detailled_history["Datetime"])
    detailled_history["datetime"] = detailled_history["datetime"].dt.strftime('%Y%m%d%H%M%S')  # '%Y%m%d%H%M%s'
    detailled_history['date'] = detailled_history['datetime'].str[:8].astype(int)
    detailled_history = detailled_history.drop([ 'Open', 'High', 'Low', 'Adj Close'], axis=1)
    detailled_history.rename(columns={'Close': 'close', 'Datetime' : 'time', 'Volume':'volume'}, inplace=True)
    return detailled_history



def get_from_yahoo (symbol, shift = 0):
    print ("___________________ yahoo ______________________")
    start = (datetime.now(pytz.timezone('US/Eastern')) -  timedelta(hours=shift) ).strftime("%Y-%m-%d")
    end = (datetime.now(pytz.timezone('US/Eastern')) -  timedelta(hours=shift) + timedelta(days=1)).strftime("%Y-%m-%d")

    print (f'real start {start}')
    print (f'real end {end}')

    if shift == 0:
        detailled_history = yfinance.download(tickers=symbol, period="1d", interval="1m")
    else:
        detailled_history = yfinance.download(tickers=symbol, start=start, end=end, interval="1m")


    detailled_history = detailled_history.reset_index()
    detailled_history["time"] = (pd.to_datetime(detailled_history["Datetime"]) +  timedelta(hours=shift)).dt.strftime('%Y%m%d%H%M%S')  # '%Y%m%d%H%M%s'
    detailled_history['date'] = detailled_history['time'].str[:8].astype(int)
    detailled_history = detailled_history.drop([ 'Open', 'High', 'Low', 'Adj Close', 'Datetime'], axis=1)
    detailled_history.rename(columns={'Close': 'close', 'Volume':'volume'}, inplace=True)
    return detailled_history


def get_from_stooq (symbol):
    filename = os.path.join('c:\\', 'WORK', 'Pystock', 'us', f'{symbol.lower()}.us.txt')
    my_file = Path(filename)
    if not my_file.is_file():
        zipfilename = os.path.join('c:\\', 'WORK', 'Pystock', 'us', '5_us_txt.zip')

        with ZipFile(zipfilename, 'r') as zipObj:
            listOfFileNames = zipObj.namelist()
            for f in listOfFileNames:
                if f.endswith(f'/{symbol.lower()}.us.txt'):
                    print (f'f {f}')
                    zipInfo = zipObj.getinfo(f)
                    print (f'zipInfo {zipInfo}')
                    zipInfo.filename = os.path.basename(f'{symbol.lower()}.us.txt')
                    zipObj.extract(zipInfo, os.path.join('c:\\', 'WORK', 'Pystock', 'us'))
                    #zipObj.extract(f, os.path.join('c:\\', 'WORK', 'Opy', 'us'))
    detailled_history = pd.read_csv(filename)
    detailled_history.rename(columns={'<CLOSE>': 'close', '<DATE>': 'date', '<TIME>': 'time'}, inplace=True)

    detailled_history["datetime"] = detailled_history["date"].astype(str) + detailled_history["time"].astype(str)

    return (detailled_history)

def concatenate (a,b):
    frames = [a, b]
    c = pd.concat(frames, ignore_index=True)
    c = c.reset_index()
    return c

def get_from_vantage_and_yahoo(symbol):
    a = get_from_vantage(symbol)
    b = get_from_yahoo(symbol)
    c = concatenate (a,b)
    return c


#c = get_from_yahoo('TSLA', 49)
#print (c)
