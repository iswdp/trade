from stocks import *
import dateutil, datetime, random
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
import numpy as np

def create_stock_dict(symbols):
    stock_data = {}

    for i in symbols:
        print i
        data = import_stock_prices(i)
        try:
            forward = forward_lag(data, i, 1)
            back = back_lag(data, i, 12)
            stock_data[i] = combine_lags(forward, back)
        except:
            print 'Skipping this symbol'
            pass

    return stock_data

def symbol_slice(df, start):
    #slices data for a single symbol up to the current test date
    start = dateutil.parser.parse(start)
    delta = datetime.timedelta(days=1)

    for i in range(50):
        try:
            end_index = df[df['Date'] == start.strftime('%Y-%m-%d')].index.values[0]
            break
        except:
            if i == 49:
                print '\tSymbol could not be sliced.'
                return DataFrame()
            pass
        start -= delta

    result = df.ix[:end_index,:]
    return result

def construct_rolling_model_data(stock_data, begin, n = 15):
    #returns a model dataframe and a feature vector for a prediction test set
    train = DataFrame()
    test = DataFrame()

    stock_dict = stock_data.copy()

    print 'Constructing model data.'

    pop_list = []
    for i in stock_dict:
        print 'Slicing ' + str(i)
        stock_dict[i] = symbol_slice(stock_dict[i], begin)

        if len(stock_dict[i]) == 0:
            pop_list.append(i)
    for i in pop_list:
        stock_dict.pop(i)

    for i in stock_dict:

        #Train------------------------------------------------------------------
        train_slice = stock_dict[i].ix[:(len(stock_dict[i])-2),:].reset_index()
        random_sample = []

        for j in range(n):
            random_sample.append(random.randint(0,(len(train_slice) - 1)))
        train_slice = train_slice.ix[random_sample,:]

        if len(train) == 0:
            train = train_slice
        else:
            train = pd.concat([train, train_slice], axis = 0)

        #Test-------------------------------------------------------------------
        if len(test) == 0:
            test = DataFrame(stock_dict[i].ix[(len(stock_dict[i])-1),:]).T
        else:
            test = pd.concat([test, DataFrame(stock_dict[i].ix[(len(stock_dict[i])-1),:]).T], axis = 0)

    train = train.reset_index()
    test = test.reset_index()
    return train, test

def sim(symbols, begin, n):
    SPY = import_stock_prices('SPY')
    date_list = []
    delta = datetime.timedelta(days=1)
    result = DataFrame()

    for i  in SPY['Date']:
        date_list.append(i)

    while begin not in date_list:
        begin = dateutil.parser.parse(begin)
        begin += delta
        begin = begin.strftime('%Y-%m-%d')

    for i in range(len(date_list)):
        if date_list[i] == begin:
            date_list = date_list[i:]
            break

    stock_data = create_stock_dict(symbols)

    m = RandomForestRegressor(n_estimators=250, n_jobs=10)
    for i in date_list:
        try:
            train, test = construct_rolling_model_data(stock_data, i, n)
            train = train.replace([np.inf, -np.inf], np.nan)
            test = test.replace([np.inf, -np.inf], np.nan)
            train = train.dropna(axis=0)
            test = test.dropna(axis=0)

            print 'Fitting model for ' + str(i)
            print ''
            print test.head()
            m.fit(train.ix[:,8:], train.ix[:,7])
            preds = m.predict(test.ix[:,7:])

            test = test.ix[:,1:7]
            test['Prediction'] = preds

            if len(result) == 0:
                result = test
            else:
                result = pd.concat([result, test], axis = 0)

            print '----------------------------------------------------------------------------------------------------------------'

        except:
            print '-------------------------------------------------------------------------------------------------'
            print 'Construct model error.  Skipping this date-------------------------------------------------------'
            print '-------------------------------------------------------------------------------------------------'
            pass

    result = result.reset_index()
    del result['index']
    return result

def main():
    fi = open('25-75_microcap_list.txt', 'r')
    symbols = []
    for i in fi:
        symbols.append(i.strip())
    #symbols = symbols[0:5]

    result = sim(symbols, '2004-01-01', n = 30)
    result.to_csv('large_micro_sim_result.csv', sep = ',', index = False)

if __name__ == '__main__':
    status = main()
    exit(status)