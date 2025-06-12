from flask import render_template, request, jsonify, redirect, url_for, flash
from app import app, db
from models import Stock, TradeJournal, ForecastPath, AIAnalysis
from stock_scanner import StockScanner
from forecasting_engine import ForecastingEngine
from ai_coach import AICoach
from confidence_scorer import ConfidenceScorer
from google_sheets_integration import GoogleSheetsIntegration
from pdf_generator import PDFGenerator
import json
import logging

# Initialize components
stock_scanner = StockScanner()
forecasting_engine = ForecastingEngine()
ai_coach = AICoach()
confidence_scorer = ConfidenceScorer()
sheets_integration = GoogleSheetsIntegration()
pdf_generator = PDFGenerator()

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
    return render_template('scanner.html', stocks=stocks)

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
    return render_template('journal.html', trades=trades, tracked_stocks=tracked_stocks)

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
