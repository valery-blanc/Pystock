import requests
import pandas as pd
import os
from pathlib import Path
from datetime import datetime
import pytz
from zipfile import ZipFile
CSV_URL = 'https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY_EXTENDED&interval=1min&slice=year1month1&apikey=D6T5YBJID9YYNA1D&symbol='


def get_from_vantage(symbol):
    ny_date = datetime.now(pytz.timezone('US/Eastern')).strftime("%Y%m%d")
    with requests.Session() as s:
        symbol_url = f'{CSV_URL}{symbol}'
        filename = os.path.join('c:\\', 'WORK', 'Pystock', 'us', f'{symbol.lower()}_{ny_date}.txt')
        my_file = Path(filename)
        if not my_file.is_file():
            detailled_history = pd.read_csv(symbol_url)
            detailled_history["datetime"] = pd.to_datetime(detailled_history["time"])
            detailled_history["datetime"] = detailled_history["datetime"].dt.strftime('%Y%m%d%H%M%S')  # '%Y%m%d%H%M%s'
            detailled_history['date'] = detailled_history['datetime'].str[:8]
            detailled_history = detailled_history[::-1]
            detailled_history.to_csv(filename, index_label=False )
        else:
            detailled_history = pd.read_csv(filename)
    return (detailled_history)




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

