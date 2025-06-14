"""
Options Flow Monitor - Enhanced Phase 1 Feature
Monitors unusual options activity that often precedes pump events
Addresses the backtesting recommendation for options flow monitoring
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass

@dataclass
class OptionsAlert:
    """Data class for options flow alerts"""
    symbol: str
    alert_type: str
    volume_ratio: float
    oi_ratio: float
    strike: float
    expiry: str
    option_type: str
    unusual_score: float
    description: str

class OptionsFlowMonitor:
    """Monitor unusual options activity for pump detection"""
    
    def __init__(self):
        self.volume_threshold = 5.0  # 5x average volume
        self.oi_threshold = 3.0      # 3x average open interest
        self.unusual_score_threshold = 70
        
        # Options activity patterns
        self.pump_patterns = {
            'gamma_squeeze': {
                'call_volume_spike': True,
                'otm_calls': True,
                'short_expiry': True,
                'score_weight': 30
            },
            'institutional_accumulation': {
                'large_block_trades': True,
                'itm_calls': True,
                'long_expiry': True,
                'score_weight': 25
            },
            'earnings_speculation': {
                'straddle_activity': True,
                'near_expiry': True,
                'high_iv': True,
                'score_weight': 20
            },
            'squeeze_setup': {
                'call_put_ratio': 'high',
                'otm_activity': True,
                'volume_surge': True,
                'score_weight': 35
            }
        }
    
    def scan_unusual_options_activity(self, symbols: List[str] = None) -> Dict:
        """Scan for unusual options activity across symbols"""
        try:
            if not symbols:
                symbols = self._get_active_symbols()
            
            unusual_activity = []
            alerts = []
            
            for symbol in symbols[:20]:  # Limit to 20 symbols for performance
                try:
                    activity = self._analyze_symbol_options(symbol)
                    if activity and activity['unusual_score'] >= self.unusual_score_threshold:
                        unusual_activity.append(activity)
                        
                        # Generate alerts for high-scoring activity
                        if activity['unusual_score'] >= 85:
                            alerts.extend(self._generate_options_alerts(symbol, activity))
                            
                except Exception as e:
                    logging.warning(f"Error analyzing options for {symbol}: {e}")
                    continue
            
            # Sort by unusual score
            unusual_activity.sort(key=lambda x: x['unusual_score'], reverse=True)
            
            return {
                'scan_timestamp': datetime.now().isoformat(),
                'symbols_scanned': len(symbols),
                'unusual_activity_count': len(unusual_activity),
                'high_priority_alerts': len([a for a in alerts if a.unusual_score >= 90]),
                'unusual_activity': unusual_activity[:15],  # Top 15
                'options_alerts': alerts,
                'flow_summary': self._create_flow_summary(unusual_activity),
                'gamma_squeeze_candidates': self._identify_gamma_squeeze_candidates(unusual_activity)
            }
            
        except Exception as e:
            logging.error(f"Error scanning options activity: {e}")
            return self._get_fallback_options_data()
    
    def _analyze_symbol_options(self, symbol: str) -> Optional[Dict]:
        """Analyze options activity for a specific symbol"""
        try:
            ticker = yf.Ticker(symbol)
            
            # Get stock data for context
            hist = ticker.history(period="1mo")
            if hist.empty:
                return None
            
            current_price = hist['Close'].iloc[-1]
            
            # Get options chain
            expiry_dates = ticker.options
            if not expiry_dates:
                return None
            
            # Analyze near-term options (next 2 expirations)
            analysis_results = []
            for expiry in expiry_dates[:2]:
                try:
                    options_chain = ticker.option_chain(expiry)
                    calls = options_chain.calls
                    puts = options_chain.puts
                    
                    if calls.empty and puts.empty:
                        continue
                    
                    # Analyze calls and puts
                    call_analysis = self._analyze_options_data(calls, current_price, 'call', expiry)
                    put_analysis = self._analyze_options_data(puts, current_price, 'put', expiry)
                    
                    analysis_results.append({
                        'expiry': expiry,
                        'calls': call_analysis,
                        'puts': put_analysis
                    })
                    
                except Exception as e:
                    logging.warning(f"Error analyzing options chain for {symbol} {expiry}: {e}")
                    continue
            
            if not analysis_results:
                return None
            
            # Calculate overall unusual score
            overall_score = self._calculate_unusual_score(symbol, analysis_results, current_price)
            
            return {
                'symbol': symbol,
                'current_price': round(current_price, 2),
                'unusual_score': round(overall_score, 1),
                'options_analysis': analysis_results,
                'flow_patterns': self._identify_flow_patterns(analysis_results),
                'pump_indicators': self._check_pump_indicators(analysis_results, overall_score),
                'recommendation': self._get_recommendation(overall_score)
            }
            
        except Exception as e:
            logging.error(f"Error analyzing options for {symbol}: {e}")
            return None
    
    def _analyze_options_data(self, options_df: pd.DataFrame, current_price: float, 
                            option_type: str, expiry: str) -> Dict:
        """Analyze options data for calls or puts"""
        try:
            if options_df.empty:
                return {'volume_analysis': {}, 'oi_analysis': {}, 'unusual_strikes': []}
            
            # Volume analysis
            total_volume = options_df['volume'].fillna(0).sum()
            avg_volume = options_df['volume'].fillna(0).mean()
            max_volume_strike = options_df.loc[options_df['volume'].idxmax(), 'strike'] if total_volume > 0 else None
            
            # Open interest analysis
            total_oi = options_df['openInterest'].fillna(0).sum()
            avg_oi = options_df['openInterest'].fillna(0).mean()
            max_oi_strike = options_df.loc[options_df['openInterest'].idxmax(), 'strike'] if total_oi > 0 else None
            
            # Identify unusual strikes
            unusual_strikes = []
            for _, option in options_df.iterrows():
                volume = option.get('volume', 0) or 0
                oi = option.get('openInterest', 0) or 0
                strike = option.get('strike', 0)
                
                # Check for unusual activity
                volume_ratio = volume / max(avg_volume, 1)
                oi_ratio = oi / max(avg_oi, 1)
                
                if volume_ratio >= self.volume_threshold or oi_ratio >= self.oi_threshold:
                    moneyness = self._calculate_moneyness(strike, current_price, option_type)
                    
                    unusual_strikes.append({
                        'strike': strike,
                        'volume': volume,
                        'volume_ratio': round(volume_ratio, 2),
                        'open_interest': oi,
                        'oi_ratio': round(oi_ratio, 2),
                        'moneyness': moneyness,
                        'bid': option.get('bid', 0),
                        'ask': option.get('ask', 0),
                        'last_price': option.get('lastPrice', 0),
                        'implied_volatility': option.get('impliedVolatility', 0)
                    })
            
            return {
                'total_volume': int(total_volume),
                'avg_volume': round(avg_volume, 2),
                'max_volume_strike': max_volume_strike,
                'total_oi': int(total_oi),
                'avg_oi': round(avg_oi, 2),
                'max_oi_strike': max_oi_strike,
                'unusual_strikes': sorted(unusual_strikes, key=lambda x: x['volume_ratio'], reverse=True)[:5],
                'expiry': expiry,
                'option_type': option_type
            }
            
        except Exception as e:
            logging.error(f"Error analyzing {option_type} options: {e}")
            return {'volume_analysis': {}, 'oi_analysis': {}, 'unusual_strikes': []}
    
    def _calculate_moneyness(self, strike: float, current_price: float, option_type: str) -> str:
        """Calculate option moneyness"""
        if option_type == 'call':
            if strike < current_price * 0.95:
                return 'ITM'
            elif strike > current_price * 1.05:
                return 'OTM'
            else:
                return 'ATM'
        else:  # put
            if strike > current_price * 1.05:
                return 'ITM'
            elif strike < current_price * 0.95:
                return 'OTM'
            else:
                return 'ATM'
    
    def _calculate_unusual_score(self, symbol: str, analysis_results: List[Dict], 
                                current_price: float) -> float:
        """Calculate overall unusual activity score"""
        try:
            score = 0
            max_score = 100
            
            for result in analysis_results:
                calls = result.get('calls', {})
                puts = result.get('puts', {})
                
                # Volume score (40 points max)
                call_volume = calls.get('total_volume', 0)
                put_volume = puts.get('total_volume', 0)
                total_volume = call_volume + put_volume
                
                if total_volume > 1000:
                    score += min(20, total_volume / 1000 * 5)
                
                # Unusual strikes score (30 points max)
                call_unusual = len(calls.get('unusual_strikes', []))
                put_unusual = len(puts.get('unusual_strikes', []))
                total_unusual = call_unusual + put_unusual
                
                score += min(15, total_unusual * 3)
                
                # Call/Put ratio score (15 points max)
                if put_volume > 0:
                    cp_ratio = call_volume / put_volume
                    if cp_ratio > 3:  # Bullish bias
                        score += 10
                    elif cp_ratio > 2:
                        score += 5
                
                # OTM activity score (15 points max)
                otm_activity = 0
                for strike_data in calls.get('unusual_strikes', []):
                    if strike_data['moneyness'] == 'OTM':
                        otm_activity += strike_data['volume_ratio']
                
                score += min(10, otm_activity / 5)
            
            return min(max_score, score)
            
        except Exception as e:
            logging.error(f"Error calculating unusual score for {symbol}: {e}")
            return 0
    
    def _identify_flow_patterns(self, analysis_results: List[Dict]) -> List[str]:
        """Identify specific flow patterns"""
        patterns = []
        
        try:
            for result in analysis_results:
                calls = result.get('calls', {})
                puts = result.get('puts', {})
                
                call_volume = calls.get('total_volume', 0)
                put_volume = puts.get('total_volume', 0)
                
                # Gamma squeeze pattern
                call_unusual = calls.get('unusual_strikes', [])
                otm_calls = [s for s in call_unusual if s['moneyness'] == 'OTM']
                
                if len(otm_calls) >= 2 and call_volume > put_volume * 2:
                    patterns.append('Gamma Squeeze Setup')
                
                # Heavy call buying
                if call_volume > 500 and call_volume > put_volume * 3:
                    patterns.append('Heavy Call Buying')
                
                # Straddle activity
                if abs(call_volume - put_volume) < call_volume * 0.3 and call_volume > 200:
                    patterns.append('Straddle Activity')
                
                # Large block trades
                large_blocks = [s for s in call_unusual + puts.get('unusual_strikes', []) 
                               if s['volume'] > 1000]
                if large_blocks:
                    patterns.append('Large Block Activity')
        
        except Exception as e:
            logging.error(f"Error identifying flow patterns: {e}")
        
        return list(set(patterns))
    
    def _check_pump_indicators(self, analysis_results: List[Dict], unusual_score: float) -> Dict:
        """Check for pump-specific indicators"""
        indicators = {
            'gamma_squeeze_risk': False,
            'institutional_activity': False,
            'retail_speculation': False,
            'short_squeeze_setup': False,
            'risk_level': 'Low'
        }
        
        try:
            total_call_volume = sum(r.get('calls', {}).get('total_volume', 0) for r in analysis_results)
            total_put_volume = sum(r.get('puts', {}).get('total_volume', 0) for r in analysis_results)
            
            # Gamma squeeze risk
            if unusual_score >= 80 and total_call_volume > total_put_volume * 3:
                indicators['gamma_squeeze_risk'] = True
                indicators['risk_level'] = 'High'
            
            # Institutional activity (large blocks)
            large_volume_strikes = 0
            for result in analysis_results:
                for option_type in ['calls', 'puts']:
                    unusual_strikes = result.get(option_type, {}).get('unusual_strikes', [])
                    large_volume_strikes += len([s for s in unusual_strikes if s['volume'] > 500])
            
            if large_volume_strikes >= 3:
                indicators['institutional_activity'] = True
            
            # Retail speculation (many small OTM calls)
            otm_call_strikes = 0
            for result in analysis_results:
                call_unusual = result.get('calls', {}).get('unusual_strikes', [])
                otm_call_strikes += len([s for s in call_unusual 
                                       if s['moneyness'] == 'OTM' and s['volume'] < 500])
            
            if otm_call_strikes >= 4:
                indicators['retail_speculation'] = True
            
            # Short squeeze setup
            if total_call_volume > 1000 and indicators['gamma_squeeze_risk']:
                indicators['short_squeeze_setup'] = True
                indicators['risk_level'] = 'Very High'
            
            # Set risk level
            if unusual_score >= 90:
                indicators['risk_level'] = 'Very High'
            elif unusual_score >= 75:
                indicators['risk_level'] = 'High'
            elif unusual_score >= 60:
                indicators['risk_level'] = 'Medium'
        
        except Exception as e:
            logging.error(f"Error checking pump indicators: {e}")
        
        return indicators
    
    def _get_recommendation(self, unusual_score: float) -> str:
        """Get recommendation based on unusual score"""
        if unusual_score >= 90:
            return 'STRONG BUY - High pump probability'
        elif unusual_score >= 80:
            return 'BUY - Significant unusual activity'
        elif unusual_score >= 70:
            return 'WATCH - Moderate unusual activity'
        elif unusual_score >= 60:
            return 'MONITOR - Some unusual activity'
        else:
            return 'NEUTRAL - No significant activity'
    
    def _generate_options_alerts(self, symbol: str, activity: Dict) -> List[OptionsAlert]:
        """Generate options flow alerts"""
        alerts = []
        
        try:
            unusual_score = activity['unusual_score']
            
            for analysis in activity['options_analysis']:
                expiry = analysis['expiry']
                
                # Check calls
                call_unusual = analysis.get('calls', {}).get('unusual_strikes', [])
                for strike_data in call_unusual:
                    if strike_data['volume_ratio'] >= self.volume_threshold:
                        alerts.append(OptionsAlert(
                            symbol=symbol,
                            alert_type='Unusual Call Volume',
                            volume_ratio=strike_data['volume_ratio'],
                            oi_ratio=strike_data['oi_ratio'],
                            strike=strike_data['strike'],
                            expiry=expiry,
                            option_type='call',
                            unusual_score=unusual_score,
                            description=f"Call volume {strike_data['volume_ratio']:.1f}x normal at ${strike_data['strike']} strike"
                        ))
                
                # Check puts
                put_unusual = analysis.get('puts', {}).get('unusual_strikes', [])
                for strike_data in put_unusual:
                    if strike_data['volume_ratio'] >= self.volume_threshold:
                        alerts.append(OptionsAlert(
                            symbol=symbol,
                            alert_type='Unusual Put Volume',
                            volume_ratio=strike_data['volume_ratio'],
                            oi_ratio=strike_data['oi_ratio'],
                            strike=strike_data['strike'],
                            expiry=expiry,
                            option_type='put',
                            unusual_score=unusual_score,
                            description=f"Put volume {strike_data['volume_ratio']:.1f}x normal at ${strike_data['strike']} strike"
                        ))
        
        except Exception as e:
            logging.error(f"Error generating alerts for {symbol}: {e}")
        
        return alerts
    
    def _create_flow_summary(self, unusual_activity: List[Dict]) -> Dict:
        """Create summary of options flow"""
        try:
            if not unusual_activity:
                return {}
            
            total_symbols = len(unusual_activity)
            high_risk = len([a for a in unusual_activity if a['unusual_score'] >= 85])
            gamma_candidates = len([a for a in unusual_activity 
                                  if 'Gamma Squeeze Setup' in a.get('flow_patterns', [])])
            
            avg_score = sum(a['unusual_score'] for a in unusual_activity) / total_symbols
            
            return {
                'total_symbols_with_activity': total_symbols,
                'high_risk_symbols': high_risk,
                'gamma_squeeze_candidates': gamma_candidates,
                'average_unusual_score': round(avg_score, 1),
                'top_symbol': unusual_activity[0]['symbol'] if unusual_activity else None,
                'top_score': unusual_activity[0]['unusual_score'] if unusual_activity else 0
            }
            
        except Exception as e:
            logging.error(f"Error creating flow summary: {e}")
            return {}
    
    def _identify_gamma_squeeze_candidates(self, unusual_activity: List[Dict]) -> List[Dict]:
        """Identify potential gamma squeeze candidates"""
        candidates = []
        
        try:
            for activity in unusual_activity:
                if 'Gamma Squeeze Setup' in activity.get('flow_patterns', []):
                    pump_indicators = activity.get('pump_indicators', {})
                    
                    candidates.append({
                        'symbol': activity['symbol'],
                        'unusual_score': activity['unusual_score'],
                        'gamma_risk': pump_indicators.get('gamma_squeeze_risk', False),
                        'risk_level': pump_indicators.get('risk_level', 'Low'),
                        'current_price': activity['current_price'],
                        'recommendation': activity['recommendation']
                    })
            
            return sorted(candidates, key=lambda x: x['unusual_score'], reverse=True)
            
        except Exception as e:
            logging.error(f"Error identifying gamma squeeze candidates: {e}")
            return []
    
    def _get_active_symbols(self) -> List[str]:
        """Get list of active symbols to monitor"""
        # Focus on our target range and commonly pumped sectors
        return [
            # High-volume biotech/pharma
            'NVAX', 'MRNA', 'GILD', 'SIGA', 'ACAD',
            # Meme stocks and squeeze candidates
            'GME', 'AMC', 'BBBY', 'CLOV', 'WKHS',
            # Small-cap growth
            'PLUG', 'CVNA', 'NKLA', 'RIDE', 'LCID',
            # Volatile tech
            'TSLA', 'RIVN', 'HOOD', 'COIN', 'SQ'
        ]
    
    def _get_fallback_options_data(self) -> Dict:
        """Provide fallback data when options data unavailable"""
        return {
            'scan_timestamp': datetime.now().isoformat(),
            'symbols_scanned': 0,
            'unusual_activity_count': 0,
            'high_priority_alerts': 0,
            'unusual_activity': [],
            'options_alerts': [],
            'flow_summary': {},
            'gamma_squeeze_candidates': [],
            'note': 'Options data unavailable - requires real-time options feed'
        }
    
    def analyze_single_symbol_options(self, symbol: str) -> Dict:
        """Analyze options activity for a single symbol"""
        try:
            activity = self._analyze_symbol_options(symbol)
            if not activity:
                return {
                    'symbol': symbol,
                    'error': 'No options data available',
                    'unusual_score': 0
                }
            
            # Generate alerts
            alerts = self._generate_options_alerts(symbol, activity)
            
            # Add alerts to response
            activity['alerts'] = [
                {
                    'alert_type': alert.alert_type,
                    'volume_ratio': alert.volume_ratio,
                    'strike': alert.strike,
                    'expiry': alert.expiry,
                    'description': alert.description
                }
                for alert in alerts
            ]
            
            return activity
            
        except Exception as e:
            logging.error(f"Error analyzing options for {symbol}: {e}")
            return {'symbol': symbol, 'error': str(e)}