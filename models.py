from datetime import datetime
from app import db
from flask_dance.consumer.storage.sqla import OAuthConsumerMixin
from flask_login import UserMixin
from sqlalchemy import UniqueConstraint


# (IMPORTANT) This table is mandatory for Replit Auth, don't drop it.
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.String, primary_key=True)
    email = db.Column(db.String, unique=True, nullable=True)
    first_name = db.Column(db.String, nullable=True)
    last_name = db.Column(db.String, nullable=True)
    profile_image_url = db.Column(db.String, nullable=True)

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