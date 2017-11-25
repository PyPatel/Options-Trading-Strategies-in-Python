# Let's Start

#Import the necesary libraries

# To get the closing prices data
from pandas_datareader import data as pdr
import fix_yahoo_finance as yf
yf.pdr_override()

# Plotting data
import matplotlib.pyplot as plt
import seaborn

#data Manipulation
import numpy as np
import pandas as pd


# Define a function to calculate the strategy performance on a stock
def strategy_performance(stock_ticker):
    stock = pdr.get_data_yahoo(stock_ticker, start = "2009-01-01", end = "2017-11-10")
    
    # Compute 55 days breakout and mean
    # 5 days high
    stock['high'] = stock.Close.shift(1).rolling(window = 55).max()

    # 55 days low
    stock['low'] = stock.Close.shift(1).rolling(window = 55).min()
    
    # 55 days mean
    stock['avg'] = stock.Close.shift(1).rolling(window = 55).mean()

    # ENTRY RULE

    ''' We will enter the position if the closing price of the stock is grreater than the high
        of the past 55 days. Go Long. '''
    stock['long_entry'] = stock.Close > stock.high
    stock['short_entry'] = stock.Close < stock.low

    # EXIT RULE
    ''' We will exit the position if the the stock price crosses the mean of the past 55 days '''

    stock['long_exit']= stock.Close < stock.avg
    stock['short_exit'] = stock.Close > stock.avg

    # POSITIONS

    '''
    Long postitions are indicated by 1 and short is indicated by -1
    No position is indicated by 0
    we will carrry forward previous position if no position exists
    '''
    stock['positions_long']= np.nan
    stock.loc[stock.long_entry, 'positions_long'] = 1
    stock.loc[stock.long_exit, 'positions_long'] = 0

    stock['positions_short']= np.nan
    stock.loc[stock.short_entry, 'positions_short'] = -1
    stock.loc[stock.short_exit, 'positions_short'] = 0

    stock['Signal'] = stock.positions_long + stock.positions_short

    stock = stock.fillna(method = 'ffill')

    ## STRATEGY RETURNS
    ''' we have to compute the log returns of the stock and multipled with the signal 1,-1,0 to
        get the strategy returns '''
    daily_log_returns = np.log(stock.Close/stock.Close.shift(1))
    daily_log_returns = daily_log_returns * stock.Signal.shift(1)

    # Plot the distribution of daily log returns
    print stock_ticker
    daily_log_returns.hist(bins = 50)
    plt.show()
    return daily_log_returns.cumsum()


##Create a portfolio of stocks and calculate the strategy performance for each stock

portfolio = ['AAPL', 'KMI', 'F']
cum_daily_return = pd.DataFrame()
for stock in portfolio:
    cum_daily_return[stock] =  strategy_performance(stock)

#  Plot the cumulative daily returns
print "Cumulative daily returns"
cum_daily_return.plot()
plt.show()

# That is all. Thanks for watching. Do like and subscribe for more videos like this.