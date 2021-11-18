import etrade
import time
import os
from datetime import datetime
import pytz
import formulas
import common



symbol_list = common.get_param("symbol_list")
now = datetime.now(pytz.timezone('US/Eastern'))
today = now.strftime("%Y%m%d")
today_file_directory = common.get_param("ETRADE_NUMBERS_BASE_URL")
today_file_name = os.path.join(today_file_directory, f'etrade_{today}.log')
print(today_file_name)
open_time = int(f'{today}{common.get_param("open_bell")}')
close_time = int(f'{today}{common.get_param("close_bell")}')
finish_time = int(f'{today}{common.get_param("finish_time")}')
print(symbol_list)
mytime = int(now.strftime("%Y%m%d%H%M%S"))

market = etrade.get_market()

print(f'now {formulas.beautify_date(mytime)} finish at {formulas.beautify_date(finish_time)}')

while mytime < finish_time:
    mytime = int(datetime.now(pytz.timezone('US/Eastern')).strftime("%Y%m%d%H%M%S"))
    if mytime >= open_time and mytime <= close_time:
        period = common.get_param("period_day")
    else:
        period = common.get_param("period_night")

    print(f'{formulas.beautify_date(mytime)} {period}')

    with open(today_file_name, "a+") as file_object:
        try:
            last = etrade.get_quote(symbol_list, market)
            file_object.write(f'\n{mytime} {last}')
        except Exception as e:
            print(f'{mytime} unable to get {symbol_list} {e}')
    # print (f'{last}')
    time.sleep(period)
