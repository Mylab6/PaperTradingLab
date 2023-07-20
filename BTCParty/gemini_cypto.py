import time
from datetime import datetime, timedelta
import gemini
from coins import popular_coins
import os

api_key = os.getenv('GEMINI_API_KEY')
api_secret = os.getenv('GEMINI_API_SECRET')

class GeminiTrader:
    def __init__(self, api_key, api_secret):
        self.privateClient = gemini.PrivateClient(api_key, api_secret, sandbox=True)
        self.publicClient = gemini.PublicClient(sandbox=True)

    def fetch_historical_data(self, coins):
        end_date = datetime.now()
        start_date = end_date - timedelta(days=2)

        hist_data = {}
        for coin in coins:
            try:
                print(f"Fetching data for {coin}")
                bars = self.publicClient.get_ticker(coin)
                hist_data[coin] = bars
            except Exception as e:
                print(f"Could not fetch data for {coin}: {e}")
                continue

        return hist_data


    def calculate_percentage_changes(self, hist_data):
        crypto_changes = []
        for coin, data in hist_data.items():
            if 'result' in data:
                print('Cant parse coin data ?',data)
                continue
           # print(data)
            yesterday_close = float(data['bid'])
            today_close = float(data['ask'])
            if( yesterday_close == 0):
                print('yesterday_close is 0', data)
                continue
            pct_change = (today_close - yesterday_close) / yesterday_close
            crypto_changes.append((coin, pct_change))
        return crypto_changes

    def place_orders(self, top_cryptos):
        # Get account balance
        account = self.privateClient.get_balance()
        print('Account data,' , account)
        usd_balance = next((x['amount'] for x in account if x['currency'] == 'USD'), None)

        if usd_balance is None:
            print("Could not fetch USD balance.")
            return

        for coin, pct_change in top_cryptos:
            print(f"{coin}: {pct_change * 100}% change")
            today_close = self.fetch_historical_data([coin])[coin]['ask']

            quantity = float(usd_balance) / (5 * float(today_close))  # equal cash allocated for each coin

            try:
                self.privateClient.new_order(symbol=coin, amount=str(quantity), price=today_close, side="buy")
                print(f"Order placed: {quantity} units of {coin} at {today_close}")
            except Exception as e:
                print(f"Error placing order for {coin}: {e}")

def trade_crypto():
    trader = GeminiTrader(api_key, api_secret)

    # Fetch historical data for each popular coin
    formatted_coins = popular_coins
    hist_data = trader.fetch_historical_data(formatted_coins)

    # Calculate percentage changes
    crypto_changes = trader.calculate_percentage_changes(hist_data)

    # Sort cryptos by percentage change and take the top 5
    sorted_changes = sorted(crypto_changes, key=lambda x: x[1], reverse=True)
    top_cryptos = sorted_changes[:5]

    # Place orders for top cryptos
    trader.place_orders(top_cryptos)

    # Give the API a few seconds to place the orders
    time.sleep(3)

if __name__ == "__main__":
    trade_crypto()
