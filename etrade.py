import pyetrade

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
    print(accounts.list_accounts())

def get_quote(symbols, tokens):
    maket = pyetrade.ETradeMarket(consumer_key,consumer_secret,tokens['oauth_token'],tokens['oauth_token_secret'],dev=False)
    quote = maket.get_quote(symbols, skip_mini_options_check=True, resp_format='json')
    #print (quote)
    return quote
    #for q in quote['QuoteResponse']['QuoteData']:
    #    print(q['All'])


tokens = {'oauth_token': 'uD5TtYU9p9eqsSn0zEPEzKpF0GfU5cXf+BcZj7JHXgs=', 'oauth_token_secret': 'jUPQVqFDZFqc4bjRmXj5/AYzVL5pI3I+FcL3flwoqMQ='}
#list_accounts(tokens)
for i in range (0,10):
    quote = get_quote(['TSLA'], tokens)
    q = quote['QuoteResponse']['QuoteData'][0]
    print (q)
    #print (f" {q['dateTime']}  {q['lastTrade']}")
