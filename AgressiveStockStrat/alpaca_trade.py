import alpaca_trade_api as tradeapi
import pandas as pd
from datetime import datetime, timedelta
import pytz
from stocks import stock_data
from trading_logic import TradingDecision
api_key = 'REDACTED'
api_secret = 'REDACTED'

class StockData:
    def __init__(self, symbol, description):
        self.symbol = symbol
        self.description = description

class AlpacaTradingBot:
    def __init__(self):
        self.alpaca = tradeapi.REST(api_key, api_key, base_url='https://paper-api.alpaca.markets') 
        self.selected_stocks = []
        self.trading_decision = TradingDecision()

        self.load_stock_data()

    def on_data(self):
        
            sorted_stocks, allocation_per_stock = self.trading_decision.get_sorted_stocks(self.selected_stocks)

            for stock in sorted_stocks:
                self.alpaca.submit_order(
                    symbol=stock.symbol,
                    qty=allocation_per_stock,
                    side='buy',
                    type='market',
                    time_in_force='gtc'
                )

    def load_stock_data(self):
        for stock in stock_data:
            symbol = stock['symbol']
            description = stock['description']
            last_trade = self.alpaca.get_last_trade(symbol)
            equity = StockData(symbol, description)
            equity.last_sale_price = last_trade.price
            self.selected_stocks.append(equity)

if __name__ == "__main__":
    bot = AlpacaTradingBot()
    bot.on_data()
