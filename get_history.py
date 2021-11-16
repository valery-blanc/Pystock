import etrade
import time
import json
import os
from datetime import datetime, timedelta
import pytz




param_list_filename = os.path.join('c:\\', 'WORK', 'Numbers', 'param_list.json')
print (param_list_filename)
f = open (param_list_filename, "r")
s = f.read()
param_list = json.loads(s)
print (param_list)
f.close()
symbol_list = param_list["symbol_list"]
now = datetime.now(pytz.timezone('US/Eastern'))
today = now.strftime("%Y%m%d")
today_file_name = os.path.join('c:\\', 'WORK', 'Numbers','etrade_logs', f'etrade_{today}.log')

open_time = int(f'{today}{param_list["open_bell"]}')
close_time = int(f'{today}{param_list["close_bell"]}')
finish_time = int(f'{today}{param_list["finish_time"]}')
print (symbol_list)
mytime = int(now.strftime("%Y%m%d%H%M%S"))

market = etrade.get_market()

print (f'now {mytime} finish at {finish_time}')


while mytime < finish_time:
    mytime = int(datetime.now(pytz.timezone('US/Eastern')).strftime("%Y%m%d%H%M%S"))
    if mytime >= open_time and mytime <= close_time:
        period = param_list["period_day"]
    else:
        period = param_list["period_night"]

    #print (f'{mytime} {period}')

    with open(today_file_name, "a+") as file_object:
        last = etrade.get_quote(symbol_list, market)
        file_object.write(f'\n{last}')
    #print (f'{last}')
    time.sleep(period)
