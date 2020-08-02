import numpy as np
import pandas as pd
from alpha_vantage.timeseries import TimeSeries

def indexToDate(index, frame):
    return str(frame.iloc[index].name)

class Portfolio:
    def __init__(self, capital):
        '''Initializer. Create a portfolio with the amount of specified capital.'''
        self.capital = capital
        self.stocks = {}
        self.shares = {}
        self.numTransactions = 0
        self.transactions = {}
        
    def add(self, symbol):
        '''Add a stock with the given symbol to your portfolio.'''
        stock = Stock(symbol)
        stock.gatherDaily()
        stock.gatherIntra()
        self.stocks[symbol] = stock
        self.shares[symbol] = 0
        
    def addTransaction(self, date, action, symbol, shares, amount):
        '''Add a record of the transaction to your portfolio.'''
        self.transactions[self.numTransactions] = {'date':date, 'action':action, 'symbol':symbol, 'shares':shares, 'dollars':amount}
        self.numTransactions += 1
    
    def buy(self, symbol, amount, index = 0, shares = 1, date = 0):
        '''Buy some stock!
        
        Inputs:
        --------
        symbol - ticker symbol of the company whose stock you want to buy
        amount - how much of the stock you want to buy; can be shares or dollars, determined by the value of shares
        index - either dataframe row or date/timestamp; the code will interpret the value as a row index unless date is set to 1
        shares - boolean to determine what the amount value is: 1 for shares, 0 for dollars
        date - boolean to determine what the index value is: 1 for row index, 0 for date/timestamp
        '''
        
        #add the stock to the portfolio if it doesn't exist
        if symbol not in self.shares.keys():
            self.add(symbol) 
            
        #reformat index, if necessary
        if not date:
            index = indexToDate(index, self.stocks[symbol].intra) 
        
        #get buying price
        price = self.stocks[symbol].buyPrice(index)
        
        #set variables appropriately if buying number of shares
        if shares: 
            numShares = amount
            dollars = amount*price            
            #if you can't buy that much, buy as much as you can
            if dollars > self.capital: 
                print('Oh no, you didn\'t have enough money to buy that many stocks. Buying what you can instead, broke boi.')
                numShares = self.capital/price
                dollars = self.capital
        
        #set variables appropriately if buying dollar amount
        else:            
            #spend the rest of your money if you don't have enough
            if amount > self.capital: 
                print('Oh no, you didn\'t have enough money to buy that many stocks. Buying what you can instead, broke boi.')
                numShares = self.capital/price
                dollars = self.capital
            numShares = amount/price
            dollars = amount
        
        #update portfolio variables and output the details of the transaction
        self.shares[symbol] += numShares
        self.capital -= dollars
        print('{:.2f} shares were purchased for ${:.2f}'.format(numShares, dollars))
        
        #log transaction
        self.addTransaction(index, 'buy', symbol, numShares, dollars)

    def sell(self, symbol, amount, index, shares = 1, date = 0):
        '''Sell some stock!
        
        Inputs:
        --------
        symbol - ticker symbol of the company whose stock you want to sell
        amount - how much of the stock you want to sell; can be shares or dollars, determined by the value of shares
        index - either dataframe row or date/timestamp; the code will interpret the value as a row index unless date is set to 1
        shares - boolean to determine what the amount value is: 1 for shares, 0 for dollars
        date - boolean to determine what the index value is: 1 for row index, 0 for date/timestamp
        '''
        
        #ridicule the user if they try to sell stock they don't own
        if (symbol not in self.shares.keys()) or (self.shares[symbol] == 0):
            print('You don\'t own any of that stock, dumbass')
            return
        
        #reformat index, if necessary
        if not date:
            index = indexToDate(index, self.stocks[symbol].intra)
            
        #get selling price
        price = self.stocks[symbol].sellPrice(index)
        
        #set variables appropriately if selling shares
        if shares:
            #sell all shares if amount entered is more than amount owned
            if amount > self.shares[symbol]:
                print('Oh no, you don\'t that many shares to sell. Selling them all.')
                numShares = self.shares[symbol]
            else:
                numShares = amount
            dollars = numShares*price
        
        #set variables appropriately if selling dollar amount
        else:
            #sell all shares if amount entered is more than shares are worth
            if amount > self.shares[symbol]*price:
                print('Cheesum crepes, you don\'t have that much worth of that stock. Selling all instead.')
                numShares = self.shares[symbol]
                dollars = numShares*price
            else: 
                numShares = amount/price
                dollars = amount
        
        #update portfolio variables and output the details of the transaction
        self.shares[symbol] -= numShares
        self.capital += dollars
        print('{:.2f} shares were sold for ${:.2f}'.format(numShares, dollars))
        
        #log transaction
        self.addTransaction(index, 'sell', symbol, numShares, dollars)
        
        

class Stock:
    def __init__(self, symbol):
        '''Initializer. Create Stock object for company with given symbol.'''
        self.symbol = symbol
        self.key = 'PTI4HP742CC950TQ'
        self.timeSeries = TimeSeries(self.key, output_format='pandas')
        
    def gatherDaily(self, outputsize = 'compact'):
        '''Gather daily data for stock.
        
        Inputs:
        --------
        outputsize - determines how much data is retrieved: "compact" gets the last 100 datapoints, "full" gets all available data'''  
        self.daily, self.daily_meta = self.timeSeries.get_daily(self.symbol, outputsize)
        
    def gatherIntra(self, interval = '30min', outputsize = 'compact'):
        '''Gather intradaily data for stock at a given interval.
        
        Inputs:
        --------
        interval - interval at which the data is returned: 1min, 5min, 15min, 30min, 60min
        outputsize - determines how much data is retrieved: "compact" gets the last 100 datapoints, "full" gets all available data''' 
        self.intra, self.intra_meta = self.timeSeries.get_intraday(self.symbol, interval, outputsize)
        
    def buyPrice(self, index):
        '''Return the buy price, determined by the open value for a given index.'''
        return self.intra['1. open'][index]
    
    def sellPrice(self, index):
        '''Return the sell price, determined by the open value for a given index.'''
        return self.intra['4. close'][index]
    
    def volume(self, index):
        '''Return the trade volume for a given index.'''
        return self.intra['5. volume'][index]
    
    def percentChange(self, index1, index2, date = 0, daily = 0, kind = 'buy'):
        '''Calculate the percent change of a variable. 
        
        (index1-index2)/index2*100
        
        Inputs:
        --------
        index1 - the first index, should be more recent than index2
        index2 - the second index, should be older than index1
        date - boolean to determine what the index value is: 1 for row index, 0 for date/timestamp
        daily - boolean to determine interval for percent change: 1 for daily change, 2 for intradaily change
        kind - the variable that you want to calculate the percent change of
        
        Returns:
        ---------
        change - the percent change of the specified variable
        '''
        
        #reformat indicies, if necessary
        if not date:
            if daily:
                index1 = indexToDate(index1, self.daily)
                index2 = indexToDate(index2, self.daily)
            else:
                index1 = indexToDate(index1, self.intra)
                index2 = indexToDate(index2, self.intra)
                
        #return percent change for supported variables
        if kind == 'sell': return (self.sellPrice(index1)-self.sellPrice(index2))/self.sellPrice(index2)*100
        if kind == 'buy': return (self.buyPrice(index1)-self.buyPrice(index2))/self.buyPrice(index2)*100
        if kind == 'volume': return (self.volume(index1)-self.volume(index2))/self.volume(index2)*100
        
        #let the user know if they entered a bad variable
        else:
            print('Kind not recognized')
            return
