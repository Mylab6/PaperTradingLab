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
        # log out all the stock prices 
        for stock in stocks:
            # if stock.Price , stock.last_sale_price = stock.Price 
            if hasattr(stock, 'Price'):
                stock.last_sale_price = stock.Price
            

            
            
        sorted_stocks = sorted(stocks, key=lambda stock: stock.last_sale_price, reverse=True)[:top_n]
        allocation_per_stock = min(0.15, 2.0 / len(sorted_stocks))
        return sorted_stocks, allocation_per_stock
