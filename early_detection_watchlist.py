"""
Early Detection Watchlist for Pre-Pump Identification
Identifies stocks showing early pump signals before they fully develop
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import logging
import json

class EarlyDetectionWatchlist:
    """Identify stocks showing early pre-pump signals"""
    
    def __init__(self):
        # Early warning thresholds (lower than main pump detection)
        self.early_thresholds = {
            'volume_increase': 1.5,      # 50% volume increase
            'short_interest': 15.0,      # 15%+ short interest  
            'price_compression': 5.0,    # 5+ days tight range
            'accumulation_score': 30,    # Early accumulation signals
            'social_mentions': 3,        # Minimum social activity
            'insider_activity': 0.02     # 2%+ insider buying
        }
        
        # Watch categories
        self.categories = {
            'short_squeeze_setup': 'High short interest with early volume signs',
            'accumulation_pattern': 'Institutional accumulation detected',
            'breakout_preparation': 'Technical setup for breakout',
            'social_momentum': 'Early social media attention',
            'insider_activity': 'Recent insider buying activity',
            'earnings_catalyst': 'Upcoming earnings with setup'
        }
        
        # Candidate pools to scan
        self.candidate_pools = {
            'meme_stocks': ['GME', 'AMC', 'BB', 'NOK', 'KOSS', 'EXPR', 'BBBY'],
            'high_short_interest': ['FUBO', 'CLOV', 'RIDE', 'WKHS', 'SPCE'],
            'low_float': ['IRNT', 'OPAD', 'ANY', 'PROG', 'ATER'],
            'penny_stocks': ['SNDL', 'NAKD', 'CTRM', 'ZOM', 'SENS'],
            'biotech': ['OCGN', 'BNGO', 'CLSK', 'RIOT', 'MARA'],
            'recent_ipos': ['HOOD', 'RBLX', 'COIN', 'PLTR', 'SNOW']
        }
    
    def scan_early_pump_signals(self, symbol_pools: List[str] = None) -> Dict:
        """Scan for early pump signals across symbol pools"""
        if symbol_pools is None:
            symbol_pools = ['meme_stocks', 'high_short_interest', 'low_float']
        
        early_candidates = []
        scan_summary = {
            'total_scanned': 0,
            'early_signals_found': 0,
            'categories_detected': set(),
            'scan_timestamp': datetime.now().isoformat()
        }
        
        for pool_name in symbol_pools:
            if pool_name in self.candidate_pools:
                symbols = self.candidate_pools[pool_name]
                
                for symbol in symbols:
                    try:
                        analysis = self.analyze_early_signals(symbol)
                        scan_summary['total_scanned'] += 1
                        
                        if analysis and analysis.get('early_score', 0) >= 25:
                            early_candidates.append(analysis)
                            scan_summary['early_signals_found'] += 1
                            scan_summary['categories_detected'].add(analysis.get('primary_category', 'unknown'))
                            
                    except Exception as e:
                        logging.error(f"Error scanning {symbol}: {e}")
                        continue
        
        # Sort by early detection score
        early_candidates.sort(key=lambda x: x.get('early_score', 0), reverse=True)
        
        # Convert set to list for JSON serialization
        scan_summary['categories_detected'] = list(scan_summary['categories_detected'])
        
        return {
            'early_candidates': early_candidates,
            'scan_summary': scan_summary,
            'watchlist_tiers': self._categorize_watchlist(early_candidates)
        }
    
    def analyze_early_signals(self, symbol: str) -> Dict:
        """Analyze individual stock for early pump signals"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            hist = ticker.history(period='3mo')
            
            if hist.empty:
                return None
            
            # Calculate early signal components
            volume_signals = self._analyze_early_volume(hist)
            price_signals = self._analyze_price_compression(hist)
            technical_signals = self._analyze_technical_setup(hist)
            fundamental_signals = self._analyze_fundamental_setup(info)
            
            # Calculate composite early score
            early_score = self._calculate_early_score(
                volume_signals, price_signals, technical_signals, fundamental_signals
            )
            
            # Determine primary category
            primary_category = self._determine_category(
                volume_signals, price_signals, technical_signals, fundamental_signals
            )
            
            # Generate early alerts
            alerts = self._generate_early_alerts(symbol, early_score, primary_category)
            
            return {
                'symbol': symbol,
                'early_score': float(early_score),
                'primary_category': primary_category,
                'signals': {
                    'volume': volume_signals,
                    'price': price_signals, 
                    'technical': technical_signals,
                    'fundamental': fundamental_signals
                },
                'alerts': alerts,
                'current_price': float(hist['Close'].iloc[-1]),
                'price_change_1d': float((hist['Close'].iloc[-1] / hist['Close'].iloc[-2] - 1) * 100),
                'volume_ratio': float(volume_signals.get('volume_ratio_5d', 1)),
                'watchlist_priority': self._get_priority_level(early_score),
                'analysis_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logging.error(f"Error analyzing early signals for {symbol}: {e}")
            return None
    
    def _analyze_early_volume(self, hist: pd.DataFrame) -> Dict:
        """Analyze early volume accumulation patterns"""
        if len(hist) < 20:
            return {'volume_ratio_5d': 1.0, 'accumulation_trend': 0}
        
        # Volume ratios
        recent_volume = hist['Volume'][-5:].mean()
        baseline_volume = hist['Volume'][-20:-5].mean()
        volume_ratio_5d = recent_volume / baseline_volume if baseline_volume > 0 else 1
        
        # Volume trend analysis
        volume_trend = self._calculate_trend(hist['Volume'][-10:])
        
        # Accumulation detection (gradual volume increase)
        accumulation_score = 0
        if 1.2 <= volume_ratio_5d <= 2.5:  # Subtle but consistent increase
            accumulation_score += 20
        if volume_trend > 0.1:  # Positive volume trend
            accumulation_score += 15
        
        return {
            'volume_ratio_5d': float(volume_ratio_5d),
            'volume_trend': float(volume_trend),
            'accumulation_score': int(accumulation_score),
            'subtle_accumulation': bool(1.2 <= volume_ratio_5d <= 2.5 and volume_trend > 0)
        }
    
    def _analyze_price_compression(self, hist: pd.DataFrame) -> Dict:
        """Analyze price compression and coiling patterns"""
        if len(hist) < 20:
            return {'compression_score': 0}
        
        # Calculate recent volatility vs historical
        recent_returns = hist['Close'][-10:].pct_change()
        historical_returns = hist['Close'][-30:-10].pct_change()
        
        recent_volatility = recent_returns.std()
        historical_volatility = historical_returns.std()
        
        compression_ratio = recent_volatility / historical_volatility if historical_volatility > 0 else 1
        
        # Bollinger Band squeeze detection
        bb_squeeze = self._detect_bb_squeeze(hist)
        
        # Range contraction
        recent_range = (hist['High'][-10:].max() - hist['Low'][-10:].min())
        historical_range = (hist['High'][-30:-10].max() - hist['Low'][-30:-10].min())
        range_contraction = recent_range / historical_range if historical_range > 0 else 1
        
        compression_score = 0
        if compression_ratio < 0.7:  # Lower volatility
            compression_score += 25
        if bb_squeeze:
            compression_score += 20
        if range_contraction < 0.8:  # Range compression
            compression_score += 15
        
        return {
            'compression_ratio': float(compression_ratio),
            'bb_squeeze': bool(bb_squeeze),
            'range_contraction': float(range_contraction),
            'compression_score': int(compression_score),
            'coiling_pattern': bool(compression_score >= 40)
        }
    
    def _analyze_technical_setup(self, hist: pd.DataFrame) -> Dict:
        """Analyze technical indicators for early setup"""
        if len(hist) < 50:
            return {'technical_score': 0}
        
        current_price = hist['Close'].iloc[-1]
        
        # Moving average positioning
        ma20 = hist['Close'].rolling(20).mean().iloc[-1]
        ma50 = hist['Close'].rolling(50).mean().iloc[-1]
        
        # RSI calculation
        delta = hist['Close'].diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1]
        
        # Support/resistance levels
        high_20 = hist['High'][-20:].max()
        low_20 = hist['Low'][-20:].min()
        price_position = (current_price - low_20) / (high_20 - low_20) * 100
        
        technical_score = 0
        
        # Moving average setup
        if current_price > ma20 > ma50:
            technical_score += 15  # Bullish alignment
        elif current_price > ma20:
            technical_score += 8
        
        # RSI positioning
        if 40 <= current_rsi <= 60:  # Neutral, ready for move
            technical_score += 20
        elif 30 <= current_rsi <= 40:  # Oversold, bounce potential
            technical_score += 25
        
        # Price position
        if 20 <= price_position <= 40:  # Lower third, accumulation zone
            technical_score += 15
        
        return {
            'ma_alignment': bool(current_price > ma20 > ma50),
            'rsi': float(current_rsi),
            'price_position': float(price_position),
            'technical_score': int(technical_score),
            'setup_quality': 'Strong' if technical_score >= 40 else 'Moderate' if technical_score >= 25 else 'Weak'
        }
    
    def _analyze_fundamental_setup(self, info: Dict) -> Dict:
        """Analyze fundamental factors for early pump potential"""
        fundamental_score = 0
        factors = []
        
        # Short interest analysis
        short_ratio = info.get('shortPercentOfFloat', 0)
        if isinstance(short_ratio, (int, float)) and short_ratio >= 15:
            fundamental_score += 30
            factors.append(f"Short interest: {short_ratio:.1f}%")
        
        # Float size
        float_shares = info.get('floatShares', info.get('sharesOutstanding', 0))
        if isinstance(float_shares, (int, float)) and float_shares < 100_000_000:
            fundamental_score += 20
            factors.append("Small float")
        
        # Market cap (prefer smaller caps for pump potential)
        market_cap = info.get('marketCap', 0)
        if isinstance(market_cap, (int, float)):
            if market_cap < 1_000_000_000:  # Under $1B
                fundamental_score += 15
                factors.append("Small cap")
            elif market_cap < 5_000_000_000:  # Under $5B
                fundamental_score += 10
        
        # Institutional ownership (prefer lower for retail pumps)
        inst_ownership = info.get('heldByInstitutions', 1)
        if isinstance(inst_ownership, (int, float)) and inst_ownership < 0.3:
            fundamental_score += 10
            factors.append("Low institutional ownership")
        
        return {
            'short_ratio': short_ratio if isinstance(short_ratio, (int, float)) else 0,
            'float_shares': float_shares if isinstance(float_shares, (int, float)) else 0,
            'market_cap': market_cap if isinstance(market_cap, (int, float)) else 0,
            'fundamental_score': fundamental_score,
            'key_factors': factors
        }
    
    def _calculate_early_score(self, volume_signals: Dict, price_signals: Dict, 
                             technical_signals: Dict, fundamental_signals: Dict) -> float:
        """Calculate composite early detection score"""
        volume_score = volume_signals.get('accumulation_score', 0)
        price_score = price_signals.get('compression_score', 0)
        tech_score = technical_signals.get('technical_score', 0)
        fund_score = fundamental_signals.get('fundamental_score', 0)
        
        # Weighted combination
        composite_score = (
            volume_score * 0.3 +      # 30% volume
            price_score * 0.25 +      # 25% price compression
            tech_score * 0.25 +       # 25% technical
            fund_score * 0.2          # 20% fundamental
        )
        
        return min(100, composite_score)
    
    def _determine_category(self, volume_signals: Dict, price_signals: Dict,
                          technical_signals: Dict, fundamental_signals: Dict) -> str:
        """Determine primary category for early signal"""
        scores = {
            'accumulation_pattern': volume_signals.get('accumulation_score', 0),
            'breakout_preparation': price_signals.get('compression_score', 0),
            'short_squeeze_setup': fundamental_signals.get('fundamental_score', 0) if fundamental_signals.get('short_ratio', 0) > 15 else 0,
            'technical_setup': technical_signals.get('technical_score', 0)
        }
        
        return max(scores.items(), key=lambda x: x[1])[0]
    
    def _generate_early_alerts(self, symbol: str, early_score: float, category: str) -> List[Dict]:
        """Generate early warning alerts"""
        alerts = []
        
        if early_score >= 60:
            alerts.append({
                'type': 'EARLY_HIGH_POTENTIAL',
                'urgency': 'MEDIUM',
                'message': f"{symbol}: Strong early pump signals detected ({early_score:.0f}/100)"
            })
        elif early_score >= 40:
            alerts.append({
                'type': 'EARLY_MODERATE_POTENTIAL', 
                'urgency': 'LOW',
                'message': f"{symbol}: Moderate early signals - monitor closely ({early_score:.0f}/100)"
            })
        elif early_score >= 25:
            alerts.append({
                'type': 'EARLY_WEAK_SIGNALS',
                'urgency': 'INFO',
                'message': f"{symbol}: Early indicators present - add to watchlist ({early_score:.0f}/100)"
            })
        
        return alerts
    
    def _get_priority_level(self, score: float) -> str:
        """Convert score to priority level"""
        if score >= 60:
            return 'High'
        elif score >= 40:
            return 'Medium'
        elif score >= 25:
            return 'Low'
        else:
            return 'Monitor'
    
    def _categorize_watchlist(self, candidates: List[Dict]) -> Dict:
        """Categorize watchlist into tiers"""
        tiers = {
            'tier_1_high_priority': [],
            'tier_2_medium_priority': [],
            'tier_3_low_priority': [],
            'monitor_list': []
        }
        
        for candidate in candidates:
            score = candidate.get('early_score', 0)
            priority = candidate.get('watchlist_priority', 'Monitor')
            
            if priority == 'High':
                tiers['tier_1_high_priority'].append(candidate)
            elif priority == 'Medium':
                tiers['tier_2_medium_priority'].append(candidate)
            elif priority == 'Low':
                tiers['tier_3_low_priority'].append(candidate)
            else:
                tiers['monitor_list'].append(candidate)
        
        return tiers
    
    def _calculate_trend(self, series: pd.Series) -> float:
        """Calculate trend using linear regression"""
        if len(series) < 3:
            return 0
        
        x = np.arange(len(series))
        y = series.values
        
        # Simple linear regression slope
        n = len(x)
        if n == 0:
            return 0
            
        slope = (n * np.sum(x * y) - np.sum(x) * np.sum(y)) / (n * np.sum(x**2) - np.sum(x)**2)
        
        # Normalize by average value
        avg_val = np.mean(y)
        normalized_slope = slope / avg_val if avg_val > 0 else 0
        
        return float(normalized_slope)
    
    def _detect_bb_squeeze(self, hist: pd.DataFrame) -> bool:
        """Detect Bollinger Band squeeze"""
        if len(hist) < 20:
            return False
        
        # Simple BB calculation
        close = hist['Close']
        bb_period = 20
        bb_std = 2
        
        sma = close.rolling(bb_period).mean()
        std = close.rolling(bb_period).std()
        
        upper_band = sma + (std * bb_std)
        lower_band = sma - (std * bb_std)
        
        # Current band width vs historical
        current_width = (upper_band.iloc[-1] - lower_band.iloc[-1]) / sma.iloc[-1]
        avg_width = ((upper_band - lower_band) / sma).rolling(50).mean().iloc[-1]
        
        # Squeeze when current width is significantly below average
        return current_width < avg_width * 0.8
    
    def get_watchlist_summary(self) -> Dict:
        """Get summary of watchlist capabilities"""
        return {
            'purpose': 'Identify stocks showing early pre-pump signals',
            'detection_focus': [
                'Volume accumulation patterns',
                'Price compression and coiling',
                'Technical setup formation',
                'Fundamental pump prerequisites'
            ],
            'early_indicators': [
                'Subtle volume increases (50-150%)',
                'Volatility compression',
                'Range contraction',
                'Moving average alignment',
                'RSI positioning (30-60)',
                'High short interest (15%+)',
                'Small float characteristics'
            ],
            'watchlist_tiers': {
                'tier_1': 'High priority - Strong early signals (60+ score)',
                'tier_2': 'Medium priority - Moderate signals (40-59 score)', 
                'tier_3': 'Low priority - Weak signals (25-39 score)',
                'monitor': 'Background monitoring (below 25 score)'
            },
            'update_frequency': 'Real-time analysis available',
            'cost': 'Free with Yahoo Finance data'
        }