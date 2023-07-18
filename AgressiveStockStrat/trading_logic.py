class TradingDecision:
    def __init__(self):
        self.last_rebalance = -1

    def should_rebalance(self, today):
        # Check if the current day is different from the last rebalance day and if it's time for noon trading
        if today.weekday() != self.last_rebalance and today.hour >= 16:
            self.last_rebalance = today.weekday()
            return True
        else:
            return False

    def get_sorted_stocks(self, stocks, top_n=11):
        for stock in stocks:
            if hasattr(stock, 'Price'):
                stock.last_sale_price = stock.Price
        sorted_stocks = sorted(stocks, key=lambda stock: stock.last_sale_price, reverse=True)[:top_n]
        allocation_per_stock = min(0.15, 2.0 / len(sorted_stocks))
        return sorted_stocks, allocation_per_stock

    def get_diverse_stocks(self, stocks, top_n=11):
        # Sort stocks by price first
        sorted_stocks = sorted(stocks, key=lambda stock: stock.last_sale_price, reverse=True)
        
        # Keep track of the sectors and their counts
        sector_counts = {}

        # Now select the top stocks ensuring diversity across sectors
        diverse_stocks = []
        for stock in sorted_stocks:
            # Update the count for the stock's sector
            sector_counts[stock.Sector] = sector_counts.get(stock.Sector, 0) + 1

            # Only add the stock if it doesn't exceed the maximum per sector
            if sector_counts[stock.Sector] <= (2 * top_n / 3):
                diverse_stocks.append(stock)

                # Stop if we have enough stocks
                if len(diverse_stocks) >= top_n:
                    break
        
        allocation_per_stock = min(0.1, 2.0 / len(diverse_stocks))
        return diverse_stocks, allocation_per_stock
        
