import alpaca_trade_api as tradeapi
import pandas as pd
from datetime import datetime, timedelta
import pytz
from trading_logic import TradingDecision
import math
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
    
        # Calculate the cash allocated for each stock
        cash_per_stock = self.cash_available * allocation_per_stock

        exceptions = []
        # First, handle selling
        for stock in sorted_stocks:
            # Calculate quantity for each stock
            target_quantity = int(cash_per_stock / stock.last_sale_price) 
            # Get current quantity of this stock
            position = None
            try:
                position = self.alpaca.get_position(stock.symbol)
            except:
                pass
            current_quantity = position.qty if position else 0

            # If current quantity is less or equal to target, do nothing
            if current_quantity <= target_quantity:
                continue

            qty = current_quantity - target_quantity

            try:
                self.alpaca.submit_order(
                    symbol=stock.symbol,
                    qty=qty,
                    side='sell',
                    type='market',
                    time_in_force='gtc'
                )
                # Update cash available after each successful trade
                self.update_cash_available()
            except Exception as e:
                exceptions.append(str(e))

        # Then, handle buying
        for stock in sorted_stocks:
            target_quantity = int(cash_per_stock / stock.last_sale_price) 
            position = None
            try:
                position = self.alpaca.get_position(stock.symbol)
            except:
                pass
            current_quantity = position.qty if position else 0

            # If current quantity is greater or equal to target, do nothing
            if current_quantity >= target_quantity:
                continue

            qty = target_quantity - current_quantity

            # Check if we have enough money to buy
            if qty * stock.last_sale_price > self.cash_available:
                continue

            try:
                self.alpaca.submit_order(
                    symbol=stock.symbol,
                    qty=qty,
                    side='buy',
                    type='market',
                    time_in_force='gtc'
                )
                # Update cash available after each successful trade
                self.update_cash_available()
            except Exception as e:
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
