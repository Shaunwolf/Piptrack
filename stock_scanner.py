import yfinance as yf
import pandas as pd
import numpy as np
import ta
from datetime import datetime, timedelta
import logging

class StockScanner:
    def __init__(self):
        self.top_gappers = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX', 
            'AMD', 'BABA', 'CRM', 'ORCL', 'ADBE', 'PYPL', 'INTC', 'CSCO',
            'PFE', 'JNJ', 'KO', 'PEP', 'WMT', 'HD', 'BAC', 'JPM', 'V', 'MA'
        ]
    
    def scan_top_gappers(self, limit=20):
        """Scan for top gapping stocks"""
        results = []
        
        try:
            for symbol in self.top_gappers[:limit]:
                try:
                    stock_data = self.get_stock_data(symbol)
                    if stock_data:
                        results.append(stock_data)
                except Exception as e:
                    logging.warning(f"Error scanning {symbol}: {e}")
                    continue
            
            # Sort by gap percentage (volume spike as proxy)
            results.sort(key=lambda x: x.get('volume_spike', 0), reverse=True)
            
        except Exception as e:
            logging.error(f"Error in scan_top_gappers: {e}")
        
        return results
    
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
