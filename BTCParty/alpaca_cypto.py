import alpaca_trade_api as tradeapi
from datetime import datetime, timedelta
from alpaca_trade_api.rest import TimeFrame
import time
from coins import popular_coins
import os

# 2k account balance, keys for keith@beatquestgames.com
api_key = os.getenv('ALPACA_API_KEY')
secret_key = os.getenv('ALPACA_API_SECRET')
api_url = os.getenv('ALPACA_API_URL', 'https://paper-api.alpaca.markets')


class AlpacaTrader:
    def __init__(self, api_key, secret_key):
        self.api = tradeapi.REST(api_key, secret_key, base_url=api_url)
    def fetch_all_cryptos(self):
        """Fetch all available cryptocurrencies from Alpaca"""
        assets = self.api.list_assets(asset_class='crypto')
        return [asset.symbol for asset in assets if asset.tradable and asset.symbol.endswith("USD")]
    def fetch_historical_data(self, coins):
        end_date = datetime.now()
        start_date = end_date - timedelta(days=2)
        start_date_str = start_date.strftime('%Y-%m-%dT%H:%M:%SZ')

        hist_data = {}
        for coin in coins:
            print(f"Fetching data for {coin}")
            bars = self.api.get_crypto_bars([coin], TimeFrame.Hour, start=start_date_str).df
            hist_data[coin] = bars

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

    def place_orders(self, top_cryptos):
        for coin, pct_change in top_cryptos:
            print(f"{coin}: {pct_change * 100}% change")
            today_close = self.fetch_historical_data([coin])[coin].iloc[-1]['close']
    
        # Get account cash balance
            account = self.api.get_account()
            cash = float(account.cash)

        # Calculate the quantity to buy (allowing fractional quantities)
            amount_per_coin = cash / len(top_cryptos)  # Allocate cash equally for each coin
            quantity = amount_per_coin / today_close  # Calculate quantity, allowing fractional amounts

           # if amount_per_coin < today_close:  # Skip this coin if not enough cash for at least 1 unit
            #    print(f"Not enough cash to buy a fraction of {coin}, skipping...")
            #    continue

            try:
                self.api.submit_order(
                symbol=coin,
                qty=round(quantity, 8),  # Round quantity to 8 decimal places, as a typical limit for cryptos
                side='buy',
                type='market',
                time_in_force='gtc',
                )
                print(f"Order placed: {round(quantity, 8)} units of {coin} at {today_close} each")
            except tradeapi.rest.APIError as e:
                print(f"Error placing order for {coin}: {e}")


    def sell_unwanted_coins(self, top_cryptos):
        # Get a list of all current positions
        positions = self.api.list_positions()

        for position in positions:
            if position.symbol not in top_cryptos:
                try:
                    self.api.submit_order(
                        symbol=position.symbol,
                        qty=position.qty,
                        side='sell',
                        type='market',
                        time_in_force='gtc',
                    )
                    print(f"Sell order placed: {position.qty} units of {position.symbol}")
                except tradeapi.rest.APIError as e:
                    print(f"Error placing sell order for {position.symbol}: {e}")

def trade_crypto():
    trader = AlpacaTrader(api_key, secret_key)

    # Fetch historical data for each popular coin
   # popular_coins = ["BTCUSD", "ETHUSD", "XRPUSD", "LTCUSD", "BCHUSD"]
    all_cryptos = trader.fetch_all_cryptos()
    print(all_cryptos)
  #  formatted_coins = [coin[:-3] + "/USD" for coin in popular_coins]
    hist_data = trader.fetch_historical_data(all_cryptos)

    # Calculate percentage changes
    crypto_changes = trader.calculate_percentage_changes(hist_data)

    # Sort cryptos by percentage change and take the top 5
    sorted_changes = sorted(crypto_changes, key=lambda x: x[1], reverse=True)
    top_cryptos = sorted_changes[:5]

    # Sell coins that are no longer in the top 5
    trader.sell_unwanted_coins([crypto[0] for crypto in top_cryptos])
    time.sleep(3)

    # Place orders for top cryptos
    trader.place_orders(top_cryptos)

    # Give the API a few seconds to place the orders
    time.sleep(3)

    # Confirm orders were placed
    orders = trader.api.list_orders()
    for order in orders:
        print(f"Placed order: {order.symbol}, {order.qty}, {order.side}, {order.status}")

if __name__ == "__main__":
    trade_crypto()
