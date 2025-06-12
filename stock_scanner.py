import yfinance as yf
import pandas as pd
import numpy as np
import ta
from datetime import datetime, timedelta
import logging
import requests
import os
import time

class StockScanner:
    def __init__(self):
        self.api_key = os.environ.get('ALPHA_VANTAGE_API_KEY')
        self.base_url = 'https://www.alphavantage.co/query'
        
        # Expanded list focusing on $1-$50 price range stocks
        self.top_gappers = [
            # Tech stocks in range
            'AMD', 'INTC', 'MU', 'QCOM', 'TXN', 'AMAT', 'LRCX', 'KLAC', 'MCHP', 'SWKS',
            'MRVL', 'NXPI', 'TSM', 'ASML', 'CSCO', 'ORCL', 'IBM', 'HPQ', 'DELL', 'WDC',
            
            # Energy stocks 
            'XOM', 'CVX', 'COP', 'EOG', 'SLB', 'HAL', 'OXY', 'DVN', 'FANG', 'MRO',
            'APA', 'EQT', 'CTRA', 'AR', 'CNX', 'RRC', 'CLR', 'PXD', 'MTDR', 'HES',
            
            # Financial stocks
            'BAC', 'WFC', 'C', 'GS', 'MS', 'COF', 'AXP', 'USB', 'PNC', 'TFC',
            'RF', 'ZION', 'CMA', 'HBAN', 'CFG', 'FITB', 'KEY', 'MTB', 'STI', 'BBT',
            
            # Healthcare/biotech
            'PFE', 'MRK', 'BMY', 'ABBV', 'GILD', 'BIIB', 'AMGN', 'REGN', 'VRTX', 'ILMN',
            'MRNA', 'BNTX', 'JNJ', 'UNH', 'CVS', 'CI', 'HUM', 'ANTM', 'CNC', 'MOH',
            
            # Industrial/materials
            'CAT', 'DE', 'BA', 'HON', 'MMM', 'GE', 'LMT', 'RTX', 'UPS', 'FDX',
            'AA', 'FCX', 'NEM', 'VALE', 'RIO', 'BHP', 'CLF', 'X', 'STLD', 'NUE',
            
            # Consumer stocks
            'F', 'GM', 'NIO', 'RIVN', 'LCID', 'KO', 'PEP', 'SBUX', 'NKE', 'LULU',
            'TGT', 'BBY', 'GPS', 'ANF', 'M', 'JWN', 'COST', 'WMT', 'HD', 'LOW',
            
            # REITs and utilities in range
            'SPG', 'O', 'REIT', 'EXR', 'PSA', 'DLR', 'CCI', 'AMT', 'EQIX', 'PLD',
            'NEE', 'SO', 'DUK', 'AEP', 'EXC', 'XEL', 'ED', 'ETR', 'ES', 'FE'
        ]
    
    def scan_top_gappers(self, limit=25):
        """Scan for top gapping stocks in $1-$50 price range"""
        results = []
        
        # Priority stocks likely in $1-$50 range
        priority_symbols = [
            'AMD', 'INTC', 'MU', 'BAC', 'WFC', 'F', 'PFE', 'XOM', 
            'CVX', 'SLB', 'HAL', 'AA', 'FCX', 'CLF', 'T', 'VZ'
        ]
        
        try:
            # Use batch processing for faster data retrieval
            for i in range(0, min(len(priority_symbols), limit * 2), 4):
                batch = priority_symbols[i:i+4]
                
                for symbol in batch:
                    try:
                        # Quick data fetch with minimal history
                        ticker = yf.Ticker(symbol)
                        
                        # Get current price from basic quote
                        quote = ticker.fast_info
                        if hasattr(quote, 'last_price') and quote.last_price:
                            current_price = float(quote.last_price)
                        else:
                            # Fallback to history if fast_info fails
                            hist = ticker.history(period="2d")
                            if hist.empty:
                                continue
                            current_price = float(hist['Close'].iloc[-1])
                        
                        # Filter for $1-$50 price range
                        if not (1.0 <= current_price <= 50.0):
                            continue
                        
                        # Get basic info
                        info = ticker.info
                        
                        # Calculate basic volume spike from recent data
                        hist = ticker.history(period="5d")
                        if not hist.empty and len(hist) >= 2:
                            volume_current = float(hist['Volume'].iloc[-1])
                            volume_avg = float(hist['Volume'].mean())
                            volume_spike = (volume_current / volume_avg) * 100 if volume_avg > 0 else 100
                            
                            # Calculate RSI
                            closes = hist['Close']
                            delta = closes.diff()
                            gain = delta.where(delta > 0, 0).mean()
                            loss = (-delta.where(delta < 0, 0)).mean()
                            rs = gain / loss if loss != 0 else 100
                            rsi = 100 - (100 / (1 + rs))
                        else:
                            volume_spike = 100
                            rsi = 50
                        
                        results.append({
                            'symbol': symbol,
                            'name': info.get('longName', symbol),
                            'price': round(current_price, 2),
                            'rsi': round(float(rsi), 2) if not pd.isna(rsi) else 50,
                            'volume_spike': round(volume_spike, 2),
                            'pattern_type': self.detect_pattern(hist) if not hist.empty else 'Unknown',
                            'fibonacci_position': 50.0,
                            'market_cap': info.get('marketCap', 0),
                            'sector': info.get('sector', 'Unknown')
                        })
                        
                        # Stop if we have enough results
                        if len(results) >= limit:
                            break
                            
                    except Exception as e:
                        logging.warning(f"Error scanning {symbol}: {e}")
                        continue
                
                # Break if we have enough results
                if len(results) >= limit:
                    break
            
            # Sort by volume spike (gap indicator)
            results.sort(key=lambda x: x.get('volume_spike', 0), reverse=True)
            
        except Exception as e:
            logging.error(f"Error in scan_top_gappers: {e}")
        
        return results[:limit]
    
    def scan_selected_tickers(self, tickers):
        """Scan specific tickers"""
        results = []
        
        for symbol in tickers:
            try:
                stock_data = self.get_stock_data(symbol)
                if stock_data:
                    results.append(stock_data)
            except Exception as e:
                logging.warning(f"Error scanning {symbol}: {e}")
                continue
        
        return results
    
    def get_stock_data(self, symbol):
        """Get comprehensive stock data for analysis"""
        try:
            ticker = yf.Ticker(symbol)
            
            # Get historical data (30 days)
            hist = ticker.history(period="1mo")
            if hist.empty:
                return None
            
            # Get basic info
            info = ticker.info
            current_price = hist['Close'].iloc[-1]
            
            # Calculate technical indicators
            rsi = ta.momentum.RSIIndicator(hist['Close']).rsi().iloc[-1]
            
            # Volume analysis
            avg_volume = hist['Volume'].rolling(20).mean().iloc[-2]  # Previous 20-day average
            current_volume = hist['Volume'].iloc[-1]
            volume_spike = ((current_volume - avg_volume) / avg_volume * 100) if avg_volume > 0 else 0
            
            # Pattern detection (simplified)
            pattern_type = self.detect_pattern(hist)
            
            # Fibonacci analysis
            fibonacci_position = self.calculate_fibonacci_position(hist)
            
            return {
                'symbol': symbol,
                'name': info.get('longName', symbol),
                'price': round(current_price, 2),
                'rsi': round(rsi, 2) if not pd.isna(rsi) else 50,
                'volume_spike': round(volume_spike, 2),
                'pattern_type': pattern_type,
                'fibonacci_position': round(fibonacci_position, 2),
                'market_cap': info.get('marketCap', 0),
                'sector': info.get('sector', 'Unknown')
            }
            
        except Exception as e:
            logging.error(f"Error getting stock data for {symbol}: {e}")
            return None
    
    def detect_pattern(self, hist):
        """Detect chart patterns (simplified implementation)"""
        try:
            # Calculate moving averages
            hist['SMA_20'] = hist['Close'].rolling(20).mean()
            hist['SMA_50'] = hist['Close'].rolling(50).mean()
            
            current_price = hist['Close'].iloc[-1]
            sma_20 = hist['SMA_20'].iloc[-1]
            sma_50 = hist['SMA_50'].iloc[-1]
            
            # Simple pattern detection
            if current_price > sma_20 > sma_50:
                return "Bullish Trend"
            elif current_price < sma_20 < sma_50:
                return "Bearish Trend"
            elif abs(current_price - sma_20) / sma_20 < 0.02:
                return "Consolidation"
            else:
                return "Neutral"
                
        except Exception as e:
            logging.error(f"Error detecting pattern: {e}")
            return "Unknown"
    
    def calculate_fibonacci_position(self, hist):
        """Calculate current price position relative to Fibonacci levels"""
        try:
            # Use recent high and low (20 days)
            recent_data = hist.tail(20)
            high = recent_data['High'].max()
            low = recent_data['Low'].min()
            current = hist['Close'].iloc[-1]
            
            if high == low:
                return 50  # Neutral position
            
            # Calculate position as percentage from low to high
            position = ((current - low) / (high - low)) * 100
            return max(0, min(100, position))
            
        except Exception as e:
            logging.error(f"Error calculating Fibonacci position: {e}")
            return 50
