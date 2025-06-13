from typing import Dict, List
import logging
from datetime import datetime
from stock_scanner import StockScanner
from multi_timeframe_analyzer import MultiTimeframeAnalyzer
from pattern_evolution_tracker import PatternEvolutionTracker

class ScannerWidgets:
    def __init__(self):
        self.scanner = StockScanner()
        try:
            self.mtf_analyzer = MultiTimeframeAnalyzer()
            self.pattern_tracker = PatternEvolutionTracker()
        except ImportError:
            self.mtf_analyzer = None
            self.pattern_tracker = None
    
    def get_widget_presets(self) -> List[Dict]:
        """Get all available scanner widget presets"""
        return [
            {
                'id': 'momentum_rockets',
                'name': '🚀 Momentum Rockets',
                'description': 'High-momentum breakouts with explosive volume',
                'color': 'from-red-500 to-orange-500',
                'criteria': {
                    'min_volume_spike': 2.0,
                    'min_confidence': 70,
                    'rsi_range': [50, 80],
                    'price_range': [1, 25],
                    'pattern_types': ['breakout', 'bull_flag'],
                    'trend_filter': 'bullish'
                },
                'icon': '🚀'
            },
            {
                'id': 'reversal_hunters',
                'name': '🔄 Reversal Hunters',
                'description': 'Oversold stocks showing reversal signals',
                'color': 'from-blue-500 to-purple-500',
                'criteria': {
                    'min_volume_spike': 1.5,
                    'min_confidence': 60,
                    'rsi_range': [20, 40],
                    'price_range': [1, 25],
                    'pattern_types': ['reversal', 'cup_and_handle'],
                    'trend_filter': 'any'
                },
                'icon': '🔄'
            },
            {
                'id': 'gap_masters',
                'name': '⚡ Gap Masters',
                'description': 'Pre-market and opening gap plays',
                'color': 'from-yellow-500 to-red-500',
                'criteria': {
                    'min_gap_percent': 5.0,
                    'min_volume_spike': 3.0,
                    'min_confidence': 65,
                    'price_range': [1, 25],
                    'time_filter': 'market_open'
                },
                'icon': '⚡'
            },
            {
                'id': 'pattern_perfection',
                'name': '📐 Pattern Perfection',
                'description': 'Technical patterns at optimal entry points',
                'color': 'from-green-500 to-blue-500',
                'criteria': {
                    'min_pattern_completion': 80,
                    'min_confidence': 75,
                    'breakout_probability': 70,
                    'price_range': [1, 25],
                    'pattern_types': ['triangle', 'cup_and_handle', 'bull_flag']
                },
                'icon': '📐'
            },
            {
                'id': 'penny_powerhouse',
                'name': '💎 Penny Powerhouse',
                'description': 'Sub-$5 stocks with institutional interest',
                'color': 'from-purple-500 to-pink-500',
                'criteria': {
                    'price_range': [1, 5],
                    'min_volume_spike': 2.5,
                    'min_confidence': 60,
                    'unusual_volume': True,
                    'institutional_activity': True
                },
                'icon': '💎'
            },
            {
                'id': 'sector_rotation',
                'name': '🔄 Sector Rotation',
                'description': 'Leading stocks in rotating sectors',
                'color': 'from-indigo-500 to-blue-500',
                'criteria': {
                    'sector_strength': 'top_3',
                    'relative_strength': 70,
                    'min_confidence': 65,
                    'price_range': [1, 25],
                    'market_cap_filter': 'small_to_mid'
                },
                'icon': '🔄'
            },
            {
                'id': 'volatility_crushers',
                'name': '📈 Volatility Crushers',
                'description': 'Stocks breaking out of low volatility',
                'color': 'from-teal-500 to-green-500',
                'criteria': {
                    'volatility_breakout': True,
                    'min_confidence': 70,
                    'bollinger_position': [80, 100],
                    'price_range': [1, 25],
                    'volume_acceleration': True
                },
                'icon': '📈'
            },
            {
                'id': 'earnings_warriors',
                'name': '📊 Earnings Warriors',
                'description': 'Pre/post earnings momentum plays',
                'color': 'from-orange-500 to-yellow-500',
                'criteria': {
                    'earnings_proximity': 'within_week',
                    'options_activity': 'unusual',
                    'min_confidence': 65,
                    'price_range': [1, 25],
                    'analyst_sentiment': 'positive'
                },
                'icon': '📊'
            },
            {
                'id': 'fibonacci_magnet',
                'name': '🌟 Fibonacci Magnet',
                'description': 'Stocks reacting at key Fibonacci levels',
                'color': 'from-pink-500 to-purple-500',
                'criteria': {
                    'fibonacci_level': 'key_retracement',
                    'min_confidence': 70,
                    'support_resistance_confluence': True,
                    'price_range': [1, 25],
                    'pattern_types': ['retracement', 'continuation']
                },
                'icon': '🌟'
            },
            {
                'id': 'dark_horse',
                'name': '🏴 Dark Horse',
                'description': 'Under-the-radar stocks with hidden potential',
                'color': 'from-gray-600 to-gray-800',
                'criteria': {
                    'analyst_coverage': 'minimal',
                    'insider_activity': 'positive',
                    'min_confidence': 55,
                    'price_range': [1, 15],
                    'institutional_accumulation': True
                },
                'icon': '🏴'
            }
        ]
    
    def run_widget_scan(self, widget_id: str, limit: int = 10) -> Dict:
        """Run a specific widget scanner preset"""
        try:
            presets = self.get_widget_presets()
            widget = next((w for w in presets if w['id'] == widget_id), None)
            
            if not widget:
                return {'success': False, 'error': f'Widget {widget_id} not found'}
            
            # Get the criteria for this widget
            criteria = widget['criteria']
            
            # Run specialized scan based on widget type
            if widget_id == 'momentum_rockets':
                results = self._scan_momentum_rockets(criteria, limit)
            elif widget_id == 'reversal_hunters':
                results = self._scan_reversal_hunters(criteria, limit)
            elif widget_id == 'gap_masters':
                results = self._scan_gap_masters(criteria, limit)
            elif widget_id == 'pattern_perfection':
                results = self._scan_pattern_perfection(criteria, limit)
            elif widget_id == 'penny_powerhouse':
                results = self._scan_penny_powerhouse(criteria, limit)
            elif widget_id == 'sector_rotation':
                results = self._scan_sector_rotation(criteria, limit)
            elif widget_id == 'volatility_crushers':
                results = self._scan_volatility_crushers(criteria, limit)
            elif widget_id == 'earnings_warriors':
                results = self._scan_earnings_warriors(criteria, limit)
            elif widget_id == 'fibonacci_magnet':
                results = self._scan_fibonacci_magnet(criteria, limit)
            elif widget_id == 'dark_horse':
                results = self._scan_dark_horse(criteria, limit)
            else:
                results = self._scan_generic(criteria, limit)
            
            return {
                'success': True,
                'widget': widget,
                'results': results,
                'scan_time': datetime.now().isoformat(),
                'total_found': len(results) if results else 0
            }
            
        except Exception as e:
            logging.error(f"Error running widget scan {widget_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    def _scan_momentum_rockets(self, criteria: Dict, limit: int) -> List[Dict]:
        """Scan for high-momentum breakout stocks"""
        try:
            # Get base scan results
            base_results = self.scanner.scan_for_opportunities('gappers')
            
            if isinstance(base_results, dict) and 'results' in base_results:
                stocks = base_results['results']
            else:
                stocks = base_results
            
            # Filter for momentum criteria
            filtered = []
            for stock in stocks:
                if (stock.get('volume_spike', 0) >= criteria.get('min_volume_spike', 2.0) and
                    stock.get('confidence_score', 0) >= criteria.get('min_confidence', 70) and
                    criteria['rsi_range'][0] <= stock.get('rsi', 50) <= criteria['rsi_range'][1] and
                    criteria['price_range'][0] <= stock.get('price', 0) <= criteria['price_range'][1]):
                    
                    # Add momentum score
                    momentum_score = self._calculate_momentum_score(stock)
                    stock['momentum_score'] = momentum_score
                    stock['widget_score'] = momentum_score
                    
                    filtered.append(stock)
            
            # Sort by momentum score and return top results
            filtered.sort(key=lambda x: x.get('momentum_score', 0), reverse=True)
            return filtered[:limit]
            
        except Exception as e:
            logging.error(f"Error in momentum rockets scan: {e}")
            return []
    
    def _scan_reversal_hunters(self, criteria: Dict, limit: int) -> List[Dict]:
        """Scan for oversold reversal candidates"""
        try:
            base_results = self.scanner.scan_for_opportunities('gappers')
            
            if isinstance(base_results, dict) and 'results' in base_results:
                stocks = base_results['results']
            else:
                stocks = base_results
            
            filtered = []
            for stock in stocks:
                rsi = stock.get('rsi', 50)
                if (criteria['rsi_range'][0] <= rsi <= criteria['rsi_range'][1] and
                    stock.get('volume_spike', 0) >= criteria.get('min_volume_spike', 1.5) and
                    criteria['price_range'][0] <= stock.get('price', 0) <= criteria['price_range'][1]):
                    
                    # Calculate reversal probability
                    reversal_score = self._calculate_reversal_score(stock)
                    stock['reversal_score'] = reversal_score
                    stock['widget_score'] = reversal_score
                    
                    filtered.append(stock)
            
            filtered.sort(key=lambda x: x.get('reversal_score', 0), reverse=True)
            return filtered[:limit]
            
        except Exception as e:
            logging.error(f"Error in reversal hunters scan: {e}")
            return []
    
    def _scan_gap_masters(self, criteria: Dict, limit: int) -> List[Dict]:
        """Scan for gap trading opportunities"""
        try:
            # Use the scanner's gap detection
            gap_stocks = self.scanner.scan_top_gappers(50)
            
            filtered = []
            for stock in gap_stocks:
                # Calculate gap percentage (simplified)
                gap_score = stock.get('volume_spike', 1) * stock.get('confidence_score', 0) / 100
                
                if (gap_score >= 2.0 and
                    stock.get('volume_spike', 0) >= criteria.get('min_volume_spike', 3.0) and
                    criteria['price_range'][0] <= stock.get('price', 0) <= criteria['price_range'][1]):
                    
                    stock['gap_score'] = gap_score
                    stock['widget_score'] = gap_score
                    filtered.append(stock)
            
            filtered.sort(key=lambda x: x.get('gap_score', 0), reverse=True)
            return filtered[:limit]
            
        except Exception as e:
            logging.error(f"Error in gap masters scan: {e}")
            return []
    
    def _scan_pattern_perfection(self, criteria: Dict, limit: int) -> List[Dict]:
        """Scan for perfect technical patterns"""
        try:
            if not self.pattern_tracker:
                return self._scan_generic(criteria, limit)
            
            base_results = self.scanner.scan_for_opportunities('gappers')
            
            if isinstance(base_results, dict) and 'results' in base_results:
                stocks = base_results['results']
            else:
                stocks = base_results
            
            filtered = []
            for stock in stocks:
                try:
                    # Get pattern evolution data
                    pattern_data = self.pattern_tracker.track_pattern_evolution(stock['symbol'])
                    
                    if pattern_data:
                        completion = pattern_data.get('completion_percentage', 0)
                        breakout_prob = pattern_data.get('breakout_probability_5_days', 0)
                        
                        if (completion >= criteria.get('min_pattern_completion', 80) and
                            breakout_prob >= criteria.get('breakout_probability', 70) and
                            criteria['price_range'][0] <= stock.get('price', 0) <= criteria['price_range'][1]):
                            
                            pattern_score = (completion + breakout_prob) / 2
                            stock['pattern_score'] = pattern_score
                            stock['widget_score'] = pattern_score
                            stock['pattern_data'] = pattern_data
                            
                            filtered.append(stock)
                            
                except Exception as e:
                    logging.error(f"Error analyzing pattern for {stock['symbol']}: {e}")
                    continue
            
            filtered.sort(key=lambda x: x.get('pattern_score', 0), reverse=True)
            return filtered[:limit]
            
        except Exception as e:
            logging.error(f"Error in pattern perfection scan: {e}")
            return []
    
    def _scan_penny_powerhouse(self, criteria: Dict, limit: int) -> List[Dict]:
        """Scan for penny stocks with institutional interest"""
        try:
            base_results = self.scanner.scan_for_opportunities('gappers')
            
            if isinstance(base_results, dict) and 'results' in base_results:
                stocks = base_results['results']
            else:
                stocks = base_results
            
            filtered = []
            for stock in stocks:
                price = stock.get('price', 0)
                if (criteria['price_range'][0] <= price <= criteria['price_range'][1] and
                    stock.get('volume_spike', 0) >= criteria.get('min_volume_spike', 2.5)):
                    
                    # Calculate penny power score
                    penny_score = stock.get('volume_spike', 1) * (6 - price) * stock.get('confidence_score', 0) / 100
                    stock['penny_score'] = penny_score
                    stock['widget_score'] = penny_score
                    
                    filtered.append(stock)
            
            filtered.sort(key=lambda x: x.get('penny_score', 0), reverse=True)
            return filtered[:limit]
            
        except Exception as e:
            logging.error(f"Error in penny powerhouse scan: {e}")
            return []
    
    def _scan_sector_rotation(self, criteria: Dict, limit: int) -> List[Dict]:
        """Scan for sector rotation plays"""
        try:
            # Get market overview for sector performance
            market_overview = self.scanner.get_market_overview()
            
            if 'error' in market_overview:
                return self._scan_generic(criteria, limit)
            
            # Get top performing sectors
            top_sectors = market_overview.get('top_sectors', [])[:3]
            
            base_results = self.scanner.scan_for_opportunities('gappers')
            
            if isinstance(base_results, dict) and 'results' in base_results:
                stocks = base_results['results']
            else:
                stocks = base_results
            
            # For this demo, we'll use a simplified sector scoring
            filtered = []
            for stock in stocks:
                if (stock.get('confidence_score', 0) >= criteria.get('min_confidence', 65) and
                    criteria['price_range'][0] <= stock.get('price', 0) <= criteria['price_range'][1]):
                    
                    sector_score = stock.get('confidence_score', 0) + stock.get('volume_spike', 1) * 10
                    stock['sector_score'] = sector_score
                    stock['widget_score'] = sector_score
                    
                    filtered.append(stock)
            
            filtered.sort(key=lambda x: x.get('sector_score', 0), reverse=True)
            return filtered[:limit]
            
        except Exception as e:
            logging.error(f"Error in sector rotation scan: {e}")
            return []
    
    def _scan_volatility_crushers(self, criteria: Dict, limit: int) -> List[Dict]:
        """Scan for volatility breakout candidates"""
        try:
            base_results = self.scanner.scan_for_opportunities('gappers')
            
            if isinstance(base_results, dict) and 'results' in base_results:
                stocks = base_results['results']
            else:
                stocks = base_results
            
            filtered = []
            for stock in stocks:
                # Look for volume acceleration as proxy for volatility breakout
                volume_spike = stock.get('volume_spike', 1)
                confidence = stock.get('confidence_score', 0)
                
                if (volume_spike >= 2.0 and
                    confidence >= criteria.get('min_confidence', 70) and
                    criteria['price_range'][0] <= stock.get('price', 0) <= criteria['price_range'][1]):
                    
                    volatility_score = volume_spike * confidence / 10
                    stock['volatility_score'] = volatility_score
                    stock['widget_score'] = volatility_score
                    
                    filtered.append(stock)
            
            filtered.sort(key=lambda x: x.get('volatility_score', 0), reverse=True)
            return filtered[:limit]
            
        except Exception as e:
            logging.error(f"Error in volatility crushers scan: {e}")
            return []
    
    def _scan_earnings_warriors(self, criteria: Dict, limit: int) -> List[Dict]:
        """Scan for earnings-related plays"""
        try:
            base_results = self.scanner.scan_for_opportunities('gappers')
            
            if isinstance(base_results, dict) and 'results' in base_results:
                stocks = base_results['results']
            else:
                stocks = base_results
            
            # For earnings plays, prioritize high volume and volatility
            filtered = []
            for stock in stocks:
                volume_spike = stock.get('volume_spike', 1)
                confidence = stock.get('confidence_score', 0)
                
                if (volume_spike >= 1.8 and
                    confidence >= criteria.get('min_confidence', 65) and
                    criteria['price_range'][0] <= stock.get('price', 0) <= criteria['price_range'][1]):
                    
                    earnings_score = volume_spike * confidence / 8
                    stock['earnings_score'] = earnings_score
                    stock['widget_score'] = earnings_score
                    
                    filtered.append(stock)
            
            filtered.sort(key=lambda x: x.get('earnings_score', 0), reverse=True)
            return filtered[:limit]
            
        except Exception as e:
            logging.error(f"Error in earnings warriors scan: {e}")
            return []
    
    def _scan_fibonacci_magnet(self, criteria: Dict, limit: int) -> List[Dict]:
        """Scan for Fibonacci retracement plays"""
        try:
            base_results = self.scanner.scan_for_opportunities('gappers')
            
            if isinstance(base_results, dict) and 'results' in base_results:
                stocks = base_results['results']
            else:
                stocks = base_results
            
            filtered = []
            for stock in stocks:
                # Use fibonacci_position as proxy for Fibonacci alignment
                fib_position = stock.get('fibonacci_position', 50)
                confidence = stock.get('confidence_score', 0)
                
                # Look for stocks near key Fibonacci levels (38.2%, 50%, 61.8%)
                key_levels = [38.2, 50.0, 61.8]
                near_key_level = any(abs(fib_position - level) < 5 for level in key_levels)
                
                if (near_key_level and
                    confidence >= criteria.get('min_confidence', 70) and
                    criteria['price_range'][0] <= stock.get('price', 0) <= criteria['price_range'][1]):
                    
                    fib_score = confidence + (100 - min(abs(fib_position - level) for level in key_levels))
                    stock['fib_score'] = fib_score
                    stock['widget_score'] = fib_score
                    
                    filtered.append(stock)
            
            filtered.sort(key=lambda x: x.get('fib_score', 0), reverse=True)
            return filtered[:limit]
            
        except Exception as e:
            logging.error(f"Error in fibonacci magnet scan: {e}")
            return []
    
    def _scan_dark_horse(self, criteria: Dict, limit: int) -> List[Dict]:
        """Scan for under-the-radar opportunities"""
        try:
            base_results = self.scanner.scan_for_opportunities('gappers')
            
            if isinstance(base_results, dict) and 'results' in base_results:
                stocks = base_results['results']
            else:
                stocks = base_results
            
            # Look for lower confidence but interesting setups
            filtered = []
            for stock in stocks:
                confidence = stock.get('confidence_score', 0)
                volume_spike = stock.get('volume_spike', 1)
                price = stock.get('price', 0)
                
                if (criteria.get('min_confidence', 55) <= confidence <= 75 and
                    volume_spike >= 1.3 and
                    criteria['price_range'][0] <= price <= criteria['price_range'][1]):
                    
                    # Dark horse score: potential vs recognition
                    dark_score = volume_spike * (80 - confidence) / 2
                    stock['dark_score'] = dark_score
                    stock['widget_score'] = dark_score
                    
                    filtered.append(stock)
            
            filtered.sort(key=lambda x: x.get('dark_score', 0), reverse=True)
            return filtered[:limit]
            
        except Exception as e:
            logging.error(f"Error in dark horse scan: {e}")
            return []
    
    def _scan_generic(self, criteria: Dict, limit: int) -> List[Dict]:
        """Generic scan fallback"""
        try:
            base_results = self.scanner.scan_for_opportunities('gappers')
            
            if isinstance(base_results, dict) and 'results' in base_results:
                stocks = base_results['results']
            else:
                stocks = base_results
            
            # Apply basic filtering
            filtered = []
            for stock in stocks:
                confidence = stock.get('confidence_score', 0)
                price = stock.get('price', 0)
                
                if (confidence >= criteria.get('min_confidence', 50) and
                    criteria.get('price_range', [1, 25])[0] <= price <= criteria.get('price_range', [1, 25])[1]):
                    
                    stock['widget_score'] = confidence
                    filtered.append(stock)
            
            filtered.sort(key=lambda x: x.get('widget_score', 0), reverse=True)
            return filtered[:limit]
            
        except Exception as e:
            logging.error(f"Error in generic scan: {e}")
            return []
    
    def _calculate_momentum_score(self, stock: Dict) -> float:
        """Calculate momentum score for a stock"""
        try:
            volume_spike = stock.get('volume_spike', 1)
            confidence = stock.get('confidence_score', 0)
            rsi = stock.get('rsi', 50)
            
            # Momentum favors high RSI, high volume, high confidence
            momentum = (volume_spike * 20) + confidence + (rsi - 50)
            return max(0, min(100, momentum))
            
        except Exception as e:
            logging.error(f"Error calculating momentum score: {e}")
            return 0
    
    def _calculate_reversal_score(self, stock: Dict) -> float:
        """Calculate reversal probability score"""
        try:
            volume_spike = stock.get('volume_spike', 1)
            confidence = stock.get('confidence_score', 0)
            rsi = stock.get('rsi', 50)
            
            # Reversal favors low RSI with volume confirmation
            reversal_potential = (50 - rsi) + (volume_spike * 15) + (confidence * 0.5)
            return max(0, min(100, reversal_potential))
            
        except Exception as e:
            logging.error(f"Error calculating reversal score: {e}")
            return 0