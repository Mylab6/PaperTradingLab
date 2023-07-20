from AlgorithmImports import *
from trading_logic import TradingDecision
from s_and_p_first_half import stock_data as stock_data_1
from s_and_p_second_half import stock_data as stock_data_2
from stocks import stock_data as magic_100
from stocks import additional_stock_data as additional_stock_data

use_magic_100 = True
use_extended_magic = True
sell_first = True
stock_data = stock_data_1 + stock_data_2
get_diverse_stocks = False

if(use_magic_100):
    stock_data = magic_100
if(use_extended_magic):
    stock_data = stock_data + additional_stock_data

class StockData:
    def __init__(self, symbol, description):
        self.symbol = symbol
        self.description = description

class QuantConnectBacktester(QCAlgorithm):
    def Initialize(self):
        self.SetStartDate(2022, 7, 17)  # Set Start Date
        self.SetCash(100000)  # Set Strategy Cash
        self.initial_capital = 100000  # Store the initial capital
        self.SetBenchmark("SPY")

        self.selected_stocks = []  # Define selected_stocks before calling LoadStockData
        self.trading_decision = TradingDecision()

        # Load stock_data from your data source
        self.LoadStockData()

        self.SetBrokerageModel(BrokerageName.InteractiveBrokersBrokerage, AccountType.Margin)  # Enable margin trading

    def OnData(self, data):
        if self.trading_decision.should_rebalance(self.Time):
            sorted_stocks, allocation_per_stock = self.trading_decision.get_sorted_stocks(self.selected_stocks)
            if get_diverse_stocks:
                sorted_stocks, allocation_per_stock = self.trading_decision.get_diverse_stocks(self.selected_stocks)
            
            if sell_first:
                self.sell_excess_holdings(sorted_stocks, allocation_per_stock)
            
            self.buy_new_stocks(sorted_stocks, allocation_per_stock)

    def sell_excess_holdings(self, sorted_stocks, allocation_per_stock):
        for stock in self.Portfolio.Values:
            stock_price = self.Securities[stock.Symbol].Price
            target_value = allocation_per_stock * self.Portfolio.TotalPortfolioValue
            if stock_price == 0 :
                print('Could not fetch price for ' , stock.Symbol)
                continue
            desired_quantity = int(target_value / stock_price)

            current_quantity = self.Portfolio[stock.Symbol].Quantity

            if current_quantity > desired_quantity:
                # Sell some of the holdings
                self.Order(stock.Symbol, desired_quantity - current_quantity)

    def buy_new_stocks(self, sorted_stocks, allocation_per_stock):
        for stock in sorted_stocks:
            if self.Portfolio.Cash > 0.15 * self.initial_capital:
                stock_price = self.Securities[stock.Symbol].Price
                target_value = allocation_per_stock * self.Portfolio.TotalPortfolioValue
                desired_quantity = int(target_value / stock_price)
                current_quantity = self.Portfolio[stock.Symbol].Quantity

                if current_quantity < desired_quantity:
                    # Buy more of the stock, respecting the cash reserve
                    cash_required = (desired_quantity - current_quantity) * stock_price
                    if cash_required <= (self.Portfolio.Cash - 0.15 * self.initial_capital):
                        self.Order(stock.Symbol, desired_quantity - current_quantity)

    def LoadStockData(self):
        for stock in stock_data:
            symbol = stock['Symbol']
            description = stock['Security']
            equity = self.AddEquity(symbol, Resolution.Minute)
            equity.Tag = StockData(symbol, description)
            equity.Sector = stock['Sector']
            self.selected_stocks.append(equity)
