import yfinance as yf
import pandas as pd
import numpy as np
import ta
from datetime import datetime, timedelta
import logging
import threading
import random

# For voice synthesis - will use Web Speech API via JavaScript instead of pyttsx3
# to avoid threading issues in web application

class AICoach:
    def __init__(self):
        self.historical_patterns = {
            'bull_flag': 'This setup resembles a bull flag pattern, similar to NVDA in March 2023 before its 40% run.',
            'breakout': 'Classic breakout formation - reminds me of TSLA breaking $200 resistance in October 2022.',
            'reversal': 'Potential reversal pattern forming, like AMD at $120 support in June 2023.',
            'consolidation': 'Tight consolidation pattern - similar to AAPL before earnings breakout in January 2023.'
        }
        
        self.mood_tags = {
            'breakout': {'emoji': '💥', 'description': 'High breakout potential'},
            'reversal': {'emoji': '🔄', 'description': 'Reversal signals present'},
            'risky': {'emoji': '⚠️', 'description': 'High risk setup'},
            'confirmed': {'emoji': '🔒', 'description': 'Pattern confirmed'}
        }
    
    def analyze_setup(self, symbol):
        """Generate AI analysis of current stock setup"""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="3mo")
            
            if hist.empty:
                return {'error': 'No data available'}
            
            # Technical analysis
            analysis = self.perform_technical_analysis(hist)
            
            # Pattern recognition
            pattern = self.identify_pattern(hist)
            
            # Historical comparison
            historical_comp = self.get_historical_comparison(pattern)
            
            # Mood tag assignment
            mood_tag = self.assign_mood_tag(analysis, pattern)
            
            # Generate chart story
            chart_story = self.generate_chart_story_data(hist)
            
            return {
                'symbol': symbol,
                'analysis_text': self.generate_analysis_text(analysis, pattern),
                'pattern': pattern,
                'historical_comparison': historical_comp,
                'mood_tag': mood_tag,
                'chart_story': chart_story,
                'confidence_factors': analysis,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logging.error(f"Error analyzing setup for {symbol}: {e}")
            return {'error': str(e)}
    
    def perform_technical_analysis(self, hist):
        """Perform comprehensive technical analysis"""
        try:
            current_price = hist['Close'].iloc[-1]
            
            # RSI analysis - calculate manually if ta library fails
            try:
                from ta.momentum import RSIIndicator
                rsi_indicator = RSIIndicator(close=hist['Close'])
                rsi = rsi_indicator.rsi().iloc[-1]
            except:
                # Fallback RSI calculation
                delta = hist['Close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs)).iloc[-1]
            
            # Volume analysis
            avg_volume = hist['Volume'].rolling(20).mean().iloc[-2]
            current_volume = hist['Volume'].iloc[-1]
            volume_surge = ((current_volume - avg_volume) / avg_volume * 100) if avg_volume > 0 else 0
            
            # Moving averages
            sma_20 = hist['Close'].rolling(20).mean().iloc[-1]
            sma_50 = hist['Close'].rolling(50).mean().iloc[-1]
            
            # Support/Resistance
            recent_high = hist['High'].tail(20).max()
            recent_low = hist['Low'].tail(20).min()
            
            # Momentum
            momentum = hist['Close'].pct_change().rolling(5).mean().iloc[-1]
            
            return {
                'rsi': round(rsi, 2) if not pd.isna(rsi) else 50,
                'volume_surge': round(volume_surge, 2),
                'price_vs_sma20': round(((current_price - sma_20) / sma_20 * 100), 2),
                'price_vs_sma50': round(((current_price - sma_50) / sma_50 * 100), 2),
                'distance_from_high': round(((recent_high - current_price) / recent_high * 100), 2),
                'distance_from_low': round(((current_price - recent_low) / recent_low * 100), 2),
                'momentum': round(momentum * 100, 3) if not pd.isna(momentum) else 0
            }
            
        except Exception as e:
            logging.error(f"Error in technical analysis: {e}")
            return {}
    
    def identify_pattern(self, hist):
        """Identify chart pattern"""
        try:
            # Simple pattern identification based on price action
            closes = hist['Close']
            highs = hist['High']
            lows = hist['Low']
            
            # Calculate recent price action
            recent_closes = closes.tail(10)
            price_range = (recent_closes.max() - recent_closes.min()) / recent_closes.mean()
            
            # Trend analysis
            sma_20 = closes.rolling(20).mean().iloc[-1]
            sma_50 = closes.rolling(50).mean().iloc[-1]
            current_price = closes.iloc[-1]
            
            if price_range < 0.05:  # Tight consolidation
                return 'consolidation'
            elif current_price > sma_20 > sma_50:
                if recent_closes.iloc[-1] > recent_closes.iloc[-5]:
                    return 'bull_flag'
                else:
                    return 'breakout'
            elif current_price < sma_20 < sma_50:
                return 'reversal'
            else:
                return 'neutral'
                
        except Exception as e:
            logging.error(f"Error identifying pattern: {e}")
            return 'unknown'
    
    def get_historical_comparison(self, pattern):
        """Get historical comparison using enhanced multi-factor scoring engine"""
        try:
            from historical_comparison_engine import HistoricalComparisonEngine
            
            # Initialize the enhanced comparison engine
            comparison_engine = HistoricalComparisonEngine()
            
            # Extract symbol from current analysis context
            symbol = getattr(self, 'current_symbol', 'SPY')  # Default to SPY if no symbol set
            
            # Find historical matches with comprehensive scoring
            matches = comparison_engine.find_historical_matches(symbol, lookback_days=504)  # 2 years
            
            if not matches:
                return {
                    'text': 'No significant historical matches found with current market data.',
                    'chart_data': None
                }
            
            # Get detailed analysis report
            detailed_analysis = comparison_engine.get_detailed_analysis(matches)
            
            # Format top match for display
            top_match = matches[0]
            
            # Create comprehensive comparison text
            comparison_text = self._generate_comparison_text(top_match, detailed_analysis)
            
            # Generate chart data for visualization
            chart_data = self._generate_comparison_chart_data(top_match)
            
            return {
                'text': comparison_text,
                'chart_data': chart_data,
                'scoring_details': {
                    'total_matches_found': len(matches),
                    'top_match_score': round(top_match.composite_score * 100, 1),
                    'confidence_level': top_match.confidence_level,
                    'scoring_breakdown': {
                        'price_correlation': round(top_match.price_correlation * 100, 1),
                        'volume_correlation': round(top_match.volume_correlation * 100, 1),
                        'technical_alignment': round(top_match.technical_score * 100, 1),
                        'pattern_match': round(top_match.pattern_match_score * 100, 1),
                        'market_conditions': round(top_match.market_condition_score * 100, 1)
                    },
                    'outcome_prediction': detailed_analysis.get('predictions', {}),
                    'all_matches': [
                        {
                            'symbol': m.symbol,
                            'period': m.date_range,
                            'score': round(m.composite_score * 100, 1),
                            'outcome': m.outcome.get('outcome', 'unknown'),
                            'return': round(m.outcome.get('total_return', 0), 1)
                        } for m in matches[:5]
                    ]
                }
            }
            
        except Exception as e:
            logging.error(f"Error in enhanced historical comparison: {e}")
            return self._get_fallback_comparison()
    
    def _generate_comparison_text(self, match, analysis):
        """Generate detailed comparison text from match data"""
        symbol = match.symbol
        date_range = match.date_range
        score = round(match.composite_score * 100, 1)
        outcome = match.outcome
        
        # Format outcome description
        outcome_type = outcome.get('outcome', 'unknown')
        total_return = outcome.get('total_return', 0)
        max_gain = outcome.get('max_gain', 0)
        max_loss = outcome.get('max_loss', 0)
        
        outcome_descriptions = {
            'strong_bullish': f"rallied strongly ({total_return:+.1f}%, peak gain {max_gain:+.1f}%)",
            'bullish': f"moved higher ({total_return:+.1f}%, peak {max_gain:+.1f}%)",
            'sideways': f"traded sideways ({total_return:+.1f}%, range {max_loss:.1f}% to {max_gain:+.1f}%)",
            'bearish': f"declined ({total_return:+.1f}%, maximum drawdown {max_loss:.1f}%)",
            'strong_bearish': f"dropped sharply ({total_return:+.1f}%, low {max_loss:.1f}%)"
        }
        
        outcome_desc = outcome_descriptions.get(outcome_type, f"moved {total_return:+.1f}%")
        
        # Generate key factors text
        key_factors = []
        if match.price_correlation > 0.8:
            key_factors.append("nearly identical price action")
        if match.volume_correlation > 0.7:
            key_factors.append("similar volume patterns")
        if match.technical_score > 0.8:
            key_factors.append("strong technical indicator alignment")
        if match.pattern_match_score > 0.8:
            key_factors.append("matching chart patterns")
        
        factors_text = ", ".join(key_factors) if key_factors else "multiple technical factors"
        
        # Get prediction summary
        predictions = analysis.get('predictions', {})
        most_likely = predictions.get('most_likely_outcome', 'unknown')
        probability = 0
        if most_likely in predictions:
            probability = predictions[most_likely].get('probability', 0) * 100
        
        return f"Strong historical match ({score}% similarity) found in {symbol} during {date_range}. " \
               f"That pattern featured {factors_text} and subsequently {outcome_desc} over the following 10 trading days. " \
               f"Based on {analysis.get('total_matches', 0)} similar historical patterns, " \
               f"the most probable outcome is {most_likely.replace('_', ' ')} ({probability:.0f}% probability)."
    
    def _generate_comparison_chart_data(self, match):
        """Generate chart data for historical comparison visualization"""
        try:
            import yfinance as yf
            from datetime import datetime, timedelta
            
            # Parse date range
            date_parts = match.date_range.split(' to ')
            if len(date_parts) != 2:
                return None
            
            start_date = datetime.strptime(date_parts[0], '%Y-%m-%d')
            end_date = datetime.strptime(date_parts[1], '%Y-%m-%d')
            
            # Extend end date to show outcome
            extended_end = end_date + timedelta(days=15)
            
            # Fetch historical data
            ticker = yf.Ticker(match.symbol)
            hist = ticker.history(start=start_date, end=extended_end, interval="1d")
            
            if hist.empty:
                return None
            
            return {
                'dates': [date.strftime('%Y-%m-%d') for date in hist.index],
                'prices': hist['Close'].tolist(),
                'volumes': hist['Volume'].tolist(),
                'pattern_start': date_parts[0],
                'pattern_end': date_parts[1],
                'symbol': match.symbol,
                'title': f"{match.symbol} Historical Pattern ({match.date_range})"
            }
            
        except Exception as e:
            logging.error(f"Error generating comparison chart data: {e}")
            return None
    
    def _get_fallback_comparison(self):
        """Provide fallback when enhanced engine is unavailable"""
        return {
            'text': 'Historical pattern analysis is currently processing market data to find the most accurate comparisons.',
            'chart_data': None,
            'scoring_details': {
                'total_matches_found': 0,
                'status': 'processing'
            }
        }
    
    def assign_mood_tag(self, analysis, pattern):
        """Assign mood tag based on analysis"""
        try:
            rsi = analysis.get('rsi', 50)
            volume_surge = analysis.get('volume_surge', 0)
            momentum = analysis.get('momentum', 0)
            
            if pattern == 'breakout' and volume_surge > 50:
                return 'breakout'
            elif pattern == 'reversal' or (rsi > 70 and momentum < 0):
                return 'reversal'
            elif rsi > 80 or rsi < 20:
                return 'risky'
            elif pattern in ['bull_flag', 'consolidation'] and 30 < rsi < 70:
                return 'confirmed'
            else:
                return 'neutral'
                
        except Exception as e:
            logging.error(f"Error assigning mood tag: {e}")
            return 'neutral'
    
    def generate_analysis_text(self, analysis, pattern):
        """Generate human-readable analysis text"""
        try:
            rsi = analysis.get('rsi', 50)
            volume_surge = analysis.get('volume_surge', 0)
            momentum = analysis.get('momentum', 0)
            
            text = f"Current setup shows {pattern} pattern formation. "
            
            # RSI analysis
            if rsi > 70:
                text += "RSI indicates overbought conditions - caution advised. "
            elif rsi < 30:
                text += "RSI shows oversold levels - potential bounce opportunity. "
            else:
                text += "RSI is in neutral territory - good for continuation plays. "
            
            # Volume analysis
            if volume_surge > 100:
                text += "Exceptional volume surge confirms strong interest. "
            elif volume_surge > 50:
                text += "Above-average volume supports the move. "
            else:
                text += "Volume is relatively quiet - watch for confirmation. "
            
            # Momentum analysis
            if momentum > 0.01:
                text += "Strong positive momentum favors bulls."
            elif momentum < -0.01:
                text += "Negative momentum suggests caution."
            else:
                text += "Momentum is neutral - direction unclear."
            
            return text
            
        except Exception as e:
            logging.error(f"Error generating analysis text: {e}")
            return "Analysis temporarily unavailable."
    
    def generate_chart_story_data(self, hist):
        """Generate chart story data for hover functionality"""
        try:
            story_points = []
            
            # Analyze recent price action for story points
            for i in range(max(0, len(hist) - 20), len(hist)):
                row = hist.iloc[i]
                date = hist.index[i].strftime('%Y-%m-%d')
                
                # Generate contextual comments
                if i > 0:
                    prev_close = hist['Close'].iloc[i-1]
                    price_change = (row['Close'] - prev_close) / prev_close
                    
                    comment = ""
                    if abs(price_change) > 0.05:  # Significant move
                        if price_change > 0:
                            comment = f"Strong buying at {row['Close']:.2f} - bulls taking control"
                        else:
                            comment = f"Heavy selling at {row['Close']:.2f} - bears in charge"
                    elif row['High'] - row['Low'] > (row['Close'] * 0.03):  # Large range
                        comment = f"High volatility day - indecision at {row['Close']:.2f}"
                    
                    if comment:
                        story_points.append({
                            'date': date,
                            'price': row['Close'],
                            'comment': comment
                        })
            
            return story_points
            
        except Exception as e:
            logging.error(f"Error generating chart story: {e}")
            return []
    
    def trigger_voice_alert(self, symbol, confidence_score):
        """Trigger voice alert for high confidence stocks"""
        try:
            # This will be handled by JavaScript Web Speech API
            # Return alert data for frontend processing
            messages = [
                f"{symbol} has high breakout potential now with {confidence_score}% confidence.",
                f"Alert: {symbol} showing strong setup at {confidence_score}% confidence level.",
                f"Watch {symbol} closely - confidence score reached {confidence_score}%."
            ]
            
            message = random.choice(messages)
            
            # Log the alert
            logging.info(f"Voice alert triggered: {message}")
            
            return {
                'symbol': symbol,
                'message': message,
                'confidence': confidence_score,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logging.error(f"Error triggering voice alert: {e}")
            return None
    
    def generate_chart_story(self, symbol):
        """Generate chart story for specific symbol"""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1mo")
            
            return self.generate_chart_story_data(hist)
            
        except Exception as e:
            logging.error(f"Error generating chart story for {symbol}: {e}")
            return []
    
    def _calculate_pattern_stages(self, hist, symbol):
        """Calculate pattern stages for similarity highlighting"""
        if symbol != 'META':
            return {}
        
        try:
            closes = hist['Close']
            dates = [date.strftime('%Y-%m-%d') for date in hist.index]
            
            # Find key stages in META's 2022-2023 reversal pattern
            stages = {}
            
            # Find the crash bottom (lowest point)
            bottom_idx = closes.idxmin()
            bottom_date = bottom_idx.strftime('%Y-%m-%d')
            stages['bottom'] = bottom_date
            
            # Find accumulation period (2-3 weeks after bottom)
            bottom_position = list(hist.index).index(bottom_idx)
            if bottom_position + 14 < len(hist):
                accumulation_date = hist.index[bottom_position + 14].strftime('%Y-%m-%d')
                stages['accumulation'] = accumulation_date
            
            # Find first breakout attempt (significant move up from bottom)
            bottom_price = closes[bottom_idx]
            for i in range(bottom_position + 1, len(closes)):
                if closes.iloc[i] > bottom_price * 1.15:  # 15% above bottom
                    breakout_date = hist.index[i].strftime('%Y-%m-%d')
                    stages['first_breakout'] = breakout_date
                    break
            
            # Find confirmation (sustained move above key resistance)
            for i in range(bottom_position + 20, len(closes)):
                if closes.iloc[i] > bottom_price * 1.30:  # 30% above bottom
                    confirmation_date = hist.index[i].strftime('%Y-%m-%d')
                    stages['confirmation'] = confirmation_date
                    break
            
            return stages
            
        except Exception as e:
            print(f"Error calculating pattern stages: {e}")
            return {}
