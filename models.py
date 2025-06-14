from datetime import datetime
from app import db
from flask_dance.consumer.storage.sqla import OAuthConsumerMixin
from flask_login import UserMixin
from sqlalchemy import UniqueConstraint


# Enhanced User model supporting multiple authentication methods
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.String, primary_key=True)
    email = db.Column(db.String, unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=True)  # For email/password auth
    first_name = db.Column(db.String, nullable=True)
    last_name = db.Column(db.String, nullable=True)
    profile_image_url = db.Column(db.String, nullable=True)
    
    # Authentication method tracking
    auth_method = db.Column(db.String(20), default='email')  # 'email', 'google', 'replit'
    is_verified = db.Column(db.Boolean, default=False)
    verification_token = db.Column(db.String(64), nullable=True)
    
    # Beta access tracking
    beta_user_number = db.Column(db.Integer, nullable=True)  # 1-100 for first 100 users
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime,
                           default=datetime.now,
                           onupdate=datetime.now)

# (IMPORTANT) This table is mandatory for Replit Auth, don't drop it.
class OAuth(OAuthConsumerMixin, db.Model):
    user_id = db.Column(db.String, db.ForeignKey(User.id))
    browser_session_key = db.Column(db.String, nullable=False)
    user = db.relationship(User)

    __table_args__ = (UniqueConstraint(
        'user_id',
        'browser_session_key',
        'provider',
        name='uq_user_browser_session_key_provider',
    ),)

class Stock(db.Model):
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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class TradeJournal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(10), nullable=False)
    entry_price = db.Column(db.Float)
    stop_loss = db.Column(db.Float)
    take_profit = db.Column(db.Float)
    pattern_confirmed = db.Column(db.Boolean, default=False)
    screenshot_taken = db.Column(db.Boolean, default=False)
    reflection = db.Column(db.Text)
    perfect_trade = db.Column(db.Boolean, default=False)
    confidence_at_entry = db.Column(db.Float)
    outcome = db.Column(db.String(20))  # 'win', 'loss', 'breakeven', 'active'
    exit_price = db.Column(db.Float)
    pnl = db.Column(db.Float)
    lessons_learned = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ForecastPath(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(10), nullable=False)
    path_type = db.Column(db.String(50))  # 'momentum', 'retest', 'breakdown', 'sideways'
    probability = db.Column(db.Float)
    price_targets = db.Column(db.JSON)  # Store array of price points
    timeframe_days = db.Column(db.Integer, default=5)
    risk_zones = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class AIAnalysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(10), nullable=False)
    analysis_text = db.Column(db.Text)
    mood_tag = db.Column(db.String(20))  # 'breakout', 'reversal', 'risky', 'confirmed'
    historical_comparison = db.Column(db.Text)
    chart_story = db.Column(db.JSON)  # Store hover comments for chart levels
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class PatternEvolution(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(10), nullable=False)
    pattern_type = db.Column(db.String(50))  # 'bull_flag', 'cup_and_handle', etc.
    confidence_score = db.Column(db.Float)
    stage = db.Column(db.String(30))  # 'forming', 'building', 'mature', 'apex_approaching'
    completion_percentage = db.Column(db.Float)
    time_in_pattern = db.Column(db.Integer)  # days
    
    # Evolution metrics
    volatility_trend = db.Column(db.Float)
    volume_trend = db.Column(db.Float)
    momentum_change = db.Column(db.Float)
    support_resistance_strength = db.Column(db.Float)
    
    # Timing predictions
    estimated_days_to_breakout = db.Column(db.Integer)
    breakout_probability_5_days = db.Column(db.Float)
    breakout_probability_10_days = db.Column(db.Float)
    direction_bias = db.Column(db.Float)  # 0-1 (bearish to bullish)
    timing_confidence = db.Column(db.Float)
    
    # Key levels
    resistance_level = db.Column(db.Float)
    support_level = db.Column(db.Float)
    breakout_confirmation_level = db.Column(db.Float)
    breakdown_confirmation_level = db.Column(db.Float)
    
    # Pattern-specific data
    pattern_data = db.Column(db.JSON)  # Store pattern-specific metrics
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Personalized Recommendation System Models
class UserTradingProfile(db.Model):
    __tablename__ = 'user_trading_profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    
    # Risk and style preferences
    risk_tolerance = db.Column(db.String(20), default='moderate')  # conservative, moderate, aggressive
    trading_style = db.Column(db.String(20), default='swing')     # day_trading, short_term, swing, position
    avg_holding_period = db.Column(db.Integer, default=21)        # days
    
    # Sector and market preferences
    preferred_sectors = db.Column(db.JSON)                        # Array of sector names
    market_cap_preference = db.Column(db.String(10), default='large')  # small, mid, large
    price_range_min = db.Column(db.Float, default=10.0)
    price_range_max = db.Column(db.Float, default=500.0)
    preferred_price = db.Column(db.Float, default=100.0)
    
    # Performance metrics
    success_rate = db.Column(db.Float, default=0.6)
    avg_winner_pct = db.Column(db.Float, default=8.0)
    avg_loser_pct = db.Column(db.Float, default=-4.0)
    total_return_pct = db.Column(db.Float, default=0.0)
    sharpe_ratio = db.Column(db.Float, default=1.0)
    max_drawdown_pct = db.Column(db.Float, default=0.0)
    
    # Technical preferences
    volatility_preference = db.Column(db.Float, default=0.15)
    technical_indicators = db.Column(db.JSON)  # Array of preferred indicators
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='trading_profile')

class StockRecommendation(db.Model):
    __tablename__ = 'stock_recommendations'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    symbol = db.Column(db.String(10), nullable=False)
    
    # Scoring components
    total_score = db.Column(db.Float, nullable=False)
    technical_score = db.Column(db.Float)
    fundamental_score = db.Column(db.Float)
    sentiment_score = db.Column(db.Float)
    fit_score = db.Column(db.Float)
    
    # Stock data at recommendation time
    current_price = db.Column(db.Float)
    target_price = db.Column(db.Float)
    sector = db.Column(db.String(50))
    market_cap = db.Column(db.BigInteger)
    beta = db.Column(db.Float)
    pe_ratio = db.Column(db.Float)
    volume = db.Column(db.BigInteger)
    
    # Recommendation details
    confidence_level = db.Column(db.String(10))  # High, Medium, Low
    risk_assessment = db.Column(db.String(10))   # High, Medium, Low
    time_horizon = db.Column(db.String(20))      # e.g., "2-8 weeks"
    recommendation_reason = db.Column(db.Text)
    ai_insight = db.Column(db.Text)
    
    # User interaction tracking
    viewed = db.Column(db.Boolean, default=False)
    action_taken = db.Column(db.String(20))      # bought, watchlisted, ignored, rejected
    user_feedback = db.Column(db.String(20))     # excellent, good, neutral, poor
    feedback_notes = db.Column(db.Text)
    
    # Performance tracking
    performance_tracked = db.Column(db.Boolean, default=True)
    price_at_follow_up = db.Column(db.Float)     # Price after time horizon
    recommendation_return_pct = db.Column(db.Float)  # Theoretical return
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)  # When recommendation expires
    
    # Relationships
    user = db.relationship('User', backref='recommendations')

class RecommendationFeedback(db.Model):
    __tablename__ = 'recommendation_feedback'
    id = db.Column(db.Integer, primary_key=True)
    recommendation_id = db.Column(db.Integer, db.ForeignKey('stock_recommendations.id'), nullable=False)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    
    # Feedback details
    feedback_type = db.Column(db.String(20))     # positive, negative, neutral
    rating = db.Column(db.Integer)               # 1-5 stars
    comment = db.Column(db.Text)
    action_taken = db.Column(db.String(20))      # bought, sold, watchlisted, ignored
    entry_price = db.Column(db.Float)            # If they acted on it
    quantity = db.Column(db.Integer)
    
    # Performance if they acted
    exit_price = db.Column(db.Float)
    actual_return_pct = db.Column(db.Float)
    holding_days = db.Column(db.Integer)
    outcome = db.Column(db.String(20))           # win, loss, breakeven, active
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    recommendation = db.relationship('StockRecommendation', backref='feedback')
    user = db.relationship('User', backref='recommendation_feedback')