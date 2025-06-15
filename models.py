from datetime import datetime
from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import secrets

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=True)
    first_name = db.Column(db.String(50), nullable=True)
    last_name = db.Column(db.String(50), nullable=True)
    profile_image_url = db.Column(db.String(200), nullable=True)
    
    # Authentication and verification
    auth_method = db.Column(db.String(20), default='email')
    is_verified = db.Column(db.Boolean, default=False)
    verification_token = db.Column(db.String(64), nullable=True)
    
    # Beta user tracking
    beta_user_number = db.Column(db.Integer, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    trades = db.relationship('TradeJournal', backref='user', lazy=True)
    recommendations = db.relationship('StockRecommendation', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def generate_verification_token(self):
        self.verification_token = secrets.token_urlsafe(32)
        return self.verification_token

class Stock(db.Model):
    __tablename__ = 'stocks'
    
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(10), nullable=False, unique=True)
    name = db.Column(db.String(200))
    price = db.Column(db.Float)
    rsi = db.Column(db.Float)
    volume_spike = db.Column(db.Float)
    pattern_type = db.Column(db.String(50))
    fibonacci_position = db.Column(db.Float)
    confidence_score = db.Column(db.Float, default=0.0)
    is_tracked = db.Column(db.Boolean, default=False)
    
    # Technical indicators
    macd = db.Column(db.Float)
    bollinger_position = db.Column(db.Float)
    volume_ma_ratio = db.Column(db.Float)
    
    # Market data
    market_cap = db.Column(db.BigInteger)
    sector = db.Column(db.String(50))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class TradeJournal(db.Model):
    __tablename__ = 'trade_journal'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    symbol = db.Column(db.String(10), nullable=False)
    
    # Trade details
    entry_price = db.Column(db.Float)
    exit_price = db.Column(db.Float)
    stop_loss = db.Column(db.Float)
    take_profit = db.Column(db.Float)
    quantity = db.Column(db.Integer)
    
    # Pattern and analysis
    pattern_confirmed = db.Column(db.Boolean, default=False)
    screenshot_taken = db.Column(db.Boolean, default=False)
    confidence_at_entry = db.Column(db.Float)
    
    # Outcome tracking
    outcome = db.Column(db.String(20))  # 'win', 'loss', 'breakeven', 'active'
    pnl = db.Column(db.Float)
    pnl_percentage = db.Column(db.Float)
    
    # Notes and reflection
    reflection = db.Column(db.Text)
    lessons_learned = db.Column(db.Text)
    perfect_trade = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class StockRecommendation(db.Model):
    __tablename__ = 'stock_recommendations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    symbol = db.Column(db.String(10), nullable=False)
    
    # Scoring system
    total_score = db.Column(db.Float, nullable=False)
    technical_score = db.Column(db.Float)
    fundamental_score = db.Column(db.Float)
    sentiment_score = db.Column(db.Float)
    fit_score = db.Column(db.Float)
    
    # Market data
    current_price = db.Column(db.Float)
    target_price = db.Column(db.Float)
    sector = db.Column(db.String(50))
    market_cap = db.Column(db.BigInteger)
    
    # Risk assessment
    confidence_level = db.Column(db.String(10))  # High, Medium, Low
    risk_assessment = db.Column(db.String(10))   # High, Medium, Low
    time_horizon = db.Column(db.String(20))      # e.g., "2-8 weeks"
    
    # AI insights
    recommendation_reason = db.Column(db.Text)
    ai_insight = db.Column(db.Text)
    
    # User interaction
    viewed = db.Column(db.Boolean, default=False)
    action_taken = db.Column(db.String(20))      # bought, watchlisted, ignored
    user_feedback = db.Column(db.String(20))     # excellent, good, neutral, poor
    
    # Performance tracking
    performance_tracked = db.Column(db.Boolean, default=True)
    recommendation_return_pct = db.Column(db.Float)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)

class PatternEvolution(db.Model):
    __tablename__ = 'pattern_evolution'
    
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(10), nullable=False)
    pattern_type = db.Column(db.String(50))  # 'bull_flag', 'cup_and_handle', etc.
    
    # Pattern metrics
    confidence_score = db.Column(db.Float)
    stage = db.Column(db.String(30))  # 'forming', 'building', 'mature', 'apex_approaching'
    completion_percentage = db.Column(db.Float)
    time_in_pattern = db.Column(db.Integer)  # days
    
    # Market dynamics
    volatility_trend = db.Column(db.Float)
    volume_trend = db.Column(db.Float)
    momentum_change = db.Column(db.Float)
    
    # Prediction metrics
    estimated_days_to_breakout = db.Column(db.Integer)
    breakout_probability_5_days = db.Column(db.Float)
    breakout_probability_10_days = db.Column(db.Float)
    direction_bias = db.Column(db.Float)  # 0-1 (bearish to bullish)
    
    # Key levels
    resistance_level = db.Column(db.Float)
    support_level = db.Column(db.Float)
    breakout_confirmation_level = db.Column(db.Float)
    
    # Pattern data (JSON field for additional metrics)
    pattern_data = db.Column(db.JSON)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ForecastPath(db.Model):
    __tablename__ = 'forecast_paths'
    
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(10), nullable=False)
    path_type = db.Column(db.String(50))  # 'momentum', 'retest', 'breakdown', 'sideways'
    probability = db.Column(db.Float)
    price_targets = db.Column(db.JSON)  # Array of price points
    timeframe_days = db.Column(db.Integer, default=5)
    risk_zones = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class AIAnalysis(db.Model):
    __tablename__ = 'ai_analysis'
    
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(10), nullable=False)
    analysis_text = db.Column(db.Text)
    mood_tag = db.Column(db.String(20))  # 'breakout', 'reversal', 'risky', 'confirmed'
    historical_comparison = db.Column(db.Text)
    chart_story = db.Column(db.JSON)  # Store hover comments for chart levels
    confidence_score = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)