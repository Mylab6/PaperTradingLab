class TradingDecision:
    def __init__(self):
        self.last_rebalance = -1

    def should_rebalance(self, today):
        if today.weekday() != self.last_rebalance:
            self.last_rebalance = today.weekday()
            return True
        else:
            return False

    def get_sorted_stocks(self, stocks, top_n=11):
        for stock in stocks:
            # if stock.Price , stock.last_sale_price = stock.Price 
            if hasattr(stock, 'Price'):
                stock.last_sale_price = stock.Price
        sorted_stocks = sorted(stocks, key=lambda stock: stock.last_sale_price, reverse=True)[:top_n]
        allocation_per_stock = min(0.15, 2.0 / len(sorted_stocks))
        return sorted_stocks, allocation_per_stock

    def get_diverse_stocks(self, stocks, top_n=11):
        # Sort stocks by price first
        sorted_stocks = sorted(stocks, key=lambda stock: stock.last_sale_price, reverse=True)
        
        # Keep track of the sectors we've added
        sectors_added = set()

        # Now select the top stocks ensuring diversity across sectors
        diverse_stocks = []
        for stock in sorted_stocks:
            if stock.Sector not in sectors_added:
                diverse_stocks.append(stock)
                sectors_added.add(stock.Sector)

                # Stop if we have enough stocks
                if len(diverse_stocks) >= top_n:
                    break
        
        allocation_per_stock = min(0.15, 2.0 / len(diverse_stocks))
        return diverse_stocks, allocation_per_stock
