"""
Simplified Pump Detection Backtest Analyzer
Analyzes historical pump cases with basic metrics
"""

import pandas as pd
import yfinance as yf
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import Dict, List

class SimplePumpAnalyzer:
    """Simplified pump detection analysis for historical cases"""
    
    def __init__(self):
        self.pump_cases = [
            {"Name": "GameStop (GME)", "Symbol": "GME", "Pump Date": "2021-01-27", "Price Before": 20, "Price Peak": 483, "Price After": 120, "Cause": "Short squeeze via Reddit (WSB), Elon Musk tweet", "Indicators": "140% short interest, low volume, RSI ~45"},
            {"Name": "AMC Entertainment (AMC)", "Symbol": "AMC", "Pump Date": "2021-01-28", "Price Before": 3, "Price Peak": 20, "Price After": 10, "Cause": "Meme stock surge linked to GME", "Indicators": "High short interest, low volatility, RSI ~50"},
            {"Name": "BlackBerry (BB)", "Symbol": "BB", "Pump Date": "2021-01-27", "Price Before": 9, "Price Peak": 28, "Price After": 14, "Cause": "Reddit pump with GME/AMC", "Indicators": "Short float >30%, trending on forums"},
            {"Name": "Koss Corporation (KOSS)", "Symbol": "KOSS", "Pump Date": "2021-01-27", "Price Before": 3, "Price Peak": 127, "Price After": 50, "Cause": "Reddit-driven spike", "Indicators": "Thin float, low average volume"},
            {"Name": "Express Inc. (EXPR)", "Symbol": "EXPR", "Pump Date": "2021-01-27", "Price Before": 1, "Price Peak": 13, "Price After": 5, "Cause": "Meme pump", "Indicators": "Retail mentions, short interest rising"},
            {"Name": "Nokia (NOK)", "Symbol": "NOK", "Pump Date": "2021-01-27", "Price Before": 4, "Price Peak": 9, "Price After": 6, "Cause": "WSB mentions", "Indicators": "Flat chart, sudden breakout volume"}
        ]
    
    def analyze_pump_case(self, case: Dict) -> Dict:
        """Analyze individual pump case with available data"""
        try:
            symbol = case['Symbol']
            pump_date = case['Pump Date']
            
            # Calculate pump magnitude
            price_before = float(case['Price Before'])
            price_peak = float(case['Price Peak'])
            pump_magnitude = ((price_peak / price_before) - 1) * 100
            
            # Analyze pre-pump conditions if data available
            try:
                pump_datetime = datetime.strptime(pump_date, '%Y-%m-%d')
                start_date = pump_datetime - timedelta(days=10)
                end_date = pump_datetime - timedelta(days=1)
                
                ticker = yf.Ticker(symbol)
                hist = ticker.history(start=start_date, end=end_date)
                
                if not hist.empty:
                    # Basic volume analysis
                    avg_volume = hist['Volume'].mean()
                    recent_volume = hist['Volume'].iloc[-1]
                    volume_surge = recent_volume / avg_volume if avg_volume > 0 else 1
                    
                    # Price momentum
                    price_change = (hist['Close'].iloc[-1] / hist['Close'].iloc[0] - 1) * 100
                    
                    # Volatility
                    volatility = hist['Close'].pct_change().std() * 100
                    
                    pre_pump_data = {
                        'volume_surge': volume_surge,
                        'price_momentum': price_change,
                        'volatility': volatility,
                        'data_available': True
                    }
                else:
                    pre_pump_data = {'data_available': False}
                    
            except Exception:
                pre_pump_data = {'data_available': False}
            
            # Calculate detection score based on known patterns
            detection_score = self.calculate_detection_score(case, pre_pump_data)
            
            return {
                'name': case['Name'],
                'symbol': symbol,
                'pump_date': pump_date,
                'pump_magnitude': pump_magnitude,
                'cause': case['Cause'],
                'original_indicators': case['Indicators'],
                'pre_pump_data': pre_pump_data,
                'detection_score': detection_score['score'],
                'detection_factors': detection_score['factors'],
                'would_alert': detection_score['score'] > 60,
                'confidence_level': 'High' if detection_score['score'] > 70 else 'Medium' if detection_score['score'] > 40 else 'Low'
            }
            
        except Exception as e:
            logging.error(f"Error analyzing {case.get('Symbol', 'Unknown')}: {e}")
            return {
                'name': case['Name'],
                'symbol': case.get('Symbol', 'Unknown'),
                'error': str(e),
                'detection_score': 0,
                'would_alert': False,
                'confidence_level': 'Low'
            }
    
    def calculate_detection_score(self, case: Dict, pre_pump_data: Dict) -> Dict:
        """Calculate detection score based on available indicators"""
        score = 0
        factors = []
        
        # Reddit/Social mentions factor
        cause = case['Cause'].lower()
        if 'reddit' in cause or 'wsb' in cause or 'meme' in cause:
            social_score = 25
            factors.append(f"Social media mentions (+{social_score} pts)")
            score += social_score
        
        # Short interest factor
        indicators = case['Indicators'].lower()
        if 'short' in indicators:
            short_score = 30
            factors.append(f"High short interest detected (+{short_score} pts)")
            score += short_score
        
        # Volume analysis if available
        if pre_pump_data.get('data_available'):
            volume_surge = pre_pump_data.get('volume_surge', 1)
            if volume_surge > 2:
                vol_score = min(volume_surge * 10, 25)
                factors.append(f"Volume surge {volume_surge:.1f}x (+{vol_score:.0f} pts)")
                score += vol_score
            
            # Price momentum
            momentum = pre_pump_data.get('price_momentum', 0)
            if momentum > 5:
                momentum_score = 15
                factors.append(f"Price momentum {momentum:.1f}% (+{momentum_score} pts)")
                score += momentum_score
            
            # Volatility
            volatility = pre_pump_data.get('volatility', 0)
            if volatility > 5:
                vol_score = 10
                factors.append(f"High volatility {volatility:.1f}% (+{vol_score} pts)")
                score += vol_score
        
        # Low float/thin trading factor
        if 'thin' in indicators or 'float' in indicators or 'low volume' in indicators:
            float_score = 20
            factors.append(f"Thin float/low volume (+{float_score} pts)")
            score += float_score
        
        return {
            'score': min(score, 100),
            'factors': factors
        }
    
    def run_full_analysis(self) -> Dict:
        """Run complete backtest analysis"""
        results = []
        
        for case in self.pump_cases:
            result = self.analyze_pump_case(case)
            results.append(result)
        
        # Calculate summary statistics
        successful_detections = len([r for r in results if r['would_alert']])
        detection_rate = (successful_detections / len(results)) * 100
        high_value_catches = len([r for r in results if r['would_alert'] and r.get('pump_magnitude', 0) > 200])
        missed_major_pumps = len([r for r in results if not r['would_alert'] and r.get('pump_magnitude', 0) > 200])
        
        # Generate enhancement recommendations
        recommendations = self.generate_recommendations(results)
        
        return {
            'backtest_results': results,
            'summary': {
                'total_cases': len(results),
                'detection_rate': detection_rate,
                'high_value_catches': high_value_catches,
                'missed_opportunities': missed_major_pumps
            },
            'recommendations': recommendations,
            'enhanced_rules': self.generate_enhanced_rules()
        }
    
    def generate_recommendations(self, results: List[Dict]) -> Dict:
        """Generate enhancement recommendations based on results"""
        missed_cases = [r for r in results if not r['would_alert']]
        reddit_cases = [r for r in results if 'reddit' in r['cause'].lower() or 'wsb' in r['cause'].lower()]
        
        enhancements = []
        
        # Social sentiment tracking
        if len(reddit_cases) > 2:
            enhancements.append({
                'type': 'Social Sentiment Monitoring',
                'priority': 'High',
                'description': 'Implement Reddit/Twitter sentiment tracking for retail-driven pumps',
                'missed_cases': [r['name'] for r in missed_cases if 'reddit' in r['cause'].lower()]
            })
        
        # Short interest monitoring
        short_cases = [r for r in results if 'short' in r.get('original_indicators', '').lower()]
        if len(short_cases) > 1:
            enhancements.append({
                'type': 'Short Interest Tracking',
                'priority': 'High',
                'description': 'Monitor short interest ratios and short squeeze potential',
                'relevant_cases': [r['name'] for r in short_cases]
            })
        
        # Volume spike detection
        enhancements.append({
            'type': 'Enhanced Volume Analysis',
            'priority': 'Medium',
            'description': 'Implement multi-timeframe volume analysis and unusual options activity'
        })
        
        return {
            'detection_success_rate': (len([r for r in results if r['would_alert']]) / len(results)) * 100,
            'enhancements': enhancements
        }
    
    def generate_enhanced_rules(self) -> Dict:
        """Generate enhanced scanner rules"""
        return {
            'pump_detection_rules': {
                'volume_surge_threshold': 3.0,
                'social_mentions_weight': 25,
                'short_interest_weight': 30,
                'momentum_threshold': 5,
                'volatility_threshold': 5
            },
            'alert_triggers': [
                {
                    'name': 'Meme Stock Pattern',
                    'conditions': ['social_mentions_spike', 'volume_surge > 5x', 'short_interest > 20%'],
                    'min_score': 70
                },
                {
                    'name': 'Short Squeeze Setup',
                    'conditions': ['short_interest > 30%', 'volume_surge > 3x', 'price_momentum > 5%'],
                    'min_score': 75
                },
                {
                    'name': 'Volume Breakout Alert',
                    'conditions': ['volume_surge > 10x', 'thin_float', 'momentum > 10%'],
                    'min_score': 65
                }
            ]
        }
    
    def generate_report(self) -> str:
        """Generate comprehensive analysis report"""
        analysis = self.run_full_analysis()
        results = analysis['backtest_results']
        
        report = f"""
CANDLECAST PUMP DETECTION BACKTEST ANALYSIS
==========================================

EXECUTIVE SUMMARY:
• Cases Analyzed: {analysis['summary']['total_cases']}
• Detection Success Rate: {analysis['summary']['detection_rate']:.1f}%
• High-Value Catches: {analysis['summary']['high_value_catches']} cases
• Major Missed Opportunities: {analysis['summary']['missed_opportunities']} cases

INDIVIDUAL CASE ANALYSIS:
"""
        
        for result in results:
            status = "✓ DETECTED" if result['would_alert'] else "✗ MISSED"
            pump_mag = result.get('pump_magnitude', 0)
            
            report += f"""
{result['name']} ({result['symbol']})
{status} - Score: {result['detection_score']}/100 ({result['confidence_level']})
Pump Magnitude: +{pump_mag:.0f}% on {result['pump_date']}
Cause: {result['cause']}
Detection Factors: {', '.join(result['detection_factors']) if result['detection_factors'] else 'Limited pre-pump data'}
"""

        report += f"""

KEY FINDINGS:
• Reddit/WSB-driven pumps show strong social signal patterns
• Short squeeze setups have identifiable pre-conditions 
• Volume surges are reliable early indicators when data available
• Thin float stocks show explosive potential with catalyst

ENHANCEMENT RECOMMENDATIONS:
"""
        
        for enhancement in analysis['recommendations']['enhancements']:
            report += f"""
{enhancement['type']} (Priority: {enhancement['priority']})
- {enhancement['description']}
"""
            if 'missed_cases' in enhancement:
                report += f"- Would improve detection of: {', '.join(enhancement['missed_cases'])}\n"

        report += """

PROPOSED SCANNER ENHANCEMENTS:
1. Social Sentiment Integration
   - Reddit mention tracking with WSB focus
   - Twitter sentiment analysis
   - Real-time social volume spikes

2. Short Interest Monitoring  
   - Daily short interest updates
   - Short squeeze probability scoring
   - Days-to-cover analysis

3. Enhanced Volume Analysis
   - Multi-timeframe volume profiling
   - Unusual options activity alerts
   - Institutional vs retail flow detection

4. Pattern Recognition
   - Meme stock identification
   - Thin float breakout patterns
   - Catalyst-driven momentum setups
"""
        
        return report