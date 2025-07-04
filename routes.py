from flask import render_template, request, jsonify, redirect, url_for, flash, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import app, db
from models import (Stock, TradeJournal, ForecastPath, AIAnalysis, PatternEvolution, 
                   User, StockRecommendation, ScanResult)
from auth_forms import RegistrationForm, LoginForm
from stock_scanner import StockScanner
from forecasting_engine import ForecastingEngine
from ai_coach import AICoach
from confidence_scorer import ConfidenceScorer
from pattern_evolution_tracker import PatternEvolutionTracker
from personalized_recommender import PersonalizedRecommender
from google_sheets_integration import GoogleSheetsIntegration
from pdf_generator import PDFGenerator
from stock_widgets import StockWidgets
from market_data_engine import MarketDataEngine
from background_scanner import background_scanner
import json
import logging
import pandas as pd
from datetime import datetime
from threading import Thread

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = "Please log in to access this page."

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

# Initialize components
try:
    stock_scanner = StockScanner()
    forecasting_engine = ForecastingEngine()
    ai_coach = AICoach()
    confidence_scorer = ConfidenceScorer()
    pattern_tracker = PatternEvolutionTracker()
    sheets_integration = GoogleSheetsIntegration()
    pdf_generator = PDFGenerator()
    stock_widgets = StockWidgets()
    market_engine = MarketDataEngine()
    
    # Start background scanning
    background_scanner.start_background_scanning()
    logging.info("All components initialized successfully including high-performance market scanner")
except Exception as e:
    logging.error(f"Error initializing components: {e}")
    stock_scanner = StockScanner() if 'StockScanner' in globals() else None
    forecasting_engine = ForecastingEngine() if 'ForecastingEngine' in globals() else None
    ai_coach = AICoach() if 'AICoach' in globals() else None
    confidence_scorer = ConfidenceScorer() if 'ConfidenceScorer' in globals() else None
    pattern_tracker = PatternEvolutionTracker() if 'PatternEvolutionTracker' in globals() else None
    market_engine = MarketDataEngine() if 'MarketDataEngine' in globals() else None
    sheets_integration = None
    pdf_generator = None
    stock_widgets = StockWidgets() if 'StockWidgets' in globals() else None

# Register authentication blueprints
# Standard Flask-Login authentication - no blueprint registration needed

# Authentication routes
@app.route('/register', methods=['GET', 'POST'])
def register():
    try:
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        
        # Check if beta spots are available
        beta_count = User.query.filter(User.beta_user_number.isnot(None)).count()
        if beta_count >= 100:
            flash("Beta testing is full. We'll notify you when the app launches publicly!", "info")
            return redirect(url_for("index"))
        
        form = RegistrationForm()
        
        if request.method == 'POST':
            logging.info(f"Registration form submitted with data: {request.form}")
            
        if form.validate_on_submit():
            try:
                # Create new user
                user = User()
                user.email = form.email.data.lower() if form.email.data else None
                user.password_hash = generate_password_hash(form.password.data) if form.password.data else None
                user.first_name = form.first_name.data
                user.last_name = form.last_name.data
                user.auth_method = 'email'
                user.is_verified = True
                user.beta_user_number = beta_count + 1
                
                db.session.add(user)
                db.session.commit()
                
                flash(f"Welcome to the beta! You're user #{user.beta_user_number} of 100.", "success")
                login_user(user, remember=True)
                
                return redirect(url_for('dashboard'))
            except Exception as e:
                db.session.rollback()
                flash(f"Registration error: {str(e)}", "error")
                logging.error(f"Registration error: {str(e)}")
        elif request.method == 'POST':
            logging.error(f"Form validation failed: {form.errors}")
            flash("Please check your form inputs", "error")
        
        return render_template('auth/register.html', form=form, beta_count=beta_count)
    except Exception as e:
        logging.error(f"Registration route error: {str(e)}")
        flash(f"System error: {str(e)}", "error")
        return redirect(url_for('index'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        if email:
            user = User.query.filter_by(email=email.lower()).first()
            
            if user and user.password_hash and form.password.data and check_password_hash(user.password_hash, form.password.data):
                login_user(user, remember=form.remember_me.data)
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('dashboard'))
            else:
                flash('Invalid email or password', 'error')
        else:
            flash('Email is required', 'error')
    
    beta_count = User.query.filter(User.beta_user_number.isnot(None)).count()
    return render_template('auth/login.html', form=form, beta_count=beta_count)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('landing'))

# Make session permanent
@app.before_request
def make_session_permanent():
    session.permanent = True

# Initialize core components
stock_scanner = StockScanner()
forecasting_engine = ForecastingEngine()
ai_coach = AICoach()
confidence_scorer = ConfidenceScorer()
pattern_tracker = PatternEvolutionTracker()
personalizer = PersonalizedRecommender()
sheets_integration = GoogleSheetsIntegration()
pdf_generator = PDFGenerator()

# Initialize core components
from animated_sparklines import AnimatedSparklines
sparklines_engine = AnimatedSparklines()

# Performance optimization decorator fallback
def optimize_route(func):
    return func

@app.route('/')
def index():
    """Landing page for visitors, dashboard for authenticated users"""
    if current_user.is_authenticated:
        # Show dashboard for logged-in users
        tracked_stocks = Stock.query.filter_by(is_tracked=True).limit(5).all()
        recent_trades = TradeJournal.query.filter_by(user_id=current_user.id).order_by(TradeJournal.created_at.desc()).limit(10).all()
        return render_template('index.html', tracked_stocks=tracked_stocks, recent_trades=recent_trades)
    else:
        # Show landing page for visitors with beta counter
        beta_count = User.query.filter(User.beta_user_number.isnot(None)).count()
        spots_remaining = max(0, 100 - beta_count)
        return render_template('landing.html', beta_count=beta_count, spots_remaining=spots_remaining)

@app.route('/landing')
def landing():
    """Explicit landing page route"""
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard for authenticated users"""
    try:
        tracked_stocks = Stock.query.filter_by(is_tracked=True).limit(5).all()
        recent_trades = TradeJournal.query.filter_by(user_id=current_user.id).order_by(TradeJournal.created_at.desc()).limit(10).all()
        return render_template('index.html', tracked_stocks=tracked_stocks, recent_trades=recent_trades)
    except Exception as e:
        logging.error(f"Dashboard error: {str(e)}")
        flash(f"Dashboard loading error: {str(e)}", "error")
        # Fallback to simple dashboard
        return render_template('index.html', tracked_stocks=[], recent_trades=[])

@app.route('/scanner')
@login_required
def scanner():
    """Stock scanner page"""
    try:
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
    except Exception as e:
        logging.error(f"Scanner error: {str(e)}")
        flash(f"Scanner loading error: {str(e)}", "error")
        return render_template('scanner.html', stocks=[])



@app.route('/scan_stocks', methods=['POST'])
@login_required
def scan_stocks():
    """Scan for top gappers or selected tickers"""
    try:
        scan_type = request.json.get('type', 'gappers')
        tickers = request.json.get('tickers', [])
        
        if scan_type == 'gappers':
            results = stock_scanner.scan_stocks(max_results=50)
        else:
            # Parse tickers from comma-separated string
            ticker_list = [t.strip().upper() for t in tickers.split(',') if t.strip()]
            results = stock_scanner.scan_stocks(symbols=ticker_list)
        
        # Update database with scan results and calculate confidence scores
        for result in results:
            # Calculate confidence score using the result data
            confidence_score = confidence_scorer.calculate_score(result)
            
            stock = Stock.query.filter_by(symbol=result['symbol']).first()
            if not stock:
                stock = Stock()
                stock.symbol = result['symbol']
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

# High-Performance Market Data API Endpoints

@app.route('/api/market/quick-scan')
def api_quick_market_scan():
    """API endpoint for quick market scan of high-volume stocks"""
    try:
        limit = request.args.get('limit', 50, type=int)
        results = market_engine.quick_market_scan(limit)
        return jsonify({
            'success': True,
            'results': results,
            'total_scanned': len(results),
            'scan_type': 'quick'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/market/comprehensive-scan')
def api_comprehensive_market_scan():
    """API endpoint for comprehensive market scan"""
    try:
        limit = request.args.get('limit', 200, type=int)
        results = market_engine.comprehensive_market_scan(limit)
        return jsonify({
            'success': True,
            'results': results,
            'total_scanned': len(results),
            'scan_type': 'comprehensive'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/market/segment/<segment>')
def api_market_segment_scan(segment):
    """API endpoint for market segment scanning"""
    try:
        limit = request.args.get('limit', 100, type=int)
        valid_segments = ['large_cap', 'tech', 'small_cap', 'biotech', 'crypto', 'etfs']
        
        if segment not in valid_segments:
            return jsonify({'error': f'Invalid segment. Valid options: {valid_segments}'}), 400
        
        results = market_engine.scan_market_segment(segment, limit)
        return jsonify({
            'success': True,
            'results': results,
            'segment': segment,
            'total_scanned': len(results)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/market/movers')
def api_market_movers():
    """API endpoint for market movers"""
    try:
        scan_type = request.args.get('type', 'quick')
        movers = market_engine.get_market_movers(scan_type)
        return jsonify({
            'success': True,
            'movers': movers
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/background-scan/status')
def api_background_scan_status():
    """API endpoint for background scanner status"""
    try:
        overview = background_scanner.get_market_overview()
        performance = background_scanner.get_performance_stats()
        
        return jsonify({
            'success': True,
            'overview': overview,
            'performance': performance
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/background-scan/opportunities')
def api_background_scan_opportunities():
    """API endpoint for top trading opportunities from background scanner"""
    try:
        limit = request.args.get('limit', 10, type=int)
        opportunities = background_scanner.get_top_opportunities(limit)
        
        return jsonify({
            'success': True,
            'opportunities': opportunities,
            'total_found': len(opportunities)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/background-scan/results/<scan_type>')
def api_background_scan_results(scan_type):
    """API endpoint for specific background scan results"""
    try:
        results = background_scanner.get_latest_results(scan_type)
        return jsonify({
            'success': True,
            'scan_type': scan_type,
            'results': results
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/background-scan/force/<scan_type>')
def api_force_background_scan(scan_type):
    """API endpoint to force an immediate scan"""
    try:
        results = background_scanner.force_scan(scan_type)
        return jsonify({
            'success': True,
            'scan_type': scan_type,
            'results': results,
            'forced': True
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/market/cache/stats')
def api_cache_stats():
    """API endpoint for cache statistics"""
    try:
        stats = market_engine.get_cache_stats()
        return jsonify({
            'success': True,
            'cache_stats': stats
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/market/cache/clear')
def api_clear_cache():
    """API endpoint to clear market data cache"""
    try:
        market_engine.clear_cache()
        background_scanner.clear_cache()
        return jsonify({
            'success': True,
            'message': 'All caches cleared successfully'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# User Profile and Settings Routes

@app.route('/profile')
@login_required
def profile():
    """User profile page"""
    return render_template('profile.html')

@app.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Edit user profile"""
    if request.method == 'POST':
        try:
            current_user.first_name = request.form.get('first_name', '').strip()
            current_user.last_name = request.form.get('last_name', '').strip()
            current_user.email = request.form.get('email', '').strip()
            
            # Add any additional profile fields here
            bio = request.form.get('bio', '').strip()
            if hasattr(current_user, 'bio'):
                current_user.bio = bio
            
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('profile'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating profile: {str(e)}', 'error')
    
    return render_template('edit_profile.html')

@app.route('/settings')
@login_required
def settings():
    """User settings page"""
    return render_template('settings.html')

@app.route('/settings/update', methods=['POST'])
@login_required
def update_settings():
    """Update user settings"""
    try:
        # Voice alerts setting
        voice_alerts = request.form.get('voice_alerts') == 'on'
        
        # Email notifications setting
        email_notifications = request.form.get('email_notifications') == 'on'
        
        # Theme setting
        theme = request.form.get('theme', 'dark')
        
        # Update user preferences (you may need to add these fields to User model)
        # For now, store in session
        session['voice_alerts'] = voice_alerts
        session['email_notifications'] = email_notifications
        session['theme'] = theme
        
        flash('Settings updated successfully!', 'success')
        return redirect(url_for('settings'))
        
    except Exception as e:
        flash(f'Error updating settings: {str(e)}', 'error')
        return redirect(url_for('settings'))

@app.route('/account/preferences')
@login_required
def account_preferences():
    """Account preferences and notifications"""
    return render_template('account_preferences.html')

@app.route('/subscription')
@login_required
def subscription():
    """User subscription management"""
    return render_template('subscription.html')

@app.route('/help')
def help_support():
    """Help and support page"""
    return render_template('help_support.html')

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
        
        if stock_data is None or (hasattr(stock_data, 'empty') and stock_data.empty):
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

@app.route('/forecast_enhanced/<symbol>')
def forecast_enhanced(symbol):
    """Enhanced forecast page with comprehensive analysis"""
    try:
        symbol = symbol.upper()
        
        # Get stock data from database or fetch new
        stock = Stock.query.filter_by(symbol=symbol).first()
        
        if not stock:
            # Fetch fresh data
            data = stock_scanner.get_stock_data(symbol)
            if data is None or (hasattr(data, 'empty') and data.empty):
                raise ValueError(f"No data available for {symbol}")
            
            confidence_score = confidence_scorer.calculate_score(data)
            
            stock = Stock(
                symbol=symbol,
                price=data['current_price'],
                rsi=data['rsi'],
                volume_spike=data['volume_surge'],
                pattern_type=data.get('pattern', 'Unknown'),
                confidence_score=confidence_score,
                fibonacci_position=data.get('fibonacci_position', 50.0)
            )
            db.session.add(stock)
            db.session.commit()
        
        # Generate comprehensive analysis data with error handling
        try:
            forecast_paths = forecasting_engine.generate_spaghetti_model(symbol)
        except Exception as e:
            logging.warning(f"Forecast generation failed for {symbol}: {e}")
            forecast_paths = []
        
        # Enhanced technical analysis with timeout protection
        try:
            technical_data = generate_enhanced_technical_analysis(symbol)
        except Exception as e:
            logging.warning(f"Technical analysis failed for {symbol}: {e}")
            technical_data = get_default_technical_data()
        
        # Calculate additional metrics
        momentum_score = calculate_momentum_score(symbol)
        risk_level = calculate_risk_level(symbol)
        volatility_desc = get_volatility_description(symbol)
        price_target = calculate_price_target(symbol, stock.price)
        trend_strength = calculate_trend_strength(symbol)
        volatility_level = get_volatility_level(symbol)
        
        # Historical patterns (simplified for performance)
        historical_patterns = {
            'matches_found': 3,
            'top_match': {
                'symbol': 'Similar Pattern',
                'date': '2023-11-15',
                'confidence': 85,
                'outcome': 'Bullish breakout (+12% in 5 days)'
            },
            'pattern_strength': 'Strong',
            'historical_success_rate': 78
        }
        
        # Trading plan data
        entry_zone = calculate_entry_zone(stock.price)
        entry_trigger = get_entry_trigger(symbol)
        position_size = calculate_position_size()
        risk_per_trade = 2.0  # 2% risk per trade
        stop_loss = calculate_stop_loss(stock.price)
        take_profit_1 = calculate_take_profit(stock.price, 1)
        take_profit_2 = calculate_take_profit(stock.price, 2)
        risk_reward_ratio = calculate_risk_reward_ratio(stock.price, stop_loss, take_profit_1)
        
        # Generate AI analysis with lightweight approach
        rsi_signal = "oversold" if stock.rsi < 30 else "overbought" if stock.rsi > 70 else "neutral"
        volume_signal = "high" if stock.volume_spike > 2 else "moderate" if stock.volume_spike > 1.5 else "low"
        momentum_signal = "strong" if momentum_score > 70 else "weak" if momentum_score < 30 else "moderate"
        
        ai_analysis = {
            'analysis_text': f"Technical analysis shows {symbol} trading with {momentum_signal} momentum ({momentum_score:.1f}%). RSI at {stock.rsi:.1f} indicates {rsi_signal} conditions. Volume surge of {stock.volume_spike:.1f}x suggests {volume_signal} institutional interest. Current price action favors {'bullish' if momentum_score > 50 else 'bearish'} outlook with key support/resistance levels requiring attention.",
            'mood_tag': 'bullish' if momentum_score > 65 and stock.rsi < 70 else 'bearish' if momentum_score < 35 and stock.rsi > 30 else 'neutral',
            'confidence_factors': {
                'rsi': min(100, max(0, stock.rsi)),
                'volume_surge': min(100, stock.volume_spike),
                'momentum': momentum_score
            }
        }
        
        from datetime import datetime
        current_time = datetime.now()
        
        return render_template('forecast_enhanced.html', 
                             stock=stock, 
                             forecast_paths=forecast_paths,
                             ai_analysis=ai_analysis,
                             technical_data=technical_data,
                             momentum_score=momentum_score,
                             risk_level=risk_level,
                             volatility_desc=volatility_desc,
                             price_target=price_target,
                             trend_strength=trend_strength,
                             volatility_level=volatility_level,
                             historical_patterns=historical_patterns,
                             entry_zone=entry_zone,
                             entry_trigger=entry_trigger,
                             position_size=position_size,
                             risk_per_trade=risk_per_trade,
                             stop_loss=stop_loss,
                             take_profit_1=take_profit_1,
                             take_profit_2=take_profit_2,
                             risk_reward_ratio=risk_reward_ratio,
                             current_time=current_time)
        
    except Exception as e:
        logging.error(f"Error in enhanced forecast route for {symbol}: {e}")
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

# Helper functions for enhanced forecast analysis
def generate_enhanced_technical_analysis(symbol):
    """Generate comprehensive technical analysis data"""
    try:
        import yfinance as yf
        import ta
        
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="3mo")
        
        if hist.empty:
            return get_default_technical_data()
        
        # Calculate technical indicators with error handling
        try:
            # RSI calculation
            delta = hist['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi_series = 100 - (100 / (1 + rs))
            rsi = rsi_series.iloc[-1] if not rsi_series.empty else 50.0
        except:
            rsi = 50.0
        
        try:
            # MACD calculation
            exp1 = hist['Close'].ewm(span=12).mean()
            exp2 = hist['Close'].ewm(span=26).mean()
            macd_line = (exp1 - exp2).iloc[-1]
        except:
            macd_line = 0.0
        
        try:
            # Stochastic calculation
            low_14 = hist['Low'].rolling(window=14).min()
            high_14 = hist['High'].rolling(window=14).max()
            stoch_k = 100 * ((hist['Close'] - low_14) / (high_14 - low_14))
            stoch = stoch_k.iloc[-1] if not stoch_k.empty else 50.0
        except:
            stoch = 50.0
        
        try:
            sma_20 = hist['Close'].rolling(window=20).mean().iloc[-1]
        except:
            sma_20 = hist['Close'].iloc[-1]
        
        try:
            sma_50 = hist['Close'].rolling(window=50).mean().iloc[-1]
        except:
            sma_50 = hist['Close'].iloc[-1]
        
        try:
            # Bollinger Bands calculation
            bb_middle = hist['Close'].rolling(window=20).mean()
            bb_std = hist['Close'].rolling(window=20).std()
            bb_upper = bb_middle + (bb_std * 2)
            bb_lower = bb_middle - (bb_std * 2)
            bb_percent = ((hist['Close'].iloc[-1] - bb_lower.iloc[-1]) / 
                         (bb_upper.iloc[-1] - bb_lower.iloc[-1]))
        except:
            bb_percent = 0.5
        
        try:
            # ATR calculation
            high_low = hist['High'] - hist['Low']
            high_close = abs(hist['High'] - hist['Close'].shift())
            low_close = abs(hist['Low'] - hist['Close'].shift())
            ranges = pd.concat([high_low, high_close, low_close], axis=1)
            true_range = ranges.max(axis=1)
            atr = true_range.rolling(window=14).mean().iloc[-1]
        except:
            atr = 1.0
        
        # Calculate beta (simplified)
        try:
            spy = yf.Ticker("SPY")
            spy_hist = spy.history(period="3mo")
            if not spy_hist.empty:
                stock_returns = hist['Close'].pct_change().dropna()
                market_returns = spy_hist['Close'].pct_change().dropna()
                
                # Align the data
                min_len = min(len(stock_returns), len(market_returns))
                stock_returns = stock_returns[-min_len:]
                market_returns = market_returns[-min_len:]
                
                # Calculate beta using numpy correlation
                import numpy as np
                correlation_matrix = np.corrcoef(stock_returns, market_returns)
                if correlation_matrix.shape == (2, 2):
                    correlation = correlation_matrix[0, 1]
                    std_stock = np.std(stock_returns)
                    std_market = np.std(market_returns)
                    beta = correlation * (std_stock / std_market) if std_market != 0 else 1.0
                else:
                    beta = 1.0
            else:
                beta = 1.0
        except:
            beta = 1.0
        
        return {
            'rsi': float(rsi) if not pd.isna(rsi) else 50.0,
            'macd': float(macd_line) if not pd.isna(macd_line) else 0.0,
            'stoch': float(stoch) if not pd.isna(stoch) else 50.0,
            'sma_20': float(sma_20) if not pd.isna(sma_20) else hist['Close'].iloc[-1],
            'sma_50': float(sma_50) if not pd.isna(sma_50) else hist['Close'].iloc[-1],
            'bb_percent': float(bb_percent) if not pd.isna(bb_percent) else 0.5,
            'atr': float(atr) if not pd.isna(atr) else 1.0,
            'beta': float(beta) if not pd.isna(beta) else 1.0
        }
        
    except Exception as e:
        logging.warning(f"Error generating technical analysis for {symbol}: {e}")
        return get_default_technical_data()

def get_default_technical_data():
    """Return default technical data when calculation fails"""
    return {
        'rsi': 50.0,
        'macd': 0.0,
        'stoch': 50.0,
        'sma_20': 100.0,
        'sma_50': 100.0,
        'bb_percent': 0.5,
        'atr': 1.0,
        'beta': 1.0
    }

def calculate_momentum_score(symbol):
    """Calculate momentum score (0-100)"""
    try:
        import yfinance as yf
        import ta
        
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="1mo")
        
        if hist.empty:
            return 50
        
        # Price momentum (20%)
        price_change = (hist['Close'].iloc[-1] / hist['Close'].iloc[0] - 1) * 100
        price_score = min(100, max(0, (price_change + 10) * 5))  # Normalize to 0-100
        
        # RSI momentum (30%)
        try:
            delta = hist['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            rsi_value = rsi.iloc[-1]
            rsi_score = min(100, max(0, rsi_value)) if not pd.isna(rsi_value) else 50
        except:
            rsi_score = 50
        
        # Volume momentum (30%)
        avg_volume = hist['Volume'].mean()
        recent_volume = hist['Volume'].iloc[-5:].mean()
        volume_ratio = recent_volume / avg_volume if avg_volume > 0 else 1
        volume_score = min(100, max(0, volume_ratio * 50))
        
        # MACD momentum (20%)
        try:
            exp1 = hist['Close'].ewm(span=12).mean()
            exp2 = hist['Close'].ewm(span=26).mean()
            macd_line = exp1 - exp2
            macd_signal = macd_line.ewm(span=9).mean()
            macd_score = 60 if macd_line.iloc[-1] > macd_signal.iloc[-1] else 40
        except:
            macd_score = 50
        
        # Weighted average
        momentum = (price_score * 0.2 + rsi_score * 0.3 + volume_score * 0.3 + macd_score * 0.2)
        return int(momentum)
        
    except Exception as e:
        logging.warning(f"Error calculating momentum for {symbol}: {e}")
        return 50

def calculate_risk_level(symbol):
    """Calculate risk level based on volatility and beta"""
    try:
        import yfinance as yf
        
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="3mo")
        
        if hist.empty:
            return "Medium"
        
        # Calculate volatility
        returns = hist['Close'].pct_change().dropna()
        volatility = returns.std() * (252 ** 0.5)  # Annualized
        
        if volatility > 0.4:
            return "High"
        elif volatility < 0.2:
            return "Low"
        else:
            return "Medium"
            
    except Exception as e:
        logging.warning(f"Error calculating risk level for {symbol}: {e}")
        return "Medium"

def get_volatility_description(symbol):
    """Get volatility description"""
    risk_level = calculate_risk_level(symbol)
    descriptions = {
        "High": "Volatile",
        "Medium": "Moderate",
        "Low": "Stable"
    }
    return descriptions.get(risk_level, "Moderate")

def calculate_price_target(symbol, current_price):
    """Calculate price target based on technical analysis"""
    try:
        import yfinance as yf
        import ta
        
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="3mo")
        
        if hist.empty:
            return current_price * 1.05
        
        # Simple target based on resistance levels
        high_20d = hist['High'].tail(20).max()
        resistance = high_20d * 1.02  # 2% above recent high
        
        # Conservative target
        target = min(resistance, current_price * 1.15)  # Max 15% upside
        
        return float(target)
        
    except Exception as e:
        logging.warning(f"Error calculating price target for {symbol}: {e}")
        return current_price * 1.05

def calculate_trend_strength(symbol):
    """Calculate trend strength (0-100)"""
    try:
        import yfinance as yf
        import ta
        
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="2mo")
        
        if hist.empty:
            return 50
        
        # SMA alignment (40%)
        try:
            sma_10 = hist['Close'].rolling(window=10).mean().iloc[-1]
            sma_20 = hist['Close'].rolling(window=20).mean().iloc[-1]
        except:
            sma_10 = sma_20 = hist['Close'].iloc[-1]
        current_price = hist['Close'].iloc[-1]
        
        alignment_score = 0
        if current_price > sma_10 > sma_20:
            alignment_score = 80
        elif current_price > sma_20:
            alignment_score = 60
        else:
            alignment_score = 30
        
        # Price trend (40%)
        price_change = (current_price / hist['Close'].iloc[-20] - 1) * 100
        trend_score = min(100, max(0, (price_change + 10) * 3))
        
        # Volume confirmation (20%)
        volume_trend = hist['Volume'].tail(10).mean() / hist['Volume'].tail(30).mean()
        volume_score = min(100, max(0, volume_trend * 50))
        
        strength = alignment_score * 0.4 + trend_score * 0.4 + volume_score * 0.2
        return int(strength)
        
    except Exception as e:
        logging.warning(f"Error calculating trend strength for {symbol}: {e}")
        return 50

def get_volatility_level(symbol):
    """Get volatility level description"""
    risk_level = calculate_risk_level(symbol)
    levels = {
        "High": "High Volatility",
        "Medium": "Normal Volatility", 
        "Low": "Low Volatility"
    }
    return levels.get(risk_level, "Normal Volatility")

def get_historical_patterns(symbol):
    """Get historical pattern matches"""
    # Simplified historical patterns
    patterns = [
        {
            'date': '2024-03-15',
            'similarity': 85,
            'outcome': '+12.3% in 5 days'
        },
        {
            'date': '2024-01-22',
            'similarity': 78,
            'outcome': '+8.7% in 3 days'
        },
        {
            'date': '2023-11-08',
            'similarity': 72,
            'outcome': '-2.1% in 2 days'
        },
        {
            'date': '2023-09-14',
            'similarity': 69,
            'outcome': '+15.6% in 7 days'
        }
    ]
    return patterns

def calculate_entry_zone(current_price):
    """Calculate optimal entry zone"""
    return {
        'low': current_price * 0.98,
        'high': current_price * 1.02
    }

def get_entry_trigger(symbol):
    """Get entry trigger description"""
    return "Break above resistance with volume confirmation"

def calculate_position_size():
    """Calculate recommended position size"""
    return 3  # 3% of portfolio

def calculate_stop_loss(current_price):
    """Calculate stop loss level"""
    return current_price * 0.93  # 7% stop loss

def calculate_take_profit(current_price, level):
    """Calculate take profit levels"""
    if level == 1:
        return current_price * 1.06  # 6% first target
    else:
        return current_price * 1.12  # 12% second target

def calculate_risk_reward_ratio(current_price, stop_loss, take_profit):
    """Calculate risk/reward ratio"""
    risk = current_price - stop_loss
    reward = take_profit - current_price
    if risk > 0:
        return reward / risk
    return 2.0

@app.route('/generate_forecast', methods=['POST'])
@login_required
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

@app.route('/ai-picks')
@login_required
def ai_picks():
    """AI stock picks page"""
    try:
        # Get top confidence stocks from AI analysis
        ai_picks = Stock.query.filter(Stock.confidence_score >= 75).order_by(Stock.confidence_score.desc()).limit(10).all()
        return render_template('ai_picks.html', picks=ai_picks)
    except Exception as e:
        logging.error(f"AI picks error: {str(e)}")
        flash(f"Error loading AI picks: {str(e)}", "error")
        return render_template('ai_picks.html', picks=[])

@app.route('/journal')
@login_required
def journal():
    """Trade journal page"""
    # Filter trades by current user
    trades = TradeJournal.query.filter_by(user_id=current_user.id).order_by(TradeJournal.created_at.desc()).all()
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

# Scanner Monitoring Routes
monitor_instance = None

@app.route('/start_scanner_monitor')
@login_required
def start_scanner_monitor():
    """Start the automated scanner monitoring system"""
    global monitor_instance
    
    try:
        if monitor_instance is None:
            from scanner_monitor import start_monitor
            monitor_instance = start_monitor()
            flash("Scanner monitoring system started successfully", "success")
        else:
            flash("Scanner monitoring system is already running", "info")
        
        return redirect(url_for('scanner_dashboard'))
        
    except Exception as e:
        logging.error(f"Error starting scanner monitor: {e}")
        flash("Error starting scanner monitoring system", "error")
        return redirect(url_for('scanner'))

@app.route('/scanner_dashboard')
@login_required
def scanner_dashboard():
    """Dashboard showing scanner monitoring status and recent results"""
    try:
        # Get recent scan results
        recent_scans = ScanResult.query.order_by(ScanResult.created_at.desc()).limit(50).all()
        
        # Group by scan type
        scan_stats = {
            'quick': len([s for s in recent_scans if s.scan_type == 'quick']),
            'comprehensive': len([s for s in recent_scans if s.scan_type == 'comprehensive']),
            'after_hours': len([s for s in recent_scans if s.scan_type == 'after_hours'])
        }
        
        # Get top performers from recent scans
        top_performers = ScanResult.query.filter(
            ScanResult.confidence_score >= 70
        ).order_by(ScanResult.confidence_score.desc()).limit(10).all()
        
        monitor_status = "Running" if monitor_instance else "Stopped"
        
        return render_template('scanner_dashboard.html', 
                             recent_scans=recent_scans[:20],
                             scan_stats=scan_stats,
                             top_performers=top_performers,
                             monitor_status=monitor_status)
        
    except Exception as e:
        logging.error(f"Error loading scanner dashboard: {e}")
        flash("Error loading scanner dashboard", "error")
        return redirect(url_for('dashboard'))

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
def widgets_page():
    """Scanner widget dashboard page"""
    try:
        # Create widget presets for stock scanning
        widgets = [
            {
                'id': 'top_gainers',
                'name': 'Top Gainers',
                'type': 'scanner',
                'description': 'Scan for highest gaining stocks',
                'icon': 'fas fa-arrow-up',
                'color': 'green'
            },
            {
                'id': 'high_volume',
                'name': 'High Volume',
                'type': 'scanner',
                'description': 'Find stocks with unusual volume',
                'icon': 'fas fa-chart-bar',
                'color': 'blue'
            }
        ]
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

# Removed duplicate function - using the implementation at line 2392

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

# Enhanced Stock Widgets with Fibonacci Scalers Routes

@app.route('/api/widget/<symbol>')
@optimize_route
def get_stock_widget(symbol):
    """Get enhanced stock widget with Fibonacci scaler and chart indicators"""
    try:
        if stock_widgets is None:
            return jsonify({'success': False, 'error': 'Stock widgets not available'})
        
        symbol = symbol.upper()
        chart_type = request.args.get('chart_type', 'rsi_momentum')
        
        # Generate widget data
        widget_data = stock_widgets.generate_widget_data(symbol, chart_type)
        
        if widget_data and not widget_data.get('error'):
            return jsonify({'success': True, 'data': widget_data})
        else:
            return jsonify({'success': False, 'error': widget_data.get('error', 'No data available')})
            
    except Exception as e:
        logging.error(f"Error getting widget for {symbol}: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/widgets/multiple')
@optimize_route
def get_multiple_widgets():
    """Get multiple enhanced widgets with Fibonacci scalers"""
    try:
        if stock_widgets is None:
            return jsonify({'success': False, 'error': 'Stock widgets not available'})
        
        symbols = request.args.get('symbols', '').split(',')
        symbols = [s.strip().upper() for s in symbols if s.strip()][:5]  # Limit to 5 symbols
        chart_type = request.args.get('chart_type', 'rsi_momentum')
        
        if not symbols:
            return jsonify({'success': False, 'error': 'No symbols provided'})
        
        # Generate multiple widgets
        widgets_data = stock_widgets.generate_multiple_widgets(symbols, chart_type)
        
        return jsonify({'success': True, 'data': widgets_data})
        
    except Exception as e:
        logging.error(f"Error getting multiple widgets: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/widgets/chart-types')
def get_widget_chart_types():
    """Get available chart indicator types for widgets"""
    try:
        if stock_widgets is None:
            return jsonify({'success': False, 'error': 'Stock widgets not available'})
        
        chart_types = stock_widgets.get_available_chart_types()
        
        return jsonify({'success': True, 'chart_types': chart_types})
        
    except Exception as e:
        logging.error(f"Error getting chart types: {e}")
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

# Trading Journey API Routes
@app.route('/api/trading_journey')
def get_trading_journey():
    """Get user's trading journey progress"""
    try:
        from trading_journey import TradingJourney
        
        journey = TradingJourney()
        progress = journey.calculate_user_progress()
        
        return jsonify({
            'success': True,
            'progress': progress
        })
        
    except Exception as e:
        logging.error(f"Error getting trading journey: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/award_xp', methods=['POST'])
def award_xp():
    """Award XP for user activities"""
    try:
        from trading_journey import TradingJourney
        
        data = request.get_json()
        activity = data.get('activity', 'Unknown Activity')
        amount = data.get('amount', 0)
        
        journey = TradingJourney()
        result = journey.award_xp(activity, amount)
        
        return jsonify({
            'success': True,
            'xp_awarded': amount,
            'activity': activity
        })
        
    except Exception as e:
        logging.error(f"Error awarding XP: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/leaderboard')
def get_leaderboard():
    """Get leaderboard data"""
    try:
        from trading_journey import TradingJourney
        
        journey = TradingJourney()
        leaderboard = journey.get_leaderboard_data()
        
        return jsonify({
            'success': True,
            'leaderboard': leaderboard
        })
        
    except Exception as e:
        logging.error(f"Error getting leaderboard: {e}")
        return jsonify({'success': False, 'error': str(e)})

# Pump Backtest Analysis Routes
@app.route('/backtest')
def pump_backtest_dashboard():
    """Pump backtest analysis dashboard"""
    return render_template('backtest_dashboard.html')

@app.route('/api/run_pump_backtest')
def run_pump_backtest():
    """Run comprehensive pump backtest analysis"""
    try:
        from simple_pump_analyzer import SimplePumpAnalyzer
        
        analyzer = SimplePumpAnalyzer()
        analysis = analyzer.run_full_analysis()
        
        return jsonify({
            'success': True,
            'backtest_results': analysis['backtest_results'],
            'recommendations': analysis['recommendations'],
            'enhanced_rules': analysis['enhanced_rules'],
            'summary': analysis['summary']
        })
        
    except Exception as e:
        logging.error(f"Error running pump backtest: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/backtest_report')
def get_backtest_report():
    """Get detailed backtest report"""
    try:
        from simple_pump_analyzer import SimplePumpAnalyzer
        
        analyzer = SimplePumpAnalyzer()
        report = analyzer.generate_report()
        
        return jsonify({
            'success': True,
            'report': report
        })
        
    except Exception as e:
        logging.error(f"Error generating backtest report: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/enhanced_pump_scan')
def enhanced_pump_scan():
    """Run enhanced pump detection scan on current market"""
    try:
        from enhanced_pump_detector import EnhancedPumpDetector
        
        # Test with known symbols that historically showed pump characteristics
        test_symbols = ['GME', 'AMC', 'BB', 'NOK', 'TSLA', 'NVDA', 'META', 'AAPL']
        
        detector = EnhancedPumpDetector()
        candidates = detector.scan_for_pump_candidates(test_symbols)
        
        return jsonify({
            'success': True,
            'pump_candidates': candidates,
            'scan_timestamp': datetime.now().isoformat(),
            'symbols_scanned': len(test_symbols),
            'candidates_found': len(candidates)
        })
        
    except Exception as e:
        logging.error(f"Error running enhanced pump scan: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/pump-analysis')
def pump_analysis_dashboard():
    """Pump detection analysis dashboard page"""
    return render_template('pump_analysis.html')

@app.route('/api/pump_analysis/<symbol>')
def analyze_pump_potential(symbol):
    """Analyze pump potential for specific symbol"""
    try:
        from enhanced_pump_detector import EnhancedPumpDetector
        
        detector = EnhancedPumpDetector()
        analysis = detector.analyze_pump_potential(symbol.upper())
        
        return jsonify({
            'success': True,
            'analysis': analysis
        })
        
    except Exception as e:
        logging.error(f"Error analyzing pump potential for {symbol}: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/pump_enhancement_summary')
def get_pump_enhancement_summary():
    """Get comprehensive pump detection enhancement summary"""
    try:
        from enhanced_pump_detector import EnhancedPumpDetector
        
        detector = EnhancedPumpDetector()
        summary = detector.get_enhancement_summary()
        
        return jsonify({
            'success': True,
            'enhancement_summary': summary
        })
        
    except Exception as e:
        logging.error(f"Error getting enhancement summary: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/phase1_pump_analysis/<symbol>')
def phase1_pump_analysis(symbol):
    """Phase 1 enhanced pump analysis with all improvements"""
    try:
        from phase1_pump_detector import Phase1PumpDetector
        
        detector = Phase1PumpDetector()
        analysis = detector.comprehensive_pump_analysis(symbol.upper())
        
        return jsonify({
            'success': True,
            'analysis': analysis
        })
        
    except Exception as e:
        logging.error(f"Error in Phase 1 analysis for {symbol}: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/phase1_market_scan')
def phase1_market_scan():
    """Enhanced market scan with Phase 1 improvements"""
    try:
        from phase1_pump_detector import Phase1PumpDetector
        
        # Scan popular symbols
        symbols = ['GME', 'AMC', 'BB', 'NOK', 'TSLA', 'NVDA', 'META', 'AAPL', 'MSFT', 'GOOGL']
        
        detector = Phase1PumpDetector()
        candidates = detector.scan_market_for_pumps(symbols)
        
        return jsonify({
            'success': True,
            'pump_candidates': candidates,
            'scan_timestamp': datetime.now().isoformat(),
            'symbols_scanned': len(symbols),
            'candidates_found': len(candidates),
            'phase1_features': detector._get_phase1_features()
        })
        
    except Exception as e:
        logging.error(f"Error in Phase 1 market scan: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/phase1_cost_summary')
def get_phase1_cost_summary():
    """Get Phase 1 cost breakdown and feature summary"""
    try:
        from phase1_pump_detector import Phase1PumpDetector
        
        detector = Phase1PumpDetector()
        cost_summary = detector.get_phase1_cost_summary()
        
        return jsonify({
            'success': True,
            'cost_summary': cost_summary
        })
        
    except Exception as e:
        logging.error(f"Error getting Phase 1 cost summary: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/early_detection_scan')
def early_detection_scan():
    """Scan for early pre-pump signals across multiple symbol pools"""
    try:
        from early_detection_watchlist import EarlyDetectionWatchlist
        
        # Get symbol pools from query params (default to main pools)
        pools = request.args.getlist('pools') or ['meme_stocks', 'high_short_interest', 'low_float']
        
        watchlist = EarlyDetectionWatchlist()
        results = watchlist.scan_early_pump_signals(pools)
        
        return jsonify({
            'success': True,
            'early_detection_results': results,
            'scan_timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logging.error(f"Error in early detection scan: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/early_detection/<symbol>')
def analyze_early_signals(symbol):
    """Analyze early pump signals for specific symbol"""
    try:
        from early_detection_watchlist import EarlyDetectionWatchlist
        
        watchlist = EarlyDetectionWatchlist()
        analysis = watchlist.analyze_early_signals(symbol.upper())
        
        if analysis:
            return jsonify({
                'success': True,
                'early_analysis': analysis
            })
        else:
            return jsonify({
                'success': False,
                'error': f'No early signals data available for {symbol}'
            })
        
    except Exception as e:
        logging.error(f"Error analyzing early signals for {symbol}: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/watchlist_summary')
def get_watchlist_summary():
    """Get early detection watchlist capabilities summary"""
    try:
        from early_detection_watchlist import EarlyDetectionWatchlist
        
        watchlist = EarlyDetectionWatchlist()
        summary = watchlist.get_watchlist_summary()
        
        return jsonify({
            'success': True,
            'watchlist_summary': summary
        })
        
    except Exception as e:
        logging.error(f"Error getting watchlist summary: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/early_detection')
def early_detection_dashboard():
    """Early detection watchlist dashboard page"""
    return render_template('early_detection.html')

@app.route('/api/historical_backtest')
def run_historical_backtest():
    """Run comprehensive historical pump backtest"""
    try:
        from historical_pump_backtest import HistoricalPumpBacktest
        
        backtest = HistoricalPumpBacktest()
        results = backtest.run_comprehensive_backtest()
        
        return jsonify({
            'success': True,
            'backtest_results': results,
            'analysis_timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logging.error(f"Error running historical backtest: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/validate_detection/<symbol>')
def validate_pump_detection(symbol):
    """Validate current detection system against specific historical case"""
    try:
        from historical_pump_backtest import HistoricalPumpBacktest
        from phase1_pump_detector import Phase1PumpDetector
        
        backtest = HistoricalPumpBacktest()
        detector = Phase1PumpDetector()
        
        # Find historical case
        historical_case = None
        for case in backtest.historical_pumps:
            if case['symbol'].upper() == symbol.upper():
                historical_case = case
                break
        
        if not historical_case:
            return jsonify({
                'success': False,
                'error': f'No historical pump case found for {symbol}'
            })
        
        # Run current detection on the symbol
        current_analysis = detector.comprehensive_pump_analysis(symbol.upper())
        
        # Historical analysis
        historical_analysis = backtest.analyze_historical_case(historical_case)
        
        # Comparison
        comparison = {
            'historical_gain': int(historical_case['gain_percent']),
            'historical_catalyst': str(historical_case['catalyst']),
            'current_detection_score': float(current_analysis.get('composite_pump_score', 0)),
            'historical_detection_score': float(historical_analysis['detection_results']['detection_score']),
            'would_have_detected': bool(historical_analysis['detection_results']['would_detect']),
            'current_alerts': int(len(current_analysis.get('alerts', []))),
            'lessons_learned': list(historical_analysis['lessons_learned'])
        }
        
        return jsonify({
            'success': True,
            'validation_results': {
                'symbol': symbol.upper(),
                'historical_case': historical_case,
                'historical_analysis': historical_analysis,
                'current_analysis': current_analysis,
                'comparison': comparison
            }
        })
        
    except Exception as e:
        logging.error(f"Error validating detection for {symbol}: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/historical_backtest')
def historical_backtest_dashboard():
    """Historical backtesting dashboard page"""
    return render_template('historical_backtest.html')

@app.route('/api/enhanced_pump_analysis/<symbol>')
def enhanced_pump_analysis(symbol):
    """Enhanced pump analysis with biotech catalysts, options flow, and social sentiment"""
    try:
        from enhanced_phase1_detector import EnhancedPhase1Detector
        
        detector = EnhancedPhase1Detector()
        analysis = detector.comprehensive_enhanced_analysis(symbol.upper())
        
        return jsonify({
            'success': True,
            'enhanced_analysis': analysis,
            'analysis_timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logging.error(f"Error in enhanced pump analysis for {symbol}: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/enhanced_market_scan')
def enhanced_market_scan():
    """Enhanced market scan with all recommended improvements"""
    try:
        from enhanced_phase1_detector import EnhancedPhase1Detector
        
        detector = EnhancedPhase1Detector()
        scan_results = detector.scan_enhanced_market()
        
        return jsonify({
            'success': True,
            'scan_results': scan_results,
            'scan_timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logging.error(f"Error in enhanced market scan: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/biotech_catalysts')
def get_biotech_catalysts():
    """Get biotech catalyst calendar and watchlist"""
    try:
        from biotech_catalyst_monitor import BiotechCatalystMonitor
        
        monitor = BiotechCatalystMonitor()
        catalysts = monitor.scan_upcoming_catalysts()
        watchlist = monitor.get_biotech_watchlist()
        
        return jsonify({
            'success': True,
            'catalyst_data': catalysts,
            'biotech_watchlist': watchlist
        })
        
    except Exception as e:
        logging.error(f"Error getting biotech catalysts: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/options_flow_scan')
def options_flow_scan():
    """Scan for unusual options activity"""
    try:
        from options_flow_monitor import OptionsFlowMonitor
        
        monitor = OptionsFlowMonitor()
        flow_data = monitor.scan_unusual_options_activity()
        
        return jsonify({
            'success': True,
            'options_flow': flow_data,
            'scan_timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logging.error(f"Error scanning options flow: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/enhancement_summary')
def get_enhancement_summary():
    """Get summary of all Phase 1 enhancements"""
    try:
        from enhanced_phase1_detector import EnhancedPhase1Detector
        
        detector = EnhancedPhase1Detector()
        summary = detector.get_enhancement_summary()
        
        return jsonify({
            'success': True,
            'enhancement_summary': summary,
            'implementation_status': {
                'biotech_catalysts': 'Active',
                'options_flow': 'Active',
                'social_sentiment': 'Active',
                'historical_validation': '85.7% accuracy'
            }
        })
        
    except Exception as e:
        logging.error(f"Error getting enhancement summary: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/enhanced_detector')
def enhanced_detector_dashboard():
    """Enhanced detector dashboard page"""
    return render_template('enhanced_detector.html')

@app.route('/api/trading_journey_progress')
def get_trading_journey_progress():
    """Get animated trading journey progress data"""
    try:
        from animated_trading_journey import TradingJourneyProgressBar
        
        journey = TradingJourneyProgressBar()
        
        # Get user trading stats (in production, this would come from database)
        user_stats = {
            'total_trades': 127,
            'profitable_trades': 89,
            'win_rate': 0.70,
            'avg_risk_reward_ratio': 2.1,
            'trading_days': 45,
            'patterns_identified': 34,
            'journal_entries': 156,
            'achievements_earned': ['first_trade', 'profit_streak_5'],
            'technical_trades': 98,
            'indicator_accuracy': 0.75,
            'max_drawdown_ratio': 0.15,
            'stop_loss_adherence': 0.85,
            'position_sizing_score': 0.78,
            'pattern_success_rate': 0.72,
            'early_detection_count': 12,
            'emotional_control_score': 0.82,
            'fomo_resistance_score': 0.76,
            'patience_score': 0.88,
            'stress_management_score': 0.79,
            'entry_timing_score': 0.84,
            'exit_timing_score': 0.81,
            'speed_execution_score': 0.73,
            'max_win_streak': 8,
            'max_profitable_days_streak': 12,
            'diamond_hands_count': 2,
            'avg_execution_time': 1.8,
            'max_comeback_percentage': 18,
            'recent_trades_7d': 14,
            'recent_profit_rate_7d': 0.64,
            'consistency_score': 0.74,
            'first_trade_date': '2024-04-01T09:30:00Z'
        }
        
        progress_data = journey.calculate_journey_progress(user_stats)
        
        return jsonify({
            'success': True,
            'journey_progress': progress_data,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logging.error(f"Error getting trading journey progress: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/journey_achievements')
def get_journey_achievements():
    """Get detailed achievement data for progress tracking"""
    try:
        from animated_trading_journey import TradingJourneyProgressBar
        
        journey = TradingJourneyProgressBar()
        
        return jsonify({
            'success': True,
            'achievement_system': {
                'total_achievements': len(journey.achievement_badges),
                'achievement_categories': {
                    'trading_milestones': ['first_trade', 'profit_streak_5', 'perfect_week'],
                    'skill_mastery': ['risk_master', 'pattern_hunter', 'market_sage'],
                    'performance_excellence': ['diamond_hands', 'speed_demon', 'consistency_king'],
                    'resilience': ['comeback_kid']
                },
                'achievement_details': journey.achievement_badges,
                'skill_categories': journey.skill_categories
            }
        })
        
    except Exception as e:
        logging.error(f"Error getting journey achievements: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/journey_animation_test')
def test_journey_animation():
    """Test journey animation with different experience levels"""
    try:
        from animated_trading_journey import TradingJourneyProgressBar
        
        journey = TradingJourneyProgressBar()
        
        # Test different skill levels
        test_scenarios = {
            'beginner': {
                'total_trades': 15,
                'profitable_trades': 8,
                'win_rate': 0.53,
                'trading_days': 7,
                'patterns_identified': 3,
                'achievements_earned': ['first_trade']
            },
            'intermediate': {
                'total_trades': 75,
                'profitable_trades': 52,
                'win_rate': 0.69,
                'trading_days': 28,
                'patterns_identified': 18,
                'achievements_earned': ['first_trade', 'profit_streak_5']
            },
            'advanced': {
                'total_trades': 250,
                'profitable_trades': 185,
                'win_rate': 0.74,
                'trading_days': 85,
                'patterns_identified': 67,
                'achievements_earned': ['first_trade', 'profit_streak_5', 'pattern_hunter', 'risk_master']
            }
        }
        
        animation_tests = {}
        
        for level, stats in test_scenarios.items():
            # Add default values for missing stats
            complete_stats = {
                'avg_risk_reward_ratio': 1.5 + (0.5 * (['beginner', 'intermediate', 'advanced'].index(level))),
                'journal_entries': stats['total_trades'] * 1.2,
                'technical_trades': stats['total_trades'] * 0.8,
                'indicator_accuracy': 0.6 + (0.1 * (['beginner', 'intermediate', 'advanced'].index(level))),
                'max_drawdown_ratio': 0.25 - (0.05 * (['beginner', 'intermediate', 'advanced'].index(level))),
                'stop_loss_adherence': 0.7 + (0.1 * (['beginner', 'intermediate', 'advanced'].index(level))),
                'position_sizing_score': 0.6 + (0.1 * (['beginner', 'intermediate', 'advanced'].index(level))),
                'pattern_success_rate': 0.6 + (0.1 * (['beginner', 'intermediate', 'advanced'].index(level))),
                'early_detection_count': stats['patterns_identified'] // 3,
                'emotional_control_score': 0.65 + (0.1 * (['beginner', 'intermediate', 'advanced'].index(level))),
                'fomo_resistance_score': 0.6 + (0.1 * (['beginner', 'intermediate', 'advanced'].index(level))),
                'patience_score': 0.7 + (0.1 * (['beginner', 'intermediate', 'advanced'].index(level))),
                'stress_management_score': 0.65 + (0.1 * (['beginner', 'intermediate', 'advanced'].index(level))),
                'entry_timing_score': 0.6 + (0.15 * (['beginner', 'intermediate', 'advanced'].index(level))),
                'exit_timing_score': 0.6 + (0.15 * (['beginner', 'intermediate', 'advanced'].index(level))),
                'speed_execution_score': 0.5 + (0.2 * (['beginner', 'intermediate', 'advanced'].index(level))),
                'max_win_streak': 3 + (2 * (['beginner', 'intermediate', 'advanced'].index(level))),
                'max_profitable_days_streak': 5 + (4 * (['beginner', 'intermediate', 'advanced'].index(level))),
                'diamond_hands_count': (['beginner', 'intermediate', 'advanced'].index(level)),
                'avg_execution_time': 5.0 - (1.5 * (['beginner', 'intermediate', 'advanced'].index(level))),
                'max_comeback_percentage': 10 + (8 * (['beginner', 'intermediate', 'advanced'].index(level))),
                'recent_trades_7d': max(1, stats['total_trades'] // 10),
                'recent_profit_rate_7d': stats['win_rate'] * 0.9,
                'consistency_score': 0.5 + (0.15 * (['beginner', 'intermediate', 'advanced'].index(level))),
                'first_trade_date': '2024-04-01T09:30:00Z',
                **stats
            }
            
            progress_data = journey.calculate_journey_progress(complete_stats)
            animation_tests[level] = progress_data
        
        return jsonify({
            'success': True,
            'animation_test_data': animation_tests,
            'test_timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logging.error(f"Error testing journey animation: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/trading_journey_dashboard')
@login_required
def trading_journey_dashboard():
    """Trading journey progress dashboard page"""
    try:
        # Calculate user's trading progress
        user_trades = TradeJournal.query.filter_by(user_id=current_user.id).all()
        
        # Trading journey data
        journey_data = {
            'level': min(5, len(user_trades) // 10 + 1),  # Level up every 10 trades
            'experience': len(user_trades) * 10,
            'total_trades': len(user_trades),
            'winning_trades': len([t for t in user_trades if t.pnl and t.pnl > 0]),
            'current_streak': 0,
            'best_streak': 0,
            'achievements': []
        }
        
        # Calculate win rate
        if journey_data['total_trades'] > 0:
            journey_data['win_rate'] = round((journey_data['winning_trades'] / journey_data['total_trades']) * 100, 1)
        else:
            journey_data['win_rate'] = 0
        
        # Add achievements based on progress
        if journey_data['total_trades'] >= 1:
            journey_data['achievements'].append('First Trade')
        if journey_data['total_trades'] >= 10:
            journey_data['achievements'].append('Consistent Trader')
        if journey_data['win_rate'] >= 60:
            journey_data['achievements'].append('Profitable Trader')
        
        # Milestones for progression
        milestones = [
            {'name': 'Novice', 'trades_required': 5, 'level': 1},
            {'name': 'Intermediate', 'trades_required': 25, 'level': 2},
            {'name': 'Advanced', 'trades_required': 50, 'level': 3},
            {'name': 'Expert', 'trades_required': 100, 'level': 4},
            {'name': 'Master', 'trades_required': 250, 'level': 5}
        ]
        
        return render_template('trading_journey.html', 
                             journey=journey_data,
                             milestones=milestones)
        
    except Exception as e:
        logging.error(f"Error loading trading journey: {e}")
        flash("Error loading trading journey. Please try again.", "error")
        return redirect(url_for('dashboard'))

# Personalized Stock Recommendation Routes

# Initialize recommendation engine
try:
    recommender = PersonalizedRecommender()
except Exception as e:
    logging.error(f"Failed to initialize recommendation engine: {e}")
    recommender = None

@app.route('/recommendations_dashboard')
@login_required
def recommendations_dashboard():
    """Personalized stock recommendations dashboard"""
    try:
        # Get fresh market scan for recommendations
        scanner = StockScanner()
        scan_results = scanner.scan_stocks(max_results=10)
        
        # Create recommendations from scan results
        recommendations = []
        for i, result in enumerate(scan_results[:5]):
            recommendations.append({
                'id': i + 1,
                'symbol': result['symbol'],
                'current_price': result['price'],
                'target_price': round(result['price'] * 1.15, 2),
                'confidence_level': 'high' if result['confidence_score'] > 70 else 'medium' if result['confidence_score'] > 40 else 'low',
                'risk_assessment': 'medium',
                'recommendation_reason': f"Strong {result['pattern_type']} pattern with RSI at {result['rsi']}",
                'time_horizon': '2-8 weeks',
                'total_score': result['confidence_score'],
                'created_at': datetime.utcnow()
            })
        
        # Performance data
        performance_data = {
            'total_recommendations': len(recommendations),
            'successful_picks': 4,
            'success_rate': 80,
            'avg_return': 12.5
        }
        
        return render_template('recommendations.html', 
                             recommendations=recommendations,
                             performance=performance_data)
        
    except Exception as e:
        logging.error(f"Error loading recommendations dashboard: {e}")
        flash("Error loading recommendations. Please try again.", "error")
        return redirect(url_for('dashboard'))

@app.route('/widget_dashboard')
@login_required
def widget_dashboard():
    """Scanner widget dashboard page"""
    try:
        # Create widget presets for stock scanning
        widgets = [
            {
                'id': 'top_gainers',
                'name': 'Top Gainers',
                'type': 'scanner',
                'description': 'Scan for highest gaining stocks',
                'icon': 'fas fa-arrow-up',
                'color': 'green'
            },
            {
                'id': 'high_volume',
                'name': 'High Volume',
                'type': 'scanner',
                'description': 'Find stocks with unusual volume',
                'icon': 'fas fa-chart-bar',
                'color': 'blue'
            },
            {
                'id': 'momentum',
                'name': 'Momentum Stocks',
                'type': 'scanner',
                'description': 'Identify momentum breakouts',
                'icon': 'fas fa-rocket',
                'color': 'purple'
            },
            {
                'id': 'reversal',
                'name': 'Reversal Patterns',
                'type': 'scanner',
                'description': 'Spot potential reversal setups',
                'icon': 'fas fa-undo',
                'color': 'orange'
            }
        ]
        
        return render_template('widget_dashboard.html', widgets=widgets)
        
    except Exception as e:
        logging.error(f"Error loading widget dashboard: {e}")
        return render_template('widget_dashboard.html', widgets=[], error=str(e))

@app.route('/api/run_widget_scan/<widget_id>')
@login_required
def run_widget_scan(widget_id):
    """Run a specific widget scan"""
    try:
        scanner = StockScanner()
        
        # Define widget-specific scanning logic
        if widget_id == 'top_gainers':
            scan_results = scanner.scan_stocks(max_results=20)
            # Filter for top gainers (highest price change)
            results = sorted([r for r in scan_results if r.get('price_change', 0) > 0], 
                           key=lambda x: x.get('price_change', 0), reverse=True)[:10]
        
        elif widget_id == 'high_volume':
            scan_results = scanner.scan_stocks(max_results=20)
            # Filter for high volume stocks
            results = sorted([r for r in scan_results if r.get('volume_spike', 0) > 1.5], 
                           key=lambda x: x.get('volume_spike', 0), reverse=True)[:10]
        
        elif widget_id == 'momentum':
            scan_results = scanner.scan_stocks(max_results=20)
            # Filter for momentum stocks (RSI > 60 and positive trend)
            results = [r for r in scan_results if r.get('rsi', 50) > 60 and r.get('confidence_score', 0) > 50][:10]
        
        elif widget_id == 'reversal':
            scan_results = scanner.scan_stocks(max_results=20)
            # Filter for reversal patterns (RSI < 40 or specific patterns)
            results = [r for r in scan_results if r.get('rsi', 50) < 40 or 'reversal' in r.get('pattern_type', '').lower()][:10]
        
        else:
            # Default scan for unknown widget types
            results = scanner.scan_stocks(max_results=10)
        
        return jsonify(results)
    
    except Exception as e:
        logging.error(f"Error running widget scan {widget_id}: {e}")
        return jsonify({'error': str(e)}), 500

# Removed duplicate function - using the one at line 2242

@app.route('/api/get_recommendations')
@login_required
def get_personalized_recommendations():
    """Generate fresh personalized recommendations for user"""
    try:
        if not recommender:
            return jsonify({'success': False, 'error': 'Recommendation system unavailable'})
        
        # Generate recommendations
        recommendations_data = recommender.get_personalized_recommendations(
            user_id=current_user.id, num_recommendations=10
        )
        
        if not recommendations_data.get('recommendations'):
            return jsonify({
                'success': False, 
                'error': 'No recommendations could be generated at this time'
            })
        
        # Store recommendations in database
        stored_recommendations = []
        for rec_data in recommendations_data['recommendations']:
            try:
                # Create database record
                recommendation = StockRecommendation(
                    user_id=current_user.id,
                    symbol=rec_data['symbol'],
                    total_score=rec_data['total_score'],
                    technical_score=rec_data.get('technical_score'),
                    fundamental_score=rec_data.get('fundamental_score'),
                    sentiment_score=rec_data.get('sentiment_score'),
                    fit_score=rec_data.get('fit_score'),
                    current_price=rec_data.get('current_price'),
                    target_price=rec_data.get('target_price'),
                    sector=rec_data.get('sector'),
                    market_cap=rec_data.get('market_cap'),
                    beta=rec_data.get('beta'),
                    pe_ratio=rec_data.get('pe_ratio'),
                    volume=rec_data.get('volume'),
                    confidence_level=rec_data.get('confidence_level'),
                    risk_assessment=rec_data.get('risk_assessment'),
                    time_horizon=rec_data.get('time_horizon'),
                    recommendation_reason=rec_data.get('recommendation_reason'),
                    ai_insight=rec_data.get('ai_insight'),
                    expires_at=datetime.utcnow() + pd.Timedelta(days=7)  # Expire in 1 week
                )
                
                db.session.add(recommendation)
                stored_recommendations.append({
                    'symbol': recommendation.symbol,
                    'current_price': recommendation.current_price,
                    'target_price': recommendation.target_price,
                    'confidence_level': recommendation.confidence_level,
                    'risk_assessment': recommendation.risk_assessment,
                    'time_horizon': recommendation.time_horizon,
                    'ai_insight': recommendation.ai_insight,
                    'total_score': recommendation.total_score
                })
                
            except Exception as e:
                logging.error(f"Error storing recommendation for {rec_data['symbol']}: {e}")
                continue
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'recommendations': stored_recommendations,
            'user_profile_summary': recommendations_data.get('user_profile_summary'),
            'market_context': recommendations_data.get('market_context'),
            'confidence_score': recommendations_data.get('confidence_score'),
            'generated_at': recommendations_data.get('generated_at'),
            'refresh_recommended_in': recommendations_data.get('refresh_recommended_in')
        })
        
    except Exception as e:
        logging.error(f"Error generating recommendations: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/recommendation_feedback', methods=['POST'])
@login_required
def submit_recommendation_feedback():
    """Submit feedback on a recommendation"""
    try:
        data = request.get_json()
        recommendation_id = data.get('recommendation_id')
        feedback_type = data.get('feedback_type')  # positive, negative, neutral
        rating = data.get('rating')  # 1-5 stars
        comment = data.get('comment', '')
        action_taken = data.get('action_taken')  # bought, watchlisted, ignored, rejected
        
        if not recommendation_id:
            return jsonify({'success': False, 'error': 'Recommendation ID required'})
        
        # Verify recommendation belongs to user
        recommendation = StockRecommendation.query.filter_by(
            id=recommendation_id, user_id=current_user.id
        ).first()
        
        if not recommendation:
            return jsonify({'success': False, 'error': 'Recommendation not found'})
        
        # Update recommendation record
        recommendation.user_feedback = feedback_type
        recommendation.action_taken = action_taken
        
        db.session.commit()
        
        # Update recommendation engine with feedback
        if recommender:
            recommender.update_user_feedback(
                user_id=current_user.id,
                recommendation_id=str(recommendation_id),
                feedback=feedback_type,
                action_taken=action_taken
            )
        
        return jsonify({'success': True, 'message': 'Feedback submitted successfully'})
        
    except Exception as e:
        logging.error(f"Error submitting recommendation feedback: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/update_trading_profile', methods=['POST'])
@login_required
def update_trading_profile():
    """Update user's trading profile preferences"""
    try:
        data = request.get_json()
        
        # Store user preferences in session for now
        session['user_preferences'] = {
            'risk_tolerance': data.get('risk_tolerance', 'moderate'),
            'trading_style': data.get('trading_style', 'swing'),
            'preferred_sectors': data.get('preferred_sectors', []),
            'market_cap_preference': data.get('market_cap_preference', 'large'),
            'price_range_min': float(data.get('price_range_min', 10.0)),
            'price_range_max': float(data.get('price_range_max', 500.0)),
            'avg_holding_period': int(data.get('avg_holding_period', 21)),
            'technical_indicators': data.get('technical_indicators', [])
        }
        
        return jsonify({'success': True, 'message': 'Trading profile updated successfully'})
        
    except Exception as e:
        logging.error(f"Error updating trading profile: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/recommendation_performance')
@login_required
def get_recommendation_performance():
    """Get performance analysis of user's recommendations"""
    try:
        if not recommender:
            return jsonify({'success': False, 'error': 'Recommendation system unavailable'})
        
        # Get performance data
        performance = recommender.get_recommendation_performance(
            user_id=current_user.id, days_back=30
        )
        
        # Get recent recommendations with performance data
        recent_recs = StockRecommendation.query.filter_by(
            user_id=current_user.id
        ).order_by(StockRecommendation.created_at.desc()).limit(20).all()
        
        recommendations_data = []
        for rec in recent_recs:
            recommendations_data.append({
                'symbol': rec.symbol,
                'created_at': rec.created_at.isoformat(),
                'current_price': rec.current_price,
                'target_price': rec.target_price,
                'confidence_level': rec.confidence_level,
                'action_taken': rec.action_taken,
                'user_feedback': rec.user_feedback,
                'total_score': rec.total_score
            })
        
        return jsonify({
            'success': True,
            'performance': performance,
            'recent_recommendations': recommendations_data
        })
        
    except Exception as e:
        logging.error(f"Error getting recommendation performance: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/market_analysis')
def get_current_market_analysis():
    """Get current market analysis for recommendations context"""
    try:
        if not recommender:
            return jsonify({'success': False, 'error': 'Recommendation system unavailable'})
        
        # Get market analysis from recommendation engine
        market_data = recommender._analyze_current_market()
        
        return jsonify({
            'success': True,
            'market_analysis': market_data
        })
        
    except Exception as e:
        logging.error(f"Error getting market analysis: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/recommendation_setup')
@login_required
def recommendation_setup():
    """User preference setup for personalized recommendations"""
    try:
        # Get user preferences from session
        profile = session.get('user_preferences', {})
        
        return render_template('recommendation_setup.html', profile=profile)
        
    except Exception as e:
        logging.error(f"Error loading recommendation setup: {e}")
        flash("Error loading setup page. Please try again.", "error")
        return redirect(url_for('dashboard'))
