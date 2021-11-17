import sys
import time

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytz
from matplotlib.widgets import Slider, RangeSlider, Button, RadioButtons

import stockapi
from formulas import datetime_to_index, calculate_buy_sell, calculate_gain, itterative_calculate_gain
import common

newyork_tz = pytz.timezone('America/New_York')


# symbol_list = ['AAPL', 'NTES', 'STX', 'TX', 'WDC', 'LYFT', 'FNF', 'DAL', 'TPR']
# symbol_list = ['TSLA', 'APP', 'AMD','ASAN','BILI','BKI','CAN','DQ','DIDI','DOCN','DASH','FTCH','FCX','YMM','JD','BEKE'	]
# symbol_list = ['TLS','CREX','CSPR','PNBK','EYPT','OTLY','KERN','SSNT','BFLY','BTB','BTAI','MJXL','RANI','VRCA','BGRY']

detailled_history_dict = dict()

symbol_list                       = common.get_param("symbol_list")
SIMU_DEFAULT_DELTA                = common.get_param("SIMU_DEFAULT_DELTA")
SIMU_DEFAULT_FILTER_ORDER         = common.get_param("SIMU_DEFAULT_FILTER_ORDER")
SIMU_DEFAULT_MAX_ACTION_PER_DAY   = common.get_param("SIMU_DEFAULT_MAX_ACTION_PER_DAY")
SIMU_DEFAULT_FILTER_CRITICAL_FREQ = common.get_param("SIMU_DEFAULT_FILTER_CRITICAL_FREQ")
SIMU_DEFAULT_FILTER_SAMPLING_FREQ = common.get_param("SIMU_DEFAULT_FILTER_SAMPLING_FREQ")
SIMU_AXCOLOR                      = common.get_param("SIMU_AXCOLOR")
SIMU_DEFAULT_INTRADAY_INDEX       = common.get_param("SIMU_DEFAULT_INTRADAY_INDEX")
SIMU_DEFAULT_ITERATIVE_MAX_GAIN   = common.get_param("SIMU_DEFAULT_ITERATIVE_MAX_GAIN")
SIMU_DEFAULT_NB_DAYS_FOR_BEST_ALL = common.get_param("SIMU_DEFAULT_NB_DAYS_FOR_BEST_ALL")
SIMU_BEST_X_BUTTON_LIST           = common.get_param("SIMU_BEST_X_BUTTON_LIST")




def get_detailled_history(symbol):
    if not symbol in detailled_history_dict.keys():
        detailled_history_dict[symbol] = dict()
        detailled_history = stockapi.get_from_vantage(symbol)#get_from_vantage_and_logs(symbol)
        detailled_history_dict[symbol]['full_datetime'] = np.array(detailled_history["time"]).astype(np.longlong)
        detailled_history_dict[symbol]['dates'] = np.array(detailled_history["date"])
        detailled_history_dict[symbol]['full_sig'] = np.array(detailled_history["close"])
    return detailled_history_dict[symbol]


def get_best_pc_average(full_sig, full_datetime, days_list):
    start = time.time()
    best_order = 3
    best_moy = -100000.0
    best_fc = 8
    best_fs = 0
    best_delta = SIMU_DEFAULT_DELTA
    max_nb_orders = SIMU_DEFAULT_MAX_ACTION_PER_DAY * len(days_list)
    for delta_i in range(10, 200, 10):  # [0.04,0.05, 0.06, 0.07,]:
        delta = float(delta_i) / 1000.0
        # print (".", end = '')
        for fs in range(50, 4000, 100):  # (1480, 1520, 1):
            moy, pc_array, sum_nb_orders = simu_all_dates(full_sig, full_datetime, days_list, best_order, best_fc, fs, delta)
            if moy > best_moy and sum_nb_orders < max_nb_orders:
                best_moy = moy
                best_fs = fs
                best_delta = delta
    end = time.time()
    # print(f'=========== time {end - start}')
    return (best_moy, best_order, best_fc, best_fs, best_delta)


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
    max_nb_order = SIMU_DEFAULT_MAX_ACTION_PER_DAY * len(days_list)

    days_list_indexes = [datetime_to_index(full_datetime, d) for d in days_list]
    (min_start_index, min_end_index) = days_list_indexes[0]

    print(f' min indexes {min_start_index}  {min_end_index}   {full_datetime[min_start_index]}  {full_datetime[min_end_index]} ')
    for order in range(2, 7):
        print(order)
        for fc in range(8, 25, 1):  # [8]:  # range(8, 25, 1):
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


# def plot_last(ax, full_sig, full_datetime, full_color_array, full_buy_sell_array, full_hyst):
#    color_dict = {-1: 'r', 0: 'w', 1: 'g'}
#    color = full_color_array[-1]
#    buysell = full_buy_sell_array[-1]
#    hyst = full_hyst[-2:]
#    sig = full_sig[-2:]
#    x = [len(full_datetime) - 1, len(full_datetime)]
#    lastx = len(full_datetime)
#
#    ax.plot(x, sig)
#    ax.plot(x, hyst)
#    ax.plot(lastx, color, color=color_dict[color], marker='o', linestyle='', markersize=5)
#    ax.plot(lastx, buysell, color=color_dict[color], marker='|', linestyle='', markersize=5)

def simu_all_dates(full_sig, full_datetime, day_list, order, fc, fs, delta):
    # print (f'simu_all_dates {unique_dates}')
    pc_array = []
    sum_nb_orders = 0
    for mydate in day_list:
        # print (f' mydate {mydate}')
        (start_index, end_index) = datetime_to_index(full_datetime, mydate, None)
        (full_color_array, full_buy_sell_array, full_hyst) = calculate_buy_sell(full_sig, full_datetime, order, fc, fs, delta, False, start_index, end_index)
        (account, pc, papers, nb_orders) = calculate_gain(full_sig, full_buy_sell_array, start_index, end_index, disp=False)
        # (i_account, i_pc, i_papers, i_nb_orders) = itterative_calculate_gain(full_sig, full_buy_sell_array, start_index, end_index, MAX_GAIN, disp=False)
        sum_nb_orders = sum_nb_orders + nb_orders
        pc_array.append(pc)
        # i_pc_array.append(i_pc)

        # print (f'{mydate} {account:.2f} {100 * pc:.2f} ')

    moy = sum(pc_array) / len(pc_array)
    # i_moy = sum(i_pc_array)/len(i_pc_array)
    # print (f'std pc {100 * moy:.2f}')
    # print (f'max pc {100 * i_moy:.2f}')
    return moy, pc_array, sum_nb_orders  # , i_moy


def replot(ax, symbol, full_sig, full_datetime, datestart, dateend, order, fc, fs, delta, intraday_index_min, intraday_index_max):
    print(f'_____________________ replot {symbol} {datestart}  {dateend}, {order} {fc} {fs} {delta} ')

    ax.clear()
    (day_start_index, day_end_index) = datetime_to_index(full_datetime, datestart, dateend)
    if not day_end_index:
        return
    end_index = min(day_start_index + intraday_index_max, day_end_index)
    start_index = day_start_index + intraday_index_min
    print(f'replot len full_datetime {len(full_datetime)}')
    print(f'replot start_index {start_index} end_index {end_index} day_start_index {day_start_index} day_end_index {day_end_index}')
    print(f'replot start_index {full_datetime[start_index]} end_index {full_datetime[end_index]} day_start_index {full_datetime[day_start_index]} day_end_index {full_datetime[day_end_index]}')

    (full_color_array, full_buy_sell_array, full_hyst) = calculate_buy_sell(full_sig, full_datetime, order, fc, fs, delta, False, start_index, end_index)
    (account, pc, papers, nb_orders) = calculate_gain(full_sig, full_buy_sell_array, start_index, end_index, disp=True)
    (i_account, i_pc, i_papers, i_nb_orders) = itterative_calculate_gain(full_sig, full_buy_sell_array, start_index, end_index, SIMU_DEFAULT_ITERATIVE_MAX_GAIN, disp=True)
    print(f'i_account {i_account} i_pc {i_pc}')
    full_buy_sell_array = np.insert(full_buy_sell_array, 0, 0)

    hystcolor = pd.DataFrame({'full_sig': full_sig[:end_index], 'full_color_array': full_color_array[:end_index]})
    buy_sell_color = pd.DataFrame({'full_sig': full_sig[:end_index], 'full_buy_sell_array': full_buy_sell_array[:end_index]})

    color_groups = hystcolor.groupby('full_color_array')
    buy_sell_groups = buy_sell_color.groupby('full_buy_sell_array')
    print(f'full_buy_sell_array {full_buy_sell_array}')

    moy, pc_array, sum_nb_orders = simu_all_dates(full_sig, full_datetime, unique_dates, order, fc, fs, delta)
    print(f'pc_array {pc_array}')
    text = f'{datestart} account:{account:.2f} {100.0 * pc:.2f}% {nb_orders} orders action:{full_buy_sell_array[-2]} | CAP${SIMU_DEFAULT_ITERATIVE_MAX_GAIN} {i_account:.2f} {(100.0 * i_pc):.2f}% {i_nb_orders} orders | {order}/{fc}/{fs} | moy {100 * moy:.2f} '
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

    nb_x = xmax - xmin
    delta_label = int(nb_x / 60)
    print(f' nb_x {nb_x} {int(nb_x / 60)}')
    ax.axvline(x=start_index, color='#1f77b4')
    ax.text(start_index, ymin, f'{str(full_datetime[start_index])[8:12]}')
    ax.axvline(x=end_index, color='#1f77b4')
    ax.text(end_index, ymin, f'{str(full_datetime[end_index])[8:12]}')

    ax.plot(full_sig[:end_index + 1])  # ax.plot(time, sig)
    ax.plot(full_hyst)
    ax.set_title(f'{symbol} {text}')

    for i in range(start_index, end_index + 1):
        if full_buy_sell_array[i] == -1.0 or full_buy_sell_array[i] == 1.0 or i == end_index:
            ax.text(i, full_sig[i], f'{full_sig[i]:.2f} {str(full_datetime[i])[4:8]} {str(full_datetime[i])[8:14]}')

    ax.set_xlabel('Time')

    # print(f'start_index {start_index}  end_index {end_index} {end_index - start_index}')
    ax.set_xticks(range(len(full_datetime))[::delta_label])
    ax.set_xticklabels(full_datetime[::delta_label], rotation=45, ha="right")

    # for label in ax.get_xticklabels():
    #    label.set_ha("right")
    #    label.set_rotation(45)

    # ax.axis([np.min(time), np.max(time), np.min(sig), np.max(sig)])
    ax.set(xlim=(xmin, xmax), ylim=(ymin, ymax))
    plt.draw()
    print(f' {full_sig[-5:]}')
    print(f'--------------------------------- end replot {symbol} ----------------------------')


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


def update_best_20_days(val):
    update_best_x_days(val, 20)


def update_best_10_days(val):
    update_best_x_days(val, 10)


def update_best_5_days(val):
    update_best_x_days(val, 5)


def update_best_3_days(val):
    update_best_x_days(val, 3)


def update_best_1_days(val):
    update_best_x_days(val, 1)


def update_best_x_days(val, nb_days):
    print(f' nb_days {nb_days} ')
    calc_date = int(date_radio.value_selected)
    print(f'calc_date {calc_date}  ')

    dateend_index = list(unique_dates).index(calc_date)

    datestart_index = dateend_index - nb_days
    if datestart_index < 0:
        datestart_index = 0
    day_list = unique_dates[datestart_index:dateend_index]
    print(f'day_list {day_list}')

    update_best(day_list)


def best_all(val):
    nb_days = SIMU_DEFAULT_NB_DAYS_FOR_BEST_ALL
    calc_date = int(date_radio.value_selected)
    # print(f'calc_date {calc_date}  ')

    dateend_index = list(unique_dates).index(calc_date)

    datestart_index = dateend_index - nb_days
    if datestart_index < 0:
        datestart_index = 0
    day_list = unique_dates[datestart_index:dateend_index]
    # print(f'day_list {day_list}')

    for symbol in symbol_list:

        # print(f'---------update_best  {symbol} {day_list}  ')
        # (best_account, best_pc, best_nb_orders, best_order, best_fc, best_fs, best_delta) = get_best_parameters(full_sig, full_datetime, day_list)
        try:
            full_datetime = get_detailled_history(symbol)['full_datetime']
            full_sig = get_detailled_history(symbol)['full_sig']
            (best_moy, best_order, best_fc, best_fs, best_delta) = get_best_pc_average(full_sig, full_datetime, day_list)
            print(f'BEST {symbol} {nb_days} {100 * best_moy:.2f} {best_order} {best_fc} {best_fs} {best_delta}')
        except:
            print(f'BEST {symbol} {nb_days} not found')


def update_best(day_list):
    symbol = symbol_radio.value_selected
    print(f'---------update_best  {symbol} {day_list}  ')
    full_datetime = get_detailled_history(symbol)['full_datetime']
    full_sig = get_detailled_history(symbol)['full_sig']
    # (best_account, best_pc, best_nb_orders, best_order, best_fc, best_fs, best_delta) = get_best_parameters(full_sig, full_datetime, day_list)

    (best_moy, best_order, best_fc, best_fs, best_delta) = get_best_pc_average(full_sig, full_datetime, day_list)
    print(f'BEST {best_moy} {best_order} {best_fc} {best_fs} {best_delta}')
    order_slider.set_val(best_order)
    critical_slider.set_val(best_fc)
    sampling_slider.set_val(best_fs)
    delta_slider.set_val(best_delta)
    change_date(0)


def change_date(val):
    symbol = symbol_radio.value_selected
    full_datetime = get_detailled_history(symbol)['full_datetime']

    datestart_index, end_index = datetime_to_index(full_datetime, date_radio.value_selected)
    intraday_index_slider.ax.set_xlim(0, end_index - datestart_index + 5)
    intraday_index_slider.set_val([0, end_index - datestart_index])
    update(None)


def update(val):
    print(f'============================== update {symbol_radio.value_selected} {date_radio.value_selected} ')
    symbol = symbol_radio.value_selected

    full_datetime = get_detailled_history(symbol)['full_datetime']
    full_sig = get_detailled_history(symbol)['full_sig']
    dates = get_detailled_history(symbol)['dates']

    unique_dates = np.unique(dates)
    print(f' unique_dates {unique_dates} ')

    intraday_index_min, intraday_index_max = intraday_index_slider.val
    replot(ax, symbol, full_sig, full_datetime, date_radio.value_selected, None, order_slider.val, critical_slider.val, sampling_slider.val, delta_slider.val, intraday_index_min, intraday_index_max)


def calc_all(val):
    symbol = symbol_radio.value_selected
    full_datetime = get_detailled_history(symbol)['full_datetime']
    full_sig = get_detailled_history(symbol)['full_sig']

    simu_all_dates(full_sig, full_datetime, unique_dates, order_slider.val, critical_slider.val, sampling_slider.val, delta_slider.val)


fig, ax = plt.subplots(figsize=(25, 12), dpi=80)
plt.subplots_adjust(left=0.12, bottom=0.25, right=0.9)

first_symbol = symbol_list[0]
first_dates = get_detailled_history(first_symbol)["dates"]

calc_date = int(max(first_dates))
unique_dates = np.unique(first_dates)
print(f' unique_dates {unique_dates} ')

date_radio_ax = plt.axes([0.0, 0.2, 0.07, 0.4])
date_radio = RadioButtons(date_radio_ax, np.flip(unique_dates))
for c in date_radio.circles:  # adjust radius here. The default is 0.05
    c.set_radius(0.02)

symbol_radio_ax = plt.axes([0.0, 0.62, 0.07, 0.3])
symbol_radio = RadioButtons(symbol_radio_ax, symbol_list)
for c in symbol_radio.circles:  # adjust radius here. The default is 0.05
    c.set_radius(0.02)

order_axe = plt.axes([0.91, 0.1, 0.015, 0.8], facecolor=SIMU_AXCOLOR)
order_slider = Slider(
    ax=order_axe,
    label="order",
    valmin=1,
    valmax=10,
    valinit=SIMU_DEFAULT_FILTER_ORDER,
    valstep=1,
    orientation="vertical"
)
critical_axe = plt.axes([0.93, 0.1, 0.015, 0.8], facecolor=SIMU_AXCOLOR)
critical_slider = Slider(
    ax=critical_axe,
    label="fc",
    valmin=0,
    valmax=30,
    valstep=1,
    valinit=SIMU_DEFAULT_FILTER_CRITICAL_FREQ,

    orientation="vertical"
)
sampling_axe = plt.axes([0.95, 0.1, 0.015, 0.8], facecolor=SIMU_AXCOLOR)
sampling_slider = Slider(
    ax=sampling_axe,
    label="fs",
    valmin=0,
    valmax=5000,
    valstep=1,
    valinit=SIMU_DEFAULT_FILTER_SAMPLING_FREQ,
    orientation="vertical"
)

delta_axe = plt.axes([0.97, 0.1, 0.015, 0.8], facecolor=SIMU_AXCOLOR)
delta_slider = Slider(
    ax=delta_axe,
    label="delta",
    valmin=0,
    valmax=1,
    valstep=0.001,
    valinit=SIMU_DEFAULT_DELTA,
    orientation="vertical"
)

intraday_index_axe = plt.axes([0.14, 0.07, 0.74, 0.03], facecolor=SIMU_AXCOLOR)
intraday_index_slider = RangeSlider(
    ax=intraday_index_axe,
    label="minutes",
    valmin=0,
    valmax=1570,
    valstep=1,
    valinit=(0, SIMU_DEFAULT_INTRADAY_INDEX)
)

update_axe = plt.axes([0.01, 0.14, 0.04, 0.05], facecolor=SIMU_AXCOLOR)
update_now = Button(update_axe, 'update')

best_axe = plt.axes([0.01, 0.08, 0.04, 0.05], facecolor=SIMU_AXCOLOR)
best_today = Button(best_axe, 'Best today')

xx = 0.01
i = 0
best_x_buttons = []
for nb_days in SIMU_BEST_X_BUTTON_LIST:

    exec(f"def update_best_{nb_days}_days(val): update_best_x_days(val, {nb_days})")
    best_axe = plt.axes([xx, 0.02, 0.03, 0.05], facecolor=SIMU_AXCOLOR)
    best_x_button = Button(best_axe, f'Best {nb_days} d')
    function_name = f'update_best_{nb_days}_days'
    funct = getattr(sys.modules[__name__], function_name)
    best_x_button.on_clicked(funct)
    best_x_buttons.append(best_x_button)
    xx = xx + .03

# up_axe = plt.axes([0.05, 0.14, 0.04, 0.05], facecolor=axcolor)
# action_up = Button(up_axe, '+')
#
down_axe = plt.axes([0.05, 0.08, 0.04, 0.05], facecolor=SIMU_AXCOLOR)
action_down = Button(down_axe, 'Best ALL')

# intraday_index_slider.on_changed(update)
date_radio.on_clicked(change_date)
symbol_radio.on_clicked(update)
best_today.on_clicked(update_best_today)
update_now.on_clicked(update)
action_down.on_clicked(best_all)
change_date(0)
plt.show()
