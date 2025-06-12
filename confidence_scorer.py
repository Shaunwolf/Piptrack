import numpy as np
import pandas as pd
import ta
import logging
from datetime import datetime

class ConfidenceScorer:
    def __init__(self):
        # Weights for different factors in confidence calculation
        self.weights = {
            'rsi_momentum': 0.20,
            'volume_surge': 0.25,
            'pattern_strength': 0.20,
            'price_position': 0.15,
            'trend_alignment': 0.15,
            'volatility_factor': 0.05
        }
    
    def calculate_score(self, stock_data):
        """Calculate confidence score (0-100) based on multiple factors"""
        try:
            if not stock_data:
                return 0
            
            scores = {}
            
            # RSI Momentum Score (0-100)
            scores['rsi_momentum'] = self.calculate_rsi_score(stock_data.get('rsi', 50))
            
            # Volume Surge Score (0-100)
            scores['volume_surge'] = self.calculate_volume_score(stock_data.get('volume_spike', 0))
            
            # Pattern Strength Score (0-100)
            scores['pattern_strength'] = self.calculate_pattern_score(stock_data.get('pattern_type', 'Neutral'))
            
            # Price Position Score (0-100) - Fibonacci position
            scores['price_position'] = self.calculate_position_score(stock_data.get('fibonacci_position', 50))
            
            # Trend Alignment Score (0-100)
            scores['trend_alignment'] = self.calculate_trend_score(stock_data)
            
            # Volatility Factor (0-100)
            scores['volatility_factor'] = self.calculate_volatility_score(stock_data)
            
            # Calculate weighted average
            total_score = sum(scores[factor] * self.weights[factor] for factor in scores)
            
            # Apply momentum boost for exceptional setups
            if scores['volume_surge'] > 80 and scores['rsi_momentum'] > 70:
                total_score = min(100, total_score * 1.1)  # 10% boost
            
            # Apply penalty for risky setups
            if scores['rsi_momentum'] < 20 or scores['rsi_momentum'] > 95:
                total_score *= 0.8  # 20% penalty
            
            return round(max(0, min(100, total_score)), 2)
            
        except Exception as e:
            logging.error(f"Error calculating confidence score: {e}")
            return 0
    
    def calculate_rsi_score(self, rsi):
        """Calculate RSI-based momentum score"""
        try:
            if pd.isna(rsi) or rsi is None:
                return 50  # Neutral
            
            # Optimal RSI ranges for bullish setups
            if 45 <= rsi <= 65:
                return 100  # Perfect range
            elif 35 <= rsi < 45 or 65 < rsi <= 75:
                return 80   # Good range
            elif 25 <= rsi < 35 or 75 < rsi <= 85:
                return 60   # Acceptable range
            else:
                return 20   # Extreme levels - risky
                
        except Exception as e:
            logging.error(f"Error calculating RSI score: {e}")
            return 50
    
    def calculate_volume_score(self, volume_spike):
        """Calculate volume surge score"""
        try:
            # Volume surge scoring
            if volume_spike >= 200:
                return 100  # Exceptional volume
            elif volume_spike >= 100:
                return 90   # Very high volume
            elif volume_spike >= 50:
                return 75   # High volume
            elif volume_spike >= 25:
                return 60   # Above average volume
            elif volume_spike >= 0:
                return 40   # Normal volume
            else:
                return 20   # Below average volume
                
        except Exception as e:
            logging.error(f"Error calculating volume score: {e}")
            return 40
    
    def calculate_pattern_score(self, pattern_type):
        """Calculate pattern strength score"""
        try:
            pattern_scores = {
                'Bullish Trend': 90,
                'Bull Flag': 95,
                'Breakout': 85,
                'Consolidation': 70,
                'Neutral': 50,
                'Bearish Trend': 30,
                'Bear Flag': 20,
                'Breakdown': 15
            }
            
            return pattern_scores.get(pattern_type, 50)
            
        except Exception as e:
            logging.error(f"Error calculating pattern score: {e}")
            return 50
    
    def calculate_position_score(self, fibonacci_position):
        """Calculate score based on Fibonacci position"""
        try:
            if pd.isna(fibonacci_position) or fibonacci_position is None:
                return 50
            
            # Fibonacci level scoring (bullish bias)
            if 60 <= fibonacci_position <= 80:
                return 95   # Golden zone
            elif 50 <= fibonacci_position < 60 or 80 < fibonacci_position <= 90:
                return 80   # Good position
            elif 40 <= fibonacci_position < 50 or 90 < fibonacci_position <= 95:
                return 65   # Acceptable
            elif fibonacci_position < 30:
                return 30   # Oversold - risky
            else:
                return 40   # Near highs - limited upside
                
        except Exception as e:
            logging.error(f"Error calculating position score: {e}")
            return 50
    
    def calculate_trend_score(self, stock_data):
        """Calculate trend alignment score"""
        try:
            pattern = stock_data.get('pattern_type', 'Neutral')
            price = stock_data.get('price', 0)
            
            # Simple trend scoring based on pattern
            if 'Bullish' in pattern or 'Bull' in pattern or pattern == 'Breakout':
                return 85
            elif 'Bearish' in pattern or 'Bear' in pattern or pattern == 'Breakdown':
                return 25
            elif pattern == 'Consolidation':
                return 60
            else:
                return 50
                
        except Exception as e:
            logging.error(f"Error calculating trend score: {e}")
            return 50
    
    def calculate_volatility_score(self, stock_data):
        """Calculate volatility-based score"""
        try:
            # Use volume spike as proxy for volatility
            volume_spike = stock_data.get('volume_spike', 0)
            
            # Moderate volatility is preferred
            if 25 <= volume_spike <= 75:
                return 80   # Good volatility
            elif 75 < volume_spike <= 150:
                return 90   # High but manageable volatility
            elif volume_spike > 150:
                return 70   # Very high volatility - risky
            else:
                return 60   # Low volatility
                
        except Exception as e:
            logging.error(f"Error calculating volatility score: {e}")
            return 60
    
    def get_score_breakdown(self, stock_data):
        """Get detailed breakdown of confidence score components"""
        try:
            breakdown = {}
            
            # Calculate individual scores
            breakdown['rsi_momentum'] = {
                'score': self.calculate_rsi_score(stock_data.get('rsi', 50)),
                'weight': self.weights['rsi_momentum'],
                'description': 'RSI momentum analysis'
            }
            
            breakdown['volume_surge'] = {
                'score': self.calculate_volume_score(stock_data.get('volume_spike', 0)),
                'weight': self.weights['volume_surge'],
                'description': 'Volume surge analysis'
            }
            
            breakdown['pattern_strength'] = {
                'score': self.calculate_pattern_score(stock_data.get('pattern_type', 'Neutral')),
                'weight': self.weights['pattern_strength'],
                'description': 'Chart pattern strength'
            }
            
            breakdown['price_position'] = {
                'score': self.calculate_position_score(stock_data.get('fibonacci_position', 50)),
                'weight': self.weights['price_position'],
                'description': 'Fibonacci position analysis'
            }
            
            breakdown['trend_alignment'] = {
                'score': self.calculate_trend_score(stock_data),
                'weight': self.weights['trend_alignment'],
                'description': 'Trend alignment'
            }
            
            breakdown['volatility_factor'] = {
                'score': self.calculate_volatility_score(stock_data),
                'weight': self.weights['volatility_factor'],
                'description': 'Volatility assessment'
            }
            
            # Calculate weighted contributions
            for component in breakdown:
                breakdown[component]['contribution'] = round(
                    breakdown[component]['score'] * breakdown[component]['weight'], 2
                )
            
            return breakdown
            
        except Exception as e:
            logging.error(f"Error getting score breakdown: {e}")
            return {}
