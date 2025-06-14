"""
Enhanced Volume Analysis for Pump Detection
Phase 1 Enhancement: Time-normalized volume and block trade detection
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, time as dt_time
from typing import Dict, List, Tuple
import logging

class EnhancedVolumeAnalyzer:
    """Enhanced volume analysis with time normalization and block trade detection"""
    
    def __init__(self):
        # Market hours for volume normalization
        self.market_open = dt_time(9, 30)  # 9:30 AM
        self.market_close = dt_time(16, 0)  # 4:00 PM
        
        # Volume thresholds
        self.block_trade_threshold = 1000000  # $1M+ trades
        self.unusual_volume_threshold = 3.0   # 3x normal volume
        self.extreme_volume_threshold = 10.0  # 10x normal volume
        
        # Time-of-day volume patterns (normalized multipliers)
        self.time_multipliers = {
            '09:30-10:00': 2.5,  # Market open surge
            '10:00-11:00': 1.2,
            '11:00-12:00': 0.8,
            '12:00-13:00': 0.6,  # Lunch lull
            '13:00-14:00': 0.9,
            '14:00-15:00': 1.1,
            '15:00-15:30': 1.3,
            '15:30-16:00': 2.0,  # Market close surge
            'premarket': 0.3,
            'afterhours': 0.2
        }
    
    def analyze_volume_patterns(self, symbol: str, period: str = '5d') -> Dict:
        """Comprehensive volume pattern analysis"""
        try:
            ticker = yf.Ticker(symbol)
            
            # Get detailed intraday data
            hist_1d = ticker.history(period='1d', interval='5m')
            hist_5d = ticker.history(period=period, interval='1d')
            
            if hist_1d.empty or hist_5d.empty:
                return {'error': f'No volume data available for {symbol}'}
            
            # Calculate various volume metrics
            volume_metrics = self._calculate_volume_metrics(hist_1d, hist_5d)
            
            # Detect unusual patterns
            patterns = self._detect_volume_patterns(hist_1d, hist_5d)
            
            # Analyze block trades
            block_trades = self._analyze_block_trades(hist_1d, symbol)
            
            # Time-of-day analysis
            time_analysis = self._analyze_time_patterns(hist_1d)
            
            # Calculate pump probability based on volume
            pump_probability = self._calculate_volume_pump_probability(volume_metrics, patterns)
            
            return {
                'symbol': symbol,
                'volume_metrics': volume_metrics,
                'patterns': patterns,
                'block_trades': block_trades,
                'time_analysis': time_analysis,
                'pump_probability': pump_probability,
                'analysis_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logging.error(f"Error analyzing volume for {symbol}: {e}")
            return {'error': str(e)}
    
    def _calculate_volume_metrics(self, hist_1d: pd.DataFrame, hist_5d: pd.DataFrame) -> Dict:
        """Calculate comprehensive volume metrics"""
        if hist_1d.empty or hist_5d.empty:
            return {}
        
        # Current and recent volume
        current_volume = hist_1d['Volume'].iloc[-1] if not hist_1d.empty else 0
        today_volume = hist_1d['Volume'].sum()
        
        # Historical averages
        avg_volume_5d = hist_5d['Volume'].mean()
        avg_volume_20d = hist_5d['Volume'][-20:].mean() if len(hist_5d) >= 20 else avg_volume_5d
        
        # Volume ratios
        volume_ratio_5d = today_volume / avg_volume_5d if avg_volume_5d > 0 else 1
        volume_ratio_20d = today_volume / avg_volume_20d if avg_volume_20d > 0 else 1
        
        # Intraday volume distribution
        total_intraday = hist_1d['Volume'].sum()
        morning_volume = hist_1d.between_time('09:30', '12:00')['Volume'].sum() if not hist_1d.empty else 0
        afternoon_volume = hist_1d.between_time('12:00', '16:00')['Volume'].sum() if not hist_1d.empty else 0
        
        # Volume momentum (recent vs earlier)
        if len(hist_1d) >= 20:
            recent_volume = hist_1d['Volume'][-10:].mean()
            earlier_volume = hist_1d['Volume'][-20:-10].mean()
            volume_momentum = recent_volume / earlier_volume if earlier_volume > 0 else 1
        else:
            volume_momentum = 1
        
        # Volume volatility
        volume_std = hist_5d['Volume'].std()
        volume_volatility = volume_std / avg_volume_5d if avg_volume_5d > 0 else 0
        
        return {
            'current_volume': float(current_volume),
            'today_total_volume': float(today_volume),
            'avg_volume_5d': float(avg_volume_5d),
            'avg_volume_20d': float(avg_volume_20d),
            'volume_ratio_5d': float(volume_ratio_5d),
            'volume_ratio_20d': float(volume_ratio_20d),
            'morning_volume_pct': float(morning_volume / total_intraday * 100) if total_intraday > 0 else 0,
            'afternoon_volume_pct': float(afternoon_volume / total_intraday * 100) if total_intraday > 0 else 0,
            'volume_momentum': float(volume_momentum),
            'volume_volatility': float(volume_volatility)
        }
    
    def _detect_volume_patterns(self, hist_1d: pd.DataFrame, hist_5d: pd.DataFrame) -> Dict:
        """Detect unusual volume patterns"""
        patterns = {}
        
        if hist_1d.empty or hist_5d.empty:
            return patterns
        
        # Volume spike detection
        current_volume = hist_1d['Volume'].iloc[-1]
        recent_avg = hist_1d['Volume'][-10:].mean()
        
        if current_volume > recent_avg * self.extreme_volume_threshold:
            patterns['extreme_volume_spike'] = True
            patterns['spike_magnitude'] = float(current_volume / recent_avg)
        elif current_volume > recent_avg * self.unusual_volume_threshold:
            patterns['unusual_volume_spike'] = True
            patterns['spike_magnitude'] = float(current_volume / recent_avg)
        
        # Volume accumulation pattern
        volume_trend = self._calculate_volume_trend(hist_1d['Volume'])
        if volume_trend > 0.3:
            patterns['volume_accumulation'] = True
            patterns['accumulation_strength'] = float(volume_trend)
        
        # Pre-market volume analysis
        try:
            premarket_data = hist_1d.between_time('04:00', '09:30')
            if not premarket_data.empty:
                premarket_volume = premarket_data['Volume'].sum()
                normal_premarket = hist_5d['Volume'].mean() * 0.1  # Estimate
                if premarket_volume > normal_premarket * 3:
                    patterns['high_premarket_volume'] = True
                    patterns['premarket_ratio'] = float(premarket_volume / normal_premarket)
        except:
            pass  # No premarket data available
        
        # Volume distribution pattern
        volume_distribution = self._analyze_volume_distribution(hist_1d)
        patterns.update(volume_distribution)
        
        return patterns
    
    def _calculate_volume_trend(self, volume_series: pd.Series) -> float:
        """Calculate volume trend using linear regression slope"""
        if len(volume_series) < 5:
            return 0
        
        x = np.arange(len(volume_series))
        y = volume_series.values
        
        # Simple linear regression
        n = len(x)
        slope = (n * np.sum(x * y) - np.sum(x) * np.sum(y)) / (n * np.sum(x**2) - np.sum(x)**2)
        
        # Normalize slope by average volume
        avg_volume = np.mean(y)
        normalized_slope = slope / avg_volume if avg_volume > 0 else 0
        
        return float(normalized_slope)
    
    def _analyze_volume_distribution(self, hist_1d: pd.DataFrame) -> Dict:
        """Analyze intraday volume distribution patterns"""
        if hist_1d.empty:
            return {}
        
        # Group by hour
        hist_1d_copy = hist_1d.copy()
        hist_1d_copy['hour'] = hist_1d_copy.index.hour
        hourly_volume = hist_1d_copy.groupby('hour')['Volume'].sum()
        
        total_volume = hourly_volume.sum()
        if total_volume == 0:
            return {}
        
        # Calculate concentration ratio (Gini coefficient style)
        sorted_volumes = hourly_volume.sort_values(ascending=False)
        cumulative_pct = np.cumsum(sorted_volumes) / total_volume
        
        # If top 2 hours have >60% of volume, it's concentrated
        concentration_ratio = cumulative_pct.iloc[:2].iloc[-1] if len(cumulative_pct) >= 2 else 0
        
        return {
            'volume_concentration': float(concentration_ratio),
            'concentrated_trading': concentration_ratio > 0.6,
            'peak_hour': int(sorted_volumes.index[0]) if not sorted_volumes.empty else 10,
            'hourly_distribution': hourly_volume.to_dict()
        }
    
    def _analyze_block_trades(self, hist_1d: pd.DataFrame, symbol: str) -> Dict:
        """Analyze potential block trades (large volume candles)"""
        if hist_1d.empty:
            return {}
        
        # Calculate dollar volume for each period
        hist_1d_copy = hist_1d.copy()
        hist_1d_copy['dollar_volume'] = hist_1d_copy['Volume'] * hist_1d_copy['Close']
        
        # Identify large dollar volume periods
        avg_dollar_volume = hist_1d_copy['dollar_volume'].mean()
        large_trades = hist_1d_copy[hist_1d_copy['dollar_volume'] > avg_dollar_volume * 5]
        
        block_trades = []
        for idx, trade in large_trades.iterrows():
            block_trades.append({
                'timestamp': idx.strftime('%H:%M'),
                'volume': float(trade['Volume']),
                'dollar_volume': float(trade['dollar_volume']),
                'price': float(trade['Close']),
                'magnitude': float(trade['dollar_volume'] / avg_dollar_volume)
            })
        
        # Sort by magnitude
        block_trades.sort(key=lambda x: x['magnitude'], reverse=True)
        
        return {
            'block_trade_count': len(block_trades),
            'total_block_volume': sum(trade['dollar_volume'] for trade in block_trades),
            'largest_block_trades': block_trades[:5],
            'block_trade_ratio': len(block_trades) / len(hist_1d) if len(hist_1d) > 0 else 0
        }
    
    def _analyze_time_patterns(self, hist_1d: pd.DataFrame) -> Dict:
        """Analyze volume patterns by time of day"""
        if hist_1d.empty:
            return {}
        
        hist_1d_copy = hist_1d.copy()
        hist_1d_copy['time_str'] = hist_1d_copy.index.strftime('%H:%M')
        
        # Group into time buckets
        time_buckets = {
            'market_open': hist_1d.between_time('09:30', '10:30')['Volume'].sum(),
            'mid_morning': hist_1d.between_time('10:30', '12:00')['Volume'].sum(),
            'lunch_time': hist_1d.between_time('12:00', '14:00')['Volume'].sum(),
            'afternoon': hist_1d.between_time('14:00', '15:30')['Volume'].sum(),
            'market_close': hist_1d.between_time('15:30', '16:00')['Volume'].sum()
        }
        
        total_volume = sum(time_buckets.values())
        if total_volume == 0:
            return time_buckets
        
        # Calculate percentages
        time_percentages = {k: (v / total_volume * 100) for k, v in time_buckets.items()}
        
        # Identify unusual patterns
        unusual_patterns = {}
        if time_percentages['market_open'] > 40:
            unusual_patterns['heavy_opening'] = True
        if time_percentages['market_close'] > 30:
            unusual_patterns['heavy_closing'] = True
        if time_percentages['lunch_time'] > 25:
            unusual_patterns['lunch_volume_spike'] = True
        
        return {
            'time_buckets': {k: float(v) for k, v in time_buckets.items()},
            'time_percentages': {k: float(v) for k, v in time_percentages.items()},
            'unusual_patterns': unusual_patterns
        }
    
    def _calculate_volume_pump_probability(self, metrics: Dict, patterns: Dict) -> float:
        """Calculate pump probability based on volume analysis"""
        if not metrics or not patterns:
            return 0
        
        score = 0
        
        # Volume ratio scoring (0-40 points)
        volume_ratio = metrics.get('volume_ratio_5d', 1)
        if volume_ratio >= 10:
            score += 40
        elif volume_ratio >= 5:
            score += 30
        elif volume_ratio >= 3:
            score += 20
        elif volume_ratio >= 2:
            score += 10
        
        # Volume spike patterns (0-25 points)
        if patterns.get('extreme_volume_spike'):
            score += 25
        elif patterns.get('unusual_volume_spike'):
            score += 15
        
        # Block trades (0-15 points)
        block_ratio = patterns.get('block_trade_ratio', 0)
        if block_ratio > 0.3:
            score += 15
        elif block_ratio > 0.1:
            score += 8
        
        # Volume accumulation (0-10 points)
        if patterns.get('volume_accumulation'):
            score += 10
        
        # Time pattern analysis (0-10 points)
        time_patterns = patterns.get('unusual_patterns', {})
        if time_patterns.get('heavy_opening') or time_patterns.get('heavy_closing'):
            score += 5
        if patterns.get('high_premarket_volume'):
            score += 5
        
        return min(100, score)
    
    def get_volume_alerts(self, symbol: str) -> List[Dict]:
        """Generate volume-based alerts"""
        analysis = self.analyze_volume_patterns(symbol)
        
        if 'error' in analysis:
            return []
        
        alerts = []
        metrics = analysis.get('volume_metrics', {})
        patterns = analysis.get('patterns', {})
        
        # Extreme volume alert
        if patterns.get('extreme_volume_spike'):
            alerts.append({
                'type': 'EXTREME_VOLUME_SPIKE',
                'message': f"{symbol}: Volume spike {patterns.get('spike_magnitude', 0):.1f}x normal",
                'urgency': 'HIGH',
                'score': 90
            })
        
        # Unusual volume alert
        elif patterns.get('unusual_volume_spike'):
            alerts.append({
                'type': 'UNUSUAL_VOLUME',
                'message': f"{symbol}: Volume {patterns.get('spike_magnitude', 0):.1f}x above normal",
                'urgency': 'MEDIUM',
                'score': 70
            })
        
        # Block trade alert
        block_trades = analysis.get('block_trades', {})
        if block_trades.get('block_trade_count', 0) >= 3:
            alerts.append({
                'type': 'BLOCK_TRADE_ACTIVITY',
                'message': f"{symbol}: {block_trades['block_trade_count']} large trades detected",
                'urgency': 'MEDIUM',
                'score': 60
            })
        
        # Volume accumulation alert
        if patterns.get('volume_accumulation'):
            alerts.append({
                'type': 'VOLUME_ACCUMULATION',
                'message': f"{symbol}: Sustained volume accumulation pattern",
                'urgency': 'LOW',
                'score': 50
            })
        
        return alerts