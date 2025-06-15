import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import requests
import os
import time
from pattern_evolution_tracker import PatternEvolutionTracker
from confidence_scorer import ConfidenceScorer

class StockScanner:
    def __init__(self):
        self.api_key = os.environ.get('ALPHA_VANTAGE_API_KEY')
        self.base_url = 'https://www.alphavantage.co/query'
        self.pattern_tracker = PatternEvolutionTracker()
        self.confidence_scorer = ConfidenceScorer()
        
        # Curated list of active stocks in $1-$50 range
        self.top_gappers = [
            # Tech & Growth
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'AMD', 'NFLX', 'CRM',
            'ADBE', 'ORCL', 'INTC', 'CSCO', 'PYPL', 'UBER', 'LYFT', 'SNAP', 'TWTR', 'ZOOM',
            
            # Biotech & Healthcare
            'BIIB', 'GILD', 'AMGN', 'CELG', 'VRTX', 'REGN', 'ILMN', 'MRNA', 'BNTX', 'PFE',
            'JNJ', 'MRK', 'ABT', 'BMY', 'LLY', 'ABBV', 'TMO', 'DHR', 'SYK', 'MDT',
            
            # Financial Services
            'JPM', 'BAC', 'WFC', 'C', 'GS', 'MS', 'USB', 'PNC', 'TFC', 'COF',
            'AXP', 'BLK', 'SCHW', 'SPGI', 'ICE', 'CME', 'NDAQ', 'MCO', 'V', 'MA',
            
            # Consumer & Retail
            'WMT', 'TGT', 'COST', 'HD', 'LOW', 'NKE', 'SBUX', 'MCD', 'DIS', 'NFLX',
            'KO', 'PEP', 'PG', 'UL', 'CL', 'KMB', 'GIS', 'K', 'CPB', 'CAG',
            
            # Energy & Materials
            'XOM', 'CVX', 'COP', 'EOG', 'SLB', 'HAL', 'OXY', 'DVN', 'MPC', 'VLO',
            'FCX', 'NEM', 'GOLD', 'ABX', 'AA', 'X', 'CLF', 'MT', 'VALE', 'BHP',
            
            # Industrial & Transportation
            'BA', 'CAT', 'DE', 'GE', 'HON', 'MMM', 'LMT', 'RTX', 'UPS', 'FDX',
            'UNP', 'CSX', 'NSC', 'KSU', 'CNI', 'CP', 'EXPD', 'CHRW', 'XPO', 'JBHT',
            
            # Real Estate & Utilities
            'PLD', 'AMT', 'CCI', 'EQIX', 'DLR', 'PSA', 'EXR', 'AVB', 'EQR', 'UDR',
            'NEE', 'SO', 'DUK', 'AEP', 'EXC', 'XEL', 'PPL', 'ED', 'ES', 'PEG'
        ]
        
    def get_top_gainers_losers(self, limit=20):
        """Get top gainers and losers from Alpha Vantage API"""
        try:
            if not self.api_key:
                logging.warning("Alpha Vantage API key not found, using fallback list")
                return self.get_fallback_stocks(limit)
            
            url = f"{self.base_url}?function=TOP_GAINERS_LOSERS&apikey={self.api_key}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                gainers = data.get('top_gainers', [])[:limit//2]
                losers = data.get('top_losers', [])[:limit//2]
                
                combined = []
                for stock in gainers + losers:
                    ticker = stock.get('ticker', '').replace('.', '-')
                    if self.is_valid_ticker(ticker):
                        combined.append(ticker)
                
                return combined[:limit]
            else:
                logging.warning(f"API request failed: {response.status_code}")
                return self.get_fallback_stocks(limit)
                
        except Exception as e:
            logging.error(f"Error fetching top gainers/losers: {e}")
            return self.get_fallback_stocks(limit)
    
    def get_fallback_stocks(self, limit=20):
        """Get curated list of active stocks when API fails"""
        # Return randomized subset of curated stocks
        import random
        random.shuffle(self.top_gappers)
        return self.top_gappers[:limit]
    
    def is_valid_ticker(self, ticker):
        """Validate ticker format and common criteria"""
        if not ticker or len(ticker) > 5:
            return False
        
        # Filter out common invalid patterns
        invalid_patterns = ['.', '_', ' ', 'WARRANT', 'UNIT', 'RIGHT']
        for pattern in invalid_patterns:
            if pattern in ticker.upper():
                return False
        
        return True
    
    def get_stock_data(self, symbol, period="3mo"):
        """Get historical stock data with enhanced error handling"""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period)
            
            if hist.empty:
                logging.warning(f"No data available for {symbol}")
                return None
            
            # Validate data quality
            if len(hist) < 10:
                logging.warning(f"Insufficient data for {symbol}")
                return None
            
            return hist
            
        except Exception as e:
            logging.error(f"Error fetching data for {symbol}: {e}")
            return None
    
    def analyze_stock(self, symbol):
        """Comprehensive stock analysis with multiple timeframes"""
        try:
            hist = self.get_stock_data(symbol)
            if hist is None:
                return None
            
            current_price = hist['Close'].iloc[-1]
            
            # Price filters
            if current_price < 1 or current_price > 500:
                return None
            
            # Volume filter - ensure adequate liquidity
            avg_volume = hist['Volume'].mean()
            if avg_volume < 100000:  # Minimum 100k average volume
                return None
            
            # RSI calculation with pandas
            try:
                delta = hist['Close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs))
                rsi_value = rsi.iloc[-1] if hasattr(rsi, 'iloc') and len(rsi) > 0 else 50
                if pd.isna(rsi_value) or rsi_value < 0 or rsi_value > 100:
                    rsi_value = 50
            except:
                rsi_value = 50
            
            # Volume analysis
            avg_volume_series = hist['Volume'].rolling(20).mean()
            avg_volume = avg_volume_series.iloc[-2] if len(avg_volume_series) > 1 else hist['Volume'].mean()
            current_volume = hist['Volume'].iloc[-1]
            volume_spike = ((current_volume - avg_volume) / avg_volume * 100) if avg_volume > 0 else 0
            
            # Pattern detection
            pattern_type = self.detect_pattern(hist)
            
            # Fibonacci analysis
            fibonacci_position = self.calculate_fibonacci_position(hist)
            
            # Confidence scoring
            confidence_score = self.confidence_scorer.calculate_confidence({
                'rsi': rsi_value,
                'volume_spike': volume_spike,
                'pattern_type': pattern_type,
                'fibonacci_position': fibonacci_position,
                'price': current_price
            })
            
            return {
                'symbol': symbol,
                'price': round(current_price, 2),
                'rsi': round(rsi_value, 2),
                'volume_spike': round(volume_spike, 2),
                'pattern_type': pattern_type,
                'fibonacci_position': round(fibonacci_position, 3),
                'confidence_score': round(confidence_score, 2),
                'volume': int(current_volume),
                'avg_volume': int(avg_volume)
            }
            
        except Exception as e:
            logging.error(f"Error analyzing {symbol}: {e}")
            return None
    
    def detect_pattern(self, hist):
        """Simplified pattern detection"""
        try:
            if len(hist) < 20:
                return "insufficient_data"
            
            # Simple moving averages
            sma_5 = hist['Close'].rolling(window=5).mean()
            sma_20 = hist['Close'].rolling(window=20).mean()
            
            current_price = hist['Close'].iloc[-1]
            sma_5_current = sma_5.iloc[-1]
            sma_20_current = sma_20.iloc[-1]
            
            # Pattern classification
            if current_price > sma_5_current > sma_20_current:
                return "uptrend"
            elif current_price < sma_5_current < sma_20_current:
                return "downtrend"
            elif abs(current_price - sma_20_current) / sma_20_current < 0.02:
                return "sideways"
            else:
                return "mixed"
                
        except Exception as e:
            logging.error(f"Pattern detection error: {e}")
            return "unknown"
    
    def calculate_fibonacci_position(self, hist):
        """Calculate Fibonacci retracement position"""
        try:
            if len(hist) < 20:
                return 0.5
            
            # Find recent high and low
            lookback = min(20, len(hist))
            recent_data = hist.tail(lookback)
            
            high = recent_data['High'].max()
            low = recent_data['Low'].min()
            current = hist['Close'].iloc[-1]
            
            if high == low:
                return 0.5
            
            # Calculate position in range (0 = low, 1 = high)
            position = (current - low) / (high - low)
            return max(0, min(1, position))
            
        except Exception as e:
            logging.error(f"Fibonacci calculation error: {e}")
            return 0.5
    
    def scan_stocks(self, symbols=None, max_results=50):
        """Main scanning function with performance optimization"""
        if symbols is None:
            symbols = self.get_top_gainers_losers(100)  # Get more to filter down
        
        results = []
        processed = 0
        
        for symbol in symbols:
            if processed >= max_results:
                break
                
            try:
                # Rate limiting
                time.sleep(0.1)
                
                analysis = self.analyze_stock(symbol)
                if analysis and analysis['confidence_score'] > 0:
                    results.append(analysis)
                    processed += 1
                    
            except Exception as e:
                logging.error(f"Error processing {symbol}: {e}")
                continue
        
        # Sort by confidence score
        results.sort(key=lambda x: x['confidence_score'], reverse=True)
        
        return results[:max_results]
    
    def get_pattern_evolution(self, symbol):
        """Get pattern evolution data for detailed analysis"""
        try:
            return self.pattern_tracker.track_pattern_evolution(symbol)
        except Exception as e:
            logging.error(f"Pattern evolution error for {symbol}: {e}")
            return None