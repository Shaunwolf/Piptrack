"""
Animated Trading Journey Progress Bar
Visualizes trading progression with smooth animations, milestone tracking, and skill development indicators
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import math
import json

class TradingJourneyProgressBar:
    """Animated progress bar tracking trading journey milestones and skill development"""
    
    def __init__(self):
        self.journey_stages = {
            'novice': {'threshold': 0, 'color': '#ef4444', 'title': 'Learning the Basics'},
            'developing': {'threshold': 100, 'color': '#f97316', 'title': 'Building Skills'},
            'competent': {'threshold': 500, 'color': '#eab308', 'title': 'Gaining Confidence'},
            'proficient': {'threshold': 1500, 'color': '#22c55e', 'title': 'Consistent Performance'},
            'expert': {'threshold': 5000, 'color': '#3b82f6', 'title': 'Trading Mastery'},
            'master': {'threshold': 15000, 'color': '#8b5cf6', 'title': 'Elite Trader'}
        }
        
        self.skill_categories = {
            'technical_analysis': {'weight': 0.25, 'max_score': 1000},
            'risk_management': {'weight': 0.30, 'max_score': 1000},
            'pattern_recognition': {'weight': 0.20, 'max_score': 1000},
            'market_psychology': {'weight': 0.15, 'max_score': 1000},
            'execution_timing': {'weight': 0.10, 'max_score': 1000}
        }
        
        self.achievement_badges = {
            'first_trade': {'points': 50, 'icon': '🎯', 'title': 'First Trade'},
            'profit_streak_5': {'points': 100, 'icon': '🔥', 'title': '5-Trade Win Streak'},
            'perfect_week': {'points': 200, 'icon': '⭐', 'title': 'Perfect Trading Week'},
            'risk_master': {'points': 150, 'icon': '🛡️', 'title': 'Risk Management Master'},
            'pattern_hunter': {'points': 125, 'icon': '🎯', 'title': 'Pattern Recognition Expert'},
            'diamond_hands': {'points': 175, 'icon': '💎', 'title': 'Diamond Hands Discipline'},
            'market_sage': {'points': 300, 'icon': '🧙', 'title': 'Market Psychology Sage'},
            'speed_demon': {'points': 100, 'icon': '⚡', 'title': 'Lightning Fast Execution'},
            'comeback_kid': {'points': 250, 'icon': '🔄', 'title': 'Epic Comeback'},
            'consistency_king': {'points': 400, 'icon': '👑', 'title': 'Consistency Champion'}
        }
        
    def calculate_journey_progress(self, user_stats: Dict) -> Dict:
        """Calculate comprehensive journey progress with animation data"""
        
        # Calculate base experience points
        total_experience = self._calculate_total_experience(user_stats)
        
        # Determine current stage and progress
        current_stage, stage_progress = self._determine_stage_progress(total_experience)
        
        # Calculate skill breakdown
        skill_scores = self._calculate_skill_scores(user_stats)
        
        # Identify earned achievements
        earned_achievements = self._check_achievements(user_stats)
        
        # Generate animation keyframes
        animation_data = self._generate_animation_keyframes(
            total_experience, current_stage, stage_progress, skill_scores
        )
        
        # Calculate milestone predictions
        milestone_predictions = self._predict_milestones(user_stats, total_experience)
        
        return {
            'total_experience': total_experience,
            'current_stage': current_stage,
            'stage_progress': stage_progress,
            'next_stage_threshold': self._get_next_stage_threshold(current_stage),
            'skill_scores': skill_scores,
            'earned_achievements': earned_achievements,
            'available_achievements': self._get_available_achievements(earned_achievements),
            'animation_data': animation_data,
            'milestone_predictions': milestone_predictions,
            'journey_stats': self._generate_journey_stats(user_stats, total_experience),
            'progress_velocity': self._calculate_progress_velocity(user_stats)
        }
    
    def _calculate_total_experience(self, user_stats: Dict) -> int:
        """Calculate total experience points from trading activities"""
        
        experience = 0
        
        # Base points from trades
        total_trades = user_stats.get('total_trades', 0)
        experience += total_trades * 10
        
        # Bonus for profitable trades
        profitable_trades = user_stats.get('profitable_trades', 0)
        experience += profitable_trades * 15
        
        # Win rate bonuses
        win_rate = user_stats.get('win_rate', 0)
        if win_rate > 0.6:
            experience += int(total_trades * (win_rate - 0.6) * 50)
        
        # Risk management points
        avg_risk_reward = user_stats.get('avg_risk_reward_ratio', 1.0)
        if avg_risk_reward > 1.5:
            experience += int(total_trades * (avg_risk_reward - 1.5) * 20)
        
        # Consistency bonuses
        trading_days = user_stats.get('trading_days', 1)
        consistency_bonus = min(trading_days * 5, 1000)
        experience += consistency_bonus
        
        # Pattern recognition points
        patterns_identified = user_stats.get('patterns_identified', 0)
        experience += patterns_identified * 8
        
        # Journal entries bonus
        journal_entries = user_stats.get('journal_entries', 0)
        experience += journal_entries * 5
        
        # Special achievement multipliers
        achievements = user_stats.get('achievements_earned', [])
        for achievement in achievements:
            if achievement in self.achievement_badges:
                experience += self.achievement_badges[achievement]['points']
        
        return max(0, experience)
    
    def _determine_stage_progress(self, total_experience: int) -> Tuple[str, float]:
        """Determine current stage and progress percentage"""
        
        current_stage = 'novice'
        
        for stage, data in reversed(list(self.journey_stages.items())):
            if total_experience >= data['threshold']:
                current_stage = stage
                break
        
        # Calculate progress within current stage
        current_threshold = self.journey_stages[current_stage]['threshold']
        next_threshold = self._get_next_stage_threshold(current_stage)
        
        if next_threshold is None:
            progress = 100.0  # Master level - complete
        else:
            stage_range = next_threshold - current_threshold
            progress_in_stage = total_experience - current_threshold
            progress = min(100.0, (progress_in_stage / stage_range) * 100)
        
        return current_stage, progress
    
    def _get_next_stage_threshold(self, current_stage: str) -> Optional[int]:
        """Get the experience threshold for the next stage"""
        
        stages = list(self.journey_stages.keys())
        try:
            current_index = stages.index(current_stage)
            if current_index < len(stages) - 1:
                next_stage = stages[current_index + 1]
                return self.journey_stages[next_stage]['threshold']
        except ValueError:
            pass
        
        return None
    
    def _calculate_skill_scores(self, user_stats: Dict) -> Dict:
        """Calculate individual skill category scores"""
        
        skill_scores = {}
        
        # Technical Analysis Score
        ta_factors = [
            user_stats.get('patterns_identified', 0) * 2,
            user_stats.get('technical_trades', 0) * 3,
            min(user_stats.get('indicator_accuracy', 0) * 10, 200)
        ]
        skill_scores['technical_analysis'] = min(sum(ta_factors), 1000)
        
        # Risk Management Score
        rm_factors = [
            min(user_stats.get('avg_risk_reward_ratio', 1.0) * 100, 300),
            (1 - user_stats.get('max_drawdown_ratio', 0.2)) * 200,
            user_stats.get('stop_loss_adherence', 0.5) * 300,
            user_stats.get('position_sizing_score', 0.5) * 200
        ]
        skill_scores['risk_management'] = min(sum(rm_factors), 1000)
        
        # Pattern Recognition Score
        pr_factors = [
            user_stats.get('patterns_identified', 0) * 5,
            user_stats.get('pattern_success_rate', 0.5) * 400,
            user_stats.get('early_detection_count', 0) * 8
        ]
        skill_scores['pattern_recognition'] = min(sum(pr_factors), 1000)
        
        # Market Psychology Score
        mp_factors = [
            user_stats.get('emotional_control_score', 0.5) * 300,
            user_stats.get('fomo_resistance_score', 0.5) * 250,
            user_stats.get('patience_score', 0.5) * 200,
            user_stats.get('stress_management_score', 0.5) * 250
        ]
        skill_scores['market_psychology'] = min(sum(mp_factors), 1000)
        
        # Execution Timing Score
        et_factors = [
            user_stats.get('entry_timing_score', 0.5) * 400,
            user_stats.get('exit_timing_score', 0.5) * 400,
            user_stats.get('speed_execution_score', 0.5) * 200
        ]
        skill_scores['execution_timing'] = min(sum(et_factors), 1000)
        
        return skill_scores
    
    def _check_achievements(self, user_stats: Dict) -> List[str]:
        """Check which achievements have been earned"""
        
        earned = []
        
        # First Trade
        if user_stats.get('total_trades', 0) >= 1:
            earned.append('first_trade')
        
        # 5-Trade Win Streak
        if user_stats.get('max_win_streak', 0) >= 5:
            earned.append('profit_streak_5')
        
        # Perfect Week (7 consecutive profitable days)
        if user_stats.get('max_profitable_days_streak', 0) >= 7:
            earned.append('perfect_week')
        
        # Risk Master (avg R:R > 2.0 with 50+ trades)
        if (user_stats.get('avg_risk_reward_ratio', 0) > 2.0 and 
            user_stats.get('total_trades', 0) >= 50):
            earned.append('risk_master')
        
        # Pattern Hunter (50+ patterns identified with 70%+ success)
        if (user_stats.get('patterns_identified', 0) >= 50 and
            user_stats.get('pattern_success_rate', 0) >= 0.7):
            earned.append('pattern_hunter')
        
        # Diamond Hands (held position through 20%+ drawdown for profit)
        if user_stats.get('diamond_hands_count', 0) >= 1:
            earned.append('diamond_hands')
        
        # Market Sage (95%+ emotional control score)
        if user_stats.get('emotional_control_score', 0) >= 0.95:
            earned.append('market_sage')
        
        # Speed Demon (avg execution time < 2 seconds)
        if user_stats.get('avg_execution_time', 10) < 2.0:
            earned.append('speed_demon')
        
        # Comeback Kid (recovered from 30%+ drawdown)
        if user_stats.get('max_comeback_percentage', 0) >= 30:
            earned.append('comeback_kid')
        
        # Consistency King (profitable for 30+ consecutive days)
        if user_stats.get('max_profitable_days_streak', 0) >= 30:
            earned.append('consistency_king')
        
        return earned
    
    def _get_available_achievements(self, earned_achievements: List[str]) -> List[Dict]:
        """Get list of achievements still available to earn"""
        
        available = []
        
        for achievement_id, data in self.achievement_badges.items():
            if achievement_id not in earned_achievements:
                progress = self._calculate_achievement_progress(achievement_id, {})
                available.append({
                    'id': achievement_id,
                    'title': data['title'],
                    'icon': data['icon'],
                    'points': data['points'],
                    'progress': progress,
                    'requirements': self._get_achievement_requirements(achievement_id)
                })
        
        return sorted(available, key=lambda x: x['progress'], reverse=True)
    
    def _calculate_achievement_progress(self, achievement_id: str, user_stats: Dict) -> float:
        """Calculate progress towards a specific achievement"""
        
        # This would be implemented based on specific achievement requirements
        # For now, return a placeholder progress
        return min(50.0, len(user_stats) * 10)
    
    def _get_achievement_requirements(self, achievement_id: str) -> str:
        """Get human-readable requirements for achievement"""
        
        requirements = {
            'first_trade': 'Execute your first trade',
            'profit_streak_5': 'Win 5 trades in a row',
            'perfect_week': 'Be profitable for 7 consecutive days',
            'risk_master': 'Maintain 2:1 risk/reward ratio over 50+ trades',
            'pattern_hunter': 'Identify 50+ patterns with 70%+ success rate',
            'diamond_hands': 'Hold through 20%+ drawdown for eventual profit',
            'market_sage': 'Achieve 95%+ emotional control score',
            'speed_demon': 'Average execution time under 2 seconds',
            'comeback_kid': 'Recover from 30%+ account drawdown',
            'consistency_king': 'Stay profitable for 30+ consecutive days'
        }
        
        return requirements.get(achievement_id, 'Unknown requirements')
    
    def _generate_animation_keyframes(self, total_experience: int, current_stage: str, 
                                    stage_progress: float, skill_scores: Dict) -> Dict:
        """Generate animation keyframes for smooth progress bar transitions"""
        
        keyframes = []
        
        # Main progress bar animation
        progress_keyframes = self._create_progress_keyframes(stage_progress)
        
        # Skill radar chart animation
        skill_keyframes = self._create_skill_keyframes(skill_scores)
        
        # Stage transition effects
        stage_transition = self._create_stage_transition_effects(current_stage)
        
        # Experience counter animation
        experience_animation = self._create_experience_counter_animation(total_experience)
        
        return {
            'progress_bar': progress_keyframes,
            'skill_radar': skill_keyframes,
            'stage_transition': stage_transition,
            'experience_counter': experience_animation,
            'duration': 2500,  # 2.5 seconds total animation
            'easing': 'cubic-bezier(0.4, 0, 0.2, 1)'
        }
    
    def _create_progress_keyframes(self, stage_progress: float) -> List[Dict]:
        """Create keyframes for main progress bar animation"""
        
        return [
            {'time': 0, 'progress': 0, 'opacity': 0.8},
            {'time': 0.3, 'progress': stage_progress * 0.6, 'opacity': 0.9},
            {'time': 0.7, 'progress': stage_progress * 0.9, 'opacity': 1.0},
            {'time': 1.0, 'progress': stage_progress, 'opacity': 1.0}
        ]
    
    def _create_skill_keyframes(self, skill_scores: Dict) -> List[Dict]:
        """Create keyframes for skill radar chart animation"""
        
        keyframes = []
        
        for i, (skill, score) in enumerate(skill_scores.items()):
            normalized_score = score / 1000  # Normalize to 0-1
            
            keyframes.append({
                'skill': skill,
                'keyframes': [
                    {'time': i * 0.1, 'value': 0},
                    {'time': 0.5 + i * 0.1, 'value': normalized_score * 0.8},
                    {'time': 0.8 + i * 0.1, 'value': normalized_score}
                ]
            })
        
        return keyframes
    
    def _create_stage_transition_effects(self, current_stage: str) -> Dict:
        """Create stage transition visual effects"""
        
        stage_color = self.journey_stages[current_stage]['color']
        
        return {
            'stage_name': current_stage,
            'color_transition': {
                'from': '#6b7280',  # Gray
                'to': stage_color,
                'duration': 1000
            },
            'glow_effect': {
                'intensity': [0, 0.5, 1.0, 0.7, 0.5],
                'color': stage_color,
                'duration': 2000
            },
            'particle_burst': {
                'count': 20,
                'color': stage_color,
                'duration': 1500
            }
        }
    
    def _create_experience_counter_animation(self, total_experience: int) -> Dict:
        """Create experience counter animation"""
        
        return {
            'start_value': max(0, total_experience - 100),
            'end_value': total_experience,
            'duration': 2000,
            'easing': 'ease-out',
            'digit_roll_effect': True
        }
    
    def _predict_milestones(self, user_stats: Dict, current_experience: int) -> Dict:
        """Predict when user will reach upcoming milestones"""
        
        # Calculate recent progress velocity
        recent_velocity = self._calculate_progress_velocity(user_stats)
        
        predictions = {}
        
        # Next stage prediction
        next_threshold = self._get_next_stage_threshold(
            self._determine_stage_progress(current_experience)[0]
        )
        
        if next_threshold and recent_velocity > 0:
            experience_needed = next_threshold - current_experience
            days_to_next_stage = max(1, experience_needed / recent_velocity)
            predictions['next_stage'] = {
                'days': int(days_to_next_stage),
                'experience_needed': experience_needed,
                'confidence': self._calculate_prediction_confidence(user_stats)
            }
        
        # Achievement predictions
        predictions['next_achievements'] = self._predict_next_achievements(user_stats)
        
        return predictions
    
    def _calculate_progress_velocity(self, user_stats: Dict) -> float:
        """Calculate recent progress velocity (experience per day)"""
        
        recent_trades = user_stats.get('recent_trades_7d', 0)
        recent_profit_rate = user_stats.get('recent_profit_rate_7d', 0.5)
        
        # Estimate daily experience gain based on recent activity
        daily_trades = recent_trades / 7
        daily_experience = (daily_trades * 10) + (daily_trades * recent_profit_rate * 15)
        
        return max(1.0, daily_experience)
    
    def _calculate_prediction_confidence(self, user_stats: Dict) -> float:
        """Calculate confidence level for milestone predictions"""
        
        factors = [
            min(user_stats.get('trading_days', 1) / 30, 1.0),  # Trading history
            user_stats.get('consistency_score', 0.5),  # Consistency
            min(user_stats.get('recent_trades_7d', 0) / 10, 1.0)  # Recent activity
        ]
        
        return sum(factors) / len(factors)
    
    def _predict_next_achievements(self, user_stats: Dict) -> List[Dict]:
        """Predict which achievements are closest to completion"""
        
        # This would analyze current stats against achievement requirements
        # Return top 3 most achievable
        return [
            {'achievement': 'profit_streak_5', 'probability': 0.7, 'estimated_days': 5},
            {'achievement': 'pattern_hunter', 'probability': 0.5, 'estimated_days': 14},
            {'achievement': 'risk_master', 'probability': 0.3, 'estimated_days': 30}
        ]
    
    def _generate_journey_stats(self, user_stats: Dict, total_experience: int) -> Dict:
        """Generate comprehensive journey statistics"""
        
        return {
            'total_experience': total_experience,
            'rank_percentile': self._calculate_rank_percentile(total_experience),
            'journey_start_date': user_stats.get('first_trade_date', datetime.now().isoformat()),
            'days_trading': user_stats.get('trading_days', 1),
            'total_achievements': len(user_stats.get('achievements_earned', [])),
            'skill_average': sum(self._calculate_skill_scores(user_stats).values()) / 5000 * 100,
            'next_milestone': self._get_next_milestone_description(total_experience),
            'journey_highlights': self._get_journey_highlights(user_stats)
        }
    
    def _calculate_rank_percentile(self, experience: int) -> float:
        """Calculate user's rank percentile based on experience"""
        
        # Simulated percentile calculation
        if experience < 100:
            return experience / 100 * 20
        elif experience < 500:
            return 20 + ((experience - 100) / 400) * 30
        elif experience < 1500:
            return 50 + ((experience - 500) / 1000) * 25
        elif experience < 5000:
            return 75 + ((experience - 1500) / 3500) * 15
        else:
            return min(95, 90 + ((experience - 5000) / 10000) * 5)
    
    def _get_next_milestone_description(self, experience: int) -> str:
        """Get description of next major milestone"""
        
        current_stage, _ = self._determine_stage_progress(experience)
        next_threshold = self._get_next_stage_threshold(current_stage)
        
        if next_threshold:
            stages = list(self.journey_stages.keys())
            current_index = stages.index(current_stage)
            next_stage = stages[current_index + 1]
            return f"Reach {self.journey_stages[next_stage]['title']} level"
        
        return "Maintain trading mastery"
    
    def _get_journey_highlights(self, user_stats: Dict) -> List[str]:
        """Get key highlights from trading journey"""
        
        highlights = []
        
        if user_stats.get('total_trades', 0) >= 100:
            highlights.append(f"Completed {user_stats['total_trades']} trades")
        
        if user_stats.get('win_rate', 0) > 0.6:
            highlights.append(f"{user_stats['win_rate']*100:.1f}% win rate")
        
        if user_stats.get('max_win_streak', 0) >= 5:
            highlights.append(f"{user_stats['max_win_streak']} trade win streak")
        
        if user_stats.get('patterns_identified', 0) >= 20:
            highlights.append(f"Identified {user_stats['patterns_identified']} patterns")
        
        return highlights[:4]  # Return top 4 highlights

    def get_progress_summary(self) -> Dict:
        """Get summary of progress tracking capabilities"""
        
        return {
            'journey_stages': len(self.journey_stages),
            'skill_categories': len(self.skill_categories),
            'available_achievements': len(self.achievement_badges),
            'animation_features': [
                'Smooth progress bar transitions',
                'Skill radar chart animations',
                'Stage transition effects',
                'Experience counter animations',
                'Achievement unlock celebrations'
            ],
            'tracking_metrics': [
                'Total experience points',
                'Individual skill scores',
                'Achievement progress',
                'Milestone predictions',
                'Progress velocity analysis'
            ]
        }