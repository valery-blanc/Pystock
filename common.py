import json
import os
import platform
from pathlib import Path
from fabric.connection import Connection
from fabric.transfer import Transfer


global PARAM_LIST
global REFRESH
param_file = os.path.join(os.getcwd(), '..', 'param_list.json')
param_file_localhost = os.path.join(os.getcwd(), '..', f'param_list_{platform.node()}.json')


PARAM_LIST = dict()
REFRESH = True


def read_from_file(filename):
    param_list = {}
    if Path(filename).is_file():
        f = open(filename, "r")
        s = f.read()
        param_list = json.loads(s)
        f.close()
    else:
        print(f'read_from_file {filename} not found')
    return param_list


def write_to_file(param_list, filename):
    global REFRESH
    a_file = open(filename, "w+")
    json.dump(param_list, a_file, indent=2, sort_keys=True)
    a_file.close()


def synchronize_TANA():
    TANA_PARAM_FILE = get_param('TANA_PARAM_FILE', '/home/val/PycharmProject/Pystock/param_list.json')
    sftp_tana_host = get_param("sftp_tana_host")
    sftp_tana_passwd= get_param("sftp_tana_passwd")

    if TANA_PARAM_FILE == param_file:
        return ()
    print('synchronize_TANA transfer')
    c = Connection(host=sftp_tana_host, connect_kwargs={"password": sftp_tana_passwd})
    Transfer(c).put(param_file, TANA_PARAM_FILE)


def update_params(update_dict, global_file=True):
    PARAM_LIST.update(update_dict)

    if global_file:
        filename = param_file
    else:
        filename = param_file_localhost
    param_list = read_from_file(filename)

    for key in update_dict.keys():
        if update_dict[key] is None:
            param_list.pop(key, None)
        else:
            param_list[key] = update_dict[key]

    write_to_file(param_list, filename)
    synchronize_TANA()


def get_param(key, default_value=None, create_in_global_file=True):
    global PARAM_LIST
    global REFRESH
    if not PARAM_LIST or REFRESH:
        PARAM_LIST.update(read_from_file(param_file))
        PARAM_LIST.update(read_from_file(param_file_localhost))
        REFRESH = False
    if key in PARAM_LIST.keys():
        return PARAM_LIST[key]
    else:  # create the parameter with default value
        update_params({key: default_value}, create_in_global_file)
    return default_value


