import numpy as np
import pandas as pd
from alpha_vantage.timeseries import TimeSeries

def indexToDate(index, frame, isDaily = 0):
    '''Helper function to translate a row index to the corresponding date/timestamp
    
    Inputs:
    --------
    index - the row index
    frame - the dataframe with the data'''

    if isDaily: return str(frame.iloc[index].name)[0:10]
    else: return str(frame.iloc[index].name)

class Portfolio:
    '''Create a portfolio with the amount of specified capital.'''
    def __init__(self, capital):
        '''Initializer. 
        
        Inputs:
        --------
        capital - how much money you want to start out with'''
        self.capital = capital
        self.stocks = {}
        self.shares = {}
        self.numTransactions = 0
        self.ledger = {}
        
    def add(self, symbol, isDaily = 1):
        '''Add a stock with the given symbol to your portfolio.'''
        stock = Stock(symbol)
        if isDaily: stock.gatherDaily()
        else: stock.gatherIntra()
        self.stocks[symbol] = stock
        self.shares[symbol] = 0
        
    def addTransaction(self, date, action, symbol, shares, dollars):
        '''Add a record of the transaction to your portfolio.'''
        self.ledger[self.numTransactions] = {'date':date, 'action':action, 'symbol':symbol, '\u0394shares':shares, '\u0394dollars':dollars, 'capital':self.capital}
        self.numTransactions += 1
    
    def getLedger(self):
        return pd.DataFrame.from_dict(self.ledger, orient='index').round(2)
    
    def buy(self, symbol, amount, index = 0, isShares = 1, isDate = 0, isDaily = 0):
        '''Buy some stock! Specify the index/date and share/dollar amount.
        
        Inputs:
        --------
        symbol - ticker symbol of the company whose stock you want to buy
        amount - how much of the stock you want to buy; can be shares or dollars, determined by the value of isShares
        index - either dataframe row or date/timestamp; the code will interpret the value as a row index unless date is set to 1
        isShares - boolean to determine what the amount value is: 1 for shares, 0 for dollars
        isDate - boolean to determine what the index value is: 1 for row index, 0 for date/timestamp
        '''
        
        #check is there is available capital
        if self.capital <= 0:
            print("You have no money left...")
            return
        
        #add the stock to the portfolio if it doesn't exist
        if symbol not in self.shares.keys():
            self.add(symbol, isDaily) 
        
        isDaily = self.stocks[symbol].isDaily
        
        #reformat index, if necessary
        if not isDate:
            if isDaily: index = indexToDate(index, self.stocks[symbol].daily, isDaily) 
            else: index = indexToDate(index, self.stocks[symbol].intra, isDaily) 
        
        #get buying price
        price = self.stocks[symbol].buyPrice(index, 1)
        
        #set variables appropriately if buying number of shares
        if isShares: 
            numShares = amount
            dollars = amount*price
            #if you can't buy that much, buy as much as you can
            if dollars > self.capital: 
                print('Oh no, you don\'t have enough money to buy that many stocks. Buying what you can instead, broke boi.')
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
        numShares = round(numShares,2)
        dollars = round(dollars,2)
        
        self.shares[symbol] += numShares
        self.capital -= dollars
        print('{} shares of {} were purchased for ${}'.format(numShares, symbol, dollars))
        
        #clean up variables
        if self.capital != 0 and 1/self.capital > 1000:
            self.capital = 0
        
        #log transaction
        self.addTransaction(index, 'buy', symbol, numShares, -dollars)

    def sell(self, symbol, amount = 0, index = -2, isShares = 1, isDate = 0, isDaily = 0):
        '''Sell some stock! Specify the index/date and share/dollar amount.
        
        Inputs:
        --------
        symbol - ticker symbol of the company whose stock you want to sell
        index - either dataframe row or date/timestamp; the code will interpret the value as a row index unless date is set to 1; will default to last row in dataset
        amount - how much of the stock you want to sell; can be shares or dollars, determined by the value of shares; if left blank, all shares are sold
        isShares - boolean to determine what the amount value is: 1 for shares, 0 for dollars
        isDate - boolean to determine what the index value is: 1 for row index, 0 for date/timestamp
        '''
        
        #ridicule the user if they try to sell stock they don't own
        if (symbol not in self.shares.keys()) or (self.shares[symbol] == 0):
            print('You don\'t own any of that stock, dumbass')
            return
        
        isDaily = self.stocks[symbol].isDaily
        
        #reformat index, if necessary
        if not isDate:
            if isDaily: index = indexToDate(index, self.stocks[symbol].daily, isDaily) 
            else: index = indexToDate(index, self.stocks[symbol].intra, isDaily) 
            
        #get selling price
        price = self.stocks[symbol].sellPrice(index, 1)
        
        #set variables appropriately if selling shares
        if isShares:
            #sell all shares if no amount is entered or if the value is more than amount owned
            if amount == 0:
                print('No value entered, all shares will be sold')
                numShares = self.shares[symbol]
                dollars = numShares*price  
            elif amount > self.shares[symbol]:
                print('Oh no, you don\'t have that many shares to sell. Selling them all.')
                numShares = self.shares[symbol]
            else:
                numShares = amount
            dollars = numShares*price
        
        #set variables appropriately if selling dollar amount
        else:
            #sell all shares if no amount is entered or the value is more than shares are worth
            if amount == 0:
                print('No value entered, all shares will be sold')
                numShares = self.shares[symbol]
                dollars = numShares*price                
            elif amount > self.shares[symbol]*price:
                print('Cheesum crepes, you don\'t have that much worth of that stock. Selling all instead.')
                numShares = self.shares[symbol]
                dollars = numShares*price
                
            else: 
                numShares = amount/price
                dollars = amount
        
        #update portfolio variables and output the details of the transaction
        numShares = round(numShares,2)
        dollars = round(dollars,2)
        
        self.shares[symbol] -= numShares
        self.capital += dollars
        print('{} shares of {} were sold for ${}'.format(numShares, symbol, dollars))
        
        #log transaction
        self.addTransaction(index, 'sell', symbol, -numShares, dollars)
        
        

class Stock:
    '''Create Stock object for company with given symbol.'''
    def __init__(self, symbol):
        '''Initializer. 
        
        Inputs:
        --------
        symbol - the ticker symbol for the company'''
        self.symbol = symbol
        self.key = 'PTI4HP742CC950TQ'
        self.timeSeries = TimeSeries(self.key, output_format='pandas')
        self.isDaily = 0
        
    def gatherDaily(self, outputsize = 'compact'):
        '''Gather daily data for stock.
        
        Inputs:
        --------
        outputsize - determines how much data is retrieved: "compact" gets the last 100 datapoints, "full" gets all available data'''  
        self.daily, self.daily_meta = self.timeSeries.get_daily(self.symbol, outputsize)
        self.isDaily = 1
        
    def gatherIntra(self, interval = '30min', outputsize = 'compact'):
        '''Gather intradaily data for stock at a given interval.
        
        Inputs:
        --------
        interval - interval at which the data is returned: 1min, 5min, 15min, 30min, 60min
        outputsize - determines how much data is retrieved: "compact" gets the last 100 datapoints, "full" gets all available data''' 
        self.intra, self.intra_meta = self.timeSeries.get_intraday(self.symbol, interval, outputsize)
        self.isDaily = 0
        
    def buyPrice(self, index, isDate = 1):
        '''Return the buy price, determined by the next open value for a given index.
        
        Inputs:
        --------
        index - either row index or date/timestamp
        isDate - 1 if index is date, 0 if row index'''
        
        #switch date to row index to increment
        if isDate:
            if self.isDaily: index = np.where(self.daily.index == index)[0].tolist()[0]
            else: index = np.where(self.intra.index == index)[0].tolist()[0]
            
        #get date of next index
        if self.isDaily: index = indexToDate(index+1, self.daily, self.isDaily)
        else: index = indexToDate(index+1, self.intra, self.isDaily)
        
        #return open value for next index
        if self.isDaily: return self.daily['1. open'][index]
        else: return self.intra['1. open'][index]
    
    def sellPrice(self, index, isDate = 1):
        '''Return the sell price, determined by the next open value for a given index.  
        
        Inputs:
        --------
        index - either row index or date/timestamp
        isDate - 1 if index is date, 0 if row index'''
        
        #switch date to row index to increment
        if isDate:
            if self.isDaily: index = np.where(self.daily.index == index)[0].tolist()[0]
            else: index = np.where(self.intra.index == index)[0].tolist()[0]
            
        #get date of next index
        if self.isDaily: index = indexToDate(index+1, self.daily, self.isDaily)
        else: index = indexToDate(index+1, self.intra, self.isDaily)
        
        #return open value for next index
        if self.isDaily: return self.daily['1. open'][index]
        else: return self.intra['1. open'][index]
    
    def volume(self, index, isDate = 1):
        '''Return the trade volume for a given index.
                
        Inputs:
        --------
        index - either row index or date/timestamp
        isDate - 1 if index is date, 0 if row index'''
        
        #switch row index to date
        if not isDate:
            if self.isDaily: index = indexToDate(index, self.daily, self.isDaily)
            else: indexToDate(index, self.intra, self.isDaily)
            
        #reutrn volume value for given index
        if self.isDaily: return self.daily['5. volume'][index]
        else: return self.intra['5. volume'][index]
    
    def percentChange(self, index1, index2, kind = 'buy', isDate = 0):
        '''Calculate the percent change of a variable. 
        
        (index1-index2)/index2*100
        
        Inputs:
        --------
        index1 - the first index, should be more recent than index2
        index2 - the second index, should be older than index1
        kind - the variable that you want to calculate the percent change of
        isDate - boolean to determine what the index value is: 1 for date/timestamp, 0 for row index
        isDaily - boolean to determine interval for percent change: 1 for daily change, 2 for intradaily change
        
        Returns:
        ---------
        change - the percent change of the specified variable
        '''
        
        #reformat indicies, if necessary
        if not isDate:
            if self.isDaily:
                index1 = indexToDate(index1, self.daily, self.isDaily)
                index2 = indexToDate(index2, self.daily, self.isDaily)
            else:
                index1 = indexToDate(index1, self.intra, self.isDaily)
                index2 = indexToDate(index2, self.intra, self.isDaily)
                
        #return percent change for supported variables
        if kind == 'sell': return (self.sellPrice(index1)-self.sellPrice(index2))/self.sellPrice(index2)*100
        if kind == 'buy': return (self.buyPrice(index1)-self.buyPrice(index2))/self.buyPrice(index2)*100
        if kind == 'volume': return (self.volume(index1)-self.volume(index2))/self.volume(index2)*100
        
        #let the user know if they entered a bad variable
        else:
            print('Kind not recognized')
            return
