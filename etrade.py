import pyetrade
import time
import datetime, pytz
consumer_key = "7054284dfb42fd505030408d4ec0d4d3"
consumer_secret = "1e9dee8bc1bd2b62a3a555560f635bbf4689512f03441e1bdea0a0487f79a108"


def gettokens():
    oauth = pyetrade.ETradeOAuth(consumer_key, consumer_secret)
    print(oauth.get_request_token())  # Use the printed URL

    verifier_code = input("Enter verification code: ")
    tokens = oauth.get_access_token(verifier_code)
    print(tokens)

def list_accounts(tokens):
    accounts = pyetrade.ETradeAccounts(consumer_key,consumer_secret,tokens['oauth_token'],tokens['oauth_token_secret'],dev=False)
    return accounts.list_accounts()

def get_quote(symbols, tokens):
    maket = pyetrade.ETradeMarket(consumer_key,consumer_secret,tokens['oauth_token'],tokens['oauth_token_secret'],dev=False)
    quote = maket.get_quote(symbols, detail_flag='intraday', skip_mini_options_check=True, resp_format='json')
    #print (quote)
    return quote
    #for q in quote['QuoteResponse']['QuoteData']:
    #    print(q['All'])


def stream_quote(symbol,tokens):
    start = time.time()
    for i in range(0, 10):
        quote = get_quote([symbol], tokens)
        q = quote['QuoteResponse']['QuoteData'][0]['Intraday']
        nyc_datetime = datetime.datetime.now(pytz.timezone('US/Eastern')).strftime("%Y-%m-%d %H:%M:%S.%f")
        print(f" {nyc_datetime} {q['lastTrade']}")
    end = time.time()
    print(end - start)

def preview_and_place (symbol, tokens, account_id_key):
    order = pyetrade.ETradeOrder (consumer_key,consumer_secret,tokens['oauth_token'],tokens['oauth_token_secret'],dev=False)
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





def list_order (tokens, account_id_key):
    orders = pyetrade.ETradeOrder (consumer_key,consumer_secret,tokens['oauth_token'],tokens['oauth_token_secret'],dev=False)

    print(f"list : {orders.list_orders(account_id_key, resp_format='json')}")


tokens = {'oauth_token': 'hQRjEPLUdeOM0Xj0GHhv8V8z1zanULHtaj5H5rZ50FM=', 'oauth_token_secret': 'YhhTnyVkvT35MtX4HL/Ah1N5CbC5O8BK/sknx5CzW2s='}
symbol = 'ZNGA'

accounts = list_accounts(tokens)
print (f'accounts:{accounts}')
account_id_key = accounts['AccountListResponse']['Accounts']['Account']['accountIdKey']
print (f'account_id_key:{account_id_key}')

#list_order(tokens, account_id_key)
nyc_datetime = datetime.datetime.now(pytz.timezone('US/Eastern')).strftime("%Y-%m-%d %H:%M:%S.%f")
quote = get_quote([symbol], tokens)
q = quote['QuoteResponse']['QuoteData'][0]['Intraday']
print(f" {nyc_datetime} lastTrade : {q['lastTrade']}")
#myorder = preview_and_place (symbol, tokens, account_id_key)
#nyc_datetime = datetime.datetime.now(pytz.timezone('US/Eastern')).strftime("%Y-%m-%d %H:%M:%S.%f")
#print(f"{nyc_datetime}  myorder : {myorder}")
list_order (tokens, account_id_key)