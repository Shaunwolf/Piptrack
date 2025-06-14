"""
Animated Trading Journey Progress Bar
Tracks user progress through different stages of trading development
"""

import json
from datetime import datetime, timedelta
from app import db
from models import TradeJournal, Stock
import logging

class TradingJourney:
    def __init__(self):
        self.journey_stages = [
            {
                'id': 'novice',
                'name': 'Market Observer',
                'description': 'Learning market basics and building watchlists',
                'color': '#3B82F6',
                'icon': 'fa-eye',
                'requirements': {
                    'stocks_analyzed': 5,
                    'days_active': 3,
                    'forecasts_generated': 3
                },
                'xp_required': 0
            },
            {
                'id': 'beginner',
                'name': 'Pattern Spotter',
                'description': 'Identifying chart patterns and technical signals',
                'color': '#10B981',
                'icon': 'fa-chart-line',
                'requirements': {
                    'stocks_analyzed': 15,
                    'patterns_identified': 5,
                    'forecasts_generated': 10,
                    'confidence_scores_above_70': 3
                },
                'xp_required': 100
            },
            {
                'id': 'intermediate',
                'name': 'Risk Manager',
                'description': 'Managing risk and developing discipline',
                'color': '#F59E0B',
                'icon': 'fa-shield-alt',
                'requirements': {
                    'trades_logged': 5,
                    'positive_risk_reward_trades': 3,
                    'journal_entries': 10,
                    'checklist_completions': 5
                },
                'xp_required': 300
            },
            {
                'id': 'advanced',
                'name': 'Strategy Builder',
                'description': 'Creating and testing trading strategies',
                'color': '#8B5CF6',
                'icon': 'fa-cogs',
                'requirements': {
                    'trades_logged': 20,
                    'win_rate_above_60': True,
                    'avg_risk_reward_above_2': True,
                    'consecutive_profitable_weeks': 2
                },
                'xp_required': 750
            },
            {
                'id': 'expert',
                'name': 'Market Analyst',
                'description': 'Advanced market analysis and forecasting',
                'color': '#EF4444',
                'icon': 'fa-brain',
                'requirements': {
                    'trades_logged': 50,
                    'win_rate_above_70': True,
                    'max_drawdown_below_10': True,
                    'consistent_profits_3_months': True
                },
                'xp_required': 1500
            },
            {
                'id': 'master',
                'name': 'Trading Master',
                'description': 'Consistent profitable trading with refined edge',
                'color': '#6366F1',
                'icon': 'fa-crown',
                'requirements': {
                    'trades_logged': 100,
                    'win_rate_above_75': True,
                    'sharpe_ratio_above_2': True,
                    'teaching_contributions': 5
                },
                'xp_required': 3000
            }
        ]
        
    def calculate_user_progress(self, user_id=None):
        """Calculate user's current progress and stage"""
        try:
            # Get user statistics from database
            stats = self._get_user_stats(user_id)
            
            # Calculate current stage and progress
            current_stage = self._determine_current_stage(stats)
            next_stage = self._get_next_stage(current_stage['id'])
            
            # Calculate progress percentages
            stage_progress = self._calculate_stage_progress(stats, current_stage, next_stage)
            overall_progress = self._calculate_overall_progress(current_stage['id'])
            
            # Calculate XP and achievements
            xp_data = self._calculate_xp(stats)
            achievements = self._check_achievements(stats)
            
            return {
                'current_stage': current_stage,
                'next_stage': next_stage,
                'stage_progress': stage_progress,
                'overall_progress': overall_progress,
                'xp_data': xp_data,
                'achievements': achievements,
                'stats': stats,
                'milestones': self._get_upcoming_milestones(stats, next_stage),
                'badges': self._get_earned_badges(stats)
            }
            
        except Exception as e:
            logging.error(f"Error calculating user progress: {e}")
            return self._get_default_progress()
    
    def _get_user_stats(self, user_id=None):
        """Get comprehensive user statistics"""
        try:
            # Count trades and journal entries
            trades_count = TradeJournal.query.count()
            
            # Count stocks analyzed (from database)
            stocks_analyzed = Stock.query.count()
            
            # Calculate days active (simplified - based on data in database)
            first_trade = TradeJournal.query.order_by(TradeJournal.id.asc()).first()
            days_active = 1
            if first_trade:
                days_active = max(1, (datetime.now() - first_trade.timestamp).days + 1)
            
            # Get trade performance metrics
            trades = TradeJournal.query.all()
            
            profitable_trades = 0
            total_pnl = 0.0
            risk_reward_trades = 0
            max_drawdown = 0.0
            
            for trade in trades:
                try:
                    # Parse trade data
                    if hasattr(trade, 'pnl') and trade.pnl:
                        pnl = float(trade.pnl) if isinstance(trade.pnl, str) else trade.pnl
                        total_pnl += pnl
                        if pnl > 0:
                            profitable_trades += 1
                    
                    # Check risk/reward ratio
                    if hasattr(trade, 'risk_reward_ratio'):
                        rr = float(trade.risk_reward_ratio) if trade.risk_reward_ratio else 0
                        if rr >= 2.0:
                            risk_reward_trades += 1
                            
                except (ValueError, AttributeError):
                    continue
            
            win_rate = (profitable_trades / len(trades) * 100) if trades else 0
            avg_risk_reward = risk_reward_trades / len(trades) if trades else 0
            
            return {
                'stocks_analyzed': stocks_analyzed,
                'days_active': days_active,
                'forecasts_generated': stocks_analyzed,  # Simplified
                'trades_logged': trades_count,
                'journal_entries': trades_count,
                'win_rate': win_rate,
                'profitable_trades': profitable_trades,
                'total_pnl': total_pnl,
                'avg_risk_reward': avg_risk_reward,
                'risk_reward_trades': risk_reward_trades,
                'max_drawdown': max_drawdown,
                'patterns_identified': min(stocks_analyzed, 10),  # Estimated
                'confidence_scores_above_70': min(stocks_analyzed // 2, 5),  # Estimated
                'checklist_completions': trades_count,  # Simplified
                'consecutive_profitable_weeks': self._calculate_consecutive_weeks(trades),
                'sharpe_ratio': self._calculate_sharpe_ratio(trades),
                'teaching_contributions': 0  # Future feature
            }
            
        except Exception as e:
            logging.error(f"Error getting user stats: {e}")
            return self._get_default_stats()
    
    def _determine_current_stage(self, stats):
        """Determine user's current stage based on stats"""
        current_stage = self.journey_stages[0]  # Default to novice
        
        for stage in self.journey_stages:
            if self._meets_requirements(stats, stage['requirements']):
                current_stage = stage
            else:
                break
                
        return current_stage
    
    def _meets_requirements(self, stats, requirements):
        """Check if user meets all requirements for a stage"""
        for req_key, req_value in requirements.items():
            if req_key not in stats:
                return False
                
            user_value = stats[req_key]
            
            if isinstance(req_value, bool):
                if not user_value:
                    return False
            elif isinstance(req_value, (int, float)):
                if user_value < req_value:
                    return False
                    
        return True
    
    def _get_next_stage(self, current_stage_id):
        """Get the next stage after current"""
        current_index = next(i for i, stage in enumerate(self.journey_stages) if stage['id'] == current_stage_id)
        
        if current_index < len(self.journey_stages) - 1:
            return self.journey_stages[current_index + 1]
        else:
            return None  # Already at max stage
    
    def _calculate_stage_progress(self, stats, current_stage, next_stage):
        """Calculate progress towards next stage"""
        if not next_stage:
            return 100  # Already at max stage
        
        requirements = next_stage['requirements']
        progress_items = []
        total_progress = 0
        
        for req_key, req_value in requirements.items():
            if req_key in stats:
                user_value = stats[req_key]
                
                if isinstance(req_value, bool):
                    progress = 100 if user_value else 0
                elif isinstance(req_value, (int, float)):
                    progress = min(100, (user_value / req_value) * 100)
                else:
                    progress = 0
                
                progress_items.append({
                    'requirement': req_key.replace('_', ' ').title(),
                    'current': user_value,
                    'required': req_value,
                    'progress': progress,
                    'completed': progress >= 100
                })
                
                total_progress += progress
        
        avg_progress = total_progress / len(requirements) if requirements else 100
        
        return {
            'percentage': min(100, avg_progress),
            'items': progress_items
        }
    
    def _calculate_overall_progress(self, current_stage_id):
        """Calculate overall progress through all stages"""
        current_index = next(i for i, stage in enumerate(self.journey_stages) if stage['id'] == current_stage_id)
        return ((current_index + 1) / len(self.journey_stages)) * 100
    
    def _calculate_xp(self, stats):
        """Calculate XP based on user activities"""
        xp = 0
        
        # XP from different activities
        xp += stats.get('stocks_analyzed', 0) * 10
        xp += stats.get('trades_logged', 0) * 25
        xp += stats.get('profitable_trades', 0) * 15
        xp += stats.get('journal_entries', 0) * 5
        xp += stats.get('patterns_identified', 0) * 20
        xp += stats.get('days_active', 0) * 2
        
        # Bonus XP for achievements
        if stats.get('win_rate', 0) > 70:
            xp += 200
        if stats.get('avg_risk_reward', 0) > 2:
            xp += 150
        if stats.get('consecutive_profitable_weeks', 0) > 2:
            xp += 300
        
        return {
            'total': xp,
            'daily_earned': min(50, xp // max(1, stats.get('days_active', 1))),
            'weekly_earned': min(200, xp // max(1, stats.get('days_active', 1) // 7))
        }
    
    def _check_achievements(self, stats):
        """Check for unlocked achievements"""
        achievements = []
        
        # Trading volume achievements
        if stats.get('trades_logged', 0) >= 10:
            achievements.append({
                'name': 'Active Trader',
                'description': 'Logged 10+ trades',
                'icon': 'fa-chart-bar',
                'color': '#10B981',
                'unlocked_date': datetime.now().strftime('%Y-%m-%d')
            })
        
        if stats.get('trades_logged', 0) >= 50:
            achievements.append({
                'name': 'Trading Veteran',
                'description': 'Logged 50+ trades',
                'icon': 'fa-medal',
                'color': '#F59E0B',
                'unlocked_date': datetime.now().strftime('%Y-%m-%d')
            })
        
        # Performance achievements
        if stats.get('win_rate', 0) >= 70:
            achievements.append({
                'name': 'Consistent Winner',
                'description': '70%+ win rate',
                'icon': 'fa-trophy',
                'color': '#EF4444',
                'unlocked_date': datetime.now().strftime('%Y-%m-%d')
            })
        
        # Analysis achievements
        if stats.get('stocks_analyzed', 0) >= 25:
            achievements.append({
                'name': 'Market Researcher',
                'description': 'Analyzed 25+ stocks',
                'icon': 'fa-search',
                'color': '#8B5CF6',
                'unlocked_date': datetime.now().strftime('%Y-%m-%d')
            })
        
        # Risk management achievements
        if stats.get('avg_risk_reward', 0) >= 2:
            achievements.append({
                'name': 'Risk Master',
                'description': 'Average R:R ratio above 2:1',
                'icon': 'fa-shield-alt',
                'color': '#6366F1',
                'unlocked_date': datetime.now().strftime('%Y-%m-%d')
            })
        
        return achievements
    
    def _get_upcoming_milestones(self, stats, next_stage):
        """Get upcoming milestones to work towards"""
        if not next_stage:
            return []
        
        milestones = []
        requirements = next_stage['requirements']
        
        for req_key, req_value in requirements.items():
            if req_key in stats:
                user_value = stats[req_key]
                
                if isinstance(req_value, (int, float)) and user_value < req_value:
                    remaining = req_value - user_value
                    milestones.append({
                        'name': req_key.replace('_', ' ').title(),
                        'current': user_value,
                        'target': req_value,
                        'remaining': remaining,
                        'percentage': (user_value / req_value) * 100
                    })
        
        return sorted(milestones, key=lambda x: x['percentage'], reverse=True)
    
    def _get_earned_badges(self, stats):
        """Get earned badges based on achievements"""
        badges = []
        
        # Consecutive achievements
        days_active = stats.get('days_active', 0)
        if days_active >= 7:
            badges.append({'name': '7-Day Streak', 'icon': 'fa-fire', 'color': '#F59E0B'})
        if days_active >= 30:
            badges.append({'name': '30-Day Streak', 'icon': 'fa-fire', 'color': '#EF4444'})
        
        # Performance badges
        if stats.get('win_rate', 0) >= 80:
            badges.append({'name': 'Elite Trader', 'icon': 'fa-star', 'color': '#6366F1'})
        
        # Volume badges
        trades = stats.get('trades_logged', 0)
        if trades >= 100:
            badges.append({'name': 'Century Club', 'icon': 'fa-certificate', 'color': '#10B981'})
        
        return badges
    
    def _calculate_consecutive_weeks(self, trades):
        """Calculate consecutive profitable weeks"""
        if not trades:
            return 0
        
        # Simplified calculation - would need more sophisticated logic in production
        return min(2, len(trades) // 10)
    
    def _calculate_sharpe_ratio(self, trades):
        """Calculate Sharpe ratio from trades"""
        if not trades or len(trades) < 5:
            return 0
        
        # Simplified calculation
        profitable_count = sum(1 for trade in trades if hasattr(trade, 'pnl') and trade.pnl and float(trade.pnl) > 0)
        return (profitable_count / len(trades)) * 2  # Simplified Sharpe approximation
    
    def _get_default_stats(self):
        """Default stats when calculation fails"""
        return {
            'stocks_analyzed': 0,
            'days_active': 1,
            'forecasts_generated': 0,
            'trades_logged': 0,
            'journal_entries': 0,
            'win_rate': 0,
            'profitable_trades': 0,
            'total_pnl': 0,
            'avg_risk_reward': 0,
            'risk_reward_trades': 0,
            'max_drawdown': 0,
            'patterns_identified': 0,
            'confidence_scores_above_70': 0,
            'checklist_completions': 0,
            'consecutive_profitable_weeks': 0,
            'sharpe_ratio': 0,
            'teaching_contributions': 0
        }
    
    def _get_default_progress(self):
        """Default progress when calculation fails"""
        return {
            'current_stage': self.journey_stages[0],
            'next_stage': self.journey_stages[1],
            'stage_progress': {'percentage': 0, 'items': []},
            'overall_progress': 0,
            'xp_data': {'total': 0, 'daily_earned': 0, 'weekly_earned': 0},
            'achievements': [],
            'stats': self._get_default_stats(),
            'milestones': [],
            'badges': []
        }
    
    def get_leaderboard_data(self):
        """Get leaderboard data for competitive elements"""
        # This would be implemented with user accounts in production
        return {
            'top_traders': [
                {'name': 'Anonymous Trader', 'xp': 1250, 'stage': 'Strategy Builder', 'win_rate': 75.5},
                {'name': 'Current User', 'xp': 0, 'stage': 'Market Observer', 'win_rate': 0}
            ],
            'weekly_challenge': {
                'name': 'Pattern Master',
                'description': 'Identify 5 chart patterns this week',
                'progress': 0,
                'reward': '50 XP + Pattern Badge'
            }
        }
    
    def award_xp(self, activity, amount):
        """Award XP for specific activities"""
        # This would be implemented with user sessions in production
        logging.info(f"Awarded {amount} XP for {activity}")
        return {'success': True, 'xp_awarded': amount}