"""
Reddit Sentiment Monitor for Pump Detection
Phase 1 Enhancement: Track WSB mentions and sentiment scoring
"""

import praw
import os
import re
import time
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import logging

class RedditSentimentMonitor:
    """Monitor Reddit for pump-related sentiment and mentions"""
    
    def __init__(self):
        self.analyzer = SentimentIntensityAnalyzer()
        
        # Pump-related keywords and phrases
        self.pump_keywords = [
            'moon', 'mooning', 'to the moon', 'squeeze', 'short squeeze',
            'diamond hands', 'hold', 'hodl', 'buy the dip', 'btd',
            'gamma squeeze', 'rocket', 'tendies', 'apes', 'stonks',
            'yolo', 'dd', 'due diligence', 'calls', 'options'
        ]
        
        self.bearish_keywords = [
            'dump', 'crash', 'sell', 'puts', 'bearish', 'overvalued',
            'bubble', 'correction', 'tank', 'drop', 'fall'
        ]
        
        # Target subreddits for monitoring
        self.target_subreddits = [
            'wallstreetbets', 'stocks', 'investing', 'SecurityAnalysis',
            'StockMarket', 'pennystocks', 'smallstreetbets'
        ]
        
        # Initialize Reddit API (will need credentials)
        self.reddit = None
        self._initialize_reddit()
    
    def _initialize_reddit(self):
        """Initialize Reddit API connection"""
        try:
            # Check for Reddit API credentials in environment
            client_id = os.environ.get('REDDIT_CLIENT_ID')
            client_secret = os.environ.get('REDDIT_CLIENT_SECRET')
            user_agent = os.environ.get('REDDIT_USER_AGENT', 'CandleCast Pump Monitor v1.0')
            
            if client_id and client_secret:
                self.reddit = praw.Reddit(
                    client_id=client_id,
                    client_secret=client_secret,
                    user_agent=user_agent
                )
                logging.info("Reddit API initialized successfully")
            else:
                logging.warning("Reddit API credentials not found. Social monitoring disabled.")
                self.reddit = None
                
        except Exception as e:
            logging.error(f"Failed to initialize Reddit API: {e}")
            self.reddit = None
    
    def extract_stock_symbols(self, text: str) -> List[str]:
        """Extract stock symbols from Reddit text"""
        # Match $SYMBOL or SYMBOL patterns
        symbol_pattern = r'\$([A-Z]{1,5})\b|(?<!\w)([A-Z]{2,5})(?=\s|$|[^\w])'
        matches = re.findall(symbol_pattern, text.upper())
        
        symbols = []
        for match in matches:
            symbol = match[0] if match[0] else match[1]
            # Filter out common false positives
            if symbol not in ['THE', 'AND', 'FOR', 'ARE', 'BUT', 'NOT', 'YOU', 'ALL', 'CAN', 'HER', 'WAS', 'ONE', 'OUR', 'HAD', 'BUT', 'HAS', 'HIS', 'DID', 'GET', 'TWO', 'WAY', 'NEW', 'MAY', 'SAY', 'USE', 'MAN', 'DAY', 'TOO', 'ANY', 'SET', 'PUT', 'END', 'WHY', 'LET', 'TRY', 'BIG', 'OLD', 'SEE', 'HIM', 'HOW', 'ITS', 'NOW', 'TOP', 'RUN', 'GOT', 'EAT', 'FAR', 'SEA', 'EYE', 'BED', 'RED', 'HOT', 'SUN', 'LET', 'BAD', 'ETC', 'CEO', 'IPO', 'ETF', 'ESG', 'SEC', 'FDA', 'IRA', 'LLC', 'ATH', 'ATL', 'YTD', 'QOQ', 'YOY', 'EOY', 'EOD', 'AH']:
                symbols.append(symbol)
        
        return list(set(symbols))  # Remove duplicates
    
    def analyze_sentiment(self, text: str) -> Dict:
        """Analyze sentiment of text using multiple methods"""
        # VADER sentiment (good for social media text)
        vader_scores = self.analyzer.polarity_scores(text)
        
        # TextBlob sentiment
        blob = TextBlob(text)
        textblob_sentiment = blob.sentiment.polarity
        
        # Keyword-based pump sentiment
        pump_score = self._calculate_pump_sentiment(text)
        
        # Combined sentiment score
        combined_score = (vader_scores['compound'] + textblob_sentiment + pump_score) / 3
        
        return {
            'vader_compound': vader_scores['compound'],
            'vader_positive': vader_scores['pos'],
            'vader_negative': vader_scores['neg'],
            'vader_neutral': vader_scores['neu'],
            'textblob_polarity': textblob_sentiment,
            'textblob_subjectivity': blob.sentiment.subjectivity,
            'pump_sentiment': pump_score,
            'combined_sentiment': combined_score,
            'bullish_keywords': self._count_keywords(text, self.pump_keywords),
            'bearish_keywords': self._count_keywords(text, self.bearish_keywords)
        }
    
    def _calculate_pump_sentiment(self, text: str) -> float:
        """Calculate pump-specific sentiment score"""
        text_lower = text.lower()
        
        pump_count = sum(1 for keyword in self.pump_keywords if keyword in text_lower)
        bearish_count = sum(1 for keyword in self.bearish_keywords if keyword in text_lower)
        
        # Normalize based on text length
        text_length = len(text.split())
        if text_length == 0:
            return 0
        
        pump_density = pump_count / text_length * 100
        bearish_density = bearish_count / text_length * 100
        
        # Return score between -1 and 1
        return max(-1, min(1, (pump_density - bearish_density) / 10))
    
    def _count_keywords(self, text: str, keywords: List[str]) -> int:
        """Count occurrences of keywords in text"""
        text_lower = text.lower()
        return sum(1 for keyword in keywords if keyword in text_lower)
    
    def monitor_subreddit_mentions(self, symbol: str, subreddit: str = 'wallstreetbets', 
                                 hours_back: int = 24, limit: int = 100) -> Dict:
        """Monitor specific subreddit for symbol mentions"""
        if not self.reddit:
            return {'error': 'Reddit API not available'}
        
        try:
            sub = self.reddit.subreddit(subreddit)
            mentions = []
            
            # Search for symbol mentions in recent posts
            for submission in sub.new(limit=limit):
                # Check if post is within time window
                post_time = datetime.fromtimestamp(submission.created_utc)
                if post_time < datetime.now() - timedelta(hours=hours_back):
                    continue
                
                # Check title and selftext for symbol
                title_symbols = self.extract_stock_symbols(submission.title)
                selftext_symbols = self.extract_stock_symbols(submission.selftext or '')
                
                if symbol.upper() in title_symbols or symbol.upper() in selftext_symbols:
                    # Analyze sentiment
                    full_text = f"{submission.title} {submission.selftext or ''}"
                    sentiment = self.analyze_sentiment(full_text)
                    
                    mentions.append({
                        'id': submission.id,
                        'title': submission.title,
                        'text': submission.selftext[:500] if submission.selftext else '',
                        'score': submission.score,
                        'upvote_ratio': submission.upvote_ratio,
                        'num_comments': submission.num_comments,
                        'created_utc': submission.created_utc,
                        'url': submission.url,
                        'sentiment': sentiment,
                        'symbols_found': list(set(title_symbols + selftext_symbols))
                    })
            
            # Also check comments in hot posts
            for submission in sub.hot(limit=25):
                if hasattr(submission, 'comments'):
                    submission.comments.replace_more(limit=0)
                    for comment in submission.comments.list()[:50]:
                        if hasattr(comment, 'body'):
                            comment_symbols = self.extract_stock_symbols(comment.body)
                            if symbol.upper() in comment_symbols:
                                sentiment = self.analyze_sentiment(comment.body)
                                
                                mentions.append({
                                    'id': comment.id,
                                    'title': f"Comment on: {submission.title}",
                                    'text': comment.body[:500],
                                    'score': getattr(comment, 'score', 0),
                                    'created_utc': getattr(comment, 'created_utc', 0),
                                    'sentiment': sentiment,
                                    'symbols_found': comment_symbols,
                                    'type': 'comment'
                                })
            
            return self._analyze_mention_data(mentions, symbol)
            
        except Exception as e:
            logging.error(f"Error monitoring subreddit {subreddit}: {e}")
            return {'error': str(e)}
    
    def _analyze_mention_data(self, mentions: List[Dict], symbol: str) -> Dict:
        """Analyze collected mention data for pump signals"""
        if not mentions:
            return {
                'symbol': symbol,
                'mention_count': 0,
                'sentiment_score': 0,
                'pump_probability': 0,
                'mentions': []
            }
        
        # Calculate metrics
        mention_count = len(mentions)
        avg_sentiment = sum(m['sentiment']['combined_sentiment'] for m in mentions) / mention_count
        avg_score = sum(m['score'] for m in mentions) / mention_count
        total_pump_keywords = sum(m['sentiment']['bullish_keywords'] for m in mentions)
        total_bearish_keywords = sum(m['sentiment']['bearish_keywords'] for m in mentions)
        
        # Calculate pump probability (0-100)
        pump_probability = self._calculate_pump_probability(
            mention_count, avg_sentiment, avg_score, total_pump_keywords, total_bearish_keywords
        )
        
        # Sort mentions by engagement (score + comments)
        mentions.sort(key=lambda x: x['score'] + x.get('num_comments', 0), reverse=True)
        
        return {
            'symbol': symbol,
            'mention_count': mention_count,
            'sentiment_score': avg_sentiment,
            'average_post_score': avg_score,
            'pump_keywords_total': total_pump_keywords,
            'bearish_keywords_total': total_bearish_keywords,
            'pump_probability': pump_probability,
            'top_mentions': mentions[:10],  # Top 10 by engagement
            'analysis_timestamp': datetime.now().isoformat()
        }
    
    def _calculate_pump_probability(self, mention_count: int, avg_sentiment: float, 
                                  avg_score: float, pump_keywords: int, bearish_keywords: int) -> float:
        """Calculate probability of pump based on social signals"""
        score = 0
        
        # Mention volume scoring (0-30 points)
        if mention_count >= 50:
            score += 30
        elif mention_count >= 20:
            score += 20
        elif mention_count >= 10:
            score += 15
        elif mention_count >= 5:
            score += 10
        
        # Sentiment scoring (0-25 points)
        if avg_sentiment > 0.5:
            score += 25
        elif avg_sentiment > 0.2:
            score += 15
        elif avg_sentiment > 0:
            score += 10
        
        # Engagement scoring (0-20 points)
        if avg_score > 100:
            score += 20
        elif avg_score > 50:
            score += 15
        elif avg_score > 20:
            score += 10
        elif avg_score > 10:
            score += 5
        
        # Keyword ratio scoring (0-25 points)
        if pump_keywords > 0:
            keyword_ratio = pump_keywords / (pump_keywords + bearish_keywords + 1)
            score += min(25, keyword_ratio * 40)
        
        return min(100, score)
    
    def scan_trending_symbols(self, hours_back: int = 6) -> List[Dict]:
        """Scan for trending symbols across monitored subreddits"""
        if not self.reddit:
            return []
        
        symbol_data = {}
        
        for subreddit_name in self.target_subreddits[:3]:  # Limit to avoid rate limits
            try:
                subreddit = self.reddit.subreddit(subreddit_name)
                
                for submission in subreddit.hot(limit=50):
                    post_time = datetime.fromtimestamp(submission.created_utc)
                    if post_time < datetime.now() - timedelta(hours=hours_back):
                        continue
                    
                    symbols = self.extract_stock_symbols(f"{submission.title} {submission.selftext or ''}")
                    
                    for symbol in symbols:
                        if len(symbol) <= 5:  # Valid stock symbol length
                            if symbol not in symbol_data:
                                symbol_data[symbol] = []
                            
                            sentiment = self.analyze_sentiment(f"{submission.title} {submission.selftext or ''}")
                            symbol_data[symbol].append({
                                'sentiment': sentiment['combined_sentiment'],
                                'score': submission.score,
                                'comments': submission.num_comments,
                                'subreddit': subreddit_name
                            })
                
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                logging.error(f"Error scanning subreddit {subreddit_name}: {e}")
                continue
        
        # Analyze collected data
        trending_symbols = []
        for symbol, data in symbol_data.items():
            if len(data) >= 3:  # Minimum mentions threshold
                avg_sentiment = sum(d['sentiment'] for d in data) / len(data)
                total_engagement = sum(d['score'] + d['comments'] for d in data)
                
                trending_symbols.append({
                    'symbol': symbol,
                    'mention_count': len(data),
                    'avg_sentiment': avg_sentiment,
                    'total_engagement': total_engagement,
                    'pump_score': self._calculate_trending_score(len(data), avg_sentiment, total_engagement)
                })
        
        # Sort by pump score
        trending_symbols.sort(key=lambda x: x['pump_score'], reverse=True)
        return trending_symbols[:20]  # Top 20
    
    def _calculate_trending_score(self, mentions: int, sentiment: float, engagement: int) -> float:
        """Calculate trending score for symbol"""
        # Normalize factors and combine
        mention_score = min(50, mentions * 5)  # Up to 50 points
        sentiment_score = max(0, sentiment * 30)  # Up to 30 points for positive sentiment
        engagement_score = min(20, engagement / 100)  # Up to 20 points
        
        return mention_score + sentiment_score + engagement_score
    
    def get_pump_alerts(self, symbol: str) -> Dict:
        """Get pump alerts based on Reddit sentiment analysis"""
        analysis = self.monitor_subreddit_mentions(symbol, 'wallstreetbets', hours_back=12)
        
        if 'error' in analysis:
            return analysis
        
        alerts = []
        
        # High mention volume alert
        if analysis['mention_count'] >= 20:
            alerts.append({
                'type': 'HIGH_SOCIAL_VOLUME',
                'message': f"{symbol} has {analysis['mention_count']} mentions in last 12h",
                'urgency': 'HIGH' if analysis['mention_count'] >= 50 else 'MEDIUM'
            })
        
        # Positive sentiment surge
        if analysis['sentiment_score'] > 0.4 and analysis['mention_count'] >= 5:
            alerts.append({
                'type': 'POSITIVE_SENTIMENT_SURGE',
                'message': f"{symbol} showing strong positive sentiment ({analysis['sentiment_score']:.2f})",
                'urgency': 'MEDIUM'
            })
        
        # High pump probability
        if analysis['pump_probability'] >= 70:
            alerts.append({
                'type': 'HIGH_PUMP_PROBABILITY',
                'message': f"{symbol} pump probability: {analysis['pump_probability']:.0f}%",
                'urgency': 'HIGH'
            })
        
        return {
            'symbol': symbol,
            'alerts': alerts,
            'analysis': analysis
        }