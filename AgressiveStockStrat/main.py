from AlgorithmImports import *
from trading_logic import TradingDecision
from s_and_p_first_half import stock_data as stock_data_1
from s_and_p_second_half import stock_data as stock_data_2
from stocks import stock_data as magic_100

use_magic_100 = True
stock_data = stock_data_1 + stock_data_2
if(use_magic_100):
    stock_data = magic_100

class StockData:
    def __init__(self, symbol, description):
        self.symbol = symbol
        self.description = description

class QuantConnectBacktester(QCAlgorithm):
    def Initialize(self):
        self.SetStartDate(2023, 5, 15)  # Set Start Date
        self.SetCash(100000)  # Set Strategy Cash
        self.SetBenchmark("SPY")

        self.selected_stocks = []  # Define selected_stocks before calling LoadStockData
        self.trading_decision = TradingDecision()

        # Load stock_data from your data source
        self.LoadStockData()

        self.SetBrokerageModel(BrokerageName.InteractiveBrokersBrokerage, AccountType.Margin)  # Enable margin trading

    def OnData(self, data):
        if self.trading_decision.should_rebalance(self.Time):
            sorted_stocks, allocation_per_stock = self.trading_decision.get_sorted_stocks(self.selected_stocks)

            # First sell
            for stock in sorted_stocks:
                if self.Portfolio[stock.Symbol].IsLong and self.Portfolio[stock.Symbol].Quantity > allocation_per_stock:
                    self.SetHoldings(stock.Symbol, 0)

            # Then buy
            for stock in sorted_stocks:
                if self.Portfolio[stock.Symbol].Quantity < allocation_per_stock and self.Portfolio.Cash > 0:
                    self.SetHoldings(stock.Symbol, allocation_per_stock)

    def LoadStockData(self):
        for stock in stock_data:
            symbol = stock['Symbol']
            description = stock['Security']
            equity = self.AddEquity(symbol, Resolution.Minute)
            equity.Tag = StockData(symbol, description)
            self.selected_stocks.append(equity)
