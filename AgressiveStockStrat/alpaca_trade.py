import alpaca_trade_api as tradeapi
import os
import pandas as pd
from datetime import datetime, timedelta
import pytz
from trading_logic import TradingDecision
import math
from alpaca_trade_api.rest import APIError

from s_and_p_first_half import stock_data as stock_data_1
from s_and_p_second_half import stock_data as stock_data_2
from stocks import stock_data as magic_100
from stocks import additional_stock_data as additional_stock_data

use_magic_100 = True
use_extended_magic = True
get_diverse_stocks = False
stock_data = stock_data_1 + stock_data_2
if(use_magic_100):
    stock_data = magic_100
if(use_extended_magic):
    stock_data = stock_data + additional_stock_data
api_key = os.getenv('ALPACA_API_KEY')
api_secret = os.getenv('ALPACA_API_SECRET')
api_url = os.getenv('ALPACA_API_URL', 'https://paper-api.alpaca.markets')

class StockData:
    def __init__(self, symbol, description):
        self.symbol = symbol
        self.description = description

class AlpacaTradingBot:
    def __init__(self):
        self.alpaca = tradeapi.REST(api_key, api_secret, base_url=api_url) 
        self.selected_stocks = []
        self.trading_decision = TradingDecision()

        self.account = self.alpaca.get_account()
        self.initial_capital = float(self.account.portfolio_value)  # Save the initial portfolio value
        print( 'Initial portfolio value: $' + str(self.initial_capital))
        self.load_stock_data()

    def on_data(self):
        self.account = self.alpaca.get_account() # Refresh account data
        sorted_stocks, allocation_per_stock = self.trading_decision.get_sorted_stocks(self.selected_stocks)
        if get_diverse_stocks:
            sorted_stocks, allocation_per_stock = self.trading_decision.get_diverse_stocks(self.selected_stocks)
        
        cash_per_stock = float(self.account.cash) * allocation_per_stock

        exceptions = []
        
        for stock in sorted_stocks:
            target_quantity = int(cash_per_stock / stock.last_sale_price)
            position = None
            try:
                position = self.alpaca.get_position(stock.symbol)
            except:
                pass
            current_quantity = position.qty if position else 0
            current_quantity = int(current_quantity)
            if target_quantity != current_quantity:
                qty = abs(target_quantity - current_quantity)
                side = 'buy' if target_quantity > current_quantity else 'sell'

                # If the purchase would reduce cash to less than 15% of current portfolio value, don't proceed
                if side == 'buy' and float(self.account.cash) - qty * stock.last_sale_price < 0.15 * float(self.account.portfolio_value):
                    print('Skipping investment to avoid reducing cash to less than 15% of portfolio value')
                    print('Current portfolio value: $' + str(self.account.portfolio_value))
                    print('Current cash: $' + str(self.account.cash))
                    continue

                try:
                    order = self.alpaca.submit_order(
                        symbol=stock.symbol,
                        qty=qty,
                        side=side,
                        type='market',
                        time_in_force='gtc'
                    )
                    print(f"Order {order.id} submitted: {qty} shares of {stock.symbol} to {side}")
                except APIError as e:
                    if 'insufficient qty' in str(e):
                        exceptions.append(f"No more {stock.symbol} to sell")
                    else:
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
                equity.Sector = stock['Sector']
                equity.last_sale_price = last_trade.price
                self.selected_stocks.append(equity)
            except Exception as e:
                print(f"Error loading stock data for {symbol}: {str(e)}")

if __name__ == "__main__":
    bot = AlpacaTradingBot()
    bot.on_data()
