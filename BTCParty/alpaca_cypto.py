import alpaca_trade_api as tradeapi
import pandas as pd
import time
from coins import popular_coins
import alpaca_trade_api as tradeapi
from datetime import datetime, timedelta
from alpaca_trade_api.rest import TimeFrame
class AlpacaTrader:
    def __init__(self, api_key, secret_key):
        self.api = tradeapi.REST(api_key, secret_key, base_url='https://paper-api.alpaca.markets')

    def fetch_historical_data(self, coins):
        end_date = datetime.now()
        start_date = end_date - timedelta(days=2)
        start_date_str = start_date.strftime('%Y-%m-%dT%H:%M:%SZ')

        hist_data = {}
        bars = self.api.get_crypto_bars(coins, TimeFrame.Hour, start=start_date_str).df

        for coin in coins:
            print(f"Fetching data for {coin}")
            # print all the properties of the bars
            print(type(bars))
            for b in bars:
                print(bars[b])
            hist_data[coin] = bars['coin'].set_index('t')

        return hist_data







    def calculate_percentage_changes(self, hist_data):
        crypto_changes = []
        for coin, data in hist_data.items():
            if len(data) >= 2:
                yesterday_close = data.iloc[-2]['close']
                today_close = data.iloc[-1]['close']
                pct_change = (today_close - yesterday_close) / yesterday_close
                crypto_changes.append((coin, pct_change))
        return crypto_changes

    def place_orders(self, top_cryptos, cash):
        for coin, pct_change in top_cryptos:
            print(f"{coin}: {pct_change * 100}% change")
            quantity = cash / (5 * today_close)  # equal cash allocated for each coin
            self.api.submit_order(
                symbol=coin,
                qty=quantity,
                side='buy',
                type='market',
                time_in_force='gtc',
            )

# Replace with your actual Alpaca API keys
api_key = 'REDACTED'
secret_key = 'REDACTED'

trader = AlpacaTrader(api_key, secret_key)

# Fetch historical data for each popular coin
formatted_coins = [coin[:-3] + "/USD" for coin in popular_coins]

hist_data = trader.fetch_historical_data(formatted_coins)

# Calculate percentage changes
crypto_changes = trader.calculate_percentage_changes(hist_data)

# Sort cryptos by percentage change and take the top 5
sorted_changes = sorted(crypto_changes, key=lambda x: x[1], reverse=True)
top_cryptos = sorted_changes[:5]

# Get account cash balance
account = trader.api.get_account()
cash = float(account.cash)

# Place orders for top cryptos
trader.place_orders(top_cryptos, cash)

# Give the API a few seconds to place the orders
time.sleep(3)

# Confirm orders were placed
orders = trader.api.list_orders()
for order in orders:
    print(f"Placed order: {order.symbol}, {order.qty}, {order.side}, {order.status}")
