"""
Enhanced Stock Widgets with Fibonacci Scalers and Chart Indicators
Replaces sparklines with colored Fibonacci-style visualization
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
import ta

try:
    from performance_optimizer import cached_api_call
    PERFORMANCE_OPTIMIZED = True
except ImportError:
    PERFORMANCE_OPTIMIZED = False
    def cached_api_call(ttl=300):
        def decorator(func):
            return func
        return decorator

class FibonacciScaler:
    """Creates colored Fibonacci-style scalers for stock widgets"""
    
    def __init__(self):
        self.fibonacci_levels = [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0]
        self.colors = {
            'extreme_oversold': '#ff4444',    # Red
            'oversold': '#ff8800',            # Orange  
            'neutral_low': '#ffcc00',         # Yellow
            'neutral': '#00ff88',             # Green
            'neutral_high': '#00ccff',        # Light Blue
            'overbought': '#4488ff',          # Blue
            'extreme_overbought': '#8844ff'   # Purple
        }
    
    def calculate_fibonacci_position(self, current_price: float, high: float, low: float) -> Dict:
        """Calculate position within Fibonacci retracement levels"""
        if high == low:
            return {'level': 0.5, 'color': self.colors['neutral'], 'label': 'Neutral'}
        
        # Calculate position (0 = low, 1 = high)
        position = (current_price - low) / (high - low)
        position = max(0, min(1, position))  # Clamp between 0 and 1
        
        # Find closest Fibonacci level
        closest_level = min(self.fibonacci_levels, key=lambda x: abs(x - position))
        
        # Determine color and label based on position
        if position <= 0.236:
            color = self.colors['extreme_oversold']
            label = 'Extreme Oversold'
        elif position <= 0.382:
            color = self.colors['oversold']
            label = 'Oversold'
        elif position <= 0.5:
            color = self.colors['neutral_low']
            label = 'Below Neutral'
        elif position <= 0.618:
            color = self.colors['neutral']
            label = 'Neutral'
        elif position <= 0.786:
            color = self.colors['neutral_high']
            label = 'Above Neutral'
        elif position <= 0.9:
            color = self.colors['overbought']
            label = 'Overbought'
        else:
            color = self.colors['extreme_overbought']
            label = 'Extreme Overbought'
        
        return {
            'position': position,
            'level': closest_level,
            'color': color,
            'label': label,
            'percentage': round(position * 100, 1)
        }

class ChartIndicators:
    """Generates various chart indicators for stock analysis"""
    
    def __init__(self):
        self.chart_types = {
            'rsi_momentum': self.generate_rsi_chart,
            'bollinger_squeeze': self.generate_bollinger_chart,
            'macd_divergence': self.generate_macd_chart,
            'volume_profile': self.generate_volume_chart,
            'support_resistance': self.generate_sr_chart
        }
    
    def generate_rsi_chart(self, data: pd.DataFrame) -> Dict:
        """Generate RSI momentum chart data"""
        rsi = ta.momentum.RSIIndicator(data['Close']).rsi()
        
        current_rsi = float(rsi.iloc[-1]) if not rsi.empty and not pd.isna(rsi.iloc[-1]) else 50.0
        rsi_values = [float(val) if not pd.isna(val) else 50.0 for val in rsi[-20:]]
        
        chart_data = {
            'type': 'rsi_momentum',
            'title': 'RSI Momentum Analysis',
            'data': [
                {
                    'x': [str(ts) for ts in data.index[-20:]],
                    'y': rsi_values,
                    'type': 'line',
                    'name': 'RSI',
                    'line': {'color': '#00ff88', 'width': 2}
                }
            ],
            'current_value': current_rsi,
            'signal': 'BUY' if current_rsi < 30 else 'SELL' if current_rsi > 70 else 'HOLD'
        }
        
        return chart_data
    
    def generate_bollinger_chart(self, data: pd.DataFrame) -> Dict:
        """Generate Bollinger Bands squeeze chart"""
        bb = ta.volatility.BollingerBands(data['Close'])
        
        squeeze_detected = self._detect_squeeze(bb)
        breakout_direction = self._predict_breakout(data, bb)
        
        chart_data = {
            'type': 'bollinger_squeeze',
            'title': 'Bollinger Bands Analysis',
            'squeeze_detected': bool(squeeze_detected),
            'breakout_direction': str(breakout_direction),
            'status': 'Active Squeeze' if squeeze_detected else 'Normal Range',
            'signal_color': '#ffcc00' if squeeze_detected else '#6b7280'
        }
        
        return chart_data
    
    def generate_macd_chart(self, data: pd.DataFrame) -> Dict:
        """Generate MACD divergence chart"""
        macd = ta.trend.MACD(data['Close'])
        
        bullish_div = self._detect_bullish_divergence(data, macd)
        bearish_div = self._detect_bearish_divergence(data, macd)
        
        chart_data = {
            'type': 'macd_divergence',
            'title': 'MACD Analysis',
            'bullish_divergence': bool(bullish_div),
            'bearish_divergence': bool(bearish_div)
        }
        
        return chart_data
    
    def generate_volume_chart(self, data: pd.DataFrame) -> Dict:
        """Generate volume profile chart"""
        volume_sma = data['Volume'].rolling(window=10).mean()
        
        current_volume = float(data['Volume'].iloc[-1])
        avg_volume = float(volume_sma.iloc[-1]) if not pd.isna(volume_sma.iloc[-1]) else current_volume
        
        chart_data = {
            'type': 'volume_profile',
            'title': 'Volume Analysis',
            'volume_trend': str(self._analyze_volume_trend(data)),
            'unusual_volume': bool(current_volume > avg_volume * 2)
        }
        
        return chart_data
    
    def generate_sr_chart(self, data: pd.DataFrame) -> Dict:
        """Generate support/resistance chart"""
        support_levels, resistance_levels = self._find_support_resistance(data)
        key_distances = self._calculate_key_level_distance(data, support_levels, resistance_levels)
        
        chart_data = {
            'type': 'support_resistance',
            'title': 'Support & Resistance',
            'support_level': float(support_levels) if support_levels else 0.0,
            'resistance_level': float(resistance_levels) if resistance_levels else 0.0,
            'key_level_distance': {
                'support_distance': f"{key_distances.get('support_distance', 0):.2f}",
                'resistance_distance': f"{key_distances.get('resistance_distance', 0):.2f}"
            }
        }
        
        return chart_data
    
    def _detect_squeeze(self, bb) -> bool:
        """Detect Bollinger Band squeeze"""
        band_width = bb.bollinger_hband() - bb.bollinger_lband()
        avg_width = band_width.rolling(window=20).mean()
        return band_width.iloc[-1] < avg_width.iloc[-1] * 0.8
    
    def _predict_breakout(self, data, bb) -> str:
        """Predict breakout direction"""
        price = data['Close'].iloc[-1]
        middle = bb.bollinger_mavg().iloc[-1]
        return 'UP' if price > middle else 'DOWN'
    
    def _detect_bullish_divergence(self, data, macd) -> bool:
        """Detect bullish MACD divergence"""
        recent_prices = data['Close'][-10:]
        recent_macd = macd.macd()[-10:]
        
        if len(recent_prices) < 5:
            return False
            
        price_trend = recent_prices.iloc[-1] < recent_prices.iloc[-5]
        macd_trend = recent_macd.iloc[-1] > recent_macd.iloc[-5]
        
        return price_trend and macd_trend
    
    def _detect_bearish_divergence(self, data, macd) -> bool:
        """Detect bearish MACD divergence"""
        recent_prices = data['Close'][-10:]
        recent_macd = macd.macd()[-10:]
        
        if len(recent_prices) < 5:
            return False
            
        price_trend = recent_prices.iloc[-1] > recent_prices.iloc[-5]
        macd_trend = recent_macd.iloc[-1] < recent_macd.iloc[-5]
        
        return price_trend and macd_trend
    
    def _analyze_volume_trend(self, data) -> str:
        """Analyze volume trend"""
        recent_volume = data['Volume'][-5:].mean()
        previous_volume = data['Volume'][-10:-5].mean()
        
        if recent_volume > previous_volume * 1.2:
            return 'INCREASING'
        elif recent_volume < previous_volume * 0.8:
            return 'DECREASING'
        else:
            return 'STABLE'
    
    def _find_support_resistance(self, data) -> tuple:
        """Find support and resistance levels"""
        highs = data['High'][-20:]
        lows = data['Low'][-20:]
        
        # Simple pivot point calculation
        resistance = []
        support = []
        
        for i in range(1, len(highs) - 1):
            # Resistance: local high
            if highs.iloc[i] > highs.iloc[i-1] and highs.iloc[i] > highs.iloc[i+1]:
                resistance.append(float(highs.iloc[i]))
            
            # Support: local low
            if lows.iloc[i] < lows.iloc[i-1] and lows.iloc[i] < lows.iloc[i+1]:
                support.append(float(lows.iloc[i]))
        
        return sorted(support, reverse=True)[:3], sorted(resistance)[:3]
    
    def _calculate_key_level_distance(self, data, support, resistance) -> Dict:
        """Calculate distance to key levels"""
        current_price = float(data['Close'].iloc[-1])
        
        nearest_support = max([s for s in support if s < current_price], default=0)
        nearest_resistance = min([r for r in resistance if r > current_price], default=current_price * 1.1)
        
        return {
            'support_distance': round(((current_price - nearest_support) / current_price) * 100, 2),
            'resistance_distance': round(((nearest_resistance - current_price) / current_price) * 100, 2),
            'nearest_support': nearest_support,
            'nearest_resistance': nearest_resistance
        }

class EnhancedStockWidgets:
    """Main class for enhanced stock widgets with Fibonacci scalers"""
    
    def __init__(self):
        self.fibonacci_scaler = FibonacciScaler()
        self.chart_indicators = ChartIndicators()
        self.cache = {}
        self.cache_duration = 300  # 5 minutes
    
    @cached_api_call(ttl=300)
    def _fetch_stock_data(self, symbol: str) -> pd.DataFrame:
        """Fetch stock data with caching"""
        ticker = yf.Ticker(symbol)
        return ticker.history(period="1d", interval="5m")
    
    def generate_widget_data(self, symbol: str, chart_type: str = 'rsi_momentum') -> Dict:
        """Generate complete widget data with Fibonacci scaler and chart"""
        try:
            # Fetch stock data
            data = self._fetch_stock_data(symbol)
            
            if data.empty:
                return {'error': f'No data available for {symbol}'}
            
            current_price = float(data['Close'].iloc[-1])
            day_high = float(data['High'].max())
            day_low = float(data['Low'].min())
            
            # Calculate price change
            prev_close = float(data['Close'].iloc[0])
            price_change = current_price - prev_close
            change_percent = (price_change / prev_close) * 100
            
            # Generate Fibonacci scaler
            fibonacci_data = self.fibonacci_scaler.calculate_fibonacci_position(
                current_price, day_high, day_low
            )
            
            # Generate chart indicator
            chart_data = None
            if chart_type in self.chart_indicators.chart_types:
                chart_data = self.chart_indicators.chart_types[chart_type](data)
            
            widget_data = {
                'symbol': symbol,
                'current_price': current_price,
                'price_change': price_change,
                'change_percent': change_percent,
                'day_high': day_high,
                'day_low': day_low,
                'volume': int(data['Volume'].iloc[-1]),
                'fibonacci': fibonacci_data,
                'chart': chart_data,
                'last_updated': datetime.now().isoformat()
            }
            
            return widget_data
            
        except Exception as e:
            logging.error(f"Error generating widget for {symbol}: {e}")
            return {'error': str(e)}
    
    def generate_multiple_widgets(self, symbols: List[str], chart_type: str = 'rsi_momentum') -> Dict:
        """Generate multiple stock widgets"""
        widgets = {}
        
        for symbol in symbols[:5]:  # Limit to 5 symbols for performance
            try:
                widget_data = self.generate_widget_data(symbol, chart_type)
                widgets[symbol] = widget_data
            except Exception as e:
                logging.warning(f"Failed to generate widget for {symbol}: {e}")
                widgets[symbol] = {'error': f'Data unavailable for {symbol}'}
        
        return widgets
    
    def get_available_chart_types(self) -> List[Dict]:
        """Get list of available chart indicator types"""
        return [
            {'id': 'rsi_momentum', 'name': 'RSI Momentum', 'description': 'Relative Strength Index with overbought/oversold levels'},
            {'id': 'bollinger_squeeze', 'name': 'Bollinger Squeeze', 'description': 'Bollinger Bands with squeeze detection'},
            {'id': 'macd_divergence', 'name': 'MACD Divergence', 'description': 'MACD with bullish/bearish divergence signals'},
            {'id': 'volume_profile', 'name': 'Volume Profile', 'description': 'Volume analysis with trend detection'},
            {'id': 'support_resistance', 'name': 'Support & Resistance', 'description': 'Key support and resistance levels'}
        ]

# Global instance
enhanced_widgets = EnhancedStockWidgets()