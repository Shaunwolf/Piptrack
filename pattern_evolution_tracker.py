import yfinance as yf
import numpy as np
import pandas as pd
import ta
from datetime import datetime, timedelta
import logging
from scipy import stats
from sklearn.metrics.pairwise import cosine_similarity
import json

class PatternEvolutionTracker:
    def __init__(self):
        self.pattern_templates = {
            'bull_flag': {
                'flagpole_min_length': 5,  # days
                'flag_max_length': 15,     # days
                'consolidation_range': 0.05,  # 5% range
                'volume_decline': True,
                'breakout_volume_spike': 1.5
            },
            'cup_and_handle': {
                'cup_min_length': 30,      # days
                'handle_max_length': 20,   # days
                'cup_depth': (0.12, 0.33), # 12-33% correction
                'handle_depth': 0.15,      # max 15% from cup high
                'rounding_bottom': True
            },
            'ascending_triangle': {
                'min_length': 20,          # days
                'resistance_touches': 3,   # minimum touches
                'support_slope': 'positive',
                'volume_pattern': 'declining_then_spike'
            },
            'descending_triangle': {
                'min_length': 20,
                'support_touches': 3,
                'resistance_slope': 'negative',
                'volume_pattern': 'declining_then_spike'
            },
            'symmetrical_triangle': {
                'min_length': 15,
                'convergence_angle': (15, 45),  # degrees
                'volume_decline': True,
                'breakout_direction': 'trend_continuation'
            }
        }
        
        self.breakout_signals = {
            'volume_confirmation': 1.5,    # 50% above average
            'price_confirmation': 0.02,    # 2% beyond resistance/support
            'momentum_threshold': 0.6,     # RSI or similar
            'pattern_maturity': 0.8        # 80% pattern completion
        }

    def track_pattern_evolution(self, symbol, pattern_type=None):
        """Track how a pattern is evolving and predict breakout timing"""
        try:
            # Get extended historical data
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="6mo", interval="1d")
            
            if hist.empty:
                return None
            
            # Detect active patterns
            if pattern_type:
                patterns = [self.analyze_specific_pattern(hist, pattern_type)]
            else:
                patterns = self.detect_all_patterns(hist)
            
            evolution_data = []
            
            for pattern in patterns:
                if pattern and pattern['confidence'] > 0.6:
                    evolution = self.calculate_pattern_evolution(hist, pattern)
                    breakout_prediction = self.predict_breakout_timing(hist, pattern, evolution)
                    
                    evolution_data.append({
                        'pattern_type': pattern['type'],
                        'confidence': pattern['confidence'],
                        'evolution': evolution,
                        'breakout_prediction': breakout_prediction,
                        'current_stage': pattern.get('stage', 'unknown'),
                        'completion_percentage': pattern.get('completion', 0),
                        'time_in_pattern': pattern.get('duration', 0)
                    })
            
            return {
                'symbol': symbol,
                'timestamp': datetime.now().isoformat(),
                'patterns': evolution_data,
                'overall_breakout_probability': self.calculate_overall_breakout_probability(evolution_data)
            }
            
        except Exception as e:
            logging.error(f"Error tracking pattern evolution for {symbol}: {e}")
            return None

    def detect_all_patterns(self, hist):
        """Detect all active patterns in the price data"""
        patterns = []
        
        # Bull Flag Pattern
        bull_flag = self.detect_bull_flag(hist)
        if bull_flag:
            patterns.append(bull_flag)
        
        # Cup and Handle
        cup_handle = self.detect_cup_and_handle(hist)
        if cup_handle:
            patterns.append(cup_handle)
        
        # Triangle Patterns
        ascending_triangle = self.detect_ascending_triangle(hist)
        if ascending_triangle:
            patterns.append(ascending_triangle)
        
        descending_triangle = self.detect_descending_triangle(hist)
        if descending_triangle:
            patterns.append(descending_triangle)
        
        symmetrical_triangle = self.detect_symmetrical_triangle(hist)
        if symmetrical_triangle:
            patterns.append(symmetrical_triangle)
        
        return patterns

    def detect_bull_flag(self, hist):
        """Detect bull flag pattern with evolution tracking"""
        try:
            closes = hist['Close'].values
            volumes = hist['Volume'].values
            highs = hist['High'].values
            lows = hist['Low'].values
            
            # Look for flagpole (strong upward move)
            for i in range(20, len(closes) - 15):
                # Check for flagpole
                flagpole_start = i - 20
                flagpole_end = i
                
                flagpole_gain = (closes[flagpole_end] - closes[flagpole_start]) / closes[flagpole_start]
                
                if flagpole_gain > 0.15:  # 15% minimum gain
                    # Look for flag consolidation
                    flag_period = closes[flagpole_end:flagpole_end + 15]
                    if len(flag_period) < 5:
                        continue
                    
                    flag_high = max(flag_period)
                    flag_low = min(flag_period)
                    flag_range = (flag_high - flag_low) / flag_high
                    
                    # Check consolidation criteria
                    if flag_range < 0.08:  # Tight consolidation
                        volume_trend = self.calculate_volume_trend(volumes[flagpole_end:flagpole_end + 10])
                        
                        pattern = {
                            'type': 'bull_flag',
                            'start_date': hist.index[flagpole_start],
                            'flagpole_end': hist.index[flagpole_end],
                            'current_date': hist.index[-1],
                            'flagpole_gain': flagpole_gain,
                            'consolidation_range': flag_range,
                            'volume_declining': volume_trend < -0.1,
                            'confidence': self.calculate_bull_flag_confidence(flagpole_gain, flag_range, volume_trend),
                            'stage': self.determine_flag_stage(hist.index[flagpole_end:], flag_period),
                            'completion': min(len(flag_period) / 15, 1.0),
                            'duration': len(flag_period)
                        }
                        
                        if pattern['confidence'] > 0.6:
                            return pattern
            
            return None
            
        except Exception as e:
            logging.error(f"Error detecting bull flag: {e}")
            return None

    def detect_cup_and_handle(self, hist):
        """Detect cup and handle pattern"""
        try:
            closes = hist['Close'].values
            
            if len(closes) < 50:
                return None
            
            # Look for cup formation (U-shaped recovery)
            for i in range(30, len(closes) - 20):
                cup_start = i - 30
                cup_end = i
                
                cup_data = closes[cup_start:cup_end]
                cup_high = max(cup_data)
                cup_low = min(cup_data)
                cup_depth = (cup_high - cup_low) / cup_high
                
                # Check if it's a valid cup depth
                if 0.12 <= cup_depth <= 0.35:
                    # Check for U-shape (rounding bottom)
                    low_index = np.argmin(cup_data) + cup_start
                    
                    # Look for handle formation
                    handle_start = cup_end
                    handle_data = closes[handle_start:handle_start + 15]
                    
                    if len(handle_data) > 5:
                        handle_high = max(handle_data)
                        handle_low = min(handle_data)
                        handle_depth = (handle_high - handle_low) / handle_high
                        
                        if handle_depth < 0.15:  # Shallow handle
                            pattern = {
                                'type': 'cup_and_handle',
                                'start_date': hist.index[cup_start],
                                'cup_end': hist.index[cup_end],
                                'current_date': hist.index[-1],
                                'cup_depth': cup_depth,
                                'handle_depth': handle_depth,
                                'confidence': self.calculate_cup_handle_confidence(cup_depth, handle_depth, len(cup_data)),
                                'stage': 'handle_formation' if len(handle_data) < 15 else 'mature',
                                'completion': min(len(handle_data) / 15, 1.0),
                                'duration': len(cup_data) + len(handle_data)
                            }
                            
                            if pattern['confidence'] > 0.6:
                                return pattern
            
            return None
            
        except Exception as e:
            logging.error(f"Error detecting cup and handle: {e}")
            return None

    def detect_ascending_triangle(self, hist):
        """Detect ascending triangle pattern"""
        try:
            highs = hist['High'].values
            lows = hist['Low'].values
            closes = hist['Close'].values
            
            if len(closes) < 20:
                return None
            
            # Look for horizontal resistance and ascending support
            for i in range(20, len(closes)):
                period_data = closes[i-20:i]
                period_highs = highs[i-20:i]
                period_lows = lows[i-20:i]
                
                # Find resistance level (horizontal)
                resistance_touches = self.find_resistance_touches(period_highs)
                
                # Find support trend (ascending)
                support_slope = self.calculate_support_slope(period_lows)
                
                if len(resistance_touches) >= 2 and support_slope > 0:
                    convergence = self.calculate_triangle_convergence(period_highs, period_lows)
                    
                    pattern = {
                        'type': 'ascending_triangle',
                        'start_date': hist.index[i-20],
                        'current_date': hist.index[-1],
                        'resistance_level': np.mean([period_highs[j] for j in resistance_touches]),
                        'support_slope': support_slope,
                        'convergence_progress': convergence,
                        'confidence': self.calculate_triangle_confidence(resistance_touches, support_slope),
                        'stage': 'building' if convergence < 0.8 else 'apex_approaching',
                        'completion': convergence,
                        'duration': 20
                    }
                    
                    if pattern['confidence'] > 0.6:
                        return pattern
            
            return None
            
        except Exception as e:
            logging.error(f"Error detecting ascending triangle: {e}")
            return None

    def detect_descending_triangle(self, hist):
        """Detect descending triangle pattern"""
        try:
            highs = hist['High'].values
            lows = hist['Low'].values
            closes = hist['Close'].values
            
            if len(closes) < 20:
                return None
            
            # Look for horizontal support and descending resistance
            for i in range(20, len(closes)):
                period_data = closes[i-20:i]
                period_highs = highs[i-20:i]
                period_lows = lows[i-20:i]
                
                # Find support level (horizontal)
                support_touches = self.find_support_touches(period_lows)
                
                # Find resistance trend (descending)
                resistance_slope = self.calculate_resistance_slope(period_highs)
                
                if len(support_touches) >= 2 and resistance_slope < 0:
                    convergence = self.calculate_triangle_convergence(period_highs, period_lows)
                    
                    pattern = {
                        'type': 'descending_triangle',
                        'start_date': hist.index[i-20],
                        'current_date': hist.index[-1],
                        'support_level': np.mean([period_lows[j] for j in support_touches]),
                        'resistance_slope': resistance_slope,
                        'convergence_progress': convergence,
                        'confidence': self.calculate_triangle_confidence(support_touches, abs(resistance_slope)),
                        'stage': 'building' if convergence < 0.8 else 'apex_approaching',
                        'completion': convergence,
                        'duration': 20
                    }
                    
                    if pattern['confidence'] > 0.6:
                        return pattern
            
            return None
            
        except Exception as e:
            logging.error(f"Error detecting descending triangle: {e}")
            return None

    def detect_symmetrical_triangle(self, hist):
        """Detect symmetrical triangle pattern"""
        try:
            highs = hist['High'].values
            lows = hist['Low'].values
            closes = hist['Close'].values
            
            if len(closes) < 15:
                return None
            
            # Look for converging trendlines
            for i in range(15, len(closes)):
                period_highs = highs[i-15:i]
                period_lows = lows[i-15:i]
                
                # Calculate trendline slopes
                resistance_slope = self.calculate_resistance_slope(period_highs)
                support_slope = self.calculate_support_slope(period_lows)
                
                # Check for convergence (negative resistance slope, positive support slope)
                if resistance_slope < -0.001 and support_slope > 0.001:
                    convergence = self.calculate_triangle_convergence(period_highs, period_lows)
                    
                    pattern = {
                        'type': 'symmetrical_triangle',
                        'start_date': hist.index[i-15],
                        'current_date': hist.index[-1],
                        'resistance_slope': resistance_slope,
                        'support_slope': support_slope,
                        'convergence_progress': convergence,
                        'confidence': self.calculate_symmetrical_triangle_confidence(resistance_slope, support_slope),
                        'stage': 'building' if convergence < 0.7 else 'apex_approaching',
                        'completion': convergence,
                        'duration': 15
                    }
                    
                    if pattern['confidence'] > 0.6:
                        return pattern
            
            return None
            
        except Exception as e:
            logging.error(f"Error detecting symmetrical triangle: {e}")
            return None

    def calculate_pattern_evolution(self, hist, pattern):
        """Calculate how the pattern has evolved over time"""
        try:
            evolution = {
                'pattern_age_days': pattern['duration'],
                'volatility_trend': self.calculate_volatility_trend(hist, pattern),
                'volume_trend': self.calculate_volume_trend_in_pattern(hist, pattern),
                'momentum_change': self.calculate_momentum_change(hist, pattern),
                'support_resistance_strength': self.calculate_sr_strength(hist, pattern),
                'breakout_probability_trend': self.calculate_breakout_probability_trend(hist, pattern)
            }
            
            return evolution
            
        except Exception as e:
            logging.error(f"Error calculating pattern evolution: {e}")
            return {}

    def predict_breakout_timing(self, hist, pattern, evolution):
        """Predict when a breakout is likely to occur"""
        try:
            current_stage = pattern.get('stage', 'unknown')
            completion = pattern.get('completion', 0)
            
            # Base prediction on pattern type and current stage
            base_days = self.get_base_breakout_timing(pattern['type'], current_stage)
            
            # Adjust based on evolution factors
            volatility_multiplier = 1 + (evolution.get('volatility_trend', 0) * 0.3)
            volume_multiplier = 1 - (evolution.get('volume_trend', 0) * 0.2)
            momentum_multiplier = 1 - (evolution.get('momentum_change', 0) * 0.25)
            
            adjusted_days = base_days * volatility_multiplier * volume_multiplier * momentum_multiplier
            
            # Calculate probability scores
            breakout_probability = self.calculate_breakout_probability(pattern, evolution)
            direction_bias = self.calculate_breakout_direction_bias(hist, pattern)
            
            # Determine timing confidence
            timing_confidence = self.calculate_timing_confidence(pattern, evolution)
            
            prediction = {
                'estimated_days_to_breakout': max(1, int(adjusted_days)),
                'breakout_probability_next_5_days': min(breakout_probability * 5 / adjusted_days, 0.95),
                'breakout_probability_next_10_days': min(breakout_probability * 10 / adjusted_days, 0.98),
                'direction_bias': direction_bias,
                'timing_confidence': timing_confidence,
                'key_levels': self.identify_key_breakout_levels(hist, pattern),
                'volume_confirmation_needed': evolution.get('volume_trend', 0) < 0.5,
                'pattern_maturity': completion
            }
            
            return prediction
            
        except Exception as e:
            logging.error(f"Error predicting breakout timing: {e}")
            return {}

    def calculate_overall_breakout_probability(self, patterns):
        """Calculate overall breakout probability across all detected patterns"""
        if not patterns:
            return 0.0
        
        total_probability = 0
        total_weight = 0
        
        for pattern in patterns:
            breakout_pred = pattern.get('breakout_prediction', {})
            prob_5_days = breakout_pred.get('breakout_probability_next_5_days', 0)
            confidence = pattern.get('confidence', 0)
            
            total_probability += prob_5_days * confidence
            total_weight += confidence
        
        return total_probability / total_weight if total_weight > 0 else 0.0

    # Helper methods for pattern detection and analysis
    def calculate_volume_trend(self, volumes):
        """Calculate volume trend over period"""
        if len(volumes) < 5:
            return 0
        
        x = np.arange(len(volumes))
        slope, _, r_value, _, _ = stats.linregress(x, volumes)
        return slope * r_value ** 2  # Slope adjusted by R-squared

    def find_resistance_touches(self, highs, tolerance=0.02):
        """Find points where price touched resistance level"""
        max_high = max(highs)
        resistance_level = max_high * (1 - tolerance)
        
        touches = []
        for i, high in enumerate(highs):
            if high >= resistance_level:
                touches.append(i)
        
        return touches

    def find_support_touches(self, lows, tolerance=0.02):
        """Find points where price touched support level"""
        min_low = min(lows)
        support_level = min_low * (1 + tolerance)
        
        touches = []
        for i, low in enumerate(lows):
            if low <= support_level:
                touches.append(i)
        
        return touches

    def calculate_support_slope(self, lows):
        """Calculate slope of support trendline"""
        x = np.arange(len(lows))
        slope, _, _, _, _ = stats.linregress(x, lows)
        return slope

    def calculate_resistance_slope(self, highs):
        """Calculate slope of resistance trendline"""
        x = np.arange(len(highs))
        slope, _, _, _, _ = stats.linregress(x, highs)
        return slope

    def calculate_triangle_convergence(self, highs, lows):
        """Calculate how much triangle has converged (0-1)"""
        initial_range = max(highs[:5]) - min(lows[:5])
        current_range = max(highs[-5:]) - min(lows[-5:])
        
        if initial_range == 0:
            return 0
        
        convergence = 1 - (current_range / initial_range)
        return max(0, min(1, convergence))

    def calculate_bull_flag_confidence(self, flagpole_gain, consolidation_range, volume_trend):
        """Calculate confidence score for bull flag pattern"""
        confidence = 0
        
        # Flagpole strength (max 40 points)
        confidence += min(flagpole_gain * 100, 40)
        
        # Tight consolidation (max 30 points)
        confidence += max(0, 30 - (consolidation_range * 1000))
        
        # Declining volume (max 30 points)
        if volume_trend < -0.05:
            confidence += 30
        elif volume_trend < 0:
            confidence += 15
        
        return min(confidence / 100, 1.0)

    def calculate_cup_handle_confidence(self, cup_depth, handle_depth, cup_length):
        """Calculate confidence score for cup and handle pattern"""
        confidence = 0
        
        # Ideal cup depth (max 40 points)
        if 0.15 <= cup_depth <= 0.25:
            confidence += 40
        elif 0.12 <= cup_depth <= 0.35:
            confidence += 25
        
        # Shallow handle (max 30 points)
        if handle_depth < 0.10:
            confidence += 30
        elif handle_depth < 0.15:
            confidence += 20
        
        # Sufficient cup length (max 30 points)
        if cup_length >= 30:
            confidence += 30
        elif cup_length >= 20:
            confidence += 20
        
        return min(confidence / 100, 1.0)

    def calculate_triangle_confidence(self, touches, slope_strength):
        """Calculate confidence score for triangle patterns"""
        confidence = 0
        
        # Number of touches (max 40 points)
        confidence += min(len(touches) * 10, 40)
        
        # Slope strength (max 30 points)
        confidence += min(abs(slope_strength) * 10000, 30)
        
        # Pattern clarity (max 30 points)
        if len(touches) >= 3:
            confidence += 30
        elif len(touches) >= 2:
            confidence += 20
        
        return min(confidence / 100, 1.0)

    def calculate_symmetrical_triangle_confidence(self, resistance_slope, support_slope):
        """Calculate confidence for symmetrical triangle"""
        confidence = 0
        
        # Balanced slopes (max 50 points)
        slope_balance = abs(abs(resistance_slope) - abs(support_slope))
        confidence += max(0, 50 - (slope_balance * 50000))
        
        # Adequate slope strength (max 50 points)
        avg_slope = (abs(resistance_slope) + abs(support_slope)) / 2
        confidence += min(avg_slope * 25000, 50)
        
        return min(confidence / 100, 1.0)

    def get_base_breakout_timing(self, pattern_type, stage):
        """Get base timing estimate for breakout based on pattern type and stage"""
        timing_map = {
            'bull_flag': {'building': 7, 'mature': 3, 'apex_approaching': 1},
            'cup_and_handle': {'handle_formation': 10, 'mature': 5},
            'ascending_triangle': {'building': 12, 'apex_approaching': 4},
            'descending_triangle': {'building': 12, 'apex_approaching': 4},
            'symmetrical_triangle': {'building': 8, 'apex_approaching': 3}
        }
        
        return timing_map.get(pattern_type, {}).get(stage, 7)

    def calculate_breakout_probability(self, pattern, evolution):
        """Calculate probability of breakout occurring"""
        base_prob = pattern.get('confidence', 0.5)
        
        # Adjust based on evolution factors
        volatility_factor = 1 + (evolution.get('volatility_trend', 0) * 0.2)
        volume_factor = 1 + (evolution.get('volume_trend', 0) * 0.15)
        momentum_factor = 1 + (evolution.get('momentum_change', 0) * 0.25)
        
        adjusted_prob = base_prob * volatility_factor * volume_factor * momentum_factor
        
        return min(adjusted_prob, 0.95)

    def calculate_breakout_direction_bias(self, hist, pattern):
        """Calculate bias toward bullish or bearish breakout"""
        pattern_type = pattern['type']
        
        # Pattern-specific biases
        bullish_patterns = ['bull_flag', 'cup_and_handle', 'ascending_triangle']
        bearish_patterns = ['descending_triangle']
        
        if pattern_type in bullish_patterns:
            base_bias = 0.7  # 70% bullish
        elif pattern_type in bearish_patterns:
            base_bias = 0.3  # 30% bullish (70% bearish)
        else:
            base_bias = 0.5  # Neutral
        
        # Adjust based on overall trend
        recent_trend = self.calculate_recent_trend(hist)
        trend_adjustment = recent_trend * 0.2
        
        final_bias = base_bias + trend_adjustment
        return max(0.1, min(0.9, final_bias))

    def calculate_timing_confidence(self, pattern, evolution):
        """Calculate confidence in timing prediction"""
        base_confidence = pattern.get('confidence', 0.5)
        completion = pattern.get('completion', 0)
        
        # Higher confidence for more mature patterns
        maturity_bonus = completion * 0.3
        
        # Adjust based on evolution consistency
        evolution_consistency = self.calculate_evolution_consistency(evolution)
        
        timing_confidence = base_confidence + maturity_bonus + evolution_consistency
        return min(timing_confidence, 0.95)

    def identify_key_breakout_levels(self, hist, pattern):
        """Identify key price levels for breakout confirmation"""
        closes = hist['Close'].values
        current_price = closes[-1]
        
        pattern_type = pattern['type']
        
        if pattern_type == 'bull_flag':
            resistance = pattern.get('flagpole_end_price', current_price * 1.02)
            support = current_price * 0.98
        elif pattern_type in ['ascending_triangle', 'descending_triangle']:
            resistance = pattern.get('resistance_level', current_price * 1.025)
            support = pattern.get('support_level', current_price * 0.975)
        else:
            resistance = current_price * 1.02
            support = current_price * 0.98
        
        return {
            'resistance_level': resistance,
            'support_level': support,
            'breakout_confirmation': resistance * 1.01,
            'breakdown_confirmation': support * 0.99
        }

    def calculate_recent_trend(self, hist, periods=20):
        """Calculate recent price trend"""
        closes = hist['Close'].values[-periods:]
        x = np.arange(len(closes))
        slope, _, r_value, _, _ = stats.linregress(x, closes)
        
        # Normalize slope and adjust by R-squared
        normalized_slope = slope / closes[0] * len(closes)
        return normalized_slope * r_value ** 2

    def calculate_evolution_consistency(self, evolution):
        """Calculate how consistent the evolution indicators are"""
        indicators = [
            evolution.get('volatility_trend', 0),
            evolution.get('volume_trend', 0),
            evolution.get('momentum_change', 0)
        ]
        
        # Check if indicators are pointing in same direction
        positive_count = sum(1 for x in indicators if x > 0.1)
        negative_count = sum(1 for x in indicators if x < -0.1)
        
        if positive_count >= 2 or negative_count >= 2:
            return 0.2  # Consistent signals
        else:
            return 0.0  # Mixed signals

    def calculate_volatility_trend(self, hist, pattern):
        """Calculate volatility trend within pattern timeframe"""
        pattern_start = pattern.get('start_date')
        if not pattern_start:
            return 0
        
        try:
            pattern_data = hist[hist.index >= pattern_start]
            returns = pattern_data['Close'].pct_change().dropna()
            
            # Calculate rolling volatility
            window = min(10, len(returns) // 2)
            if window < 3:
                return 0
            
            rolling_vol = returns.rolling(window=window).std()
            
            # Calculate trend in volatility
            x = np.arange(len(rolling_vol.dropna()))
            y = rolling_vol.dropna().values
            
            if len(x) < 3:
                return 0
            
            slope, _, r_value, _, _ = stats.linregress(x, y)
            return slope * r_value ** 2
            
        except Exception as e:
            logging.error(f"Error calculating volatility trend: {e}")
            return 0

    def calculate_volume_trend_in_pattern(self, hist, pattern):
        """Calculate volume trend within pattern timeframe"""
        pattern_start = pattern.get('start_date')
        if not pattern_start:
            return 0
        
        try:
            pattern_data = hist[hist.index >= pattern_start]
            volumes = pattern_data['Volume'].values
            
            return self.calculate_volume_trend(volumes)
            
        except Exception as e:
            logging.error(f"Error calculating volume trend in pattern: {e}")
            return 0

    def calculate_momentum_change(self, hist, pattern):
        """Calculate momentum change within pattern"""
        pattern_start = pattern.get('start_date')
        if not pattern_start:
            return 0
        
        try:
            pattern_data = hist[hist.index >= pattern_start]
            closes = pattern_data['Close']
            
            # Calculate RSI trend
            rsi = ta.momentum.rsi(closes)
            
            if len(rsi.dropna()) < 5:
                return 0
            
            # Calculate trend in RSI
            x = np.arange(len(rsi.dropna()))
            y = rsi.dropna().values
            
            slope, _, r_value, _, _ = stats.linregress(x, y)
            return slope * r_value ** 2 / 100  # Normalize to 0-1 range
            
        except Exception as e:
            logging.error(f"Error calculating momentum change: {e}")
            return 0

    def calculate_sr_strength(self, hist, pattern):
        """Calculate support/resistance strength"""
        try:
            pattern_type = pattern['type']
            
            if pattern_type in ['ascending_triangle', 'descending_triangle']:
                if 'resistance_level' in pattern:
                    touches = pattern.get('resistance_touches', 0)
                    return min(touches / 5, 1.0)  # Normalize to 0-1
                elif 'support_level' in pattern:
                    touches = pattern.get('support_touches', 0)
                    return min(touches / 5, 1.0)
            
            return 0.5  # Default moderate strength
            
        except Exception as e:
            logging.error(f"Error calculating S/R strength: {e}")
            return 0.5

    def calculate_breakout_probability_trend(self, hist, pattern):
        """Calculate trend in breakout probability over time"""
        try:
            completion = pattern.get('completion', 0)
            confidence = pattern.get('confidence', 0.5)
            
            # Higher completion and confidence increase breakout probability
            base_prob = (completion + confidence) / 2
            
            # Adjust based on pattern maturity
            age_factor = min(pattern.get('duration', 0) / 30, 1.0)
            
            return base_prob * (1 + age_factor * 0.3)
            
        except Exception as e:
            logging.error(f"Error calculating breakout probability trend: {e}")
            return 0.5

    def analyze_specific_pattern(self, hist, pattern_type):
        """Analyze a specific pattern type"""
        if pattern_type == 'bull_flag':
            return self.detect_bull_flag(hist)
        elif pattern_type == 'cup_and_handle':
            return self.detect_cup_and_handle(hist)
        elif pattern_type == 'ascending_triangle':
            return self.detect_ascending_triangle(hist)
        elif pattern_type == 'descending_triangle':
            return self.detect_descending_triangle(hist)
        elif pattern_type == 'symmetrical_triangle':
            return self.detect_symmetrical_triangle(hist)
        else:
            return None

    def determine_flag_stage(self, dates, flag_data):
        """Determine current stage of flag pattern"""
        if len(flag_data) < 5:
            return 'forming'
        elif len(flag_data) < 12:
            return 'building'
        else:
            return 'mature'