from System import *
from QuantConnect import *
from QuantConnect.Algorithm import *
from QuantConnect.Data.UniverseSelection import *
from AlgorithmImports import *
from coins import popular_coins

class RandomCryptoAlgo(QCAlgorithm):
    def Initialize(self):
        self.SetStartDate(2020, 1, 1)  # Set start date for backtesting
        #  self.SetEndDate(2023, 12, 31)  # Set end date for backtesting
        self.SetCash(2000)  # Set initial capital

        self.UniverseSettings.Resolution = Resolution.Hour
        self.SetBrokerageModel(BrokerageName.GDAX, AccountType.Cash)

        # Define top 20 popular cryptos
        self.popular_cryptos = popular_coins

        # Filter universe to contain only the top 20 popular cryptos
        filter_function = lambda crypto_coarse: [c.Symbol for c in crypto_coarse if c.Symbol.Value in self.popular_cryptos]
        self.AddUniverse(CryptoCoarseFundamentalUniverse(Market.GDAX, self.UniverseSettings, filter_function))

        # Initialize the current top 5 cryptos
        self.current_top_5 = []

    def OnData(self, data):
        # Create a list to store crypto and their price changes
        crypto_changes = []

        # Iterate over each crypto in our universe
        for crypto in self.ActiveSecurities.Values:
            # Request historical data for the past two hours
            history = self.History(crypto.Symbol, 2, Resolution.Hour)

            # Ensure we have two hours of history
            if len(history) >= 2:
                # Get the closing prices
                last_hour_close = history.iloc[-2]['close']
                current_hour_close = history.iloc[-1]['close']

                # Calculate the percentage change
                pct_change = (current_hour_close - last_hour_close) / last_hour_close

                # Append to our list
                crypto_changes.append((crypto, pct_change))

        # Sort the cryptos by percentage change in descending order
        sorted_changes = sorted(crypto_changes, key=lambda x: x[1], reverse=True)

        # Get the top 5 cryptos
        new_top_5 = [crypto for crypto, pct_change in sorted_changes[:5]]

        # Liquidate cryptos that are no longer in top 5
        for crypto in self.current_top_5:
            if crypto not in new_top_5:
                self.Liquidate(crypto.Symbol)

        # Update the current top 5 cryptos
        self.current_top_5 = new_top_5

        # Log the top 5 cryptos and their percentage change
        for crypto, pct_change in sorted_changes[:5]:
            self.Debug(f"{crypto.Symbol}: {pct_change * 100}% change")

            # Invest an equal amount in each of the top 5 cryptos
            self.SetHoldings(crypto.Symbol, 1 / len(self.current_top_5))
