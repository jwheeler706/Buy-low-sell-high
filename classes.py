import numpy as np
import pandas as pd
from alpha_vantage.timeseries import TimeSeries

def indexToDate(index, frame):
    return str(frame.iloc[index].name)

class Portfolio:
    def __init__(self, capital):
        self.capital = capital
        self.stocks = {}
        self.shares = {}
        self.numTransactions = 0
        self.transactions = {}
        
    def add(self, symbol):
        stock = Stock(symbol)
        stock.gatherDaily()
        stock.gatherIntra()
        self.stocks[symbol] = stock
        self.shares[symbol] = 0
        
    def addTransaction(self, date, action, symbol, shares, amount):
        self.transactions[self.numTransactions] = {'date':date, 'action':action, 'symbol':symbol, 'shares':shares, 'dollars':amount}
        self.numTransactions += 1
    
    def buy(self, symbol, amount, index = 0, shares = 1, date = 0):
        if symbol not in self.shares.keys():
            self.add(symbol)        
        if not date:
            index = indexToDate(index, self.stocks[symbol].intra)
        price = self.stocks[symbol].buyPrice(index)
        if shares:
            numShares = amount
            dollars = amount*price
            if dollars > self.capital:
                print('Oh no, you didn\'t have enough money to buy that many stocks. Buying what you can instead, broke boi.')
                numShares = self.capital/price
                dollars = self.capital
        else:
            if amount > self.capital:
                print('Oh no, you didn\'t have enough money to buy that many stocks. Buying what you can instead, broke boi.')
                numShares = self.capital/price
                dollars = self.capital
            numShares = amount/price
            dollars = amount
        self.shares[symbol] += numShares
        self.capital -= dollars
        print('{:.2f} shares were purchased for ${:.2f}'.format(numShares, dollars))
        self.addTransaction(index, 'buy', symbol, numShares, dollars)

    def sell(self, symbol, amount, index, shares = 1, date = 0):
        if symbol not in self.shares.keys():
            print('You don\'t own any of that stock, dumbass')
            return
        if not date:
            index = indexToDate(index, self.stocks[symbol].intra)
        price = self.stocks[symbol].sellPrice(index)
        if shares:
            if amount > self.shares[symbol]:
                print('Oh no, you don\'t that many shares to sell. Selling them all.')
                numShares = self.shares[symbol]
            else:
                numShares = amount
            dollars = numShares*price
        else:
            if amount > self.shares[symbol]*price:
                print('Cheesum crepes, you don\'t have that much worth of that stock. Selling all instead.')
                numShares = self.shares[symbol]
                dollars = numShares*price
            else: 
                numShares = amount/price
                dollars = amount
        self.shares[symbol] -= numShares
        self.capital += dollars
        print('{:.2f} shares were sold for ${:.2f}'.format(numShares, dollars))
        self.addTransaction(index, 'sell', symbol, numShares, dollars)
        
        

class Stock:
    def __init__(self, symbol):
        self.symbol = symbol
        self.key = 'PTI4HP742CC950TQ'
        self.timeSeries = TimeSeries(self.key, output_format='pandas')
        
    def gatherDaily(self, outputsize = 'compact'):
        self.daily, self.daily_meta = self.timeSeries.get_daily(self.symbol, outputsize)
        
    def gatherIntra(self, interval = '30min', outputsize = 'compact'):
        self.intra, self.intra_meta = self.timeSeries.get_intraday(self.symbol, interval, outputsize)
        
    def buyPrice(self, index):
        return self.intra['1. open'][index]
    
    def sellPrice(self, index):
        return self.intra['4. close'][index]
    
    def volume(self, index):
        return self.intra['5. volume'][index]
    
    def percentChange(self, index, index2, date = 0, daily = 0, kind = 'buy'):
        if not date:
            if daily:
                index = indexToDate(index, self.daily)
                index2 = indexToDate(index2, self.daily)
            else:
                index = indexToDate(index, self.intra)
                index2 = indexToDate(index2, self.intra)
        if kind == 'sell': return (self.sellPrice(index)-self.sellPrice(index2))/self.sellPrice(index2)*100
        if kind == 'buy': return (self.buyPrice(index)-self.buyPrice(index2))/self.buyPrice(index2)*100
        if kind == 'volume': return (self.volume(index)-self.volume(index2))/self.volume(index2)*100
        else:
            print('Kind not recognized')
            return
