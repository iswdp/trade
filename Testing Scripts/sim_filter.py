import pandas as pd
from pandas import DataFrame

data = pd.read_csv('temp_results/pennies_result.csv')
result = DataFrame()

date_list = []
for i in  data['Date']:
    if i not in date_list:
        date_list.append(i)

for i in date_list:
    temp = data.ix[data['Date'] == i,:].sort('Prediction', ascending = False).reset_index()
    del temp['index']
    temp = DataFrame(temp.ix[0,:]).T

    if len(result) == 0:
        result = temp
    else:
        result = pd.concat([result, temp], axis = 0)

result = result.reset_index()
del result['index']

result.to_csv('temp_results/current_filtered_result1.csv', sep=',', index = False)