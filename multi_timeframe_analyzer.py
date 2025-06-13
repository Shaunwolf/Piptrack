import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Tuple, Optional
import ta
from pattern_evolution_tracker import PatternEvolutionTracker
from confidence_scorer import ConfidenceScorer

class MultiTimeframeAnalyzer:
    def __init__(self):
        self.pattern_tracker = PatternEvolutionTracker()
        self.confidence_scorer = ConfidenceScorer()
        self.timeframes = ['1m', '5m', '15m', '1h', '1d']
        self.timeframe_weights = {
            '1m': 0.10,   # Short-term noise
            '5m': 0.15,   # Scalping timeframe
            '15m': 0.20,  # Day trading
            '1h': 0.25,   # Swing setup
            '1d': 0.30    # Position trading (highest weight)
        }
        
    def analyze_multi_timeframe_patterns(self, symbol: str) -> Dict:
        """Analyze patterns across multiple timeframes and provide alignment scoring"""
        try:
            results = {
                'symbol': symbol,
                'analysis_timestamp': datetime.now().isoformat(),
                'timeframe_data': {},
                'alignment_score': 0,
                'dominant_trend': 'neutral',
                'confluence_zones': [],
                'trade_recommendation': {},
                'risk_assessment': {}
            }
            
            # Collect data for each timeframe
            for timeframe in self.timeframes:
                tf_data = self._analyze_single_timeframe(symbol, timeframe)
                results['timeframe_data'][timeframe] = tf_data
            
            # Calculate cross-timeframe alignment
            results['alignment_score'] = self._calculate_alignment_score(results['timeframe_data'])
            results['dominant_trend'] = self._determine_dominant_trend(results['timeframe_data'])
            results['confluence_zones'] = self._identify_confluence_zones(results['timeframe_data'])
            results['trade_recommendation'] = self._generate_trade_recommendation(results)
            results['risk_assessment'] = self._assess_multi_timeframe_risk(results)
            
            return results
            
        except Exception as e:
            logging.error(f"Error in multi-timeframe analysis for {symbol}: {e}")
            return {'error': str(e), 'symbol': symbol}
    
    def _analyze_single_timeframe(self, symbol: str, timeframe: str) -> Dict:
        """Analyze patterns for a single timeframe"""
        try:
            # Get appropriate period for timeframe
            period = self._get_period_for_timeframe(timeframe)
            
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period, interval=timeframe)
            
            if hist.empty:
                return {'error': 'No data available', 'timeframe': timeframe}
            
            # Basic technical analysis
            hist['RSI'] = ta.momentum.RSIIndicator(hist['Close']).rsi()
            hist['MACD'] = ta.trend.MACD(hist['Close']).macd()
            hist['MACD_Signal'] = ta.trend.MACD(hist['Close']).macd_signal()
            hist['BB_Upper'] = ta.volatility.BollingerBands(hist['Close']).bollinger_hband()
            hist['BB_Lower'] = ta.volatility.BollingerBands(hist['Close']).bollinger_lband()
            hist['Volume_SMA'] = hist['Volume'].rolling(window=20).mean()
            
            # Pattern detection
            patterns = self.pattern_tracker.detect_all_patterns(hist)
            
            # Trend analysis
            trend_strength = self._calculate_trend_strength(hist)
            momentum_score = self._calculate_momentum_score(hist)
            volume_profile = self._analyze_volume_profile(hist)
            
            # Support and resistance levels
            support_resistance = self._find_support_resistance_levels(hist)
            
            return {
                'timeframe': timeframe,
                'current_price': float(hist['Close'].iloc[-1]),
                'trend_strength': trend_strength,
                'momentum_score': momentum_score,
                'patterns': patterns,
                'volume_profile': volume_profile,
                'support_resistance': support_resistance,
                'technical_indicators': {
                    'rsi': float(hist['RSI'].iloc[-1]) if not hist['RSI'].empty else None,
                    'macd': float(hist['MACD'].iloc[-1]) if not hist['MACD'].empty else None,
                    'macd_signal': float(hist['MACD_Signal'].iloc[-1]) if not hist['MACD_Signal'].empty else None,
                    'bb_position': self._calculate_bb_position(hist)
                },
                'data_quality': len(hist),
                'last_update': hist.index[-1].isoformat() if not hist.empty else None
            }
            
        except Exception as e:
            logging.error(f"Error analyzing {timeframe} for {symbol}: {e}")
            return {'error': str(e), 'timeframe': timeframe}
    
    def _get_period_for_timeframe(self, timeframe: str) -> str:
        """Get appropriate data period for each timeframe"""
        period_map = {
            '1m': '1d',    # 1 day of 1-minute data
            '5m': '5d',    # 5 days of 5-minute data
            '15m': '1mo',  # 1 month of 15-minute data
            '1h': '3mo',   # 3 months of hourly data
            '1d': '1y'     # 1 year of daily data
        }
        return period_map.get(timeframe, '1mo')
    
    def _calculate_trend_strength(self, hist: pd.DataFrame) -> Dict:
        """Calculate trend strength using multiple indicators"""
        try:
            closes = hist['Close']
            
            # Simple moving averages
            sma_20 = closes.rolling(20).mean()
            sma_50 = closes.rolling(50).mean() if len(closes) >= 50 else closes.rolling(len(closes)//2).mean()
            
            current_price = closes.iloc[-1]
            
            # Trend direction
            if current_price > sma_20.iloc[-1] > sma_50.iloc[-1]:
                direction = 'bullish'
            elif current_price < sma_20.iloc[-1] < sma_50.iloc[-1]:
                direction = 'bearish'
            else:
                direction = 'neutral'
            
            # Trend strength (0-100)
            price_vs_sma20 = ((current_price - sma_20.iloc[-1]) / sma_20.iloc[-1]) * 100
            strength = min(abs(price_vs_sma20) * 10, 100)
            
            # Trend consistency
            trend_periods = 0
            for i in range(min(10, len(closes)-1)):
                if direction == 'bullish' and closes.iloc[-(i+1)] > closes.iloc[-(i+2)]:
                    trend_periods += 1
                elif direction == 'bearish' and closes.iloc[-(i+1)] < closes.iloc[-(i+2)]:
                    trend_periods += 1
            
            consistency = (trend_periods / min(10, len(closes)-1)) * 100
            
            return {
                'direction': direction,
                'strength': float(strength),
                'consistency': float(consistency),
                'price_vs_sma20': float(price_vs_sma20)
            }
            
        except Exception as e:
            logging.error(f"Error calculating trend strength: {e}")
            return {'direction': 'neutral', 'strength': 0, 'consistency': 0, 'price_vs_sma20': 0}
    
    def _calculate_momentum_score(self, hist: pd.DataFrame) -> Dict:
        """Calculate momentum using RSI, MACD, and price momentum"""
        try:
            rsi = hist['RSI'].iloc[-1] if 'RSI' in hist.columns and not hist['RSI'].empty else 50
            
            # Price momentum (5-period rate of change)
            price_momentum = ((hist['Close'].iloc[-1] - hist['Close'].iloc[-6]) / hist['Close'].iloc[-6]) * 100 if len(hist) >= 6 else 0
            
            # MACD momentum
            macd_momentum = 0
            if 'MACD' in hist.columns and 'MACD_Signal' in hist.columns:
                macd = hist['MACD'].iloc[-1]
                macd_signal = hist['MACD_Signal'].iloc[-1]
                if not pd.isna(macd) and not pd.isna(macd_signal):
                    macd_momentum = macd - macd_signal
            
            # Composite momentum score (0-100)
            rsi_score = rsi
            momentum_score = (rsi_score + (price_momentum * 2) + (macd_momentum * 10) + 50) / 2
            momentum_score = max(0, min(100, momentum_score))
            
            return {
                'composite_score': float(momentum_score),
                'rsi': float(rsi),
                'price_momentum': float(price_momentum),
                'macd_momentum': float(macd_momentum)
            }
            
        except Exception as e:
            logging.error(f"Error calculating momentum score: {e}")
            return {'composite_score': 50, 'rsi': 50, 'price_momentum': 0, 'macd_momentum': 0}
    
    def _analyze_volume_profile(self, hist: pd.DataFrame) -> Dict:
        """Analyze volume patterns and surge detection"""
        try:
            volumes = hist['Volume']
            current_volume = volumes.iloc[-1]
            avg_volume = volumes.rolling(20).mean().iloc[-1]
            
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
            
            # Volume trend
            recent_volumes = volumes.tail(5)
            volume_trend = 'increasing' if recent_volumes.is_monotonic_increasing else \
                          'decreasing' if recent_volumes.is_monotonic_decreasing else 'mixed'
            
            # Volume surge detection
            volume_surge = volume_ratio > 1.5
            
            return {
                'current_volume': int(current_volume),
                'average_volume': int(avg_volume),
                'volume_ratio': float(volume_ratio),
                'volume_trend': volume_trend,
                'volume_surge': volume_surge,
                'surge_intensity': min(volume_ratio * 20, 100)
            }
            
        except Exception as e:
            logging.error(f"Error analyzing volume profile: {e}")
            return {'current_volume': 0, 'average_volume': 0, 'volume_ratio': 1, 'volume_trend': 'mixed', 'volume_surge': False, 'surge_intensity': 0}
    
    def _find_support_resistance_levels(self, hist: pd.DataFrame) -> Dict:
        """Identify key support and resistance levels"""
        try:
            highs = hist['High']
            lows = hist['Low']
            closes = hist['Close']
            
            current_price = closes.iloc[-1]
            
            # Find recent highs and lows
            recent_highs = []
            recent_lows = []
            
            # Look for swing highs and lows
            for i in range(2, len(hist) - 2):
                # Swing high: higher than 2 periods before and after
                if (highs.iloc[i] > highs.iloc[i-1] and highs.iloc[i] > highs.iloc[i-2] and
                    highs.iloc[i] > highs.iloc[i+1] and highs.iloc[i] > highs.iloc[i+2]):
                    recent_highs.append(float(highs.iloc[i]))
                
                # Swing low: lower than 2 periods before and after
                if (lows.iloc[i] < lows.iloc[i-1] and lows.iloc[i] < lows.iloc[i-2] and
                    lows.iloc[i] < lows.iloc[i+1] and lows.iloc[i] < lows.iloc[i+2]):
                    recent_lows.append(float(lows.iloc[i]))
            
            # Find nearest support and resistance
            resistance_levels = [h for h in recent_highs if h > current_price]
            support_levels = [l for l in recent_lows if l < current_price]
            
            nearest_resistance = min(resistance_levels) if resistance_levels else None
            nearest_support = max(support_levels) if support_levels else None
            
            return {
                'nearest_support': nearest_support,
                'nearest_resistance': nearest_resistance,
                'support_levels': sorted(support_levels, reverse=True)[:3],
                'resistance_levels': sorted(resistance_levels)[:3],
                'support_strength': len(support_levels),
                'resistance_strength': len(resistance_levels)
            }
            
        except Exception as e:
            logging.error(f"Error finding support/resistance levels: {e}")
            return {'nearest_support': None, 'nearest_resistance': None, 'support_levels': [], 'resistance_levels': [], 'support_strength': 0, 'resistance_strength': 0}
    
    def _calculate_bb_position(self, hist: pd.DataFrame) -> float:
        """Calculate position within Bollinger Bands (0-100)"""
        try:
            if 'BB_Upper' in hist.columns and 'BB_Lower' in hist.columns:
                current_price = hist['Close'].iloc[-1]
                bb_upper = hist['BB_Upper'].iloc[-1]
                bb_lower = hist['BB_Lower'].iloc[-1]
                
                if not pd.isna(bb_upper) and not pd.isna(bb_lower) and bb_upper != bb_lower:
                    position = ((current_price - bb_lower) / (bb_upper - bb_lower)) * 100
                    return max(0, min(100, position))
            return 50
        except:
            return 50
    
    def _calculate_alignment_score(self, timeframe_data: Dict) -> float:
        """Calculate how well trends align across timeframes"""
        try:
            trend_directions = []
            momentum_scores = []
            weights = []
            
            for tf, data in timeframe_data.items():
                if 'error' not in data and 'trend_strength' in data:
                    direction = data['trend_strength']['direction']
                    momentum = data['momentum_score']['composite_score']
                    
                    # Convert direction to numeric (-1, 0, 1)
                    direction_score = 1 if direction == 'bullish' else -1 if direction == 'bearish' else 0
                    trend_directions.append(direction_score)
                    momentum_scores.append(momentum)
                    weights.append(self.timeframe_weights[tf])
            
            if not trend_directions:
                return 0
            
            # Calculate weighted alignment
            weighted_direction = sum(d * w for d, w in zip(trend_directions, weights))
            weighted_momentum = sum(m * w for m, w in zip(momentum_scores, weights))
            
            # Alignment score (0-100)
            direction_consistency = abs(weighted_direction) * 50  # 0-50 points for direction consistency
            momentum_strength = (weighted_momentum - 50) / 50 * 50  # 0-50 points for momentum strength
            
            alignment_score = max(0, min(100, direction_consistency + momentum_strength))
            return float(alignment_score)
            
        except Exception as e:
            logging.error(f"Error calculating alignment score: {e}")
            return 0
    
    def _determine_dominant_trend(self, timeframe_data: Dict) -> str:
        """Determine the dominant trend across timeframes"""
        try:
            bullish_weight = 0
            bearish_weight = 0
            
            for tf, data in timeframe_data.items():
                if 'error' not in data and 'trend_strength' in data:
                    direction = data['trend_strength']['direction']
                    weight = self.timeframe_weights[tf]
                    
                    if direction == 'bullish':
                        bullish_weight += weight
                    elif direction == 'bearish':
                        bearish_weight += weight
            
            if bullish_weight > bearish_weight + 0.1:
                return 'bullish'
            elif bearish_weight > bullish_weight + 0.1:
                return 'bearish'
            else:
                return 'neutral'
                
        except Exception as e:
            logging.error(f"Error determining dominant trend: {e}")
            return 'neutral'
    
    def _identify_confluence_zones(self, timeframe_data: Dict) -> List[Dict]:
        """Identify price zones where multiple timeframes show support/resistance"""
        try:
            all_levels = []
            
            for tf, data in timeframe_data.items():
                if 'error' not in data and 'support_resistance' in data:
                    sr_data = data['support_resistance']
                    weight = self.timeframe_weights[tf]
                    
                    # Add support levels
                    for level in sr_data.get('support_levels', []):
                        all_levels.append({
                            'price': level,
                            'type': 'support',
                            'timeframe': tf,
                            'weight': weight
                        })
                    
                    # Add resistance levels
                    for level in sr_data.get('resistance_levels', []):
                        all_levels.append({
                            'price': level,
                            'type': 'resistance',
                            'timeframe': tf,
                            'weight': weight
                        })
            
            # Group nearby levels (within 2% of each other)
            confluence_zones = []
            tolerance = 0.02  # 2% tolerance
            
            for level in all_levels:
                # Find nearby levels
                nearby_levels = [l for l in all_levels 
                               if abs(l['price'] - level['price']) / level['price'] <= tolerance]
                
                if len(nearby_levels) >= 2:  # At least 2 timeframes agree
                    total_weight = sum(l['weight'] for l in nearby_levels)
                    avg_price = sum(l['price'] * l['weight'] for l in nearby_levels) / total_weight
                    
                    confluence_zone = {
                        'price': float(avg_price),
                        'strength': float(total_weight),
                        'timeframes': [l['timeframe'] for l in nearby_levels],
                        'types': list(set(l['type'] for l in nearby_levels))
                    }
                    
                    # Avoid duplicates
                    if not any(abs(cz['price'] - confluence_zone['price']) / confluence_zone['price'] <= tolerance 
                             for cz in confluence_zones):
                        confluence_zones.append(confluence_zone)
            
            # Sort by strength
            confluence_zones.sort(key=lambda x: x['strength'], reverse=True)
            return confluence_zones[:5]  # Return top 5 confluence zones
            
        except Exception as e:
            logging.error(f"Error identifying confluence zones: {e}")
            return []
    
    def _generate_trade_recommendation(self, analysis_results: Dict) -> Dict:
        """Generate trade recommendation based on multi-timeframe analysis"""
        try:
            alignment_score = analysis_results['alignment_score']
            dominant_trend = analysis_results['dominant_trend']
            confluence_zones = analysis_results['confluence_zones']
            
            # Base recommendation on alignment and trend
            if alignment_score >= 70 and dominant_trend == 'bullish':
                action = 'strong_buy'
                confidence = 'high'
            elif alignment_score >= 50 and dominant_trend == 'bullish':
                action = 'buy'
                confidence = 'medium'
            elif alignment_score >= 70 and dominant_trend == 'bearish':
                action = 'strong_sell'
                confidence = 'high'
            elif alignment_score >= 50 and dominant_trend == 'bearish':
                action = 'sell'
                confidence = 'medium'
            else:
                action = 'hold'
                confidence = 'low'
            
            # Entry and exit levels from confluence zones
            entry_level = None
            stop_loss = None
            take_profit = None
            
            if confluence_zones:
                current_price = None
                for tf_data in analysis_results['timeframe_data'].values():
                    if 'current_price' in tf_data:
                        current_price = tf_data['current_price']
                        break
                
                if current_price:
                    if action in ['buy', 'strong_buy']:
                        # Find support for entry, resistance for target
                        supports = [cz for cz in confluence_zones if 'support' in cz['types'] and cz['price'] < current_price]
                        resistances = [cz for cz in confluence_zones if 'resistance' in cz['types'] and cz['price'] > current_price]
                        
                        if supports:
                            entry_level = supports[0]['price']
                            stop_loss = entry_level * 0.95  # 5% below entry
                        if resistances:
                            take_profit = resistances[0]['price']
                    
                    elif action in ['sell', 'strong_sell']:
                        # Find resistance for entry, support for target
                        resistances = [cz for cz in confluence_zones if 'resistance' in cz['types'] and cz['price'] > current_price]
                        supports = [cz for cz in confluence_zones if 'support' in cz['types'] and cz['price'] < current_price]
                        
                        if resistances:
                            entry_level = resistances[0]['price']
                            stop_loss = entry_level * 1.05  # 5% above entry
                        if supports:
                            take_profit = supports[0]['price']
            
            return {
                'action': action,
                'confidence': confidence,
                'alignment_score': alignment_score,
                'entry_level': entry_level,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'reasoning': self._generate_reasoning(analysis_results),
                'timeframe_priority': self._get_timeframe_priority(analysis_results)
            }
            
        except Exception as e:
            logging.error(f"Error generating trade recommendation: {e}")
            return {'action': 'hold', 'confidence': 'low', 'reasoning': 'Analysis incomplete'}
    
    def _assess_multi_timeframe_risk(self, analysis_results: Dict) -> Dict:
        """Assess risk based on multi-timeframe alignment"""
        try:
            alignment_score = analysis_results['alignment_score']
            confluence_zones = analysis_results['confluence_zones']
            
            # Risk level based on alignment
            if alignment_score >= 80:
                risk_level = 'low'
            elif alignment_score >= 60:
                risk_level = 'medium'
            elif alignment_score >= 40:
                risk_level = 'high'
            else:
                risk_level = 'very_high'
            
            # Risk factors
            risk_factors = []
            if alignment_score < 50:
                risk_factors.append('Low timeframe alignment')
            if len(confluence_zones) < 2:
                risk_factors.append('Limited support/resistance levels')
            
            # Volatility assessment from daily timeframe
            volatility_risk = 'medium'
            daily_data = analysis_results['timeframe_data'].get('1d', {})
            if 'technical_indicators' in daily_data:
                bb_position = daily_data['technical_indicators'].get('bb_position', 50)
                if bb_position > 80 or bb_position < 20:
                    volatility_risk = 'high'
                    risk_factors.append('Price near Bollinger Band extremes')
            
            return {
                'risk_level': risk_level,
                'volatility_risk': volatility_risk,
                'risk_factors': risk_factors,
                'position_sizing_multiplier': self._get_position_sizing_multiplier(risk_level)
            }
            
        except Exception as e:
            logging.error(f"Error assessing multi-timeframe risk: {e}")
            return {'risk_level': 'high', 'volatility_risk': 'high', 'risk_factors': ['Analysis error']}
    
    def _generate_reasoning(self, analysis_results: Dict) -> str:
        """Generate human-readable reasoning for the recommendation"""
        try:
            alignment_score = analysis_results['alignment_score']
            dominant_trend = analysis_results['dominant_trend']
            confluence_zones = len(analysis_results['confluence_zones'])
            
            reasoning = f"Multi-timeframe analysis shows {alignment_score:.0f}% alignment "
            reasoning += f"with {dominant_trend} trend dominance. "
            reasoning += f"Identified {confluence_zones} confluence zones for support/resistance. "
            
            # Add timeframe-specific insights
            strong_timeframes = []
            weak_timeframes = []
            
            for tf, data in analysis_results['timeframe_data'].items():
                if 'error' not in data and 'momentum_score' in data:
                    momentum = data['momentum_score']['composite_score']
                    if momentum > 70:
                        strong_timeframes.append(tf)
                    elif momentum < 30:
                        weak_timeframes.append(tf)
            
            if strong_timeframes:
                reasoning += f"Strong momentum on {', '.join(strong_timeframes)} timeframes. "
            if weak_timeframes:
                reasoning += f"Weak momentum on {', '.join(weak_timeframes)} timeframes. "
            
            return reasoning.strip()
            
        except Exception as e:
            return "Multi-timeframe analysis completed with mixed signals."
    
    def _get_timeframe_priority(self, analysis_results: Dict) -> str:
        """Determine which timeframe should be prioritized for entry"""
        try:
            best_score = 0
            best_timeframe = '1d'
            
            for tf, data in analysis_results['timeframe_data'].items():
                if 'error' not in data:
                    momentum = data.get('momentum_score', {}).get('composite_score', 50)
                    trend_strength = data.get('trend_strength', {}).get('strength', 0)
                    
                    # Calculate composite score
                    composite = (momentum + trend_strength) / 2
                    weighted_score = composite * self.timeframe_weights[tf]
                    
                    if weighted_score > best_score:
                        best_score = weighted_score
                        best_timeframe = tf
            
            return best_timeframe
            
        except Exception as e:
            return '1d'
    
    def _get_position_sizing_multiplier(self, risk_level: str) -> float:
        """Get position sizing multiplier based on risk level"""
        multipliers = {
            'low': 1.0,
            'medium': 0.75,
            'high': 0.5,
            'very_high': 0.25
        }
        return multipliers.get(risk_level, 0.5)