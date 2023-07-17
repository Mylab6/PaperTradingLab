import alpaca_trade_api as tradeapi
import pandas as pd
from datetime import datetime, timedelta
import pytz
from stocks import stock_data
from trading_logic import TradingDecision
import math
api_key = 'REDACTED'
api_secret = 'REDACTED'

class StockData:
    def __init__(self, symbol, description):
        self.symbol = symbol
        self.description = description

class AlpacaTradingBot:
    def __init__(self):
        self.alpaca = tradeapi.REST(api_key, api_secret, base_url='https://paper-api.alpaca.markets') 
        self.selected_stocks = []
        self.trading_decision = TradingDecision()
        
        self.account = self.alpaca.get_account()
        self.cash_available = float(self.account.cash) # amount of cash available for trading

        self.load_stock_data()

    def on_data(self):
        sorted_stocks, allocation_per_stock = self.trading_decision.get_sorted_stocks(self.selected_stocks)
        print("Sorted Stocks: " + str(sorted_stocks))
        print("Allocation per stock: " + str(allocation_per_stock))
        
        # calculate cash per stock
        cash_per_stock = self.cash_available * allocation_per_stock

        for stock in sorted_stocks:
            if cash_per_stock < stock.last_sale_price:
                print(stock.symbol + " is not worth buying")
                print("Last Price ", stock.last_sale_price) 
                continue
            else:
                quantity = int(cash_per_stock / stock.last_sale_price) # calculate quantity for each stock
                
                self.alpaca.submit_order(
                    symbol=stock.symbol,
                    qty=quantity,
                    side='buy',
                    type='market',
                    time_in_force='gtc'
                )
                print("Bought " + str(quantity) + " shares of " + stock.symbol)
    def load_stock_data(self):
        for stock in stock_data:
            # add a try catch here
            try:
                symbol = stock['symbol']
                description = stock['description']
                last_trade = self.alpaca.get_latest_trade(symbol)
                equity = StockData(symbol, description)
                equity.last_sale_price = last_trade.price
                self.selected_stocks.append(equity)
            except:
                print("Error loading stock data for " + symbol)



if __name__ == "__main__":
    bot = AlpacaTradingBot()
    bot.on_data()
