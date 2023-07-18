from System import Random
from AlgorithmImports import *

class RandomCryptoAlgo(QCAlgorithm):
    def Initialize(self):
        self.SetStartDate(2023, 1, 1)  # Set start date for backtesting
        self.SetEndDate(2023, 1, 31)  # Set end date for backtesting
        self.SetCash(100000)  # Set initial capital

        # Define a list of popular cryptocurrencies
        self.popular_coins = ['BTCUSD', 'ETHUSD', 'XRPUSD', 'LTCUSD', 'BCHUSD', 'ADAUSD']

        # Set up data subscriptions for each popular coin
        for coin in self.popular_coins:
            self.AddCrypto(coin, Resolution.Minute)

        # Set up random number generator
        self.random_generator = Random()

    def OnData(self, data):
        # Select a random coin from the list
        random_coin = self.popular_coins[self.random_generator.Next(len(self.popular_coins))]

        # Check if there is data available for the selected coin
        if random_coin in data.Keys:
            coin_data = data[random_coin]
            if coin_data.IsReady:
                # Place a market order for the selected coin
                self.MarketOrder(random_coin, 1)

                # Print the order details to the console
                self.Debug(f"Placed market order for {random_coin} at {coin_data.Close}")
