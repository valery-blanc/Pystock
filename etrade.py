import datetime
import json
import os
import pytz
import time
import logging
import pyetrade

consumer_key = "7054284dfb42fd505030408d4ec0d4d3"
consumer_secret = "1e9dee8bc1bd2b62a3a555560f635bbf4689512f03441e1bdea0a0487f79a108"
token = {'oauth_token': 'TjBpug93PD1z+MQEgSK7rrc4U/HqVLNyOZ7d27jNx/8=', 'oauth_token_secret': 'mPSdXOS6bs0qQ2zobM9OEtbOornAeoO3lutjdkriI4U='}
symbol = 'TSLA'
account_id_key = 'lZoUChkHRHCYTtouLpG4WQ'
date_now = datetime.datetime.now(pytz.timezone('US/Eastern')).strftime("%Y%m%d")
logging.basicConfig(format='%(message)s', filename=f'etrade_{date_now}.log',  level=logging.INFO)

def format_preview_response (preview):
    nyc_datetime = datetime.datetime.now(pytz.timezone('US/Eastern')).strftime("%Y-%m-%d %H:%M:%S")

    r_action = preview['PreviewOrderResponse']['Order']['Instrument']['orderAction']
    r_quantity = preview['PreviewOrderResponse']['Order']['Instrument']['quantity']
    r_symbol = preview['PreviewOrderResponse']['Order']['Instrument']['Product']['symbol']
    r_price = preview['PreviewOrderResponse']['Order']['estimatedTotalAmount']
    r_s = f'{nyc_datetime} {r_action} {r_quantity} {r_symbol} {r_price}'
    return r_s


def creation_date(path_to_file):
    fileStatsObj = os.stat(path_to_file)
    mydate = datetime.datetime.fromtimestamp(fileStatsObj.st_mtime, pytz.timezone('US/Eastern'))
    print(mydate)
    return mydate.strftime("%Y%m%d")


def get_token():
    token = None

    try:
        token_date = creation_date("token.txt")
        if token_date == datetime.datetime.now(pytz.timezone('US/Eastern')).strftime("%Y%m%d"):
            with open('token.txt', 'r') as file:
                token = json.load(file)
                print('token form file')
    except:
        print('token not read')

    if not token:
        oauth = pyetrade.ETradeOAuth(consumer_key, consumer_secret)
        print(oauth.get_request_token())  # Use the printed URL

        verifier_code = input("Enter verification code: ")
        token = oauth.get_access_token(verifier_code)

        with open('token.txt', 'w') as file:
            file.write(json.dumps(token))  # use `json.loads` to do the reverse

    print(f'token = {token}')
    return token


def list_accounts(token):
    accounts = pyetrade.ETradeAccounts(consumer_key, consumer_secret, token['oauth_token'], token['oauth_token_secret'], dev=False)
    return accounts.list_accounts()


def get_quote(symbols, market):
    quote = market.get_quote(symbols, detail_flag='intraday', skip_mini_options_check=True, resp_format='json')
    #logging.info(f'{quote}')

    return quote
    # for q in quote['QuoteResponse']['QuoteData']:
    #    print(q['All'])


def get_last_price(market, symbol):
    now = datetime.datetime.now(pytz.timezone('US/Eastern'))
    mydatetime = now.strftime("%Y%m%d%H%M%S")
    mytime = int(mydatetime)
    mydate = int(mydatetime[:8])
    quote = market.get_quote([symbol], detail_flag='intraday', skip_mini_options_check=True, resp_format='json')
    line = quote['QuoteResponse']['QuoteData'][0]['Intraday']
    myvolume = line['totalVolume']
    myclose = line['lastTrade']
    return {'time': mytime, 'date': mydate, 'close': myclose, 'volume': myvolume}


def get_market():
    token = get_token()
    market = pyetrade.ETradeMarket(consumer_key, consumer_secret, token['oauth_token'], token['oauth_token_secret'], dev=False)
    print(f'get_market ')
    return market

def get_order():
    token = get_token()
    order = pyetrade.ETradeOrder(consumer_key, consumer_secret, token['oauth_token'], token['oauth_token_secret'], dev=False)
    print(f'get_order ')
    return order


def stream_quote(symbol, token):
    start = time.time()
    for i in range(0, 10):
        quote = get_quote([symbol], token)
        q = quote['QuoteResponse']['QuoteData'][0]['Intraday']
        nyc_datetime = datetime.datetime.now(pytz.timezone('US/Eastern')).strftime("%Y-%m-%d %H:%M:%S.%f")
        print(f" {nyc_datetime} {q['lastTrade']}")
        time.sleep(10)
    end = time.time()
    print(end - start)

def preview (symbol,orderAction, order):
    client_order_id = str(time.time())
    print(f'{orderAction} {symbol} client_order_id {client_order_id} account_id_key {account_id_key}')
    try:
        my_preview = order.preview_equity_order(  # resp_format='json', #bug in pyetrade
            accountId=account_id_key,
            symbol=symbol,
            allOrNone=False,
            orderAction=orderAction,
            clientOrderId=client_order_id,
            priceType='MARKET',
            quantity=1,
            marketSession='REGULAR',
            orderTerm='GOOD_FOR_DAY')
        r_s = format_preview_response (my_preview)
        print (f'preview {r_s}')
        logging.info(f'{r_s}')
        return my_preview
    except:
        logging.info(f'exeption {orderAction} ')
    return {}


def preview_and_place(symbol, token, account_id_key):
    order = pyetrade.ETradeOrder(consumer_key, consumer_secret, token['oauth_token'], token['oauth_token_secret'], dev=False)
    client_order_id = str(time.time())
    print(f'client_order_id {client_order_id}')
    nyc_datetime = datetime.datetime.now(pytz.timezone('US/Eastern')).strftime("%Y-%m-%d %H:%M:%S.%f")

    my_preview = order.preview_equity_order(  # resp_format='json', #bug in pyetrade
        accountId=account_id_key,
        symbol=symbol,
        allOrNone=False,
        orderAction='BUY',
        clientOrderId=client_order_id,
        priceType='MARKET',
        quantity=1,
        marketSession='REGULAR',
        orderTerm='GOOD_FOR_DAY')

    preview_id = my_preview['PreviewOrderResponse']['PreviewIds']['previewId']
    print(f"{nyc_datetime}  preview_id : {preview_id}")

    myorder = order.place_equity_order(
        orderId=preview_id,
        accountId=account_id_key,
        symbol=symbol,
        orderAction='BUY',
        clientOrderId=client_order_id,
        priceType='MARKET',
        quantity=1,
        orderTerm='GOOD_FOR_DAY',
        marketSession='REGULAR'
    )
    return myorder


def list_order(token, account_id_key):
    orders = pyetrade.ETradeOrder(consumer_key, consumer_secret, token['oauth_token'], token['oauth_token_secret'], dev=False)

    print(f"list : {orders.list_orders(account_id_key, resp_format='json')}")





token = get_token()
###quit()
##

#
#
#accounts = list_accounts(token)
#print (f'accounts:{accounts}')
#account_id_key = accounts['AccountListResponse']['Accounts']['Account']['accountIdKey']
#print (f'account_id_key:{account_id_key}')
#
##list_order(token, account_id_key)
# nyc_datetime = datetime.datetime.now(pytz.timezone('US/Eastern')).strftime("%Y-%m-%d %H:%M:%S.%f")
# quote = get_quote([symbol], token)
# q = quote['QuoteResponse']['QuoteData'][0]['Intraday']
# print(f" {nyc_datetime} lastTrade : {q['lastTrade']}")
##myorder = preview_and_place (symbol, token, account_id_key)
##nyc_datetime = datetime.datetime.now(pytz.timezone('US/Eastern')).strftime("%Y-%m-%d %H:%M:%S.%f")
##print(f"{nyc_datetime}  myorder : {myorder}")
# list_order (token, account_id_key)
