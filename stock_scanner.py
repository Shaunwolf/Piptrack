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
    
    def get_stock_quote_alpha_vantage(self, symbol):
        """Get real-time stock quote from Alpha Vantage API with rate limit handling"""
        try:
            if not self.api_key:
                logging.error("Alpha Vantage API key not found")
                return None
                
            url = f"{self.base_url}?function=GLOBAL_QUOTE&symbol={symbol}&apikey={self.api_key}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for rate limit message
                if 'Note' in data and 'API rate limit' in data['Note']:
                    logging.warning(f"Alpha Vantage rate limit exceeded for {symbol}")
                    return None
                
                quote = data.get('Global Quote', {})
                
                if quote and quote.get('05. price'):
                    return {
                        'symbol': quote.get('01. symbol', symbol),
                        'price': float(quote.get('05. price', 0)),
                        'change': float(quote.get('09. change', 0)),
                        'change_percent': quote.get('10. change percent', '0%').replace('%', ''),
                        'volume': int(quote.get('06. volume', 0))
                    }
                else:
                    logging.warning(f"No valid quote data received for {symbol}")
                    
            else:
                logging.error(f"Alpha Vantage API error {response.status_code} for {symbol}")
                
        except Exception as e:
            logging.error(f"Error fetching quote for {symbol}: {e}")
        
        return None
    
    def get_technical_indicators_alpha_vantage(self, symbol):
        """Get RSI and other technical indicators from Alpha Vantage"""
        try:
            if not self.api_key:
                return {'rsi': 50}
                
            url = f"{self.base_url}?function=RSI&symbol={symbol}&interval=daily&time_period=14&series_type=close&apikey={self.api_key}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                rsi_data = data.get('Technical Analysis: RSI', {})
                
                if rsi_data:
                    # Get most recent RSI value
                    latest_date = max(rsi_data.keys())
                    rsi_value = float(rsi_data[latest_date]['RSI'])
                    return {'rsi': rsi_value}
            
            time.sleep(1)  # Rate limiting
            
        except Exception as e:
            logging.error(f"Error fetching RSI for {symbol}: {e}")
        
        return {'rsi': 50}  # Default RSI value
    
    def get_company_overview_alpha_vantage(self, symbol):
        """Get company information from Alpha Vantage"""
        try:
            if not self.api_key:
                return {'name': symbol, 'sector': 'Unknown'}
                
            url = f"{self.base_url}?function=OVERVIEW&symbol={symbol}&apikey={self.api_key}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'name': data.get('Name', symbol),
                    'sector': data.get('Sector', 'Unknown'),
                    'market_cap': int(data.get('MarketCapitalization', 0)) if data.get('MarketCapitalization') else 0
                }
                
        except Exception as e:
            logging.error(f"Error fetching overview for {symbol}: {e}")
        
        return {'name': symbol, 'sector': 'Unknown', 'market_cap': 0}
    
    def scan_top_gappers(self, limit=15):
        """Scan for top gapping stocks in $1-$50 price range with fallback to yfinance"""
        results = []
        
        # Expanded list of symbols covering various sectors and price ranges
        scan_symbols = [
            # Technology
            'INTC', 'AMD', 'MU', 'QCOM', 'TXN', 'ADI', 'MRVL', 'KLAC', 'LRCX', 'AMAT',
            # Financial
            'BAC', 'WFC', 'C', 'JPM', 'GS', 'MS', 'COF', 'AXP', 'USB', 'PNC',
            # Energy  
            'CVX', 'XOM', 'COP', 'EOG', 'SLB', 'HAL', 'OXY', 'KMI', 'WMB', 'EPD',
            # Industrial
            'CAT', 'DE', 'BA', 'GE', 'HON', 'MMM', 'LMT', 'RTX', 'UNP', 'CSX',
            # Healthcare
            'PFE', 'JNJ', 'MRK', 'ABT', 'TMO', 'DHR', 'BMY', 'AMGN', 'GILD', 'BIIB',
            # Consumer
            'WMT', 'HD', 'PG', 'KO', 'PEP', 'NKE', 'COST', 'TGT', 'LOW', 'SBUX',
            # Telecommunications
            'T', 'VZ', 'TMUS', 'CHTR', 'CMCSA',
            # Materials
            'LIN', 'APD', 'ECL', 'FCX', 'NEM', 'AA', 'CLF', 'X', 'NUE', 'STLD',
            # Utilities
            'NEE', 'DUK', 'SO', 'D', 'EXC', 'XEL', 'WEC', 'ES', 'AEP', 'PPL',
            # REITs & Real Estate  
            'AMT', 'PLD', 'CCI', 'EQIX', 'PSA', 'EXR', 'AVB', 'EQR', 'DLR', 'O',
            # Transportation
            'UPS', 'FDX', 'DAL', 'UAL', 'AAL', 'LUV', 'JBLU', 'ALK',
            # Retail
            'BBY', 'M', 'KSS', 'JWN', 'GPS', 'ANF', 'AEO', 'URBN',
            # Automotive
            'F', 'GM', 'RIVN', 'LCID', 'FSLY', 'GOEV',
            # Small-Mid Cap Growth
            'SOFI', 'PLTR', 'WISH', 'CLOV', 'SPCE', 'NKLA', 'RIDE', 'WKHS'
        ]
        
        try:
            # Collect all candidates with price changes
            candidates = []
            
            for symbol in scan_symbols:
                try:
                    # Use yfinance for comprehensive data
                    stock_data = self.get_stock_data(symbol)
                    
                    if stock_data:
                        current_price = stock_data['price']
                        
                        # Filter for $1-$50 price range
                        if not (1.0 <= current_price <= 50.0):
                            continue
                            
                        # Calculate gapping score based on price change and volume
                        price_change = abs(stock_data.get('change_percent', 0))
                        volume_spike = abs(stock_data.get('volume_spike', 0))
                        confidence = stock_data.get('confidence_score', 0)
                        
                        # Gapping score combines price movement, volume, and confidence
                        gap_score = (price_change * 2) + (volume_spike * 0.5) + (confidence * 0.3)
                        stock_data['gap_score'] = gap_score
                        
                        candidates.append(stock_data)
                        logging.info(f"Scanned {symbol}: ${current_price:.2f}, change: {price_change:.1f}%, gap_score: {gap_score:.1f}")
                        
                except Exception as e:
                    logging.error(f"Error scanning {symbol}: {e}")
                    continue
            
            # Sort by gap score and select top performers
            candidates.sort(key=lambda x: x['gap_score'], reverse=True)
            results = candidates[:limit]
            
            
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
