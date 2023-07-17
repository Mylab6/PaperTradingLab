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
        self.update_cash_available()

        self.load_stock_data()

    def update_cash_available(self):
        self.cash_available = float(self.account.cash)

    def on_data(self):
        sorted_stocks, allocation_per_stock = self.trading_decision.get_sorted_stocks(self.selected_stocks)
    
    # Calculate the cash allocated for each stock
        cash_per_stock = self.cash_available * allocation_per_stock

        exceptions = []
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

        # Do nothing if target quantity equals current quantity
            if target_quantity == current_quantity:
                continue

            side = 'buy' if target_quantity > current_quantity else 'sell'
            qty = abs(target_quantity - current_quantity)

        # Check if we have enough money to buy
            if side == 'buy' and qty * stock.last_sale_price > self.cash_available:
                continue

            try:
                self.alpaca.submit_order(
                symbol=stock.symbol,
                qty=qty,
                side=side,
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
                symbol = stock['symbol']
                description = stock['description']
                last_trade = self.alpaca.get_latest_trade(symbol)
                equity = StockData(symbol, description)
                equity.last_sale_price = last_trade.price
                self.selected_stocks.append(equity)
            except Exception as e:
                print(f"Error loading stock data for {symbol}: {str(e)}")

if __name__ == "__main__":
    bot = AlpacaTradingBot()
    bot.on_data()
