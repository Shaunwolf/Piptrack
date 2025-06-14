from flask import render_template, request, jsonify, redirect, url_for, flash
from app import app, db
from models import Stock, TradeJournal, ForecastPath, AIAnalysis, PatternEvolution
from stock_scanner import StockScanner
from forecasting_engine import ForecastingEngine
from ai_coach import AICoach
from confidence_scorer import ConfidenceScorer
from google_sheets_integration import GoogleSheetsIntegration
from pdf_generator import PDFGenerator
from pattern_evolution_tracker import PatternEvolutionTracker
import json
import logging
from datetime import datetime

# Initialize performance optimizer
try:
    from performance_optimizer import optimize_route, perf_optimizer
    PERFORMANCE_OPTIMIZED = True
    # Preload common symbols for better performance
    common_symbols = ['AAPL', 'META', 'NVDA', 'TSLA', 'MSFT']
    def preload_symbols():
        try:
            for symbol in common_symbols:
                if sparklines_engine:
                    sparklines_engine.generate_sparkline(symbol)
        except Exception as e:
            logging.warning(f"Failed to preload symbols: {e}")
    
    # Run preload in background
    perf_optimizer.background_task(preload_symbols)
except ImportError:
    PERFORMANCE_OPTIMIZED = False
    def optimize_route(func):
        return func

# Initialize components
stock_scanner = StockScanner()
forecasting_engine = ForecastingEngine()
ai_coach = AICoach()
confidence_scorer = ConfidenceScorer()
sheets_integration = GoogleSheetsIntegration()
pdf_generator = PDFGenerator()
pattern_tracker = PatternEvolutionTracker()

# Initialize enhanced components
try:
    from enhanced_journal import EnhancedTradingJournal
    from multi_timeframe_analyzer import MultiTimeframeAnalyzer
    from scanner_widgets import ScannerWidgets
    from physics_market_engine import PhysicsMarketEngine
    from simple_sparklines import SimpleSparklines
    enhanced_journal = EnhancedTradingJournal()
    mtf_analyzer = MultiTimeframeAnalyzer()
    scanner_widgets = ScannerWidgets()
    physics_engine = PhysicsMarketEngine()
    sparklines_engine = SimpleSparklines()
except ImportError as e:
    logging.warning(f"Enhanced components not available: {e}")
    enhanced_journal = None
    mtf_analyzer = None
    scanner_widgets = None
    physics_engine = None
    sparklines_engine = None

@app.route('/')
@optimize_route
def index():
    """Main dashboard"""
    tracked_stocks = Stock.query.filter_by(is_tracked=True).limit(5).all()
    recent_trades = TradeJournal.query.order_by(TradeJournal.created_at.desc()).limit(10).all()
    return render_template('index.html', tracked_stocks=tracked_stocks, recent_trades=recent_trades)

@app.route('/scanner')
def scanner():
    """Stock scanner page"""
    stocks = Stock.query.order_by(Stock.confidence_score.desc()).all()
    # Convert stocks to dictionaries for JSON serialization
    stocks_data = []
    for stock in stocks:
        stocks_data.append({
            'id': stock.id,
            'symbol': stock.symbol,
            'name': stock.name,
            'price': stock.price,
            'rsi': stock.rsi,
            'volume_spike': stock.volume_spike,
            'pattern_type': stock.pattern_type,
            'fibonacci_position': stock.fibonacci_position,
            'confidence_score': stock.confidence_score,
            'is_tracked': stock.is_tracked,
            'created_at': stock.created_at.isoformat() if stock.created_at else None,
            'updated_at': stock.updated_at.isoformat() if stock.updated_at else None
        })
    return render_template('scanner.html', stocks=stocks_data)

@app.route('/scan_stocks', methods=['POST'])
def scan_stocks():
    """Scan for top gappers or selected tickers"""
    try:
        scan_type = request.json.get('type', 'gappers')
        tickers = request.json.get('tickers', [])
        
        if scan_type == 'gappers':
            results = stock_scanner.scan_top_gappers(limit=50)
        else:
            results = stock_scanner.scan_selected_tickers(tickers)
        
        # Update database with scan results and calculate confidence scores
        for result in results:
            # Calculate confidence score using the result data
            confidence_score = confidence_scorer.calculate_score(result)
            
            stock = Stock.query.filter_by(symbol=result['symbol']).first()
            if not stock:
                stock = Stock(symbol=result['symbol'])
                db.session.add(stock)
            
            stock.name = result.get('name', '')
            stock.price = float(result.get('price', 0))
            stock.rsi = float(result.get('rsi', 0))
            stock.volume_spike = float(result.get('volume_spike', 0))
            stock.pattern_type = result.get('pattern_type', '')
            stock.fibonacci_position = float(result.get('fibonacci_position', 0))
            stock.confidence_score = float(confidence_score)
            
            # Add confidence score to result for display
            result['confidence_score'] = confidence_score
        
        db.session.commit()
        return jsonify({'success': True, 'results': results})
    
    except Exception as e:
        logging.error(f"Error scanning stocks: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/track_stock/<symbol>')
def track_stock(symbol):
    """Add stock to tracked list (Top 5)"""
    try:
        # First, check if we already have 5 tracked stocks
        tracked_count = Stock.query.filter_by(is_tracked=True).count()
        
        stock = Stock.query.filter_by(symbol=symbol).first()
        if not stock:
            return jsonify({'error': 'Stock not found'}), 404
        
        if tracked_count >= 5 and not stock.is_tracked:
            return jsonify({'error': 'Maximum 5 stocks can be tracked'}), 400
        
        stock.is_tracked = True
        db.session.commit()
        
        return jsonify({'success': True, 'message': f'{symbol} added to tracking'})
    
    except Exception as e:
        logging.error(f"Error tracking stock: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/forecast/<symbol>')
def forecast(symbol):
    """Forecast page for specific stock"""
    symbol = symbol.upper()
    
    # Try to get stock data first to validate ticker
    try:
        scanner = StockScanner()
        stock_data = scanner.get_stock_data(symbol)
        
        if not stock_data or stock_data.get('error'):
            # Create a user-friendly error page
            error_message = f"Unable to find data for ticker '{symbol}'"
            suggestions = [
                "Check if the ticker symbol is correct",
                "The stock may be delisted or suspended", 
                "OTC/Pink Sheet stocks have limited data",
                "Try a different ticker symbol"
            ]
            
            return render_template('ticker_error.html', 
                                 symbol=symbol, 
                                 error_message=error_message,
                                 suggestions=suggestions)
        
        # Get or create stock entry
        stock = Stock.query.filter_by(symbol=symbol).first()
        if not stock:
            # Create new stock entry with the validated data
            from confidence_scorer import ConfidenceScorer
            confidence_scorer = ConfidenceScorer()
            confidence_score = confidence_scorer.calculate_score(stock_data)
            
            stock = Stock(
                symbol=symbol,
                name=stock_data.get('name', 'Unknown Company'),
                price=stock_data.get('price', 0),
                rsi=stock_data.get('rsi', 50),
                volume_spike=stock_data.get('volume_spike', 0),
                pattern_type=stock_data.get('pattern_type', 'Unknown'),
                fibonacci_position=stock_data.get('fibonacci_position', 50),
                confidence_score=confidence_score
            )
            db.session.add(stock)
            db.session.commit()
        
        # Generate forecast paths
        forecast_paths = forecasting_engine.generate_spaghetti_model(symbol)
        ai_analysis = ai_coach.analyze_setup(symbol)
        
        return render_template('forecast.html', stock=stock, forecast_paths=forecast_paths, ai_analysis=ai_analysis)
        
    except Exception as e:
        logging.error(f"Error in forecast route for {symbol}: {e}")
        error_message = f"Unable to analyze ticker '{symbol}' due to a data retrieval error"
        suggestions = [
            "Verify the ticker symbol is correct",
            "Try again in a few moments",
            "Use the scanner to find valid tickers",
            "Search for a different stock symbol"
        ]
        
        return render_template('ticker_error.html', 
                             symbol=symbol, 
                             error_message=error_message,
                             suggestions=suggestions)

@app.route('/generate_forecast', methods=['POST'])
def generate_forecast():
    """Generate spaghetti model forecast"""
    try:
        symbol = request.json.get('symbol')
        if not symbol:
            return jsonify({'error': 'Symbol required'}), 400
        
        # Generate forecast paths
        paths = forecasting_engine.generate_spaghetti_model(symbol)
        
        # Store in database
        ForecastPath.query.filter_by(symbol=symbol).delete()
        
        for path in paths:
            forecast_path = ForecastPath(
                symbol=symbol,
                path_type=path['type'],
                probability=path['probability'],
                price_targets=path['targets'],
                risk_zones=path['risk_zones']
            )
            db.session.add(forecast_path)
        
        db.session.commit()
        
        return jsonify({'success': True, 'paths': paths})
    
    except Exception as e:
        logging.error(f"Error generating forecast: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/journal')
def journal():
    """Trade journal page"""
    trades = TradeJournal.query.order_by(TradeJournal.created_at.desc()).all()
    tracked_stocks = Stock.query.filter_by(is_tracked=True).all()
    
    # Convert trades to dictionaries for JSON serialization
    trades_data = []
    for trade in trades:
        trades_data.append({
            'id': trade.id,
            'symbol': trade.symbol,
            'entry_price': trade.entry_price,
            'stop_loss': trade.stop_loss,
            'take_profit': trade.take_profit,
            'pattern_confirmed': trade.pattern_confirmed,
            'screenshot_taken': trade.screenshot_taken,
            'reflection': trade.reflection,
            'perfect_trade': trade.perfect_trade,
            'confidence_at_entry': trade.confidence_at_entry,
            'outcome': trade.outcome,
            'exit_price': trade.exit_price,
            'pnl': trade.pnl,
            'lessons_learned': trade.lessons_learned,
            'created_at': trade.created_at.isoformat() if trade.created_at else None,
            'updated_at': trade.updated_at.isoformat() if trade.updated_at else None
        })
    
    return render_template('journal_clean.html', trades=trades_data, tracked_stocks=tracked_stocks)

@app.route('/journal/save', methods=['POST'])
def save_journal_entry():
    """Save journal entry from clean journal interface"""
    try:
        data = request.json
        
        # Create new journal entry
        trade = TradeJournal(
            symbol=data.get('symbol', 'JOURNAL'),
            entry_price=float(data.get('entry_price', 0)),
            stop_loss=float(data.get('stop_loss', 0)),
            take_profit=float(data.get('take_profit', 0)),
            pattern_confirmed=data.get('pattern_confirmed', False),
            screenshot_taken=data.get('screenshot_taken', False),
            reflection=data.get('tradeHighlights', ''),
            perfect_trade=data.get('perfect_trade', False),
            confidence_at_entry=float(data.get('confidence', 50)),
            lessons_learned=data.get('keyLearnings', ''),
            outcome='journal_entry'
        )
        
        db.session.add(trade)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Journal entry saved successfully'})
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error saving journal entry: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/add_trade', methods=['POST'])
def add_trade():
    """Add new trade to journal with enhanced Lisa Frank journal data"""
    try:
        data = request.json
        
        # Handle both old format (individual trades) and new format (journal entries)
        if 'mood' in data:
            # New Lisa Frank journal entry format
            trade = TradeJournal(
                symbol=data.get('symbol', 'JOURNAL'),  # Use JOURNAL as default for mood entries
                entry_price=float(data.get('entry_price', 0)),
                stop_loss=float(data.get('stop_loss', 0)),
                take_profit=float(data.get('take_profit', 0)),
                pattern_confirmed=data.get('pattern_confirmed', False),
                screenshot_taken=data.get('screenshot_taken', False),
                reflection=data.get('highlights', ''),
                perfect_trade=data.get('perfect_trade', False),
                confidence_at_entry=float(data.get('confidence', 50)),
                lessons_learned=data.get('learnings', ''),
                # Store additional journal data as JSON in reflection field
                outcome='journal_entry'  # Mark as journal entry vs trade
            )
            
            # Create extended reflection with mood and behavior data
            journal_data = {
                'mood': data.get('mood'),
                'behaviors': data.get('behaviors', []),
                'num_trades': data.get('numTrades'),
                'win_rate': data.get('winRate'),
                'rr_ratio': data.get('rrRatio'),
                'stickers': data.get('stickers', []),
                'theme': data.get('theme', 'bubblegum'),
                'highlights': data.get('highlights', ''),
                'learnings': data.get('learnings', '')
            }
            
            trade.reflection = f"Mood: {data.get('mood', 'unknown')} | Behaviors: {', '.join(data.get('behaviors', []))} | {data.get('highlights', '')}"
            
        else:
            # Original trade format
            trade = TradeJournal(
                symbol=data['symbol'],
                entry_price=float(data['entry_price']),
                stop_loss=float(data['stop_loss']),
                take_profit=float(data['take_profit']),
                pattern_confirmed=data.get('pattern_confirmed', False),
                screenshot_taken=data.get('screenshot_taken', False),
                reflection=data.get('reflection', ''),
                perfect_trade=data.get('perfect_trade', False),
                confidence_at_entry=float(data.get('confidence_at_entry', 0))
            )
        
        db.session.add(trade)
        db.session.commit()
        
        # Submit to Google Sheets if it's a regular trade
        if 'mood' not in data:
            try:
                sheets_integration.submit_trade(trade)
            except Exception as sheets_error:
                logging.warning(f"Could not submit to Google Sheets: {sheets_error}")
        
        return jsonify({'success': True, 'message': 'Entry saved successfully!'})
    
    except Exception as e:
        logging.error(f"Error adding trade/journal entry: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/ai_review/<symbol>')
def ai_review(symbol):
    """Get AI analysis for a stock"""
    try:
        analysis = ai_coach.analyze_setup(symbol)
        return jsonify({'success': True, 'analysis': analysis})
    
    except Exception as e:
        logging.error(f"Error getting AI review: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/update_confidence_scores', methods=['POST'])
def update_confidence_scores():
    """Update confidence scores for tracked stocks"""
    try:
        tracked_stocks = Stock.query.filter_by(is_tracked=True).all()
        updated_scores = []
        
        for stock in tracked_stocks:
            # Get latest data
            stock_data = stock_scanner.get_stock_data(stock.symbol)
            new_score = confidence_scorer.calculate_score(stock_data)
            
            stock.confidence_score = new_score
            updated_scores.append({
                'symbol': stock.symbol,
                'score': new_score
            })
            
            # Trigger voice alert if score is high
            if new_score >= 80:
                ai_coach.trigger_voice_alert(stock.symbol, new_score)
        
        db.session.commit()
        
        return jsonify({'success': True, 'scores': updated_scores})
    
    except Exception as e:
        logging.error(f"Error updating confidence scores: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/export_weekly_report')
def export_weekly_report():
    """Generate and download weekly PDF report"""
    try:
        pdf_path = pdf_generator.generate_weekly_report()
        return jsonify({'success': True, 'pdf_url': f'/static/reports/{pdf_path}'})
    
    except Exception as e:
        logging.error(f"Error generating weekly report: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/chart_story/<symbol>')
def chart_story(symbol):
    """Get chart story comments for hover functionality"""
    try:
        story = ai_coach.generate_chart_story(symbol)
        return jsonify({'success': True, 'story': story})
    
    except Exception as e:
        logging.error(f"Error getting chart story: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/pattern_evolution/<symbol>')
def pattern_evolution_analysis(symbol):
    """Get pattern evolution tracking and breakout timing predictions"""
    try:
        evolution_data = pattern_tracker.track_pattern_evolution(symbol)
        
        if evolution_data:
            # Store in database
            for pattern in evolution_data['patterns']:
                existing = PatternEvolution.query.filter_by(
                    symbol=symbol, 
                    pattern_type=pattern['pattern_type']
                ).first()
                
                breakout_pred = pattern['breakout_prediction']
                evolution = pattern['evolution']
                
                if existing:
                    # Update existing record with numpy conversion
                    existing.confidence_score = float(pattern['confidence'])
                    existing.stage = pattern['current_stage']
                    existing.completion_percentage = float(pattern['completion_percentage'])
                    existing.time_in_pattern = int(pattern['time_in_pattern'])
                    existing.volatility_trend = float(evolution.get('volatility_trend', 0))
                    existing.volume_trend = float(evolution.get('volume_trend', 0))
                    existing.momentum_change = float(evolution.get('momentum_change', 0))
                    existing.support_resistance_strength = float(evolution.get('support_resistance_strength', 0))
                    existing.estimated_days_to_breakout = int(breakout_pred.get('estimated_days_to_breakout', 7))
                    existing.breakout_probability_5_days = float(breakout_pred.get('breakout_probability_next_5_days', 0))
                    existing.breakout_probability_10_days = float(breakout_pred.get('breakout_probability_next_10_days', 0))
                    existing.direction_bias = float(breakout_pred.get('direction_bias', 0.5))
                    existing.timing_confidence = float(breakout_pred.get('timing_confidence', 0.5))
                    existing.updated_at = datetime.utcnow()
                else:
                    # Create new record with numpy conversion
                    new_evolution = PatternEvolution(
                        symbol=symbol,
                        pattern_type=pattern['pattern_type'],
                        confidence_score=float(pattern['confidence']),
                        stage=pattern['current_stage'],
                        completion_percentage=float(pattern['completion_percentage']),
                        time_in_pattern=int(pattern['time_in_pattern']),
                        volatility_trend=float(evolution.get('volatility_trend', 0)),
                        volume_trend=float(evolution.get('volume_trend', 0)),
                        momentum_change=float(evolution.get('momentum_change', 0)),
                        support_resistance_strength=float(evolution.get('support_resistance_strength', 0)),
                        estimated_days_to_breakout=int(breakout_pred.get('estimated_days_to_breakout', 7)),
                        breakout_probability_5_days=float(breakout_pred.get('breakout_probability_next_5_days', 0)),
                        breakout_probability_10_days=float(breakout_pred.get('breakout_probability_next_10_days', 0)),
                        direction_bias=float(breakout_pred.get('direction_bias', 0.5)),
                        timing_confidence=float(breakout_pred.get('timing_confidence', 0.5)),
                        pattern_data=breakout_pred.get('key_levels', {})
                    )
                    db.session.add(new_evolution)
                
                db.session.commit()
            
            return jsonify({'success': True, 'evolution': evolution_data})
        else:
            return jsonify({'success': False, 'message': 'No patterns detected'})
            
    except Exception as e:
        logging.error(f"Error analyzing pattern evolution for {symbol}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/pattern_evolution/all')
def all_pattern_evolutions():
    """Get pattern evolution data for all tracked stocks"""
    try:
        tracked_stocks = Stock.query.filter_by(is_tracked=True).all()
        all_evolutions = {}
        
        for stock in tracked_stocks:
            latest_evolution = PatternEvolution.query.filter_by(
                symbol=stock.symbol
            ).order_by(PatternEvolution.updated_at.desc()).first()
            
            if latest_evolution:
                all_evolutions[stock.symbol] = {
                    'pattern_type': latest_evolution.pattern_type,
                    'confidence_score': latest_evolution.confidence_score,
                    'stage': latest_evolution.stage,
                    'completion_percentage': latest_evolution.completion_percentage,
                    'estimated_days_to_breakout': latest_evolution.estimated_days_to_breakout,
                    'breakout_probability_5_days': latest_evolution.breakout_probability_5_days,
                    'direction_bias': latest_evolution.direction_bias,
                    'timing_confidence': latest_evolution.timing_confidence,
                    'updated_at': latest_evolution.updated_at.isoformat()
                }
        
        return jsonify({'success': True, 'evolutions': all_evolutions})
        
    except Exception as e:
        logging.error(f"Error getting all pattern evolutions: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/sparkline/<symbol>')
def get_sparkline_data(symbol):
    """Get enhanced animated sparkline data for a stock symbol"""
    try:
        if sparklines_engine is None:
            # Fallback to basic implementation
            import yfinance as yf
            from datetime import datetime, timedelta
            
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="7d", interval="1d")
            
            if hist.empty:
                return jsonify({
                    'error': 'No data available',
                    'symbol': symbol
                }), 404
            
            prices = hist['Close'].tolist()
            dates = [date.strftime('%Y-%m-%d') for date in hist.index]
            
            if len(prices) >= 2:
                change = ((prices[-1] - prices[0]) / prices[0]) * 100
            else:
                change = 0
        else:
            # Use enhanced animated sparklines engine
            period = request.args.get('period', '1d')
            interval = request.args.get('interval', '5m')
            
            sparkline_data = sparklines_engine.generate_sparkline(symbol)
            
            if 'error' in sparkline_data:
                return jsonify({
                    'error': sparkline_data['error'],
                    'symbol': symbol
                }), 404
            
            # Convert to format expected by existing frontend
            prices = sparkline_data['prices']
            import pandas as pd
            dates = [pd.Timestamp(ts, unit='ms').strftime('%Y-%m-%d') for ts in sparkline_data['timestamps']]
            change = sparkline_data['price_change_pct']
            
            # Add enhanced sparkline features to response
            response = {
                'symbol': symbol,
                'prices': prices,
                'dates': dates,
                'change': round(change, 2),
                'high': round(max(prices), 2),
                'low': round(min(prices), 2)
            }
            
            # Include CandleCast candle guy features
            response.update({
                'candle_guy_mood': sparkline_data.get('candle_guy_mood', 'neutral'),
                'animation_speed': sparkline_data.get('animation_speed', 1.0),
                'price_change_pct': sparkline_data.get('price_change_pct', 0),
                'volatility_score': sparkline_data.get('volatility_score', 0),
                'trend_direction': sparkline_data.get('trend_direction', 'flat'),
                'volume_trend': sparkline_data.get('volume_trend', 'stable')
            })
            
            return jsonify(response)
        
        # Basic fallback response format
        return jsonify({
            'symbol': symbol,
            'prices': prices,
            'dates': dates,
            'change': round(change, 2),
            'high': round(max(prices), 2),
            'low': round(min(prices), 2)
        })
        
    except Exception as e:
        logging.error(f"Error fetching sparkline data for {symbol}: {e}")
        return jsonify({
            'error': str(e),
            'symbol': symbol
        }), 500

@app.route('/update_pattern_evolutions', methods=['POST'])
def update_pattern_evolutions():
    """Update pattern evolution data for all tracked stocks"""
    try:
        tracked_stocks = Stock.query.filter_by(is_tracked=True).all()
        updated_count = 0
        
        for stock in tracked_stocks:
            try:
                evolution_data = pattern_tracker.track_pattern_evolution(stock.symbol)
                if evolution_data and evolution_data['patterns']:
                    updated_count += 1
                
            except Exception as stock_error:
                logging.error(f"Error updating pattern evolution for {stock.symbol}: {stock_error}")
                continue
        
        return jsonify({
            'success': True, 
            'message': f'Updated pattern evolution for {updated_count} stocks',
            'updated_count': updated_count
        })
        
    except Exception as e:
        logging.error(f"Error updating pattern evolutions: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/pattern_dashboard')
def pattern_dashboard():
    """Pattern evolution dashboard page"""
    try:
        # Get all stocks with pattern evolution data
        pattern_stocks = []
        
        all_stocks = Stock.query.all()
        
        for stock in all_stocks:
            recent_evolution = PatternEvolution.query.filter_by(
                symbol=stock.symbol
            ).order_by(PatternEvolution.updated_at.desc()).first()
            
            if recent_evolution:
                pattern_stocks.append({
                    'stock': stock,
                    'evolution': recent_evolution
                })
        
        return render_template('pattern_dashboard.html', pattern_stocks=pattern_stocks)
        
    except Exception as e:
        logging.error(f"Error loading pattern dashboard: {e}")
        return redirect(url_for('index'))

# Scanner Widget Routes

@app.route('/widgets')
def widget_dashboard():
    """Scanner widget dashboard page"""
    try:
        if scanner_widgets is None:
            return render_template('widget_dashboard.html', widgets=[], error="Widget system not available")
        
        widgets = scanner_widgets.get_widget_presets()
        return render_template('widget_dashboard.html', widgets=widgets)
        
    except Exception as e:
        logging.error(f"Error loading widget dashboard: {e}")
        return render_template('widget_dashboard.html', widgets=[], error=str(e))

@app.route('/api/widgets')
def get_widget_presets():
    """Get all widget presets"""
    try:
        if scanner_widgets is None:
            return jsonify({'success': False, 'error': 'Widget system not available'})
        
        widgets = scanner_widgets.get_widget_presets()
        return jsonify({'success': True, 'widgets': widgets})
        
    except Exception as e:
        logging.error(f"Error getting widget presets: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/widgets/<widget_id>/scan')
def run_widget_scan(widget_id):
    """Run a specific widget scan"""
    try:
        if scanner_widgets is None:
            return jsonify({'success': False, 'error': 'Widget system not available'})
        
        limit = request.args.get('limit', 10, type=int)
        result = scanner_widgets.run_widget_scan(widget_id, limit)
        
        return jsonify(result)
        
    except Exception as e:
        logging.error(f"Error running widget scan {widget_id}: {e}")
        return jsonify({'success': False, 'error': str(e)})

# Physics-Based Market Analysis Routes

@app.route('/physics/<symbol>')
def physics_analysis(symbol):
    """Physics-based stock analysis page"""
    return render_template('physics_analysis.html', symbol=symbol.upper())

@app.route('/api/physics/gravity/<symbol>')
def gravity_wells_analysis(symbol):
    """Get gravitational wells analysis"""
    try:
        if physics_engine is None:
            return jsonify({'success': False, 'error': 'Physics engine not available'})
        
        analysis = physics_engine.analyze_gravity_wells(symbol)
        
        if 'error' in analysis:
            return jsonify({'success': False, 'error': analysis['error']})
        
        return jsonify({'success': True, 'analysis': analysis})
        
    except Exception as e:
        logging.error(f"Error in gravity wells analysis for {symbol}: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/physics/momentum/<symbol>')
def momentum_particles_analysis(symbol):
    """Get momentum particles simulation"""
    try:
        if physics_engine is None:
            return jsonify({'success': False, 'error': 'Physics engine not available'})
        
        analysis = physics_engine.simulate_momentum_particles(symbol)
        
        if 'error' in analysis:
            return jsonify({'success': False, 'error': analysis['error']})
        
        return jsonify({'success': True, 'analysis': analysis})
        
    except Exception as e:
        logging.error(f"Error in momentum particles analysis for {symbol}: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/physics/magnetic/<symbol>')
def magnetic_fields_analysis(symbol):
    """Get magnetic fields analysis"""
    try:
        if physics_engine is None:
            return jsonify({'success': False, 'error': 'Physics engine not available'})
        
        analysis = physics_engine.analyze_magnetic_fields(symbol)
        
        if 'error' in analysis:
            return jsonify({'success': False, 'error': analysis['error']})
        
        return jsonify({'success': True, 'analysis': analysis})
        
    except Exception as e:
        logging.error(f"Error in magnetic fields analysis for {symbol}: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/physics/weather/<symbol>')
def weather_patterns_analysis(symbol):
    """Get weather patterns simulation"""
    try:
        if physics_engine is None:
            return jsonify({'success': False, 'error': 'Physics engine not available'})
        
        analysis = physics_engine.simulate_weather_patterns(symbol)
        
        if 'error' in analysis:
            return jsonify({'success': False, 'error': analysis['error']})
        
        return jsonify({'success': True, 'analysis': analysis})
        
    except Exception as e:
        logging.error(f"Error in weather patterns analysis for {symbol}: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/physics/quantum/<symbol>')
def quantum_tunneling_analysis(symbol):
    """Get quantum tunneling analysis"""
    try:
        if physics_engine is None:
            return jsonify({'success': False, 'error': 'Physics engine not available'})
        
        analysis = physics_engine.calculate_quantum_tunneling(symbol)
        
        if 'error' in analysis:
            return jsonify({'success': False, 'error': analysis['error']})
        
        return jsonify({'success': True, 'analysis': analysis})
        
    except Exception as e:
        logging.error(f"Error in quantum tunneling analysis for {symbol}: {e}")
        return jsonify({'success': False, 'error': str(e)})

# Enhanced Animated Sparklines Routes

@app.route('/api/sparkline/summary/<symbol>')
def get_sparkline_summary(symbol):
    """Get condensed sparkline summary for dashboard widgets"""
    try:
        if sparklines_engine is None:
            return jsonify({'success': False, 'error': 'Sparklines engine not available'})
        
        # Use the simple sparkline generator for summary data
        sparkline_data = sparklines_engine.generate_sparkline(symbol)
        if 'error' in sparkline_data:
            return jsonify({'success': False, 'error': sparkline_data['error']})
        
        # Create summary from sparkline data
        summary = {
            'symbol': symbol,
            'current_price': sparkline_data.get('current_price', 0),
            'price_change': sparkline_data.get('price_change', 0),
            'price_change_pct': sparkline_data.get('price_change_pct', 0),
            'candle_guy_mood': sparkline_data.get('candle_guy_mood', 'neutral'),
            'trend_direction': sparkline_data.get('trend_direction', 'flat'),
            'volatility_score': sparkline_data.get('volatility_score', 0)
        }
        
        if 'error' in summary:
            return jsonify({'success': False, 'error': summary['error']})
        
        return jsonify({'success': True, 'summary': summary})
        
    except Exception as e:
        logging.error(f"Error getting sparkline summary for {symbol}: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/sparklines/multiple')
@optimize_route
def get_multiple_sparklines():
    """Get sparklines for multiple symbols"""
    try:
        if sparklines_engine is None:
            return jsonify({'success': False, 'error': 'Sparklines engine not available'})
        
        symbols = request.args.get('symbols', '').split(',')
        symbols = [s.strip().upper() for s in symbols if s.strip()][:3]  # Limit to 3 symbols
        
        if not symbols:
            return jsonify({'success': False, 'error': 'No symbols provided'})
        
        period = request.args.get('period', '1d')
        interval = request.args.get('interval', '15m')
        
        # Use individual sparkline generation with better error handling
        sparklines_data = {}
        for symbol in symbols:
            try:
                data = sparklines_engine.generate_sparkline(symbol)
                if data and not data.get('error'):
                    sparklines_data[symbol] = data
                else:
                    sparklines_data[symbol] = {'error': 'No data available'}
            except Exception as e:
                logging.warning(f"Failed to get sparkline for {symbol}: {e}")
                sparklines_data[symbol] = {'error': 'Data unavailable'}
        
        return jsonify({'success': True, 'data': sparklines_data})
        
    except Exception as e:
        logging.error(f"Error getting multiple sparklines: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/sparklines/cache/stats')
def get_sparklines_cache_stats():
    """Get sparklines cache statistics"""
    try:
        if sparklines_engine is None:
            return jsonify({'success': False, 'error': 'Sparklines engine not available'})
        
        stats = sparklines_engine.get_cache_stats()
        return jsonify({'success': True, 'cache_stats': stats})
        
    except Exception as e:
        logging.error(f"Error getting cache stats: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/sparklines/cache/clear', methods=['POST'])
def clear_sparklines_cache():
    """Clear sparklines cache"""
    try:
        if sparklines_engine is None:
            return jsonify({'success': False, 'error': 'Sparklines engine not available'})
        
        sparklines_engine.clear_cache()
        return jsonify({'success': True, 'message': 'Cache cleared successfully'})
        
    except Exception as e:
        logging.error(f"Error clearing cache: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/historical-comparison/<symbol>')
def get_historical_comparison_api(symbol):
    """Get enhanced historical comparison with comprehensive scoring"""
    try:
        from historical_comparison_engine import HistoricalComparisonEngine
        
        engine = HistoricalComparisonEngine()
        matches = engine.find_historical_matches(symbol.upper(), lookback_days=504)
        
        if not matches:
            return jsonify({
                'success': False,
                'message': 'No significant historical matches found',
                'total_matches': 0,
                'symbol': symbol.upper()
            })
        
        # Get detailed analysis
        detailed_analysis = engine.get_detailed_analysis(matches)
        
        # Format response with comprehensive scoring data
        response_data = {
            'success': True,
            'symbol': symbol.upper(),
            'total_matches_found': len(matches),
            'analysis_summary': detailed_analysis,
            'top_matches': []
        }
        
        # Add top 10 matches with full scoring breakdown
        for match in matches[:10]:
            match_data = {
                'symbol': match.symbol,
                'date_range': match.date_range,
                'confidence_level': match.confidence_level,
                'scoring_breakdown': {
                    'composite_score': round(match.composite_score * 100, 1),
                    'price_correlation': round(match.price_correlation * 100, 1),
                    'volume_correlation': round(match.volume_correlation * 100, 1),
                    'technical_score': round(match.technical_score * 100, 1),
                    'pattern_match_score': round(match.pattern_match_score * 100, 1),
                    'news_sentiment_score': round(match.news_sentiment_score * 100, 1),
                    'market_condition_score': round(match.market_condition_score * 100, 1)
                },
                'key_metrics': match.key_metrics,
                'outcome': match.outcome,
                'factors_matched': []
            }
            
            # Identify key factors that contributed to high scores
            if match.price_correlation > 0.8:
                match_data['factors_matched'].append('Strong price correlation')
            if match.volume_correlation > 0.7:
                match_data['factors_matched'].append('Similar volume patterns')
            if match.technical_score > 0.8:
                match_data['factors_matched'].append('Technical indicators aligned')
            if match.pattern_match_score > 0.8:
                match_data['factors_matched'].append('Chart patterns match')
            if match.news_sentiment_score > 0.7:
                match_data['factors_matched'].append('Similar market sentiment')
            if match.market_condition_score > 0.7:
                match_data['factors_matched'].append('Comparable market conditions')
            
            response_data['top_matches'].append(match_data)
        
        return jsonify(response_data)
        
    except Exception as e:
        logging.error(f"Error in historical comparison API: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Historical comparison analysis failed'
        }), 500
