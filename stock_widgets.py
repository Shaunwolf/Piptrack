"""
Stock Widgets System
Enhanced stock widget generation with real-time data and technical indicators
"""
import yfinance as yf
import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
import time

class StockWidgets:
    def __init__(self):
        self.cache = {}
        self.cache_duration = 300  # 5 minutes
        
    def generate_widget_data(self, symbol, chart_type='rsi_momentum'):
        """Generate enhanced widget data for a stock symbol"""
        try:
            # Check cache first
            cache_key = f"{symbol}_{chart_type}"
            current_time = time.time()
            
            if cache_key in self.cache:
                cache_data, cache_time = self.cache[cache_key]
                if current_time - cache_time < self.cache_duration:
                    return cache_data
            
            # Get fresh data
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="3mo", interval="1d")
            
            if hist.empty:
                return {'error': f'No data available for {symbol}'}
            
            current_price = hist['Close'].iloc[-1]
            
            # Calculate technical indicators
            widget_data = {
                'symbol': symbol,
                'current_price': round(float(current_price), 2),
                'price_change': self._calculate_price_change(hist),
                'rsi': self._calculate_rsi(hist),
                'volume_analysis': self._calculate_volume_analysis(hist),
                'momentum_score': self._calculate_momentum_score(hist),
                'chart_data': self._generate_chart_data(hist, chart_type),
                'fibonacci_levels': self._calculate_fibonacci_levels(hist),
                'support_resistance': self._find_support_resistance(hist),
                'trend_strength': self._calculate_trend_strength(hist),
                'last_updated': datetime.now().isoformat()
            }
            
            # Cache the result
            self.cache[cache_key] = (widget_data, current_time)
            
            return widget_data
            
        except Exception as e:
            logging.error(f"Error generating widget data for {symbol}: {e}")
            return {'error': str(e)}
    
    def generate_multiple_widgets(self, symbols, chart_type='rsi_momentum'):
        """Generate widget data for multiple symbols"""
        widgets = {}
        for symbol in symbols:
            widgets[symbol] = self.generate_widget_data(symbol, chart_type)
            time.sleep(0.1)  # Rate limiting
        return widgets
    
    def _calculate_price_change(self, hist):
        """Calculate price change and percentage"""
        try:
            current_price = hist['Close'].iloc[-1]
            prev_price = hist['Close'].iloc[-2]
            change = current_price - prev_price
            change_percent = (change / prev_price) * 100
            
            return {
                'absolute': round(float(change), 2),
                'percentage': round(float(change_percent), 2),
                'direction': 'up' if change > 0 else 'down'
            }
        except:
            return {'absolute': 0, 'percentage': 0, 'direction': 'neutral'}
    
    def _calculate_rsi(self, hist, period=14):
        """Calculate RSI indicator"""
        try:
            delta = hist['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            current_rsi = rsi.iloc[-1]
            if pd.isna(current_rsi):
                return 50
            
            return round(float(current_rsi), 2)
        except:
            return 50
    
    def _calculate_volume_analysis(self, hist):
        """Calculate volume analysis"""
        try:
            avg_volume = hist['Volume'].rolling(20).mean().iloc[-1]
            current_volume = hist['Volume'].iloc[-1]
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
            
            return {
                'current': int(current_volume),
                'average': int(avg_volume),
                'ratio': round(float(volume_ratio), 2),
                'status': 'high' if volume_ratio > 1.5 else 'normal' if volume_ratio > 0.8 else 'low'
            }
        except:
            return {'current': 0, 'average': 0, 'ratio': 1, 'status': 'normal'}
    
    def _calculate_momentum_score(self, hist):
        """Calculate momentum score (0-100)"""
        try:
            # Price momentum (40%)
            price_change_5d = (hist['Close'].iloc[-1] / hist['Close'].iloc[-6] - 1) * 100
            price_momentum = min(100, max(0, (price_change_5d + 10) * 3))
            
            # Volume momentum (30%)
            vol_ratio = hist['Volume'].iloc[-1] / hist['Volume'].rolling(10).mean().iloc[-1]
            volume_momentum = min(100, max(0, vol_ratio * 30))
            
            # RSI momentum (30%)
            rsi = self._calculate_rsi(hist)
            rsi_momentum = 100 if 30 <= rsi <= 70 else max(0, 100 - abs(rsi - 50) * 2)
            
            total_momentum = (price_momentum * 0.4 + volume_momentum * 0.3 + rsi_momentum * 0.3)
            return round(float(total_momentum), 1)
        except:
            return 50.0
    
    def _generate_chart_data(self, hist, chart_type):
        """Generate chart data based on type"""
        try:
            chart_data = {
                'dates': [d.strftime('%Y-%m-%d') for d in hist.index[-30:]],
                'prices': [round(float(p), 2) for p in hist['Close'][-30:]],
                'volumes': [int(v) for v in hist['Volume'][-30:]]
            }
            
            if chart_type == 'rsi_momentum':
                rsi_values = []
                for i in range(len(hist)):
                    if i >= 13:  # Need 14 periods for RSI
                        subset = hist.iloc[i-13:i+1]
                        rsi = self._calculate_rsi(subset)
                        rsi_values.append(rsi)
                    else:
                        rsi_values.append(50)
                
                chart_data['rsi'] = rsi_values[-30:]
            
            return chart_data
        except:
            return {'dates': [], 'prices': [], 'volumes': []}
    
    def _calculate_fibonacci_levels(self, hist):
        """Calculate Fibonacci retracement levels"""
        try:
            high = hist['High'].max()
            low = hist['Low'].min()
            diff = high - low
            
            return {
                'high': round(float(high), 2),
                'low': round(float(low), 2),
                'fib_23_6': round(float(high - 0.236 * diff), 2),
                'fib_38_2': round(float(high - 0.382 * diff), 2),
                'fib_50_0': round(float(high - 0.5 * diff), 2),
                'fib_61_8': round(float(high - 0.618 * diff), 2)
            }
        except:
            return {}
    
    def _find_support_resistance(self, hist):
        """Find key support and resistance levels"""
        try:
            recent_data = hist[-20:]  # Last 20 days
            highs = recent_data['High'].values
            lows = recent_data['Low'].values
            
            # Simple pivot point calculation
            resistance = np.percentile(highs, 80)
            support = np.percentile(lows, 20)
            
            return {
                'resistance': round(float(resistance), 2),
                'support': round(float(support), 2)
            }
        except:
            return {'resistance': 0, 'support': 0}
    
    def _calculate_trend_strength(self, hist):
        """Calculate trend strength (0-100)"""
        try:
            # Simple moving averages
            sma_10 = hist['Close'].rolling(10).mean().iloc[-1]
            sma_20 = hist['Close'].rolling(20).mean().iloc[-1]
            current_price = hist['Close'].iloc[-1]
            
            # Trend alignment score
            if current_price > sma_10 > sma_20:
                trend_score = 80
            elif current_price > sma_20:
                trend_score = 60
            elif current_price < sma_10 < sma_20:
                trend_score = 20
            else:
                trend_score = 40
            
            return round(float(trend_score), 1)
        except:
            return 50.0
    
    def clear_cache(self):
        """Clear the widget cache"""
        self.cache.clear()
    
    def get_cache_stats(self):
        """Get cache statistics"""
        return {
            'cached_items': len(self.cache),
            'cache_duration': self.cache_duration
        }