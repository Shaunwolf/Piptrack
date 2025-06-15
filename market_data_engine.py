"""
High-Performance Market Data Engine
Efficiently scans entire US stock market with minimal performance impact
"""

import yfinance as yf
import pandas as pd
import numpy as np
import requests
import time
import logging
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
import pickle
import os
from typing import List, Dict, Tuple, Optional
import queue

class MarketDataEngine:
    def __init__(self):
        self.cache_dir = "market_cache"
        self.cache_duration = 300  # 5 minutes
        self.batch_size = 50  # Process stocks in batches
        self.max_workers = 10  # Concurrent threads
        self.rate_limit_delay = 0.05  # 50ms between requests
        
        # Create cache directory
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Initialize comprehensive stock universe
        self.stock_universe = self._load_comprehensive_universe()
        
        logging.info(f"Market Data Engine initialized with {len(self.stock_universe)} symbols")
    
    def _load_comprehensive_universe(self) -> List[str]:
        """Load comprehensive stock universe from multiple sources"""
        symbols = set()
        
        # S&P 500 stocks
        symbols.update(self._get_sp500_symbols())
        
        # NASDAQ 100
        symbols.update(self._get_nasdaq100_symbols())
        
        # Russell 2000 (small caps)
        symbols.update(self._get_russell2000_symbols())
        
        # Actively traded ETFs
        symbols.update(self._get_popular_etfs())
        
        # High volume stocks
        symbols.update(self._get_high_volume_stocks())
        
        # Biotech and pharma
        symbols.update(self._get_biotech_symbols())
        
        # Crypto-related stocks
        symbols.update(self._get_crypto_symbols())
        
        return list(symbols)
    
    def _get_sp500_symbols(self) -> List[str]:
        """Get S&P 500 symbols"""
        return [
            'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'TSLA', 'META', 'NVDA', 'BRK.B', 'UNH',
            'JNJ', 'XOM', 'JPM', 'V', 'PG', 'HD', 'CVX', 'MA', 'PFE', 'ABBV',
            'BAC', 'KO', 'AVGO', 'PEP', 'TMO', 'COST', 'DHR', 'MRK', 'ABT', 'ACN',
            'VZ', 'ADBE', 'NKE', 'WMT', 'CRM', 'NFLX', 'T', 'NEE', 'CSCO', 'ORCL',
            'AMD', 'TXN', 'LLY', 'QCOM', 'WFC', 'MS', 'RTX', 'MDT', 'HON', 'UPS',
            'IBM', 'AMGN', 'LOW', 'CAT', 'INTC', 'DE', 'GS', 'SBUX', 'BMY', 'BA',
            'SPGI', 'AXP', 'BLK', 'GILD', 'MMM', 'C', 'CVS', 'MO', 'USB', 'LMT',
            'ISRG', 'TJX', 'PNC', 'ADP', 'SYK', 'BKNG', 'AMT', 'MDLZ', 'CI', 'SO',
            'VRTX', 'FIS', 'CB', 'DUK', 'CCI', 'NSC', 'PYPL', 'AON', 'BSX', 'CL'
        ]
    
    def _get_nasdaq100_symbols(self) -> List[str]:
        """Get NASDAQ 100 symbols"""
        return [
            'AAPL', 'MSFT', 'AMZN', 'TSLA', 'GOOGL', 'GOOG', 'META', 'NVDA', 'NFLX', 'ADBE',
            'PYPL', 'INTC', 'CSCO', 'CMCSA', 'PEP', 'COST', 'AVGO', 'TXN', 'QCOM', 'AMD',
            'INTU', 'TMUS', 'AMAT', 'SBUX', 'CHTR', 'ISRG', 'GILD', 'BKNG', 'REGN', 'MU',
            'ADI', 'FISV', 'CSX', 'ATVI', 'MRNA', 'PANW', 'ADP', 'ILMN', 'LRCX', 'MDLZ',
            'KLAC', 'KDP', 'SNPS', 'EXC', 'CDNS', 'MCHP', 'ORLY', 'CTAS', 'BIIB', 'LULU',
            'PLTR', 'SNOW', 'COIN', 'RBLX', 'U', 'DKNG', 'ROKU', 'SQ', 'SHOP', 'PINS'
        ]
    
    def _get_russell2000_symbols(self) -> List[str]:
        """Get Russell 2000 small cap symbols"""
        return [
            'AMC', 'GME', 'BBBY', 'KOSS', 'EXPR', 'NAKD', 'SNDL', 'NOK', 'BB', 'PLTR',
            'WISH', 'CLOV', 'MVIS', 'TLRY', 'WKHS', 'SKLZ', 'RIDE', 'SPCE', 'RKT', 'SOFI',
            'UWMC', 'OPEN', 'ROOT', 'HOOD', 'AFRM', 'UPST', 'PENN', 'FVRR', 'ETSY', 'PINS',
            'CRSR', 'CRWD', 'ZS', 'OKTA', 'DDOG', 'NET', 'FSLY', 'ESTC', 'TEAM', 'WORK'
        ]
    
    def _get_popular_etfs(self) -> List[str]:
        """Get popular ETFs"""
        return [
            'SPY', 'QQQ', 'IWM', 'DIA', 'VTI', 'VEA', 'VWO', 'BND', 'AGG', 'LQD',
            'GLD', 'SLV', 'USO', 'XLE', 'XLF', 'XLK', 'XBI', 'ARKK', 'ARKG', 'ARKF',
            'TQQQ', 'SQQQ', 'UVXY', 'SPXS', 'SPXL', 'TLT', 'HYG', 'EEM', 'FXI'
        ]
    
    def _get_high_volume_stocks(self) -> List[str]:
        """Get high volume trading stocks"""
        return [
            'F', 'GE', 'BAC', 'PFE', 'T', 'WFC', 'C', 'KO', 'XOM', 'JPM',
            'JNJ', 'PG', 'V', 'MA', 'NVDA', 'AAPL', 'MSFT', 'AMZN', 'TSLA', 'META'
        ]
    
    def _get_biotech_symbols(self) -> List[str]:
        """Get biotech and pharmaceutical symbols"""
        return [
            'MRNA', 'BNTX', 'NVAX', 'OCGN', 'INO', 'VXRT', 'SRNE', 'ATOS', 'CTXR', 'BNGO',
            'SENS', 'OBSV', 'CTIC', 'CPRX', 'CYTH', 'SHIP', 'ADMP', 'PROG', 'RGBP', 'ENZC',
            'VBIV', 'VERU', 'CRTX', 'SAVA', 'AVXL', 'BIIB', 'GILD', 'AMGN', 'VRTX', 'REGN'
        ]
    
    def _get_crypto_symbols(self) -> List[str]:
        """Get crypto-related symbols"""
        return [
            'COIN', 'MSTR', 'RIOT', 'MARA', 'CAN', 'BTBT', 'EBON', 'SOS', 'DGLY', 'HVBT',
            'ARGO', 'HIVE', 'BITF', 'HUT', 'CLSK', 'EQOS', 'INSG', 'LFUS', 'ANY', 'NCTY'
        ]
    
    def get_cached_data(self, symbol: str) -> Optional[Dict]:
        """Get cached stock data if available and fresh"""
        cache_file = os.path.join(self.cache_dir, f"{symbol}.pkl")
        
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'rb') as f:
                    cached_data = pickle.load(f)
                
                # Check if cache is still fresh
                cache_time = cached_data.get('timestamp', 0)
                if time.time() - cache_time < self.cache_duration:
                    return cached_data['data']
            except Exception as e:
                logging.warning(f"Cache read error for {symbol}: {e}")
        
        return None
    
    def cache_data(self, symbol: str, data: Dict):
        """Cache stock data"""
        cache_file = os.path.join(self.cache_dir, f"{symbol}.pkl")
        
        try:
            cached_data = {
                'timestamp': time.time(),
                'data': data
            }
            
            with open(cache_file, 'wb') as f:
                pickle.dump(cached_data, f)
        except Exception as e:
            logging.warning(f"Cache write error for {symbol}: {e}")
    
    def fetch_stock_data(self, symbol: str) -> Optional[Dict]:
        """Fetch individual stock data with caching"""
        # Check cache first
        cached_data = self.get_cached_data(symbol)
        if cached_data:
            return cached_data
        
        try:
            # Rate limiting
            time.sleep(self.rate_limit_delay)
            
            # Fetch data
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="3mo")
            
            if hist.empty:
                return None
            
            # Get current price and calculate metrics
            current_price = hist['Close'].iloc[-1]
            volume_avg = hist['Volume'].rolling(20).mean().iloc[-1]
            volume_current = hist['Volume'].iloc[-1]
            volume_spike = volume_current / volume_avg if volume_avg > 0 else 1
            
            # Calculate price change
            price_change = ((current_price - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2]) * 100
            
            # Calculate volatility
            returns = hist['Close'].pct_change().dropna()
            volatility = returns.std() * np.sqrt(252) * 100
            
            data = {
                'symbol': symbol,
                'current_price': float(current_price),
                'price_change': float(price_change),
                'volume_spike': float(volume_spike),
                'volatility': float(volatility),
                'last_updated': datetime.now().isoformat()
            }
            
            # Cache the data
            self.cache_data(symbol, data)
            
            return data
            
        except Exception as e:
            logging.warning(f"Error fetching data for {symbol}: {e}")
            return None
    
    def batch_fetch_data(self, symbols: List[str]) -> List[Dict]:
        """Fetch data for multiple symbols concurrently"""
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_symbol = {
                executor.submit(self.fetch_stock_data, symbol): symbol 
                for symbol in symbols
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                try:
                    data = future.result(timeout=10)  # 10 second timeout
                    if data:
                        results.append(data)
                except Exception as e:
                    logging.warning(f"Error processing {symbol}: {e}")
        
        return results
    
    def scan_market_segment(self, segment: str, limit: int = 100) -> List[Dict]:
        """Scan specific market segment"""
        segment_symbols = {
            'large_cap': self._get_sp500_symbols()[:limit],
            'tech': self._get_nasdaq100_symbols()[:limit],
            'small_cap': self._get_russell2000_symbols()[:limit],
            'biotech': self._get_biotech_symbols()[:limit],
            'crypto': self._get_crypto_symbols()[:limit],
            'etfs': self._get_popular_etfs()[:limit]
        }
        
        symbols = segment_symbols.get(segment, self.stock_universe[:limit])
        return self.batch_fetch_data(symbols)
    
    def quick_market_scan(self, limit: int = 50) -> List[Dict]:
        """Quick scan of most active stocks"""
        # Focus on high-volume, liquid stocks for speed
        priority_symbols = (
            self._get_high_volume_stocks() + 
            self._get_popular_etfs() + 
            self._get_sp500_symbols()[:30]
        )
        
        # Remove duplicates and limit
        unique_symbols = list(dict.fromkeys(priority_symbols))[:limit]
        
        return self.batch_fetch_data(unique_symbols)
    
    def comprehensive_market_scan(self, limit: int = 500) -> List[Dict]:
        """Comprehensive scan of entire market in batches"""
        all_results = []
        symbols_to_scan = self.stock_universe[:limit]
        
        # Process in batches to avoid overwhelming the system
        for i in range(0, len(symbols_to_scan), self.batch_size):
            batch = symbols_to_scan[i:i + self.batch_size]
            batch_results = self.batch_fetch_data(batch)
            all_results.extend(batch_results)
            
            # Small delay between batches
            time.sleep(0.5)
            
            logging.info(f"Processed batch {i//self.batch_size + 1}/{(len(symbols_to_scan) + self.batch_size - 1)//self.batch_size}")
        
        return all_results
    
    def get_market_movers(self, scan_type: str = "quick") -> Dict:
        """Get market movers with different scan intensities"""
        if scan_type == "quick":
            data = self.quick_market_scan(50)
        elif scan_type == "comprehensive":
            data = self.comprehensive_market_scan(200)
        else:
            data = self.scan_market_segment(scan_type, 100)
        
        if not data:
            return {'gainers': [], 'losers': [], 'volume_leaders': []}
        
        # Sort by price change
        sorted_data = sorted(data, key=lambda x: x.get('price_change', 0), reverse=True)
        
        gainers = [stock for stock in sorted_data if stock.get('price_change', 0) > 0][:10]
        losers = [stock for stock in sorted_data if stock.get('price_change', 0) < 0][-10:]
        
        # Sort by volume spike
        volume_leaders = sorted(data, key=lambda x: x.get('volume_spike', 0), reverse=True)[:10]
        
        return {
            'gainers': gainers,
            'losers': losers,
            'volume_leaders': volume_leaders,
            'total_scanned': len(data),
            'scan_type': scan_type
        }
    
    def clear_cache(self):
        """Clear all cached data"""
        try:
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.pkl'):
                    os.remove(os.path.join(self.cache_dir, filename))
            logging.info("Cache cleared successfully")
        except Exception as e:
            logging.error(f"Error clearing cache: {e}")
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        try:
            cache_files = [f for f in os.listdir(self.cache_dir) if f.endswith('.pkl')]
            total_size = sum(
                os.path.getsize(os.path.join(self.cache_dir, f)) 
                for f in cache_files
            )
            
            return {
                'cached_symbols': len(cache_files),
                'cache_size_mb': round(total_size / (1024 * 1024), 2),
                'cache_duration_minutes': self.cache_duration / 60
            }
        except Exception as e:
            logging.error(f"Error getting cache stats: {e}")
            return {'error': str(e)}