import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from zipfile import ZipFile
import numpy as np
import pandas as pd
import pytz
import requests
import yfinance

INTRADAY_EXTENDED_URL = 'https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY_EXTENDED&interval=1min&slice=year1month1&apikey=D6T5YBJID9YYNA1D&symbol='
INTRADAY_URL = 'https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&interval=1min&apikey=D6T5YBJID9YYNA1D&symbol='


def from_logs(filename):
    result_dict = dict()

    with open(filename) as fp:

        for line in fp:
            json_str = line[25:].replace("'", "\"")
            line = json.loads(json_str)
            QuoteData = line["QuoteResponse"]["QuoteData"]
            for data in QuoteData:
                symbol = data["Product"]["symbol"]
                #ask = data["Intraday"]["ask"]
                #bid = data["Intraday"]["bid"]
                lastTrade = data["Intraday"]["lastTrade"]
                totalVolume = data["Intraday"]["totalVolume"]
                mytime = datetime.fromtimestamp(data["dateTimeUTC"], pytz.timezone('US/Eastern')).strftime('%Y%m%d%H%M%S')
                if symbol not in result_dict:
                    result_dict[symbol] = dict()
                    result_dict[symbol]["date"] = []
                    result_dict[symbol]["time"] = []
                    result_dict[symbol]["close"] = []
                    result_dict[symbol]["volume"] = []
                    result_dict[symbol]["source"] = []
                result_dict[symbol]["date"].append(int(mytime[:8]))
                result_dict[symbol]["time"].append(mytime)
                result_dict[symbol]["close"].append(lastTrade)
                result_dict[symbol]["volume"].append(totalVolume)
                result_dict[symbol]["source"].append("logs")

                #print (f'{mytime} {symbol} {ask} {bid} {lastTrade} {totalVolume}')
    return result_dict

def get_from_vantage(symbol):
    ny_date = datetime.now(pytz.timezone('US/Eastern')).strftime("%Y%m%d")
    with requests.Session() as s:
        symbol_url = f'{INTRADAY_EXTENDED_URL}{symbol}'
        filename = os.path.join('c:\\', 'WORK', 'Pystock', 'us', f'{symbol.lower()}_{ny_date}.txt')
        my_file = Path(filename)
        if not my_file.is_file():
            detailled_history = pd.read_csv(symbol_url)
            # print (detailled_history["time"])
            # print (type(detailled_history))
            detailled_history["time"] = pd.to_datetime(detailled_history["time"])
            detailled_history["time"] = detailled_history["time"].dt.strftime('%Y%m%d%H%M%S')  # '%Y%m%d%H%M%s'
            detailled_history['date'] = detailled_history['time'].str[:8].astype(int)
            detailled_history = detailled_history[::-1]
            detailled_history = detailled_history.drop(['high', 'open', 'low'], axis=1)
            detailled_history["source"] = "vantage"

            detailled_history.to_csv(filename, index_label=False)
        else:
            detailled_history = pd.read_csv(filename)
    detailled_history.reset_index()
    return (detailled_history)



def get_last_info_from_yahoo (symbol):
    ticker = yfinance.Ticker(symbol)
    # get stock info
    return ticker.info


def get_from_yahoo(symbol, shift=0):
    print("___________________ yahoo ______________________")
    start = (datetime.now(pytz.timezone('US/Eastern')) - timedelta(hours=shift)).strftime("%Y-%m-%d")
    end = (datetime.now(pytz.timezone('US/Eastern')) - timedelta(hours=shift) + timedelta(days=1)).strftime("%Y-%m-%d")

    #print(f'real start {start}')
    #print(f'real end {end}')

    if shift == 0:
        detailled_history = yfinance.download(tickers=symbol, period="1d", interval="1m")
    else:
        detailled_history = yfinance.download(tickers=symbol, start=start, end=end, interval="1m")

    detailled_history = detailled_history.reset_index()
    detailled_history["time"] = (pd.to_datetime(detailled_history["Datetime"]) + timedelta(hours=shift)).dt.strftime('%Y%m%d%H%M%S')  # '%Y%m%d%H%M%s'
    detailled_history['date'] = detailled_history['time'].str[:8].astype(int)
    detailled_history["time"] = detailled_history["time"].astype(np.int64)
    detailled_history = detailled_history.drop(['Open', 'High', 'Low', 'Adj Close', 'Datetime'], axis=1)
    detailled_history.rename(columns={'Close': 'close', 'Volume': 'volume'}, inplace=True)
    detailled_history["source"][:-1] = "yahoo"
    detailled_history.reset_index()
    return detailled_history


def get_from_stooq(symbol):
    filename = os.path.join('c:\\', 'WORK', 'Pystock', 'us', f'{symbol.lower()}.us.txt')
    my_file = Path(filename)
    if not my_file.is_file():
        zipfilename = os.path.join('c:\\', 'WORK', 'Pystock', 'us', '5_us_txt.zip')

        with ZipFile(zipfilename, 'r') as zipObj:
            listOfFileNames = zipObj.namelist()
            for f in listOfFileNames:
                if f.endswith(f'/{symbol.lower()}.us.txt'):
                    print(f'f {f}')
                    zipInfo = zipObj.getinfo(f)
                    print(f'zipInfo {zipInfo}')
                    zipInfo.filename = os.path.basename(f'{symbol.lower()}.us.txt')
                    zipObj.extract(zipInfo, os.path.join('c:\\', 'WORK', 'Pystock', 'us'))
                    # zipObj.extract(f, os.path.join('c:\\', 'WORK', 'Opy', 'us'))
    detailled_history = pd.read_csv(filename)
    detailled_history.rename(columns={'<CLOSE>': 'close', '<DATE>': 'date', '<TIME>': 'time'}, inplace=True)

    detailled_history["datetime"] = detailled_history["date"].astype(str) + detailled_history["time"].astype(str)
    detailled_history["source"][:-1] = "stooq"
    detailled_history.reset_index()
    return (detailled_history)


def concatenate(a, b):
    first_b_time = int(b.iloc[0]['time'])
    print (f' concatenate, junction on {first_b_time} ')
    first_b_time_index = -1
    first_b_time_index = np.where (a['time'] >= first_b_time )[0][0]
    #except:
    #    first_b_time_index = -1
    #    print (f'concatenate first index not found')#not found

    print (f'concatenate {first_b_time_index}')#not found

    frames = [a[:first_b_time_index], b]
    c = pd.concat(frames, ignore_index=True)
    c = c.reset_index()
    return c


def get_from_vantage_and_yahoo(symbol):
    vantage_data_frame = get_from_vantage(symbol)
    yahoo_data_frame = get_from_yahoo(symbol)
    c = concatenate(vantage_data_frame, yahoo_data_frame)
    #print(f'{c}')
    return c

def get_from_vantage_and_logs(symbol, logfilename):
    vantage_data_frame = get_from_vantage(symbol)
    logs_data_frame = get_from_logs(symbol, logfilename)
    c = concatenate(vantage_data_frame, logs_data_frame)


    return c



def get_from_logs(symbol, logfilename):
    data_dict = from_logs(logfilename)
    df = pd.DataFrame(data_dict[symbol])
    #print (df)
    return df

get_from_vantage_and_logs('TSLA', 'etrade_20211112.log')
#get_from_vantage_and_yahoo('TSLA')

# c = get_from_yahoo('TSLA', 49)
# print (c)
