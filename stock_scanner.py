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
    
    def scan_top_gappers(self, limit=50):
        """Scan for top gapping stocks in $1-$25 price range with optimized processing"""
        results = []
        
        # Carefully selected symbols known to trade in $1-$25 range
        scan_symbols = [
            # Financial - Under $25
            'F', 'T', 'BAC', 'WFC', 'C', 'KEY', 'RF', 'ZION', 'FITB', 'HBAN',
            # Energy & Materials - Under $25  
            'CLF', 'X', 'AA', 'HAL', 'SLB', 'OXY', 'KMI', 'ET', 'AR', 'MRO',
            # Technology - Lower Priced
            'INTC', 'AMD', 'MU', 'SIRI', 'NOK', 'HPQ', 'WDC', 'QCOM', 'TXN', 'MRVL',
            # Airlines & Transportation
            'DAL', 'UAL', 'AAL', 'LUV', 'JBLU', 'ALK', 'SAVE', 'SKYW', 'MESA', 'HA',
            # Retail & Consumer
            'M', 'KSS', 'GPS', 'ANF', 'AEO', 'URBN', 'JWN', 'EXPR', 'DDS', 'KIRK',
            # Small-Cap Growth
            'SOFI', 'PLTR', 'WISH', 'CLOV', 'SPCE', 'NKLA', 'RIDE', 'WKHS', 'GOEV', 'LCID',
            # Energy Services & Exploration
            'FANG', 'DVN', 'CNX', 'HES', 'APA', 'OVV', 'MTDR', 'SM', 'CTRA', 'EQT',
            # Cannabis & Biotech
            'SNDL', 'TLRY', 'CGC', 'ACB', 'HEXO', 'CRON', 'APHA', 'TEVA', 'GILD', 'BMY',
            # Meme & Penny Stocks
            'AMC', 'GME', 'KOSS', 'EXPR', 'NAKD', 'CINE', 'GNUS', 'IDEX', 'XSPA', 'SHIP',
            # Clean Energy & EV
            'FCEL', 'PLUG', 'BLDP', 'HYLN', 'QS', 'CHPT', 'BLNK', 'EVGO', 'CLSK', 'MARA'
        ]
        
        try:
            # Collect all candidates with price changes
            candidates = []
            
            for symbol in scan_symbols:
                try:
                    # Quick price check first to avoid heavy processing
                    ticker = yf.Ticker(symbol)
                    try:
                        info = ticker.info
                        current_price = info.get('currentPrice') or info.get('regularMarketPrice', 0)
                        
                        # Skip if price is outside $1-$25 range or unavailable
                        if not current_price or not (1.0 <= current_price <= 25.0):
                            logging.info(f"Skipping {symbol}: price ${current_price} outside $1-$25 range")
                            continue
                            
                    except Exception as e:
                        logging.warning(f"Could not get price for {symbol}: {e}")
                        continue
                    
                    # Get comprehensive data only for valid price range stocks
                    stock_data = self.get_stock_data(symbol)
                    
                    if stock_data:
                        # Double-check price from comprehensive data
                        final_price = stock_data['price']
                        if not (1.0 <= final_price <= 25.0):
                            logging.info(f"Final filter: {symbol} price ${final_price} outside range")
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
        """Get comprehensive stock data for analysis with error handling"""
        try:
            ticker = yf.Ticker(symbol)
            
            # Get historical data with timeout and error handling
            try:
                hist = ticker.history(period="1mo", timeout=10)
                if hist.empty or len(hist) < 5:
                    logging.warning(f"Insufficient data for {symbol}")
                    return None
            except Exception as e:
                logging.warning(f"Failed to get history for {symbol}: {e}")
                return None
            
            # Get basic info with fallback
            current_price = hist['Close'].iloc[-1]
            if pd.isna(current_price) or current_price <= 0:
                return None
            
            try:
                info = ticker.info
            except:
                info = {}  # Use empty dict if info fails
            
            # Calculate RSI manually since ta library has issues
            try:
                closes = hist['Close']
                delta = closes.diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs))
                rsi = rsi.iloc[-1]
                if pd.isna(rsi) or rsi < 0 or rsi > 100:
                    rsi = 50
            except:
                rsi = 50
            
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
