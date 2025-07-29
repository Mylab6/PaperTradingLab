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
            account_info = {
                'account_id': account.id,
                'status': account.status,
                'currency': getattr(account, 'currency', 'USD'),
                'buying_power': float(account.buying_power) if account.buying_power else 0.0,
                'cash': float(account.cash) if account.cash else 0.0,
                'portfolio_value': float(account.portfolio_value) if account.portfolio_value else 0.0,
                'equity': float(account.equity) if account.equity else 0.0,
                'last_equity': float(getattr(account, 'last_equity', 0)) if hasattr(account, 'last_equity') else 0.0,
                'trading_blocked': getattr(account, 'trading_blocked', False),
                'transfers_blocked': getattr(account, 'transfers_blocked', False),
                'account_blocked': getattr(account, 'account_blocked', False)
            }
            
            # Add optional fields if they exist
            optional_fields = [
                'day_trade_buying_power', 'daytrading_buying_power',
                'pattern_day_trader', 'max_day_trade_buying_power',
                'regt_buying_power', 'initial_margin', 'maintenance_margin',
                'sma', 'multiplier'
            ]
            
            for field in optional_fields:
                if hasattr(account, field) and getattr(account, field) is not None:
                    try:
                        value = getattr(account, field)
                        if isinstance(value, (int, float)):
                            account_info[field] = float(value)
                        else:
                            account_info[field] = value
                    except (ValueError, AttributeError):
                        continue
            
            return account_info
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
                    'qty': float(position.qty) if position.qty else 0.0,
                    'side': position.side,
                    'market_value': float(position.market_value) if position.market_value else 0.0,
                    'cost_basis': float(position.cost_basis) if position.cost_basis else 0.0,
                    'unrealized_pl': float(position.unrealized_pl) if position.unrealized_pl else 0.0,
                    'unrealized_plpc': float(position.unrealized_plpc) if position.unrealized_plpc else 0.0,
                    'avg_entry_price': float(position.avg_entry_price) if position.avg_entry_price else 0.0,
                    'current_price': float(getattr(position, 'current_price', 0)) if hasattr(position, 'current_price') else 0.0
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
            if hasattr(portfolio_history, 'timestamp') and portfolio_history.timestamp and hasattr(portfolio_history, 'equity') and portfolio_history.equity:
                for i, timestamp in enumerate(portfolio_history.timestamp):
                    if i < len(portfolio_history.equity) and portfolio_history.equity[i] is not None:
                        history_entry = {
                            'timestamp': datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S'),
                            'equity': float(portfolio_history.equity[i])
                        }
                        
                        # Add optional profit_loss and profit_loss_pct if available
                        if hasattr(portfolio_history, 'profit_loss') and portfolio_history.profit_loss and i < len(portfolio_history.profit_loss):
                            if portfolio_history.profit_loss[i] is not None:
                                history_entry['profit_loss'] = float(portfolio_history.profit_loss[i])
                        
                        if hasattr(portfolio_history, 'profit_loss_pct') and portfolio_history.profit_loss_pct and i < len(portfolio_history.profit_loss_pct):
                            if portfolio_history.profit_loss_pct[i] is not None:
                                history_entry['profit_loss_pct'] = float(portfolio_history.profit_loss_pct[i])
                        
                        history_data.append(history_entry)
            
            return history_data
        except Exception as e:
            print(f"Error getting portfolio history: {e}")
            return []
    
    def get_account_activities(self, activity_types=None, page_size=1000):
        """Get account activities for P&L calculation"""
        try:
            # Get all account activities
            if activity_types is None:
                activity_types = ['FILL', 'DIV', 'INTEREST', 'FEE', 'SOSO', 'CSO', 'CSD']
            
            all_activities = []
            page_token = None
            
            # Paginate through all activities
            for _ in range(10):  # Limit to prevent infinite loops
                activities = self.alpaca.get_account_activities(
                    activity_types=activity_types,
                    page_size=page_size,
                    page_token=page_token
                )
                
                if not activities:
                    break
                
                for activity in activities:
                    activity_data = {
                        'id': activity.id,
                        'activity_type': activity.activity_type,
                        'date': activity.date.strftime('%Y-%m-%d') if activity.date else '',
                        'symbol': getattr(activity, 'symbol', ''),
                        'side': getattr(activity, 'side', ''),
                        'qty': float(getattr(activity, 'qty', 0)) if hasattr(activity, 'qty') and getattr(activity, 'qty') else 0.0,
                        'price': float(getattr(activity, 'price', 0)) if hasattr(activity, 'price') and getattr(activity, 'price') else 0.0,
                        'net_amount': float(getattr(activity, 'net_amount', 0)) if hasattr(activity, 'net_amount') and getattr(activity, 'net_amount') else 0.0,
                        'description': getattr(activity, 'description', '')
                    }
                    all_activities.append(activity_data)
                
                # Check if there are more pages
                if len(activities) < page_size:
                    break
                
                # Get the page token for next page (this might vary based on API version)
                page_token = getattr(activities[-1], 'id', None)
            
            return all_activities
        except Exception as e:
            print(f"Error getting account activities: {e}")
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
                order_entry = {
                    'id': order.id,
                    'symbol': order.symbol,
                    'qty': float(order.qty) if order.qty else 0.0,
                    'side': order.side,
                    'order_type': order.order_type,
                    'status': order.status,
                    'filled_qty': float(order.filled_qty) if order.filled_qty else 0.0,
                    'filled_avg_price': float(order.filled_avg_price) if order.filled_avg_price else 0.0,
                }
                
                # Handle timestamps safely
                if hasattr(order, 'submitted_at') and order.submitted_at:
                    order_entry['submitted_at'] = order.submitted_at.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    order_entry['submitted_at'] = ''
                    
                if hasattr(order, 'filled_at') and order.filled_at:
                    order_entry['filled_at'] = order.filled_at.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    order_entry['filled_at'] = ''
                    
                if hasattr(order, 'created_at') and order.created_at:
                    order_entry['created_at'] = order.created_at.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    order_entry['created_at'] = ''
                
                order_data.append(order_entry)
            
            return order_data
        except Exception as e:
            print(f"Error getting orders: {e}")
            return []
        """Get recent orders"""
        try:
            orders = self.alpaca.list_orders(
                status=status,
                limit=limit,
                nested=True
            )
            
            order_data = []
            for order in orders:
                order_entry = {
                    'id': order.id,
                    'symbol': order.symbol,
                    'qty': float(order.qty) if order.qty else 0.0,
                    'side': order.side,
                    'order_type': order.order_type,
                    'status': order.status,
                    'filled_qty': float(order.filled_qty) if order.filled_qty else 0.0,
                    'filled_avg_price': float(order.filled_avg_price) if order.filled_avg_price else 0.0,
                }
                
                # Handle timestamps safely
                if hasattr(order, 'submitted_at') and order.submitted_at:
                    order_entry['submitted_at'] = order.submitted_at.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    order_entry['submitted_at'] = ''
                    
                if hasattr(order, 'filled_at') and order.filled_at:
                    order_entry['filled_at'] = order.filled_at.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    order_entry['filled_at'] = ''
                    
                if hasattr(order, 'created_at') and order.created_at:
                    order_entry['created_at'] = order.created_at.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    order_entry['created_at'] = ''
                
                order_data.append(order_entry)
            
            return order_data
        except Exception as e:
            print(f"Error getting orders: {e}")
            return []
    
    def calculate_lifetime_pnl(self, activities):
        """Calculate lifetime realized P&L from account activities"""
        realized_pnl = 0.0
        dividends = 0.0
        interest = 0.0
        fees = 0.0
        deposits = 0.0
        withdrawals = 0.0
        
        # Track cash flows and trading activities
        for activity in activities:
            activity_type = activity['activity_type']
            net_amount = activity['net_amount']
            
            if activity_type == 'FILL':
                # Trading fills - this includes realized P&L from completed trades
                realized_pnl += net_amount
            elif activity_type == 'DIV':
                # Dividends received
                dividends += net_amount
            elif activity_type == 'INTEREST':
                # Interest earned
                interest += net_amount
            elif activity_type == 'FEE':
                # Fees paid
                fees += net_amount  # net_amount is usually negative for fees
            elif activity_type in ['SOSO', 'CSO']:
                # Stock splits, spin-offs
                pass  # These don't affect P&L directly
            elif activity_type == 'CSD':
                # Cash deposits/withdrawals
                if net_amount > 0:
                    deposits += net_amount
                else:
                    withdrawals += abs(net_amount)
        
        return {
            'realized_pnl': realized_pnl,
            'dividends': dividends,
            'interest': interest,
            'fees': fees,
            'deposits': deposits,
            'withdrawals': withdrawals,
            'net_deposits': deposits - withdrawals
        }
    
    def calculate_total_pnl(self):
        """Calculate comprehensive lifetime P&L summary"""
        print("Calculating Total Lifetime PnL...")
        
        # Get account info
        account_info = self.get_account_info()
        if not account_info:
            return None
        
        # Get current positions
        positions = self.get_positions()
        
        # Get portfolio history
        portfolio_history = self.get_portfolio_history()
        
        # Get account activities for lifetime P&L calculation
        print("Fetching account activities...")
        activities = self.get_account_activities()
        
        # Get recent orders
        orders = self.get_orders()
        
        # Calculate position statistics
        total_unrealized_pl = sum([pos['unrealized_pl'] for pos in positions])
        total_market_value = sum([pos['market_value'] for pos in positions])
        total_cost_basis = sum([pos['cost_basis'] for pos in positions])
        
        # Calculate lifetime P&L from activities
        lifetime_pnl = self.calculate_lifetime_pnl(activities)
        
        # Calculate total lifetime P&L
        # Total P&L = Current Equity - Net Deposits
        current_equity = account_info['equity']
        net_deposits = lifetime_pnl['net_deposits']
        total_lifetime_pnl = current_equity - net_deposits
        
        # Alternative calculation: Realized P&L + Unrealized P&L + Dividends + Interest + Fees
        calculated_lifetime_pnl = (lifetime_pnl['realized_pnl'] + 
                                 total_unrealized_pl + 
                                 lifetime_pnl['dividends'] + 
                                 lifetime_pnl['interest'] + 
                                 lifetime_pnl['fees'])
        
        # Day P&L calculation
        last_equity = account_info.get('last_equity', 0)
        day_pl = current_equity - last_equity if last_equity > 0 else 0
        
        # Get filled orders for reference
        filled_orders = [order for order in orders if order['status'] == 'filled']
        
        summary = {
            'calculation_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            
            # Account basics
            'account_equity': current_equity,
            'portfolio_value': account_info['portfolio_value'],
            'cash': account_info['cash'],
            'buying_power': account_info['buying_power'],
            'account_status': account_info['status'],
            
            # Position summary
            'total_positions': len(positions),
            'total_market_value': total_market_value,
            'total_cost_basis': total_cost_basis,
            'total_unrealized_pl': total_unrealized_pl,
            
            # Lifetime P&L breakdown
            'net_deposits': net_deposits,
            'total_deposits': lifetime_pnl['deposits'],
            'total_withdrawals': lifetime_pnl['withdrawals'],
            'realized_pnl_from_trades': lifetime_pnl['realized_pnl'],
            'dividends_received': lifetime_pnl['dividends'],
            'interest_earned': lifetime_pnl['interest'],
            'fees_paid': lifetime_pnl['fees'],
            
            # Total lifetime P&L calculations
            'total_lifetime_pnl_simple': total_lifetime_pnl,
            'total_lifetime_pnl_detailed': calculated_lifetime_pnl,
            
            # Performance metrics
            'lifetime_return_pct': (total_lifetime_pnl / net_deposits * 100) if net_deposits > 0 else 0,
            'unrealized_return_pct': (total_unrealized_pl / total_cost_basis * 100) if total_cost_basis > 0 else 0,
            
            # Daily and activity stats
            'day_pl': day_pl,
            'total_activities': len(activities),
            'total_orders': len(orders),
            'filled_orders': len(filled_orders)
        }
        
        # Add optional account info to summary
        optional_fields = ['day_trade_buying_power', 'pattern_day_trader', 'initial_margin', 
                          'maintenance_margin', 'currency', 'trading_blocked', 'account_blocked']
        for key in optional_fields:
            if key in account_info:
                summary[key] = account_info[key]
        
        return {
            'summary': summary,
            'positions': positions,
            'portfolio_history': portfolio_history,
            'activities': activities,
            'orders': orders,
            'account_info': account_info,
            'lifetime_pnl_breakdown': lifetime_pnl
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
        
        # Save activities
        if pnl_data['activities']:
            activities_file = os.path.join(output_dir, f'activities_{timestamp}.csv')
            df_activities = pd.DataFrame(pnl_data['activities'])
            df_activities.to_csv(activities_file, index=False)
            print(f"Activities saved to: {activities_file}")
        
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
            'activities_file': activities_file if pnl_data['activities'] else None,
            'orders_file': orders_file if pnl_data['orders'] else None
        }
    
    def print_summary(self, pnl_data):
        """Print a nice summary of the PnL data"""
        if not pnl_data:
            print("No PnL data available")
            return
        
        summary = pnl_data['summary']
        
        print("\n" + "="*60)
        print("PORTFOLIO LIFETIME PROFIT & LOSS SUMMARY")
        print("="*60)
        
        print(f"Calculation Date: {summary['calculation_date']}")
        print(f"Account Status: {summary.get('account_status', 'N/A')}")
        print(f"Account Equity: ${summary['account_equity']:,.2f}")
        print(f"Portfolio Value: ${summary['portfolio_value']:,.2f}")
        print(f"Cash Available: ${summary['cash']:,.2f}")
        print(f"Buying Power: ${summary['buying_power']:,.2f}")
        
        if summary.get('day_pl', 0) != 0:
            print(f"Day P&L: ${summary['day_pl']:,.2f}")
        
        print("\n" + "-"*40)
        print("LIFETIME CASH FLOWS")
        print("-"*40)
        print(f"Total Deposits: ${summary['total_deposits']:,.2f}")
        print(f"Total Withdrawals: ${summary['total_withdrawals']:,.2f}")
        print(f"Net Deposits: ${summary['net_deposits']:,.2f}")
        
        print("\n" + "-"*40)
        print("LIFETIME P&L BREAKDOWN")
        print("-"*40)
        print(f"Realized P&L from Trades: ${summary['realized_pnl_from_trades']:,.2f}")
        print(f"Current Unrealized P&L: ${summary['total_unrealized_pl']:,.2f}")
        print(f"Dividends Received: ${summary['dividends_received']:,.2f}")
        print(f"Interest Earned: ${summary['interest_earned']:,.2f}")
        print(f"Fees Paid: ${summary['fees_paid']:,.2f}")
        
        print("\n" + "-"*40)
        print("TOTAL LIFETIME P&L")
        print("-"*40)
        print(f"Total Lifetime P&L: ${summary['total_lifetime_pnl_simple']:,.2f}")
        print(f"Detailed Calculation: ${summary['total_lifetime_pnl_detailed']:,.2f}")
        print(f"Lifetime Return: {summary['lifetime_return_pct']:.2f}%")
        
        # Print optional account info if available
        optional_display = {
            'day_trade_buying_power': 'Day Trade Buying Power',
            'pattern_day_trader': 'Pattern Day Trader',
            'initial_margin': 'Initial Margin',
            'maintenance_margin': 'Maintenance Margin',
            'currency': 'Account Currency'
        }
        
        print("\n" + "-"*40)
        print("ACCOUNT DETAILS")
        print("-"*40)
        for key, label in optional_display.items():
            if key in summary and summary[key] is not None:
                if isinstance(summary[key], (int, float)):
                    print(f"{label}: ${summary[key]:,.2f}")
                else:
                    print(f"{label}: {summary[key]}")
        
        if summary.get('trading_blocked') or summary.get('account_blocked'):
            print(f"⚠️  Account Restrictions: Trading Blocked: {summary.get('trading_blocked', False)}, Account Blocked: {summary.get('account_blocked', False)}")
        
        print("\n" + "-"*40)
        print("POSITION SUMMARY")
        print("-"*40)
        print(f"Total Positions: {summary['total_positions']}")
        print(f"Total Market Value: ${summary['total_market_value']:,.2f}")
        print(f"Total Cost Basis: ${summary['total_cost_basis']:,.2f}")
        if summary['total_cost_basis'] > 0:
            print(f"Unrealized Return %: {summary['unrealized_return_pct']:.2f}%")
        
        print("\n" + "-"*40)
        print("ACTIVITY SUMMARY")
        print("-"*40)
        print(f"Total Account Activities: {summary['total_activities']}")
        print(f"Total Orders: {summary['total_orders']}")
        print(f"Filled Orders: {summary['filled_orders']}")
        
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
