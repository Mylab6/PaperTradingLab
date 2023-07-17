from AlgorithmImports import *
from stocks import stock_data
from trading_logic import TradingDecision

class StockData:
    def __init__(self, symbol, description):
        self.symbol = symbol
        self.description = description

class QuantConnectBacktester(QCAlgorithm):
    def Initialize(self):
        self.SetStartDate(2023, 5, 15)  # Set Start Date
        self.SetCash(100000)  # Set Strategy Cash

        self.selected_stocks = []  # Define selected_stocks before calling LoadStockData
        self.trading_decision = TradingDecision()

        # Load stock_data from your data source
        self.LoadStockData()

        self.SetBrokerageModel(BrokerageName.InteractiveBrokersBrokerage, AccountType.Margin)  # Enable margin trading

    def OnData(self, data):
        if self.trading_decision.should_rebalance(self.Time):
            sorted_stocks, allocation_per_stock = self.trading_decision.get_sorted_stocks(self.selected_stocks)

            for stock in sorted_stocks:
                self.SetHoldings(stock.Symbol, allocation_per_stock)

    def LoadStockData(self):
        for stock in stock_data:
            symbol = stock['symbol']
            description = stock['description']
            equity = self.AddEquity(symbol, Resolution.Minute)
            equity.Tag = StockData(symbol, description)
            self.selected_stocks.append(equity)
