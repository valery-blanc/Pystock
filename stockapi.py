import fnmatch
import glob
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
from fabric.connection import Connection
from fabric.transfer import Transfer

import common

global QUOTES_LOG_DICT

# noinspection PyRedeclaration
QUOTES_LOG_DICT = dict()


def synchronize_etrade_numbers_from_server(filenames='etrade_*.log'):
    TANA_ETRADE_NUMBERS_BASE_DIRECTORY = common.get_param('TANA_ETRADE_NUMBERS_BASE_DIRECTORY', '/home/val/PycharmProject/Numbers/etrade_logs/')
    ETRADE_NUMBERS_BASE_DIRECTORY = common.get_param('ETRADE_NUMBERS_BASE_DIRECTORY')
    c = Connection(host="val@TANA.local", connect_kwargs={"password": "Manon888"})
    listdir = c.sftp().listdir(TANA_ETRADE_NUMBERS_BASE_DIRECTORY)
    remote_list = fnmatch.filter(listdir, f'{filenames}')
    # print (f'remote_list {remote_list}')
    filenames = os.path.join(ETRADE_NUMBERS_BASE_DIRECTORY, filenames)
    local_list = [os.path.basename(x) for x in glob.glob(filenames)]
    # print (f'local_list before {local_list}')

    local_directory = os.path.join(common.get_param('ETRADE_NUMBERS_BASE_DIRECTORY'), '')
    for file in remote_list:
        if file not in local_list:
            # print (f'missing {file}')
            Transfer(c).get(f'{TANA_ETRADE_NUMBERS_BASE_DIRECTORY}/{file}', local=local_directory)
            print(f'transfered {file}')
    print('etrade number files synchronized with TANA')
    # local_list = [os.path.basename(x) for x in glob.glob(filenames)]
    # print (f'local_list after {local_list}')


def read_one_file_from_logs(fp):
    for line in fp:
        if len(line) < 10:
            continue
        timestamp = None
        json_str = line.replace("'", "\"")
        if json_str[0] == '2':  # time stamp before json
            timestamp = json_str[:14]
            json_str = json_str[15:]
        try:
            line_dict = json.loads(json_str)
            QuoteData = line_dict["QuoteResponse"]["QuoteData"]
            for data in QuoteData:
                symbol = data["Product"]["symbol"]
                # ask = data["Intraday"]["ask"]
                # bid = data["Intraday"]["bid"]
                lastTrade = data["Intraday"]["lastTrade"]
                totalVolume = data["Intraday"]["totalVolume"]
                if timestamp:
                    mytime = timestamp
                else:
                    mytime = datetime.fromtimestamp(data["dateTimeUTC"], pytz.timezone('US/Eastern')).strftime('%Y%m%d%H%M%S')
                if symbol not in QUOTES_LOG_DICT:
                    QUOTES_LOG_DICT[symbol] = dict()
                    QUOTES_LOG_DICT[symbol]["date"] = []
                    QUOTES_LOG_DICT[symbol]["time"] = []
                    QUOTES_LOG_DICT[symbol]["close"] = []
                    QUOTES_LOG_DICT[symbol]["volume"] = []
                    QUOTES_LOG_DICT[symbol]["source"] = []
                QUOTES_LOG_DICT[symbol]["date"].append(int(mytime[:8]))
                QUOTES_LOG_DICT[symbol]["time"].append(int(mytime))
                QUOTES_LOG_DICT[symbol]["close"].append(lastTrade)
                QUOTES_LOG_DICT[symbol]["volume"].append(totalVolume)
                QUOTES_LOG_DICT[symbol]["source"].append("logs")
        except:
            print(f'line not read {json_str}')


def from_logs(filenames='etrade_*.log'):
    synchronize_etrade_numbers_from_server(filenames)
    global QUOTES_LOG_DICT

    if QUOTES_LOG_DICT:
        return QUOTES_LOG_DICT
    filenames = os.path.join(common.get_param('ETRADE_NUMBERS_BASE_DIRECTORY'), filenames)
    logFilenamesList = glob.glob(filenames)
    for filename in logFilenamesList:
        print(f'from_logs {filename}')
        with open(filename) as fp:
            read_one_file_from_logs(fp)

    return QUOTES_LOG_DICT


def from_sftp_logs(filenames='etrade_*.log'):
    global QUOTES_LOG_DICT

    TANA_ETRADE_NUMBERS_BASE_DIRECTORY = common.get_param('TANA_ETRADE_NUMBERS_BASE_DIRECTORY', '/home/val/PycharmProject/Numbers/etrade_logs/')
    c = Connection(host="val@TANA.local", connect_kwargs={"password": "Manon888"})
    sftp = c.sftp()
    listdir = c.sftp().listdir(TANA_ETRADE_NUMBERS_BASE_DIRECTORY)
    logFilenamesList = fnmatch.filter(listdir, f'{filenames}')
    print(logFilenamesList)

    for filename in logFilenamesList:
        with  sftp.open(f'{TANA_ETRADE_NUMBERS_BASE_DIRECTORY}/{filename}') as fp:
            print(f'from_sftp_logs {filename} {fp}')
            read_one_file_from_logs(fp)

    return QUOTES_LOG_DICT


def get_from_vantage(symbol):
    ny_date = datetime.now(pytz.timezone('US/Eastern')).strftime("%Y%m%d")
    with requests.Session():
        symbol_url = f'{common.get_param("VANTAGE_INTRADAY_EXTENDED_URL")}{symbol}'
        filename = os.path.join(common.get_param("VANTAGE_NUMBERS_BASE_DIRECTORY"), f'{symbol.lower()}_{ny_date}.txt')
        my_file = Path(filename)
        if not my_file.is_file():
            detailled_history = pd.read_csv(symbol_url)
            # print (detailled_history["time"])
            # print (type(detailled_history))
            detailled_history["time"] = pd.to_datetime(detailled_history["time"])
            detailled_history["time"] = detailled_history["time"].dt.strftime('%Y%m%d%H%M%S')  # '%Y%m%d%H%M%s'
            detailled_history['date'] = detailled_history['time'].str[:8].astype(np.int64)
            detailled_history["time"] = detailled_history["time"].astype(np.int64)
            detailled_history = detailled_history[::-1]
            detailled_history = detailled_history.drop(['high', 'open', 'low'], axis=1)
            detailled_history["source"] = "vantage"

            detailled_history.to_csv(filename, index_label=False)
        else:
            detailled_history = pd.read_csv(filename)
    detailled_history.reset_index()
    return detailled_history


def get_last_info_from_yahoo(symbol):
    ticker = yfinance.Ticker(symbol)
    # get stock info
    return ticker.info


def get_from_yahoo(symbol, shift=0):
    print("___________________ yahoo ______________________")
    start = (datetime.now(pytz.timezone('US/Eastern')) - timedelta(hours=shift)).strftime("%Y-%m-%d")
    end = (datetime.now(pytz.timezone('US/Eastern')) - timedelta(hours=shift) + timedelta(days=1)).strftime("%Y-%m-%d")

    # print(f'real start {start}')
    # print(f'real end {end}')

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
    detailled_history["source"] = "yahoo"
    detailled_history.reset_index()
    return detailled_history


def get_from_stooq(symbol):
    filename = os.path.join(common.get_param("STOOQ_NUMBERS_BASE_DIRECTORY"), f'{symbol.lower()}.us.txt')
    my_file = Path(filename)
    if not my_file.is_file():
        zipfilename = os.path.join(common.get_param("STOOQ_NUMBERS_BASE_DIRECTORY"), '5_us_txt.zip')

        with ZipFile(zipfilename, 'r') as zipObj:
            listOfFileNames = zipObj.namelist()
            for f in listOfFileNames:
                if f.endswith(f'/{symbol.lower()}.us.txt'):
                    print(f'f {f}')
                    zipInfo = zipObj.getinfo(f)
                    print(f'zipInfo {zipInfo}')
                    zipInfo.filename = os.path.basename(f'{symbol.lower()}.us.txt')
                    zipObj.extract(zipInfo, common.get_param("STOOQ_NUMBERS_BASE_DIRECTORY"))
                    # zipObj.extract(f, os.path.join('c:\\', 'WORK', 'Opy', 'us'))
    detailled_history = pd.read_csv(filename)
    detailled_history.rename(columns={'<CLOSE>': 'close', '<DATE>': 'date', '<TIME>': 'time'}, inplace=True)

    detailled_history["datetime"] = detailled_history["date"].astype(str) + detailled_history["time"].astype(str)
    detailled_history["source"] = "stooq"
    detailled_history.reset_index()
    return detailled_history


def concatenate(a, b):
    first_b_time = int(b.iloc[0]['time'])
    print(f'concatenate, junction on {first_b_time} ')
    first_b_time_index = -1
    first_b_time_index_a = np.where(a['time'] >= first_b_time)
    # print(f'concatenate first_b_time_index_a {first_b_time_index_a}')
    try:
        first_b_time_index = first_b_time_index_a[0][0]
    except:
        first_b_time_index = -1
        print(f'concatenate first index not found')  # not found

    print(f'concatenate first_b_time_index {first_b_time_index}')  # not found

    frames = [a[:first_b_time_index], b]
    c = pd.concat(frames, ignore_index=True)
    c = c.reset_index()
    return c


def get_from_vantage_and_yahoo(symbol):
    vantage_data_frame = get_from_vantage(symbol)
    yahoo_data_frame = get_from_yahoo(symbol)
    c = concatenate(vantage_data_frame, yahoo_data_frame).sort_values('time')
    # print(f'{c}')
    return c


def get_from_vantage_and_logs(symbol, logfilename='etrade_*.log'):
    vantage_data_frame = get_from_vantage(symbol)
    logs_data_frame = get_from_logs(symbol, logfilename)
    if not logs_data_frame.empty:
        vantage_data_frame = concatenate(vantage_data_frame, logs_data_frame).sort_values('time')
    return vantage_data_frame


def get_from_logs(symbol, logfilename='etrade_*.log'):
    data_dict = from_logs(logfilename)
    if symbol not in data_dict.keys():
        column_names = ["time", "datetime", "close", "volume", "source"]
        df = pd.DataFrame(columns=column_names)
    else:
        df = pd.DataFrame(data_dict[symbol]).sort_values('time')
    # print (df)
    return df


# get_from_vantage_and_logs('TSLA', 'etrade_20211112.log')
# c = get_from_vantage('TSLA')
# print (c)

# d = get_from_stooq('TSLA')
# c = get_from_vantage_and_logs('TSLA')
c = get_from_logs('TSLA')
# print (d)
# c = from_sftp_logs ('etrade_*.log')
print(c)
# synchronize_etrade_numbers_from_server ()
