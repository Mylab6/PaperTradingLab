import alpaca_trade_api as tradeapi
import os
import pandas as pd
from datetime import datetime, timedelta
import csv

class PnLCalculator:
    def __init__(self):
        """Initialize the PnL Calculator with Alpaca API credentials"""
        self.api_key = os.getenv('ALPACA_API_KEY')
        self.api_secret = os.getenv('ALPACA_API_SECRET')
        self.api_url = os.getenv('ALPACA_API_URL', 'https://paper-api.alpaca.markets')
        
        if not self.api_key or not self.api_secret:
            raise ValueError("Missing Alpaca API credentials. Please set ALPACA_API_KEY and ALPACA_API_SECRET environment variables.")
        
        self.alpaca = tradeapi.REST(self.api_key, self.api_secret, base_url=self.api_url)
    
    def get_account_info(self):
        """Get current account information"""
        try:
            account = self.alpaca.get_account()
            return {
                'account_id': account.id,
                'buying_power': float(account.buying_power),
                'cash': float(account.cash),
                'portfolio_value': float(account.portfolio_value),
                'equity': float(account.equity),
                'day_trade_buying_power': float(account.day_trade_buying_power),
                'pattern_day_trader': account.pattern_day_trader
            }
        except Exception as e:
            print(f"Error getting account info: {e}")
            return None
    
    def get_positions(self):
        """Get current positions"""
        try:
            positions = self.alpaca.list_positions()
            position_data = []
            
            for position in positions:
                position_data.append({
                    'symbol': position.symbol,
                    'qty': float(position.qty),
                    'side': position.side,
                    'market_value': float(position.market_value),
                    'cost_basis': float(position.cost_basis),
                    'unrealized_pl': float(position.unrealized_pl),
                    'unrealized_plpc': float(position.unrealized_plpc),
                    'avg_entry_price': float(position.avg_entry_price),
                    'current_price': float(position.current_price)
                })
            
            return position_data
        except Exception as e:
            print(f"Error getting positions: {e}")
            return []
    
    def get_portfolio_history(self, timeframe='1D', period='1M'):
        """Get portfolio history"""
        try:
            portfolio_history = self.alpaca.get_portfolio_history(
                timeframe=timeframe,
                period=period
            )
            
            history_data = []
            if portfolio_history.timestamp and portfolio_history.equity:
                for i, timestamp in enumerate(portfolio_history.timestamp):
                    if i < len(portfolio_history.equity):
                        history_data.append({
                            'timestamp': datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S'),
                            'equity': portfolio_history.equity[i],
                            'profit_loss': portfolio_history.profit_loss[i] if i < len(portfolio_history.profit_loss) else 0,
                            'profit_loss_pct': portfolio_history.profit_loss_pct[i] if i < len(portfolio_history.profit_loss_pct) else 0
                        })
            
            return history_data
        except Exception as e:
            print(f"Error getting portfolio history: {e}")
            return []
    
    def get_orders(self, status='all', limit=500):
        """Get recent orders"""
        try:
            orders = self.alpaca.list_orders(
                status=status,
                limit=limit,
                nested=True
            )
            
            order_data = []
            for order in orders:
                order_data.append({
                    'id': order.id,
                    'symbol': order.symbol,
                    'qty': float(order.qty) if order.qty else 0,
                    'side': order.side,
                    'order_type': order.order_type,
                    'status': order.status,
                    'filled_qty': float(order.filled_qty) if order.filled_qty else 0,
                    'filled_avg_price': float(order.filled_avg_price) if order.filled_avg_price else 0,
                    'submitted_at': order.submitted_at.strftime('%Y-%m-%d %H:%M:%S') if order.submitted_at else '',
                    'filled_at': order.filled_at.strftime('%Y-%m-%d %H:%M:%S') if order.filled_at else '',
                    'created_at': order.created_at.strftime('%Y-%m-%d %H:%M:%S') if order.created_at else ''
                })
            
            return order_data
        except Exception as e:
            print(f"Error getting orders: {e}")
            return []
    
    def calculate_total_pnl(self):
        """Calculate comprehensive PnL summary"""
        print("Calculating Total PnL...")
        
        # Get account info
        account_info = self.get_account_info()
        if not account_info:
            return None
        
        # Get current positions
        positions = self.get_positions()
        
        # Get portfolio history
        portfolio_history = self.get_portfolio_history()
        
        # Get recent orders
        orders = self.get_orders()
        
        # Calculate summary statistics
        total_unrealized_pl = sum([pos['unrealized_pl'] for pos in positions])
        total_market_value = sum([pos['market_value'] for pos in positions])
        total_cost_basis = sum([pos['cost_basis'] for pos in positions])
        
        # Calculate realized PnL from filled orders
        realized_pl = 0
        filled_orders = [order for order in orders if order['status'] == 'filled']
        
        # Simple realized PnL calculation (buy orders negative, sell orders positive)
        for order in filled_orders:
            if order['side'] == 'sell':
                realized_pl += order['filled_qty'] * order['filled_avg_price']
            elif order['side'] == 'buy':
                realized_pl -= order['filled_qty'] * order['filled_avg_price']
        
        summary = {
            'calculation_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'account_equity': account_info['equity'],
            'portfolio_value': account_info['portfolio_value'],
            'cash': account_info['cash'],
            'buying_power': account_info['buying_power'],
            'total_positions': len(positions),
            'total_market_value': total_market_value,
            'total_cost_basis': total_cost_basis,
            'total_unrealized_pl': total_unrealized_pl,
            'estimated_realized_pl': realized_pl,
            'total_estimated_pl': total_unrealized_pl + realized_pl,
            'total_orders': len(orders),
            'filled_orders': len(filled_orders)
        }
        
        return {
            'summary': summary,
            'positions': positions,
            'portfolio_history': portfolio_history,
            'orders': orders,
            'account_info': account_info
        }
    
    def save_to_csv(self, pnl_data, output_dir='./'):
        """Save PnL data to CSV files"""
        if not pnl_data:
            print("No PnL data to save")
            return
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save summary
        summary_file = os.path.join(output_dir, f'pnl_summary_{timestamp}.csv')
        with open(summary_file, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Metric', 'Value'])
            for key, value in pnl_data['summary'].items():
                writer.writerow([key, value])
        
        print(f"Summary saved to: {summary_file}")
        
        # Save positions
        if pnl_data['positions']:
            positions_file = os.path.join(output_dir, f'positions_{timestamp}.csv')
            df_positions = pd.DataFrame(pnl_data['positions'])
            df_positions.to_csv(positions_file, index=False)
            print(f"Positions saved to: {positions_file}")
        
        # Save portfolio history
        if pnl_data['portfolio_history']:
            history_file = os.path.join(output_dir, f'portfolio_history_{timestamp}.csv')
            df_history = pd.DataFrame(pnl_data['portfolio_history'])
            df_history.to_csv(history_file, index=False)
            print(f"Portfolio history saved to: {history_file}")
        
        # Save orders
        if pnl_data['orders']:
            orders_file = os.path.join(output_dir, f'orders_{timestamp}.csv')
            df_orders = pd.DataFrame(pnl_data['orders'])
            df_orders.to_csv(orders_file, index=False)
            print(f"Orders saved to: {orders_file}")
        
        return {
            'summary_file': summary_file,
            'positions_file': positions_file if pnl_data['positions'] else None,
            'history_file': history_file if pnl_data['portfolio_history'] else None,
            'orders_file': orders_file if pnl_data['orders'] else None
        }
    
    def print_summary(self, pnl_data):
        """Print a nice summary of the PnL data"""
        if not pnl_data:
            print("No PnL data available")
            return
        
        summary = pnl_data['summary']
        
        print("\n" + "="*60)
        print("PORTFOLIO PROFIT & LOSS SUMMARY")
        print("="*60)
        
        print(f"Calculation Date: {summary['calculation_date']}")
        print(f"Account Equity: ${summary['account_equity']:,.2f}")
        print(f"Portfolio Value: ${summary['portfolio_value']:,.2f}")
        print(f"Cash Available: ${summary['cash']:,.2f}")
        print(f"Buying Power: ${summary['buying_power']:,.2f}")
        
        print("\n" + "-"*40)
        print("POSITION SUMMARY")
        print("-"*40)
        print(f"Total Positions: {summary['total_positions']}")
        print(f"Total Market Value: ${summary['total_market_value']:,.2f}")
        print(f"Total Cost Basis: ${summary['total_cost_basis']:,.2f}")
        print(f"Total Unrealized P&L: ${summary['total_unrealized_pl']:,.2f}")
        
        print("\n" + "-"*40)
        print("TRADING SUMMARY")
        print("-"*40)
        print(f"Total Orders: {summary['total_orders']}")
        print(f"Filled Orders: {summary['filled_orders']}")
        print(f"Estimated Realized P&L: ${summary['estimated_realized_pl']:,.2f}")
        
        print("\n" + "-"*40)
        print("TOTAL P&L ESTIMATE")
        print("-"*40)
        print(f"Total Estimated P&L: ${summary['total_estimated_pl']:,.2f}")
        
        if summary['total_cost_basis'] > 0:
            total_return_pct = (summary['total_estimated_pl'] / summary['total_cost_basis']) * 100
            print(f"Estimated Return %: {total_return_pct:.2f}%")
        
        print("="*60)

def main():
    """Main function to calculate and export PnL"""
    try:
        calculator = PnLCalculator()
        
        # Calculate PnL
        pnl_data = calculator.calculate_total_pnl()
        
        if pnl_data:
            # Print summary to console
            calculator.print_summary(pnl_data)
            
            # Save to CSV files in the same directory as the script
            script_dir = os.path.dirname(os.path.abspath(__file__))
            files = calculator.save_to_csv(pnl_data, script_dir)
            
            print(f"\nPnL calculation completed successfully!")
            print(f"Files generated:")
            for file_type, file_path in files.items():
                if file_path:
                    print(f"  - {file_type}: {file_path}")
        else:
            print("Failed to calculate PnL data")
            
    except Exception as e:
        print(f"Error in PnL calculation: {e}")
        raise

if __name__ == "__main__":
    main()
