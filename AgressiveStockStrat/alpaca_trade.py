import alpaca_trade_api as tradeapi
import pandas as pd
from datetime import datetime, timedelta
import pytz
from trading_logic import TradingDecision
import math
from alpaca_trade_api.rest import APIError  # Import the exception

from s_and_p_first_half import stock_data as stock_data_1
from s_and_p_second_half import stock_data as stock_data_2

# combine the two lists of stock data
from stocks import stock_data as magic_100
use_magic_100 = True
stock_data = stock_data_1 + stock_data_2
if(use_magic_100):
    stock_data = magic_100
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
        self.update_cash_available()

        self.load_stock_data()

    def update_cash_available(self):
        self.cash_available = float(self.account.cash)


    def on_data(self):
        sorted_stocks, allocation_per_stock = self.trading_decision.get_sorted_stocks(self.selected_stocks)
        cash_per_stock = self.cash_available * allocation_per_stock

        exceptions = []
        # Handle selling transactions
        for stock in sorted_stocks:
            target_quantity = int(cash_per_stock / stock.last_sale_price)
            position = None
            try:
                position = self.alpaca.get_position(stock.symbol)
            except:
                pass
            current_quantity = position.qty if position else 0
            if target_quantity >= current_quantity:
                continue
            qty = current_quantity - target_quantity
            if qty > 0:
                try:
                    self.alpaca.submit_order(
                        symbol=stock.symbol,
                        qty=qty,
                        side='sell',
                        type='market',
                        time_in_force='gtc'
                    )
                    self.update_cash_available()
                except APIError as e:
                    if 'insufficient qty' in str(e):
                        exceptions.append(f"No more {stock.symbol} to sell")
                    else:
                        exceptions.append(str(e))
        
        # Update cash after selling
        self.update_cash_available()
        
        # Handle buying transactions
        for stock in sorted_stocks:
            target_quantity = int(cash_per_stock / stock.last_sale_price)
            position = None
            try:
                position = self.alpaca.get_position(stock.symbol)
            except:
                pass
            current_quantity = position.qty if position else 0
            if target_quantity <= current_quantity:
                continue
            qty = target_quantity - current_quantity
            if qty * stock.last_sale_price <= self.cash_available:
                try:
                    self.alpaca.submit_order(
                        symbol=stock.symbol,
                        qty=qty,
                        side='buy',
                        type='market',
                        time_in_force='gtc'
                    )
                    self.update_cash_available()
                except APIError as e:
                    exceptions.append(str(e))
        
        if exceptions:
            raise Exception('; '.join(exceptions))

    def load_stock_data(self):
        for stock in stock_data:
            try:
                symbol = stock['Symbol']
                description = stock['Security']
                last_trade = self.alpaca.get_latest_trade(symbol)
                equity = StockData(symbol, description)
                equity.last_sale_price = last_trade.price
                self.selected_stocks.append(equity)
            except Exception as e:
                print(f"Error loading stock data for {symbol}: {str(e)}")

if __name__ == "__main__":
    bot = AlpacaTradingBot()
    bot.on_data()
