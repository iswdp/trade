from stocks import *
import pandas as pd
import dateutil

def construct_local_model_data(symbol_list, date_split, n = 10, flag = 1, blag = 10):
    train = DataFrame()
    test = DataFrame()
    date_split = dateutil.parser.parse(date_split)
    for i in symbol_list:
        print i

        try:
            path = '45-165caps/' + i + '.csv'
            data = pd.read_csv(path)
            forward = forward_lag(data, i, flag)
            back = back_lag(data, i, blag)
            combined = combine_lags(forward, back)
            combined = combined.ix[combined['Forward Lag  1'] < .2,:].reset_index()
            del combined['index']

            for j in range(len(combined)):
                combined['Date'][j] = dateutil.parser.parse(combined['Date'][j])

            #Train------------------------------------------------------------------
            random_sample = []
            train_section = combined.ix[combined['Date'] < date_split,:].copy()
            for j in range(n):
                random_sample.append(random.randint(0,(len(train_section) - 1)))
            data_slice = train_section.ix[random_sample,:].reset_index()
            if len(train) == 0:
                train = data_slice
            else:
                train = pd.concat([train, data_slice], axis = 0)

            #Test-------------------------------------------------------------------
            random_sample = []
            test_section = combined.ix[combined['Date'] > date_split,:].reset_index()
            for j in range(n):
                random_sample.append(random.randint(0,(len(test_section) - 1)))
            #data_slice = test_section.ix[random_sample,:].reset_index() #Use a sample of test set
            data_slice = test_section.ix[:,:].reset_index() #Use entire test set
            if len(test) == 0:
                test = data_slice
            else:
                test = pd.concat([test, data_slice], axis = 0)

        except:
            print '\tSkipping this symbol.'

    test = test.sort('Date')

    del train['index']
    del test['index']
    del test['level_0']

    return train, test

fi = open('45-165caps.txt', 'r')
symbols = []
for i in fi:
    symbols.append(i.strip())
#symbols = symbols[0:25]

train, test = construct_local_model_data(symbols, '01-01/2012', n = 200, flag = 1, blag = 20)
train.to_csv('local_train.csv', sep = ',', index = False)
test.to_csv('local_test.csv', sep = ',', index = False)