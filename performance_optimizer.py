"""
Performance Optimization Engine for CandleCast
Implements caching, lazy loading, and API rate limiting
"""

import time
import threading
from datetime import datetime, timedelta
from functools import wraps
import json
import os
import logging

class CacheManager:
    """Advanced caching system with TTL and memory management"""
    
    def __init__(self, max_size=1000, default_ttl=300):
        self.cache = {}
        self.timestamps = {}
        self.access_times = {}
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.lock = threading.RLock()
    
    def get(self, key, default=None):
        """Get cached value with TTL check"""
        with self.lock:
            if key not in self.cache:
                return default
            
            # Check TTL
            if self._is_expired(key):
                self._remove(key)
                return default
            
            # Update access time for LRU
            self.access_times[key] = time.time()
            return self.cache[key]
    
    def set(self, key, value, ttl=None):
        """Set cached value with TTL"""
        with self.lock:
            # Enforce size limit
            if len(self.cache) >= self.max_size and key not in self.cache:
                self._evict_lru()
            
            self.cache[key] = value
            self.timestamps[key] = time.time()
            self.access_times[key] = time.time()
            
            if ttl:
                self.timestamps[key] = time.time() + ttl
    
    def _is_expired(self, key):
        """Check if cache entry is expired"""
        if key not in self.timestamps:
            return True
        return time.time() > (self.timestamps[key] + self.default_ttl)
    
    def _remove(self, key):
        """Remove cache entry"""
        self.cache.pop(key, None)
        self.timestamps.pop(key, None)
        self.access_times.pop(key, None)
    
    def _evict_lru(self):
        """Evict least recently used item"""
        if not self.access_times:
            return
        
        lru_key = min(self.access_times, key=self.access_times.get)
        self._remove(lru_key)
    
    def clear(self):
        """Clear all cache"""
        with self.lock:
            self.cache.clear()
            self.timestamps.clear()
            self.access_times.clear()
    
    def get_stats(self):
        """Get cache statistics"""
        with self.lock:
            return {
                'size': len(self.cache),
                'max_size': self.max_size,
                'hit_ratio': getattr(self, '_hits', 0) / max(getattr(self, '_requests', 1), 1)
            }

class APIRateLimiter:
    """Rate limiter for external API calls"""
    
    def __init__(self, calls_per_minute=60):
        self.calls_per_minute = calls_per_minute
        self.calls = []
        self.lock = threading.Lock()
    
    def wait_if_needed(self):
        """Wait if rate limit would be exceeded"""
        with self.lock:
            now = time.time()
            
            # Remove old calls
            self.calls = [call_time for call_time in self.calls if now - call_time < 60]
            
            # Check if we need to wait
            if len(self.calls) >= self.calls_per_minute:
                sleep_time = 60 - (now - self.calls[0])
                if sleep_time > 0:
                    time.sleep(sleep_time)
            
            # Record this call
            self.calls.append(now)

class PerformanceOptimizer:
    """Main performance optimization coordinator"""
    
    def __init__(self):
        self.cache = CacheManager(max_size=2000, default_ttl=300)  # 5 minute TTL
        self.rate_limiter = APIRateLimiter(calls_per_minute=45)  # Conservative limit
        self.background_tasks = []
        self.setup_logging()
    
    def setup_logging(self):
        """Setup performance logging"""
        self.logger = logging.getLogger('performance')
        self.logger.setLevel(logging.INFO)
    
    def cached_api_call(self, ttl=300):
        """Decorator for caching API calls"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Create cache key
                cache_key = f"{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
                
                # Try cache first
                cached_result = self.cache.get(cache_key)
                if cached_result is not None:
                    return cached_result
                
                # Rate limit API call
                self.rate_limiter.wait_if_needed()
                
                # Make API call
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    
                    # Cache successful result
                    self.cache.set(cache_key, result, ttl)
                    
                    # Log performance
                    duration = time.time() - start_time
                    self.logger.info(f"{func.__name__} took {duration:.2f}s")
                    
                    return result
                    
                except Exception as e:
                    self.logger.error(f"{func.__name__} failed: {e}")
                    raise
            
            return wrapper
        return decorator
    
    def background_task(self, func):
        """Run function in background thread"""
        def run():
            try:
                func()
            except Exception as e:
                self.logger.error(f"Background task failed: {e}")
        
        thread = threading.Thread(target=run, daemon=True)
        thread.start()
        self.background_tasks.append(thread)
    
    def preload_data(self, symbols):
        """Preload data for common symbols"""
        def preload():
            from simple_sparklines import SimpleSparklines
            sparklines = SimpleSparklines()
            
            for symbol in symbols:
                try:
                    sparklines.generate_sparkline_data(symbol)
                    time.sleep(0.1)  # Small delay to avoid overwhelming API
                except Exception as e:
                    self.logger.warning(f"Failed to preload {symbol}: {e}")
        
        self.background_task(preload)
    
    def optimize_database_queries(self):
        """Optimize database performance"""
        from app import db
        
        # Add database indexes if not exists
        try:
            db.engine.execute("""
                CREATE INDEX IF NOT EXISTS idx_stock_symbol ON stock(symbol);
                CREATE INDEX IF NOT EXISTS idx_stock_tracked ON stock(is_tracked);
                CREATE INDEX IF NOT EXISTS idx_trade_created ON trade_journal(created_at);
                CREATE INDEX IF NOT EXISTS idx_forecast_symbol ON forecast_path(symbol);
            """)
        except Exception as e:
            self.logger.warning(f"Database optimization failed: {e}")
    
    def compress_responses(self):
        """Enable response compression"""
        from flask import Flask
        from flask_compress import Compress
        
        try:
            # Enable gzip compression
            app = Flask(__name__)
            Compress(app)
            return True
        except ImportError:
            self.logger.warning("Flask-Compress not available")
            return False
    
    def get_performance_stats(self):
        """Get comprehensive performance statistics"""
        return {
            'cache_stats': self.cache.get_stats(),
            'active_background_tasks': len([t for t in self.background_tasks if t.is_alive()]),
            'memory_usage': self._get_memory_usage(),
            'uptime': time.time() - getattr(self, 'start_time', time.time())
        }
    
    def _get_memory_usage(self):
        """Get current memory usage"""
        try:
            import psutil
            process = psutil.Process(os.getpid())
            return {
                'rss': process.memory_info().rss / 1024 / 1024,  # MB
                'vms': process.memory_info().vms / 1024 / 1024   # MB
            }
        except ImportError:
            return {'rss': 0, 'vms': 0}

# Global performance optimizer instance
perf_optimizer = PerformanceOptimizer()

# Decorator for easy use
def cached_api_call(ttl=300):
    """Decorator for caching API calls with performance optimization"""
    return perf_optimizer.cached_api_call(ttl)

def optimize_route(func):
    """Decorator to optimize Flask routes"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            
            # Log slow routes
            duration = time.time() - start_time
            if duration > 2.0:  # Warn about routes taking > 2 seconds
                logging.warning(f"Slow route {func.__name__}: {duration:.2f}s")
            
            return result
            
        except Exception as e:
            logging.error(f"Route {func.__name__} failed: {e}")
            raise
    
    return wrapper

class LazyLoader:
    """Lazy loading for expensive operations"""
    
    def __init__(self):
        self._loaded = {}
        self._loading = set()
        self.lock = threading.Lock()
    
    def load_when_needed(self, key, loader_func):
        """Load data only when needed"""
        with self.lock:
            if key in self._loaded:
                return self._loaded[key]
            
            if key in self._loading:
                # Wait for other thread to finish loading
                while key in self._loading:
                    time.sleep(0.01)
                return self._loaded.get(key)
            
            # Mark as loading
            self._loading.add(key)
        
        try:
            # Load data
            result = loader_func()
            
            with self.lock:
                self._loaded[key] = result
                self._loading.discard(key)
            
            return result
            
        except Exception as e:
            with self.lock:
                self._loading.discard(key)
            raise

# Global lazy loader
lazy_loader = LazyLoader()