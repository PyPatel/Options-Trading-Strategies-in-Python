import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import math
import quandl

def variance_calculator(series, series_average, win_len):
    sma = win_len
    temp = series.subtract(series_average) # Difference a-b
    temp2 = temp.apply(lambda x:x**2)  # Square them.. (a-b)^2
    temp3 = temp2.rolling(sma - 1).mean() # Summation (a-b)^2 / (sma - 1)
    sigma = temp3.apply(lambda x: math.sqrt(x)) 
    return sigma

def fetch_data(string1, string2, string3, filename):
    w = quandl.get(string1, authtoken = string2, start_date = string3)
    w.to_csv(filename)
    w = pd.read_csv(filename)
    return w

# The Data pulled from quandl and stored locally for faster execution
Data = fetch_data("CHRIS/CME_SP1", "", "2017-07-31", "local_future.csv")
Data1 = fetch_data("CHRIS/SPX_PC", "", "2017-07-31", "local_data.csv")

Data['future'] = Data1['Last']
Data['PCR'] = Data['S&P PUT-CALL RATIO']

# Variables

sma = 20 #  Moving Average Window length
k = 1.5 # Constant representing 'k' times sigma away from moving average (fir Bollinger bands)
l = 2 # cons.representing 'l' times sigma away from Bollinger band (for stoploss band) 
pro = 0  # Profit Variable
flag = 1 # Flag is there for begin first transaction -- transaction should start with LBB/UBB crossing only
buy_flag = False
sell_flag = False
transaction_start_price = 0
abs_SL = 25  # Absolute Stoploss Variable
mtm = list()
order_details = list()
order = list()  #list which contains the orders: BUY / SELL / Do Nothing
profit = list()
buy_sell = list()
stoploss = list()
trade_cause = list()

Data['mAvg'] = Data['PCR'].rolling(sma).mean() # Calculating the moving average of the PCR
Data['PCR_prev'] = Data['PCR'].shift(1)

sigma = variance_calculator(Data['PCR'], Data['mAvg'], sma )  # Calculating the standard deviation
k_sigma = k * sigma
l_sigma = l * sigma

Data['UBB'] = Data['mAvg'].add(k_sigma) # Upper Bollinger Band
Data['LBB'] = Data['mAvg'].subtract(k_sigma)  # Lower Bollinger Band
Data['USL'] = Data['UBB'].add(l_sigma)  # Upper Stoploss Band
Data['LSL'] = Data['LBB'].subtract(l_sigma)  # Lower Stoploss Band
Data['order'] = pd.Series() # list which contains the orders: BUY / SELL / Do Nothing

s = Data['PCR'].size  # Total Number of Data point

for i in range(s):
    
    pro = 0    # Profit at each trade
    future_cost = Data['future'][i]   # Cost of big S&P 500 futures bought
    PCR = Data['PCR'][i] # Put Call ratio 
    PCR_prev = Data['PCR_prev'][i]  # Previous day's put call ratio
    LBB = Data['LBB'][i]  # Lower Bollinger Band
    UBB = Data['UBB'][i]  # # Upper Bollinger Band
    mAvg = Data['mAvg'][i] # Moving Average
    USL = Data['USL'][i]  # Upper Stoploss Band
    LSL = Data['LSL'][i]  # Lower Stoploss Band

    # Comparisons stores as boolean variables a to place order accordingly
    UBB_cross = (PCR > UBB) and (PCR_prev < UBB)  # Check if PCR crosses Upper Bollinger Band
    LBB_cross = (PCR < LBB) and (PCR_prev > LBB)  # Check if PCR crosses Lower Bollinger Band
    mAvg_cross_up = (PCR > mAvg) and (PCR_prev < mAvg)  # Check if PCR crosses moving average from low to high
    mAvg_cross_down = (PCR < mAvg) and (PCR_prev > mAvg)  # Check if PCR crosses moving average from high to low
    USL_cross = (PCR > USL) and (PCR_prev < USL) # Check if PCR Crosses upper stoploss band
    LSL_cross = (PCR < LSL) and (PCR_prev > LSL) # Check if PCR Crosses lower stoploss band


    # Strategy
    if(UBB_cross and (not buy_flag) and flag == 1):  # Places "BUY" order if PCR crosses upper Bollinger band to open trade
        flag = 0
        buy_flag = True
        sell_flag = False
        transaction_start_price = future_cost  # Price at which s&P 500 future bought when the order is placed
        order_details = [1, "Buy", "UBB Crossed", "0", "Position taken"]

    elif(LBB_cross and (not sell_flag) and flag == 1):
        flag = 0
        sell_flag = True
        buy_flag = False
        transaction_start_price = future_cost
        order_details = [-1, "Sell", "LBB Crossed", "0", "Position taken"]

     elif(mAvg_cross_up and (not buy_flag) and flag == 0):  # Places "BUY" order if PCR crosses mAvg from low to high to close a trade
        flag = 1
        buy_flag = False
        sell_flag = False
        pro = future_cost - transaction_start_price
        order_details = [1, "Buy", "mAvg Crossed", "0", "Position Closed"]

    elif(LSL_cross and (not buy_flag) and flag == 0):  # Places "BUY" order if PCR crosses lower stoploss band to close a trade
        flag = 1
        buy_flag = False
        sell_flag = False
        pro = future_cost - transaction_start_price
        order_details = [1, "Buy", "LSB Crossed", "Stoploss Executed", "Position Closed"]

    elif((future_cost - transaction_start_price) > abs_SL and (not buy_flag) and flag == 0):  # Places "BUY" order if PCR crosses lower stoploss absolute value
        flag = 0
        buy_flag = False
        sell_flag = False
        pro = future_cost - transaction_start_price
        order_details = [1, "Buy", "LSB Crossed", "Stoploss Executed", "Position Closed"]

     elif(mAvg_cross_down and (not sell_flag) and flag == 0):  # Places "Sell" order if PCR crosses mAvg from high to low to close a trade
        flag = 1
        buy_flag = False
        sell_flag = False
        pro = - (future_cost - transaction_start_price)
        order_details = [-1, "Sell", "mAvg Crossed (H to L)", "0", "Position Closed"]

    elif(USL_cross and (not sell_flag) and flag == 0):  # Places "Sell" order if PCR crosses Upper stoploss band to close a trade
        flag = 1
        buy_flag = False
        sell_flag = False
        pro = - (future_cost - transaction_start_price)
        order_details = [-1, "Sell", "USB Crossed", "Stoploss Executed", "Position Closed"]

    elif( (- future_cost - transaction_start_price) > abs_SL and (not sell_flag) and flag == 0):  # Places "SELL" order if PCR crosses Upper stoploss absolute value
        flag = 1
        buy_flag = False
        sell_flag = False
        pro = - (future_cost - transaction_start_price)
        order_details = [-1, "Sell", "USB Crossed", "Abs Stoploss Executed", "Position Closed"]

    else:
        if(buy_flag == 0 and sell_flag == 0):
            tempo = "0"
        else:
            if(buy_flag == 1 and sell_flag == 0):
                tempo = (Data['future'][i] - transaction_start_price) * 500
            if(buy_flag == 0 and sell_flag == 1):
                tempo = (- Data['future'][i] + transaction_start_price) * 500
        order_details = [0, "No Trade", "No Trade", "0", tempo]

    profit.append(pro)
    order.append(order_details[0])
    buy_sell.append(order_details[1])
    trade_cause.append(order_details[2])
    stoploss.append(order_details[3])
    mtm.append(order_details[4])

Data['placed_order'] = pd.Series(order)  # Converting list into Panda Series
Data['cost'] = - (Data['placed_order'].multiply(Data['future'])) * 500  #  Cost of each transaction
Data['out'] = Data['cost'].cumsum()   # Out is the cumulative cost profit / loss after transaction till now
Data['buy_sell'] = pd.Series(buy_sell)
Data['profit'] = -pd.Series(profit) * 500
Data['stoploss'] = pd.Series(stoploss)
Data['trade_cause'] = pd.Series(trade_cause)
Data['mtm'] = pd.Series(mtm)

print(Data['out'])

output = pd.DataFrame() # Final output to be stored in excel file
output['date'] = Data['Date']
output['Close'] = Data['future']
output['PCR'] = Data['PCR']
output['placed_order'] = Data['placed_order']
output['buy_sell'] = Data['buy_sell']
output['trade_cause'] = Data['trade_cause']
output['PnL'] = Data['profit']
output['mtm'] = Data['mtm']
output['stoploss'] = Data['stoploss']
output['Cash Account'] = Data['out']

output.to_excel('PCR_SL_output.xlsx', sheet_name='Sheet1')


# Plot
plt.plot(Data['PCR'])
plt.plot(Data['mAvg'])
plt.plot(Data['UBB'])
plt.plot(Data['LBB'])
plt.show()