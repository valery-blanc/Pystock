import etrade
import time


market = etrade.get_market()
for i in range(0,1200):
    last = etrade.get_quote(['TSLA','AAPL', 'NTES', 'AMD', 'STX', 'TX', 'WDC', 'LYFT', 'FNF', 'DAL', 'TPR'], market)
    print (f'{last}')
    time.sleep(15)
