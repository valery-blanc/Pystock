import requests
import pandas as pd
import os
from pathlib import Path

# replace the "demo" apikey below with your own key from https://www.alphavantage.co/support/#api-key
CSV_URL = 'https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY_EXTENDED&interval=1min&slice=year1month1&apikey=D6T5YBJID9YYNA1D&symbol='

with requests.Session() as s:
    symbol = 'IBM'
    symbol_url = f'{CSV_URL}{symbol}'
    filename = os.path.join('c:\\', 'WORK', 'Opy', 'us', f'{symbol.lower()}.txt')
    my_file = Path(filename)
    if not my_file.is_file():
        detailled_history = pd.read_csv(symbol_url)
        detailled_history["datetime"] = pd.to_datetime(detailled_history["time"])
        detailled_history["datetime"] = detailled_history["datetime"].dt.strftime('%Y%m%d%H%M%S')  # '%Y%m%d%H%M%s'
        detailled_history['date'] = detailled_history['datetime'].str[:8]
        detailled_history[::-1].to_csv(filename, index_label=False )
    else:
        detailled_history = pd.read_csv(filename)

    print (f'{detailled_history}')



    #for row in my_list:
    #    print(row)

