import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
from models import TradeJournal, db
from sqlalchemy import func, desc, and_
import yfinance as yf
from multi_timeframe_analyzer import MultiTimeframeAnalyzer
from pattern_evolution_tracker import PatternEvolutionTracker

class EnhancedTradingJournal:
    def __init__(self):
        self.mtf_analyzer = MultiTimeframeAnalyzer()
        self.pattern_tracker = PatternEvolutionTracker()
    
    def add_enhanced_trade(self, trade_data: Dict) -> Dict:
        """Add trade with enhanced analytics and pre-trade analysis"""
        try:
            symbol = trade_data['symbol']
            
            # Capture market conditions at entry
            market_conditions = self._capture_market_conditions(symbol)
            
            # Pattern analysis at entry
            pattern_analysis = self._analyze_entry_patterns(symbol)
            
            # Multi-timeframe confirmation
            mtf_analysis = self.mtf_analyzer.analyze_multi_timeframe_patterns(symbol)
            
            # Risk assessment
            risk_metrics = self._calculate_entry_risk_metrics(trade_data, market_conditions)
            
            # Create enhanced trade record
            trade = TradeJournal(
                symbol=symbol,
                entry_price=trade_data['entry_price'],
                stop_loss=trade_data.get('stop_loss'),
                take_profit=trade_data.get('take_profit'),
                pattern_confirmed=trade_data.get('pattern_confirmed', False),
                screenshot_taken=trade_data.get('screenshot_taken', False),
                reflection=trade_data.get('reflection', ''),
                perfect_trade=trade_data.get('perfect_trade', False),
                confidence_at_entry=trade_data.get('confidence_at_entry', 0),
                outcome='active'
            )
            
            # Add enhanced metadata as JSON in reflection field
            enhanced_data = {
                'market_conditions': market_conditions,
                'pattern_analysis': pattern_analysis,
                'mtf_analysis': mtf_analysis,
                'risk_metrics': risk_metrics,
                'entry_timestamp': datetime.now().isoformat(),
                'trade_setup': trade_data.get('trade_setup', 'manual'),
                'timeframe_priority': mtf_analysis.get('timeframe_priority', '1d') if 'error' not in mtf_analysis else '1d'
            }
            
            # Combine original reflection with enhanced data
            if trade.reflection:
                trade.reflection = f"{trade.reflection}\n\n--- Enhanced Analytics ---\n{str(enhanced_data)}"
            else:
                trade.reflection = f"--- Enhanced Analytics ---\n{str(enhanced_data)}"
            
            db.session.add(trade)
            db.session.commit()
            
            return {
                'success': True,
                'trade_id': trade.id,
                'enhanced_data': enhanced_data,
                'recommendations': self._generate_trade_recommendations(enhanced_data)
            }
            
        except Exception as e:
            logging.error(f"Error adding enhanced trade: {e}")
            db.session.rollback()
            return {'success': False, 'error': str(e)}
    
    def _capture_market_conditions(self, symbol: str) -> Dict:
        """Capture comprehensive market conditions at trade entry"""
        try:
            # Get market indices
            indices = ['SPY', 'QQQ', 'IWM']
            market_data = {}
            
            for index in indices:
                ticker = yf.Ticker(index)
                hist = ticker.history(period='5d')
                if not hist.empty:
                    current_price = hist['Close'].iloc[-1]
                    prev_close = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
                    change_pct = ((current_price - prev_close) / prev_close) * 100
                    
                    market_data[index] = {
                        'price': float(current_price),
                        'change_pct': float(change_pct),
                        'volume_ratio': float(hist['Volume'].iloc[-1] / hist['Volume'].mean()) if len(hist) > 1 else 1.0
                    }
            
            # VIX for volatility
            vix_data = self._get_vix_level()
            
            # Sector strength
            sector_performance = self._get_sector_performance(symbol)
            
            return {
                'timestamp': datetime.now().isoformat(),
                'market_indices': market_data,
                'vix_level': vix_data,
                'sector_performance': sector_performance,
                'overall_sentiment': self._calculate_market_sentiment(market_data)
            }
            
        except Exception as e:
            logging.error(f"Error capturing market conditions: {e}")
            return {'error': str(e)}
    
    def _analyze_entry_patterns(self, symbol: str) -> Dict:
        """Analyze patterns present at trade entry"""
        try:
            # Get current pattern state
            patterns = self.pattern_tracker.track_pattern_evolution(symbol)
            
            # Historical pattern success rate
            pattern_success_rate = self._calculate_pattern_success_rate(
                patterns.get('pattern_type') if patterns else None
            )
            
            return {
                'current_patterns': patterns,
                'pattern_success_rate': pattern_success_rate,
                'pattern_maturity': self._assess_pattern_maturity(patterns),
                'breakout_probability': patterns.get('breakout_probability_5_days', 0) if patterns else 0
            }
            
        except Exception as e:
            logging.error(f"Error analyzing entry patterns: {e}")
            return {'error': str(e)}
    
    def _calculate_entry_risk_metrics(self, trade_data: Dict, market_conditions: Dict) -> Dict:
        """Calculate comprehensive risk metrics for the trade"""
        try:
            entry_price = trade_data['entry_price']
            stop_loss = trade_data.get('stop_loss')
            take_profit = trade_data.get('take_profit')
            
            # Basic risk/reward
            risk_amount = abs(entry_price - stop_loss) if stop_loss else entry_price * 0.05
            reward_amount = abs(take_profit - entry_price) if take_profit else entry_price * 0.10
            risk_reward_ratio = reward_amount / risk_amount if risk_amount > 0 else 0
            
            # Market risk adjustment
            market_risk_multiplier = self._calculate_market_risk_multiplier(market_conditions)
            
            # Position sizing recommendation
            base_position_size = 1000  # Base $1000 position
            recommended_position = base_position_size / market_risk_multiplier
            
            # Risk score (0-100, lower is better)
            risk_score = self._calculate_composite_risk_score(
                market_conditions, risk_reward_ratio, market_risk_multiplier
            )
            
            return {
                'risk_reward_ratio': float(risk_reward_ratio),
                'risk_amount_pct': float((risk_amount / entry_price) * 100),
                'reward_amount_pct': float((reward_amount / entry_price) * 100),
                'market_risk_multiplier': float(market_risk_multiplier),
                'recommended_position_size': float(recommended_position),
                'risk_score': float(risk_score),
                'risk_level': self._categorize_risk_level(risk_score)
            }
            
        except Exception as e:
            logging.error(f"Error calculating risk metrics: {e}")
            return {'error': str(e)}
    
    def get_performance_analytics(self, days: int = 30) -> Dict:
        """Get comprehensive performance analytics"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Get trades in period
            trades = TradeJournal.query.filter(
                TradeJournal.created_at >= start_date,
                TradeJournal.created_at <= end_date
            ).all()
            
            if not trades:
                return {'error': 'No trades found in the specified period'}
            
            # Basic performance metrics
            basic_metrics = self._calculate_basic_performance(trades)
            
            # Pattern performance analysis
            pattern_performance = self._analyze_pattern_performance(trades)
            
            # Market condition performance
            market_condition_performance = self._analyze_market_condition_performance(trades)
            
            # Time-based performance
            time_performance = self._analyze_time_based_performance(trades)
            
            # Risk analysis
            risk_analysis = self._analyze_risk_performance(trades)
            
            # Improvement recommendations
            recommendations = self._generate_improvement_recommendations(
                basic_metrics, pattern_performance, risk_analysis
            )
            
            return {
                'period': f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
                'total_trades': len(trades),
                'basic_metrics': basic_metrics,
                'pattern_performance': pattern_performance,
                'market_condition_performance': market_condition_performance,
                'time_performance': time_performance,
                'risk_analysis': risk_analysis,
                'recommendations': recommendations,
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logging.error(f"Error generating performance analytics: {e}")
            return {'error': str(e)}
    
    def _calculate_basic_performance(self, trades: List) -> Dict:
        """Calculate basic performance metrics"""
        try:
            completed_trades = [t for t in trades if t.outcome in ['win', 'loss', 'breakeven']]
            
            if not completed_trades:
                return {'error': 'No completed trades found'}
            
            wins = [t for t in completed_trades if t.outcome == 'win']
            losses = [t for t in completed_trades if t.outcome == 'loss']
            
            win_rate = (len(wins) / len(completed_trades)) * 100
            
            # Calculate P&L
            total_pnl = sum(t.pnl for t in completed_trades if t.pnl)
            avg_win = sum(t.pnl for t in wins if t.pnl) / len(wins) if wins else 0
            avg_loss = sum(t.pnl for t in losses if t.pnl) / len(losses) if losses else 0
            
            # Profit factor
            gross_profit = sum(t.pnl for t in wins if t.pnl and t.pnl > 0)
            gross_loss = abs(sum(t.pnl for t in losses if t.pnl and t.pnl < 0))
            profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
            
            # Expectancy
            expectancy = (win_rate / 100 * avg_win) + ((1 - win_rate / 100) * avg_loss)
            
            return {
                'total_trades': len(completed_trades),
                'wins': len(wins),
                'losses': len(losses),
                'win_rate': float(win_rate),
                'total_pnl': float(total_pnl),
                'avg_win': float(avg_win),
                'avg_loss': float(avg_loss),
                'profit_factor': float(profit_factor),
                'expectancy': float(expectancy),
                'largest_win': float(max((t.pnl for t in wins if t.pnl), default=0)),
                'largest_loss': float(min((t.pnl for t in losses if t.pnl), default=0))
            }
            
        except Exception as e:
            logging.error(f"Error calculating basic performance: {e}")
            return {'error': str(e)}
    
    def _analyze_pattern_performance(self, trades: List) -> Dict:
        """Analyze performance by pattern type"""
        try:
            pattern_stats = {}
            
            for trade in trades:
                if trade.outcome in ['win', 'loss', 'breakeven'] and hasattr(trade, 'reflection'):
                    # Extract pattern info from reflection (simplified)
                    pattern_type = self._extract_pattern_from_reflection(trade.reflection)
                    
                    if pattern_type not in pattern_stats:
                        pattern_stats[pattern_type] = {
                            'trades': 0,
                            'wins': 0,
                            'total_pnl': 0,
                            'win_rate': 0
                        }
                    
                    pattern_stats[pattern_type]['trades'] += 1
                    if trade.outcome == 'win':
                        pattern_stats[pattern_type]['wins'] += 1
                    if trade.pnl:
                        pattern_stats[pattern_type]['total_pnl'] += trade.pnl
            
            # Calculate win rates
            for pattern, stats in pattern_stats.items():
                if stats['trades'] > 0:
                    stats['win_rate'] = (stats['wins'] / stats['trades']) * 100
            
            # Sort by profitability
            sorted_patterns = dict(sorted(pattern_stats.items(), 
                                        key=lambda x: x[1]['total_pnl'], reverse=True))
            
            return {
                'pattern_breakdown': sorted_patterns,
                'best_pattern': max(pattern_stats.keys(), 
                                  key=lambda k: pattern_stats[k]['total_pnl']) if pattern_stats else None,
                'worst_pattern': min(pattern_stats.keys(), 
                                   key=lambda k: pattern_stats[k]['total_pnl']) if pattern_stats else None
            }
            
        except Exception as e:
            logging.error(f"Error analyzing pattern performance: {e}")
            return {'error': str(e)}
    
    def _analyze_market_condition_performance(self, trades: List) -> Dict:
        """Analyze performance under different market conditions"""
        try:
            condition_stats = {
                'bullish_market': {'trades': 0, 'wins': 0, 'total_pnl': 0},
                'bearish_market': {'trades': 0, 'wins': 0, 'total_pnl': 0},
                'neutral_market': {'trades': 0, 'wins': 0, 'total_pnl': 0},
                'high_volatility': {'trades': 0, 'wins': 0, 'total_pnl': 0},
                'low_volatility': {'trades': 0, 'wins': 0, 'total_pnl': 0}
            }
            
            for trade in trades:
                if trade.outcome in ['win', 'loss', 'breakeven']:
                    # Extract market conditions from reflection (simplified)
                    market_condition = self._extract_market_condition_from_reflection(trade.reflection)
                    
                    if market_condition in condition_stats:
                        condition_stats[market_condition]['trades'] += 1
                        if trade.outcome == 'win':
                            condition_stats[market_condition]['wins'] += 1
                        if trade.pnl:
                            condition_stats[market_condition]['total_pnl'] += trade.pnl
            
            # Calculate win rates
            for condition, stats in condition_stats.items():
                if stats['trades'] > 0:
                    stats['win_rate'] = (stats['wins'] / stats['trades']) * 100
                else:
                    stats['win_rate'] = 0
            
            return condition_stats
            
        except Exception as e:
            logging.error(f"Error analyzing market condition performance: {e}")
            return {'error': str(e)}
    
    def _analyze_time_based_performance(self, trades: List) -> Dict:
        """Analyze performance by time of day, day of week, etc."""
        try:
            time_stats = {
                'by_hour': {},
                'by_day_of_week': {},
                'by_week_of_month': {}
            }
            
            for trade in trades:
                if trade.outcome in ['win', 'loss', 'breakeven'] and trade.created_at:
                    hour = trade.created_at.hour
                    day_of_week = trade.created_at.strftime('%A')
                    week_of_month = (trade.created_at.day - 1) // 7 + 1
                    
                    # Hour analysis
                    if hour not in time_stats['by_hour']:
                        time_stats['by_hour'][hour] = {'trades': 0, 'wins': 0, 'total_pnl': 0}
                    
                    time_stats['by_hour'][hour]['trades'] += 1
                    if trade.outcome == 'win':
                        time_stats['by_hour'][hour]['wins'] += 1
                    if trade.pnl:
                        time_stats['by_hour'][hour]['total_pnl'] += trade.pnl
                    
                    # Day of week analysis
                    if day_of_week not in time_stats['by_day_of_week']:
                        time_stats['by_day_of_week'][day_of_week] = {'trades': 0, 'wins': 0, 'total_pnl': 0}
                    
                    time_stats['by_day_of_week'][day_of_week]['trades'] += 1
                    if trade.outcome == 'win':
                        time_stats['by_day_of_week'][day_of_week]['wins'] += 1
                    if trade.pnl:
                        time_stats['by_day_of_week'][day_of_week]['total_pnl'] += trade.pnl
            
            # Calculate win rates
            for category in time_stats:
                for period, stats in time_stats[category].items():
                    if stats['trades'] > 0:
                        stats['win_rate'] = (stats['wins'] / stats['trades']) * 100
            
            return time_stats
            
        except Exception as e:
            logging.error(f"Error analyzing time-based performance: {e}")
            return {'error': str(e)}
    
    def _analyze_risk_performance(self, trades: List) -> Dict:
        """Analyze risk management performance"""
        try:
            risk_stats = {
                'stop_loss_hit_rate': 0,
                'take_profit_hit_rate': 0,
                'average_risk_per_trade': 0,
                'average_reward_per_trade': 0,
                'risk_reward_adherence': 0,
                'max_consecutive_losses': 0,
                'max_drawdown': 0
            }
            
            completed_trades = [t for t in trades if t.outcome in ['win', 'loss', 'breakeven']]
            
            if not completed_trades:
                return risk_stats
            
            stop_loss_hits = sum(1 for t in completed_trades if t.outcome == 'loss')
            take_profit_hits = sum(1 for t in completed_trades if t.outcome == 'win')
            
            risk_stats['stop_loss_hit_rate'] = (stop_loss_hits / len(completed_trades)) * 100
            risk_stats['take_profit_hit_rate'] = (take_profit_hits / len(completed_trades)) * 100
            
            # Calculate consecutive losses
            consecutive_losses = 0
            max_consecutive = 0
            
            for trade in completed_trades:
                if trade.outcome == 'loss':
                    consecutive_losses += 1
                    max_consecutive = max(max_consecutive, consecutive_losses)
                else:
                    consecutive_losses = 0
            
            risk_stats['max_consecutive_losses'] = max_consecutive
            
            # Calculate drawdown
            running_pnl = 0
            peak_pnl = 0
            max_drawdown = 0
            
            for trade in completed_trades:
                if trade.pnl:
                    running_pnl += trade.pnl
                    peak_pnl = max(peak_pnl, running_pnl)
                    drawdown = peak_pnl - running_pnl
                    max_drawdown = max(max_drawdown, drawdown)
            
            risk_stats['max_drawdown'] = float(max_drawdown)
            
            return risk_stats
            
        except Exception as e:
            logging.error(f"Error analyzing risk performance: {e}")
            return {'error': str(e)}
    
    def _generate_improvement_recommendations(self, basic_metrics: Dict, pattern_performance: Dict, risk_analysis: Dict) -> List[str]:
        """Generate personalized improvement recommendations"""
        recommendations = []
        
        try:
            # Win rate recommendations
            if basic_metrics.get('win_rate', 0) < 50:
                recommendations.append("Focus on improving entry timing - current win rate is below 50%")
            
            # Risk management recommendations
            if risk_analysis.get('max_consecutive_losses', 0) > 3:
                recommendations.append("Consider reducing position size after 2 consecutive losses")
            
            if risk_analysis.get('stop_loss_hit_rate', 0) > 60:
                recommendations.append("Review stop loss placement - stops are being hit too frequently")
            
            # Pattern recommendations
            if pattern_performance.get('best_pattern'):
                recommendations.append(f"Focus more on {pattern_performance['best_pattern']} setups - your most profitable pattern")
            
            if pattern_performance.get('worst_pattern'):
                recommendations.append(f"Avoid or refine {pattern_performance['worst_pattern']} setups")
            
            # Profit factor recommendations
            if basic_metrics.get('profit_factor', 0) < 1.5:
                recommendations.append("Work on letting winners run longer - aim for 2:1 reward to risk minimum")
            
            return recommendations
            
        except Exception as e:
            logging.error(f"Error generating recommendations: {e}")
            return ["Unable to generate specific recommendations due to insufficient data"]
    
    # Helper methods for extracting data from reflections
    def _extract_pattern_from_reflection(self, reflection: str) -> str:
        """Extract pattern type from trade reflection"""
        if not reflection:
            return 'unknown'
        
        patterns = ['bull_flag', 'cup_and_handle', 'triangle', 'breakout', 'reversal', 'continuation']
        for pattern in patterns:
            if pattern in reflection.lower():
                return pattern
        return 'unknown'
    
    def _extract_market_condition_from_reflection(self, reflection: str) -> str:
        """Extract market condition from trade reflection"""
        if not reflection:
            return 'neutral_market'
        
        if 'bullish' in reflection.lower():
            return 'bullish_market'
        elif 'bearish' in reflection.lower():
            return 'bearish_market'
        elif 'volatile' in reflection.lower():
            return 'high_volatility'
        else:
            return 'neutral_market'
    
    # Additional helper methods
    def _get_vix_level(self) -> Dict:
        """Get current VIX level for volatility assessment"""
        try:
            vix = yf.Ticker('^VIX')
            hist = vix.history(period='1d')
            if not hist.empty:
                current_vix = hist['Close'].iloc[-1]
                return {
                    'level': float(current_vix),
                    'category': 'high' if current_vix > 20 else 'low'
                }
        except:
            pass
        return {'level': 20, 'category': 'unknown'}
    
    def _get_sector_performance(self, symbol: str) -> Dict:
        """Get sector performance for the stock's sector"""
        # Simplified sector mapping - could be enhanced with sector lookup
        return {'sector': 'unknown', 'performance': 0}
    
    def _calculate_market_sentiment(self, market_data: Dict) -> str:
        """Calculate overall market sentiment"""
        if not market_data:
            return 'neutral'
        
        positive_indices = sum(1 for data in market_data.values() if data.get('change_pct', 0) > 0)
        total_indices = len(market_data)
        
        if positive_indices / total_indices >= 0.67:
            return 'bullish'
        elif positive_indices / total_indices <= 0.33:
            return 'bearish'
        else:
            return 'neutral'
    
    def _calculate_pattern_success_rate(self, pattern_type: str) -> float:
        """Calculate historical success rate for pattern type"""
        if not pattern_type:
            return 50.0
        
        # Query historical trades with this pattern
        try:
            # This would require pattern type to be stored in database
            # For now, return estimated success rates
            pattern_success_rates = {
                'bull_flag': 65.0,
                'cup_and_handle': 70.0,
                'triangle': 60.0,
                'breakout': 55.0,
                'reversal': 45.0,
                'continuation': 60.0
            }
            return pattern_success_rates.get(pattern_type, 50.0)
        except:
            return 50.0
    
    def _assess_pattern_maturity(self, patterns: Dict) -> str:
        """Assess how mature the current pattern is"""
        if not patterns:
            return 'no_pattern'
        
        completion = patterns.get('completion_percentage', 0)
        if completion >= 80:
            return 'mature'
        elif completion >= 50:
            return 'developing'
        else:
            return 'early'
    
    def _calculate_market_risk_multiplier(self, market_conditions: Dict) -> float:
        """Calculate risk multiplier based on market conditions"""
        base_multiplier = 1.0
        
        try:
            sentiment = market_conditions.get('overall_sentiment', 'neutral')
            vix_level = market_conditions.get('vix_level', {}).get('level', 20)
            
            # Adjust for market sentiment
            if sentiment == 'bearish':
                base_multiplier *= 1.5
            elif sentiment == 'bullish':
                base_multiplier *= 0.8
            
            # Adjust for volatility
            if vix_level > 25:
                base_multiplier *= 1.3
            elif vix_level < 15:
                base_multiplier *= 0.9
            
            return base_multiplier
            
        except:
            return 1.0
    
    def _calculate_composite_risk_score(self, market_conditions: Dict, risk_reward_ratio: float, market_risk_multiplier: float) -> float:
        """Calculate composite risk score (0-100, lower is better)"""
        try:
            base_score = 50
            
            # Adjust for risk/reward
            if risk_reward_ratio >= 2.0:
                base_score -= 20
            elif risk_reward_ratio < 1.0:
                base_score += 30
            
            # Adjust for market conditions
            base_score += (market_risk_multiplier - 1.0) * 20
            
            return max(0, min(100, base_score))
            
        except:
            return 50
    
    def _categorize_risk_level(self, risk_score: float) -> str:
        """Categorize risk level based on score"""
        if risk_score <= 30:
            return 'low'
        elif risk_score <= 60:
            return 'medium'
        else:
            return 'high'
    
    def _generate_trade_recommendations(self, enhanced_data: Dict) -> List[str]:
        """Generate specific recommendations for the trade"""
        recommendations = []
        
        try:
            # Risk-based recommendations
            risk_level = enhanced_data.get('risk_metrics', {}).get('risk_level', 'medium')
            if risk_level == 'high':
                recommendations.append("Consider reducing position size due to high risk environment")
            
            # Pattern-based recommendations
            pattern_analysis = enhanced_data.get('pattern_analysis', {})
            breakout_prob = pattern_analysis.get('breakout_probability', 0)
            if breakout_prob > 70:
                recommendations.append("High breakout probability - consider adding to position on confirmation")
            
            # Market condition recommendations
            market_sentiment = enhanced_data.get('market_conditions', {}).get('overall_sentiment', 'neutral')
            if market_sentiment == 'bearish':
                recommendations.append("Market headwinds present - consider tighter stops")
            
            # Multi-timeframe recommendations
            mtf_analysis = enhanced_data.get('mtf_analysis', {})
            alignment_score = mtf_analysis.get('alignment_score', 0)
            if alignment_score < 50:
                recommendations.append("Low timeframe alignment - wait for better confirmation")
            
            return recommendations
            
        except Exception as e:
            logging.error(f"Error generating trade recommendations: {e}")
            return ["Monitor trade closely and follow your trading plan"]