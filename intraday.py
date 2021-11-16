import datetime
import time
import numpy as np
import etrade
import formulas
import stockapi


def init_full_sig(close, interval=30):
    f = lambda x: x.strftime("%Y%m%d%H%M%S")  # your elementwise fn
    fv = np.vectorize(f)

    nb_points = int(2 * 24 * 3600 / interval)  # 2 days before
    print(nb_points)

    full_sig = np.full(nb_points, close, dtype=float)
    now = datetime.datetime.now()
    begin = now - datetime.timedelta(seconds=interval * nb_points)
    t = np.arange(begin, now, datetime.timedelta(seconds=interval)).astype(datetime.datetime)
    full_datetime = fv(t)

    return nb_points, full_sig, full_datetime


def get_price(symbol, market=None, simu=True, close_history=None, shift=0):
    if simu:

        # now = datetime.datetime.now(pytz.timezone('US/Eastern'))
        now = datetime.datetime.now()
        mydatetime = now.strftime("%Y%m%d%H%M%S")
        mytime = int(mydatetime)
        mydate = int(mydatetime[:8])
        myvolume = 1000
        myclose = close_history[shift - 1000]

        return {'time': mytime, 'date': mydate, 'close': myclose, 'volume': myvolume}

    else:
        return etrade.get_last_price(market, symbol)


symbol = 'TSLA'
order = 3
fc = 8
fs = 1500
delta = 0.005
simu = False
etrade_token = etrade.token
etrade_market = None
etrade_order = None

detailled_history = stockapi.get_from_vantage(symbol)
close_history = np.array(detailled_history["close"])

if simu:
    close = close_history[-1000]
else:
    etrade_token = etrade.get_token()
    etrade_market = etrade.get_market(etrade_token)
    etrade_order = etrade.get_order(etrade_token)
    close = etrade.get_last_price(etrade_market, symbol)['close']
print(close)

first_trade = True
start_index, full_sig, full_datetime = init_full_sig(close)
for shift_index in range(0, 1500):

    line = get_price(symbol, market=etrade_market, simu=simu, close_history=close_history, shift=shift_index)

    end_index = start_index + shift_index
    full_sig = np.append(full_sig, line['close'])
    full_datetime = np.append(full_datetime, line['time'])
    color_array, buy_sell_array, full_hyst = formulas.calculate_buy_sell(full_sig, full_datetime, order, fc, fs, delta, disp=False, start_index=start_index, end_index=end_index)

    color = color_array[-2]
    buy_sell = buy_sell_array[-2]

    myline = f'\nsimu {simu} {full_datetime[-1]} full_sig {full_sig[-1]} color {color} buy_sell {buy_sell}'
    print(myline)
    with open("TSLA_20211111.txt", "a+") as file_object:
        file_object.write(myline)

    preview1 = None
    preview2 = None

    if buy_sell > 0:  # BUY
        if not first_trade:  # BUY TO COVER
            preview1 = etrade.preview(symbol, 'BUY_TO_COVER', etrade_order)
        preview2 = etrade.preview(symbol, 'BUY', etrade_order)
        first_trade = False

    if buy_sell < 0:  # SELL
        if not first_trade:  # BUY TO COVER
            preview1 = etrade.preview(symbol, 'SELL', etrade_order)
        preview2 = etrade.preview(symbol, 'SELL_SHORT', etrade_order)
        first_trade = False

    time.sleep(30)

file_object.close()
