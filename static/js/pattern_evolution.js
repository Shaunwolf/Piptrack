// Pattern Evolution Tracker with Breakout Timing Predictions

// Global pattern evolution state
window.patternEvolutionState = {
    currentEvolutions: new Map(),
    updateInterval: null,
    lastUpdate: null
};

// Initialize pattern evolution functionality
document.addEventListener('DOMContentLoaded', function() {
    initializePatternEvolution();
    setupPatternEvolutionListeners();
});

// Initialize pattern evolution system
function initializePatternEvolution() {
    console.log('Pattern Evolution Tracker initialized');
    
    // Load existing pattern data
    loadAllPatternEvolutions();
    
    // Set up auto-update every 5 minutes
    window.patternEvolutionState.updateInterval = setInterval(() => {
        updateAllPatternEvolutions();
    }, 300000); // 5 minutes
    
    // Add pattern evolution indicators to stock cards
    addPatternEvolutionIndicators();
}

// Setup event listeners for pattern evolution
function setupPatternEvolutionListeners() {
    // Pattern evolution button clicks
    document.addEventListener('click', function(e) {
        if (e.target.closest('.pattern-evolution-btn')) {
            e.preventDefault();
            const symbol = e.target.closest('.pattern-evolution-btn').dataset.symbol;
            if (symbol) {
                showPatternEvolutionModal(symbol);
            }
        }
    });
    
    // Breakout timing alerts
    document.addEventListener('click', function(e) {
        if (e.target.closest('.breakout-timing-btn')) {
            e.preventDefault();
            const symbol = e.target.closest('.breakout-timing-btn').dataset.symbol;
            if (symbol) {
                showBreakoutTimingAlert(symbol);
            }
        }
    });
    
    // Update pattern evolutions button
    const updateBtn = document.getElementById('updatePatternEvolutions');
    if (updateBtn) {
        updateBtn.addEventListener('click', updateAllPatternEvolutions);
    }
}

// Load all pattern evolutions for tracked stocks
async function loadAllPatternEvolutions() {
    try {
        const response = await fetch('/pattern_evolution/all');
        const data = await response.json();
        
        if (data.success) {
            window.patternEvolutionState.currentEvolutions.clear();
            
            Object.entries(data.evolutions).forEach(([symbol, evolution]) => {
                window.patternEvolutionState.currentEvolutions.set(symbol, evolution);
            });
            
            updatePatternEvolutionUI();
            window.patternEvolutionState.lastUpdate = new Date();
            
            console.log(`Loaded pattern evolutions for ${Object.keys(data.evolutions).length} stocks`);
        }
    } catch (error) {
        console.error('Error loading pattern evolutions:', error);
    }
}

// Update all pattern evolutions
async function updateAllPatternEvolutions() {
    try {
        showLoading();
        
        const response = await fetch('/update_pattern_evolutions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        const data = await response.json();
        
        if (data.success) {
            showAlert(`Updated pattern evolution for ${data.updated_count} stocks`, 'success');
            
            // Reload all evolutions
            await loadAllPatternEvolutions();
        } else {
            showAlert('Failed to update pattern evolutions', 'error');
        }
        
    } catch (error) {
        console.error('Error updating pattern evolutions:', error);
        showAlert('Error updating pattern evolutions', 'error');
    } finally {
        hideLoading();
    }
}

// Get pattern evolution for specific symbol
async function getPatternEvolution(symbol) {
    try {
        const response = await fetch(`/pattern_evolution/${symbol}`);
        const data = await response.json();
        
        if (data.success) {
            // Update local cache
            if (data.evolution && data.evolution.patterns.length > 0) {
                const pattern = data.evolution.patterns[0]; // Use first/primary pattern
                window.patternEvolutionState.currentEvolutions.set(symbol, {
                    pattern_type: pattern.pattern_type,
                    confidence_score: pattern.confidence,
                    stage: pattern.current_stage,
                    completion_percentage: pattern.completion_percentage,
                    estimated_days_to_breakout: pattern.breakout_prediction.estimated_days_to_breakout,
                    breakout_probability_5_days: pattern.breakout_prediction.breakout_probability_next_5_days,
                    direction_bias: pattern.breakout_prediction.direction_bias,
                    timing_confidence: pattern.breakout_prediction.timing_confidence,
                    updated_at: new Date().toISOString()
                });
            }
            
            return data.evolution;
        }
        
        return null;
        
    } catch (error) {
        console.error(`Error getting pattern evolution for ${symbol}:`, error);
        return null;
    }
}

// Add pattern evolution indicators to stock cards
function addPatternEvolutionIndicators() {
    document.querySelectorAll('.stock-card').forEach(card => {
        const symbol = card.dataset.symbol;
        if (symbol && !card.querySelector('.pattern-evolution-indicator')) {
            addPatternIndicatorToCard(card, symbol);
        }
    });
}

// Add pattern indicator to specific stock card
function addPatternIndicatorToCard(card, symbol) {
    const evolution = window.patternEvolutionState.currentEvolutions.get(symbol);
    
    if (evolution) {
        // Add breakout timing badge
        const confidenceBadge = card.querySelector('.confidence-badge');
        if (confidenceBadge && !card.querySelector('.pattern-evolution-indicator')) {
            const patternIndicator = document.createElement('div');
            patternIndicator.className = 'pattern-evolution-indicator mt-2';
            
            const breakoutDays = evolution.estimated_days_to_breakout;
            const breakoutProb = Math.round(evolution.breakout_probability_5_days * 100);
            const direction = evolution.direction_bias > 0.6 ? 'bullish' : evolution.direction_bias < 0.4 ? 'bearish' : 'neutral';
            
            patternIndicator.innerHTML = `
                <div class="flex items-center justify-between text-xs">
                    <span class="text-gray-400">${evolution.pattern_type}</span>
                    <span class="pattern-stage ${getStageColor(evolution.stage)}">${evolution.stage}</span>
                </div>
                <div class="flex items-center justify-between text-xs mt-1">
                    <span class="breakout-timing ${getUrgencyColor(breakoutDays)}">~${breakoutDays}d to breakout</span>
                    <span class="breakout-probability ${getDirectionColor(direction)}">${breakoutProb}% ${direction}</span>
                </div>
                <div class="pattern-progress-bar mt-1">
                    <div class="w-full bg-gray-600 rounded-full h-1">
                        <div class="bg-accent-blue h-1 rounded-full" style="width: ${evolution.completion_percentage * 100}%"></div>
                    </div>
                </div>
            `;
            
            confidenceBadge.parentNode.insertBefore(patternIndicator, confidenceBadge.nextSibling);
        }
        
        // Add pattern evolution button to action buttons
        const actionButtons = card.querySelector('.flex.space-x-2');
        if (actionButtons && !card.querySelector('.pattern-evolution-btn')) {
            const patternBtn = document.createElement('button');
            patternBtn.className = 'btn-secondary pattern-evolution-btn';
            patternBtn.dataset.symbol = symbol;
            patternBtn.title = 'Pattern Evolution';
            patternBtn.innerHTML = '<i class="fas fa-chart-line"></i>';
            
            actionButtons.appendChild(patternBtn);
        }
    }
}

// Update pattern evolution UI for all cards
function updatePatternEvolutionUI() {
    window.patternEvolutionState.currentEvolutions.forEach((evolution, symbol) => {
        const card = document.querySelector(`[data-symbol="${symbol}"]`);
        if (card) {
            // Remove existing indicator
            const existingIndicator = card.querySelector('.pattern-evolution-indicator');
            if (existingIndicator) {
                existingIndicator.remove();
            }
            
            // Add updated indicator
            addPatternIndicatorToCard(card, symbol);
            
            // Update breakout alerts if needed
            checkBreakoutAlert(symbol, evolution);
        }
    });
}

// Show pattern evolution modal for specific symbol
async function showPatternEvolutionModal(symbol) {
    try {
        showLoading();
        
        const evolution = await getPatternEvolution(symbol);
        
        if (evolution && evolution.patterns.length > 0) {
            const pattern = evolution.patterns[0];
            const breakoutPred = pattern.breakout_prediction;
            const patternEvol = pattern.evolution;
            
            const modal = createPatternEvolutionModal(symbol, pattern, breakoutPred, patternEvol);
            document.body.appendChild(modal);
            showModal('patternEvolutionModal');
        } else {
            showAlert('No pattern evolution data available for ' + symbol, 'info');
        }
        
    } catch (error) {
        console.error('Error showing pattern evolution modal:', error);
        showAlert('Error loading pattern evolution data', 'error');
    } finally {
        hideLoading();
    }
}

// Create pattern evolution modal
function createPatternEvolutionModal(symbol, pattern, breakoutPred, evolution) {
    // Remove existing modal if present
    const existingModal = document.getElementById('patternEvolutionModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    const modal = document.createElement('div');
    modal.id = 'patternEvolutionModal';
    modal.className = 'modal';
    
    const directionBias = breakoutPred.direction_bias > 0.6 ? 'Bullish' : 
                         breakoutPred.direction_bias < 0.4 ? 'Bearish' : 'Neutral';
    
    modal.innerHTML = `
        <div class="modal-content max-w-4xl">
            <div class="modal-header">
                <h3 class="text-xl font-bold flex items-center">
                    <i class="fas fa-chart-line text-accent-blue mr-2"></i>
                    Pattern Evolution - ${symbol}
                </h3>
                <button onclick="closeModal('patternEvolutionModal')" class="modal-close">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="modal-body">
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <!-- Pattern Overview -->
                    <div class="space-y-4">
                        <div class="bg-dark-accent rounded-lg p-4">
                            <h4 class="font-semibold text-accent-blue mb-3">Pattern Overview</h4>
                            <div class="space-y-2">
                                <div class="flex justify-between">
                                    <span class="text-gray-400">Type:</span>
                                    <span class="font-semibold">${pattern.pattern_type}</span>
                                </div>
                                <div class="flex justify-between">
                                    <span class="text-gray-400">Stage:</span>
                                    <span class="px-2 py-1 rounded text-xs font-semibold ${getStageColor(pattern.current_stage)}">${pattern.current_stage}</span>
                                </div>
                                <div class="flex justify-between">
                                    <span class="text-gray-400">Confidence:</span>
                                    <span class="font-semibold">${Math.round(pattern.confidence * 100)}%</span>
                                </div>
                                <div class="flex justify-between">
                                    <span class="text-gray-400">Completion:</span>
                                    <span class="font-semibold">${Math.round(pattern.completion_percentage * 100)}%</span>
                                </div>
                                <div class="flex justify-between">
                                    <span class="text-gray-400">Time in Pattern:</span>
                                    <span class="font-semibold">${pattern.time_in_pattern} days</span>
                                </div>
                            </div>
                            
                            <!-- Progress Bar -->
                            <div class="mt-4">
                                <div class="flex justify-between text-xs text-gray-400 mb-1">
                                    <span>Pattern Progress</span>
                                    <span>${Math.round(pattern.completion_percentage * 100)}%</span>
                                </div>
                                <div class="w-full bg-gray-600 rounded-full h-2">
                                    <div class="bg-gradient-to-r from-accent-blue to-accent-green h-2 rounded-full" 
                                         style="width: ${pattern.completion_percentage * 100}%"></div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Evolution Metrics -->
                        <div class="bg-dark-accent rounded-lg p-4">
                            <h4 class="font-semibold text-accent-blue mb-3">Evolution Metrics</h4>
                            <div class="space-y-3">
                                ${renderEvolutionMetric('Volatility Trend', evolution.volatility_trend)}
                                ${renderEvolutionMetric('Volume Trend', evolution.volume_trend)}
                                ${renderEvolutionMetric('Momentum Change', evolution.momentum_change)}
                                ${renderEvolutionMetric('S/R Strength', evolution.support_resistance_strength)}
                            </div>
                        </div>
                    </div>
                    
                    <!-- Breakout Prediction -->
                    <div class="space-y-4">
                        <div class="bg-dark-accent rounded-lg p-4">
                            <h4 class="font-semibold text-accent-blue mb-3">Breakout Timing Prediction</h4>
                            <div class="space-y-4">
                                <!-- Timing Estimate -->
                                <div class="text-center p-4 bg-dark-surface rounded-lg">
                                    <div class="text-2xl font-bold ${getUrgencyColor(breakoutPred.estimated_days_to_breakout)}">
                                        ${breakoutPred.estimated_days_to_breakout} Days
                                    </div>
                                    <div class="text-sm text-gray-400">Estimated to Breakout</div>
                                </div>
                                
                                <!-- Probability Gauges -->
                                <div class="grid grid-cols-2 gap-4">
                                    <div class="text-center">
                                        <div class="text-lg font-semibold">${Math.round(breakoutPred.breakout_probability_next_5_days * 100)}%</div>
                                        <div class="text-xs text-gray-400">5-Day Probability</div>
                                    </div>
                                    <div class="text-center">
                                        <div class="text-lg font-semibold">${Math.round(breakoutPred.breakout_probability_next_10_days * 100)}%</div>
                                        <div class="text-xs text-gray-400">10-Day Probability</div>
                                    </div>
                                </div>
                                
                                <!-- Direction Bias -->
                                <div class="text-center p-3 bg-dark-surface rounded-lg">
                                    <div class="text-lg font-semibold ${getDirectionColor(directionBias.toLowerCase())}">${directionBias} Bias</div>
                                    <div class="text-sm text-gray-400">${Math.round(breakoutPred.direction_bias * 100)}% Bullish Probability</div>
                                </div>
                                
                                <!-- Timing Confidence -->
                                <div class="space-y-2">
                                    <div class="flex justify-between text-sm">
                                        <span class="text-gray-400">Timing Confidence</span>
                                        <span class="font-semibold">${Math.round(breakoutPred.timing_confidence * 100)}%</span>
                                    </div>
                                    <div class="w-full bg-gray-600 rounded-full h-2">
                                        <div class="bg-accent-green h-2 rounded-full" style="width: ${breakoutPred.timing_confidence * 100}%"></div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Key Levels -->
                        ${breakoutPred.key_levels ? renderKeyLevels(breakoutPred.key_levels) : ''}
                        
                        <!-- Action Recommendations -->
                        <div class="bg-dark-accent rounded-lg p-4">
                            <h4 class="font-semibold text-accent-blue mb-3">Action Recommendations</h4>
                            <div class="space-y-2 text-sm">
                                ${generateActionRecommendations(breakoutPred, pattern)}
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Action Buttons -->
                <div class="flex space-x-3 mt-6 pt-4 border-t border-dark-accent">
                    <a href="/forecast/${symbol}" class="btn-primary flex-1">
                        <i class="fas fa-chart-area mr-1"></i>View Forecast
                    </a>
                    <button onclick="setBreakoutAlert('${symbol}')" class="btn-secondary flex-1">
                        <i class="fas fa-bell mr-1"></i>Set Alert
                    </button>
                    <button onclick="exportPatternEvolution('${symbol}')" class="btn-secondary">
                        <i class="fas fa-download"></i>
                    </button>
                </div>
            </div>
        </div>
    `;
    
    return modal;
}

// Render evolution metric with visual indicator
function renderEvolutionMetric(label, value) {
    const absValue = Math.abs(value);
    const direction = value > 0 ? 'positive' : value < 0 ? 'negative' : 'neutral';
    const color = direction === 'positive' ? 'text-accent-green' : 
                  direction === 'negative' ? 'text-accent-red' : 'text-gray-400';
    
    return `
        <div class="flex items-center justify-between">
            <span class="text-gray-400 text-sm">${label}</span>
            <div class="flex items-center space-x-2">
                <div class="w-16 h-1 bg-gray-600 rounded-full overflow-hidden">
                    <div class="h-full ${direction === 'positive' ? 'bg-accent-green' : direction === 'negative' ? 'bg-accent-red' : 'bg-gray-400'}" 
                         style="width: ${Math.min(absValue * 100, 100)}%"></div>
                </div>
                <span class="text-xs font-semibold w-12 text-right ${color}">
                    ${value > 0 ? '+' : ''}${(value * 100).toFixed(1)}%
                </span>
            </div>
        </div>
    `;
}

// Render key levels section
function renderKeyLevels(levels) {
    return `
        <div class="bg-dark-accent rounded-lg p-4">
            <h4 class="font-semibold text-accent-blue mb-3">Key Levels</h4>
            <div class="space-y-2 text-sm">
                <div class="flex justify-between">
                    <span class="text-gray-400">Resistance:</span>
                    <span class="font-semibold text-accent-red">$${levels.resistance_level?.toFixed(2) || 'N/A'}</span>
                </div>
                <div class="flex justify-between">
                    <span class="text-gray-400">Support:</span>
                    <span class="font-semibold text-accent-green">$${levels.support_level?.toFixed(2) || 'N/A'}</span>
                </div>
                <div class="flex justify-between">
                    <span class="text-gray-400">Breakout Confirm:</span>
                    <span class="font-semibold text-accent-blue">$${levels.breakout_confirmation?.toFixed(2) || 'N/A'}</span>
                </div>
                <div class="flex justify-between">
                    <span class="text-gray-400">Breakdown Confirm:</span>
                    <span class="font-semibold text-yellow-500">$${levels.breakdown_confirmation?.toFixed(2) || 'N/A'}</span>
                </div>
            </div>
        </div>
    `;
}

// Generate action recommendations
function generateActionRecommendations(breakoutPred, pattern) {
    const recommendations = [];
    
    if (breakoutPred.estimated_days_to_breakout <= 3) {
        recommendations.push('<i class="fas fa-exclamation-triangle text-yellow-500 mr-1"></i>Breakout imminent - watch closely');
    }
    
    if (breakoutPred.breakout_probability_next_5_days > 0.7) {
        recommendations.push('<i class="fas fa-arrow-up text-accent-green mr-1"></i>High breakout probability - consider entry');
    }
    
    if (breakoutPred.volume_confirmation_needed) {
        recommendations.push('<i class="fas fa-volume-up text-accent-blue mr-1"></i>Wait for volume confirmation');
    }
    
    if (pattern.completion_percentage < 0.8) {
        recommendations.push('<i class="fas fa-clock text-gray-400 mr-1"></i>Pattern still developing - be patient');
    }
    
    if (breakoutPred.timing_confidence < 0.6) {
        recommendations.push('<i class="fas fa-question-circle text-yellow-500 mr-1"></i>Low timing confidence - use wider stops');
    }
    
    return recommendations.map(rec => `<div>${rec}</div>`).join('');
}

// Get color class for pattern stage
function getStageColor(stage) {
    const stageColors = {
        'forming': 'text-gray-400 bg-gray-600',
        'building': 'text-accent-blue bg-blue-600',
        'mature': 'text-accent-green bg-green-600',
        'apex_approaching': 'text-yellow-500 bg-yellow-600'
    };
    return stageColors[stage] || 'text-gray-400 bg-gray-600';
}

// Get color class for urgency (days to breakout)
function getUrgencyColor(days) {
    if (days <= 2) return 'text-accent-red';
    if (days <= 5) return 'text-yellow-500';
    if (days <= 10) return 'text-accent-blue';
    return 'text-gray-400';
}

// Get color class for direction bias
function getDirectionColor(direction) {
    const colors = {
        'bullish': 'text-accent-green',
        'bearish': 'text-accent-red',
        'neutral': 'text-gray-400'
    };
    return colors[direction] || 'text-gray-400';
}

// Check for breakout alerts
function checkBreakoutAlert(symbol, evolution) {
    const daysToBreakout = evolution.estimated_days_to_breakout;
    const probability = evolution.breakout_probability_5_days;
    
    // Alert for imminent breakouts with high probability
    if (daysToBreakout <= 2 && probability > 0.7) {
        triggerBreakoutTimingAlert(symbol, daysToBreakout, probability);
    }
}

// Trigger breakout timing alert
function triggerBreakoutTimingAlert(symbol, days, probability) {
    const message = `${symbol} breakout expected in ${days} day${days > 1 ? 's' : ''} with ${Math.round(probability * 100)}% probability`;
    
    // Show visual alert
    showAlert(message, 'warning', 8000);
    
    // Trigger voice alert if enabled
    if (window.voiceAlertState && window.voiceAlertState.isEnabled) {
        queueVoiceAlert(message, 'high', { priority: 'breakout_timing' });
    }
    
    // Show desktop notification if supported
    if ('Notification' in window && Notification.permission === 'granted') {
        new Notification('Breakout Timing Alert', {
            body: message,
            icon: '/static/images/icon.png'
        });
    }
}

// Show breakout timing alert for specific symbol
function showBreakoutTimingAlert(symbol) {
    const evolution = window.patternEvolutionState.currentEvolutions.get(symbol);
    
    if (evolution) {
        const days = evolution.estimated_days_to_breakout;
        const probability = Math.round(evolution.breakout_probability_5_days * 100);
        const direction = evolution.direction_bias > 0.6 ? 'bullish' : evolution.direction_bias < 0.4 ? 'bearish' : 'neutral';
        
        showAlert(`${symbol}: ${evolution.pattern_type} breakout in ~${days} days (${probability}% ${direction})`, 'info', 6000);
    }
}

// Set breakout alert for symbol
function setBreakoutAlert(symbol) {
    // This would integrate with the voice alert system
    showAlert(`Breakout alert set for ${symbol}`, 'success');
    closeModal('patternEvolutionModal');
}

// Export pattern evolution data
function exportPatternEvolution(symbol) {
    const evolution = window.patternEvolutionState.currentEvolutions.get(symbol);
    
    if (evolution) {
        const data = {
            symbol: symbol,
            pattern_evolution: evolution,
            exported_at: new Date().toISOString()
        };
        
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `${symbol}_pattern_evolution.json`;
        link.click();
        URL.revokeObjectURL(url);
        
        showAlert(`Pattern evolution data exported for ${symbol}`, 'success');
    }
}

// Clean up when page unloads
window.addEventListener('beforeunload', function() {
    if (window.patternEvolutionState.updateInterval) {
        clearInterval(window.patternEvolutionState.updateInterval);
    }
});

// Export functions for global access
window.getPatternEvolution = getPatternEvolution;
window.showPatternEvolutionModal = showPatternEvolutionModal;
window.updateAllPatternEvolutions = updateAllPatternEvolutions;
window.setBreakoutAlert = setBreakoutAlert;
window.exportPatternEvolution = exportPatternEvolution;