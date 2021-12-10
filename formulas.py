import numpy as np
from scipy import signal

import common

open_bell = common.get_param("open_bell")
close_bell = common.get_param("close_bell")
green_sign_array = np.empty(3000)
green_sign_array[::2] = 1
green_sign_array[1::2] = -1
red_sign_array = np.empty(3000)
red_sign_array[::2] = -1
red_sign_array[1::2] = 1


def beautify_date(date_int):
    d = str(date_int)
    return f'{d[4:6]}.{d[6:8]} {d[8:10]}h{d[10:12]}:{d[12:14]}'


def calculate_buy_sell(full_sig, full_datetime, order, fc, fs, delta, disp=False, start_index=0, end_index=0):
    first_day_colored_index = None
    color_array = np.zeros(len(full_sig))
    buy_sell_array = np.zeros(len(full_sig))

    sig2 = np.array(full_sig)
    sig2[0:start_index] = full_sig[start_index]
    if end_index and end_index > 0:
        sig2[end_index:] = full_sig[end_index]

    if disp:
        print(f'----------- calc order {order} fc {fc} fs {fs} start_index {start_index} {beautify_date(full_datetime[start_index])} start_index {start_index} end {end_index} {beautify_date(full_datetime[end_index])}')
    try:

        sos = signal.butter(order, fc, 'highpass', fs=fs, output='sos')
        filtered = signal.sosfilt(sos, sig2)
        full_hyst = sig2 - filtered
        up_indexes = np.where(np.diff(full_hyst) > delta)[0]
        down_indexes = np.where(np.diff(full_hyst) < -1.0 * delta)[0]
    except Exception as e:
        print(f'order {order}, fc {fc}, fs {fs} {e}')
        return color_array, buy_sell_array, np.zeros(len(full_sig))

    color_array[up_indexes] = 1
    color_array[down_indexes] = -1
    color_array[start_index] = 0
    colored_indexes = np.where(color_array != 0)
    first_day_colored_index_color = []
    try:
        first_day_colored_index = colored_indexes[0][np.where(colored_indexes[0] > start_index)[0][0]]
        first_day_colored_index_color = color_array[first_day_colored_index]
    except:
        if disp:
            print(f'no first action')

    colored_array = color_array[colored_indexes]
    buy_colored_index = np.where(np.diff(colored_array) > 0)[0] + 1
    sell_colored_index = np.where(np.diff(colored_array) < 0)[0] + 1

    buy_index = np.take(colored_indexes, buy_colored_index)
    sell_index = np.take(colored_indexes, sell_colored_index)

    buy_sell_array[buy_index] = 1
    buy_sell_array[sell_index] = -1

    buy_sell_array[start_index] = 0
    buy_sell_array[start_index] = 0
    if first_day_colored_index:
        buy_sell_array[first_day_colored_index] = first_day_colored_index_color

    if disp:
        print(f'calc color_array       {color_array[start_index:end_index]}')
        print(f'calc buy_sell_array    {buy_sell_array[start_index:end_index]}')
        print(f'calc full_datetime     {full_datetime[start_index:end_index]}')

        print(f' calc  len buy_sell_array {len(buy_sell_array)} len not null {len(buy_sell_array[np.where(buy_sell_array != 0)])}')
    return color_array, buy_sell_array, full_hyst


def itterative_calculate_gain(full_sig, full_buy_sell_array, start_index, end_index, max_gain=100000, disp=False):
    if disp:
        print(f'----------- itterative gain index: {start_index}, {end_index}')

    account = 0
    first_trade = True
    nb_order = 0
    last_action = 0
    virtual_account = 0
    first_value = full_sig[start_index]
    value = 0
    for index in range(start_index, end_index + 1):
        action = full_buy_sell_array[index - 1]
        value = full_sig[index]
        if action == 1:
            nb_order = nb_order + 1
            if disp:
                print(f'{nb_order} buy {value}')
            if not first_trade:
                account = account - value  # BUY TO COVER
            account = account - value  # BUY
            first_trade = False
            last_action = 1

        if action == -1:
            nb_order = nb_order + 1
            if disp:
                print(f'{nb_order} sell {value}')
            if not first_trade:
                account = account + value  # SELL
            account = account + value  # SELL SHORT
            first_trade = False
            last_action = -1
        if action == 0:
            if last_action == -1:
                virtual_account = account - value
            if last_action == 1:
                virtual_account = account + value
            if virtual_account > max_gain:
                nb_order = nb_order + 1
                if disp:
                    print(f'{nb_order} sell/buy {value}')
                    print(f'Max gain exit {virtual_account} {100.0 * virtual_account / first_value:.2f}%')
                return virtual_account, virtual_account / first_value, 0, nb_order  # EXIT NOW

    nb_order = nb_order + 1
    if last_action == -1:
        account = account - value
        if disp:
            print(f'{nb_order} buy {value}')
    if last_action == 1:
        account = account + value
        if disp:
            print(f'{nb_order} sell {value}')
    if disp:
        print(f'itterative gain {account} {100.0 * account / first_value:.2f}%')

    return account, account / first_value, 0, nb_order


def calculate_gain(full_sig, full_buy_sell_array, start_index, end_index, disp=False):
    if disp:
        print(f'----------- gain index: {start_index}, {end_index}')

    buy_sell_array = full_buy_sell_array[start_index:end_index]

    buy_sell_array = np.insert(buy_sell_array, 0, 0)
    non_zero_index = np.where(buy_sell_array != 0)
    non_zero_bsa = buy_sell_array[non_zero_index]

    if not np.any(buy_sell_array):
        return 0, 0, 0, 0
    sig = full_sig[start_index:end_index + 2]
    non_zero_sig = sig[non_zero_index]
    action_sig = np.append(non_zero_sig, full_sig[end_index])
    if disp:
        print(f'non_zero_bsa {non_zero_bsa} {len(non_zero_bsa)}')
        print(f'action_sig {action_sig} {len(action_sig)}')
        print(f'non_zero_index {non_zero_index} {len(non_zero_bsa)}')

    diff_array = np.diff(action_sig)

    if non_zero_bsa[0] == 1:
        sum_array = diff_array * green_sign_array[:len(diff_array)]
    else:
        sum_array = diff_array * red_sign_array[:len(diff_array)]

    account = np.sum(sum_array)
    pc = account / sig[0]
    nb_orders = len(non_zero_bsa) + 1
    if disp:
        print(f'gain {account} {100.0 * pc:.2f}%')

    return account, pc, 0, nb_orders


def datetime_to_index(full_datetime, datestart, dateend=None):
    if dateend is None:
        datestart_int = int(f'{datestart}{open_bell}')
        dateend_int = int(f'{datestart}{close_bell}')
    else:
        datestart_int = datestart
        dateend_int = dateend

    # print(f'datetime_to_index  {datestart_int} {dateend_int}')

    if datestart_int > full_datetime[-1]:
        return None, None

    start_index = np.where(full_datetime >= datestart_int)[0][0]
    end_index = np.where(full_datetime <= dateend_int)[0][-1]
    # print (f'start_index {start_index}  end_index {end_index}')
    return start_index, end_index
