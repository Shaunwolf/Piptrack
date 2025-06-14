"""
Database Performance Optimizer for CandleCast
Implements connection pooling, query optimization, and index management
"""

import logging
from sqlalchemy import text, event
from sqlalchemy.engine import Engine
from sqlalchemy.pool import QueuePool
import time
import threading
from contextlib import contextmanager

class DatabaseOptimizer:
    """Optimizes database performance for production deployment"""
    
    def __init__(self, app=None):
        self.app = app
        self.query_times = []
        self.slow_queries = []
        self.connection_pool_stats = {}
        self.lock = threading.Lock()
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize database optimizations for Flask app"""
        self.app = app
        
        # Configure connection pooling
        self._configure_connection_pool()
        
        # Add query monitoring
        self._setup_query_monitoring()
        
        # Create database indexes
        self._create_performance_indexes()
        
        logging.info("Database optimizer initialized")
    
    def _configure_connection_pool(self):
        """Configure optimized connection pooling"""
        if not self.app:
            return
            
        # Update database configuration for production
        pool_config = {
            'poolclass': QueuePool,
            'pool_size': 10,          # Number of connections to maintain
            'max_overflow': 20,       # Additional connections when pool is full
            'pool_pre_ping': True,    # Validate connections before use
            'pool_recycle': 3600,     # Recycle connections every hour
            'pool_timeout': 30,       # Wait time for connection
        }
        
        # Apply to existing engine if available
        try:
            from app import db
            if hasattr(db.engine, 'pool'):
                for key, value in pool_config.items():
                    if key != 'poolclass':
                        setattr(db.engine.pool, key.replace('pool_', ''), value)
        except Exception as e:
            logging.warning(f"Could not configure connection pool: {e}")
    
    def _setup_query_monitoring(self):
        """Setup query performance monitoring"""
        @event.listens_for(Engine, "before_cursor_execute")
        def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            context._query_start_time = time.time()
        
        @event.listens_for(Engine, "after_cursor_execute")
        def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            total = time.time() - context._query_start_time
            
            with self.lock:
                self.query_times.append(total)
                
                # Keep only last 1000 queries
                if len(self.query_times) > 1000:
                    self.query_times = self.query_times[-1000:]
                
                # Track slow queries (>1 second)
                if total > 1.0:
                    self.slow_queries.append({
                        'query': statement[:500],  # Truncate long queries
                        'time': total,
                        'timestamp': time.time()
                    })
                    
                    # Keep only last 50 slow queries
                    if len(self.slow_queries) > 50:
                        self.slow_queries = self.slow_queries[-50:]
                    
                    logging.warning(f"Slow query detected: {total:.2f}s - {statement[:100]}...")
    
    def _create_performance_indexes(self):
        """Create database indexes for better performance"""
        indexes = [
            # Stock table indexes
            "CREATE INDEX IF NOT EXISTS idx_stock_symbol ON stock(symbol);",
            "CREATE INDEX IF NOT EXISTS idx_stock_tracked ON stock(is_tracked);",
            "CREATE INDEX IF NOT EXISTS idx_stock_updated ON stock(last_updated);",
            
            # TradeJournal indexes
            "CREATE INDEX IF NOT EXISTS idx_trade_created ON trade_journal(created_at);",
            "CREATE INDEX IF NOT EXISTS idx_trade_symbol ON trade_journal(symbol);",
            "CREATE INDEX IF NOT EXISTS idx_trade_status ON trade_journal(status);",
            
            # ForecastPath indexes
            "CREATE INDEX IF NOT EXISTS idx_forecast_symbol ON forecast_path(symbol);",
            "CREATE INDEX IF NOT EXISTS idx_forecast_created ON forecast_path(created_at);",
            
            # AIAnalysis indexes
            "CREATE INDEX IF NOT EXISTS idx_analysis_symbol ON ai_analysis(symbol);",
            "CREATE INDEX IF NOT EXISTS idx_analysis_created ON ai_analysis(created_at);",
            
            # PatternEvolution indexes
            "CREATE INDEX IF NOT EXISTS idx_pattern_symbol ON pattern_evolution(symbol);",
            "CREATE INDEX IF NOT EXISTS idx_pattern_stage ON pattern_evolution(current_stage);",
        ]
        
        try:
            from app import db
            for index_sql in indexes:
                try:
                    db.session.execute(text(index_sql))
                    db.session.commit()
                except Exception as e:
                    logging.warning(f"Failed to create index: {e}")
                    db.session.rollback()
        except Exception as e:
            logging.error(f"Database index creation failed: {e}")
    
    def optimize_query_cache(self):
        """Optimize database query cache settings"""
        cache_settings = [
            "SET shared_preload_libraries = 'pg_stat_statements';",
            "SET track_activity_query_size = 2048;",
            "SET log_min_duration_statement = 1000;",  # Log queries > 1s
        ]
        
        try:
            from app import db
            for setting in cache_settings:
                try:
                    db.session.execute(text(setting))
                except Exception as e:
                    logging.debug(f"Cache setting not applied: {e}")
        except Exception as e:
            logging.warning(f"Query cache optimization failed: {e}")
    
    @contextmanager
    def optimized_session(self):
        """Context manager for optimized database sessions"""
        try:
            from app import db
            # Use autocommit=False for better performance in transactions
            session = db.session
            yield session
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()
    
    def batch_insert(self, model_class, data_list, batch_size=100):
        """Optimized batch insert for large datasets"""
        try:
            from app import db
            
            for i in range(0, len(data_list), batch_size):
                batch = data_list[i:i + batch_size]
                db.session.bulk_insert_mappings(model_class, batch)
                db.session.commit()
                
        except Exception as e:
            db.session.rollback()
            logging.error(f"Batch insert failed: {e}")
            raise
    
    def cleanup_old_data(self, days=30):
        """Clean up old data to maintain performance"""
        cleanup_queries = [
            f"DELETE FROM ai_analysis WHERE created_at < NOW() - INTERVAL '{days} days';",
            f"DELETE FROM forecast_path WHERE created_at < NOW() - INTERVAL '{days} days';",
            f"DELETE FROM pattern_evolution WHERE updated_at < NOW() - INTERVAL '{days * 2} days';",
        ]
        
        try:
            from app import db
            for query in cleanup_queries:
                result = db.session.execute(text(query))
                logging.info(f"Cleaned up {result.rowcount} old records")
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logging.error(f"Data cleanup failed: {e}")
    
    def get_performance_stats(self):
        """Get database performance statistics"""
        with self.lock:
            avg_query_time = sum(self.query_times) / max(len(self.query_times), 1)
            
            return {
                'average_query_time': avg_query_time,
                'total_queries': len(self.query_times),
                'slow_queries_count': len(self.slow_queries),
                'recent_slow_queries': self.slow_queries[-5:],
                'connection_pool': self._get_pool_stats()
            }
    
    def _get_pool_stats(self):
        """Get connection pool statistics"""
        try:
            from app import db
            pool = db.engine.pool
            
            return {
                'size': getattr(pool, 'size', 0),
                'checked_in': getattr(pool, 'checkedin', 0),
                'checked_out': getattr(pool, 'checkedout', 0),
                'overflow': getattr(pool, 'overflow', 0),
            }
        except Exception:
            return {'error': 'Pool stats unavailable'}
    
    def analyze_table_sizes(self):
        """Analyze table sizes for optimization insights"""
        try:
            from app import db
            
            size_query = text("""
                SELECT 
                    schemaname as schema,
                    tablename as table,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                    pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
                FROM pg_tables 
                WHERE schemaname NOT IN ('information_schema', 'pg_catalog')
                ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
            """)
            
            result = db.session.execute(size_query)
            return [dict(row) for row in result]
            
        except Exception as e:
            logging.error(f"Table size analysis failed: {e}")
            return []
    
    def optimize_vacuum(self):
        """Run VACUUM ANALYZE for table optimization"""
        try:
            from app import db
            
            # Get all table names
            tables_query = text("""
                SELECT tablename FROM pg_tables 
                WHERE schemaname = 'public';
            """)
            
            result = db.session.execute(tables_query)
            tables = [row[0] for row in result]
            
            # Run VACUUM ANALYZE on each table
            for table in tables:
                try:
                    db.session.execute(text(f"VACUUM ANALYZE {table};"))
                    db.session.commit()
                except Exception as e:
                    logging.warning(f"VACUUM failed for {table}: {e}")
                    
        except Exception as e:
            logging.error(f"Database vacuum failed: {e}")

# Global database optimizer instance
db_optimizer = DatabaseOptimizer()

def initialize_database_optimizations(app):
    """Initialize database optimizations for the Flask app"""
    db_optimizer.init_app(app)
    return db_optimizer