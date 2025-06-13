import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import logging
from datetime import datetime, timedelta
import json

class AnimatedSparklines:
    def __init__(self):
        """Initialize the animated sparklines generator"""
        self.cache = {}
        self.cache_duration = 300  # 5 minutes cache
        
    def generate_sparkline_data(self, symbol: str, period: str = "1d", interval: str = "5m") -> Dict:
        """Generate sparkline data with animation keyframes"""
        try:
            cache_key = f"{symbol}_{period}_{interval}"
            current_time = datetime.now()
            
            # Check cache
            if (cache_key in self.cache and 
                (current_time - self.cache[cache_key]['timestamp']).seconds < self.cache_duration):
                return self.cache[cache_key]['data']
            
            # Fetch fresh data
            stock = yf.Ticker(symbol)
            hist = stock.history(period=period, interval=interval)
            
            if hist.empty:
                return {'error': f'No data available for {symbol}'}
            
            # Calculate sparkline metrics with proper error handling
            try:
                prices = hist['Close'].values
                volumes = hist['Volume'].values
                timestamps = [int(ts.timestamp() * 1000) for ts in hist.index]
                
                # Ensure we have valid data
                if len(prices) == 0:
                    return {'error': f'No price data available for {symbol}'}
                
                # Calculate performance metrics
                start_price = float(prices[0])
                current_price = float(prices[-1])
                high_price = float(np.max(prices))
                low_price = float(np.min(prices))
            except Exception as e:
                return {'error': f'Error processing data for {symbol}: {str(e)}'}
            
            price_change = current_price - start_price
            price_change_pct = (price_change / start_price) * 100
            
            # Generate simplified animation data
            try:
                animation_frames = self._generate_animation_frames(np.array(prices), timestamps)
                volatility_bands = self._calculate_volatility_bands(np.array(prices))
                price_events = self._detect_price_events(np.array(prices), timestamps)
                momentum_data = self._calculate_momentum_indicators(hist)
            except Exception as e:
                # Fallback to basic data if animation features fail
                animation_frames = []
                volatility_bands = {'trend': 'stable', 'upper': high_price, 'lower': low_price}
                price_events = []
                momentum_data = {'rsi': 50, 'trend_strength': 0.5}
            
            # Determine candle guy mood based on price movement
            if price_change_pct > 5:
                candle_guy_mood = 'excited'
            elif price_change_pct > 2:
                candle_guy_mood = 'bullish'
            elif price_change_pct < -5:
                candle_guy_mood = 'bearish'
            elif price_change_pct < -2:
                candle_guy_mood = 'confused'
            else:
                candle_guy_mood = 'neutral'

            sparkline_data = {
                'symbol': symbol,
                'period': period,
                'interval': interval,
                'current_price': float(current_price),
                'start_price': float(start_price),
                'high_price': float(high_price),
                'low_price': float(low_price),
                'price_change': float(price_change),
                'price_change_pct': float(price_change_pct),
                'prices': [float(p) for p in prices],
                'volumes': [float(v) for v in volumes],
                'timestamps': timestamps,
                'animation_frames': animation_frames,
                'volatility_bands': volatility_bands,
                'price_events': price_events,
                'momentum_data': momentum_data,
                'candle_guy_mood': candle_guy_mood,
                'animation_speed': min(2.0, abs(price_change_pct) / 5),
                'trend_direction': 'up' if price_change > 0 else 'down' if price_change < 0 else 'flat',
                'volatility_score': float(abs(price_change_pct)),
                'volume_trend': 'increasing' if len(volumes) > 1 and volumes[-1] > volumes[0] else 'decreasing',
                'generated_at': current_time.isoformat()
            }
            
            # Cache the result
            self.cache[cache_key] = {
                'data': sparkline_data,
                'timestamp': current_time
            }
            
            return sparkline_data
            
        except Exception as e:
            logging.error(f"Error generating sparkline data for {symbol}: {e}")
            return {'error': str(e)}
    
    def _generate_animation_frames(self, prices: np.ndarray, timestamps: List[int]) -> List[Dict]:
        """Generate keyframes for smooth price animation"""
        frames = []
        
        for i in range(len(prices)):
            # Calculate animation properties for each price point
            frame = {
                'timestamp': timestamps[i],
                'price': float(prices[i]),
                'progress': i / (len(prices) - 1),  # 0 to 1 progress
                'velocity': 0,
                'acceleration': 0
            }
            
            # Calculate velocity (rate of price change)
            if i > 0:
                price_diff = prices[i] - prices[i-1]
                time_diff = (timestamps[i] - timestamps[i-1]) / 1000  # Convert to seconds
                frame['velocity'] = float(price_diff / time_diff) if time_diff > 0 else 0
            
            # Calculate acceleration (rate of velocity change)
            if i > 1:
                prev_velocity = frames[i-1]['velocity']
                frame['acceleration'] = float(frame['velocity'] - prev_velocity)
            
            frames.append(frame)
        
        return frames
    
    def _calculate_volatility_bands(self, prices: np.ndarray) -> Dict:
        """Calculate volatility bands for visual enhancement"""
        mean_price = np.mean(prices)
        std_price = np.std(prices)
        
        return {
            'upper_band': float(mean_price + 2 * std_price),
            'middle_band': float(mean_price),
            'lower_band': float(mean_price - 2 * std_price),
            'band_width': float(4 * std_price),
            'squeeze_level': float(std_price / mean_price)  # Normalized volatility
        }
    
    def _detect_price_events(self, prices: np.ndarray, timestamps: List[int]) -> List[Dict]:
        """Detect significant price movement events for animation highlights"""
        events = []
        
        if len(prices) < 3:
            return events
        
        # Calculate price changes
        price_changes = np.diff(prices)
        change_threshold = np.std(price_changes) * 1.5  # 1.5 standard deviations
        
        for i in range(1, len(prices)):
            change = price_changes[i-1]
            
            if abs(change) > change_threshold:
                event_type = 'spike_up' if change > 0 else 'spike_down'
                
                events.append({
                    'timestamp': timestamps[i],
                    'price': float(prices[i]),
                    'type': event_type,
                    'magnitude': float(abs(change)),
                    'intensity': min(float(abs(change) / change_threshold), 3.0)  # Cap at 3x
                })
        
        return events
    
    def _calculate_momentum_indicators(self, hist: pd.DataFrame) -> Dict:
        """Calculate momentum indicators for animation dynamics"""
        try:
            closes = hist['Close']
            volumes = hist['Volume']
            
            # Simple momentum indicators
            momentum_data = {
                'rsi': None,
                'macd_signal': None,
                'volume_sma_ratio': None,
                'price_momentum': None
            }
            
            # RSI calculation (simplified)
            if len(closes) >= 14:
                deltas = closes.diff()
                gains = deltas.where(deltas > 0, 0)
                losses = -deltas.where(deltas < 0, 0)
                
                avg_gain = gains.rolling(window=14).mean()
                avg_loss = losses.rolling(window=14).mean()
                
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
                momentum_data['rsi'] = float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else None
            
            # Volume momentum
            if len(volumes) >= 10:
                volume_sma = volumes.rolling(window=10).mean()
                current_volume = volumes.iloc[-1]
                momentum_data['volume_sma_ratio'] = float(current_volume / volume_sma.iloc[-1]) if volume_sma.iloc[-1] > 0 else 1.0
            
            # Price momentum (rate of change)
            if len(closes) >= 5:
                price_momentum = (closes.iloc[-1] - closes.iloc[-5]) / closes.iloc[-5] * 100
                momentum_data['price_momentum'] = float(price_momentum)
            
            return momentum_data
            
        except Exception as e:
            logging.error(f"Error calculating momentum indicators: {e}")
            return {'rsi': None, 'macd_signal': None, 'volume_sma_ratio': None, 'price_momentum': None}
    
    def _calculate_volume_trend(self, volumes: np.ndarray) -> str:
        """Calculate volume trend for animation intensity"""
        if len(volumes) < 5:
            return 'stable'
        
        recent_volume = np.mean(volumes[-3:])
        earlier_volume = np.mean(volumes[-10:-3]) if len(volumes) >= 10 else np.mean(volumes[:-3])
        
        if earlier_volume == 0:
            return 'stable'
        
        volume_change = (recent_volume - earlier_volume) / earlier_volume
        
        if volume_change > 0.2:
            return 'increasing'
        elif volume_change < -0.2:
            return 'decreasing'
        else:
            return 'stable'
    
    def generate_multiple_sparklines(self, symbols: List[str], period: str = "1d", interval: str = "5m") -> Dict:
        """Generate sparkline data for multiple symbols"""
        results = {}
        
        for symbol in symbols:
            results[symbol] = self.generate_sparkline_data(symbol, period, interval)
        
        return {
            'sparklines': results,
            'generated_at': datetime.now().isoformat(),
            'total_symbols': len(symbols),
            'successful': len([r for r in results.values() if 'error' not in r])
        }
    
    def get_sparkline_summary(self, symbol: str) -> Dict:
        """Get a summary of sparkline data suitable for dashboard widgets"""
        try:
            full_data = self.generate_sparkline_data(symbol, period="1d", interval="15m")
            
            if 'error' in full_data:
                return full_data
            
            # Create condensed summary for dashboard use
            summary = {
                'symbol': symbol,
                'current_price': full_data['current_price'],
                'price_change': full_data['price_change'],
                'price_change_pct': full_data['price_change_pct'],
                'trend_direction': full_data['trend_direction'],
                'volatility_score': full_data['volatility_score'],
                'mini_chart_data': {
                    'prices': full_data['prices'][-20:],  # Last 20 points for mini chart
                    'timestamps': full_data['timestamps'][-20:],
                    'trend_color': '#22c55e' if full_data['price_change'] > 0 else '#ef4444' if full_data['price_change'] < 0 else '#6b7280'
                },
                'animation_speed': self._calculate_animation_speed(full_data),
                'last_updated': full_data['generated_at']
            }
            
            return summary
            
        except Exception as e:
            logging.error(f"Error generating sparkline summary for {symbol}: {e}")
            return {'error': str(e)}
    
    def _calculate_animation_speed(self, sparkline_data: Dict) -> float:
        """Calculate optimal animation speed based on volatility and momentum"""
        base_speed = 1.0
        
        # Adjust based on volatility
        volatility_multiplier = min(sparkline_data['volatility_score'] / 5.0, 2.0)
        
        # Adjust based on price events
        event_multiplier = 1.0
        if sparkline_data['price_events']:
            max_intensity = max([event['intensity'] for event in sparkline_data['price_events']])
            event_multiplier = min(1.0 + max_intensity * 0.3, 2.0)
        
        # Adjust based on volume trend
        volume_multiplier = 1.0
        if sparkline_data['volume_trend'] == 'increasing':
            volume_multiplier = 1.3
        elif sparkline_data['volume_trend'] == 'decreasing':
            volume_multiplier = 0.8
        
        return base_speed * volatility_multiplier * event_multiplier * volume_multiplier
    
    def clear_cache(self):
        """Clear the sparkline data cache"""
        self.cache.clear()
        
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        current_time = datetime.now()
        valid_entries = 0
        
        for cache_key, cache_data in self.cache.items():
            if (current_time - cache_data['timestamp']).seconds < self.cache_duration:
                valid_entries += 1
        
        return {
            'total_entries': len(self.cache),
            'valid_entries': valid_entries,
            'cache_duration_seconds': self.cache_duration,
            'last_access': current_time.isoformat()
        }