import requests
import re
from collections import Counter, defaultdict

class StockData:

    @staticmethod
    def extract_ticker(html_link):
        match = re.search(r'q\?s=([A-Z]+)', html_link)
        return match.group(1) if match else None

    @staticmethod
    def get_most_common_stocks(n=20):
        response = requests.get('https://senate-stock-watcher-data.s3-us-west-2.amazonaws.com/aggregate/all_ticker_transactions.json')
        data = response.json()

        stocks = defaultdict(list)
        for person in data:
            for transaction in person['transactions']:
                ticker = StockData.extract_ticker(transaction['ticker'])
                if ticker:
                    stock_info = {
                        'Symbol': ticker,
                        'Security': transaction.get('asset_description'),
                        'Sector': transaction.get('sector')
                    }
                    stocks[ticker].append(stock_info)

        counter = Counter(ticker for ticker in stocks)

        common_stocks = counter.most_common(n)

        stock_data = []
        for ticker, _ in common_stocks:
            stock = stocks[ticker][0]
            stock_data.append(stock)
            
        return stock_data

# Usage
#stockData = StockData()
#most_common_stocks = stockData.get_most_common_stocks(20)
#print(most_common_stocks)
