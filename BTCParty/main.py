from System import *
from QuantConnect import *
from QuantConnect.Algorithm import *
from QuantConnect.Data.UniverseSelection import *
from AlgorithmImports import *
from coins import popular_coins

class RandomCryptoAlgo(QCAlgorithm):
    def Initialize(self):
        self.SetStartDate(2023, 1, 1)  # Set start date for backtesting
        #  self.SetEndDate(2023, 12, 31)  # Set end date for backtesting
        self.SetCash(2000)  # Set initial capital

        self.UniverseSettings.Resolution = Resolution.Daily
        self.SetBrokerageModel(BrokerageName.GDAX, AccountType.Cash)

        # Define top 20 popular cryptos
        self.popular_cryptos = popular_coins
        self.top_n = 10  # Increase the number of cryptos to invest in

        # Filter universe to contain only the top 20 popular cryptos
        filter_function = lambda crypto_coarse: [c.Symbol for c in crypto_coarse if c.Symbol.Value in self.popular_cryptos]
        self.AddUniverse(CryptoCoarseFundamentalUniverse(Market.GDAX, self.UniverseSettings, filter_function))

        # Initialize the current top n cryptos
        self.current_top_n = []
        self.initial_portfolio_value = self.Portfolio.TotalPortfolioValue

    def OnData(self, data):
        # Stop the algorithm if the portfolio's total value drops more than 50%
        if self.Portfolio.TotalPortfolioValue <= 0.5 * self.initial_portfolio_value:
            self.Debug("Stopping Algorithm: Portfolio value dropped more than 50%")
            self.Quit()

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

        # Get the top n cryptos
        new_top_n = [crypto for crypto, pct_change in sorted_changes[:self.top_n]]

        # Liquidate cryptos that are no longer in top n
        for crypto in self.current_top_n:
            if crypto not in new_top_n:
                self.Liquidate(crypto.Symbol)

        # Update the current top n cryptos
        self.current_top_n = new_top_n

        # Log the top n cryptos and their percentage change
        for crypto, pct_change in sorted_changes[:self.top_n]:
            self.Debug(f"{crypto.Symbol}: {pct_change * 100}% change")

            # Invest an equal amount in each of the top n cryptos
            self.SetHoldings(crypto.Symbol, 1 / len(self.current_top_n))
