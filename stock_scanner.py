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
                
                if isinstance(rsi, pd.Series) and len(rsi) > 0:
                    rsi_value = rsi.iloc[-1]
                    if pd.isna(rsi_value) or rsi_value < 0 or rsi_value > 100:
                        rsi_value = 50
                else:
                    rsi_value = 50
            except:
                rsi_value = 50
            
            # Volume analysis
            avg_volume_series = hist['Volume'].rolling(20).mean()
            if isinstance(avg_volume_series, pd.Series) and len(avg_volume_series) > 1:
                avg_volume = avg_volume_series.iloc[-2]
            else:
                avg_volume = hist['Volume'].mean()
            current_volume = hist['Volume'].iloc[-1]
            volume_spike = ((current_volume - avg_volume) / avg_volume * 100) if avg_volume > 0 else 0
            
            # Pattern detection
            pattern_type = self.detect_pattern(hist)
            
            # Fibonacci analysis
            fibonacci_position = self.calculate_fibonacci_position(hist)
            
            # Confidence scoring
            confidence_score = self.confidence_scorer.calculate_score({
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
    
    def scan_stocks(self, symbols=None, max_results=20):
        """Main scanning function with access to entire market universe"""
        if symbols is None:
            # Get comprehensive market universe
            symbols = self.get_comprehensive_market_universe(max_results * 10)
        
        results = []
        processed = 0
        
        for symbol in symbols:
            if len(results) >= max_results:
                break
                
            try:
                # Rate limiting
                time.sleep(0.1)
                
                analysis = self.analyze_stock(symbol)
                if analysis and analysis.get('confidence_score', 0) > 30:
                    results.append(analysis)
                    logging.info(f"Scanner found: {symbol} - Confidence: {analysis.get('confidence_score')}")
                    
                processed += 1
                    
            except Exception as e:
                logging.error(f"Error processing {symbol}: {e}")
                continue
        
        # If we still don't have enough results, expand search
        if len(results) < 5:
            extended_symbols = self.get_extended_universe(max_results * 20)
            for symbol in extended_symbols[processed:]:
                if len(results) >= max_results:
                    break
                try:
                    analysis = self.analyze_stock(symbol)
                    if analysis and analysis.get('confidence_score', 0) > 15:
                        results.append(analysis)
                        logging.info(f"Scanner extended: {symbol} - Confidence: {analysis.get('confidence_score')}")
                        time.sleep(0.1)
                except:
                    continue
        
        # Sort by confidence score
        results.sort(key=lambda x: x.get('confidence_score', 0), reverse=True)
        
        logging.info(f"Stock scanner completed. Found {len(results)} stocks from market universe")
        return results[:max_results]
    
    def get_comprehensive_market_universe(self, limit=1000):
        """Get comprehensive stock universe from multiple exchanges"""
        symbols = set()
        
        # S&P 500 symbols
        symbols.update(self.get_sp500_universe())
        
        # NASDAQ listed stocks
        symbols.update(self.get_nasdaq_universe())
        
        # NYSE listed stocks  
        symbols.update(self.get_nyse_universe())
        
        # Russell 2000 small caps
        symbols.update(self.get_small_cap_universe())
        
        # Biotech and pharma universe
        symbols.update(self.get_biotech_universe())
        
        # Crypto-related stocks
        symbols.update(self.get_crypto_stocks())
        
        # Meme stocks and high volume tickers
        symbols.update(self.get_trending_stocks())
        
        # Convert to list and shuffle for diversity
        import random
        symbol_list = list(symbols)
        random.shuffle(symbol_list)
        
        logging.info(f"Loaded comprehensive universe: {len(symbol_list)} symbols")
        return symbol_list[:limit]
    
    def get_sp500_universe(self):
        """Get expanded S&P 500 universe"""
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
    
    def get_nasdaq_universe(self):
        """Get NASDAQ universe including growth stocks"""
        return [
            'AAPL', 'MSFT', 'AMZN', 'TSLA', 'GOOGL', 'GOOG', 'META', 'NVDA', 'NFLX', 'ADBE',
            'PYPL', 'INTC', 'CSCO', 'CMCSA', 'PEP', 'COST', 'AVGO', 'TXN', 'QCOM', 'AMD',
            'INTU', 'TMUS', 'AMAT', 'SBUX', 'CHTR', 'ISRG', 'GILD', 'BKNG', 'REGN', 'MU',
            'ADI', 'FISV', 'CSX', 'ATVI', 'MRNA', 'PANW', 'ADP', 'ILMN', 'LRCX', 'MDLZ',
            'KLAC', 'KDP', 'SNPS', 'EXC', 'CDNS', 'MCHP', 'ORLY', 'CTAS', 'BIIB', 'LULU',
            'PLTR', 'SNOW', 'COIN', 'RBLX', 'U', 'DKNG', 'ROKU', 'SQ', 'SHOP', 'PINS'
        ]
    
    def get_nyse_universe(self):
        """Get NYSE universe including traditional stocks"""
        return [
            'BRK.B', 'UNH', 'JNJ', 'XOM', 'JPM', 'V', 'PG', 'HD', 'CVX', 'MA',
            'BAC', 'KO', 'TMO', 'DHR', 'MRK', 'ABT', 'ACN', 'VZ', 'NKE', 'WMT',
            'CRM', 'T', 'NEE', 'WFC', 'MS', 'RTX', 'MDT', 'HON', 'UPS', 'IBM',
            'AMGN', 'LOW', 'CAT', 'DE', 'GS', 'BMY', 'BA', 'SPGI', 'AXP', 'BLK',
            'MMM', 'C', 'CVS', 'MO', 'USB', 'LMT', 'TJX', 'PNC', 'SYK', 'AMT',
            'CI', 'SO', 'FIS', 'CB', 'DUK', 'NSC', 'AON', 'BSX', 'CL', 'F',
            'GM', 'DIS', 'UBER', 'LYFT', 'ABNB', 'DASH', 'TWTR', 'SNAP', 'ZM', 'DOCU'
        ]
    
    def get_small_cap_universe(self):
        """Get small cap and Russell 2000 stocks"""
        return [
            'AMC', 'GME', 'BBBY', 'KOSS', 'EXPR', 'NAKD', 'SNDL', 'NOK', 'BB', 'PLTR',
            'WISH', 'CLOV', 'MVIS', 'TLRY', 'WKHS', 'SKLZ', 'RIDE', 'SPCE', 'RKT', 'SOFI',
            'UWMC', 'OPEN', 'ROOT', 'HOOD', 'AFRM', 'UPST', 'PENN', 'FVRR', 'ETSY', 'PINS',
            'CRSR', 'CRWD', 'ZS', 'OKTA', 'DDOG', 'NET', 'FSLY', 'ESTC', 'TEAM', 'WORK',
            'PTON', 'LMND', 'CVNA', 'OSTK', 'BYND', 'TDOC', 'MRTX', 'SAGE', 'FOLD', 'BLUE'
        ]
    
    def get_biotech_universe(self):
        """Get comprehensive biotech universe"""
        return [
            'MRNA', 'BNTX', 'NVAX', 'OCGN', 'INO', 'VXRT', 'SRNE', 'ATOS', 'CTXR', 'BNGO',
            'SENS', 'OBSV', 'CTIC', 'CPRX', 'CYTH', 'SHIP', 'ADMP', 'PROG', 'RGBP', 'ENZC',
            'VBIV', 'VERU', 'CRTX', 'SAVA', 'AVXL', 'BIIB', 'GILD', 'AMGN', 'VRTX', 'REGN',
            'ILMN', 'TECH', 'TGTX', 'FOLD', 'BLUE', 'EDIT', 'CRSP', 'NTLA', 'BEAM', 'PACB',
            'CDNA', 'NVTA', 'VCYT', 'FATE', 'BMRN', 'RARE', 'MYGN', 'HALO', 'KDNY', 'ZYME',
            'ARQL', 'PTGX', 'AXSM', 'ACAD', 'HZNP', 'INCY', 'EXAS', 'VEEV', 'TDOC', 'DXCM'
        ]
    
    def get_crypto_stocks(self):
        """Get crypto-related stocks"""
        return [
            'COIN', 'MSTR', 'RIOT', 'MARA', 'CAN', 'BTBT', 'EBON', 'SOS', 'DGLY', 'HVBT',
            'ARGO', 'HIVE', 'BITF', 'HUT', 'CLSK', 'EQOS', 'INSG', 'LFUS', 'ANY', 'NCTY',
            'PYPL', 'SQ', 'HOOD', 'SOFI', 'AFRM', 'UPST', 'LC', 'ONDK', 'TREE', 'LMND'
        ]
    
    def get_trending_stocks(self):
        """Get trending and meme stocks"""
        return [
            'SPY', 'QQQ', 'IWM', 'DIA', 'VTI', 'VEA', 'VWO', 'BND', 'AGG', 'LQD',
            'GLD', 'SLV', 'USO', 'XLE', 'XLF', 'XLK', 'XBI', 'ARKK', 'ARKG', 'ARKF',
            'TQQQ', 'SQQQ', 'UVXY', 'SPXS', 'SPXL', 'TLT', 'HYG', 'EEM', 'FXI', 'BABA',
            'NIO', 'XPEV', 'LI', 'PDD', 'JD', 'DIDI', 'TAL', 'EDU', 'BIDU', 'TME',
            'RIVN', 'LCID', 'MULN', 'NKLA', 'WKHS', 'HYLN', 'SOLO', 'AYRO', 'IDEX', 'GEVO'
        ]
    
    def get_extended_universe(self, limit=2000):
        """Get extended universe for comprehensive scanning"""
        extended = set()
        
        # Add penny stocks and micro caps
        extended.update(self.get_penny_stocks())
        
        # Add international ADRs
        extended.update(self.get_international_adrs())
        
        # Add sector-specific stocks
        extended.update(self.get_sector_stocks())
        
        return list(extended)[:limit]
    
    def get_penny_stocks(self):
        """Get penny stock universe for pump detection"""
        return [
            'GNUS', 'XSPA', 'DECN', 'UAVS', 'VISL', 'MARK', 'KTOV', 'BIOC', 'AYTU', 'IBIO',
            'OPKO', 'TOPS', 'SHIP', 'DRYS', 'GLBS', 'CTRM', 'SNDL', 'NAKD', 'ZOMEDICA', 'ZOM',
            'BNGO', 'SENS', 'OBSV', 'CTIC', 'CPRX', 'CYTH', 'ADMP', 'PROG', 'RGBP', 'ENZC',
            'HMBL', 'OZSC', 'HCMC', 'ASTI', 'TSNP', 'ALPP', 'ABML', 'EEENF', 'RTON', 'RXMD'
        ]
    
    def get_international_adrs(self):
        """Get international ADR stocks"""
        return [
            'BABA', 'NIO', 'XPEV', 'LI', 'PDD', 'JD', 'BIDU', 'TME', 'NTES', 'WB',
            'TSM', 'ASML', 'NVO', 'UL', 'SAP', 'TM', 'SONY', 'SHOP', 'TD', 'RY',
            'CNI', 'ENB', 'SU', 'CCL', 'RCL', 'NCLH', 'CUK', 'TUI', 'AHAL', 'TCOM'
        ]
    
    def get_sector_stocks(self):
        """Get sector-specific stocks"""
        return [
            # Tech
            'CRM', 'NOW', 'WDAY', 'VEEV', 'ZM', 'DOCU', 'CRWD', 'ZS', 'OKTA', 'DDOG',
            # Energy
            'XOM', 'CVX', 'COP', 'EOG', 'SLB', 'HAL', 'OXY', 'DVN', 'MPC', 'VLO',
            # Healthcare
            'UNH', 'JNJ', 'PFE', 'ABBV', 'MRK', 'TMO', 'DHR', 'ABT', 'BMY', 'AMGN',
            # Financial
            'JPM', 'BAC', 'WFC', 'C', 'GS', 'MS', 'USB', 'PNC', 'TFC', 'COF'
        ]
    
    def get_pattern_evolution(self, symbol):
        """Get pattern evolution data for detailed analysis"""
        try:
            return self.pattern_tracker.track_pattern_evolution(symbol)
        except Exception as e:
            logging.error(f"Pattern evolution error for {symbol}: {e}")
            return None