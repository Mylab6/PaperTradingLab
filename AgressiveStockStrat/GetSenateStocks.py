import requests
import re
from collections import Counter, defaultdict
from senate_stocks import senate_stocks

class StockData:
    @staticmethod
    def extract_ticker(html_link):
        match = re.search(r'q\?s=([A-Z]+)', html_link)
        return match.group(1) if match else None

    @staticmethod
    def get_most_common_stocks(n=100, useOfflineData=False):
        if useOfflineData:
            print('Using offline senate stock data')
            return senate_stocks[:n]
        
        data = None
        try:
            response = requests.get('https://senate-stock-watcher-data.s3-us-west-2.amazonaws.com/aggregate/all_ticker_transactions.json')
            data = response.json()
        except Exception as e:
            print(f"Error loading senate stock data: {str(e)}")
            print("Using backup senate stock data")
            return senate_stocks[:n]

        stocks = defaultdict(list)
        for person in data:
            for transaction in person['transactions']:
                ticker = StockData.extract_ticker(transaction['ticker'])
                if ticker:
                    stock_info = {
                        'Symbol': ticker,
                        'Security': transaction.get('asset_description'),
                        'Sector': transaction.get('sector'),
                        'Type': transaction.get('type')
                    }
                    stocks[ticker].append(stock_info)

        common_stocks = Counter(ticker for ticker in stocks).most_common(n)

        stock_data = []
        for ticker, count in common_stocks:
            transactions = stocks[ticker]
            total_buys = sum(1 for t in transactions if 'purchase' in t['Type'].lower())
            total_sales = sum(1 for t in transactions if 'sale' in t['Type'].lower())
            # use 10 as a default ratio if there are no sales
            
            buy_to_sale_ratio = total_buys / total_sales if total_sales else 10

            stock = transactions[0]
            stock.update({
                'Total Buys': total_buys,
                'Total Sales': total_sales,
                'Buy to Sale Ratio': buy_to_sale_ratio
            })
            stock_data.append(stock)

        return stock_data


if __name__ == "__main__":
    stockData = StockData()
    most_common_stocks = stockData.get_most_common_stocks(100)
    print(most_common_stocks)
