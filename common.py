import json
import platform

global PARAM_LIST
global REFRESH

PARAM_LIST = {}
REFRESH = True

def read_from_file():
    global PARAM_LIST
    param_list_filename = f'param_list_{platform.node()}.json'
    print(param_list_filename)
    f = open(param_list_filename, "r")
    s = f.read()
    PARAM_LIST = json.loads(s)
    print(PARAM_LIST)
    f.close()

def get_param(param_name):
    global PARAM_LIST
    global REFRESH
    if not PARAM_LIST or REFRESH:
        read_from_file()
        REFRESH = False
    return PARAM_LIST[param_name]

