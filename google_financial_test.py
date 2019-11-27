import pandas_datareader as pdr
import pandas as pd
import datetime
current=datetime.datetime.now().strftime("%Y-%m-%d")

aapl = pdr.get_data_yahoo('AAPL',start=current,end=current)['Adj Close']


a = pd.Series(aapl[current])

for i in a:
    j=i
j=[ i for i in a]

print(j[0])