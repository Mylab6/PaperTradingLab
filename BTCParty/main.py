from System import Random
from AlgorithmImports import *

class RandomCryptoAlgo(QCAlgorithm):
    def Initialize(self):
        self.SetStartDate(2023, 1, 1)  # Set start date for backtesting
        self.SetEndDate(2023, 12, 31)  # Set end date for backtesting
        self.SetCash(100000)  # Set initial capital

        # Define a list of popular cryptocurrencies
        self.popular_coins = ['BTCUSD', 'ETHUSD', 'XRPUSD', 'LTCUSD', 'BCHUSD', 'ADAUSD']

        # Set up data subscriptions for each popular coin
        for coin in self.popular_coins:
            self.AddCrypto(coin, Resolution.Daily)

        self.random = Random()

        self.Schedule.On(self.DateRules.Every(DayOfWeek.Monday), self.TimeRules.At(0, 0), self.Rebalance)

    def Rebalance(self):
        # Liquidate all positions
        self.Liquidate()

        # Get a random coin from the list
        random_coin = self.popular_coins[self.random.Next(len(self.popular_coins))]

        # Invest in the random coin
        self.SetHoldings(random_coin, 1)

    def OnData(self, slice):
        pass
