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
            
            # RSI analysis
            rsi = ta.rsi(hist['Close']).iloc[-1]
            
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
        """Get historical comparison for the pattern with chart data"""
        try:
            import yfinance as yf
            from datetime import datetime, timedelta
            
            # Enhanced historical patterns with specific examples and timeframes
            historical_examples = {
                'breakout': {
                    'text': 'Similar breakout patterns were seen in TSLA during March 2020 when it broke above $150 resistance with massive volume, leading to a 300% gain over 6 months. The key was the volume confirmation above 3x average.',
                    'example_symbol': 'TSLA',
                    'example_period': '2020-02-01:2020-09-01',
                    'chart_title': 'TSLA Breakout Pattern - March 2020'
                },
                'bull_flag': {
                    'text': 'This bull flag formation mirrors AMD\'s pattern in October 2022, where after a 40% run-up, it consolidated for 3 weeks before breaking out for another 25% move. Volume dried up during the flag and surged on breakout.',
                    'example_symbol': 'AMD',
                    'example_period': '2022-09-01:2022-12-01',
                    'chart_title': 'AMD Bull Flag Pattern - October 2022'
                },
                'cup_and_handle': {
                    'text': 'Similar to AAPL\'s cup and handle in Q2 2020, where it formed a 6-week base around $320, then a 2-week handle before breaking to new highs. The pattern showed classic decreasing volume in the cup.',
                    'example_symbol': 'AAPL',
                    'example_period': '2020-04-01:2020-08-01',
                    'chart_title': 'AAPL Cup & Handle - Q2 2020'
                },
                'consolidation': {
                    'text': 'Reminiscent of NVDA\'s consolidation in early 2023, where it traded sideways for 6 weeks between $210-$240 before the AI rally began. Volume was below average during the consolidation phase.',
                    'example_symbol': 'NVDA',
                    'example_period': '2023-01-01:2023-04-01',
                    'chart_title': 'NVDA Consolidation - Early 2023'
                },
                'reversal': {
                    'text': 'This reversal pattern is similar to META\'s bottom in November 2022 at $88, where RSI was oversold for weeks before forming a double bottom and reversing higher for a 200% gain.',
                    'example_symbol': 'META',
                    'example_period': '2022-10-01:2023-02-01',
                    'chart_title': 'META Reversal Pattern - November 2022'
                }
            }
            
            example = historical_examples.get(pattern)
            if not example:
                return {
                    'text': 'This pattern is unique - no direct historical comparison available.',
                    'chart_data': None
                }
            
            # Get historical chart data for the example
            try:
                ticker = yf.Ticker(example['example_symbol'])
                period_dates = example['example_period'].split(':')
                start_date = period_dates[0]
                end_date = period_dates[1]
                
                hist = ticker.history(start=start_date, end=end_date)
                
                if not hist.empty:
                    # Prepare chart data
                    chart_data = {
                        'dates': [date.strftime('%Y-%m-%d') for date in hist.index],
                        'prices': hist['Close'].tolist(),
                        'volumes': hist['Volume'].tolist(),
                        'highs': hist['High'].tolist(),
                        'lows': hist['Low'].tolist(),
                        'opens': hist['Open'].tolist(),
                        'symbol': example['example_symbol'],
                        'title': example['chart_title']
                    }
                    
                    return {
                        'text': example['text'],
                        'chart_data': chart_data
                    }
                else:
                    return {
                        'text': example['text'],
                        'chart_data': None
                    }
                    
            except Exception as e:
                logging.error(f"Error fetching historical comparison chart data: {e}")
                return {
                    'text': example['text'],
                    'chart_data': None
                }
                
        except Exception as e:
            logging.error(f"Error in get_historical_comparison: {e}")
            return {
                'text': self.historical_patterns.get(pattern, 
                    'This pattern is unique - no direct historical comparison available.'),
                'chart_data': None
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
