from stocks import *
from pandas import DataFrame
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
import datetime, random

def get_today_open(symbol):
    url = 'http://finance.yahoo.com/q?s=' + symbol
    htmltext = urllib.urlopen(url).read()
    regex = 'Open:</th><td class="yfnc_tabledata1">(.+?)</td>'
    pattern = re.compile(regex)
    today_open = float(re.findall(pattern, htmltext)[0])

    return today_open

def prediction_back_lag(stock_data, symbol, n = 1, OP = 'Open'):
    #takes yahoo finance historical stock data and backward lags it for use as a feature set
    data = stock_data
    data['Symbol'] = symbol
    data['Ave Price'] = (data['Open'] + data['High'] + data['Low'] + data['Close']) / 4.
    lag_list = []
    lag_col_names = []

    price_multiple = []
    adj_price = []
    adj_price_name = 'Adj ' + str(OP)

    volume = []
    three_vma = []
    nine_vma = []

    for i in range(len(data)):
        temp = stock_data['Close'][i] / stock_data['Adj Close'][i]
        temp_price = stock_data[OP][i] / temp
        price_multiple.append(temp)
        adj_price.append(temp_price)
        
    data['Adj Multiple'] = price_multiple
    data[adj_price_name] = adj_price
    data = data[['Symbol', 'Adj Multiple', 'Date', OP, 'Volume']]
    data['tOpen'] = data[OP]
    data = pd.concat([data, DataFrame(data.ix[len(data)-1,:]).T], axis = 0).reset_index()
    del data['index']

    today = get_today_open(symbol)
    data['Date'][len(data)-1] = datetime.datetime.today().strftime('%Y-%m-%d')
    data['Open'][len(data)-1] = today
    data['tOpen'][len(data)-1] = today


    for i in range(n):
        temp = []
        for j in range(n):
            temp.append(0)
        lag_list.append(temp)
        lag_col_names.append('Lag ' + str(i + 1))

    for i in range(n, len(data)):
        for j in range(len(lag_list)):
            lag_list[j].append((data[OP][i]/(data[OP][i - (j + 1)])) - 1)
    for i in range(0,len(data)):
        if len(volume) == 0:
            volume.append(0)
        else:
            volume.append(data['Volume'][i-1])

    del data['Volume']

    lag_list = DataFrame(lag_list).T
    lag_list.columns = lag_col_names
    
    data = pd.concat([data, lag_list], axis = 1)
    data['Volume'] = volume
    data['Volume'] = data['Volume'] * data[OP]

    for i in range(len(data)):
        if i < 3:
            three_vma.append(0)
        else:
            three_vma.append(sum(data['Volume'][(i-3):i])/3.)

        if i < 9:
            nine_vma.append(0)
        else:
            nine_vma.append(sum(data['Volume'][(i-9):i])/9.)

    data['three_vma'] = three_vma
    data['nine_vma'] = nine_vma
    data = data.ix[n:,:].reset_index()

    return data

def build_data(symbol_list, n = 15, flag = 1, blag = 10):
    train = DataFrame()
    test = DataFrame()
    for i in symbol_list:
        print i

        try:
            path = '45-165caps/' + i + '.csv'
            data = pd.read_csv(path)
            forward = forward_lag(data, i, flag)
            back = back_lag(data, i, blag)
            today_back = prediction_back_lag(data, i, blag)
            combined = combine_lags(forward, back)
            combined = combined.ix[combined['Forward Lag  1'] < .2,:].reset_index()
            del combined['index']

            #Train------------------------------------------------------------------
            random_sample = []
            for j in range(n):
                random_sample.append(random.randint(0,(len(combined) - 1)))
            data_slice = combined.ix[random_sample,:].reset_index()
            if len(train) == 0:
                train = data_slice
            else:
                train = pd.concat([train, data_slice], axis = 0)

            #Test-------------------------------------------------------------------
            data_slice = DataFrame(today_back.ix[len(today_back) - 1,:]).T

            if len(test) == 0:
                test = data_slice
            else:
                test = pd.concat([test, data_slice], axis = 0)
        except:
            print '\tSkipped'
            pass

    train = train.reset_index()
    del train['level_0']
    del train['index']

    test = test.reset_index()  
    del test['level_0']
    del test['index']

    combined.to_csv('combined1.csv', sep = ',', index = False)
    today_back.to_csv('today_back1.csv', sep = ',', index = False)

    return train, test

def main():
    fi = open('45-165caps.txt', 'r')
    symbols = []
    for i in fi:
        symbols.append(i.strip())
    #symbols = symbols[0:6]

    train, test = build_data(symbols, n = 200, flag = 1, blag = 20)

    train = train.replace([np.inf, -np.inf], np.nan)
    test = test.replace([np.inf, -np.inf], np.nan)

    train = train.dropna(axis=0)
    test = test.dropna(axis=0)

    #print train.head().T
    #print test.head().T

    print 'Fitting\n'
    m = RandomForestRegressor(n_estimators=500, n_jobs=10)
    m.fit(train.ix[:,5:], train.ix[:,4])
    print 'Predicting\n'
    preds = m.predict(test.ix[:,4:])

    result = test.ix[:,:4]
    result['Prediction'] = preds
    result = result.sort('Prediction', ascending=False)
    print result.head()
    result.to_csv('trade_result.csv', sep = ',', index = False)

if __name__ == '__main__':
    status = main()
    exit(status)