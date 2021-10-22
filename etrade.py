import pyetrade
import time
import datetime, pytz
import json
import os
import platform

consumer_key = "7054284dfb42fd505030408d4ec0d4d3"
consumer_secret = "1e9dee8bc1bd2b62a3a555560f635bbf4689512f03441e1bdea0a0487f79a108"
token = {'oauth_token': 'n1ToLbNbZD3noo9NYSvDbzDdNZzzzHwGrfGEOECf2SM=', 'oauth_token_secret': 'JiU+Pk9PtJ58Cg1/DWVxN+9m8Q+OCY+/obVm/4+Y/q8='}
symbol = 'TSLA'


def creation_date(path_to_file):
    fileStatsObj = os.stat ( path_to_file )
    mydate = datetime.datetime.fromtimestamp(fileStatsObj.st_mtime, pytz.timezone('US/Eastern'))
    print (mydate)
    return mydate.strftime("%Y%m%d")

def get_token():
    token_date = creation_date("token.txt")
    token = None

    if token_date == datetime.datetime.now(pytz.timezone('US/Eastern')).strftime("%Y%m%d"):
        try:
            with open('token.txt', 'r') as file:
                token = json.load(file)
        except:
            print ('token not read')

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
    accounts = pyetrade.ETradeAccounts(consumer_key,consumer_secret,token['oauth_token'],token['oauth_token_secret'],dev=False)
    return accounts.list_accounts()

def get_quote(symbols, token):
    market = pyetrade.ETradeMarket(consumer_key,consumer_secret,token['oauth_token'],token['oauth_token_secret'],dev=False)
    quote = market.get_quote(symbols, detail_flag='intraday', skip_mini_options_check=True, resp_format='json')
    #print (quote)
    return quote
    #for q in quote['QuoteResponse']['QuoteData']:
    #    print(q['All'])

def get_last_price (market, symbol):
    quote = market.get_quote([symbol], detail_flag='intraday', skip_mini_options_check=True, resp_format='json')
    last_price = quote['QuoteResponse']['QuoteData'][0]['Intraday']['lastTrade']
    return last_price

def get_market(token):
    start = time.time()
    market = pyetrade.ETradeMarket(consumer_key,consumer_secret,token['oauth_token'],token['oauth_token_secret'],dev=False)
    end = time.time()
    print(f'get_market : {end - start}')
    return market

def stream_quote(symbol,token):
    start = time.time()
    for i in range(0, 10):
        quote = get_quote([symbol], token)
        q = quote['QuoteResponse']['QuoteData'][0]['Intraday']
        nyc_datetime = datetime.datetime.now(pytz.timezone('US/Eastern')).strftime("%Y-%m-%d %H:%M:%S.%f")
        print(f" {nyc_datetime} {q['lastTrade']}")
    end = time.time()
    print(end - start)

def preview_and_place (symbol, token, account_id_key):
    order = pyetrade.ETradeOrder (consumer_key,consumer_secret,token['oauth_token'],token['oauth_token_secret'],dev=False)
    client_order_id = str(time.time())
    print (f'client_order_id {client_order_id}')
    nyc_datetime = datetime.datetime.now(pytz.timezone('US/Eastern')).strftime("%Y-%m-%d %H:%M:%S.%f")

    my_preview = order.preview_equity_order (#resp_format='json', #bug in pyetrade
                                accountId = account_id_key,
                                symbol=symbol ,
                                allOrNone=False,
                                orderAction='BUY',
                                clientOrderId=client_order_id,
                                priceType='MARKET',
                                quantity=1,
                                marketSession ='REGULAR',
                                orderTerm='GOOD_FOR_DAY')

    preview_id = my_preview['PreviewOrderResponse']['PreviewIds']['previewId']
    print(f"{nyc_datetime}  preview_id : {preview_id}")

    myorder = order.place_equity_order (
        orderId=preview_id,
        accountId=account_id_key,
        symbol=symbol ,
        orderAction='BUY',
        clientOrderId=client_order_id,
        priceType='MARKET',
        quantity=1,
        orderTerm='GOOD_FOR_DAY',
        marketSession='REGULAR'
        )
    return myorder





def list_order (token, account_id_key):
    orders = pyetrade.ETradeOrder (consumer_key,consumer_secret,token['oauth_token'],token['oauth_token_secret'],dev=False)

    print(f"list : {orders.list_orders(account_id_key, resp_format='json')}")


token = get_token()


market = get_market(token)
for i in range(0,30):
    nyc_datetime = datetime.datetime.now(pytz.timezone('US/Eastern')).strftime("%Y-%m-%d %H:%M:%S.%f")
    last = get_last_price(market, symbol)
    print (f'{nyc_datetime} {symbol} {last}')




#accounts = list_accounts(token)
#print (f'accounts:{accounts}')
#account_id_key = accounts['AccountListResponse']['Accounts']['Account']['accountIdKey']
#print (f'account_id_key:{account_id_key}')
#
##list_order(token, account_id_key)
#nyc_datetime = datetime.datetime.now(pytz.timezone('US/Eastern')).strftime("%Y-%m-%d %H:%M:%S.%f")
#quote = get_quote([symbol], token)
#q = quote['QuoteResponse']['QuoteData'][0]['Intraday']
#print(f" {nyc_datetime} lastTrade : {q['lastTrade']}")
##myorder = preview_and_place (symbol, token, account_id_key)
##nyc_datetime = datetime.datetime.now(pytz.timezone('US/Eastern')).strftime("%Y-%m-%d %H:%M:%S.%f")
##print(f"{nyc_datetime}  myorder : {myorder}")
#list_order (token, account_id_key)