"""
Background Market Scanner
Continuously scans entire US stock market in background without affecting site performance
"""

import threading
import time
import logging
import queue
from datetime import datetime, timedelta
from market_data_engine import MarketDataEngine
from stock_scanner import StockScanner
import json
import os

class BackgroundScanner:
    def __init__(self):
        self.market_engine = MarketDataEngine()
        self.stock_scanner = StockScanner()
        self.is_running = False
        self.scan_queue = queue.Queue()
        self.results_cache = {}
        self.last_full_scan = None
        
        # Scan intervals (in seconds)
        self.quick_scan_interval = 60  # 1 minute
        self.market_scan_interval = 300  # 5 minutes
        self.full_scan_interval = 1800  # 30 minutes
        
        # Results storage
        self.results_file = "scan_results.json"
        self.load_cached_results()
        
        logging.info("Background Scanner initialized")
    
    def load_cached_results(self):
        """Load previously cached scan results"""
        try:
            if os.path.exists(self.results_file):
                with open(self.results_file, 'r') as f:
                    self.results_cache = json.load(f)
                logging.info(f"Loaded {len(self.results_cache)} cached scan results")
        except Exception as e:
            logging.warning(f"Could not load cached results: {e}")
            self.results_cache = {}
    
    def save_results(self):
        """Save scan results to file"""
        try:
            with open(self.results_file, 'w') as f:
                json.dump(self.results_cache, f)
        except Exception as e:
            logging.error(f"Could not save scan results: {e}")
    
    def start_background_scanning(self):
        """Start background scanning threads"""
        if self.is_running:
            return
        
        self.is_running = True
        
        # Start different scanning threads
        quick_thread = threading.Thread(target=self._quick_scan_loop, daemon=True)
        market_thread = threading.Thread(target=self._market_scan_loop, daemon=True)
        full_thread = threading.Thread(target=self._full_scan_loop, daemon=True)
        
        quick_thread.start()
        market_thread.start()
        full_thread.start()
        
        logging.info("Background scanning started")
    
    def stop_background_scanning(self):
        """Stop background scanning"""
        self.is_running = False
        self.save_results()
        logging.info("Background scanning stopped")
    
    def _quick_scan_loop(self):
        """Quick scan of high-volume stocks every minute"""
        while self.is_running:
            try:
                # Scan top 50 most active stocks
                results = self.market_engine.quick_market_scan(50)
                
                # Filter for interesting stocks
                filtered_results = []
                for stock in results:
                    if (abs(stock.get('price_change', 0)) > 2 or 
                        stock.get('volume_spike', 0) > 1.5):
                        filtered_results.append(stock)
                
                # Update cache
                self.results_cache['quick_scan'] = {
                    'timestamp': datetime.now().isoformat(),
                    'results': filtered_results,
                    'total_scanned': len(results)
                }
                
                logging.info(f"Quick scan completed: {len(filtered_results)} interesting stocks found")
                
            except Exception as e:
                logging.error(f"Quick scan error: {e}")
            
            time.sleep(self.quick_scan_interval)
    
    def _market_scan_loop(self):
        """Market segment scan every 5 minutes"""
        segments = ['large_cap', 'tech', 'small_cap', 'biotech', 'crypto']
        segment_index = 0
        
        while self.is_running:
            try:
                current_segment = segments[segment_index]
                results = self.market_engine.scan_market_segment(current_segment, 100)
                
                # Analyze with stock scanner
                analyzed_results = []
                for stock_data in results[:20]:  # Limit to prevent overload
                    symbol = stock_data['symbol']
                    analysis = self.stock_scanner.analyze_stock(symbol)
                    if analysis and analysis.get('confidence_score', 0) > 25:
                        analyzed_results.append(analysis)
                
                # Update cache
                self.results_cache[f'{current_segment}_scan'] = {
                    'timestamp': datetime.now().isoformat(),
                    'results': analyzed_results,
                    'total_scanned': len(results)
                }
                
                logging.info(f"{current_segment} scan completed: {len(analyzed_results)} opportunities found")
                
                # Move to next segment
                segment_index = (segment_index + 1) % len(segments)
                
            except Exception as e:
                logging.error(f"Market scan error: {e}")
            
            time.sleep(self.market_scan_interval)
    
    def _full_scan_loop(self):
        """Full market scan every 30 minutes"""
        while self.is_running:
            try:
                # Comprehensive market scan
                all_movers = self.market_engine.get_market_movers("comprehensive")
                
                # Get top opportunities from each category
                top_gainers = all_movers['gainers'][:10]
                top_losers = all_movers['losers'][:10]
                volume_leaders = all_movers['volume_leaders'][:10]
                
                # Combine and analyze top picks
                top_picks = []
                all_candidates = top_gainers + volume_leaders
                
                for stock_data in all_candidates:
                    symbol = stock_data['symbol']
                    analysis = self.stock_scanner.analyze_stock(symbol)
                    if analysis and analysis.get('confidence_score', 0) > 30:
                        top_picks.append(analysis)
                
                # Sort by confidence
                top_picks.sort(key=lambda x: x.get('confidence_score', 0), reverse=True)
                
                # Update cache
                self.results_cache['full_scan'] = {
                    'timestamp': datetime.now().isoformat(),
                    'top_picks': top_picks[:15],
                    'market_movers': {
                        'gainers': top_gainers,
                        'losers': top_losers,
                        'volume_leaders': volume_leaders
                    },
                    'total_scanned': all_movers['total_scanned']
                }
                
                self.last_full_scan = datetime.now()
                
                # Save results to file
                self.save_results()
                
                logging.info(f"Full scan completed: {len(top_picks)} top picks identified from {all_movers['total_scanned']} stocks")
                
            except Exception as e:
                logging.error(f"Full scan error: {e}")
            
            time.sleep(self.full_scan_interval)
    
    def get_latest_results(self, scan_type: str = 'all'):
        """Get latest scan results"""
        if scan_type == 'all':
            return self.results_cache
        else:
            return self.results_cache.get(scan_type, {})
    
    def get_top_opportunities(self, limit: int = 10):
        """Get current top trading opportunities"""
        opportunities = []
        
        # Get from full scan if available
        full_scan = self.results_cache.get('full_scan', {})
        if full_scan and 'top_picks' in full_scan:
            opportunities.extend(full_scan['top_picks'])
        
        # Add from quick scan
        quick_scan = self.results_cache.get('quick_scan', {})
        if quick_scan and 'results' in quick_scan:
            for stock in quick_scan['results']:
                if stock['symbol'] not in [opp['symbol'] for opp in opportunities]:
                    # Quick analysis for quick scan results
                    analysis = self.stock_scanner.analyze_stock(stock['symbol'])
                    if analysis and analysis.get('confidence_score', 0) > 25:
                        opportunities.append(analysis)
        
        # Sort by confidence and return top results
        opportunities.sort(key=lambda x: x.get('confidence_score', 0), reverse=True)
        return opportunities[:limit]
    
    def get_market_overview(self):
        """Get comprehensive market overview"""
        overview = {
            'last_updated': datetime.now().isoformat(),
            'scan_status': 'active' if self.is_running else 'stopped',
            'total_opportunities': 0,
            'sectors_scanned': 0,
            'last_full_scan': self.last_full_scan.isoformat() if self.last_full_scan else None
        }
        
        # Count opportunities across all scans
        for scan_key, scan_data in self.results_cache.items():
            if 'results' in scan_data:
                overview['total_opportunities'] += len(scan_data['results'])
            elif 'top_picks' in scan_data:
                overview['total_opportunities'] += len(scan_data['top_picks'])
        
        # Count scanned sectors
        sector_scans = [key for key in self.results_cache.keys() if key.endswith('_scan')]
        overview['sectors_scanned'] = len(sector_scans)
        
        # Get cache stats
        cache_stats = self.market_engine.get_cache_stats()
        overview['cache_stats'] = cache_stats
        
        return overview
    
    def force_scan(self, scan_type: str = 'quick'):
        """Force an immediate scan"""
        try:
            if scan_type == 'quick':
                results = self.market_engine.quick_market_scan(50)
                scan_key = 'forced_quick_scan'
            elif scan_type == 'comprehensive':
                results = self.market_engine.get_market_movers("comprehensive")
                scan_key = 'forced_comprehensive_scan'
            else:
                results = self.market_engine.scan_market_segment(scan_type, 100)
                scan_key = f'forced_{scan_type}_scan'
            
            # Store results
            self.results_cache[scan_key] = {
                'timestamp': datetime.now().isoformat(),
                'results': results,
                'forced': True
            }
            
            logging.info(f"Forced {scan_type} scan completed")
            return results
            
        except Exception as e:
            logging.error(f"Forced scan error: {e}")
            return []
    
    def clear_cache(self):
        """Clear all cached results"""
        self.results_cache = {}
        self.market_engine.clear_cache()
        if os.path.exists(self.results_file):
            os.remove(self.results_file)
        logging.info("All caches cleared")
    
    def get_performance_stats(self):
        """Get scanner performance statistics"""
        stats = {
            'is_running': self.is_running,
            'scan_intervals': {
                'quick_scan': f"{self.quick_scan_interval}s",
                'market_scan': f"{self.market_scan_interval}s", 
                'full_scan': f"{self.full_scan_interval}s"
            },
            'cached_scans': len(self.results_cache),
            'last_full_scan': self.last_full_scan.isoformat() if self.last_full_scan else 'Never'
        }
        
        # Add market engine stats
        stats.update(self.market_engine.get_cache_stats())
        
        return stats

# Global instance
background_scanner = BackgroundScanner()