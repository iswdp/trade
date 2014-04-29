import urllib, re, datetime, random
from pandas import DataFrame
import pandas as pd

def import_stock_price_range(symbol, start_date, end_date):
    #import stock data from yahoo finance and returns a dataframe of historical price info
    end_date = end_date.split('/')
    end_month = str(int(end_date[0]) - 1)
    end_day = end_date[1]
    end_year = end_date[2]

    start_date = start_date.split('/')
    start_month = str(int(start_date[0]) - 1)
    start_day = start_date[1]
    start_year = start_date[2]  
      
    url = 'http://ichart.finance.yahoo.com/table.csv?s=' + symbol +'&d=' + end_month +'&e=' + end_day + '&f=' + end_year + '&g=d&a=' + start_month + '&b=' + start_day + '&c=' + start_year + '&ignore=.csv'
    try:
        data = pd.read_csv(url)
        data = data.reindex(index=data.index[ ::-1 ]).reset_index()
        del data['index']
        return data
    except:
        print 'No data available for selected dates.'
        return DataFrame()

def import_stock_prices(symbol):
    #import stock data from yahoo finance and returns a dataframe of all historical price info
    url = 'http://finance.yahoo.com/q/hp?s=' + symbol + '+Historical+Prices'
    month_dict = {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6, 'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12}
    try:
        htmltext = urllib.urlopen(url).read()
    except:
        print 'Error code 1'
        return 1

    regex = '<label for="startyear" class="srinfo">Year</label><input type="text" name="c" id="startyear" size="4" maxlength="4" value="(.+?)">'
    pattern = re.compile(regex)
    start_year = re.findall(pattern, htmltext)[0]

    regex = '<option selected value="[0-9][0-9]">(.+?)</option>'
    pattern = re.compile(regex)
    start_month = re.findall(pattern, htmltext)[0]
    start_month = month_dict[start_month]

    regex = '<label for="startday" class="srinfo">day</label><input type="text" name="b" id="startday" size="2" maxlength="2" value="(.+?)">'
    pattern = re.compile(regex)
    start_day = re.findall(pattern, htmltext)[0]

    end_year = datetime.datetime.now().year
    end_month = datetime.datetime.now().month
    end_day = datetime.datetime.now().day

    start_date = str(start_month) +'/' + str(start_day) + '/' + str(start_year)
    end_date = str(end_month) + '/' + str(end_day) + '/' + str(end_year)

    result = import_stock_price_range(symbol, start_date, end_date)

    return result

def forward_lag(stock_data, symbol, n = 1, OP = 'Average Price'):
    #takes yahoo finance historical stock data and forward lags it for use in trading simulations
    data = stock_data
    data['Symbol'] = symbol
    data['Average Price'] = (data['Open'] + data['High'] + data['Low'] + data['Close']) / 4.
    lag_list = []
    lag_name = 'Forward Lag  ' + str(n)

    price_multiple = []
    adj_price = []
    adj_price_name = 'Adj ' + str(OP)
    for i in range(len(data)):
        temp = stock_data['Close'][i] / stock_data['Adj Close'][i]
        temp_price = stock_data[OP][i] / temp
        price_multiple.append(temp)
        adj_price.append(temp_price)
    data['Adj Multiple'] = price_multiple
    data[adj_price_name] = adj_price
    data = data[['Symbol', 'Adj Multiple', 'Date', 'Average Price']]

    for i in range(len(data) - (n)):
        lag_list.append(((data['Average Price'][i + n]) / (data['Average Price'][i])) - 1)

    data = data.ix[0:(len(data) - n - 1),:]
    data[lag_name] = lag_list

    return data

def back_lag(stock_data, symbol, n = 1, OP = 'Open'):
    #takes yahoo finance historical stock data and backward lags it for use as a feature set
    data = stock_data
    data['Symbol'] = symbol
    data['Ave Price'] = (data['Open'] + data['High'] + data['Low'] + data['Close']) / 4.
    #data['Standard Volume'] = data['Volume'] * data['Ave Price']
    lag_list = []
    lag_col_names = []

    price_multiple = []
    adj_price = []
    adj_price_name = 'Adj ' + str(OP)
    for i in range(len(data)):
        temp = stock_data['Close'][i] / stock_data['Adj Close'][i]
        temp_price = stock_data[OP][i] / temp
        price_multiple.append(temp)
        adj_price.append(temp_price)
    data['Adj Multiple'] = price_multiple
    data[adj_price_name] = adj_price
    #data = data[['Symbol', 'Adj Multiple', 'Date', OP, adj_price_name, 'Standard Volume']]
    data = data[['Symbol', 'Adj Multiple', 'Date', OP]]
    data['tOpen'] = data[OP]

    for i in range(n):
        temp = []
        for j in range(n):
            temp.append(0)
        lag_list.append(temp)
        lag_col_names.append('Lag ' + str(i + 1))

    for i in range(n, len(data)):
        for j in range(len(lag_list)):
            lag_list[j].append((data[OP][i]/(data[OP][i - (j + 1)])) - 1)

    lag_list = DataFrame(lag_list).T
    lag_list.columns = lag_col_names
    
    data = pd.concat([data, lag_list], axis = 1)
    data = data.ix[n:,:].reset_index()

    return data

def combine_lags(forward, back):
    for i in range(len(forward)):
        if forward['Date'][i] == back['Date'][0]:
            start = i
    for i in range(len(back)):
        if back['Date'][i] == forward['Date'][len(forward)-1]:
            end = i

    forward = forward.ix[start:,:].reset_index()
    del forward['index']
    back = back.ix[:end,:].reset_index()
    del back['index']
    del back['level_0']
    del back['Symbol']
    del back['Adj Multiple']
    del back['Date']
    try:
        del back['Close']
        del back['Adj Close']
    except:
        del back['Open']

    result = pd.concat([forward, back], axis = 1)
    return result

def construct_model_data(symbol_list, n = 10, flag = 1, blag = 10):
    train = DataFrame()
    test = DataFrame()
    for i in symbol_list:
        print i

        try:
            data = import_stock_prices(i)
            forward = forward_lag(data, i, flag)
            back = back_lag(data, i, blag)
            combined = combine_lags(forward, back)

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
            combined = combined.drop(random_sample).reset_index()
            random_sample = []
            for j in range(n):
                random_sample.append(random.randint(0,(len(combined) - 1)))
            data_slice = combined.ix[random_sample,:].reset_index()
            if len(test) == 0:
                test = data_slice
            else:
                test = pd.concat([test, data_slice], axis = 0)

        except:
            print '\tSkipped'
            pass

    del train['index']
    del test['index']
    del test['level_0']

    return train, test

def main():
    fi = open('micro_cap_symbols.txt', 'r')
    symbols = []
    for i in fi:
        symbols.append(i.strip())
    #symbols = symbols[0:5]

    train, test = construct_model_data(symbols, n = 50, flag = 3, blag = 20)
    train.to_csv('stocks_train.csv', sep = ',', index = False)
    test.to_csv('stocks_test.csv', sep = ',', index = False)

if __name__ == '__main__':
    status = main()
    exit(status)