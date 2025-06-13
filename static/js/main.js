// Main JavaScript functionality for AIvest Stock Scanner

// Global state
window.appState = {
    voiceEnabled: true,
    currentStock: null,
    confidenceUpdateInterval: null
};

// Initialize application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    setupEventListeners();
    startConfidenceMonitoring();
});

// Initialize application
function initializeApp() {
    console.log('CandleCast Scanner initialized');
    
    // Check for saved preferences
    const voiceEnabled = localStorage.getItem('voiceEnabled');
    if (voiceEnabled !== null) {
        window.appState.voiceEnabled = voiceEnabled === 'true';
        updateVoiceToggle();
    }
    
    // Initialize any existing confidence dials
    document.querySelectorAll('.confidence-dial').forEach(dial => {
        const confidence = parseInt(dial.dataset.confidence);
        if (!isNaN(confidence)) {
            animateConfidenceDial(confidence);
        }
    });
    
    // Initialize tooltips
    initializeTooltips();
}

// Setup global event listeners
function setupEventListeners() {
    // Voice toggle button
    const voiceToggle = document.getElementById('voiceToggle');
    if (voiceToggle) {
        voiceToggle.addEventListener('click', toggleVoice);
    }
    
    // Modal close listeners
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('modal') || e.target.classList.contains('modal-close')) {
            const modal = e.target.closest('.modal') || e.target;
            if (modal.classList.contains('modal')) {
                closeModal(modal.id);
            }
        }
    });
    
    // Escape key to close modals
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            const openModal = document.querySelector('.modal:not(.hidden)');
            if (openModal) {
                closeModal(openModal.id);
            }
        }
    });
    
    // Form submissions
    document.addEventListener('submit', function(e) {
        if (e.target.tagName === 'FORM') {
            const submitButton = e.target.querySelector('button[type="submit"]');
            if (submitButton) {
                submitButton.disabled = true;
                submitButton.innerHTML = '<i class="fas fa-spinner fa-spin mr-1"></i>Processing...';
                
                // Re-enable after 3 seconds as fallback
                setTimeout(() => {
                    submitButton.disabled = false;
                    submitButton.innerHTML = submitButton.dataset.originalText || 'Submit';
                }, 3000);
            }
        }
    });
}

// Voice functionality
function toggleVoice() {
    window.appState.voiceEnabled = !window.appState.voiceEnabled;
    localStorage.setItem('voiceEnabled', window.appState.voiceEnabled.toString());
    updateVoiceToggle();
    
    if (window.appState.voiceEnabled) {
        speak('Voice alerts enabled');
        showAlert('Voice alerts enabled', 'success');
    } else {
        showAlert('Voice alerts disabled', 'info');
    }
}

function updateVoiceToggle() {
    const voiceToggle = document.getElementById('voiceToggle');
    if (voiceToggle) {
        const icon = voiceToggle.querySelector('i');
        if (window.appState.voiceEnabled) {
            voiceToggle.innerHTML = '<i class="fas fa-volume-up mr-1"></i>Voice: ON';
            voiceToggle.classList.remove('btn-secondary');
            voiceToggle.classList.add('btn-primary');
        } else {
            voiceToggle.innerHTML = '<i class="fas fa-volume-mute mr-1"></i>Voice: OFF';
            voiceToggle.classList.remove('btn-primary');
            voiceToggle.classList.add('btn-secondary');
        }
    }
}

function speak(text) {
    if (!window.appState.voiceEnabled || !('speechSynthesis' in window)) return;
    
    try {
        window.speechSynthesis.cancel(); // Cancel any ongoing speech
        
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 0.9;
        utterance.pitch = 1;
        utterance.volume = 0.8;
        
        window.speechSynthesis.speak(utterance);
    } catch (error) {
        console.error('Speech synthesis error:', error);
    }
}

// Alert system
function showAlert(message, type = 'info', duration = 5000) {
    const alertContainer = document.createElement('div');
    alertContainer.className = `alert alert-${type} fixed top-4 left-1/2 transform -translate-x-1/2 z-50 shadow-lg max-w-md`;
    
    const icon = getAlertIcon(type);
    alertContainer.innerHTML = `
        <div class="flex items-center space-x-2">
            <i class="${icon}"></i>
            <span>${message}</span>
            <button onclick="this.parentElement.parentElement.remove()" class="ml-2 text-gray-400 hover:text-white">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `;
    
    document.body.appendChild(alertContainer);
    
    // Auto-remove after duration
    setTimeout(() => {
        if (alertContainer.parentNode) {
            alertContainer.remove();
        }
    }, duration);
    
    // Add animation
    alertContainer.style.opacity = '0';
    alertContainer.style.transform = 'translate(-50%, -20px)';
    
    requestAnimationFrame(() => {
        alertContainer.style.transition = 'all 0.3s ease-out';
        alertContainer.style.opacity = '1';
        alertContainer.style.transform = 'translate(-50%, 0)';
    });
}

function getAlertIcon(type) {
    const icons = {
        success: 'fas fa-check-circle',
        error: 'fas fa-exclamation-triangle',
        warning: 'fas fa-exclamation-circle',
        info: 'fas fa-info-circle'
    };
    return icons[type] || icons.info;
}

// Modal system
function showModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('hidden');
        modal.classList.add('show');
        
        // Focus first input if available
        const firstInput = modal.querySelector('input, select, textarea');
        if (firstInput) {
            setTimeout(() => firstInput.focus(), 100);
        }
        
        // Prevent body scrolling
        document.body.style.overflow = 'hidden';
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('hidden');
        modal.classList.remove('show');
        
        // Restore body scrolling
        document.body.style.overflow = '';
        
        // Clear form data if it's a form modal
        const form = modal.querySelector('form');
        if (form) {
            form.reset();
        }
    }
}

// Loading states
function showLoading() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.classList.remove('hidden');
    }
}

function hideLoading() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.classList.add('hidden');
    }
}

// Confidence monitoring
function startConfidenceMonitoring() {
    // Update confidence scores every 5 minutes for tracked stocks
    window.appState.confidenceUpdateInterval = setInterval(async () => {
        try {
            const response = await fetch('/update_confidence_scores', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'}
            });
            
            const data = await response.json();
            if (data.success) {
                updateConfidenceScores(data.scores);
                
                // Check for high confidence alerts
                data.scores.forEach(stock => {
                    if (stock.score >= 80) {
                        triggerConfidenceAlert(stock.symbol, stock.score);
                    }
                });
            }
        } catch (error) {
            console.error('Error updating confidence scores:', error);
        }
    }, 5 * 60 * 1000); // 5 minutes
}

function updateConfidenceScores(scores) {
    scores.forEach(stock => {
        // Update confidence badges
        const badges = document.querySelectorAll(`[data-symbol="${stock.symbol}"] .confidence-badge`);
        badges.forEach(badge => {
            badge.textContent = `${stock.score}%`;
            
            // Update badge class
            badge.className = 'confidence-badge';
            if (stock.score >= 70) {
                badge.classList.add('confidence-high');
            } else if (stock.score >= 40) {
                badge.classList.add('confidence-medium');
            } else {
                badge.classList.add('confidence-low');
            }
        });
        
        // Update confidence dials
        const dials = document.querySelectorAll(`[data-symbol="${stock.symbol}"] .confidence-dial`);
        dials.forEach(dial => {
            updateConfidenceDial(dial, stock.score);
        });
    });
}

function triggerConfidenceAlert(symbol, score) {
    const message = `${symbol} confidence reached ${score}% - High breakout potential!`;
    
    // Show visual alert
    showAlert(message, 'success', 8000);
    
    // Trigger voice alert
    if (window.appState.voiceEnabled) {
        speak(message);
    }
    
    // Play sound effect
    playAlertSound();
}

function playAlertSound() {
    const audio = document.getElementById('alertSound');
    if (audio) {
        audio.currentTime = 0;
        audio.play().catch(e => console.log('Audio play failed:', e));
    }
}

// Utility functions
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 2
    }).format(amount);
}

function formatPercentage(value) {
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
}

function formatNumber(number) {
    if (number >= 1e9) {
        return (number / 1e9).toFixed(1) + 'B';
    } else if (number >= 1e6) {
        return (number / 1e6).toFixed(1) + 'M';
    } else if (number >= 1e3) {
        return (number / 1e3).toFixed(1) + 'K';
    }
    return number.toString();
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Initialize tooltips
function initializeTooltips() {
    // Simple tooltip implementation
    document.querySelectorAll('[title]').forEach(element => {
        element.addEventListener('mouseenter', showTooltip);
        element.addEventListener('mouseleave', hideTooltip);
    });
}

function showTooltip(e) {
    const tooltip = document.createElement('div');
    tooltip.className = 'tooltip fixed bg-dark-surface text-white px-2 py-1 rounded shadow-lg text-sm z-50 pointer-events-none';
    tooltip.textContent = e.target.title;
    
    document.body.appendChild(tooltip);
    
    const rect = e.target.getBoundingClientRect();
    tooltip.style.left = rect.left + rect.width / 2 - tooltip.offsetWidth / 2 + 'px';
    tooltip.style.top = rect.top - tooltip.offsetHeight - 5 + 'px';
    
    e.target.setAttribute('data-original-title', e.target.title);
    e.target.removeAttribute('title');
    e.target.tooltipElement = tooltip;
}

function hideTooltip(e) {
    if (e.target.tooltipElement) {
        e.target.tooltipElement.remove();
        e.target.tooltipElement = null;
    }
    
    const originalTitle = e.target.getAttribute('data-original-title');
    if (originalTitle) {
        e.target.title = originalTitle;
        e.target.removeAttribute('data-original-title');
    }
}

// API request wrapper
async function apiRequest(url, options = {}) {
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
        },
    };
    
    const mergedOptions = { ...defaultOptions, ...options };
    
    try {
        const response = await fetch(url, mergedOptions);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('API request failed:', error);
        throw error;
    }
}

// Performance monitoring
function trackPerformance(name, fn) {
    return async function(...args) {
        const start = performance.now();
        try {
            const result = await fn.apply(this, args);
            const end = performance.now();
            console.log(`${name} took ${end - start} milliseconds`);
            return result;
        } catch (error) {
            const end = performance.now();
            console.error(`${name} failed after ${end - start} milliseconds:`, error);
            throw error;
        }
    };
}

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    if (window.appState.confidenceUpdateInterval) {
        clearInterval(window.appState.confidenceUpdateInterval);
    }
    
    // Cancel any ongoing speech
    if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
    }
});

// Export functions for global access
window.showAlert = showAlert;
window.showModal = showModal;
window.closeModal = closeModal;
window.showLoading = showLoading;
window.hideLoading = hideLoading;
window.speak = speak;
window.formatCurrency = formatCurrency;
window.formatPercentage = formatPercentage;
window.formatNumber = formatNumber;
window.apiRequest = apiRequest;
