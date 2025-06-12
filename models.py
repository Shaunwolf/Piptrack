from datetime import datetime
from app import db
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, JSON

class Stock(db.Model):
    id = Column(Integer, primary_key=True)
    symbol = Column(String(10), nullable=False, unique=True)
    name = Column(String(200))
    price = Column(Float)
    rsi = Column(Float)
    volume_spike = Column(Float)
    pattern_type = Column(String(50))
    fibonacci_position = Column(Float)
    confidence_score = Column(Float, default=0.0)
    is_tracked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class TradeJournal(db.Model):
    id = Column(Integer, primary_key=True)
    symbol = Column(String(10), nullable=False)
    entry_price = Column(Float)
    stop_loss = Column(Float)
    take_profit = Column(Float)
    pattern_confirmed = Column(Boolean, default=False)
    screenshot_taken = Column(Boolean, default=False)
    reflection = Column(Text)
    perfect_trade = Column(Boolean, default=False)
    confidence_at_entry = Column(Float)
    outcome = Column(String(20))  # 'win', 'loss', 'breakeven', 'active'
    exit_price = Column(Float)
    pnl = Column(Float)
    lessons_learned = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ForecastPath(db.Model):
    id = Column(Integer, primary_key=True)
    symbol = Column(String(10), nullable=False)
    path_type = Column(String(50))  # 'momentum', 'retest', 'breakdown', 'sideways'
    probability = Column(Float)
    price_targets = Column(JSON)  # Store array of price points
    timeframe_days = Column(Integer, default=5)
    risk_zones = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

class AIAnalysis(db.Model):
    id = Column(Integer, primary_key=True)
    symbol = Column(String(10), nullable=False)
    analysis_text = Column(Text)
    mood_tag = Column(String(20))  # 'breakout', 'reversal', 'risky', 'confirmed'
    historical_comparison = Column(Text)
    chart_story = Column(JSON)  # Store hover comments for chart levels
    created_at = Column(DateTime, default=datetime.utcnow)

class PatternEvolution(db.Model):
    id = Column(Integer, primary_key=True)
    symbol = Column(String(10), nullable=False)
    pattern_type = Column(String(50))  # 'bull_flag', 'cup_and_handle', etc.
    confidence_score = Column(Float)
    stage = Column(String(30))  # 'forming', 'building', 'mature', 'apex_approaching'
    completion_percentage = Column(Float)
    time_in_pattern = Column(Integer)  # days
    
    # Evolution metrics
    volatility_trend = Column(Float)
    volume_trend = Column(Float)
    momentum_change = Column(Float)
    support_resistance_strength = Column(Float)
    
    # Breakout prediction
    estimated_days_to_breakout = Column(Integer)
    breakout_probability_5_days = Column(Float)
    breakout_probability_10_days = Column(Float)
    direction_bias = Column(Float)  # 0-1 (bearish to bullish)
    timing_confidence = Column(Float)
    
    # Key levels
    resistance_level = Column(Float)
    support_level = Column(Float)
    breakout_confirmation_level = Column(Float)
    breakdown_confirmation_level = Column(Float)
    
    # Pattern specific data
    pattern_data = Column(JSON)  # Store pattern-specific metrics
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
