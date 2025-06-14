"""
Simplified Sparklines Engine for CandleCast
Generates mini stock charts with candle guy character integration
"""

import yfinance as yf
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
import time
import threading

try:
    from performance_optimizer import cached_api_call, perf_optimizer
    PERFORMANCE_OPTIMIZED = True
except ImportError:
    PERFORMANCE_OPTIMIZED = False
    def cached_api_call(ttl=300):
        def decorator(func):
            return func
        return decorator

class SimpleSparklines:
    def __init__(self):
        """Initialize the simple sparklines generator"""
        self.cache = {}
        self.cache_duration = 300  # 5 minutes
        self.api_call_times = []
        self.max_calls_per_minute = 30
        self.lock = threading.Lock()
        
        if PERFORMANCE_OPTIMIZED:
            # Use performance optimizer's cache but fallback to dict interface
            self.perf_cache = perf_optimizer.cache
        else:
            self.perf_cache = None
        
    def _rate_limit_check(self):
        """Check and enforce API rate limiting"""
        with self.lock:
            now = time.time()
            # Remove calls older than 1 minute
            self.api_call_times = [t for t in self.api_call_times if now - t < 60]
            
            # Check if we're at the limit
            if len(self.api_call_times) >= self.max_calls_per_minute:
                sleep_time = 60 - (now - self.api_call_times[0])
                if sleep_time > 0:
                    time.sleep(sleep_time)
            
            # Record this call
            self.api_call_times.append(now)

    @cached_api_call(ttl=300)
    def _fetch_stock_data(self, symbol: str, period: str = "1d", interval: str = "5m"):
        """Fetch stock data with caching and rate limiting"""
        self._rate_limit_check()
        ticker = yf.Ticker(symbol)
        return ticker.history(period=period, interval=interval)

    def generate_sparkline(self, symbol: str) -> Dict:
        """Generate sparkline data for a stock symbol"""
        try:
            # Check cache first
            cache_key = f"{symbol}_sparkline"
            
            if PERFORMANCE_OPTIMIZED and self.perf_cache:
                cached_result = self.perf_cache.get(cache_key)
                if cached_result:
                    return cached_result
            else:
                if cache_key in self.cache:
                    cached_data = self.cache[cache_key]
                    if datetime.now().timestamp() - cached_data['timestamp'] < self.cache_duration:
                        return cached_data['data']
            
            # Fetch recent stock data with rate limiting
            hist = self._fetch_stock_data(symbol)
            
            if hist.empty:
                return {'error': f'No data available for {symbol}'}
            
            # Extract price data
            prices = hist['Close'].values
            volumes = hist['Volume'].values
            
            if len(prices) == 0:
                return {'error': f'No price data for {symbol}'}
            
            # Calculate basic metrics
            start_price = float(prices[0])
            current_price = float(prices[-1])
            high_price = float(np.max(prices))
            low_price = float(np.min(prices))
            
            price_change = current_price - start_price
            price_change_pct = (price_change / start_price) * 100 if start_price > 0 else 0
            
            # Determine candle guy mood
            if price_change_pct > 3:
                mood = 'excited'
            elif price_change_pct > 1:
                mood = 'bullish'
            elif price_change_pct < -3:
                mood = 'bearish'
            elif price_change_pct < -1:
                mood = 'confused'
            else:
                mood = 'neutral'
            
            # Create timestamps
            timestamps = [int(ts.timestamp() * 1000) for ts in hist.index]
            
            sparkline_data = {
                'symbol': symbol,
                'prices': [float(p) for p in prices],
                'timestamps': timestamps,
                'current_price': current_price,
                'start_price': start_price,
                'high_price': high_price,
                'low_price': low_price,
                'price_change': price_change,
                'price_change_pct': price_change_pct,
                'candle_guy_mood': mood,
                'animation_speed': min(2.0, abs(price_change_pct) / 2),
                'trend_direction': 'up' if price_change > 0 else 'down' if price_change < 0 else 'flat',
                'volatility_score': float(abs(price_change_pct)),
                'volume_trend': 'increasing' if len(volumes) > 1 and volumes[-1] > volumes[0] else 'decreasing',
                'generated_at': datetime.now().isoformat()
            }
            
            # Cache the result
            self.cache[cache_key] = {
                'data': sparkline_data,
                'timestamp': datetime.now().timestamp()
            }
            
            return sparkline_data
            
        except Exception as e:
            logging.error(f"Error generating sparkline for {symbol}: {e}")
            return {'error': f'Failed to generate sparkline: {str(e)}'}
    
    def generate_multiple_sparklines(self, symbols: List[str]) -> Dict[str, Dict]:
        """Generate sparklines for multiple symbols"""
        results = {}
        for symbol in symbols:
            results[symbol] = self.generate_sparkline(symbol)
        return results
    
    def clear_cache(self):
        """Clear the sparkline cache"""
        self.cache.clear()