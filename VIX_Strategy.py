import pandas as pd
import quandl
import matplotlib.pyplot as plt
import math


def fetch_data(string1, string2, string3, filename):
    w = quandl.get(string1, authtoken = string2, start_date = string3)
    w.to_csv(filename)
    w = pd.read_csv(filename)
    return w

# The Data pulled from quandl and stored locally for faster execution
Data = fetch_data("CHRIS/CME_SP1", "", "2017-07-31", "local_future.csv")
Data1 = fetch_data("CHRIS/SPX_PC", "", "2017-07-31", "local_data.csv")

Data['future'] = Data1['Last']
Data['VIX'] = Data['VIX Close']

# Variables
mtm = list()
order_details = list()
order = list()  #list which contains the orders: BUY / SELL / Do Nothing
profit = list()
buy_sell = list()
stoploss = list()
pro = 0  # Profit Variable
v = 0  # 'v' is the price at which we buy S&P 500 futures at that particular level of VIX
thresh = 22  # VIX threshold for placing buy order
change_1 = 5  # % of the buy price to be used for executing a take profit order
change_2 = 5  # % of the buy price to be used for executing a stoploss order
buy_flag = False
Sell_flag = True
s = Data['future'].size  # size of VIX dataset
c_1 = (1 + (change_1)/float(100))  # c_1 is the value above which the sell order wi;; execute in a successful trade
c_2 = (1 - (change_2)/float(100))  # c_2 is the value below a sell order will execute in a stoploss

for i in range(s):
    pro = 0

    if(Data['VIX'][i]>= thresh and (not buy_flag)):
        order_details = [-1, "Buy", "0", "Position Taken"]
        buy_flag = True
        Sell_flag = False
        v = Data['future'][i]

    elif(Data['future'][i] >= (c_1) * v and (not Sell_flag)):
        buy_flag = False
        Sell_flag = True
        pro = (Data['future'][i] - v)
        order_details = [1, "Sell", "0", "Position Closed"]

    elif(Data['future'][i] <= (c_2)*v and (not Sell_flag)):
        buy_flag = False
        Sell_flag = True
        pro = (Data['future'][i] - v)
        order_details = [1, "Sell", "Stoploss Executed", "Position Closed"]

    else:
        if(buy_flag == 1 ):
            x = (Data['future'][i] - v) * 500 * 2
        else:
            x = "0"
        order_details = [0, "No Trade", "0", x]


    profit.append(pro)
    order.append(order_details[0])
    buy_sell.append(order_details[1])
    stoploss.append(order_details[2])
    mtm.append(order_details[3])

Data['placed_order'] = pd.Series(order)  # Converting list into Panda Series
Data['cost'] = - (Data['placed_order'].multiply(Data['future'])) * 500 * 2  #  Cost of each transaction
Data['out'] = Data['cost'].cumsum()   # Out is the cumulative cost profit / loss after transaction till now
Data['buy_sell'] = pd.Series(buy_sell)
Data['profit'] = -pd.Series(profit) * 500 * 2
Data['stoploss'] = pd.Series(stoploss)
Data['mtm'] = pd.Series(mtm)

print(Data['out'])

output = pd.DataFrame() # Final output to be stored in excel file
output['date'] = Data['Date']
output['Close'] = Data['future']
output['VIX'] = Data['VIX']
output['placed_order'] = Data['placed_order']
output['buy_sell'] = Data['buy_sell']
output['Profit'] = Data['profit']
output['mtm'] = Data['mtm']
output['stoploss'] = Data['stoploss']

output.to_excel('VIX_SL_output.xlsx', sheet_name='Sheet1')

plt.plot(Data['out'])
plt.show()