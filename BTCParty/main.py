from System import Random
from AlgorithmImports import *

class RandomCryptoAlgo(QCAlgorithm):
    def Initialize(self):
        self.SetStartDate(2023, 1, 1)  # Set start date for backtesting
        self.SetEndDate(2023, 12, 31)  # Set end date for backtesting
        self.SetCash(100000)  # Set initial capital

        self.UniverseSettings.Resolution = Resolution.Daily
        self.SetBrokerageModel(BrokerageName.GDAX, AccountType.Cash)

        filter_function = lambda crypto_coarse: [c.Symbol for c in crypto_coarse]
        self.AddUniverse(CryptoCoarseFundamentalUniverse(Market.GDAX, self.UniverseSettings, filter_function))

        self.random = Random()

    def OnSecuritiesChanged(self, changes):
        # Liquidate all positions
        self.Liquidate()

    def OnData(self, data):
        # Create a list to store crypto and their price changes
        crypto_changes = []

        # Iterate over each crypto in our universe
        for crypto in self.ActiveSecurities.Values:
            # Request historical data for the past two days
            history = self.History(crypto.Symbol, 2, Resolution.Daily)

            # Ensure we have two days of history
            if len(history) >= 2:
                # Get the closing prices
                yesterday_close = history.iloc[-2]['close']
                today_close = history.iloc[-1]['close']

                # Calculate the percentage change
                pct_change = (today_close - yesterday_close) / yesterday_close

                # Append to our list
                crypto_changes.append((crypto, pct_change))

        # Sort the cryptos by percentage change in descending order
        sorted_changes = sorted(crypto_changes, key=lambda x: x[1], reverse=True)

        # Get the top 10 cryptos
        top_10_cryptos = sorted_changes[:10]

        # Log the top 10 cryptos and their percentage change
        for crypto, pct_change in top_10_cryptos:
            self.Debug(f"{crypto.Symbol}: {pct_change * 100}% change")

            # Invest an equal amount in each of the top 10 cryptos
            self.SetHoldings(crypto.Symbol, 1 / len(top_10_cryptos))
