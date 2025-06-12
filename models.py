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
