from AlgorithmImports import *
from trading_logic import TradingDecision
from s_and_p_first_half import stock_data as stock_data_1
from s_and_p_second_half import stock_data as stock_data_2
from stocks import stock_data as magic_100
from stocks import additional_stock_data as additional_stock_data

use_magic_100 = True
use_extended_magic = True
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
            
            for stock in sorted_stocks:
                if self.Portfolio.Cash > 0.15 * self.initial_capital:
                    target_allocation = allocation_per_stock
                    stock_price = self.Securities[stock.Symbol].Price
                    target_value = target_allocation * self.Portfolio.TotalPortfolioValue
                    quantity = int(target_value / stock_price)
                    cash_required = quantity * stock_price
                    
                    if cash_required > (self.Portfolio.Cash - 0.15 * self.initial_capital):
                        quantity = int((self.Portfolio.Cash - 0.15 * self.initial_capital) / stock_price)
                    self.Order(stock.Symbol, quantity)
                else:
                    break

    def LoadStockData(self):
        for stock in stock_data:
            symbol = stock['Symbol']
            description = stock['Security']
            equity = self.AddEquity(symbol, Resolution.Minute)
            equity.Tag = StockData(symbol, description)
            equity.Sector = stock['Sector']
            self.selected_stocks.append(equity)
