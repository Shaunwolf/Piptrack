"""
Historical Pump Backtest Analyzer
Analyzes how CandleCast would have detected historical pump scenarios
"""

import pandas as pd
import yfinance as yf
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Tuple
import ta
from confidence_scorer import ConfidenceScorer
from stock_scanner import StockScanner

class PumpBacktestAnalyzer:
    """Backtests pump detection capabilities against historical cases"""
    
    def __init__(self):
        self.confidence_scorer = ConfidenceScorer()
        self.stock_scanner = StockScanner()
        self.pump_cases = []
        self.analysis_results = []
        
    def load_pump_cases(self, csv_path: str = None) -> List[Dict]:
        """Load historical pump cases from CSV"""
        if csv_path:
            df = pd.read_csv(csv_path)
        else:
            # Use the provided data
            data = [
                {"Name": "GameStop (GME)", "Symbol": "GME", "Pump Date": "2021-01-27", "Price Before": 20, "Price Peak": 483, "Price After": 120, "Cause": "Short squeeze via Reddit (WSB), Elon Musk tweet", "Indicators": "140% short interest, low volume, RSI ~45"},
                {"Name": "AMC Entertainment (AMC)", "Symbol": "AMC", "Pump Date": "2021-01-28", "Price Before": 3, "Price Peak": 20, "Price After": 10, "Cause": "Meme stock surge linked to GME", "Indicators": "High short interest, low volatility, RSI ~50"},
                {"Name": "BlackBerry (BB)", "Symbol": "BB", "Pump Date": "2021-01-27", "Price Before": 9, "Price Peak": 28, "Price After": 14, "Cause": "Reddit pump with GME/AMC", "Indicators": "Short float >30%, trending on forums"},
                {"Name": "Koss Corporation (KOSS)", "Symbol": "KOSS", "Pump Date": "2021-01-27", "Price Before": 3, "Price Peak": 127, "Price After": 50, "Cause": "Reddit-driven spike", "Indicators": "Thin float, low average volume"},
                {"Name": "Express Inc. (EXPR)", "Symbol": "EXPR", "Pump Date": "2021-01-27", "Price Before": 1, "Price Peak": 13, "Price After": 5, "Cause": "Meme pump", "Indicators": "Retail mentions, short interest rising"},
                {"Name": "Bed Bath & Beyond (BBBY)", "Symbol": "BBBY", "Pump Date": "2021-01-27", "Price Before": 17, "Price Peak": 53, "Price After": 30, "Cause": "Meme stock rally", "Indicators": "High retail chatter, RSI ~60"},
                {"Name": "Virgin Galactic (SPCE)", "Symbol": "SPCE", "Pump Date": "2021-01-26", "Price Before": 23, "Price Peak": 60, "Price After": 45, "Cause": "Meme surge + test flight news", "Indicators": "Volume rising, MACD bullish crossover"},
                {"Name": "Nokia (NOK)", "Symbol": "NOK", "Pump Date": "2021-01-27", "Price Before": 4, "Price Peak": 9, "Price After": 6, "Cause": "WSB mentions", "Indicators": "Flat chart, sudden breakout volume"},
                {"Name": "Rocket Companies (RKT)", "Symbol": "RKT", "Pump Date": "2021-03-02", "Price Before": 21, "Price Peak": 41, "Price After": 26, "Cause": "Reddit squeeze, low float", "Indicators": "Call option volume spike"},
                {"Name": "Volkswagen (VW)", "Symbol": "VOW.DE", "Pump Date": "2008-10-28", "Price Before": 200, "Price Peak": 1000, "Price After": 400, "Cause": "Porsche takeover attempt", "Indicators": "Heavy institutional shorts"}
            ]
            df = pd.DataFrame(data)
        
        self.pump_cases = df.to_dict('records')
        return self.pump_cases
    
    def analyze_pre_pump_conditions(self, symbol: str, pump_date: str, days_before: int = 7) -> Dict:
        """Analyze stock conditions before pump occurred"""
        try:
            pump_datetime = datetime.strptime(pump_date, '%Y-%m-%d')
            start_date = pump_datetime - timedelta(days=days_before + 5)  # Extra buffer for indicators
            end_date = pump_datetime - timedelta(days=1)  # Day before pump
            
            # Fetch historical data
            ticker = yf.Ticker(symbol)
            hist = ticker.history(start=start_date, end=end_date)
            
            if hist.empty:
                return {"error": f"No data available for {symbol} around {pump_date}"}
            
            # Calculate technical indicators on pre-pump data
            last_price = hist['Close'].iloc[-1]
            volume_avg = hist['Volume'].rolling(5).mean().iloc[-1]
            recent_volume = hist['Volume'].iloc[-1]
            volume_surge = recent_volume / volume_avg if volume_avg > 0 else 1
            
            # RSI calculation
            rsi_series = ta.momentum.RSIIndicator(hist['Close']).rsi()
            rsi = rsi_series.iloc[-1] if not rsi_series.empty else 50
            
            # MACD
            macd = ta.trend.MACD(hist['Close'])
            macd_line = macd.macd().iloc[-1] if not macd.macd().empty else 0
            macd_signal = macd.macd_signal().iloc[-1] if not macd.macd_signal().empty else 0
            macd_histogram = macd.macd_diff().iloc[-1] if not macd.macd_diff().empty else 0
            
            # Bollinger Bands
            bb = ta.volatility.BollingerBands(hist['Close'])
            bb_upper = bb.bollinger_hband().iloc[-1] if not bb.bollinger_hband().empty else last_price * 1.02
            bb_lower = bb.bollinger_lband().iloc[-1] if not bb.bollinger_lband().empty else last_price * 0.98
            bb_position = (last_price - bb_lower) / (bb_upper - bb_lower) * 100
            
            # Price momentum
            price_change_1d = (hist['Close'].iloc[-1] / hist['Close'].iloc[-2] - 1) * 100
            price_change_5d = (hist['Close'].iloc[-1] / hist['Close'].iloc[-6] - 1) * 100 if len(hist) >= 6 else 0
            
            # Volatility
            volatility = hist['Close'].pct_change().std() * 100
            
            return {
                'symbol': symbol,
                'analysis_date': end_date.strftime('%Y-%m-%d'),
                'price': last_price,
                'volume_surge': volume_surge,
                'rsi': rsi,
                'macd_bullish': macd_line > macd_signal,
                'macd_histogram': macd_histogram,
                'bb_position': bb_position,
                'price_change_1d': price_change_1d,
                'price_change_5d': price_change_5d,
                'volatility': volatility,
                'volume_avg': volume_avg,
                'recent_volume': recent_volume
            }
            
        except Exception as e:
            logging.error(f"Error analyzing {symbol}: {e}")
            return {"error": str(e)}
    
    def calculate_pump_detection_score(self, pre_pump_data: Dict) -> Dict:
        """Calculate how likely our system would have detected this pump"""
        if 'error' in pre_pump_data:
            return {"detection_score": 0, "factors": [], "error": pre_pump_data['error']}
        
        detection_factors = []
        score = 0
        
        # Volume surge factor (high weight)
        volume_score = min(pre_pump_data['volume_surge'] * 20, 40)  # Cap at 40 points
        if pre_pump_data['volume_surge'] > 2:
            detection_factors.append(f"Volume surge {pre_pump_data['volume_surge']:.1f}x (+{volume_score:.0f} pts)")
            score += volume_score
        
        # RSI oversold condition
        if pre_pump_data['rsi'] < 35:
            rsi_score = 20
            detection_factors.append(f"RSI oversold at {pre_pump_data['rsi']:.1f} (+{rsi_score} pts)")
            score += rsi_score
        elif pre_pump_data['rsi'] < 50:
            rsi_score = 10
            detection_factors.append(f"RSI neutral at {pre_pump_data['rsi']:.1f} (+{rsi_score} pts)")
            score += rsi_score
        
        # MACD bullish crossover
        if pre_pump_data['macd_bullish'] and pre_pump_data['macd_histogram'] > 0:
            macd_score = 15
            detection_factors.append(f"MACD bullish crossover (+{macd_score} pts)")
            score += macd_score
        
        # Bollinger Band squeeze or breakout
        if pre_pump_data['bb_position'] < 20:
            bb_score = 15
            detection_factors.append(f"BB squeeze/oversold (+{bb_score} pts)")
            score += bb_score
        elif pre_pump_data['bb_position'] > 80:
            bb_score = 10
            detection_factors.append(f"BB breakout potential (+{bb_score} pts)")
            score += bb_score
        
        # Recent momentum
        if pre_pump_data['price_change_1d'] > 5:
            momentum_score = 15
            detection_factors.append(f"1-day momentum {pre_pump_data['price_change_1d']:.1f}% (+{momentum_score} pts)")
            score += momentum_score
        
        # High volatility (indicates potential)
        if pre_pump_data['volatility'] > 5:
            vol_score = 10
            detection_factors.append(f"High volatility {pre_pump_data['volatility']:.1f}% (+{vol_score} pts)")
            score += vol_score
        
        return {
            "detection_score": min(score, 100),  # Cap at 100
            "factors": detection_factors,
            "confidence_level": "High" if score > 70 else "Medium" if score > 40 else "Low"
        }
    
    def run_backtest_analysis(self) -> List[Dict]:
        """Run complete backtest analysis on all pump cases"""
        if not self.pump_cases:
            self.load_pump_cases()
        
        results = []
        
        for case in self.pump_cases:
            symbol = case.get('Symbol', case['Name'].split('(')[1].split(')')[0] if '(' in case['Name'] else case['Name'][:4].upper())
            
            # Analyze pre-pump conditions
            pre_pump_data = self.analyze_pre_pump_conditions(symbol, case['Pump Date'])
            
            # Calculate detection score
            detection_result = self.calculate_pump_detection_score(pre_pump_data)
            
            # Calculate actual pump performance
            price_before = float(case['Price Before'])
            price_peak = float(case['Price Peak'])
            pump_magnitude = ((price_peak / price_before) - 1) * 100
            
            result = {
                'name': case['Name'],
                'symbol': symbol,
                'pump_date': case['Pump Date'],
                'pump_magnitude': pump_magnitude,
                'cause': case['Cause'],
                'original_indicators': case['Indicators'],
                'pre_pump_analysis': pre_pump_data,
                'detection_score': detection_result['detection_score'],
                'detection_confidence': detection_result['confidence_level'],
                'detection_factors': detection_result['factors'],
                'would_alert': detection_result['detection_score'] > 60
            }
            
            results.append(result)
            
        self.analysis_results = results
        return results
    
    def generate_enhancement_recommendations(self) -> Dict:
        """Generate recommendations to enhance pump detection"""
        if not self.analysis_results:
            self.run_backtest_analysis()
        
        high_performers = [r for r in self.analysis_results if r['would_alert'] and r['pump_magnitude'] > 100]
        missed_opportunities = [r for r in self.analysis_results if not r['would_alert'] and r['pump_magnitude'] > 200]
        
        recommendations = {
            "detection_success_rate": len([r for r in self.analysis_results if r['would_alert']]) / len(self.analysis_results) * 100,
            "high_value_catches": len(high_performers),
            "missed_major_pumps": len(missed_opportunities),
            "enhancements": []
        }
        
        # Analyze missed opportunities for patterns
        if missed_opportunities:
            recommendations["enhancements"].append({
                "type": "Social Sentiment Monitoring",
                "priority": "High",
                "description": "Add Reddit/Twitter sentiment tracking for retail-driven pumps",
                "missed_cases": [r['name'] for r in missed_opportunities if 'Reddit' in r['cause'] or 'WSB' in r['cause']]
            })
        
        # Check for short interest patterns
        short_squeeze_cases = [r for r in self.analysis_results if 'short' in r['cause'].lower()]
        if short_squeeze_cases:
            recommendations["enhancements"].append({
                "type": "Short Interest Tracking",
                "priority": "High", 
                "description": "Monitor short interest ratios and short squeeze potential",
                "relevant_cases": [r['name'] for r in short_squeeze_cases]
            })
        
        # Volume spike enhancement
        avg_detection_score = np.mean([r['detection_score'] for r in self.analysis_results])
        if avg_detection_score < 70:
            recommendations["enhancements"].append({
                "type": "Enhanced Volume Analysis",
                "priority": "Medium",
                "description": "Implement multi-timeframe volume analysis and unusual options activity",
                "current_avg_score": avg_detection_score
            })
        
        return recommendations
    
    def create_enhanced_scanner_rules(self) -> Dict:
        """Create enhanced scanner rules based on backtest findings"""
        rules = {
            "pump_detection_rules": {
                "volume_surge_threshold": 3.0,  # 3x average volume
                "rsi_oversold_threshold": 35,
                "momentum_threshold": 5,  # 5% daily gain
                "volatility_threshold": 5,  # 5% daily volatility
                "bb_squeeze_threshold": 20,  # Bottom 20% of BB range
                "social_mentions_weight": 25,  # Weight for social sentiment
                "short_interest_weight": 30   # Weight for short squeeze potential
            },
            "alert_triggers": [
                {
                    "name": "Volume Breakout Alert",
                    "conditions": ["volume_surge > 5x", "rsi < 50", "bb_position < 30"],
                    "min_score": 60
                },
                {
                    "name": "Oversold Bounce Setup", 
                    "conditions": ["rsi < 35", "volume_surge > 2x", "macd_bullish"],
                    "min_score": 55
                },
                {
                    "name": "Meme Stock Pattern",
                    "conditions": ["social_mentions_spike", "volume_surge > 10x", "price_momentum > 10%"],
                    "min_score": 70
                },
                {
                    "name": "Short Squeeze Setup",
                    "conditions": ["short_interest > 20%", "volume_surge > 3x", "price_momentum > 5%"],
                    "min_score": 75
                }
            ]
        }
        
        return rules

    def generate_backtest_report(self) -> str:
        """Generate comprehensive backtest report"""
        if not self.analysis_results:
            self.run_backtest_analysis()
        
        recommendations = self.generate_enhancement_recommendations()
        enhanced_rules = self.create_enhanced_scanner_rules()
        
        report = f"""
CANDLECAST PUMP DETECTION BACKTEST REPORT
==========================================

SUMMARY STATISTICS:
- Cases Analyzed: {len(self.analysis_results)}
- Detection Success Rate: {recommendations['detection_success_rate']:.1f}%
- High-Value Catches: {recommendations['high_value_catches']} cases
- Major Pumps Missed: {recommendations['missed_major_pumps']} cases

INDIVIDUAL CASE ANALYSIS:
"""
        
        for result in self.analysis_results:
            status = "✓ DETECTED" if result['would_alert'] else "✗ MISSED"
            report += f"""
{result['name']} ({result['symbol']})
{status} - Score: {result['detection_score']}/100 ({result['detection_confidence']})
Pump: +{result['pump_magnitude']:.0f}% on {result['pump_date']}
Cause: {result['cause']}
Detection Factors: {', '.join(result['detection_factors']) if result['detection_factors'] else 'None identified'}
"""

        report += f"""

ENHANCEMENT RECOMMENDATIONS:
"""
        for enhancement in recommendations['enhancements']:
            report += f"""
{enhancement['type']} (Priority: {enhancement['priority']})
- {enhancement['description']}
"""
            if 'missed_cases' in enhancement:
                report += f"- Would have caught: {', '.join(enhancement['missed_cases'])}\n"
            if 'relevant_cases' in enhancement:
                report += f"- Relevant to: {', '.join(enhancement['relevant_cases'])}\n"

        report += """

PROPOSED ENHANCED SCANNER RULES:
- Volume Surge Alert: 3x+ average volume with technical confirmation
- Oversold Bounce Setup: RSI < 35 + volume spike + MACD bullish
- Social Sentiment Integration: Reddit/Twitter mention tracking
- Short Interest Monitoring: Track short squeeze potential
- Multi-timeframe Analysis: Confirm signals across timeframes
"""

        return report