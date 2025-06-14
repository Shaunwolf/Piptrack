"""
Personalized Stock Recommendation Engine
Analyzes user trading patterns, preferences, and market conditions to provide tailored stock suggestions
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans
import openai
import os

class PersonalizedRecommender:
    """Advanced stock recommendation engine with personalization"""
    
    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.user_profiles = {}
        self.market_sectors = [
            'Technology', 'Healthcare', 'Financial', 'Consumer Discretionary',
            'Communication Services', 'Industrials', 'Consumer Staples',
            'Energy', 'Utilities', 'Real Estate', 'Materials', 'Biotech'
        ]
        
    def build_user_profile(self, user_id: int, trading_history: List[Dict] = None) -> Dict:
        """Build comprehensive user trading profile from historical data"""
        try:
            # Get user's trading history from database (simulated for now)
            if not trading_history:
                trading_history = self._get_user_trading_history(user_id)
            
            profile = {
                'user_id': user_id,
                'risk_tolerance': self._calculate_risk_tolerance(trading_history),
                'preferred_sectors': self._identify_preferred_sectors(trading_history),
                'trading_style': self._determine_trading_style(trading_history),
                'success_patterns': self._analyze_success_patterns(trading_history),
                'avg_holding_period': self._calculate_avg_holding_period(trading_history),
                'preferred_price_range': self._identify_price_preferences(trading_history),
                'market_cap_preference': self._analyze_market_cap_preference(trading_history),
                'volatility_preference': self._calculate_volatility_preference(trading_history),
                'technical_indicators_used': self._identify_technical_preferences(trading_history),
                'performance_metrics': self._calculate_performance_metrics(trading_history),
                'last_updated': datetime.now().isoformat()
            }
            
            self.user_profiles[user_id] = profile
            return profile
            
        except Exception as e:
            logging.error(f"Error building user profile: {e}")
            return self._get_default_profile(user_id)
    
    def get_personalized_recommendations(self, user_id: int, num_recommendations: int = 10) -> Dict:
        """Generate personalized stock recommendations for user"""
        try:
            # Build or update user profile
            user_profile = self.build_user_profile(user_id)
            
            # Get market analysis
            market_analysis = self._analyze_current_market()
            
            # Get candidate stocks based on user preferences
            candidate_stocks = self._get_candidate_stocks(user_profile, market_analysis)
            
            # Score and rank candidates
            scored_candidates = self._score_candidates(candidate_stocks, user_profile, market_analysis)
            
            # Filter and select top recommendations
            top_recommendations = self._select_top_recommendations(
                scored_candidates, user_profile, num_recommendations
            )
            
            # Generate AI insights for each recommendation
            enhanced_recommendations = self._enhance_with_ai_insights(
                top_recommendations, user_profile
            )
            
            return {
                'user_id': user_id,
                'recommendations': enhanced_recommendations,
                'user_profile_summary': self._get_profile_summary(user_profile),
                'market_context': market_analysis,
                'confidence_score': self._calculate_recommendation_confidence(
                    enhanced_recommendations, user_profile
                ),
                'generated_at': datetime.now().isoformat(),
                'refresh_recommended_in': '4 hours'
            }
            
        except Exception as e:
            logging.error(f"Error generating recommendations: {e}")
            return self._get_fallback_recommendations(user_id)
    
    def _get_user_trading_history(self, user_id: int) -> List[Dict]:
        """Get user's trading history from database"""
        # In a real implementation, this would query the database
        # For now, return simulated data based on user patterns
        return [
            {
                'symbol': 'AAPL',
                'entry_date': '2024-01-15',
                'exit_date': '2024-02-20',
                'entry_price': 185.50,
                'exit_price': 195.75,
                'quantity': 50,
                'sector': 'Technology',
                'market_cap': 'Large',
                'success': True,
                'hold_days': 36,
                'return_pct': 5.5
            },
            {
                'symbol': 'TSLA',
                'entry_date': '2024-02-01',
                'exit_date': '2024-02-15',
                'entry_price': 195.00,
                'exit_price': 188.50,
                'quantity': 25,
                'sector': 'Consumer Discretionary',
                'market_cap': 'Large',
                'success': False,
                'hold_days': 14,
                'return_pct': -3.3
            }
        ]
    
    def _calculate_risk_tolerance(self, trading_history: List[Dict]) -> str:
        """Calculate user's risk tolerance from trading patterns"""
        if not trading_history:
            return 'moderate'
        
        # Analyze volatility of stocks traded
        volatilities = []
        for trade in trading_history:
            # Simulate volatility calculation
            if trade.get('return_pct', 0) != 0:
                volatilities.append(abs(trade['return_pct']))
        
        if not volatilities:
            return 'moderate'
        
        avg_volatility = np.mean(volatilities)
        
        if avg_volatility > 15:
            return 'aggressive'
        elif avg_volatility > 8:
            return 'moderate'
        else:
            return 'conservative'
    
    def _identify_preferred_sectors(self, trading_history: List[Dict]) -> List[str]:
        """Identify user's preferred sectors from trading history"""
        if not trading_history:
            return ['Technology', 'Healthcare']
        
        sector_counts = {}
        sector_performance = {}
        
        for trade in trading_history:
            sector = trade.get('sector', 'Unknown')
            if sector not in sector_counts:
                sector_counts[sector] = 0
                sector_performance[sector] = []
            
            sector_counts[sector] += 1
            if 'return_pct' in trade:
                sector_performance[sector].append(trade['return_pct'])
        
        # Weight by both frequency and performance
        sector_scores = {}
        for sector in sector_counts:
            frequency_score = sector_counts[sector]
            perf_score = np.mean(sector_performance[sector]) if sector_performance[sector] else 0
            sector_scores[sector] = frequency_score * (1 + max(0, perf_score) / 10)
        
        # Return top 3 sectors
        sorted_sectors = sorted(sector_scores.items(), key=lambda x: x[1], reverse=True)
        return [sector for sector, score in sorted_sectors[:3]]
    
    def _determine_trading_style(self, trading_history: List[Dict]) -> str:
        """Determine user's trading style from holding periods"""
        if not trading_history:
            return 'swing'
        
        holding_periods = [trade.get('hold_days', 30) for trade in trading_history]
        avg_holding = np.mean(holding_periods)
        
        if avg_holding <= 1:
            return 'day_trading'
        elif avg_holding <= 7:
            return 'short_term'
        elif avg_holding <= 30:
            return 'swing'
        else:
            return 'position'
    
    def _analyze_success_patterns(self, trading_history: List[Dict]) -> Dict:
        """Analyze patterns in successful trades"""
        if not trading_history:
            return {'success_rate': 0.5, 'avg_winner': 5.0, 'avg_loser': -3.0}
        
        successful_trades = [t for t in trading_history if t.get('success', False)]
        failed_trades = [t for t in trading_history if not t.get('success', True)]
        
        success_rate = len(successful_trades) / len(trading_history) if trading_history else 0.5
        
        avg_winner = np.mean([t['return_pct'] for t in successful_trades if 'return_pct' in t]) if successful_trades else 5.0
        avg_loser = np.mean([t['return_pct'] for t in failed_trades if 'return_pct' in t]) if failed_trades else -3.0
        
        return {
            'success_rate': success_rate,
            'avg_winner': avg_winner,
            'avg_loser': avg_loser,
            'win_loss_ratio': abs(avg_winner / avg_loser) if avg_loser != 0 else 1.5
        }
    
    def _calculate_avg_holding_period(self, trading_history: List[Dict]) -> int:
        """Calculate average holding period in days"""
        if not trading_history:
            return 21
        
        holding_periods = [trade.get('hold_days', 21) for trade in trading_history]
        return int(np.mean(holding_periods))
    
    def _identify_price_preferences(self, trading_history: List[Dict]) -> Dict:
        """Identify preferred price ranges"""
        if not trading_history:
            return {'min': 10, 'max': 500, 'preferred': 100}
        
        prices = [trade.get('entry_price', 100) for trade in trading_history]
        
        return {
            'min': max(5, np.percentile(prices, 25)),
            'max': min(1000, np.percentile(prices, 75) * 2),
            'preferred': np.median(prices)
        }
    
    def _analyze_market_cap_preference(self, trading_history: List[Dict]) -> str:
        """Analyze preferred market cap size"""
        if not trading_history:
            return 'large'
        
        cap_counts = {}
        for trade in trading_history:
            cap = trade.get('market_cap', 'large').lower()
            cap_counts[cap] = cap_counts.get(cap, 0) + 1
        
        return max(cap_counts, key=cap_counts.get) if cap_counts else 'large'
    
    def _calculate_volatility_preference(self, trading_history: List[Dict]) -> float:
        """Calculate preferred volatility level"""
        if not trading_history:
            return 0.15
        
        volatilities = [abs(trade.get('return_pct', 5)) / 100 for trade in trading_history]
        return np.mean(volatilities)
    
    def _identify_technical_preferences(self, trading_history: List[Dict]) -> List[str]:
        """Identify preferred technical indicators (simulated)"""
        # In real implementation, this would analyze actual indicator usage
        return ['RSI', 'MACD', 'Moving Averages', 'Bollinger Bands']
    
    def _calculate_performance_metrics(self, trading_history: List[Dict]) -> Dict:
        """Calculate user's historical performance metrics"""
        if not trading_history:
            return {'total_return': 0, 'win_rate': 0.5, 'sharpe_ratio': 1.0}
        
        returns = [trade.get('return_pct', 0) for trade in trading_history]
        
        total_return = sum(returns)
        win_rate = len([r for r in returns if r > 0]) / len(returns) if returns else 0.5
        sharpe_ratio = np.mean(returns) / np.std(returns) if np.std(returns) > 0 else 1.0
        
        return {
            'total_return': total_return,
            'win_rate': win_rate,
            'sharpe_ratio': sharpe_ratio,
            'avg_return': np.mean(returns),
            'max_drawdown': min(returns) if returns else 0
        }
    
    def _get_default_profile(self, user_id: int) -> Dict:
        """Get default profile for new users"""
        return {
            'user_id': user_id,
            'risk_tolerance': 'moderate',
            'preferred_sectors': ['Technology', 'Healthcare', 'Financial'],
            'trading_style': 'swing',
            'success_patterns': {'success_rate': 0.6, 'avg_winner': 8.0, 'avg_loser': -4.0},
            'avg_holding_period': 21,
            'preferred_price_range': {'min': 20, 'max': 300, 'preferred': 100},
            'market_cap_preference': 'large',
            'volatility_preference': 0.12,
            'technical_indicators_used': ['RSI', 'MACD', 'Moving Averages'],
            'performance_metrics': {'total_return': 0, 'win_rate': 0.6, 'sharpe_ratio': 1.2},
            'last_updated': datetime.now().isoformat()
        }
    
    def _analyze_current_market(self) -> Dict:
        """Analyze current market conditions"""
        try:
            # Get market data for major indices
            market_symbols = ['^GSPC', '^IXIC', '^DJI', '^RUT']
            market_data = {}
            
            for symbol in market_symbols:
                try:
                    ticker = yf.Ticker(symbol)
                    hist = ticker.history(period='1mo')
                    if not hist.empty:
                        current_price = hist['Close'].iloc[-1]
                        month_ago_price = hist['Close'].iloc[0]
                        momentum = (current_price - month_ago_price) / month_ago_price * 100
                        
                        market_data[symbol] = {
                            'momentum': momentum,
                            'volatility': hist['Close'].pct_change().std() * np.sqrt(252) * 100
                        }
                except:
                    continue
            
            # Calculate overall market sentiment
            if market_data:
                avg_momentum = np.mean([data['momentum'] for data in market_data.values()])
                avg_volatility = np.mean([data['volatility'] for data in market_data.values()])
                
                if avg_momentum > 2:
                    sentiment = 'bullish'
                elif avg_momentum < -2:
                    sentiment = 'bearish'
                else:
                    sentiment = 'neutral'
            else:
                sentiment = 'neutral'
                avg_momentum = 0
                avg_volatility = 15
            
            return {
                'sentiment': sentiment,
                'momentum': avg_momentum,
                'volatility': avg_volatility,
                'market_data': market_data,
                'recommended_strategy': self._get_strategy_for_market(sentiment, avg_volatility)
            }
            
        except Exception as e:
            logging.error(f"Error analyzing market: {e}")
            return {
                'sentiment': 'neutral',
                'momentum': 0,
                'volatility': 15,
                'market_data': {},
                'recommended_strategy': 'balanced'
            }
    
    def _get_strategy_for_market(self, sentiment: str, volatility: float) -> str:
        """Get recommended strategy based on market conditions"""
        if sentiment == 'bullish' and volatility < 20:
            return 'growth_momentum'
        elif sentiment == 'bearish' and volatility > 25:
            return 'defensive_value'
        elif volatility > 30:
            return 'volatility_trading'
        else:
            return 'balanced'
    
    def _get_candidate_stocks(self, user_profile: Dict, market_analysis: Dict) -> List[str]:
        """Get candidate stocks based on user preferences and market conditions"""
        # In a real implementation, this would use a stock screener API
        # For now, return a curated list based on user preferences
        
        tech_stocks = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'NFLX']
        healthcare_stocks = ['JNJ', 'UNH', 'PFE', 'ABBV', 'TMO', 'ABT', 'DHR', 'BMY']
        financial_stocks = ['JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'BLK', 'AXP']
        
        candidate_pools = {
            'Technology': tech_stocks,
            'Healthcare': healthcare_stocks,
            'Financial': financial_stocks
        }
        
        candidates = []
        preferred_sectors = user_profile.get('preferred_sectors', ['Technology'])
        
        for sector in preferred_sectors:
            if sector in candidate_pools:
                candidates.extend(candidate_pools[sector][:5])  # Top 5 from each sector
        
        # Add some market-condition specific stocks
        if market_analysis['sentiment'] == 'bullish':
            candidates.extend(['ROKU', 'SQ', 'SHOP'])
        elif market_analysis['sentiment'] == 'bearish':
            candidates.extend(['KO', 'PG', 'WMT'])
        
        return list(set(candidates))  # Remove duplicates
    
    def _score_candidates(self, candidates: List[str], user_profile: Dict, market_analysis: Dict) -> List[Dict]:
        """Score and rank candidate stocks"""
        scored_candidates = []
        
        for symbol in candidates:
            try:
                score_data = self._calculate_stock_score(symbol, user_profile, market_analysis)
                if score_data:
                    scored_candidates.append(score_data)
            except Exception as e:
                logging.error(f"Error scoring {symbol}: {e}")
                continue
        
        # Sort by total score descending
        return sorted(scored_candidates, key=lambda x: x['total_score'], reverse=True)
    
    def _calculate_stock_score(self, symbol: str, user_profile: Dict, market_analysis: Dict) -> Optional[Dict]:
        """Calculate comprehensive score for a stock"""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period='3mo')
            info = ticker.info
            
            if hist.empty:
                return None
            
            # Calculate various scoring components
            technical_score = self._calculate_technical_score(hist, user_profile)
            fundamental_score = self._calculate_fundamental_score(info, user_profile)
            sentiment_score = self._calculate_sentiment_score(symbol, market_analysis)
            fit_score = self._calculate_user_fit_score(symbol, info, user_profile)
            
            total_score = (
                technical_score * 0.3 +
                fundamental_score * 0.25 +
                sentiment_score * 0.2 +
                fit_score * 0.25
            )
            
            return {
                'symbol': symbol,
                'total_score': total_score,
                'technical_score': technical_score,
                'fundamental_score': fundamental_score,
                'sentiment_score': sentiment_score,
                'fit_score': fit_score,
                'current_price': hist['Close'].iloc[-1],
                'volume': hist['Volume'].iloc[-1],
                'market_cap': info.get('marketCap', 0),
                'sector': info.get('sector', 'Unknown'),
                'beta': info.get('beta', 1.0),
                'pe_ratio': info.get('trailingPE', 0),
                'recommendation_reason': self._generate_recommendation_reason(
                    symbol, technical_score, fundamental_score, sentiment_score, fit_score
                )
            }
            
        except Exception as e:
            logging.error(f"Error calculating score for {symbol}: {e}")
            return None
    
    def _calculate_technical_score(self, hist: pd.DataFrame, user_profile: Dict) -> float:
        """Calculate technical analysis score"""
        try:
            # RSI
            delta = hist['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            current_rsi = rsi.iloc[-1]
            
            # Moving averages
            ma_20 = hist['Close'].rolling(20).mean()
            ma_50 = hist['Close'].rolling(50).mean()
            current_price = hist['Close'].iloc[-1]
            
            # Volume trend
            avg_volume = hist['Volume'].rolling(20).mean().iloc[-1]
            recent_volume = hist['Volume'].iloc[-1]
            volume_ratio = recent_volume / avg_volume if avg_volume > 0 else 1
            
            # Scoring
            score = 50  # Base score
            
            # RSI scoring (prefer 30-70 range)
            if 30 <= current_rsi <= 70:
                score += 20
            elif current_rsi < 30:
                score += 15  # Oversold can be good
            elif current_rsi > 70:
                score += 5   # Overbought is risky
            
            # Moving average trend
            if current_price > ma_20.iloc[-1]:
                score += 15
            if current_price > ma_50.iloc[-1]:
                score += 10
            
            # Volume confirmation
            if volume_ratio > 1.2:
                score += 10
            elif volume_ratio > 1.0:
                score += 5
            
            return min(100, max(0, score))
            
        except Exception as e:
            logging.error(f"Technical score calculation error: {e}")
            return 50
    
    def _calculate_fundamental_score(self, info: Dict, user_profile: Dict) -> float:
        """Calculate fundamental analysis score"""
        try:
            score = 50  # Base score
            
            # P/E Ratio
            pe_ratio = info.get('trailingPE', 0)
            if 0 < pe_ratio < 15:
                score += 20
            elif 15 <= pe_ratio < 25:
                score += 15
            elif 25 <= pe_ratio < 35:
                score += 5
            
            # Market Cap preference alignment
            market_cap = info.get('marketCap', 0)
            user_cap_pref = user_profile.get('market_cap_preference', 'large')
            
            if user_cap_pref == 'large' and market_cap > 10e9:
                score += 15
            elif user_cap_pref == 'mid' and 2e9 <= market_cap <= 10e9:
                score += 15
            elif user_cap_pref == 'small' and market_cap < 2e9:
                score += 15
            
            # Financial health indicators
            if info.get('debtToEquity', 100) < 50:
                score += 10
            
            if info.get('returnOnEquity', 0) > 15:
                score += 10
            
            # Growth metrics
            if info.get('earningsGrowth', 0) > 0.1:
                score += 10
            
            return min(100, max(0, score))
            
        except Exception as e:
            logging.error(f"Fundamental score calculation error: {e}")
            return 50
    
    def _calculate_sentiment_score(self, symbol: str, market_analysis: Dict) -> float:
        """Calculate market sentiment score"""
        try:
            base_score = 50
            
            # Market sentiment alignment
            market_sentiment = market_analysis.get('sentiment', 'neutral')
            
            if market_sentiment == 'bullish':
                base_score += 20
            elif market_sentiment == 'bearish':
                base_score -= 10
            
            # Market momentum
            momentum = market_analysis.get('momentum', 0)
            if momentum > 3:
                base_score += 15
            elif momentum > 0:
                base_score += 5
            elif momentum < -3:
                base_score -= 15
            
            return min(100, max(0, base_score))
            
        except Exception as e:
            logging.error(f"Sentiment score calculation error: {e}")
            return 50
    
    def _calculate_user_fit_score(self, symbol: str, info: Dict, user_profile: Dict) -> float:
        """Calculate how well stock fits user's profile"""
        try:
            score = 50
            
            # Sector preference
            stock_sector = info.get('sector', '')
            preferred_sectors = user_profile.get('preferred_sectors', [])
            if stock_sector in preferred_sectors:
                score += 25
            
            # Price range preference
            current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
            price_prefs = user_profile.get('preferred_price_range', {})
            min_price = price_prefs.get('min', 0)
            max_price = price_prefs.get('max', 1000)
            
            if min_price <= current_price <= max_price:
                score += 15
            
            # Risk tolerance alignment
            beta = info.get('beta', 1.0)
            risk_tolerance = user_profile.get('risk_tolerance', 'moderate')
            
            if risk_tolerance == 'conservative' and beta < 1.2:
                score += 10
            elif risk_tolerance == 'moderate' and 0.8 <= beta <= 1.5:
                score += 10
            elif risk_tolerance == 'aggressive' and beta > 1.2:
                score += 10
            
            return min(100, max(0, score))
            
        except Exception as e:
            logging.error(f"User fit score calculation error: {e}")
            return 50
    
    def _generate_recommendation_reason(self, symbol: str, tech_score: float, 
                                      fund_score: float, sent_score: float, fit_score: float) -> str:
        """Generate human-readable recommendation reason"""
        reasons = []
        
        if tech_score > 70:
            reasons.append("strong technical setup")
        if fund_score > 70:
            reasons.append("solid fundamentals")
        if sent_score > 70:
            reasons.append("positive market sentiment")
        if fit_score > 70:
            reasons.append("excellent match for your profile")
        
        if not reasons:
            reasons = ["balanced opportunity"]
        
        return f"Recommended due to {', '.join(reasons)}"
    
    def _select_top_recommendations(self, scored_candidates: List[Dict], 
                                  user_profile: Dict, num_recommendations: int) -> List[Dict]:
        """Select top recommendations with diversification"""
        if not scored_candidates:
            return []
        
        # Ensure diversification by sector
        selected = []
        sectors_used = set()
        
        # First pass: select best from each sector
        for candidate in scored_candidates:
            if len(selected) >= num_recommendations:
                break
            
            sector = candidate.get('sector', 'Unknown')
            if sector not in sectors_used or len(sectors_used) >= 3:
                selected.append(candidate)
                sectors_used.add(sector)
        
        # Second pass: fill remaining slots with highest scores
        for candidate in scored_candidates:
            if len(selected) >= num_recommendations:
                break
            if candidate not in selected:
                selected.append(candidate)
        
        return selected[:num_recommendations]
    
    def _enhance_with_ai_insights(self, recommendations: List[Dict], user_profile: Dict) -> List[Dict]:
        """Enhance recommendations with AI-generated insights"""
        enhanced = []
        
        for rec in recommendations:
            try:
                ai_insight = self._generate_ai_insight(rec, user_profile)
                rec['ai_insight'] = ai_insight
                rec['confidence_level'] = self._calculate_individual_confidence(rec)
                rec['risk_assessment'] = self._assess_individual_risk(rec, user_profile)
                rec['target_price'] = self._estimate_target_price(rec)
                rec['time_horizon'] = self._suggest_time_horizon(rec, user_profile)
                enhanced.append(rec)
            except Exception as e:
                logging.error(f"Error enhancing recommendation for {rec['symbol']}: {e}")
                enhanced.append(rec)  # Add without enhancement
        
        return enhanced
    
    def _generate_ai_insight(self, recommendation: Dict, user_profile: Dict) -> str:
        """Generate AI-powered insight for recommendation"""
        try:
            prompt = f"""
            Analyze this stock recommendation for a trader:
            
            Stock: {recommendation['symbol']}
            Sector: {recommendation.get('sector', 'Unknown')}
            Current Price: ${recommendation.get('current_price', 0):.2f}
            Technical Score: {recommendation['technical_score']}/100
            Fundamental Score: {recommendation['fundamental_score']}/100
            P/E Ratio: {recommendation.get('pe_ratio', 'N/A')}
            Beta: {recommendation.get('beta', 'N/A')}
            
            User Profile:
            Risk Tolerance: {user_profile['risk_tolerance']}
            Trading Style: {user_profile['trading_style']}
            Preferred Sectors: {', '.join(user_profile['preferred_sectors'])}
            
            Provide a concise 2-3 sentence insight explaining why this stock fits the user's profile and what to watch for. Focus on actionable insights.
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logging.error(f"Error generating AI insight: {e}")
            return f"Strong recommendation based on {recommendation['recommendation_reason']}."
    
    def _calculate_individual_confidence(self, recommendation: Dict) -> str:
        """Calculate confidence level for individual recommendation"""
        total_score = recommendation['total_score']
        
        if total_score >= 80:
            return 'High'
        elif total_score >= 65:
            return 'Medium'
        else:
            return 'Low'
    
    def _assess_individual_risk(self, recommendation: Dict, user_profile: Dict) -> str:
        """Assess risk level for individual recommendation"""
        beta = recommendation.get('beta', 1.0)
        sector = recommendation.get('sector', '')
        
        high_risk_sectors = ['Technology', 'Biotech', 'Energy']
        
        if beta > 1.5 or sector in high_risk_sectors:
            return 'High'
        elif beta > 1.2:
            return 'Medium'
        else:
            return 'Low'
    
    def _estimate_target_price(self, recommendation: Dict) -> float:
        """Estimate target price based on analysis"""
        current_price = recommendation.get('current_price', 0)
        total_score = recommendation['total_score']
        
        # Simple target estimation based on score
        upside_potential = (total_score - 50) / 50 * 0.15  # Max 15% upside
        target_price = current_price * (1 + upside_potential)
        
        return round(target_price, 2)
    
    def _suggest_time_horizon(self, recommendation: Dict, user_profile: Dict) -> str:
        """Suggest appropriate time horizon"""
        trading_style = user_profile.get('trading_style', 'swing')
        
        style_horizons = {
            'day_trading': '1-2 days',
            'short_term': '1-2 weeks',
            'swing': '2-8 weeks',
            'position': '3-12 months'
        }
        
        return style_horizons.get(trading_style, '2-8 weeks')
    
    def _get_profile_summary(self, user_profile: Dict) -> Dict:
        """Get summary of user profile for display"""
        return {
            'risk_tolerance': user_profile['risk_tolerance'].capitalize(),
            'trading_style': user_profile['trading_style'].replace('_', ' ').title(),
            'preferred_sectors': user_profile['preferred_sectors'][:3],
            'success_rate': f"{user_profile['success_patterns']['success_rate'] * 100:.1f}%",
            'avg_holding_period': f"{user_profile['avg_holding_period']} days"
        }
    
    def _calculate_recommendation_confidence(self, recommendations: List[Dict], user_profile: Dict) -> float:
        """Calculate overall confidence in recommendations"""
        if not recommendations:
            return 0.5
        
        avg_score = np.mean([rec['total_score'] for rec in recommendations])
        profile_completeness = self._assess_profile_completeness(user_profile)
        
        # Combine factors
        confidence = (avg_score / 100) * 0.7 + profile_completeness * 0.3
        return min(1.0, max(0.1, confidence))
    
    def _assess_profile_completeness(self, user_profile: Dict) -> float:
        """Assess how complete the user profile is"""
        required_fields = [
            'risk_tolerance', 'preferred_sectors', 'trading_style',
            'success_patterns', 'performance_metrics'
        ]
        
        completeness = 0
        for field in required_fields:
            if field in user_profile and user_profile[field]:
                completeness += 1
        
        return completeness / len(required_fields)
    
    def _get_fallback_recommendations(self, user_id: int) -> Dict:
        """Provide fallback recommendations when main system fails"""
        return {
            'user_id': user_id,
            'recommendations': [
                {
                    'symbol': 'AAPL',
                    'total_score': 75,
                    'current_price': 190.00,
                    'sector': 'Technology',
                    'confidence_level': 'Medium',
                    'risk_assessment': 'Low',
                    'target_price': 205.00,
                    'time_horizon': '4-8 weeks',
                    'ai_insight': 'Solid technology leader with consistent performance.',
                    'recommendation_reason': 'Strong fundamentals and market position'
                }
            ],
            'user_profile_summary': {
                'risk_tolerance': 'Moderate',
                'trading_style': 'Swing Trading',
                'preferred_sectors': ['Technology'],
                'success_rate': '60.0%',
                'avg_holding_period': '21 days'
            },
            'market_context': {
                'sentiment': 'neutral',
                'momentum': 0,
                'volatility': 15,
                'recommended_strategy': 'balanced'
            },
            'confidence_score': 0.6,
            'generated_at': datetime.now().isoformat(),
            'refresh_recommended_in': '4 hours'
        }
    
    def update_user_feedback(self, user_id: int, recommendation_id: str, 
                           feedback: str, action_taken: str = None) -> bool:
        """Update system based on user feedback"""
        try:
            # In a real implementation, this would store feedback in database
            # and use it to improve future recommendations
            logging.info(f"User {user_id} feedback on {recommendation_id}: {feedback}")
            
            # Update user profile based on feedback
            if user_id in self.user_profiles:
                profile = self.user_profiles[user_id]
                # Adjust preferences based on feedback
                # This is a simplified implementation
                
            return True
        except Exception as e:
            logging.error(f"Error updating user feedback: {e}")
            return False
    
    def get_recommendation_performance(self, user_id: int, days_back: int = 30) -> Dict:
        """Get performance analysis of past recommendations"""
        try:
            # In a real implementation, this would analyze actual performance
            # of recommendations against user's actions and market performance
            
            return {
                'period_days': days_back,
                'recommendations_given': 25,
                'actions_taken': 8,
                'successful_recommendations': 6,
                'avg_return': 4.2,
                'hit_rate': 75.0,
                'user_satisfaction': 4.2,
                'system_learning_status': 'improving'
            }
        except Exception as e:
            logging.error(f"Error getting recommendation performance: {e}")
            return {}