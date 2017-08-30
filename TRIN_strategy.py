import pandas as pd
import quandl
import matplotlib.pyplot as plt
import math

def variance_calculator(series, series_average, win_len):
    sma = win_len
    temp = series.subtract(series_average) # Difference a-b
    temp2 = temp.apply(lambda x:x**2)  # Square them.. (a-b)^2
    temp3 = temp2.rolling(sma - 1).mean() # Summation (a-b)^2 / (sma - 1)
    sigma = temp3.apply(lambda x: math.sqrt(x)) 
    return sigma
 
# Getting the Data
data1 = quandl.get("CHRIS/CME_SP1", authtoken = "9EfoixVwAcrEgCSe7y_F" , start_date = "2017-07-27")
declining = quandl.get("URC/NYSE_DEC", authtoken = "9EfoixVwAcrEgCSe7y_F" , start_date = "2017-07-27")
advancing = quandl.get("URC/NYSE_ADV", authtoken = "9EfoixVwAcrEgCSe7y_F" , start_date = "2017-07-27")
adv_vol = quandl.get("URC/NYSE_ADV_VOL", authtoken = "9EfoixVwAcrEgCSe7y_F" , start_date = "2017-07-27")
dec_vol = quandl.get("URC/NYSE_DEC_VOL", authtoken = "9EfoixVwAcrEgCSe7y_F" , start_date = "2017-07-27")

data = declining
data['declining'] = declining['Numbers of Stocks']
data['advancing'] = advancing['Numbers of Stocks']
data['dec_vol'] = dec_vol['Numbers of Stocks']
data['adv_vol'] = adv_vol['Numbers of Stocks']

merged = data.join(data1)
merged = merged.fillna(method = 'ffill')
data = merged

# Finding the TRIN Value

ad_ratio = data['advancing'].divide(data['declining']) # AD Ratio
ad_vol = data['adv_vol'].divide(data['dec_vol']) # AD Volume Ratio
trin = ad_ratio.divide(ad_vol)  # TRIN Value

data['TRIN'] = trin
data['TRIN'] = data['TRIN'].apply(lambda x: math.log(x))
data['future'] = data['Last']
data.to_csv("tempr_data.csv")

data= pd.read_csv("tempr_data.csv")

# Variables

sma = 22 #  Moving Average Window length
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

data['mAvg'] = data['TRIN'].rolling(sma).mean() # Calculating the moving average of the TRIN
data['TRIN_prev'] = data['TRIN'].shift(1)
data.to_csv("tempr_data.csv")
data = pd.read_csv("tempr_data.csv")


sigma = variance_calculator(data['TRIN'], data['mAvg'], sma )  # Calculating the standard deviation
k_sigma = k * sigma
l_sigma = l * sigma


data['UBB'] = data['mAvg'].add(k_sigma) # Upper Bollinger Band
data['LBB'] = data['mAvg'].subtract(k_sigma)  # Lower Bollinger Band
data['USL'] = data['UBB'].add(l_sigma)  # Upper Stoploss Band
data['LSL'] = data['LBB'].subtract(l_sigma)  # Lower Stoploss Band
data['order'] = pd.Series() # list which contains the orders: BUY / SELL / Do Nothing

s = data['TRIN'].size  # Total Number of data point

# Logic for Trading

for i in range(s):

    pro = 0
    future_cost = data['future'][i]
    TRIN = data['TRIN'][i]
    TRIN_prev = data['TRIN_prev'][i]
    LBB = data['LBB'][i]
    UBB = data['UBB'][i]
    mAvg = data['mAvg'][i]
    USL = data['USL'][i]
    LSL = data['LSL'][i]


    UBB_cross = (TRIN > UBB) and (TRIN_prev < UBB)  # Check if TRIN crosses Upper Bollinger Band
    LBB_cross = (TRIN < LBB) and (TRIN_prev > LBB)  # Check if TRIN crosses Lower Bollinger Band
    mAvg_cross_up = (TRIN > mAvg) and (TRIN_prev < mAvg)  # Check if TRIN crosses moving average from low to high
    mAvg_cross_down = (TRIN < mAvg) and (TRIN_prev > mAvg)  # Check if TRIN crosses moving average from high to low
    USL_cross = (TRIN > USL) and (TRIN_prev < USL) # Check if TRIN Crosses upper stoploss band
    LSL_cross = (TRIN < LSL) and (TRIN_prev > LSL) # Check if TRIN Crosses lower stoploss band

    # Strategy
    if(UBB_cross and (not buy_flag) and flag == 1):
        flag = 0
        buy_flag = True
        sell_flag = False
        transaction_start_price = future_cost
        order_details = [1, "Buy", "UBB Crossed", "0", "Position taken"]
    
    elif(LBB_cross and (not sell_flag) and flag == 1):
        flag = 0
        sell_flag = True
        buy_flag = False
        transaction_start_price = future_cost
        order_details = [-1, "Sell", "LBB Crossed", "0", "Position taken"]

    elif(mAvg_cross_up and (not buy_flag) and flag == 0):  # Places "BUY" order if TRIN crosses mAvg from low to high to close a trade
        flag = 1
        buy_flag = False
        sell_flag = False
        pro = future_cost - transaction_start_price
        order_details = [1, "Buy", "mAvg Crossed", "0", "Position Closed"]

    elif(LSL_cross and (not buy_flag) and flag == 0):  # Places "BUY" order if TRIN crosses lower stoploss band to close a trade
        flag = 1
        buy_flag = False
        sell_flag = False
        pro = future_cost - transaction_start_price
        order_details = [1, "Buy", "LSB Crossed", "Stoploss Executed", "Position Closed"]

    elif((future_cost - transaction_start_price) > abs_SL and (not buy_flag) and flag == 0):  # Places "BUY" order if TRIN crosses lower stoploss absolute value
        flag = 0
        buy_flag = False
        sell_flag = False
        pro = future_cost - transaction_start_price
        order_details = [1, "Buy", "LSB Crossed", "Stoploss Executed", "Position Closed"]

    elif(mAvg_cross_down and (not sell_flag) and flag == 0):  # Places "Sell" order if TRIN crosses mAvg from high to low to close a trade
        flag = 1
        buy_flag = False
        sell_flag = False
        pro = - (future_cost - transaction_start_price)
        order_details = [-1, "Sell", "mAvg Crossed (H to L)", "0", "Position Closed"]

    elif(USL_cross and (not sell_flag) and flag == 0):  # Places "Sell" order if TRIN crosses Upper stoploss band to close a trade
        flag = 1
        buy_flag = False
        sell_flag = False
        pro = - (future_cost - transaction_start_price)
        order_details = [-1, "Sell", "USB Crossed", "Stoploss Executed", "Position Closed"]

    elif( (- future_cost - transaction_start_price) > abs_SL and (not sell_flag) and flag == 0):  # Places "SELL" order if TRIN crosses Upper stoploss absolute value
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
                tempo = (data['future'][i] - transaction_start_price) * 500
            if(buy_flag == 0 and sell_flag == 1):
                tempo = (- data['future'][i] + transaction_start_price) * 500
        order_details = [0, "No Trade", "No Trade", "0", tempo]

    profit.append(pro)
    order.append(order_details[0])
    buy_sell.append(order_details[1])
    trade_cause.append(order_details[2])
    stoploss.append(order_details[3])
    mtm.append(order_details[4])


data['placed_order'] = pd.Series(order)  # Converting list into Panda Series
data['cost'] = - (data['placed_order'].multiply(data['future'])) * 500  #  Cost of each transaction
data['out'] = data['cost'].cumsum()   # Out is the cumulative cost profit / loss after transaction till now
data['buy_sell'] = pd.Series(buy_sell)
data['profit'] = -pd.Series(profit) * 500
data['stoploss'] = pd.Series(stoploss)
data['trade_cause'] = pd.Series(trade_cause)
data['mtm'] = pd.Series(mtm)

print(data['out'])

output = pd.DataFrame() # Final output to be stored in excel file
output['date'] = data['Date']
output['Close'] = data['future']
output['TRIN'] = data['TRIN']
output['placed_order'] = data['placed_order']
output['buy_sell'] = data['buy_sell']
output['trade_cause'] = data['trade_cause']
output['PnL'] = data['profit']
output['mtm'] = data['mtm']
output['stoploss'] = data['stoploss']
output['Cash Account'] = data['out']

output.to_excel('TRIN_SL_output.xlsx', sheet_name='Sheet1')


# Plot
plt.plot(data['TRIN'])
plt.plot(data['mAvg'])
plt.plot(data['UBB'])
plt.plot(data['LBB'])
plt.show()