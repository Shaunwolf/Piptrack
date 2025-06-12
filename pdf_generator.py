import pdfkit
from jinja2 import Template
import os
from datetime import datetime, timedelta
import logging
from models import TradeJournal, Stock
from google_sheets_integration import GoogleSheetsIntegration

class PDFGenerator:
    def __init__(self):
        self.sheets_integration = GoogleSheetsIntegration()
        self.reports_dir = 'static/reports'
        self.ensure_reports_directory()
    
    def ensure_reports_directory(self):
        """Ensure reports directory exists"""
        try:
            os.makedirs(self.reports_dir, exist_ok=True)
        except Exception as e:
            logging.error(f"Error creating reports directory: {e}")
    
    def generate_weekly_report(self):
        """Generate comprehensive weekly trading report"""
        try:
            # Get weekly data
            weekly_data = self.get_weekly_data()
            
            # Generate HTML content
            html_content = self.generate_html_report(weekly_data)
            
            # Convert to PDF
            filename = f"weekly_report_{datetime.now().strftime('%Y%m%d')}.pdf"
            pdf_path = os.path.join(self.reports_dir, filename)
            
            # Configure PDF options
            options = {
                'page-size': 'A4',
                'margin-top': '0.75in',
                'margin-right': '0.75in',
                'margin-bottom': '0.75in',
                'margin-left': '0.75in',
                'encoding': "UTF-8",
                'no-outline': None,
                'enable-local-file-access': None
            }
            
            # Generate PDF
            pdfkit.from_string(html_content, pdf_path, options=options)
            
            logging.info(f"Weekly report generated: {filename}")
            return filename
            
        except Exception as e:
            logging.error(f"Error generating weekly report: {e}")
            return None
    
    def get_weekly_data(self):
        """Get data for the past week"""
        try:
            one_week_ago = datetime.now() - timedelta(days=7)
            
            # Get trades from database
            trades = TradeJournal.query.filter(
                TradeJournal.created_at >= one_week_ago
            ).all()
            
            # Get trade statistics from Google Sheets
            sheets_stats = self.sheets_integration.get_trade_statistics()
            
            # Get weekly data from Google Sheets
            weekly_records = self.sheets_integration.export_weekly_data()
            
            # Calculate performance metrics
            performance = self.calculate_performance_metrics(trades, weekly_records)
            
            return {
                'trades': trades,
                'weekly_records': weekly_records,
                'performance': performance,
                'sheets_stats': sheets_stats,
                'report_date': datetime.now(),
                'week_start': one_week_ago
            }
            
        except Exception as e:
            logging.error(f"Error getting weekly data: {e}")
            return {}
    
    def calculate_performance_metrics(self, trades, weekly_records):
        """Calculate comprehensive performance metrics"""
        try:
            metrics = {
                'total_trades': len(trades),
                'wins': 0,
                'losses': 0,
                'breakeven': 0,
                'active_trades': 0,
                'total_pnl': 0,
                'win_rate': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'profit_factor': 0,
                'best_trade': 0,
                'worst_trade': 0,
                'common_mistakes': [],
                'profitable_setups': [],
                'trading_streaks': []
            }
            
            if not trades:
                return metrics
            
            # Calculate basic metrics
            pnl_values = []
            wins = []
            losses = []
            
            for trade in trades:
                if trade.outcome == 'win' and trade.pnl:
                    metrics['wins'] += 1
                    wins.append(trade.pnl)
                    pnl_values.append(trade.pnl)
                elif trade.outcome == 'loss' and trade.pnl:
                    metrics['losses'] += 1
                    losses.append(abs(trade.pnl))
                    pnl_values.append(trade.pnl)
                elif trade.outcome == 'breakeven':
                    metrics['breakeven'] += 1
                else:
                    metrics['active_trades'] += 1
            
            # Calculate derived metrics
            if pnl_values:
                metrics['total_pnl'] = sum(pnl_values)
                metrics['best_trade'] = max(pnl_values)
                metrics['worst_trade'] = min(pnl_values)
            
            completed_trades = metrics['wins'] + metrics['losses']
            if completed_trades > 0:
                metrics['win_rate'] = (metrics['wins'] / completed_trades) * 100
            
            if wins:
                metrics['avg_win'] = sum(wins) / len(wins)
            
            if losses:
                metrics['avg_loss'] = sum(losses) / len(losses)
            
            if metrics['avg_loss'] > 0:
                metrics['profit_factor'] = metrics['avg_win'] / metrics['avg_loss']
            
            # Analyze patterns
            metrics['common_mistakes'] = self.identify_common_mistakes(trades)
            metrics['profitable_setups'] = self.identify_profitable_setups(trades)
            
            return metrics
            
        except Exception as e:
            logging.error(f"Error calculating performance metrics: {e}")
            return {}
    
    def identify_common_mistakes(self, trades):
        """Identify common trading mistakes"""
        mistakes = []
        
        try:
            # Analyze failed trades
            failed_trades = [t for t in trades if t.outcome == 'loss']
            
            # Check for pattern violations
            pattern_violations = sum(1 for t in failed_trades if not t.pattern_confirmed)
            if pattern_violations > len(failed_trades) * 0.5:
                mistakes.append("Entering trades without pattern confirmation")
            
            # Check for screenshot discipline
            no_screenshot = sum(1 for t in failed_trades if not t.screenshot_taken)
            if no_screenshot > len(failed_trades) * 0.3:
                mistakes.append("Not taking screenshots for trade analysis")
            
            # Check for plan adherence
            imperfect_trades = sum(1 for t in failed_trades if not t.perfect_trade)
            if imperfect_trades > len(failed_trades) * 0.7:
                mistakes.append("Not following trading plan consistently")
            
        except Exception as e:
            logging.error(f"Error identifying common mistakes: {e}")
        
        return mistakes
    
    def identify_profitable_setups(self, trades):
        """Identify most profitable trading setups"""
        setups = []
        
        try:
            # Analyze winning trades
            winning_trades = [t for t in trades if t.outcome == 'win' and t.pnl]
            
            if not winning_trades:
                return setups
            
            # Group by confidence levels
            high_confidence_wins = [t for t in winning_trades if t.confidence_at_entry >= 80]
            if high_confidence_wins:
                avg_pnl = sum(t.pnl for t in high_confidence_wins) / len(high_confidence_wins)
                setups.append(f"High confidence setups (80%+): {len(high_confidence_wins)} trades, Avg P&L: ${avg_pnl:.2f}")
            
            # Analyze pattern confirmations
            confirmed_wins = [t for t in winning_trades if t.pattern_confirmed]
            if confirmed_wins:
                win_rate = len(confirmed_wins) / len(winning_trades) * 100
                setups.append(f"Pattern-confirmed trades: {win_rate:.1f}% of wins")
            
        except Exception as e:
            logging.error(f"Error identifying profitable setups: {e}")
        
        return setups
    
    def generate_html_report(self, data):
        """Generate HTML content for the report"""
        try:
            template_str = """
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Weekly Trading Report</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 40px; color: #333; }
                    .header { text-align: center; margin-bottom: 30px; }
                    .section { margin: 30px 0; }
                    .metric { display: inline-block; margin: 10px 20px; text-align: center; }
                    .metric-value { font-size: 24px; font-weight: bold; color: #2563eb; }
                    .metric-label { font-size: 12px; color: #666; }
                    .positive { color: #059669; }
                    .negative { color: #dc2626; }
                    table { width: 100%; border-collapse: collapse; margin: 20px 0; }
                    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                    th { background-color: #f8f9fa; }
                    .list-item { margin: 5px 0; }
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>Weekly Trading Report</h1>
                    <p>{{ data.week_start.strftime('%B %d') }} - {{ data.report_date.strftime('%B %d, %Y') }}</p>
                </div>
                
                <div class="section">
                    <h2>Performance Overview</h2>
                    <div style="display: flex; flex-wrap: wrap; justify-content: center;">
                        <div class="metric">
                            <div class="metric-value">{{ data.performance.total_trades }}</div>
                            <div class="metric-label">Total Trades</div>
                        </div>
                        <div class="metric">
                            <div class="metric-value {{ 'positive' if data.performance.win_rate > 50 else 'negative' }}">
                                {{ "%.1f"|format(data.performance.win_rate) }}%
                            </div>
                            <div class="metric-label">Win Rate</div>
                        </div>
                        <div class="metric">
                            <div class="metric-value {{ 'positive' if data.performance.total_pnl > 0 else 'negative' }}">
                                ${{ "%.2f"|format(data.performance.total_pnl) }}
                            </div>
                            <div class="metric-label">Total P&L</div>
                        </div>
                        <div class="metric">
                            <div class="metric-value positive">
                                ${{ "%.2f"|format(data.performance.best_trade) }}
                            </div>
                            <div class="metric-label">Best Trade</div>
                        </div>
                    </div>
                </div>
                
                <div class="section">
                    <h2>Trade Breakdown</h2>
                    <table>
                        <tr>
                            <th>Outcome</th>
                            <th>Count</th>
                            <th>Percentage</th>
                        </tr>
                        <tr>
                            <td>Wins</td>
                            <td>{{ data.performance.wins }}</td>
                            <td>{{ "%.1f"|format((data.performance.wins / data.performance.total_trades * 100) if data.performance.total_trades > 0 else 0) }}%</td>
                        </tr>
                        <tr>
                            <td>Losses</td>
                            <td>{{ data.performance.losses }}</td>
                            <td>{{ "%.1f"|format((data.performance.losses / data.performance.total_trades * 100) if data.performance.total_trades > 0 else 0) }}%</td>
                        </tr>
                        <tr>
                            <td>Active</td>
                            <td>{{ data.performance.active_trades }}</td>
                            <td>{{ "%.1f"|format((data.performance.active_trades / data.performance.total_trades * 100) if data.performance.total_trades > 0 else 0) }}%</td>
                        </tr>
                    </table>
                </div>
                
                {% if data.performance.common_mistakes %}
                <div class="section">
                    <h2>Areas for Improvement</h2>
                    {% for mistake in data.performance.common_mistakes %}
                    <div class="list-item">• {{ mistake }}</div>
                    {% endfor %}
                </div>
                {% endif %}
                
                {% if data.performance.profitable_setups %}
                <div class="section">
                    <h2>Most Profitable Setups</h2>
                    {% for setup in data.performance.profitable_setups %}
                    <div class="list-item">• {{ setup }}</div>
                    {% endfor %}
                </div>
                {% endif %}
                
                <div class="section">
                    <h2>Recent Trades</h2>
                    <table>
                        <tr>
                            <th>Date</th>
                            <th>Symbol</th>
                            <th>Entry</th>
                            <th>Exit</th>
                            <th>P&L</th>
                            <th>Outcome</th>
                        </tr>
                        {% for trade in data.trades[:10] %}
                        <tr>
                            <td>{{ trade.created_at.strftime('%m/%d') }}</td>
                            <td>{{ trade.symbol }}</td>
                            <td>${{ "%.2f"|format(trade.entry_price) }}</td>
                            <td>{{ ("$%.2f"|format(trade.exit_price)) if trade.exit_price else '-' }}</td>
                            <td class="{{ 'positive' if trade.pnl and trade.pnl > 0 else 'negative' if trade.pnl and trade.pnl < 0 else '' }}">
                                {{ ("$%.2f"|format(trade.pnl)) if trade.pnl else '-' }}
                            </td>
                            <td>{{ trade.outcome or 'Active' }}</td>
                        </tr>
                        {% endfor %}
                    </table>
                </div>
                
                <div style="text-align: center; margin-top: 40px; color: #666; font-size: 12px;">
                    Generated on {{ data.report_date.strftime('%B %d, %Y at %I:%M %p') }}
                </div>
            </body>
            </html>
            """
            
            template = Template(template_str)
            return template.render(data=data)
            
        except Exception as e:
            logging.error(f"Error generating HTML report: {e}")
            return "<html><body><h1>Error generating report</h1></body></html>"
