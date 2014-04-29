from stocks import *
from trade import *
from pandas import DataFrame
import pandas as pd

data = import_stock_prices('SPY')
forward = forward_lag(data, 'SPY', 1)
back = back_lag(data, 'SPY', 10)
combined = combine_lags(forward, back)
combined = combined.ix[combined['Forward Lag  1'] < .8,:].reset_index()
del combined['index']
today_back = prediction_back_lag(data, 'SPY', 10)
print today_back.tail()

combined.to_csv('testing.csv', sep = ',', index = False)
forward.to_csv('forward.csv', sep = ',', index = False)
data.to_csv('datadata.csv', sep = ',', index = False)
back.to_csv('back.csv', sep = ',', index = False)
today_back.to_csv('today_back.csv', sep = ',', index = False)