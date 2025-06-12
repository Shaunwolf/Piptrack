import yfinance as yf
import numpy as np
import pandas as pd
import ta
from datetime import datetime, timedelta
import logging

class ForecastingEngine:
    def __init__(self):
        self.forecast_days = 5
        self.path_types = ['momentum', 'retest', 'breakdown', 'sideways']
    
    def generate_spaghetti_model(self, symbol):
        """Generate 3-5 probable price paths for the stock"""
        try:
            # Get stock data
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="3mo")
            
            if hist.empty:
                return []
            
            current_price = hist['Close'].iloc[-1]
            
            # Calculate volatility and trend metrics
            volatility = hist['Close'].pct_change().std() * np.sqrt(252)  # Annualized
            
            # Generate paths
            paths = []
            
            # 1. Momentum Extension Path
            momentum_path = self.generate_momentum_path(hist, current_price, volatility)
            paths.append(momentum_path)
            
            # 2. Retest and Run Path
            retest_path = self.generate_retest_path(hist, current_price, volatility)
            paths.append(retest_path)
            
            # 3. Breakdown Path
            breakdown_path = self.generate_breakdown_path(hist, current_price, volatility)
            paths.append(breakdown_path)
            
            # 4. Sideways Fade Path
            sideways_path = self.generate_sideways_path(hist, current_price, volatility)
            paths.append(sideways_path)
            
            # Calculate probabilities based on current market conditions
            paths = self.calculate_path_probabilities(paths, hist)
            
            return paths
            
        except Exception as e:
            logging.error(f"Error generating spaghetti model for {symbol}: {e}")
            return []
    
    def generate_momentum_path(self, hist, current_price, volatility):
        """Generate momentum extension scenario"""
        # Calculate support and resistance levels
        resistance = self.find_resistance_level(hist, current_price)
        
        # Generate upward trending path
        targets = []
        price = current_price
        
        for day in range(self.forecast_days):
            # Momentum typically shows acceleration
            daily_move = volatility * 0.02 * (1 + day * 0.1)  # Increasing momentum
            price *= (1 + daily_move)
            targets.append(round(price, 2))
        
        return {
            'type': 'momentum',
            'color': '#10B981',  # Green
            'probability': 0.25,  # Will be recalculated
            'targets': targets,
            'risk_zones': [resistance * 0.95, resistance * 1.05],
            'description': 'Bullish breakout with sustained momentum'
        }
    
    def generate_retest_path(self, hist, current_price, volatility):
        """Generate retest and run scenario"""
        support = self.find_support_level(hist, current_price)
        
        targets = []
        price = current_price
        
        for day in range(self.forecast_days):
            if day < 2:
                # Initial pullback to support
                daily_move = -volatility * 0.015
            else:
                # Recovery and run
                daily_move = volatility * 0.025
            
            price *= (1 + daily_move)
            targets.append(round(price, 2))
        
        return {
            'type': 'retest',
            'color': '#3B82F6',  # Blue
            'probability': 0.25,
            'targets': targets,
            'risk_zones': [support * 0.95, support * 1.05],
            'description': 'Pullback to support followed by rally'
        }
    
    def generate_breakdown_path(self, hist, current_price, volatility):
        """Generate breakdown scenario"""
        support = self.find_support_level(hist, current_price)
        
        targets = []
        price = current_price
        
        for day in range(self.forecast_days):
            # Consistent downward pressure
            daily_move = -volatility * 0.02
            price *= (1 + daily_move)
            targets.append(round(price, 2))
        
        return {
            'type': 'breakdown',
            'color': '#EF4444',  # Red
            'probability': 0.25,
            'targets': targets,
            'risk_zones': [support * 0.9, support * 1.1],
            'description': 'Support breakdown with continued selling'
        }
    
    def generate_sideways_path(self, hist, current_price, volatility):
        """Generate sideways consolidation scenario"""
        targets = []
        price = current_price
        
        # Create oscillating pattern around current price
        for day in range(self.forecast_days):
            # Random walk with mean reversion
            random_factor = np.random.uniform(-1, 1)
            daily_move = volatility * 0.01 * random_factor * 0.5  # Reduced volatility
            price *= (1 + daily_move)
            targets.append(round(price, 2))
        
        return {
            'type': 'sideways',
            'color': '#6B7280',  # Gray
            'probability': 0.25,
            'targets': targets,
            'risk_zones': [current_price * 0.97, current_price * 1.03],
            'description': 'Range-bound consolidation pattern'
        }
    
    def calculate_path_probabilities(self, paths, hist):
        """Calculate probabilities based on current market conditions"""
        try:
            # Calculate technical indicators
            rsi = ta.momentum.RSIIndicator(hist['Close']).rsi().iloc[-1]
            
            # Volume analysis
            avg_volume = hist['Volume'].rolling(20).mean().iloc[-2]
            current_volume = hist['Volume'].iloc[-1]
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
            
            # Price momentum
            returns = hist['Close'].pct_change().dropna()
            momentum = returns.rolling(5).mean().iloc[-1]
            
            # Adjust probabilities based on conditions
            for path in paths:
                if path['type'] == 'momentum':
                    # Higher probability if RSI not overbought and good volume
                    if rsi < 70 and volume_ratio > 1.5 and momentum > 0:
                        path['probability'] = 0.4
                    elif rsi > 80 or volume_ratio < 1:
                        path['probability'] = 0.1
                    else:
                        path['probability'] = 0.25
                        
                elif path['type'] == 'breakdown':
                    # Higher probability if RSI oversold or negative momentum
                    if rsi > 70 or momentum < -0.02:
                        path['probability'] = 0.4
                    elif rsi < 30:
                        path['probability'] = 0.1
                    else:
                        path['probability'] = 0.25
                        
                elif path['type'] == 'retest':
                    # Higher probability in trending markets
                    if 30 < rsi < 70 and abs(momentum) > 0.01:
                        path['probability'] = 0.3
                    else:
                        path['probability'] = 0.2
                        
                elif path['type'] == 'sideways':
                    # Higher probability in low volatility, neutral RSI
                    if 40 < rsi < 60 and abs(momentum) < 0.005:
                        path['probability'] = 0.4
                    else:
                        path['probability'] = 0.15
            
            # Normalize probabilities to sum to 1
            total_prob = sum(path['probability'] for path in paths)
            for path in paths:
                path['probability'] = round(path['probability'] / total_prob, 3)
            
            return paths
            
        except Exception as e:
            logging.error(f"Error calculating probabilities: {e}")
            # Return equal probabilities if calculation fails
            for path in paths:
                path['probability'] = 0.25
            return paths
    
    def find_support_level(self, hist, current_price):
        """Find nearest support level"""
        try:
            # Use recent lows as support
            recent_data = hist.tail(30)
            lows = recent_data['Low']
            
            # Find the highest low below current price
            support_candidates = lows[lows < current_price]
            if not support_candidates.empty:
                return support_candidates.max()
            else:
                return current_price * 0.95  # Default 5% below
                
        except Exception as e:
            logging.error(f"Error finding support level: {e}")
            return current_price * 0.95
    
    def find_resistance_level(self, hist, current_price):
        """Find nearest resistance level"""
        try:
            # Use recent highs as resistance
            recent_data = hist.tail(30)
            highs = recent_data['High']
            
            # Find the lowest high above current price
            resistance_candidates = highs[highs > current_price]
            if not resistance_candidates.empty:
                return resistance_candidates.min()
            else:
                return current_price * 1.05  # Default 5% above
                
        except Exception as e:
            logging.error(f"Error finding resistance level: {e}")
            return current_price * 1.05
