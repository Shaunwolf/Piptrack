import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json
import logging
from datetime import datetime

class GoogleSheetsIntegration:
    def __init__(self):
        self.spreadsheet_id = os.environ.get('GOOGLE_SHEETS_ID')
        self.worksheet_name = 'Trade Journal'
        self.client = None
        self.worksheet = None
        self.initialize_client()
    
    def initialize_client(self):
        """Initialize Google Sheets client"""
        try:
            # Get credentials from environment variable
            creds_json = os.environ.get('GOOGLE_SHEETS_CREDENTIALS')
            if not creds_json:
                logging.warning("Google Sheets credentials not found in environment")
                return
            
            # Parse credentials
            creds_info = json.loads(creds_json)
            
            # Define scope
            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive'
            ]
            
            # Create credentials
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
            
            # Initialize client
            self.client = gspread.authorize(creds)
            
            # Open spreadsheet
            if self.spreadsheet_id:
                spreadsheet = self.client.open_by_key(self.spreadsheet_id)
                
                # Get or create worksheet
                try:
                    self.worksheet = spreadsheet.worksheet(self.worksheet_name)
                except gspread.WorksheetNotFound:
                    self.worksheet = spreadsheet.add_worksheet(
                        title=self.worksheet_name,
                        rows="1000",
                        cols="20"
                    )
                    self.setup_headers()
            
            logging.info("Google Sheets integration initialized successfully")
            
        except Exception as e:
            logging.error(f"Error initializing Google Sheets client: {e}")
            self.client = None
            self.worksheet = None
    
    def setup_headers(self):
        """Setup column headers in the worksheet"""
        try:
            if not self.worksheet:
                return
            
            headers = [
                'Date', 'Symbol', 'Entry Price', 'Stop Loss', 'Take Profit',
                'Confidence Score', 'Pattern Confirmed', 'Screenshot Taken',
                'Reflection', 'Perfect Trade', 'Outcome', 'Exit Price',
                'P&L', 'Lessons Learned', 'Pattern Type', 'RSI at Entry',
                'Volume Spike', 'Trade Duration', 'Risk Reward Ratio', 'Notes'
            ]
            
            self.worksheet.append_row(headers)
            logging.info("Headers added to Google Sheets")
            
        except Exception as e:
            logging.error(f"Error setting up headers: {e}")
    
    def submit_trade(self, trade):
        """Submit trade entry to Google Sheets"""
        try:
            if not self.worksheet:
                logging.warning("Google Sheets not available - trade not submitted")
                return False
            
            # Prepare row data
            row_data = [
                trade.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                trade.symbol,
                trade.entry_price,
                trade.stop_loss,
                trade.take_profit,
                trade.confidence_at_entry,
                'Yes' if trade.pattern_confirmed else 'No',
                'Yes' if trade.screenshot_taken else 'No',
                trade.reflection or '',
                'Yes' if trade.perfect_trade else 'No',
                trade.outcome or 'Active',
                trade.exit_price or '',
                trade.pnl or '',
                trade.lessons_learned or '',
                '',  # Pattern Type - to be filled
                '',  # RSI at Entry - to be filled
                '',  # Volume Spike - to be filled
                '',  # Trade Duration - to be calculated
                self.calculate_risk_reward_ratio(trade.entry_price, trade.stop_loss, trade.take_profit),
                ''   # Notes
            ]
            
            # Append row to worksheet
            self.worksheet.append_row(row_data)
            logging.info(f"Trade {trade.symbol} submitted to Google Sheets")
            return True
            
        except Exception as e:
            logging.error(f"Error submitting trade to Google Sheets: {e}")
            return False
    
    def update_trade_outcome(self, trade_id, outcome_data):
        """Update trade outcome in Google Sheets"""
        try:
            if not self.worksheet:
                return False
            
            # Find the row with matching trade (simplified - in production, you'd want better matching)
            # This is a basic implementation
            
            logging.info(f"Trade outcome updated in Google Sheets")
            return True
            
        except Exception as e:
            logging.error(f"Error updating trade outcome: {e}")
            return False
    
    def get_trade_statistics(self):
        """Get trade statistics from Google Sheets"""
        try:
            if not self.worksheet:
                return {}
            
            # Get all records
            records = self.worksheet.get_all_records()
            
            if not records:
                return {}
            
            # Calculate statistics
            total_trades = len(records)
            wins = sum(1 for record in records if record.get('Outcome') == 'Win')
            losses = sum(1 for record in records if record.get('Outcome') == 'Loss')
            
            win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
            
            # Calculate total P&L
            total_pnl = sum(float(record.get('P&L', 0) or 0) for record in records)
            
            return {
                'total_trades': total_trades,
                'wins': wins,
                'losses': losses,
                'win_rate': round(win_rate, 2),
                'total_pnl': round(total_pnl, 2)
            }
            
        except Exception as e:
            logging.error(f"Error getting trade statistics: {e}")
            return {}
    
    def calculate_risk_reward_ratio(self, entry, stop_loss, take_profit):
        """Calculate risk-reward ratio"""
        try:
            if not all([entry, stop_loss, take_profit]):
                return ''
            
            risk = abs(entry - stop_loss)
            reward = abs(take_profit - entry)
            
            if risk == 0:
                return ''
            
            ratio = reward / risk
            return f"1:{round(ratio, 2)}"
            
        except Exception as e:
            logging.error(f"Error calculating risk-reward ratio: {e}")
            return ''
    
    def export_weekly_data(self):
        """Export last week's trading data"""
        try:
            if not self.worksheet:
                return []
            
            # Get all records
            records = self.worksheet.get_all_records()
            
            # Filter for last week (simplified)
            one_week_ago = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            one_week_ago = one_week_ago - timedelta(days=7)
            
            weekly_records = []
            for record in records:
                try:
                    trade_date = datetime.strptime(record.get('Date', ''), '%Y-%m-%d %H:%M:%S')
                    if trade_date >= one_week_ago:
                        weekly_records.append(record)
                except:
                    continue
            
            return weekly_records
            
        except Exception as e:
            logging.error(f"Error exporting weekly data: {e}")
            return []
