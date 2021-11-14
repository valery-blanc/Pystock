import time
from datetime import timedelta, datetime

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytz
from matplotlib.widgets import Slider, RangeSlider, Button, RadioButtons

import etrade
import formulas
import stockapi
from formulas import datetime_to_index, calculate_buy_sell, calculate_gain, itterative_calculate_gain

global full_datetime
global full_sig
global dates

newyork_tz = pytz.timezone('America/New_York')
symbol = 'AAPL'
DELTA = 0.029
order = 3
nbjours = 20
max_nb_order_per_day = 50
critical_freq = 8
sampling_freq = 1506
axcolor = 'lightgoldenrodyellow'
intraday_index = 50
MAX_GAIN = 50.0


def get_best_pc_average (full_sig, full_datetime, days_list):
    start = time.time()
    best_order = 3
    best_moy = -100000.0
    best_fc = 8
    best_fs = 0
    best_delta = DELTA
    max_nb_orders = max_nb_order_per_day * len(days_list)
    for delta_i in range(150, 200, 1) : #[0.04,0.05, 0.06, 0.07,]:
        delta = float(delta_i) / 1000.0
        print (".", end = '')
        for fs in range (1800, 1900, 1): #(1480, 1520, 1):
                moy, pc_array, sum_nb_orders = simu_all_dates(full_sig, full_datetime, days_list, best_order, best_fc, fs, delta)
                if moy > best_moy and sum_nb_orders < max_nb_orders:
                    best_moy = moy
                    best_fs = fs
                    best_delta = delta
    end = time.time()
    print(f'=========== time {end - start}')
    return (best_moy,  best_order, best_fc, best_fs, best_delta)


def get_best_parameters(full_sig, full_datetime, days_list):
    print(f'_____________________ get_best_parameters {days_list}  ')
    start = time.time()
    best_order = 0
    best_nb_orders = 0
    best_account = -100000.0
    best_fc = 0
    best_fs = 0
    best_delta = 0
    best_pc = -100
    max_nb_order = max_nb_order_per_day * len(days_list)

    days_list_indexes = [datetime_to_index(full_datetime, d) for d in days_list]
    (min_start_index, min_end_index) = days_list_indexes[0]

    print(f' min indexes {min_start_index}  {min_end_index}   {full_datetime[min_start_index]}  {full_datetime[min_end_index]} ')
    for order in range (2,7):
        print(order)
        for fc in range(8, 25, 1): #[8]:  # range(8, 25, 1):
            for delta in [0.005, 0.01, 0.05]:
                for fs in range(100, 3000, 50):  # np.logspace(1.8,3.7,400, True, 8): #range(2 * fc + 1, 400, 1): #
                    sum_account = 0
                    sum_pc = 0
                    sum_nb_orders = 0
                    (full_color_array, full_buy_sell_array, full_hyst) = calculate_buy_sell(full_sig, full_datetime, order, fc, fs, delta, False, min_start_index, 0)
                    for day_indexes in days_list_indexes:
                        (start_index, end_index) = day_indexes
                        (account, pc, papers, nb_orders) = calculate_gain(full_sig, full_buy_sell_array, start_index, end_index, disp=False)
                        sum_account = sum_account + account
                        sum_pc = sum_pc + pc
                        sum_nb_orders = sum_nb_orders + nb_orders
                    if sum_pc > best_pc and sum_nb_orders < max_nb_order:
                        best_pc = sum_pc
                        best_account = sum_account
                        best_nb_orders = sum_nb_orders
                        best_order = order
                        best_fc = fc
                        best_fs = fs
                        best_delta = delta
                        print(f'{best_account:.2f}, {100 * best_pc:.2f}%, {best_nb_orders} orders, {best_order} {best_fc} {best_fs}   start_index {start_index} end_index {end_index}')
    end = time.time()
    print(f'=========== time {end - start}')

    return (best_account, best_pc, best_nb_orders, best_order, best_fc, best_fs, best_delta)


def plot_last(ax, full_sig, full_datetime, full_color_array, full_buy_sell_array, full_hyst):
    color_dict = {-1: 'r', 0: 'w', 1: 'g'}
    color = full_color_array[-1]
    buysell = full_buy_sell_array[-1]
    hyst = full_hyst[-2:]
    sig = full_sig[-2:]
    x = [len(full_datetime) - 1, len(full_datetime)]
    lastx = len(full_datetime)

    ax.plot(x, sig)
    ax.plot(x, hyst)
    ax.plot(lastx, color, color=color_dict[color], marker='o', linestyle='', markersize=5)
    ax.plot(lastx, buysell, color=color_dict[color], marker='|', linestyle='', markersize=5)

def simu_all_dates (full_sig, full_datetime, day_list,  order, fc, fs, delta ):
    #print (f'simu_all_dates {unique_dates}')
    pc_array = []
    sum_nb_orders = 0
    for mydate in day_list:
        #print (f' mydate {mydate}')
        (start_index, end_index) = datetime_to_index(full_datetime, mydate, None)
        (full_color_array, full_buy_sell_array, full_hyst) = calculate_buy_sell(full_sig, full_datetime, order, fc, fs, delta, False, start_index, end_index)
        (account, pc, papers, nb_orders) = calculate_gain(full_sig, full_buy_sell_array, start_index, end_index, disp=False)
        #(i_account, i_pc, i_papers, i_nb_orders) = itterative_calculate_gain(full_sig, full_buy_sell_array, start_index, end_index, MAX_GAIN, disp=False)
        sum_nb_orders = sum_nb_orders + nb_orders
        pc_array.append(pc)
        #i_pc_array.append(i_pc)

        #print (f'{mydate} {account:.2f} {100 * pc:.2f} ')

    moy = sum(pc_array)/len(pc_array)
    #i_moy = sum(i_pc_array)/len(i_pc_array)
    #print (f'std pc {100 * moy:.2f}')
    #print (f'max pc {100 * i_moy:.2f}')
    return moy, pc_array, sum_nb_orders #, i_moy


def replot(ax, full_sig, full_datetime, datestart, dateend, order, fc, fs, delta, intraday_index_min, intraday_index_max):
    print(f'_____________________ replot {datestart}  {dateend}, {order} {fc} {fs} {delta} {intraday_index}')

    ax.clear()
    (day_start_index, day_end_index) = datetime_to_index(full_datetime, datestart, dateend)
    if not day_end_index:
        return
    end_index = day_start_index + intraday_index_max
    start_index = day_start_index + intraday_index_min

    print (f'replot start_index {start_index} end_index {end_index} day_start_index {day_start_index} day_end_index {day_end_index}')
    print (f'replot start_index {full_datetime[start_index]} end_index {full_datetime[end_index]} day_start_index {full_datetime[day_start_index]} day_end_index {full_datetime[day_end_index]}')

    (full_color_array, full_buy_sell_array, full_hyst) = calculate_buy_sell(full_sig, full_datetime, order, fc, fs, delta, False, start_index, end_index)
    (account, pc, papers, nb_orders) = calculate_gain(full_sig, full_buy_sell_array, start_index, end_index, disp=True)
    (i_account, i_pc, i_papers, i_nb_orders) = itterative_calculate_gain(full_sig, full_buy_sell_array, start_index, end_index, MAX_GAIN,  disp=True)
    print(f'i_account {i_account} i_pc {i_pc}')
    full_buy_sell_array = np.insert(full_buy_sell_array, 0, 0)

    hystcolor = pd.DataFrame({'full_sig': full_sig[:end_index], 'full_color_array': full_color_array[:end_index]})
    buy_sell_color = pd.DataFrame({'full_sig': full_sig[:end_index], 'full_buy_sell_array': full_buy_sell_array[:end_index]})

    color_groups = hystcolor.groupby('full_color_array')
    buy_sell_groups = buy_sell_color.groupby('full_buy_sell_array')
    print(f'full_buy_sell_array {full_buy_sell_array}')

    moy, pc_array, sum_nb_orders = simu_all_dates(full_sig, full_datetime, unique_dates, order, fc, fs, delta)
    print (f'pc_array {pc_array}')
    text = f'{datestart} account:{account:.2f} {100.0 * pc:.2f}% {nb_orders} orders action:{full_buy_sell_array[-2]} | CAP${MAX_GAIN} {i_account:.2f} {(100.0 * i_pc):.2f}% {i_nb_orders} orders | {order}/{fc}/{fs} | moy {100*moy:.2f} '
    for name, group in buy_sell_groups:
        # print (name)
        if name == 1:
            color = 'g'
        if name == 0:
            color = 'w'
        if name == -1:
            color = 'r'
        ax.plot(group.full_sig, color=color, marker='|', linestyle='', markersize=40, label=name)

    for name, group in color_groups:
        # print (name)
        if name == 1:
            color = 'g'
        if name == 0:
            color = 'b'
        if name == -1:
            color = 'r'
        ax.plot(group.full_sig, color=color, marker='o', linestyle='', markersize=5, label=name)

    if full_buy_sell_array[-2] < 0:
        ax.plot(end_index, full_sig[end_index], color='r', marker='o', linestyle='', markersize=10, label=name)

    if full_buy_sell_array[-2] > 0:
        ax.plot(end_index, full_sig[end_index], color='g', marker='o', linestyle='', markersize=10, label=name)

    sig = full_sig[start_index:end_index]
    hyst = full_hyst[start_index:end_index]

    xmin = day_start_index - 30
    ymin = min(np.min(sig), np.min(hyst))
    xmax = day_end_index + 30
    ymax = max(np.max(sig), np.max(hyst))

    ax.axvline(x=start_index, color='#1f77b4')
    ax.text(start_index, ymin, f'{str(full_datetime[start_index])[8:12]}' )
    ax.axvline(x=end_index, color='#1f77b4')
    ax.text(end_index, ymin, f'{str(full_datetime[end_index])[8:12]}' )

    ax.plot(full_sig[:end_index + 1])  # ax.plot(time, sig)
    ax.plot(full_hyst)
    ax.set_title(f'{symbol} {text}')

    for i in range(start_index, end_index + 1):
        if full_buy_sell_array[i] == -1.0 or full_buy_sell_array[i] == 1.0 or i == end_index:
            ax.text(i, full_sig[i], f'{full_sig[i]:.2f} {str(full_datetime[i])[4:8]} {str(full_datetime[i])[8:14]}')

    ax.set_xlabel('Time')

    # print(f'start_index {start_index}  end_index {end_index} {end_index - start_index}')
    ax.set_xticks(range(len(full_datetime))[::10])
    ax.set_xticklabels(full_datetime[::10], rotation=45, ha="right")

    # for label in ax.get_xticklabels():
    #    label.set_ha("right")
    #    label.set_rotation(45)

    # ax.axis([np.min(time), np.max(time), np.min(sig), np.max(sig)])
    ax.set(xlim=(xmin, xmax), ylim=(ymin, ymax))
    plt.draw()
    print(f' {full_sig[-5:]}')
    print(f'--------------------------------- end replot ----------------------------')


def update_date(val):
    calc_date = int(date_radio.value_selected)
    print(f'___________ update_date {calc_date}____________________')
    update(0)


def update_best_today(val):
    calc_date = date_radio.value_selected
    print(f'___________ update_best_today {calc_date}____________________')
    day_list = [calc_date]
    print(f'day_list {day_list}')
    update_best(day_list)


def update_best_x_days(val):
    calc_date = int(date_radio.value_selected)
    print(f'calc_date {calc_date}  ')

    dateend_index = list(unique_dates).index(calc_date)

    datestart_index = dateend_index - nbjours
    if datestart_index < 0:
        datestart_index = 0
    day_list = unique_dates[datestart_index:dateend_index]
    print(f'day_list {day_list}')

    update_best(day_list)


def update_best(day_list):
    print(f'---------update_best  {day_list}  ')
    #(best_account, best_pc, best_nb_orders, best_order, best_fc, best_fs, best_delta) = get_best_parameters(full_sig, full_datetime, day_list)

    (best_moy,  best_order, best_fc, best_fs, best_delta) = get_best_pc_average(full_sig, full_datetime, day_list)
    print(f'BEST {best_moy} {best_order} {best_fc} {best_fs} {best_delta}')
    order_slider.set_val(best_order)
    critical_slider.set_val(best_fc)
    sampling_slider.set_val(best_fs)
    delta_slider.set_val(best_delta)
    change_date(0)


def change_date(val):
    datestart_index, end_index = datetime_to_index(full_datetime, date_radio.value_selected)
    intraday_index_slider.ax.set_xlim(0, end_index - datestart_index + 5)
    intraday_index_slider.set_val([0, end_index - datestart_index])
    update(None)


def update(val):
    # datestart = int(f'{date_radio.value_selected}150000')
    # dateend = int(f'{date_radio.value_selected}220000')

    print(f'============================== update {date_radio.value_selected} ')

    intraday_index_min, intraday_index_max = intraday_index_slider.val
    replot(ax, full_sig, full_datetime, date_radio.value_selected, None, order_slider.val, critical_slider.val, sampling_slider.val, delta_slider.val, intraday_index_min,intraday_index_max)

def calc_all(val):
    simu_all_dates(full_sig, full_datetime, unique_dates, order_slider.val, critical_slider.val, sampling_slider.val, delta_slider.val)


def stock_up(val):
    print(f'====================================== ++++++')
    market = etrade.get_market(etrade.token)
    for i in range(0, 30):
        last = etrade.get_last_price(market, symbol)
        print(f'{last}')
        add_value(last)
        time.sleep(10)


def stock_down(val):
    print(f'====================================== -------')
    add_value(-0.3)


def add_value(myvalue):
    print(f'add_value {myvalue}')
    global full_datetime
    global full_sig
    global dates

    full_datetime = np.append(full_datetime, myvalue['date'])
    full_sig = np.append(full_sig, myvalue['close'])
    dates = np.append(dates, myvalue['date'])
    change_date(0)


fig, ax = plt.subplots(figsize=(25, 12), dpi=80)
detailled_history = stockapi.get_from_vantage_and_logs(symbol, 'etrade_20211112.log')
full_datetime = np.array(detailled_history["time"]).astype(np.longlong)
dates = np.array(detailled_history["date"])
full_sig = np.array(detailled_history["close"])

mindate = int(min(dates))
calc_date = int(max(dates))
unique_dates = np.unique(dates)



unique_dates = np.unique(dates)

print(f' unique_dates {unique_dates} ')

visible_dates = np.ones(len(unique_dates))
plt.subplots_adjust(left=0.12, bottom=0.25, right=0.9)

date_radio_ax = plt.axes([0.0, 0.2, 0.1, 0.7])
date_radio = RadioButtons(date_radio_ax, np.flip(unique_dates))
for c in date_radio.circles:  # adjust radius here. The default is 0.05
    c.set_radius(0.02)

order_axe = plt.axes([0.91, 0.1, 0.015, 0.8], facecolor=axcolor)
order_slider = Slider(
    ax=order_axe,
    label="order",
    valmin=1,
    valmax=10,
    valinit=order,
    valstep=1,
    orientation="vertical"
)
critical_axe = plt.axes([0.93, 0.1, 0.015, 0.8], facecolor=axcolor)
critical_slider = Slider(
    ax=critical_axe,
    label="fc",
    valmin=0,
    valmax=30,
    valstep=1,
    valinit=critical_freq,

    orientation="vertical"
)
sampling_axe = plt.axes([0.95, 0.1, 0.015, 0.8], facecolor=axcolor)
sampling_slider = Slider(
    ax=sampling_axe,
    label="fs",
    valmin=0,
    valmax=5000,
    valstep=1,
    valinit=sampling_freq,
    orientation="vertical"
)

delta_axe = plt.axes([0.97, 0.1, 0.015, 0.8], facecolor=axcolor)
delta_slider = Slider(
    ax=delta_axe,
    label="delta",
    valmin=0,
    valmax=1,
    valstep=0.001,
    valinit=DELTA,
    orientation="vertical"
)

intraday_index_axe = plt.axes([0.14, 0.07, 0.74, 0.03], facecolor=axcolor)
intraday_index_slider = RangeSlider(
    ax=intraday_index_axe,
    label="minutes",
    valmin=0,
    valmax=1570,
    valstep=1,
    valinit=(0,intraday_index)
)

update_axe = plt.axes([0.01, 0.14, 0.04, 0.05], facecolor=axcolor)
update_now = Button(update_axe, 'update')

best_axe = plt.axes([0.01, 0.08, 0.04, 0.05], facecolor=axcolor)
best_today = Button(best_axe, 'Best today')

best_axe = plt.axes([0.01, 0.02, 0.04, 0.05], facecolor=axcolor)
best_x_days = Button(best_axe, f'Best {nbjours} d')

up_axe = plt.axes([0.05, 0.14, 0.04, 0.05], facecolor=axcolor)
action_up = Button(up_axe, '+')

down_axe = plt.axes([0.05, 0.08, 0.04, 0.05], facecolor=axcolor)
action_down = Button(down_axe, '-')

# intraday_index_slider.on_changed(update)
date_radio.on_clicked(change_date)
best_x_days.on_clicked(update_best_x_days)
best_today.on_clicked(update_best_today)
update_now.on_clicked(update)
action_up.on_clicked(stock_up)
action_down.on_clicked(calc_all)
change_date(0)
# update_best_x_days(0)
plt.show()
