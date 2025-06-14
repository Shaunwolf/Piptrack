"""
Short Interest Monitor for Pump Detection
Phase 1 Enhancement: Basic short interest monitoring and squeeze alerts
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
import requests

class ShortInterestMonitor:
    """Monitor short interest data for squeeze potential"""
    
    def __init__(self):
        # Short squeeze thresholds
        self.high_short_interest = 20.0  # 20%+ of float
        self.extreme_short_interest = 40.0  # 40%+ squeeze territory
        self.high_days_to_cover = 7.0  # 7+ days to cover
        self.squeeze_threshold = 15.0  # Combined squeeze score
        
        # Data sources (free alternatives)
        self.data_sources = {
            'yahoo_finance': True,
            'finviz_scraping': True,
            'sec_filings': True
        }
    
    def analyze_short_squeeze_potential(self, symbol: str) -> Dict:
        """Comprehensive short squeeze analysis"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Get basic short data from Yahoo Finance
            short_data = self._get_short_interest_data(ticker, info)
            
            # Calculate squeeze metrics
            squeeze_metrics = self._calculate_squeeze_metrics(short_data, symbol)
            
            # Analyze recent price/volume action
            price_action = self._analyze_price_action_for_squeeze(ticker)
            
            # Calculate overall squeeze probability
            squeeze_probability = self._calculate_squeeze_probability(
                short_data, squeeze_metrics, price_action
            )
            
            return {
                'symbol': symbol,
                'short_data': short_data,
                'squeeze_metrics': squeeze_metrics,
                'price_action': price_action,
                'squeeze_probability': squeeze_probability,
                'analysis_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logging.error(f"Error analyzing short squeeze for {symbol}: {e}")
            return {'error': str(e)}
    
    def _get_short_interest_data(self, ticker, info: Dict) -> Dict:
        """Extract short interest data from available sources"""
        short_data = {}
        
        # From Yahoo Finance info
        short_data['shares_outstanding'] = info.get('sharesOutstanding', 0)
        short_data['float_shares'] = info.get('floatShares', info.get('sharesOutstanding', 0))
        short_data['shares_short'] = info.get('sharesShort', 0)
        short_data['short_ratio'] = info.get('shortRatio', 0)
        short_data['short_percent_float'] = info.get('shortPercentOfFloat', 0)
        short_data['shares_short_prior_month'] = info.get('sharesShortPriorMonth', 0)
        
        # Calculate additional metrics
        if short_data['float_shares'] > 0:
            short_data['short_interest_ratio'] = (
                short_data['shares_short'] / short_data['float_shares'] * 100
            )
        else:
            short_data['short_interest_ratio'] = 0
        
        # Short interest change
        if short_data['shares_short_prior_month'] > 0:
            short_data['short_change_pct'] = (
                (short_data['shares_short'] - short_data['shares_short_prior_month']) 
                / short_data['shares_short_prior_month'] * 100
            )
        else:
            short_data['short_change_pct'] = 0
        
        # Get average volume for days-to-cover calculation
        hist = ticker.history(period='3mo')
        if not hist.empty:
            short_data['avg_volume_10d'] = hist['Volume'][-10:].mean()
            short_data['avg_volume_30d'] = hist['Volume'][-30:].mean()
            
            # Days to cover calculation
            if short_data['avg_volume_10d'] > 0:
                short_data['days_to_cover'] = short_data['shares_short'] / short_data['avg_volume_10d']
            else:
                short_data['days_to_cover'] = 0
        else:
            short_data['avg_volume_10d'] = 0
            short_data['avg_volume_30d'] = 0
            short_data['days_to_cover'] = 0
        
        return {k: float(v) if isinstance(v, (int, float)) else v for k, v in short_data.items()}
    
    def _calculate_squeeze_metrics(self, short_data: Dict, symbol: str) -> Dict:
        """Calculate squeeze-specific metrics"""
        metrics = {}
        
        # Short interest classification
        short_ratio = short_data.get('short_interest_ratio', 0)
        if short_ratio >= self.extreme_short_interest:
            metrics['short_interest_level'] = 'Extreme'
            metrics['short_interest_score'] = 100
        elif short_ratio >= self.high_short_interest:
            metrics['short_interest_level'] = 'High'
            metrics['short_interest_score'] = 75
        elif short_ratio >= 10:
            metrics['short_interest_level'] = 'Moderate'
            metrics['short_interest_score'] = 50
        else:
            metrics['short_interest_level'] = 'Low'
            metrics['short_interest_score'] = 25
        
        # Days to cover analysis
        days_to_cover = short_data.get('days_to_cover', 0)
        if days_to_cover >= self.high_days_to_cover:
            metrics['days_to_cover_level'] = 'High'
            metrics['days_to_cover_score'] = 100
        elif days_to_cover >= 3:
            metrics['days_to_cover_level'] = 'Moderate'
            metrics['days_to_cover_score'] = 60
        else:
            metrics['days_to_cover_level'] = 'Low'
            metrics['days_to_cover_score'] = 20
        
        # Short interest trend
        short_change = short_data.get('short_change_pct', 0)
        if short_change > 10:
            metrics['short_trend'] = 'Increasing'
            metrics['short_trend_score'] = 80
        elif short_change > 0:
            metrics['short_trend'] = 'Slightly Up'
            metrics['short_trend_score'] = 60
        elif short_change < -10:
            metrics['short_trend'] = 'Decreasing'
            metrics['short_trend_score'] = 40
        else:
            metrics['short_trend'] = 'Stable'
            metrics['short_trend_score'] = 50
        
        # Float size factor (smaller float = higher squeeze potential)
        float_shares = short_data.get('float_shares', 0)
        if float_shares < 50_000_000:  # Under 50M shares
            metrics['float_size_factor'] = 'Small'
            metrics['float_score'] = 80
        elif float_shares < 200_000_000:  # Under 200M shares
            metrics['float_size_factor'] = 'Medium'
            metrics['float_score'] = 60
        else:
            metrics['float_size_factor'] = 'Large'
            metrics['float_score'] = 30
        
        return metrics
    
    def _analyze_price_action_for_squeeze(self, ticker) -> Dict:
        """Analyze price action indicators for squeeze setup"""
        try:
            hist = ticker.history(period='3mo')
            if hist.empty:
                return {}
            
            current_price = hist['Close'].iloc[-1]
            volume_recent = hist['Volume'][-10:].mean()
            volume_baseline = hist['Volume'][-30:-10].mean()
            
            # Volume surge analysis
            volume_surge_ratio = volume_recent / volume_baseline if volume_baseline > 0 else 1
            
            # Price momentum
            price_1d = (hist['Close'].iloc[-1] / hist['Close'].iloc[-2] - 1) * 100
            price_1w = (hist['Close'].iloc[-1] / hist['Close'].iloc[-8] - 1) * 100 if len(hist) >= 8 else 0
            price_1m = (hist['Close'].iloc[-1] / hist['Close'].iloc[-22] - 1) * 100 if len(hist) >= 22 else 0
            
            # Support/resistance levels
            high_52w = hist['High'].max()
            low_52w = hist['Low'].min()
            price_from_low = (current_price - low_52w) / low_52w * 100
            price_from_high = (high_52w - current_price) / high_52w * 100
            
            # Volatility analysis
            returns = hist['Close'].pct_change()
            volatility = returns.std() * np.sqrt(252) * 100  # Annualized volatility
            
            return {
                'current_price': float(current_price),
                'volume_surge_ratio': float(volume_surge_ratio),
                'price_change_1d': float(price_1d),
                'price_change_1w': float(price_1w),
                'price_change_1m': float(price_1m),
                'price_from_52w_low': float(price_from_low),
                'price_from_52w_high': float(price_from_high),
                'volatility_annual': float(volatility),
                'high_52w': float(high_52w),
                'low_52w': float(low_52w)
            }
            
        except Exception as e:
            logging.error(f"Error analyzing price action: {e}")
            return {}
    
    def _calculate_squeeze_probability(self, short_data: Dict, squeeze_metrics: Dict, 
                                     price_action: Dict) -> Dict:
        """Calculate overall short squeeze probability"""
        score = 0
        factors = []
        
        # Short interest scoring (0-40 points)
        short_score = squeeze_metrics.get('short_interest_score', 0)
        score += short_score * 0.4
        if short_score >= 75:
            factors.append(f"High short interest ({short_data.get('short_interest_ratio', 0):.1f}%)")
        
        # Days to cover scoring (0-25 points)
        days_score = squeeze_metrics.get('days_to_cover_score', 0)
        score += days_score * 0.25
        if days_score >= 60:
            factors.append(f"High days to cover ({short_data.get('days_to_cover', 0):.1f} days)")
        
        # Volume surge scoring (0-20 points)
        volume_ratio = price_action.get('volume_surge_ratio', 1)
        if volume_ratio >= 3:
            volume_score = 20
            factors.append(f"Volume surge {volume_ratio:.1f}x")
        elif volume_ratio >= 2:
            volume_score = 12
            factors.append(f"Elevated volume {volume_ratio:.1f}x")
        else:
            volume_score = 0
        score += volume_score
        
        # Price momentum scoring (0-15 points)
        price_1d = price_action.get('price_change_1d', 0)
        if price_1d > 5:
            momentum_score = 15
            factors.append(f"Strong upward momentum (+{price_1d:.1f}%)")
        elif price_1d > 2:
            momentum_score = 8
            factors.append(f"Positive momentum (+{price_1d:.1f}%)")
        else:
            momentum_score = 0
        score += momentum_score
        
        # Float size bonus (0-10 points)
        float_score = squeeze_metrics.get('float_score', 0)
        if float_score >= 80:
            score += 10
            factors.append("Small float size")
        elif float_score >= 60:
            score += 5
        
        # Determine risk level
        if score >= 80:
            risk_level = 'Very High'
        elif score >= 60:
            risk_level = 'High'
        elif score >= 40:
            risk_level = 'Moderate'
        elif score >= 20:
            risk_level = 'Low'
        else:
            risk_level = 'Very Low'
        
        return {
            'squeeze_score': min(100, score),
            'risk_level': risk_level,
            'key_factors': factors,
            'confidence': 'High' if len(factors) >= 3 else 'Medium' if len(factors) >= 2 else 'Low'
        }
    
    def scan_for_squeeze_candidates(self, symbols: List[str]) -> List[Dict]:
        """Scan multiple symbols for short squeeze potential"""
        candidates = []
        
        for symbol in symbols:
            try:
                analysis = self.analyze_short_squeeze_potential(symbol)
                
                if 'error' not in analysis:
                    squeeze_prob = analysis.get('squeeze_probability', {})
                    if squeeze_prob.get('squeeze_score', 0) >= 40:  # Minimum threshold
                        candidates.append({
                            'symbol': symbol,
                            'squeeze_score': squeeze_prob.get('squeeze_score', 0),
                            'risk_level': squeeze_prob.get('risk_level', 'Unknown'),
                            'key_factors': squeeze_prob.get('key_factors', []),
                            'short_interest': analysis.get('short_data', {}).get('short_interest_ratio', 0),
                            'days_to_cover': analysis.get('short_data', {}).get('days_to_cover', 0)
                        })
                        
            except Exception as e:
                logging.error(f"Error scanning {symbol} for squeeze: {e}")
                continue
        
        # Sort by squeeze score
        candidates.sort(key=lambda x: x['squeeze_score'], reverse=True)
        return candidates
    
    def get_squeeze_alerts(self, symbol: str) -> List[Dict]:
        """Generate short squeeze alerts"""
        analysis = self.analyze_short_squeeze_potential(symbol)
        
        if 'error' in analysis:
            return []
        
        alerts = []
        short_data = analysis.get('short_data', {})
        squeeze_prob = analysis.get('squeeze_probability', {})
        
        # High squeeze probability alert
        if squeeze_prob.get('squeeze_score', 0) >= 70:
            alerts.append({
                'type': 'HIGH_SQUEEZE_RISK',
                'message': f"{symbol}: High short squeeze probability ({squeeze_prob['squeeze_score']:.0f}/100)",
                'urgency': 'HIGH',
                'factors': squeeze_prob.get('key_factors', [])
            })
        
        # Extreme short interest alert
        if short_data.get('short_interest_ratio', 0) >= self.extreme_short_interest:
            alerts.append({
                'type': 'EXTREME_SHORT_INTEREST',
                'message': f"{symbol}: Extreme short interest ({short_data['short_interest_ratio']:.1f}%)",
                'urgency': 'HIGH'
            })
        
        # High days to cover alert
        if short_data.get('days_to_cover', 0) >= self.high_days_to_cover:
            alerts.append({
                'type': 'HIGH_DAYS_TO_COVER',
                'message': f"{symbol}: {short_data['days_to_cover']:.1f} days to cover shorts",
                'urgency': 'MEDIUM'
            })
        
        # Short interest increase alert
        if short_data.get('short_change_pct', 0) > 15:
            alerts.append({
                'type': 'SHORT_INTEREST_INCREASE',
                'message': f"{symbol}: Short interest up {short_data['short_change_pct']:.1f}%",
                'urgency': 'MEDIUM'
            })
        
        return alerts
    
    def get_free_short_data_summary(self) -> Dict:
        """Summary of available free short interest data sources"""
        return {
            'data_sources': {
                'yahoo_finance': {
                    'available': True,
                    'fields': ['sharesShort', 'shortRatio', 'shortPercentOfFloat'],
                    'update_frequency': 'Bi-monthly',
                    'cost': 'Free'
                },
                'finviz_screening': {
                    'available': True,
                    'fields': ['Short Float %', 'Float'],
                    'update_frequency': 'Daily',
                    'cost': 'Free'
                },
                'sec_filings': {
                    'available': True,
                    'fields': ['Institutional ownership changes'],
                    'update_frequency': 'Quarterly',
                    'cost': 'Free'
                }
            },
            'limitations': [
                'Data delay: 2-4 weeks for official short interest',
                'No real-time short availability tracking',
                'Limited historical short interest data',
                'No borrow rate information'
            ],
            'upgrade_benefits': {
                'real_time_data': 'Daily short interest estimates',
                'borrow_rates': 'Cost to borrow shares data',
                'short_availability': 'Hard-to-borrow alerts',
                'historical_data': '5+ years of short interest history'
            }
        }