/**
 * Animated Trading Journey Progress Bar
 * Interactive progress tracking with smooth animations and gamification
 */

class TradingJourneyManager {
    constructor() {
        this.currentProgress = null;
        this.animationSpeed = 1000; // 1 second
        this.initializeProgressBar();
    }

    async initializeProgressBar() {
        try {
            const response = await fetch('/api/trading_journey');
            const data = await response.json();
            
            if (data.success) {
                this.currentProgress = data.progress;
                this.renderProgressBar();
                this.startAnimations();
            }
        } catch (error) {
            console.error('Error loading trading journey:', error);
            this.renderFallbackProgress();
        }
    }

    renderProgressBar() {
        const container = document.getElementById('trading-journey-container');
        if (!container) return;

        const progress = this.currentProgress;
        
        container.innerHTML = `
            <div class="trading-journey-card">
                <!-- Header Section -->
                <div class="journey-header">
                    <div class="flex items-center justify-between">
                        <div class="flex items-center space-x-4">
                            <div class="current-stage-icon" style="background: ${progress.current_stage.color}">
                                <i class="fas ${progress.current_stage.icon}"></i>
                            </div>
                            <div>
                                <h3 class="stage-title">${progress.current_stage.name}</h3>
                                <p class="stage-description">${progress.current_stage.description}</p>
                            </div>
                        </div>
                        <div class="xp-display">
                            <div class="xp-amount">${progress.xp_data.total}</div>
                            <div class="xp-label">Total XP</div>
                        </div>
                    </div>
                </div>

                <!-- Progress Bar Section -->
                <div class="progress-section">
                    ${this.renderStageProgressBar(progress)}
                    ${this.renderOverallProgressBar(progress)}
                </div>

                <!-- Milestones Section -->
                ${this.renderMilestones(progress)}

                <!-- Achievements Section -->
                ${this.renderAchievements(progress)}

                <!-- Badges Section -->
                ${this.renderBadges(progress)}
            </div>
        `;

        this.addEventListeners();
    }

    renderStageProgressBar(progress) {
        const nextStage = progress.next_stage;
        if (!nextStage) {
            return `
                <div class="stage-progress completed">
                    <div class="progress-header">
                        <span class="progress-title">🎉 Journey Complete!</span>
                        <span class="progress-percentage">100%</span>
                    </div>
                    <div class="progress-bar-container">
                        <div class="progress-bar complete" style="width: 100%"></div>
                    </div>
                    <p class="progress-subtitle">You've mastered all trading stages!</p>
                </div>
            `;
        }

        return `
            <div class="stage-progress">
                <div class="progress-header">
                    <span class="progress-title">Progress to ${nextStage.name}</span>
                    <span class="progress-percentage">${Math.round(progress.stage_progress.percentage)}%</span>
                </div>
                <div class="progress-bar-container">
                    <div class="progress-bar animated" 
                         style="width: 0%; background: linear-gradient(90deg, ${progress.current_stage.color}, ${nextStage.color})"
                         data-target="${progress.stage_progress.percentage}">
                    </div>
                    <div class="progress-glow" style="background: ${nextStage.color}"></div>
                </div>
                <div class="progress-requirements">
                    ${progress.stage_progress.items.map(item => `
                        <div class="requirement-item ${item.completed ? 'completed' : ''}">
                            <div class="requirement-icon">
                                <i class="fas ${item.completed ? 'fa-check' : 'fa-clock'}"></i>
                            </div>
                            <span class="requirement-text">${item.requirement}</span>
                            <span class="requirement-progress">${item.current}/${item.required}</span>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    renderOverallProgressBar(progress) {
        return `
            <div class="overall-progress">
                <div class="progress-header">
                    <span class="progress-title">Overall Journey Progress</span>
                    <span class="progress-percentage">${Math.round(progress.overall_progress)}%</span>
                </div>
                <div class="journey-stages">
                    ${this.renderJourneyStages(progress)}
                </div>
            </div>
        `;
    }

    renderJourneyStages(progress) {
        const currentStageId = progress.current_stage.id;
        let stageHtml = '';

        // Get all stages from the journey system
        const stages = [
            { id: 'novice', name: 'Observer', color: '#3B82F6', icon: 'fa-eye' },
            { id: 'beginner', name: 'Spotter', color: '#10B981', icon: 'fa-chart-line' },
            { id: 'intermediate', name: 'Manager', color: '#F59E0B', icon: 'fa-shield-alt' },
            { id: 'advanced', name: 'Builder', color: '#8B5CF6', icon: 'fa-cogs' },
            { id: 'expert', name: 'Analyst', color: '#EF4444', icon: 'fa-brain' },
            { id: 'master', name: 'Master', color: '#6366F1', icon: 'fa-crown' }
        ];

        stages.forEach((stage, index) => {
            const isCompleted = this.getStageIndex(currentStageId) > index;
            const isCurrent = stage.id === currentStageId;
            
            stageHtml += `
                <div class="journey-stage ${isCompleted ? 'completed' : ''} ${isCurrent ? 'current' : ''}"
                     style="--stage-color: ${stage.color}">
                    <div class="stage-connector ${index < stages.length - 1 ? 'has-next' : ''}"></div>
                    <div class="stage-circle">
                        <i class="fas ${stage.icon}"></i>
                    </div>
                    <div class="stage-label">${stage.name}</div>
                </div>
            `;
        });

        return stageHtml;
    }

    renderMilestones(progress) {
        if (!progress.milestones || progress.milestones.length === 0) {
            return '';
        }

        return `
            <div class="milestones-section">
                <h4 class="section-title">
                    <i class="fas fa-flag-checkered mr-2"></i>
                    Upcoming Milestones
                </h4>
                <div class="milestones-grid">
                    ${progress.milestones.slice(0, 3).map(milestone => `
                        <div class="milestone-card">
                            <div class="milestone-header">
                                <span class="milestone-name">${milestone.name}</span>
                                <span class="milestone-percentage">${Math.round(milestone.percentage)}%</span>
                            </div>
                            <div class="milestone-progress-bar">
                                <div class="milestone-fill" style="width: ${milestone.percentage}%"></div>
                            </div>
                            <div class="milestone-details">
                                <span class="milestone-current">${milestone.current}</span>
                                <span class="milestone-separator">/</span>
                                <span class="milestone-target">${milestone.target}</span>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    renderAchievements(progress) {
        if (!progress.achievements || progress.achievements.length === 0) {
            return '';
        }

        return `
            <div class="achievements-section">
                <h4 class="section-title">
                    <i class="fas fa-trophy mr-2"></i>
                    Recent Achievements
                </h4>
                <div class="achievements-grid">
                    ${progress.achievements.map(achievement => `
                        <div class="achievement-card unlocked" style="--achievement-color: ${achievement.color}">
                            <div class="achievement-icon">
                                <i class="fas ${achievement.icon}"></i>
                            </div>
                            <div class="achievement-info">
                                <div class="achievement-name">${achievement.name}</div>
                                <div class="achievement-description">${achievement.description}</div>
                                <div class="achievement-date">Unlocked ${achievement.unlocked_date}</div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    renderBadges(progress) {
        if (!progress.badges || progress.badges.length === 0) {
            return '';
        }

        return `
            <div class="badges-section">
                <h4 class="section-title">
                    <i class="fas fa-medal mr-2"></i>
                    Earned Badges
                </h4>
                <div class="badges-container">
                    ${progress.badges.map(badge => `
                        <div class="badge-item" style="--badge-color: ${badge.color}">
                            <i class="fas ${badge.icon}"></i>
                            <span class="badge-name">${badge.name}</span>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    startAnimations() {
        // Animate progress bars
        requestAnimationFrame(() => {
            this.animateProgressBars();
            this.animateCounters();
            this.animateStageHighlight();
        });
    }

    animateProgressBars() {
        const progressBars = document.querySelectorAll('.progress-bar.animated');
        
        progressBars.forEach((bar, index) => {
            setTimeout(() => {
                const targetWidth = bar.getAttribute('data-target');
                bar.style.transition = `width ${this.animationSpeed}ms ease-out`;
                bar.style.width = `${targetWidth}%`;
                
                // Add glow effect
                setTimeout(() => {
                    bar.classList.add('glowing');
                }, this.animationSpeed / 2);
            }, index * 200);
        });

        // Animate milestone progress bars
        const milestoneBars = document.querySelectorAll('.milestone-fill');
        milestoneBars.forEach((bar, index) => {
            setTimeout(() => {
                const width = bar.style.width;
                bar.style.width = '0%';
                bar.style.transition = `width ${this.animationSpeed * 0.8}ms ease-out`;
                requestAnimationFrame(() => {
                    bar.style.width = width;
                });
            }, (index + 1) * 300);
        });
    }

    animateCounters() {
        const counters = document.querySelectorAll('.xp-amount, .progress-percentage');
        
        counters.forEach(counter => {
            const target = parseInt(counter.textContent);
            let current = 0;
            const increment = target / 50; // 50 steps
            const stepTime = this.animationSpeed / 50;
            
            const updateCounter = () => {
                current += increment;
                if (current < target) {
                    counter.textContent = Math.floor(current);
                    setTimeout(updateCounter, stepTime);
                } else {
                    counter.textContent = target;
                }
            };
            
            counter.textContent = '0';
            setTimeout(updateCounter, 500);
        });
    }

    animateStageHighlight() {
        const currentStage = document.querySelector('.journey-stage.current');
        if (currentStage) {
            setTimeout(() => {
                currentStage.classList.add('pulse');
            }, this.animationSpeed);
        }
    }

    addEventListeners() {
        // Add hover effects for interactive elements
        const achievements = document.querySelectorAll('.achievement-card');
        achievements.forEach(card => {
            card.addEventListener('mouseenter', () => {
                card.classList.add('hover-glow');
            });
            card.addEventListener('mouseleave', () => {
                card.classList.remove('hover-glow');
            });
        });

        // Add click handlers for badges
        const badges = document.querySelectorAll('.badge-item');
        badges.forEach(badge => {
            badge.addEventListener('click', () => {
                this.showBadgeDetails(badge);
            });
        });

        // Add click handlers for stages
        const stages = document.querySelectorAll('.journey-stage');
        stages.forEach(stage => {
            stage.addEventListener('click', () => {
                this.showStageDetails(stage);
            });
        });
    }

    showBadgeDetails(badge) {
        const badgeName = badge.querySelector('.badge-name').textContent;
        this.showTooltip(badge, `Badge: ${badgeName}`, 'Earned through consistent performance!');
    }

    showStageDetails(stage) {
        const stageName = stage.querySelector('.stage-label').textContent;
        this.showTooltip(stage, `Stage: ${stageName}`, 'Click to view detailed requirements');
    }

    showTooltip(element, title, content) {
        // Create tooltip element
        const tooltip = document.createElement('div');
        tooltip.className = 'journey-tooltip';
        tooltip.innerHTML = `
            <div class="tooltip-title">${title}</div>
            <div class="tooltip-content">${content}</div>
        `;
        
        document.body.appendChild(tooltip);
        
        // Position tooltip
        const rect = element.getBoundingClientRect();
        tooltip.style.left = `${rect.left + rect.width / 2}px`;
        tooltip.style.top = `${rect.top - 10}px`;
        
        // Auto-remove after 3 seconds
        setTimeout(() => {
            if (tooltip.parentNode) {
                tooltip.parentNode.removeChild(tooltip);
            }
        }, 3000);
    }

    getStageIndex(stageId) {
        const stages = ['novice', 'beginner', 'intermediate', 'advanced', 'expert', 'master'];
        return stages.indexOf(stageId);
    }

    renderFallbackProgress() {
        const container = document.getElementById('trading-journey-container');
        if (!container) return;

        container.innerHTML = `
            <div class="trading-journey-card">
                <div class="journey-header">
                    <div class="flex items-center space-x-4">
                        <div class="current-stage-icon" style="background: #3B82F6">
                            <i class="fas fa-eye"></i>
                        </div>
                        <div>
                            <h3 class="stage-title">Market Observer</h3>
                            <p class="stage-description">Starting your trading journey</p>
                        </div>
                    </div>
                    <div class="xp-display">
                        <div class="xp-amount">0</div>
                        <div class="xp-label">Total XP</div>
                    </div>
                </div>
                <div class="progress-section">
                    <div class="stage-progress">
                        <div class="progress-header">
                            <span class="progress-title">Begin your journey</span>
                            <span class="progress-percentage">0%</span>
                        </div>
                        <div class="progress-bar-container">
                            <div class="progress-bar" style="width: 0%; background: #3B82F6"></div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    // Public methods for external integration
    async updateProgress() {
        await this.initializeProgressBar();
    }

    async awardXP(activity, amount) {
        try {
            const response = await fetch('/api/award_xp', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ activity, amount })
            });
            
            const data = await response.json();
            if (data.success) {
                this.showXPNotification(amount, activity);
                setTimeout(() => this.updateProgress(), 1000);
            }
        } catch (error) {
            console.error('Error awarding XP:', error);
        }
    }

    showXPNotification(amount, activity) {
        const notification = document.createElement('div');
        notification.className = 'xp-notification';
        notification.innerHTML = `
            <div class="xp-notification-content">
                <i class="fas fa-star"></i>
                <span>+${amount} XP</span>
                <small>${activity}</small>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.classList.add('show');
        }, 100);
        
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }
}

// Global instance
window.tradingJourney = new TradingJourneyManager();

// Auto-award XP for various activities
document.addEventListener('DOMContentLoaded', () => {
    // Award XP for page visits
    if (window.location.pathname.includes('/forecast/') || window.location.pathname.includes('/forecast_enhanced/')) {
        setTimeout(() => {
            window.tradingJourney.awardXP('Stock Analysis', 10);
        }, 2000);
    }
    
    if (window.location.pathname.includes('/journal')) {
        setTimeout(() => {
            window.tradingJourney.awardXP('Journal Visit', 5);
        }, 2000);
    }
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TradingJourneyManager;
}