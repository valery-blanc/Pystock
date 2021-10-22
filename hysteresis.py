import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.widgets import Slider, Button, RadioButtons
from scipy import signal

import stockapi

symbol = 'ABG'
DELTA = 0.001
order = 3
nbjours = 10
max_nb_order_per_day = 40
critical_freq = 15
sampling_freq = 1750
axcolor = 'lightgoldenrodyellow'
intraday_index = 50

open_bell = "093000"
close_bell = "160000"
green_sign_array = np.empty(3000)
green_sign_array[::2] = 1
green_sign_array[1::2] = -1
red_sign_array = np.empty(3000)
red_sign_array[::2] = -1
red_sign_array[1::2] = 1


def calc(full_sig, intraday_index, order, fc, fs, disp=False, start_index=0):
    first_day_colored_index = None
    color_array = np.zeros(len(full_sig))
    buy_sell_array = np.zeros(len(full_sig))

    sig2 = np.array(full_sig)
    sig2[0:start_index] = full_sig[start_index]
    if intraday_index:
        sig2 [start_index+intraday_index:] = full_sig[start_index+intraday_index]

    if disp:
        print(f'----------- calc order {order} fc {fc} fs {fs} start_index {start_index} intraday_index {intraday_index} end {start_index+intraday_index}')
    try:

        sos = signal.butter(order, fc, 'highpass', fs=fs, output='sos')
        filtered = signal.sosfilt(sos, sig2)
        full_hyst = sig2 - filtered
        up_indexes = np.where(np.diff(full_hyst) > DELTA)[0]
        down_indexes = np.where(np.diff(full_hyst) < -1.0 * DELTA)[0]




    except:
        print(f'order {order}, fc {fc}, fs {fs}')
        return (color_array, buy_sell_array, np.zeros(len(full_sig)))

    color_array[up_indexes] = 1
    color_array[down_indexes] = -1
    color_array[start_index] = 0
    colored_indexes = np.where(color_array != 0)

    try:

        first_day_colored_index = colored_indexes[0][np.where(colored_indexes[0] > start_index)[0][0]]
        first_day_colored_index_color = color_array[first_day_colored_index]
        if disp:
            print(f'calc first_day_colored_index {first_day_colored_index} first_day_colored_index_color {first_day_colored_index_color} colored_indexes {colored_indexes}')
    except:
        if disp:
            print(f'no first action')

    colored_array = color_array[colored_indexes]
    if disp:
        print (f'calc colored_array {colored_array}')
    buy_colored_index = np.where(np.diff(colored_array) > 0)[0] + 1
    sell_colored_index = np.where(np.diff(colored_array) < 0)[0] + 1

    if disp:
        print (f'calc buy_colored_index {buy_colored_index}')
        print (f'calc sell_colored_index {sell_colored_index}')

    buy_index = np.take(colored_indexes, buy_colored_index)
    sell_index = np.take(colored_indexes, sell_colored_index)


    buy_sell_array[buy_index] = 1
    buy_sell_array[sell_index] = -1

    buy_sell_array[start_index] = 0
    buy_sell_array[start_index] = 0
    if first_day_colored_index:
        buy_sell_array[first_day_colored_index] = first_day_colored_index_color


    if disp:
        # print (f' gain buy_index {buy_index} len {len(buy_index)}')
        # print (f' gain sell_index {sell_index} len {len(sell_index)}')
        print(f'calc color_array       {color_array[start_index:start_index + intraday_index]}')
        print(f'calc buy_sell_array    {buy_sell_array[start_index:start_index + intraday_index]}')
        print(f'calc full_datetime     {full_datetime[start_index:start_index + intraday_index]}')

        print(f' calc  len buy_sell_array {len(buy_sell_array)} len not null {len(buy_sell_array[np.where(buy_sell_array != 0)])}')
    return (color_array, buy_sell_array, full_hyst)


def gain(full_sig, full_color_array, full_buy_sell_array, start_index, end_index, disp=False):
    if disp:
        print(f'----------- gain index: {start_index}, {end_index}')

    buy_sell_array = full_buy_sell_array[start_index:end_index + 1]
    color_array = full_color_array[start_index:end_index + 1]
    non_zero_color_index = np.where(color_array != 0)
    #if len(non_zero_color_index[0]) > 0:
    #    first_non_zero_color_index = non_zero_color_index[0][0]
    #    first_color = color_array[first_non_zero_color_index]
    #    if disp:
    #        print(f'gain first_non_zero_color_index {first_non_zero_color_index} first_color {first_color}')
#
    #    buy_sell_array[first_non_zero_color_index] = first_color
    non_zero_index = np.where(buy_sell_array != 0)

    non_zero_bsa = buy_sell_array[non_zero_index]

    if (not np.any(buy_sell_array)):
        return (-1000, -100, 0, 0)
    sig = full_sig[start_index:end_index + 1]
    action_sig = np.append(sig[non_zero_index], sig[-1])
    if disp:
        # print (f'color_array {color_array}')
        print(f'gain buy_sell_array {buy_sell_array}')
        print(f'gain action_sig {action_sig}')
    diff_array = np.diff(action_sig)

    if non_zero_bsa[0] == 1:
        sum_array = diff_array * green_sign_array[:len(diff_array)]
    else:
        sum_array = diff_array * red_sign_array[:len(diff_array)]

    account = np.sum(sum_array)
    pc = account / sig[0]
    nb_orders = len(non_zero_bsa) + 1

    return (account, pc, 0, nb_orders)


def datetime_to_index(full_datetime, datestart, dateend=None):
    if dateend is None:
        datestart_int = int(f'{datestart}{open_bell}')
        dateend_int = int(f'{datestart}{close_bell}')
    else:
        datestart_int = datestart
        dateend_int = dateend
    start_index = np.where(full_datetime >= datestart_int)[0][0]
    end_index = np.where(full_datetime <= dateend_int)[0][-1]

    return (start_index, end_index)


def get_best_parameters(full_sig, full_datetime, days_list):
    print(f'_____________________ get_best_parameters {days_list}  ')
    best_order = 0
    best_nb_orders = 0
    best_account = -100000.0
    best_fc = 0
    best_fs = 0
    best_pc = -100
    max_nb_order = max_nb_order_per_day * len(days_list)

    days_list_indexes = [datetime_to_index(full_datetime, d) for d in days_list]
    (min_start_index, min_end_index) = days_list_indexes[0]

    print(f' min indexes {min_start_index}  {min_end_index}   {full_datetime[min_start_index]}  {full_datetime[min_end_index]} ')
    for order in [3.0, 4.0, 5.0, 6.0]:
        print(order)
        for fc in range(8, 25, 1):
            for fs in range(800, 2000, 5):  # np.logspace(1.8,3.7,400, True, 8): #range(2 * fc + 1, 400, 1): #
                sum_account = 0
                sum_pc = 0
                sum_nb_orders = 0
                (full_color_array, full_buy_sell_array, full_hyst) = calc(full_sig, None, order, fc, fs, False, min_start_index)
                for day_indexes in days_list_indexes:
                    (start_index, end_index) = day_indexes
                    (account, pc, papers, nb_orders) = gain(full_sig, full_color_array, full_buy_sell_array, start_index, end_index, disp=False)
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
                    print(f'{best_account:.2f}, {100 * best_pc:.2f}%, {best_nb_orders} orders, {best_order} {best_fc} {best_fs}   start_index {start_index} end_index {end_index}')

    return (best_account, best_pc, best_nb_orders, best_order, best_fc, best_fs)


def replot(ax, full_sig, full_datetime, datestart, dateend, order, fc, fs, intraday_index):
    print(f'_____________________ replot {datestart}  {dateend}, {order} {fc} {fs} {intraday_index}')

    ax.clear()
    (start_index, end_index) = datetime_to_index(full_datetime, datestart, dateend)

    end_index = start_index + intraday_index

    (full_color_array, full_buy_sell_array, full_hyst) = calc(full_sig, intraday_index, order, fc, fs, True, start_index)

    (account, pc, papers, nb_orders) = gain(full_sig, full_color_array, full_buy_sell_array, start_index, end_index, disp=True)
    # print (f'after gain full_buy_sell_array {full_buy_sell_array[start_index:end_index]}')
    print(f'len(full_sig) {len(full_sig)}')

    hystcolor = pd.DataFrame({'full_sig': full_sig[:start_index+intraday_index], 'full_color_array': full_color_array[:start_index+intraday_index]})
    buy_sell_color = pd.DataFrame({'full_sig': full_sig[:start_index+intraday_index], 'full_buy_sell_array': full_buy_sell_array[:start_index+intraday_index]})

    color_groups = hystcolor.groupby('full_color_array')
    buy_sell_groups = buy_sell_color.groupby('full_buy_sell_array')

    text = f'{datestart} account {account:.2f} {100 * pc:.2f}% nb_orders {nb_orders} papers {papers} ({order}/{fc}/{fs})'
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


    sig = full_sig[start_index:end_index]
    hyst = full_hyst[start_index:end_index]

    xmin = start_index - 10
    ymin = min(np.min(sig), np.min(hyst))
    xmax = start_index + 400  # end_index +10
    ymax = max(np.max(sig), np.max(hyst))

    ax.axvline(x=start_index, color='#1f77b4')
    ax.axvline(x=end_index, color='#1f77b4')


    ax.plot(full_sig[:start_index+intraday_index])  # ax.plot(time, sig)
    ax.plot(full_hyst)
    ax.set_title(f'{symbol} {text}')

    for i in range(start_index, start_index+intraday_index + 1):
        if full_buy_sell_array[i] == -1.0 or full_buy_sell_array[i] == 1.0 or i == end_index:
            ax.text(i, full_sig[i], f'{str(full_sig[i])} {str(full_datetime[i])[4:8]} {str(full_datetime[i])[8:12]}')

    ax.set_xlabel('Time')

    print(f'start_index {start_index}  end_index {end_index} {end_index - start_index}')
    ax.set_xticks(range(len(full_datetime))[::10])
    ax.set_xticklabels(full_datetime[::10], rotation=45, ha="right")

    # for label in ax.get_xticklabels():
    #    label.set_ha("right")
    #    label.set_rotation(45)

    # ax.axis([np.min(time), np.max(time), np.min(sig), np.max(sig)])
    ax.set(xlim=(xmin, xmax), ylim=(ymin, ymax))
    plt.draw()
    print(f'--------------------------------- end replot ----------------------------')


def update_date(val):
    calc_date = int(check.value_selected)
    print(f'___________ update_date {calc_date}____________________')
    update(0)


def update_best_today(val):
    calc_date = check.value_selected
    print(f'___________ update_best_today {calc_date}____________________')
    day_list = [calc_date]
    print(f'day_list {day_list}')
    update_best(day_list)


def update_last_days(val):
    calc_date = np.int64(check.value_selected)
    print(f'___________ update_last_days {calc_date}____________________')
    print(f'{unique_dates} {type(unique_dates)} {type(unique_dates[0])}')

    print (f'calc_date {calc_date} {type(calc_date)} ')
    print (f'np where {np.where(unique_dates == calc_date)}')
    dateend_index = np.where(unique_dates == calc_date)[0][0]
    print(f'{unique_dates}')
    datestart_index = dateend_index - nbjours
    if datestart_index < 0:
        datestart_index = 0
    day_list = unique_dates[datestart_index:dateend_index]
    print(f'day_list {day_list}')

    update_best(day_list)


def update_best(day_list):
    print(f'---------update_best  {day_list}  ')
    (best_account, best_pc, best_nb_orders, best_order, best_fc, best_fs) = get_best_parameters(full_sig, full_datetime, day_list)
    print(f'BEST {best_account} {best_order} {best_fc} {best_fs} ')
    order_slider.set_val(best_order)
    critical_slider.set_val(best_fc)
    sampling_slider.set_val(best_fs)
    update(0)


def update(val):
    # datestart = int(f'{check.value_selected}150000')
    # dateend = int(f'{check.value_selected}220000')

    print(f'============================== update {check.value_selected} ')

    intraday_index = intraday_index_slider.val
    replot(ax, full_sig, full_datetime, check.value_selected, None, order_slider.val, critical_slider.val, sampling_slider.val, intraday_index)


detailled_history = stockapi.get_from_vantage(symbol)
full_datetime = np.array(detailled_history["datetime"]).astype(np.longlong)
print(full_datetime)
dates = np.array(detailled_history["date"])
full_sig = np.array(detailled_history["close"])

datestart = 20210915
dateend = 20210917

mindate = int(min(dates))
calc_date = int(max(dates))
unique_dates = np.unique(dates)
visible_dates = np.ones(len(unique_dates))
fig, ax = plt.subplots()
plt.subplots_adjust(left=0.12, bottom=0.25, right=0.9)

check_ax = plt.axes([0.0, 0.2, 0.1, 0.7])
check = RadioButtons(check_ax, np.flip(unique_dates))
for c in check.circles:  # adjust radius here. The default is 0.05
    c.set_radius(0.01)

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
critical_axe = plt.axes([0.94, 0.1, 0.015, 0.8], facecolor=axcolor)
critical_slider = Slider(
    ax=critical_axe,
    label="fc",
    valmin=0,
    valmax=30,
    valstep=1,
    valinit=critical_freq,

    orientation="vertical"
)
sampling_axe = plt.axes([0.97, 0.1, 0.015, 0.8], facecolor=axcolor)
sampling_slider = Slider(
    ax=sampling_axe,
    label="fs",
    valmin=0,
    valmax=5000,
    valstep=50,
    valinit=sampling_freq,
    orientation="vertical"
)

intraday_index_axe = plt.axes([0.14, 0.07, 0.74, 0.03], facecolor=axcolor)
intraday_index_slider = Slider(
    ax=intraday_index_axe,
    label="minutes",
    valmin=0,
    valmax=390,
    valstep=1,
    valinit=intraday_index
)

best_axe = plt.axes([0.01, 0.02, 0.05, 0.05], facecolor=axcolor)
best_last_day = Button(best_axe, f'Best {nbjours} d')
best_axe = plt.axes([0.01, 0.08, 0.05, 0.05], facecolor=axcolor)
best_today = Button(best_axe, 'Best today')

update_axe = plt.axes([0.01, 0.14, 0.05, 0.05], facecolor=axcolor)
update_now = Button(update_axe, 'update')

intraday_index_slider.on_changed(update)
check.on_clicked(update)
best_last_day.on_clicked(update_last_days)
best_today.on_clicked(update_best_today)
update_now.on_clicked(update)
update(0)

plt.show()
