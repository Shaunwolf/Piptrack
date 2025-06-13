"""
Enhanced Historical Comparison Engine for CandleCast
Advanced pattern matching with multi-factor scoring system
"""

import yfinance as yf
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging
from dataclasses import dataclass
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler
import ta
import requests
import json
import os

@dataclass
class HistoricalMatch:
    """Data class for historical comparison matches"""
    symbol: str
    date_range: str
    similarity_score: float
    price_correlation: float
    volume_correlation: float
    pattern_match_score: float
    technical_score: float
    news_sentiment_score: float
    market_condition_score: float
    composite_score: float
    key_metrics: Dict
    outcome: Dict
    confidence_level: str

class HistoricalComparisonEngine:
    def __init__(self):
        """Initialize the enhanced historical comparison engine"""
        self.cache = {}
        self.cache_duration = 3600  # 1 hour
        self.scaler = StandardScaler()
        
    def find_historical_matches(self, target_symbol: str, lookback_days: int = 252) -> List[HistoricalMatch]:
        """
        Find historical matches using comprehensive multi-factor analysis
        """
        try:
            # Get current pattern data for target symbol
            current_pattern = self._extract_current_pattern(target_symbol)
            if not current_pattern:
                return []
            
            # Search through historical data for similar patterns
            matches = []
            
            # Define comparison symbols (expand this list as needed)
            comparison_symbols = [
                'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'AMD', 
                'NFLX', 'CRM', 'ADBE', 'ORCL', 'INTC', 'IBM', 'HPQ', 'DELL',
                'SPY', 'QQQ', 'IWM', 'DIA', 'VTI', 'ARKK', 'XLK', 'XLF'
            ]
            
            # Add target symbol to compare against its own history
            if target_symbol not in comparison_symbols:
                comparison_symbols.append(target_symbol)
            
            for comp_symbol in comparison_symbols:
                historical_matches = self._find_matches_for_symbol(
                    current_pattern, comp_symbol, lookback_days
                )
                matches.extend(historical_matches)
            
            # Sort by composite score and return top matches
            matches.sort(key=lambda x: x.composite_score, reverse=True)
            return matches[:10]  # Return top 10 matches
            
        except Exception as e:
            logging.error(f"Error finding historical matches: {e}")
            return []
    
    def _extract_current_pattern(self, symbol: str) -> Optional[Dict]:
        """Extract current pattern characteristics for comparison"""
        try:
            ticker = yf.Ticker(symbol)
            
            # Get recent data (30 days for pattern analysis)
            hist = ticker.history(period="1mo", interval="1d")
            if hist.empty or len(hist) < 10:
                return None
            
            # Calculate technical indicators
            technical_features = self._calculate_technical_features(hist)
            
            # Extract price pattern features
            price_features = self._extract_price_pattern_features(hist)
            
            # Get volume characteristics
            volume_features = self._extract_volume_features(hist)
            
            # Get market context
            market_context = self._get_market_context()
            
            return {
                'symbol': symbol,
                'data_period': hist.index[-1],
                'technical_features': technical_features,
                'price_features': price_features,
                'volume_features': volume_features,
                'market_context': market_context,
                'raw_data': hist
            }
            
        except Exception as e:
            logging.error(f"Error extracting pattern for {symbol}: {e}")
            return None
    
    def _find_matches_for_symbol(self, current_pattern: Dict, comp_symbol: str, lookback_days: int) -> List[HistoricalMatch]:
        """Find historical matches within a specific symbol's history"""
        matches = []
        
        try:
            ticker = yf.Ticker(comp_symbol)
            
            # Get extended historical data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=lookback_days * 2)  # Get more data for sliding window
            
            hist = ticker.history(start=start_date, end=end_date, interval="1d")
            if hist.empty or len(hist) < 60:
                return matches
            
            # Use sliding window to find similar patterns
            window_size = len(current_pattern['raw_data'])
            
            for i in range(len(hist) - window_size - 10):  # Leave 10 days for outcome analysis
                window_data = hist.iloc[i:i + window_size]
                
                if len(window_data) < window_size:
                    continue
                
                # Calculate similarity scores
                similarity_scores = self._calculate_similarity_scores(
                    current_pattern, window_data, comp_symbol
                )
                
                # Only consider matches above threshold
                if similarity_scores['composite_score'] > 0.7:
                    # Analyze outcome (what happened next)
                    outcome_data = self._analyze_outcome(hist, i + window_size)
                    
                    match = HistoricalMatch(
                        symbol=comp_symbol,
                        date_range=f"{window_data.index[0].strftime('%Y-%m-%d')} to {window_data.index[-1].strftime('%Y-%m-%d')}",
                        similarity_score=similarity_scores['similarity_score'],
                        price_correlation=similarity_scores['price_correlation'],
                        volume_correlation=similarity_scores['volume_correlation'],
                        pattern_match_score=similarity_scores['pattern_match_score'],
                        technical_score=similarity_scores['technical_score'],
                        news_sentiment_score=similarity_scores['news_sentiment_score'],
                        market_condition_score=similarity_scores['market_condition_score'],
                        composite_score=similarity_scores['composite_score'],
                        key_metrics=similarity_scores['key_metrics'],
                        outcome=outcome_data,
                        confidence_level=self._determine_confidence_level(similarity_scores['composite_score'])
                    )
                    
                    matches.append(match)
            
        except Exception as e:
            logging.error(f"Error finding matches for {comp_symbol}: {e}")
        
        return matches
    
    def _calculate_similarity_scores(self, current_pattern: Dict, historical_window: pd.DataFrame, comp_symbol: str) -> Dict:
        """Calculate comprehensive similarity scores between current and historical patterns"""
        
        # 1. Price Pattern Similarity (25% weight)
        price_correlation = self._calculate_price_pattern_similarity(
            current_pattern['raw_data'], historical_window
        )
        
        # 2. Volume Pattern Similarity (15% weight)
        volume_correlation = self._calculate_volume_pattern_similarity(
            current_pattern['raw_data'], historical_window
        )
        
        # 3. Technical Indicator Similarity (25% weight)
        technical_score = self._calculate_technical_similarity(
            current_pattern, historical_window
        )
        
        # 4. Pattern Recognition Score (20% weight)
        pattern_match_score = self._calculate_pattern_recognition_score(
            current_pattern['raw_data'], historical_window
        )
        
        # 5. News Sentiment Similarity (10% weight)
        news_sentiment_score = self._calculate_news_sentiment_similarity(
            current_pattern['symbol'], comp_symbol, historical_window.index[-1]
        )
        
        # 6. Market Condition Similarity (5% weight)
        market_condition_score = self._calculate_market_condition_similarity(
            current_pattern['market_context'], historical_window.index[-1]
        )
        
        # Calculate composite score with weights
        weights = {
            'price': 0.25,
            'volume': 0.15,
            'technical': 0.25,
            'pattern': 0.20,
            'news': 0.10,
            'market': 0.05
        }
        
        composite_score = (
            price_correlation * weights['price'] +
            volume_correlation * weights['volume'] +
            technical_score * weights['technical'] +
            pattern_match_score * weights['pattern'] +
            news_sentiment_score * weights['news'] +
            market_condition_score * weights['market']
        )
        
        # Calculate overall similarity using cosine similarity
        current_features = self._extract_feature_vector(current_pattern['raw_data'])
        historical_features = self._extract_feature_vector(historical_window)
        
        if len(current_features) == len(historical_features):
            similarity_score = cosine_similarity([current_features], [historical_features])[0][0]
        else:
            similarity_score = 0.5  # Default if feature vectors don't match
        
        return {
            'similarity_score': max(0, min(1, similarity_score)),
            'price_correlation': price_correlation,
            'volume_correlation': volume_correlation,
            'pattern_match_score': pattern_match_score,
            'technical_score': technical_score,
            'news_sentiment_score': news_sentiment_score,
            'market_condition_score': market_condition_score,
            'composite_score': max(0, min(1, composite_score)),
            'key_metrics': {
                'rsi_diff': abs(self._get_rsi(current_pattern['raw_data']) - self._get_rsi(historical_window)),
                'volatility_ratio': self._calculate_volatility_ratio(current_pattern['raw_data'], historical_window),
                'trend_similarity': self._calculate_trend_similarity(current_pattern['raw_data'], historical_window)
            }
        }
    
    def _calculate_price_pattern_similarity(self, current_data: pd.DataFrame, historical_data: pd.DataFrame) -> float:
        """Calculate price pattern similarity using normalized price movements"""
        try:
            # Normalize prices to percentage changes
            current_returns = current_data['Close'].pct_change().dropna()
            historical_returns = historical_data['Close'].pct_change().dropna()
            
            min_length = min(len(current_returns), len(historical_returns))
            if min_length < 5:
                return 0.0
            
            # Trim to same length
            current_returns = current_returns[-min_length:]
            historical_returns = historical_returns[-min_length:]
            
            # Calculate correlation
            correlation = np.corrcoef(current_returns, historical_returns)[0, 1]
            return max(0, correlation) if not np.isnan(correlation) else 0.0
            
        except Exception as e:
            logging.error(f"Error calculating price pattern similarity: {e}")
            return 0.0
    
    def _calculate_volume_pattern_similarity(self, current_data: pd.DataFrame, historical_data: pd.DataFrame) -> float:
        """Calculate volume pattern similarity"""
        try:
            # Normalize volumes
            current_vol = current_data['Volume'] / current_data['Volume'].mean()
            historical_vol = historical_data['Volume'] / historical_data['Volume'].mean()
            
            min_length = min(len(current_vol), len(historical_vol))
            if min_length < 5:
                return 0.0
            
            current_vol = current_vol[-min_length:]
            historical_vol = historical_vol[-min_length:]
            
            # Calculate correlation
            correlation = np.corrcoef(current_vol, historical_vol)[0, 1]
            return max(0, correlation) if not np.isnan(correlation) else 0.0
            
        except Exception as e:
            logging.error(f"Error calculating volume pattern similarity: {e}")
            return 0.0
    
    def _calculate_technical_similarity(self, current_pattern: Dict, historical_data: pd.DataFrame) -> float:
        """Calculate technical indicator similarity"""
        try:
            score = 0.0
            comparisons = 0
            
            # RSI comparison
            current_rsi = self._get_rsi(current_pattern['raw_data'])
            historical_rsi = self._get_rsi(historical_data)
            if current_rsi and historical_rsi:
                rsi_diff = abs(current_rsi - historical_rsi) / 100
                score += (1 - rsi_diff)
                comparisons += 1
            
            # MACD comparison
            current_macd = self._get_macd_signal(current_pattern['raw_data'])
            historical_macd = self._get_macd_signal(historical_data)
            if current_macd == historical_macd:
                score += 1.0
                comparisons += 1
            elif comparisons > 0:
                comparisons += 1
            
            # Bollinger Bands position comparison
            current_bb_pos = self._get_bollinger_position(current_pattern['raw_data'])
            historical_bb_pos = self._get_bollinger_position(historical_data)
            if current_bb_pos and historical_bb_pos:
                bb_diff = abs(current_bb_pos - historical_bb_pos)
                score += (1 - bb_diff)
                comparisons += 1
            
            return score / comparisons if comparisons > 0 else 0.0
            
        except Exception as e:
            logging.error(f"Error calculating technical similarity: {e}")
            return 0.0
    
    def _calculate_pattern_recognition_score(self, current_data: pd.DataFrame, historical_data: pd.DataFrame) -> float:
        """Calculate pattern recognition similarity score"""
        try:
            score = 0.0
            patterns_checked = 0
            
            # Check for similar candlestick patterns
            current_patterns = self._identify_candlestick_patterns(current_data)
            historical_patterns = self._identify_candlestick_patterns(historical_data)
            
            # Compare pattern occurrences
            for pattern in current_patterns:
                if pattern in historical_patterns:
                    score += 1.0
                patterns_checked += 1
            
            # Check for trend patterns
            current_trend = self._identify_trend_pattern(current_data)
            historical_trend = self._identify_trend_pattern(historical_data)
            
            if current_trend == historical_trend:
                score += 1.0
            patterns_checked += 1
            
            # Check for support/resistance levels
            current_levels = self._find_support_resistance_levels(current_data)
            historical_levels = self._find_support_resistance_levels(historical_data)
            
            level_similarity = self._compare_support_resistance_levels(current_levels, historical_levels)
            score += level_similarity
            patterns_checked += 1
            
            return score / patterns_checked if patterns_checked > 0 else 0.0
            
        except Exception as e:
            logging.error(f"Error calculating pattern recognition score: {e}")
            return 0.0
    
    def _calculate_news_sentiment_similarity(self, current_symbol: str, historical_symbol: str, historical_date: pd.Timestamp) -> float:
        """Calculate news sentiment similarity (placeholder for news API integration)"""
        try:
            # For now, return neutral score
            # In production, this would integrate with news APIs to analyze sentiment
            
            # If same symbol, higher correlation likely
            if current_symbol == historical_symbol:
                return 0.8
            
            # If different symbols, check sector correlation
            sector_correlation = self._get_sector_correlation(current_symbol, historical_symbol)
            return sector_correlation * 0.6
            
        except Exception as e:
            logging.error(f"Error calculating news sentiment similarity: {e}")
            return 0.5
    
    def _calculate_market_condition_similarity(self, current_market_context: Dict, historical_date: pd.Timestamp) -> float:
        """Calculate market condition similarity"""
        try:
            # Get historical market context
            historical_market_context = self._get_historical_market_context(historical_date)
            
            # Compare VIX levels
            vix_similarity = 1 - abs(current_market_context.get('vix', 20) - historical_market_context.get('vix', 20)) / 50
            
            # Compare market trend
            trend_similarity = 1.0 if current_market_context.get('trend') == historical_market_context.get('trend') else 0.0
            
            return (vix_similarity + trend_similarity) / 2
            
        except Exception as e:
            logging.error(f"Error calculating market condition similarity: {e}")
            return 0.5
    
    def _calculate_technical_features(self, data: pd.DataFrame) -> Dict:
        """Calculate comprehensive technical indicators"""
        try:
            features = {}
            
            # RSI
            features['rsi'] = ta.momentum.RSIIndicator(data['Close']).rsi().iloc[-1]
            
            # MACD
            macd = ta.trend.MACD(data['Close'])
            features['macd'] = macd.macd().iloc[-1]
            features['macd_signal'] = macd.macd_signal().iloc[-1]
            features['macd_histogram'] = macd.macd_diff().iloc[-1]
            
            # Bollinger Bands
            bb = ta.volatility.BollingerBands(data['Close'])
            features['bb_upper'] = bb.bollinger_hband().iloc[-1]
            features['bb_lower'] = bb.bollinger_lband().iloc[-1]
            features['bb_middle'] = bb.bollinger_mavg().iloc[-1]
            
            # Moving averages
            features['sma_20'] = ta.trend.SMAIndicator(data['Close'], window=20).sma_indicator().iloc[-1]
            features['ema_12'] = ta.trend.EMAIndicator(data['Close'], window=12).ema_indicator().iloc[-1]
            
            # Volume indicators
            features['volume_sma'] = ta.volume.VolumeSMAIndicator(data['Close'], data['Volume']).volume_sma().iloc[-1]
            
            # Volatility
            features['atr'] = ta.volatility.AverageTrueRange(data['High'], data['Low'], data['Close']).average_true_range().iloc[-1]
            
            return features
            
        except Exception as e:
            logging.error(f"Error calculating technical features: {e}")
            return {}
    
    def _extract_price_pattern_features(self, data: pd.DataFrame) -> Dict:
        """Extract price pattern characteristics"""
        try:
            features = {}
            
            # Price trend
            features['trend_slope'] = (data['Close'].iloc[-1] - data['Close'].iloc[0]) / len(data)
            
            # Volatility
            features['volatility'] = data['Close'].pct_change().std()
            
            # Price range
            features['price_range'] = (data['High'].max() - data['Low'].min()) / data['Close'].mean()
            
            # Recent performance
            features['recent_return_5d'] = (data['Close'].iloc[-1] - data['Close'].iloc[-6]) / data['Close'].iloc[-6] if len(data) > 5 else 0
            features['recent_return_10d'] = (data['Close'].iloc[-1] - data['Close'].iloc[-11]) / data['Close'].iloc[-11] if len(data) > 10 else 0
            
            return features
            
        except Exception as e:
            logging.error(f"Error extracting price pattern features: {e}")
            return {}
    
    def _extract_volume_features(self, data: pd.DataFrame) -> Dict:
        """Extract volume characteristics"""
        try:
            features = {}
            
            # Volume trend
            features['volume_trend'] = (data['Volume'].iloc[-5:].mean() - data['Volume'].iloc[-10:-5].mean()) / data['Volume'].iloc[-10:-5].mean()
            
            # Volume volatility
            features['volume_volatility'] = data['Volume'].std() / data['Volume'].mean()
            
            # Volume spikes
            volume_threshold = data['Volume'].mean() + 2 * data['Volume'].std()
            features['volume_spikes'] = len(data[data['Volume'] > volume_threshold])
            
            return features
            
        except Exception as e:
            logging.error(f"Error extracting volume features: {e}")
            return {}
    
    def _get_market_context(self) -> Dict:
        """Get current market context"""
        try:
            # Get VIX data
            vix = yf.Ticker("^VIX")
            vix_data = vix.history(period="1d")
            current_vix = vix_data['Close'].iloc[-1] if not vix_data.empty else 20
            
            # Get market trend from SPY
            spy = yf.Ticker("SPY")
            spy_data = spy.history(period="1mo")
            market_trend = "bullish" if spy_data['Close'].iloc[-1] > spy_data['Close'].iloc[0] else "bearish"
            
            return {
                'vix': current_vix,
                'trend': market_trend,
                'date': datetime.now()
            }
            
        except Exception as e:
            logging.error(f"Error getting market context: {e}")
            return {'vix': 20, 'trend': 'neutral', 'date': datetime.now()}
    
    def _get_historical_market_context(self, date: pd.Timestamp) -> Dict:
        """Get historical market context for a specific date"""
        try:
            # Get historical VIX data
            end_date = date + timedelta(days=1)
            start_date = date - timedelta(days=5)
            
            vix = yf.Ticker("^VIX")
            vix_data = vix.history(start=start_date, end=end_date)
            historical_vix = vix_data['Close'].iloc[-1] if not vix_data.empty else 20
            
            # Get historical market trend
            spy = yf.Ticker("SPY")
            spy_data = spy.history(start=start_date - timedelta(days=30), end=end_date)
            if not spy_data.empty and len(spy_data) > 1:
                market_trend = "bullish" if spy_data['Close'].iloc[-1] > spy_data['Close'].iloc[0] else "bearish"
            else:
                market_trend = "neutral"
            
            return {
                'vix': historical_vix,
                'trend': market_trend,
                'date': date
            }
            
        except Exception as e:
            logging.error(f"Error getting historical market context: {e}")
            return {'vix': 20, 'trend': 'neutral', 'date': date}
    
    def _analyze_outcome(self, full_data: pd.DataFrame, start_index: int) -> Dict:
        """Analyze what happened after the historical pattern"""
        try:
            # Look at next 10 trading days
            end_index = min(start_index + 10, len(full_data))
            outcome_data = full_data.iloc[start_index:end_index]
            
            if len(outcome_data) < 2:
                return {'outcome': 'insufficient_data'}
            
            start_price = outcome_data['Close'].iloc[0]
            end_price = outcome_data['Close'].iloc[-1]
            max_price = outcome_data['High'].max()
            min_price = outcome_data['Low'].min()
            
            total_return = (end_price - start_price) / start_price * 100
            max_gain = (max_price - start_price) / start_price * 100
            max_loss = (min_price - start_price) / start_price * 100
            
            # Determine outcome category
            if total_return > 5:
                outcome_category = "strong_bullish"
            elif total_return > 2:
                outcome_category = "bullish"
            elif total_return > -2:
                outcome_category = "sideways"
            elif total_return > -5:
                outcome_category = "bearish"
            else:
                outcome_category = "strong_bearish"
            
            return {
                'outcome': outcome_category,
                'total_return': total_return,
                'max_gain': max_gain,
                'max_loss': max_loss,
                'days_analyzed': len(outcome_data),
                'volatility': outcome_data['Close'].pct_change().std() * 100
            }
            
        except Exception as e:
            logging.error(f"Error analyzing outcome: {e}")
            return {'outcome': 'error', 'total_return': 0}
    
    def _determine_confidence_level(self, composite_score: float) -> str:
        """Determine confidence level based on composite score"""
        if composite_score >= 0.9:
            return "very_high"
        elif composite_score >= 0.8:
            return "high"
        elif composite_score >= 0.7:
            return "medium"
        elif composite_score >= 0.6:
            return "low"
        else:
            return "very_low"
    
    # Helper methods for technical analysis
    def _get_rsi(self, data: pd.DataFrame) -> Optional[float]:
        """Get current RSI value"""
        try:
            rsi = ta.momentum.RSIIndicator(data['Close']).rsi()
            return rsi.iloc[-1] if not rsi.empty else None
        except:
            return None
    
    def _get_macd_signal(self, data: pd.DataFrame) -> str:
        """Get MACD signal (bullish/bearish/neutral)"""
        try:
            macd = ta.trend.MACD(data['Close'])
            macd_line = macd.macd().iloc[-1]
            signal_line = macd.macd_signal().iloc[-1]
            
            if macd_line > signal_line:
                return "bullish"
            elif macd_line < signal_line:
                return "bearish"
            else:
                return "neutral"
        except:
            return "neutral"
    
    def _get_bollinger_position(self, data: pd.DataFrame) -> Optional[float]:
        """Get position within Bollinger Bands (0-1)"""
        try:
            bb = ta.volatility.BollingerBands(data['Close'])
            upper = bb.bollinger_hband().iloc[-1]
            lower = bb.bollinger_lband().iloc[-1]
            current = data['Close'].iloc[-1]
            
            if upper == lower:
                return 0.5
            
            position = (current - lower) / (upper - lower)
            return max(0, min(1, position))
        except:
            return None
    
    def _extract_feature_vector(self, data: pd.DataFrame) -> List[float]:
        """Extract normalized feature vector for similarity comparison"""
        try:
            features = []
            
            # Price features
            returns = data['Close'].pct_change().dropna()
            features.extend([
                returns.mean(),
                returns.std(),
                returns.skew() if len(returns) > 2 else 0,
                returns.kurt() if len(returns) > 3 else 0
            ])
            
            # Volume features
            vol_norm = data['Volume'] / data['Volume'].mean()
            features.extend([
                vol_norm.mean(),
                vol_norm.std()
            ])
            
            # Technical features
            if len(data) >= 14:
                rsi = self._get_rsi(data)
                features.append(rsi / 100 if rsi else 0.5)
            else:
                features.append(0.5)
            
            return features
            
        except Exception as e:
            logging.error(f"Error extracting feature vector: {e}")
            return [0.0] * 7  # Return default vector
    
    def _identify_candlestick_patterns(self, data: pd.DataFrame) -> List[str]:
        """Identify candlestick patterns in the data"""
        patterns = []
        
        try:
            if len(data) < 3:
                return patterns
            
            # Simple pattern detection
            last_candle = data.iloc[-1]
            prev_candle = data.iloc[-2]
            
            # Doji
            body_size = abs(last_candle['Close'] - last_candle['Open'])
            wick_size = last_candle['High'] - last_candle['Low']
            if body_size < (wick_size * 0.1):
                patterns.append('doji')
            
            # Hammer/Hanging Man
            upper_wick = last_candle['High'] - max(last_candle['Open'], last_candle['Close'])
            lower_wick = min(last_candle['Open'], last_candle['Close']) - last_candle['Low']
            if lower_wick > (body_size * 2) and upper_wick < (body_size * 0.5):
                patterns.append('hammer')
            
            # Engulfing patterns
            if (prev_candle['Close'] < prev_candle['Open'] and  # Previous red
                last_candle['Close'] > last_candle['Open'] and  # Current green
                last_candle['Close'] > prev_candle['Open'] and  # Engulfs previous
                last_candle['Open'] < prev_candle['Close']):
                patterns.append('bullish_engulfing')
            
        except Exception as e:
            logging.error(f"Error identifying candlestick patterns: {e}")
        
        return patterns
    
    def _identify_trend_pattern(self, data: pd.DataFrame) -> str:
        """Identify overall trend pattern"""
        try:
            if len(data) < 10:
                return "insufficient_data"
            
            # Calculate trend using linear regression slope
            prices = data['Close'].values
            x = np.arange(len(prices))
            slope = np.polyfit(x, prices, 1)[0]
            
            # Normalize slope by average price
            normalized_slope = slope / np.mean(prices)
            
            if normalized_slope > 0.001:
                return "uptrend"
            elif normalized_slope < -0.001:
                return "downtrend"
            else:
                return "sideways"
                
        except Exception as e:
            logging.error(f"Error identifying trend pattern: {e}")
            return "unknown"
    
    def _find_support_resistance_levels(self, data: pd.DataFrame) -> Dict:
        """Find support and resistance levels"""
        try:
            levels = {'support': [], 'resistance': []}
            
            # Use rolling min/max to find potential levels
            window = min(5, len(data) // 3)
            if window < 2:
                return levels
            
            rolling_min = data['Low'].rolling(window=window).min()
            rolling_max = data['High'].rolling(window=window).max()
            
            # Find support levels (local minimums)
            for i in range(window, len(data) - window):
                if (data['Low'].iloc[i] == rolling_min.iloc[i] and
                    data['Low'].iloc[i] < data['Low'].iloc[i-1] and
                    data['Low'].iloc[i] < data['Low'].iloc[i+1]):
                    levels['support'].append(data['Low'].iloc[i])
            
            # Find resistance levels (local maximums)
            for i in range(window, len(data) - window):
                if (data['High'].iloc[i] == rolling_max.iloc[i] and
                    data['High'].iloc[i] > data['High'].iloc[i-1] and
                    data['High'].iloc[i] > data['High'].iloc[i+1]):
                    levels['resistance'].append(data['High'].iloc[i])
            
            return levels
            
        except Exception as e:
            logging.error(f"Error finding support/resistance levels: {e}")
            return {'support': [], 'resistance': []}
    
    def _compare_support_resistance_levels(self, current_levels: Dict, historical_levels: Dict) -> float:
        """Compare support and resistance levels between patterns"""
        try:
            score = 0.0
            comparisons = 0
            
            # Compare number of support/resistance levels
            current_support_count = len(current_levels.get('support', []))
            historical_support_count = len(historical_levels.get('support', []))
            
            current_resistance_count = len(current_levels.get('resistance', []))
            historical_resistance_count = len(historical_levels.get('resistance', []))
            
            # Score based on similar number of levels
            if current_support_count > 0 and historical_support_count > 0:
                support_similarity = 1 - abs(current_support_count - historical_support_count) / max(current_support_count, historical_support_count)
                score += support_similarity
                comparisons += 1
            
            if current_resistance_count > 0 and historical_resistance_count > 0:
                resistance_similarity = 1 - abs(current_resistance_count - historical_resistance_count) / max(current_resistance_count, historical_resistance_count)
                score += resistance_similarity
                comparisons += 1
            
            return score / comparisons if comparisons > 0 else 0.5
            
        except Exception as e:
            logging.error(f"Error comparing support/resistance levels: {e}")
            return 0.5
    
    def _get_sector_correlation(self, symbol1: str, symbol2: str) -> float:
        """Get sector correlation between two symbols (simplified)"""
        # This is a simplified version. In production, you'd use sector classification APIs
        tech_stocks = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'AMD', 'NFLX', 'CRM', 'ADBE', 'ORCL', 'INTC']
        finance_stocks = ['JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'USB', 'PNC', 'TFC', 'COF']
        
        if symbol1 in tech_stocks and symbol2 in tech_stocks:
            return 0.8
        elif symbol1 in finance_stocks and symbol2 in finance_stocks:
            return 0.8
        elif symbol1 == symbol2:
            return 1.0
        else:
            return 0.4
    
    def _calculate_volatility_ratio(self, current_data: pd.DataFrame, historical_data: pd.DataFrame) -> float:
        """Calculate volatility ratio between current and historical patterns"""
        try:
            current_vol = current_data['Close'].pct_change().std()
            historical_vol = historical_data['Close'].pct_change().std()
            
            if historical_vol == 0:
                return 1.0
            
            return current_vol / historical_vol
            
        except Exception as e:
            logging.error(f"Error calculating volatility ratio: {e}")
            return 1.0
    
    def _calculate_trend_similarity(self, current_data: pd.DataFrame, historical_data: pd.DataFrame) -> float:
        """Calculate trend similarity between patterns"""
        try:
            current_trend = self._identify_trend_pattern(current_data)
            historical_trend = self._identify_trend_pattern(historical_data)
            
            if current_trend == historical_trend:
                return 1.0
            elif (current_trend in ['uptrend', 'downtrend'] and 
                  historical_trend in ['uptrend', 'downtrend']):
                return 0.5  # Both trending but opposite directions
            else:
                return 0.2  # Different trend types
                
        except Exception as e:
            logging.error(f"Error calculating trend similarity: {e}")
            return 0.5

    def get_detailed_analysis(self, matches: List[HistoricalMatch]) -> Dict:
        """Generate detailed analysis report from historical matches"""
        if not matches:
            return {'error': 'No historical matches found'}
        
        # Aggregate outcomes
        outcomes = {}
        total_scores = {
            'price_correlation': 0,
            'volume_correlation': 0,
            'pattern_match_score': 0,
            'technical_score': 0,
            'composite_score': 0
        }
        
        for match in matches:
            outcome = match.outcome.get('outcome', 'unknown')
            if outcome not in outcomes:
                outcomes[outcome] = []
            outcomes[outcome].append(match)
            
            # Aggregate scores
            total_scores['price_correlation'] += match.price_correlation
            total_scores['volume_correlation'] += match.volume_correlation
            total_scores['pattern_match_score'] += match.pattern_match_score
            total_scores['technical_score'] += match.technical_score
            total_scores['composite_score'] += match.composite_score
        
        # Calculate averages
        num_matches = len(matches)
        avg_scores = {k: v / num_matches for k, v in total_scores.items()}
        
        # Generate predictions based on historical outcomes
        predictions = self._generate_predictions_from_outcomes(outcomes)
        
        return {
            'total_matches': num_matches,
            'average_scores': avg_scores,
            'outcome_distribution': {k: len(v) for k, v in outcomes.items()},
            'predictions': predictions,
            'top_matches': matches[:5],  # Top 5 matches
            'confidence_analysis': self._analyze_confidence_distribution(matches)
        }
    
    def _generate_predictions_from_outcomes(self, outcomes: Dict) -> Dict:
        """Generate predictions based on historical outcomes"""
        total_matches = sum(len(matches) for matches in outcomes.values())
        if total_matches == 0:
            return {}
        
        predictions = {}
        
        # Calculate probability of each outcome
        for outcome, matches in outcomes.items():
            probability = len(matches) / total_matches
            predictions[outcome] = {
                'probability': probability,
                'count': len(matches),
                'avg_return': np.mean([m.outcome.get('total_return', 0) for m in matches]),
                'avg_max_gain': np.mean([m.outcome.get('max_gain', 0) for m in matches]),
                'avg_max_loss': np.mean([m.outcome.get('max_loss', 0) for m in matches])
            }
        
        # Determine most likely outcome
        most_likely = max(predictions.keys(), key=lambda x: predictions[x]['probability'])
        predictions['most_likely_outcome'] = most_likely
        
        return predictions
    
    def _analyze_confidence_distribution(self, matches: List[HistoricalMatch]) -> Dict:
        """Analyze confidence distribution of matches"""
        confidence_counts = {}
        for match in matches:
            confidence = match.confidence_level
            confidence_counts[confidence] = confidence_counts.get(confidence, 0) + 1
        
        return {
            'distribution': confidence_counts,
            'high_confidence_matches': len([m for m in matches if m.confidence_level in ['high', 'very_high']]),
            'average_composite_score': np.mean([m.composite_score for m in matches])
        }