// Voice alerts and speech synthesis functionality

// Global voice alert state
window.voiceAlertState = {
    isEnabled: true,
    volume: 0.8,
    rate: 0.9,
    pitch: 1.0,
    voice: null,
    alertQueue: [],
    isPlaying: false,
    lastAlert: null,
    alertHistory: []
};

// Initialize voice alerts
document.addEventListener('DOMContentLoaded', function() {
    initializeVoiceAlerts();
    setupVoiceEventListeners();
    loadVoicePreferences();
});

// Initialize voice alert system
function initializeVoiceAlerts() {
    console.log('Voice alerts system initialized');
    
    // Check for speech synthesis support
    if (!('speechSynthesis' in window)) {
        console.warn('Speech synthesis not supported');
        window.voiceAlertState.isEnabled = false;
        return;
    }
    
    // Load available voices
    loadAvailableVoices();
    
    // Set up voice change listener
    if (speechSynthesis.onvoiceschanged !== undefined) {
        speechSynthesis.onvoiceschanged = loadAvailableVoices;
    }
    
    // Initialize UI elements
    initializeVoiceUI();
}

// Setup voice-related event listeners
function setupVoiceEventListeners() {
    // Voice toggle button
    const voiceToggle = document.getElementById('voiceToggle');
    if (voiceToggle) {
        voiceToggle.addEventListener('click', toggleVoiceAlerts);
    }
    
    // Voice settings modal (if exists)
    const voiceSettingsBtn = document.getElementById('voiceSettingsBtn');
    if (voiceSettingsBtn) {
        voiceSettingsBtn.addEventListener('click', showVoiceSettings);
    }
    
    // Listen for confidence updates that might trigger alerts
    document.addEventListener('confidenceUpdate', function(e) {
        const { symbol, score, previousScore } = e.detail;
        if (score >= 80 && (!previousScore || previousScore < 80)) {
            triggerConfidenceAlert(symbol, score);
        }
    });
    
    // Listen for breakout alerts
    document.addEventListener('breakoutAlert', function(e) {
        const { symbol, price, breakoutType } = e.detail;
        triggerBreakoutAlert(symbol, price, breakoutType);
    });
}

// Load available voices
function loadAvailableVoices() {
    const voices = speechSynthesis.getVoices();
    
    // Prefer English voices
    const englishVoices = voices.filter(voice => voice.lang.startsWith('en'));
    
    // Set default voice (prefer female, then male, then any)
    const preferredVoice = englishVoices.find(voice => 
        voice.name.toLowerCase().includes('female') || 
        voice.name.toLowerCase().includes('samantha') ||
        voice.name.toLowerCase().includes('karen')
    ) || englishVoices.find(voice => 
        voice.name.toLowerCase().includes('male') ||
        voice.name.toLowerCase().includes('daniel')
    ) || englishVoices[0] || voices[0];
    
    if (preferredVoice) {
        window.voiceAlertState.voice = preferredVoice;
        console.log('Selected voice:', preferredVoice.name);
    }
}

// Initialize voice UI elements
function initializeVoiceUI() {
    // Update voice toggle based on current state
    updateVoiceToggleUI();
    
    // Add voice settings button if not present
    addVoiceSettingsButton();
}

// Toggle voice alerts on/off
function toggleVoiceAlerts() {
    window.voiceAlertState.isEnabled = !window.voiceAlertState.isEnabled;
    
    // Save preference
    localStorage.setItem('voiceAlertsEnabled', window.voiceAlertState.isEnabled);
    
    // Update UI
    updateVoiceToggleUI();
    
    // Provide feedback
    if (window.voiceAlertState.isEnabled) {
        speak('Voice alerts enabled');
        showAlert('Voice alerts enabled', 'success');
    } else {
        // Cancel any ongoing speech
        speechSynthesis.cancel();
        showAlert('Voice alerts disabled', 'info');
    }
}

// Update voice toggle UI
function updateVoiceToggleUI() {
    const voiceToggle = document.getElementById('voiceToggle');
    if (!voiceToggle) return;
    
    if (window.voiceAlertState.isEnabled) {
        voiceToggle.innerHTML = '<i class="fas fa-volume-up mr-1"></i>Voice: ON';
        voiceToggle.classList.remove('btn-secondary');
        voiceToggle.classList.add('btn-primary');
    } else {
        voiceToggle.innerHTML = '<i class="fas fa-volume-mute mr-1"></i>Voice: OFF';
        voiceToggle.classList.remove('btn-primary');
        voiceToggle.classList.add('btn-secondary');
    }
}

// Add voice settings button to navbar
function addVoiceSettingsButton() {
    const navbar = document.querySelector('nav .flex.items-center.space-x-4');
    if (navbar && !document.getElementById('voiceSettingsBtn')) {
        const settingsBtn = document.createElement('button');
        settingsBtn.id = 'voiceSettingsBtn';
        settingsBtn.className = 'btn-secondary';
        settingsBtn.title = 'Voice Settings';
        settingsBtn.innerHTML = '<i class="fas fa-cog"></i>';
        settingsBtn.addEventListener('click', showVoiceSettings);
        
        navbar.insertBefore(settingsBtn, navbar.firstChild);
    }
}

// Main speak function
function speak(text, options = {}) {
    if (!window.voiceAlertState.isEnabled || !('speechSynthesis' in window)) {
        return;
    }
    
    if (!text || text.trim() === '') {
        return;
    }
    
    try {
        // Cancel any ongoing speech
        speechSynthesis.cancel();
        
        // Create utterance
        const utterance = new SpeechSynthesisUtterance(text);
        
        // Apply settings
        utterance.volume = options.volume || window.voiceAlertState.volume;
        utterance.rate = options.rate || window.voiceAlertState.rate;
        utterance.pitch = options.pitch || window.voiceAlertState.pitch;
        
        if (window.voiceAlertState.voice) {
            utterance.voice = window.voiceAlertState.voice;
        }
        
        // Set up event listeners
        utterance.onstart = () => {
            window.voiceAlertState.isPlaying = true;
            console.log('Voice alert started:', text);
        };
        
        utterance.onend = () => {
            window.voiceAlertState.isPlaying = false;
            processAlertQueue();
        };
        
        utterance.onerror = (event) => {
            console.error('Speech synthesis error:', event.error);
            window.voiceAlertState.isPlaying = false;
            processAlertQueue();
        };
        
        // Speak the utterance
        speechSynthesis.speak(utterance);
        
        // Log the alert
        logVoiceAlert(text, options.priority || 'normal');
        
    } catch (error) {
        console.error('Error in speak function:', error);
        window.voiceAlertState.isPlaying = false;
    }
}

// Queue voice alert
function queueVoiceAlert(text, priority = 'normal', options = {}) {
    const alert = {
        text,
        priority,
        options,
        timestamp: Date.now()
    };
    
    // Add to queue based on priority
    if (priority === 'high') {
        window.voiceAlertState.alertQueue.unshift(alert);
    } else {
        window.voiceAlertState.alertQueue.push(alert);
    }
    
    // Process queue if not currently playing
    if (!window.voiceAlertState.isPlaying) {
        processAlertQueue();
    }
}

// Process alert queue
function processAlertQueue() {
    if (window.voiceAlertState.alertQueue.length === 0 || window.voiceAlertState.isPlaying) {
        return;
    }
    
    const nextAlert = window.voiceAlertState.alertQueue.shift();
    if (nextAlert) {
        speak(nextAlert.text, nextAlert.options);
    }
}

// Trigger confidence alert
function triggerConfidenceAlert(symbol, confidence) {
    const messages = [
        `${symbol} confidence reached ${confidence} percent - high breakout potential`,
        `Alert: ${symbol} showing strong setup at ${confidence} percent confidence`,
        `${symbol} confidence spike to ${confidence} percent - watch closely`
    ];
    
    const message = messages[Math.floor(Math.random() * messages.length)];
    
    // Queue high priority alert
    queueVoiceAlert(message, 'high', { 
        priority: 'confidence',
        symbol,
        confidence 
    });
    
    // Show visual alert
    showVoiceAlertNotification(message, 'confidence', symbol);
    
    // Play alert sound
    playAlertSound('confidence');
}

// Trigger breakout alert
function triggerBreakoutAlert(symbol, price, breakoutType = 'bullish') {
    const messages = {
        bullish: [
            `${symbol} breaking out above resistance at ${price} dollars`,
            `Bullish breakout alert: ${symbol} at ${price} dollars`,
            `${symbol} momentum breakout confirmed at ${price} dollars`
        ],
        bearish: [
            `${symbol} breaking down below support at ${price} dollars`,
            `Bearish breakdown alert: ${symbol} at ${price} dollars`,
            `${symbol} support failure at ${price} dollars`
        ]
    };
    
    const messageList = messages[breakoutType] || messages.bullish;
    const message = messageList[Math.floor(Math.random() * messageList.length)];
    
    queueVoiceAlert(message, 'high', {
        priority: 'breakout',
        symbol,
        price,
        breakoutType
    });
    
    showVoiceAlertNotification(message, 'breakout', symbol);
    playAlertSound('breakout');
}

// Trigger setup alert
function triggerSetupAlert(symbol, setupType, details = '') {
    const message = `${symbol} ${setupType} setup detected. ${details}`.trim();
    
    queueVoiceAlert(message, 'normal', {
        priority: 'setup',
        symbol,
        setupType
    });
    
    showVoiceAlertNotification(message, 'setup', symbol);
}

// Show voice alert notification
function showVoiceAlertNotification(message, type, symbol) {
    const alertContainer = document.createElement('div');
    alertContainer.className = `voice-alert-notification fixed top-4 right-4 max-w-sm bg-accent-blue p-4 rounded-lg shadow-lg transform transition-transform duration-300 z-50`;
    
    const iconMap = {
        confidence: 'fas fa-chart-line',
        breakout: 'fas fa-rocket',
        setup: 'fas fa-eye',
        warning: 'fas fa-exclamation-triangle'
    };
    
    alertContainer.innerHTML = `
        <div class="flex items-start space-x-3">
            <div class="flex-shrink-0">
                <i class="${iconMap[type] || iconMap.setup} text-xl"></i>
            </div>
            <div class="flex-1">
                <div class="flex items-center justify-between mb-1">
                    <h4 class="font-semibold text-sm">Voice Alert</h4>
                    <button onclick="dismissVoiceAlert(this)" class="text-white hover:text-gray-200">
                        <i class="fas fa-times text-sm"></i>
                    </button>
                </div>
                <p class="text-sm opacity-90">${message}</p>
                ${symbol ? `<div class="mt-2"><span class="px-2 py-1 bg-white bg-opacity-20 rounded text-xs font-semibold">${symbol}</span></div>` : ''}
            </div>
        </div>
    `;
    
    document.body.appendChild(alertContainer);
    
    // Animate in
    setTimeout(() => {
        alertContainer.style.transform = 'translateX(0)';
    }, 100);
    
    // Auto-dismiss after 8 seconds
    setTimeout(() => {
        dismissVoiceAlert(alertContainer);
    }, 8000);
}

// Dismiss voice alert notification
function dismissVoiceAlert(element) {
    const notification = element.closest ? element.closest('.voice-alert-notification') : element;
    if (notification) {
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 300);
    }
}

// Play alert sound
function playAlertSound(type = 'default') {
    try {
        // Try to play the alert audio element
        const audio = document.getElementById('alertSound');
        if (audio) {
            audio.currentTime = 0;
            audio.play().catch(e => console.log('Audio play failed:', e));
            return;
        }
        
        // Fallback: create audio using Web Audio API
        if (window.AudioContext || window.webkitAudioContext) {
            createBeepSound(type);
        }
        
    } catch (error) {
        console.error('Error playing alert sound:', error);
    }
}

// Create beep sound using Web Audio API
function createBeepSound(type) {
    try {
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        // Different frequencies for different alert types
        const frequencies = {
            confidence: 800,
            breakout: 1000,
            setup: 600,
            warning: 400,
            default: 700
        };
        
        oscillator.frequency.value = frequencies[type] || frequencies.default;
        oscillator.type = 'sine';
        
        gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.3);
        
        oscillator.start(audioContext.currentTime);
        oscillator.stop(audioContext.currentTime + 0.3);
        
    } catch (error) {
        console.error('Error creating beep sound:', error);
    }
}

// Show voice settings modal
function showVoiceSettings() {
    let modal = document.getElementById('voiceSettingsModal');
    if (!modal) {
        modal = createVoiceSettingsModal();
    }
    
    // Update current settings in modal
    updateVoiceSettingsModal();
    
    showModal('voiceSettingsModal');
}

// Create voice settings modal
function createVoiceSettingsModal() {
    const modal = document.createElement('div');
    modal.id = 'voiceSettingsModal';
    modal.className = 'modal';
    modal.innerHTML = `
        <div class="modal-content max-w-md">
            <div class="modal-header">
                <h3 class="text-xl font-bold">Voice Settings</h3>
                <button onclick="closeModal('voiceSettingsModal')" class="modal-close">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="modal-body space-y-4">
                <div>
                    <label class="block text-sm font-medium mb-2">Voice</label>
                    <select id="voiceSelect" class="form-select">
                        <!-- Options will be populated -->
                    </select>
                </div>
                
                <div>
                    <label class="block text-sm font-medium mb-2">Volume</label>
                    <input type="range" id="volumeSlider" min="0" max="1" step="0.1" class="range-input">
                    <span id="volumeValue" class="text-sm text-gray-400"></span>
                </div>
                
                <div>
                    <label class="block text-sm font-medium mb-2">Speed</label>
                    <input type="range" id="rateSlider" min="0.5" max="2" step="0.1" class="range-input">
                    <span id="rateValue" class="text-sm text-gray-400"></span>
                </div>
                
                <div>
                    <label class="block text-sm font-medium mb-2">Pitch</label>
                    <input type="range" id="pitchSlider" min="0.5" max="2" step="0.1" class="range-input">
                    <span id="pitchValue" class="text-sm text-gray-400"></span>
                </div>
                
                <div class="border-t border-dark-accent pt-4">
                    <button onclick="testVoiceSettings()" class="btn-secondary w-full mb-3">
                        <i class="fas fa-play mr-1"></i>Test Voice
                    </button>
                    
                    <div class="flex space-x-3">
                        <button onclick="saveVoiceSettings()" class="btn-primary flex-1">
                            Save Settings
                        </button>
                        <button onclick="resetVoiceSettings()" class="btn-secondary">
                            Reset
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Add event listeners
    modal.addEventListener('input', updateVoiceSettingsPreview);
    
    return modal;
}

// Update voice settings modal with current values
function updateVoiceSettingsModal() {
    // Populate voice select
    const voiceSelect = document.getElementById('voiceSelect');
    if (voiceSelect) {
        const voices = speechSynthesis.getVoices();
        voiceSelect.innerHTML = voices.map(voice => 
            `<option value="${voice.name}" ${voice === window.voiceAlertState.voice ? 'selected' : ''}>
                ${voice.name} (${voice.lang})
            </option>`
        ).join('');
    }
    
    // Set slider values
    const volumeSlider = document.getElementById('volumeSlider');
    const rateSlider = document.getElementById('rateSlider');
    const pitchSlider = document.getElementById('pitchSlider');
    
    if (volumeSlider) {
        volumeSlider.value = window.voiceAlertState.volume;
        document.getElementById('volumeValue').textContent = Math.round(window.voiceAlertState.volume * 100) + '%';
    }
    
    if (rateSlider) {
        rateSlider.value = window.voiceAlertState.rate;
        document.getElementById('rateValue').textContent = window.voiceAlertState.rate + 'x';
    }
    
    if (pitchSlider) {
        pitchSlider.value = window.voiceAlertState.pitch;
        document.getElementById('pitchValue').textContent = window.voiceAlertState.pitch;
    }
}

// Update voice settings preview
function updateVoiceSettingsPreview(e) {
    const target = e.target;
    
    if (target.id === 'volumeSlider') {
        document.getElementById('volumeValue').textContent = Math.round(target.value * 100) + '%';
    } else if (target.id === 'rateSlider') {
        document.getElementById('rateValue').textContent = target.value + 'x';
    } else if (target.id === 'pitchSlider') {
        document.getElementById('pitchValue').textContent = target.value;
    }
}

// Test voice settings
function testVoiceSettings() {
    const voiceSelect = document.getElementById('voiceSelect');
    const volumeSlider = document.getElementById('volumeSlider');
    const rateSlider = document.getElementById('rateSlider');
    const pitchSlider = document.getElementById('pitchSlider');
    
    const selectedVoice = speechSynthesis.getVoices().find(v => v.name === voiceSelect.value);
    
    const testOptions = {
        volume: parseFloat(volumeSlider.value),
        rate: parseFloat(rateSlider.value),
        pitch: parseFloat(pitchSlider.value)
    };
    
    // Temporarily set voice
    const originalVoice = window.voiceAlertState.voice;
    window.voiceAlertState.voice = selectedVoice;
    
    speak('This is a test of your voice alert settings', testOptions);
    
    // Restore original voice
    window.voiceAlertState.voice = originalVoice;
}

// Save voice settings
function saveVoiceSettings() {
    const voiceSelect = document.getElementById('voiceSelect');
    const volumeSlider = document.getElementById('volumeSlider');
    const rateSlider = document.getElementById('rateSlider');
    const pitchSlider = document.getElementById('pitchSlider');
    
    // Update state
    window.voiceAlertState.voice = speechSynthesis.getVoices().find(v => v.name === voiceSelect.value);
    window.voiceAlertState.volume = parseFloat(volumeSlider.value);
    window.voiceAlertState.rate = parseFloat(rateSlider.value);
    window.voiceAlertState.pitch = parseFloat(pitchSlider.value);
    
    // Save to localStorage
    saveVoicePreferences();
    
    closeModal('voiceSettingsModal');
    showAlert('Voice settings saved', 'success');
}

// Reset voice settings to defaults
function resetVoiceSettings() {
    window.voiceAlertState.volume = 0.8;
    window.voiceAlertState.rate = 0.9;
    window.voiceAlertState.pitch = 1.0;
    
    // Update modal
    updateVoiceSettingsModal();
    
    showAlert('Voice settings reset to defaults', 'info');
}

// Load voice preferences from localStorage
function loadVoicePreferences() {
    try {
        const enabled = localStorage.getItem('voiceAlertsEnabled');
        if (enabled !== null) {
            window.voiceAlertState.isEnabled = enabled === 'true';
        }
        
        const volume = localStorage.getItem('voiceVolume');
        if (volume) {
            window.voiceAlertState.volume = parseFloat(volume);
        }
        
        const rate = localStorage.getItem('voiceRate');
        if (rate) {
            window.voiceAlertState.rate = parseFloat(rate);
        }
        
        const pitch = localStorage.getItem('voicePitch');
        if (pitch) {
            window.voiceAlertState.pitch = parseFloat(pitch);
        }
        
        const voiceName = localStorage.getItem('selectedVoice');
        if (voiceName) {
            const voice = speechSynthesis.getVoices().find(v => v.name === voiceName);
            if (voice) {
                window.voiceAlertState.voice = voice;
            }
        }
        
    } catch (error) {
        console.error('Error loading voice preferences:', error);
    }
}

// Save voice preferences to localStorage
function saveVoicePreferences() {
    try {
        localStorage.setItem('voiceAlertsEnabled', window.voiceAlertState.isEnabled);
        localStorage.setItem('voiceVolume', window.voiceAlertState.volume);
        localStorage.setItem('voiceRate', window.voiceAlertState.rate);
        localStorage.setItem('voicePitch', window.voiceAlertState.pitch);
        
        if (window.voiceAlertState.voice) {
            localStorage.setItem('selectedVoice', window.voiceAlertState.voice.name);
        }
    } catch (error) {
        console.error('Error saving voice preferences:', error);
    }
}

// Log voice alert for debugging/analytics
function logVoiceAlert(text, priority) {
    const alert = {
        text,
        priority,
        timestamp: new Date().toISOString()
    };
    
    window.voiceAlertState.alertHistory.push(alert);
    window.voiceAlertState.lastAlert = alert;
    
    // Keep only last 50 alerts
    if (window.voiceAlertState.alertHistory.length > 50) {
        window.voiceAlertState.alertHistory = window.voiceAlertState.alertHistory.slice(-50);
    }
    
    console.log('Voice alert logged:', alert);
}

// Get alert history
function getAlertHistory() {
    return window.voiceAlertState.alertHistory;
}

// Clear alert queue
function clearAlertQueue() {
    window.voiceAlertState.alertQueue = [];
    speechSynthesis.cancel();
    window.voiceAlertState.isPlaying = false;
}

// Emergency stop all voice alerts
function emergencyStopVoice() {
    speechSynthesis.cancel();
    clearAlertQueue();
    window.voiceAlertState.isPlaying = false;
    console.log('Emergency voice stop activated');
}

// Export functions for global access
window.speak = speak;
window.queueVoiceAlert = queueVoiceAlert;
window.triggerConfidenceAlert = triggerConfidenceAlert;
window.triggerBreakoutAlert = triggerBreakoutAlert;
window.triggerSetupAlert = triggerSetupAlert;
window.dismissVoiceAlert = dismissVoiceAlert;
window.showVoiceSettings = showVoiceSettings;
window.testVoiceSettings = testVoiceSettings;
window.saveVoiceSettings = saveVoiceSettings;
window.resetVoiceSettings = resetVoiceSettings;
window.getAlertHistory = getAlertHistory;
window.clearAlertQueue = clearAlertQueue;
window.emergencyStopVoice = emergencyStopVoice;
window.voiceAlertState = window.voiceAlertState;

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    emergencyStopVoice();
    saveVoicePreferences();
});
