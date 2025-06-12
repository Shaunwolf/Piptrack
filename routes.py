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

# Initialize components
stock_scanner = StockScanner()
forecasting_engine = ForecastingEngine()
ai_coach = AICoach()
confidence_scorer = ConfidenceScorer()
sheets_integration = GoogleSheetsIntegration()
pdf_generator = PDFGenerator()
pattern_tracker = PatternEvolutionTracker()

@app.route('/')
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
            results = stock_scanner.scan_top_gappers()
        else:
            results = stock_scanner.scan_selected_tickers(tickers)
        
        # Update database with scan results
        for result in results:
            stock = Stock.query.filter_by(symbol=result['symbol']).first()
            if not stock:
                stock = Stock(symbol=result['symbol'])
                db.session.add(stock)
            
            stock.name = result.get('name', '')
            stock.price = result.get('price', 0)
            stock.rsi = result.get('rsi', 0)
            stock.volume_spike = result.get('volume_spike', 0)
            stock.pattern_type = result.get('pattern_type', '')
            stock.fibonacci_position = result.get('fibonacci_position', 0)
            stock.confidence_score = confidence_scorer.calculate_score(result)
        
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
    stock = Stock.query.filter_by(symbol=symbol).first()
    if not stock:
        flash(f'Stock {symbol} not found', 'error')
        return redirect(url_for('scanner'))
    
    # Generate forecast paths
    forecast_paths = forecasting_engine.generate_spaghetti_model(symbol)
    ai_analysis = ai_coach.analyze_setup(symbol)
    
    return render_template('forecast.html', stock=stock, forecast_paths=forecast_paths, ai_analysis=ai_analysis)

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
    
    return render_template('journal.html', trades=trades_data, tracked_stocks=tracked_stocks)

@app.route('/add_trade', methods=['POST'])
def add_trade():
    """Add new trade to journal"""
    try:
        data = request.json
        
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
        
        # Submit to Google Sheets
        sheets_integration.submit_trade(trade)
        
        return jsonify({'success': True, 'message': 'Trade added to journal'})
    
    except Exception as e:
        logging.error(f"Error adding trade: {e}")
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
                    # Create new record
                    new_evolution = PatternEvolution(
                        symbol=symbol,
                        pattern_type=pattern['pattern_type'],
                        confidence_score=pattern['confidence'],
                        stage=pattern['current_stage'],
                        completion_percentage=pattern['completion_percentage'],
                        time_in_pattern=pattern['time_in_pattern'],
                        volatility_trend=evolution.get('volatility_trend', 0),
                        volume_trend=evolution.get('volume_trend', 0),
                        momentum_change=evolution.get('momentum_change', 0),
                        support_resistance_strength=evolution.get('support_resistance_strength', 0),
                        estimated_days_to_breakout=breakout_pred.get('estimated_days_to_breakout', 7),
                        breakout_probability_5_days=breakout_pred.get('breakout_probability_next_5_days', 0),
                        breakout_probability_10_days=breakout_pred.get('breakout_probability_next_10_days', 0),
                        direction_bias=breakout_pred.get('direction_bias', 0.5),
                        timing_confidence=breakout_pred.get('timing_confidence', 0.5),
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
