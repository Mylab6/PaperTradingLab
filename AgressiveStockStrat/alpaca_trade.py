import alpaca_trade_api as tradeapi
import os
import time
from trading_logic import TradingDecision
from alpaca_trade_api.rest import APIError

from s_and_p_first_half import stock_data as stock_data_1
from s_and_p_second_half import stock_data as stock_data_2
from stocks import stock_data as magic_100
from stocks import additional_stock_data as additional_stock_data
from GetSenateStocks import  GetSenateStocks
use_magic_100 = True
use_extended_magic = True
get_diverse_stocks = False
get_senate_stocks = True
only_positive_senate_ratio = True
stock_data = stock_data_1 + stock_data_2

if(use_magic_100):
    stock_data = magic_100
if(use_extended_magic):
    stock_data = stock_data + additional_stock_data
if(get_senate_stocks):
    GetSenateStocks = GetSenateStocks()
    stock_data = GetSenateStocks.get_most_common_stocks(100)
    if only_positive_senate_ratio:
        stock_data = [stock for stock in stock_data if stock['Buy to Sale Ratio'] > 1]
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
        self.load_stock_data()

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

    def sell_excess_holdings(self, sorted_stocks, allocation_per_stock):
        current_positions = self.alpaca.list_positions()
        for position in current_positions:
            symbol = position.symbol
            current_quantity = int(position.qty)
            target_quantity = 0
            for stock in sorted_stocks:
                if stock.symbol == symbol:
                    cash_per_stock = float(self.account.cash) * allocation_per_stock
                    target_quantity = int(cash_per_stock / stock.last_sale_price)
                    break
            if current_quantity > target_quantity:
                qty = current_quantity - target_quantity
                self.place_order(symbol, qty, 'sell')
                self.account = self.alpaca.get_account()  # Update account information after each sell

    def place_order(self, symbol, qty, side):
        try:
            order = self.alpaca.submit_order(
                symbol=symbol,
                qty=qty,
                side=side,
                type='market',
                time_in_force='gtc'
            )
            print(f"Order {order.id} submitted: {qty} shares of {symbol} to {side}")
            time.sleep(3)  # Wait for 3 seconds to let the order execute
        except APIError as e:
            print(f"Error placing order for {symbol}: {str(e)}")

    def on_data(self):
        self.account = self.alpaca.get_account()
        portfolio_value = float(self.account.portfolio_value)
        reserve_cash = portfolio_value * 0.15
        cash_available = float(self.account.cash)
        sorted_stocks, allocation_per_stock = self.trading_decision.get_sorted_stocks(self.selected_stocks)
        if get_diverse_stocks:
            sorted_stocks, allocation_per_stock = self.trading_decision.get_diverse_stocks(self.selected_stocks)
        
        
        self.sell_excess_holdings(sorted_stocks, allocation_per_stock)
        cash_available = float(self.account.cash)


        for stock in sorted_stocks:
            cash_per_stock = cash_available * allocation_per_stock
            target_quantity = int(cash_per_stock / stock.last_sale_price)
            
            position = None
            try:
                position = self.alpaca.get_position(stock.symbol)
            except:
                pass
            current_quantity = int(position.qty if position else 0)

            # Check if the current quantity is negative, if it is, set target quantity to 0
            if current_quantity < 0:
                target_quantity = 0
            
            if target_quantity > current_quantity:
                qty = target_quantity - current_quantity
                cost_of_trade = qty * stock.last_sale_price
                if cash_available - cost_of_trade >= reserve_cash:  # Check reserve cash requirement
                    cash_available -= cost_of_trade  # Update available cash
                    self.place_order(stock.symbol, qty, 'buy')

if __name__ == "__main__":
    bot = AlpacaTradingBot()
    bot.on_data()
