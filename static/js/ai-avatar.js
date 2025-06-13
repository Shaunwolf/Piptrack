// CandleCast Mascot Avatar System
class CandleCastMascot {
    constructor() {
        this.isVisible = false;
        this.currentMood = 'neutral';
        this.animationState = 'idle';
        this.speechQueue = [];
        this.isSpeaking = false;
        this.name = 'Candle';
        this.init();
    }

    init() {
        this.createAvatarContainer();
        this.setupEventListeners();
        this.startIdleAnimation();
        console.log('AI Avatar initialized');
    }

    createAvatarContainer() {
        const avatarHTML = `
            <div id="candlecast-mascot" class="fixed bottom-6 right-6 z-50 transition-all duration-300 transform ${this.isVisible ? 'scale-100 opacity-100' : 'scale-0 opacity-0'}">
                <div class="relative">
                    <!-- Mascot Container -->
                    <div id="mascot-container" class="w-20 h-20 cursor-pointer hover:scale-105 transition-all duration-200 flex items-center justify-center">
                        <!-- Candle Body -->
                        <div class="relative">
                            <div id="candle-body" class="w-12 h-16 bg-gradient-to-t from-orange-400 to-yellow-300 rounded-b-lg shadow-lg border-2 border-orange-500 transition-all duration-300">
                                <!-- Wax drips -->
                                <div class="absolute -left-1 top-3 w-2 h-3 bg-yellow-200 rounded-full opacity-60"></div>
                                <div class="absolute -right-1 top-6 w-1.5 h-2 bg-yellow-200 rounded-full opacity-60"></div>
                                
                                <!-- Face -->
                                <div id="candle-face" class="absolute inset-0 flex flex-col items-center justify-center text-orange-900">
                                    <div id="eyes" class="flex space-x-1 mb-1">
                                        <div class="w-1.5 h-1.5 bg-orange-900 rounded-full animate-pulse"></div>
                                        <div class="w-1.5 h-1.5 bg-orange-900 rounded-full animate-pulse"></div>
                                    </div>
                                    <div id="mouth" class="w-2 h-1 border-t-2 border-orange-900 rounded-full transition-all duration-300"></div>
                                </div>
                            </div>
                            
                            <!-- Wick -->
                            <div id="wick" class="absolute -top-2 left-1/2 transform -translate-x-1/2 w-0.5 h-2 bg-gray-700"></div>
                            
                            <!-- Flame -->
                            <div id="flame" class="absolute -top-6 left-1/2 transform -translate-x-1/2 w-3 h-4 transition-all duration-200">
                                <div class="w-full h-full bg-gradient-to-t from-red-500 via-orange-400 to-yellow-300 rounded-full animate-pulse shadow-lg">
                                    <div class="absolute inset-0.5 bg-gradient-to-t from-red-400 via-orange-300 to-yellow-200 rounded-full animate-ping opacity-75"></div>
                                </div>
                            </div>
                            
                            <!-- Glow effect -->
                            <div id="glow" class="absolute inset-0 bg-gradient-to-t from-orange-400 to-yellow-300 rounded-b-lg blur-md opacity-30 animate-pulse"></div>
                        </div>
                    </div>
                    
                    <!-- Speech Bubble -->
                    <div id="speech-bubble" class="absolute bottom-24 right-0 bg-gray-800 text-white p-3 rounded-lg shadow-lg max-w-xs opacity-0 transform scale-0 transition-all duration-200 pointer-events-none">
                        <div id="speech-text" class="text-sm"></div>
                        <div class="absolute -bottom-2 right-4 w-0 h-0 border-l-8 border-r-8 border-t-8 border-l-transparent border-r-transparent border-t-gray-800"></div>
                    </div>
                    
                    <!-- Mood indicator -->
                    <div id="mood-indicator" class="absolute -top-2 -right-2 w-6 h-6 bg-green-400 rounded-full border-2 border-white flex items-center justify-center text-xs animate-pulse">
                        📈
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', avatarHTML);
        
        // Add click handler
        document.getElementById('candlecast-mascot').addEventListener('click', () => {
            this.onAvatarClick();
        });
    }

    setupEventListeners() {
        // Listen for trading events
        document.addEventListener('stockScanned', (e) => {
            this.onStockScanned(e.detail);
        });
        
        document.addEventListener('highConfidenceStock', (e) => {
            this.onHighConfidenceStock(e.detail);
        });
        
        document.addEventListener('patternDetected', (e) => {
            this.onPatternDetected(e.detail);
        });
        
        document.addEventListener('journalEntry', (e) => {
            this.onJournalEntry(e.detail);
        });
    }

    show() {
        this.isVisible = true;
        const mascot = document.getElementById('candlecast-mascot');
        mascot.classList.remove('scale-0', 'opacity-0');
        mascot.classList.add('scale-100', 'opacity-100');
    }

    hide() {
        this.isVisible = false;
        const mascot = document.getElementById('candlecast-mascot');
        mascot.classList.remove('scale-100', 'opacity-100');
        mascot.classList.add('scale-0', 'opacity-0');
    }

    setMood(mood) {
        this.currentMood = mood;
        const candleBody = document.getElementById('candle-body');
        const flame = document.getElementById('flame');
        const mouth = document.getElementById('mouth');
        const moodIndicator = document.getElementById('mood-indicator');
        const eyes = document.getElementById('eyes').children;
        
        switch(mood) {
            case 'excited':
                // Bright green candle, bigger flame
                candleBody.className = candleBody.className.replace(/from-\w+-\d+\s+to-\w+-\d+/, 'from-green-400 to-lime-300');
                flame.style.transform = 'translate(-50%, 0) scale(1.2)';
                mouth.style.borderTopWidth = '3px';
                mouth.style.borderRadius = '50%';
                moodIndicator.textContent = '🚀';
                moodIndicator.className = moodIndicator.className.replace(/bg-\w+-\d+/, 'bg-green-400');
                break;
            case 'analytical':
                // Blue analytical candle, steady flame
                candleBody.className = candleBody.className.replace(/from-\w+-\d+\s+to-\w+-\d+/, 'from-blue-400 to-cyan-300');
                flame.style.transform = 'translate(-50%, 0) scale(1)';
                mouth.style.borderTopWidth = '1px';
                mouth.style.borderRadius = '0';
                moodIndicator.textContent = '🔍';
                moodIndicator.className = moodIndicator.className.replace(/bg-\w+-\d+/, 'bg-blue-400');
                break;
            case 'warning':
                // Red warning candle, flickering flame
                candleBody.className = candleBody.className.replace(/from-\w+-\d+\s+to-\w+-\d+/, 'from-red-400 to-orange-300');
                flame.style.transform = 'translate(-50%, 0) scale(0.9)';
                mouth.style.borderTopWidth = '2px';
                mouth.style.borderRadius = '50% 50% 0 0';
                moodIndicator.textContent = '⚠️';
                moodIndicator.className = moodIndicator.className.replace(/bg-\w+-\d+/, 'bg-red-400');
                this.flickerFlame();
                break;
            case 'thinking':
                // Purple thinking candle, slow flame
                candleBody.className = candleBody.className.replace(/from-\w+-\d+\s+to-\w+-\d+/, 'from-purple-400 to-pink-300');
                flame.style.transform = 'translate(-50%, 0) scale(0.8)';
                mouth.style.borderTopWidth = '1px';
                mouth.style.borderRadius = '50%';
                moodIndicator.textContent = '💭';
                moodIndicator.className = moodIndicator.className.replace(/bg-\w+-\d+/, 'bg-purple-400');
                break;
            case 'sleeping':
                // Dim candle, no flame
                candleBody.className = candleBody.className.replace(/from-\w+-\d+\s+to-\w+-\d+/, 'from-gray-500 to-gray-400');
                flame.style.opacity = '0.3';
                flame.style.transform = 'translate(-50%, 0) scale(0.5)';
                mouth.style.borderTopWidth = '1px';
                mouth.style.borderRadius = '50%';
                // Close eyes
                for (let eye of eyes) {
                    eye.style.height = '2px';
                }
                moodIndicator.textContent = '😴';
                moodIndicator.className = moodIndicator.className.replace(/bg-\w+-\d+/, 'bg-gray-400');
                break;
            default:
                // Default warm candle
                candleBody.className = candleBody.className.replace(/from-\w+-\d+\s+to-\w+-\d+/, 'from-orange-400 to-yellow-300');
                flame.style.transform = 'translate(-50%, 0) scale(1)';
                flame.style.opacity = '1';
                mouth.style.borderTopWidth = '2px';
                mouth.style.borderRadius = '50%';
                // Reset eyes
                for (let eye of eyes) {
                    eye.style.height = '6px';
                }
                moodIndicator.textContent = '📈';
                moodIndicator.className = moodIndicator.className.replace(/bg-\w+-\d+/, 'bg-green-400');
        }
    }

    flickerFlame() {
        const flame = document.getElementById('flame');
        let count = 0;
        const flicker = setInterval(() => {
            flame.style.opacity = count % 2 === 0 ? '0.7' : '1';
            count++;
            if (count > 8) {
                clearInterval(flicker);
                flame.style.opacity = '1';
            }
        }, 150);
    }

    speak(message, duration = 3000) {
        this.speechQueue.push({ message, duration });
        if (!this.isSpeaking) {
            this.processNextSpeech();
        }
    }

    processNextSpeech() {
        if (this.speechQueue.length === 0) {
            this.isSpeaking = false;
            return;
        }

        this.isSpeaking = true;
        const { message, duration } = this.speechQueue.shift();
        
        const bubble = document.getElementById('speech-bubble');
        const text = document.getElementById('speech-text');
        
        text.textContent = message;
        bubble.classList.remove('opacity-0', 'scale-0');
        bubble.classList.add('opacity-100', 'scale-100');
        
        // Animate avatar while speaking
        this.animateWhileSpeaking();
        
        setTimeout(() => {
            bubble.classList.remove('opacity-100', 'scale-100');
            bubble.classList.add('opacity-0', 'scale-0');
            
            setTimeout(() => {
                this.processNextSpeech();
            }, 200);
        }, duration);
    }

    animateWhileSpeaking() {
        const candleBody = document.getElementById('candle-body');
        const flame = document.getElementById('flame');
        
        let count = 0;
        const speakAnimation = setInterval(() => {
            // Candle body glow while speaking
            candleBody.style.transform = count % 2 === 0 ? 'scale(1.05)' : 'scale(1)';
            // Flame flickers while speaking
            flame.style.transform = count % 2 === 0 ? 'translate(-50%, 0) scale(1.1)' : 'translate(-50%, 0) scale(1)';
            count++;
            
            if (count > 6) {
                clearInterval(speakAnimation);
                candleBody.style.transform = 'scale(1)';
                flame.style.transform = 'translate(-50%, 0) scale(1)';
            }
        }, 200);
    }

    startIdleAnimation() {
        setInterval(() => {
            if (!this.isSpeaking && this.isVisible) {
                const flame = document.getElementById('flame');
                const glow = document.getElementById('glow');
                
                // Gentle flame animation
                flame.style.transform = 'translate(-50%, 0) scale(1.1)';
                glow.style.opacity = '0.5';
                
                setTimeout(() => {
                    flame.style.transform = 'translate(-50%, 0) scale(1)';
                    glow.style.opacity = '0.3';
                }, 1500);
            }
        }, 4000);
    }

    onAvatarClick() {
        const messages = [
            "Hi! I'm Candle, your CandleCast trading mascot! 🕯️",
            "Ready to light up some profitable trades? Let's scan the markets!",
            "I'm here to illuminate your trading journey with smart analysis.",
            "Click on any stock to see my forecasting flames in action!",
            "Don't forget to journal your trades - I'll help track your progress!"
        ];
        
        const randomMessage = messages[Math.floor(Math.random() * messages.length)];
        this.speak(randomMessage);
        this.setMood('thinking');
        
        setTimeout(() => {
            this.setMood('neutral');
        }, 2000);
    }

    onStockScanned(data) {
        if (data.stocksFound > 0) {
            this.setMood('analytical');
            this.speak(`Found ${data.stocksFound} stocks to analyze!`);
        }
    }

    onHighConfidenceStock(data) {
        this.setMood('excited');
        this.speak(`🔥 Hot setup detected: ${data.symbol} with ${data.confidence}% confidence! My flames are dancing!`, 4000);
        
        // Trigger voice alert if available
        if (window.speechSynthesis) {
            const utterance = new SpeechSynthesisUtterance(`CandleCast Alert! High confidence stock ${data.symbol} detected with ${data.confidence} percent confidence. Time to light up the charts!`);
            utterance.rate = 0.9;
            utterance.pitch = 1.1;
            window.speechSynthesis.speak(utterance);
        }
    }

    onPatternDetected(data) {
        this.setMood('analytical');
        this.speak(`Pattern detected: ${data.pattern} on ${data.symbol}`, 3500);
    }

    onJournalEntry(data) {
        this.setMood('thinking');
        const encouragement = [
            "Great job documenting your trade!",
            "Reflection is key to becoming a better trader.",
            "Your trading journal will help you identify patterns.",
            "Keep tracking your progress!"
        ];
        
        const message = encouragement[Math.floor(Math.random() * encouragement.length)];
        this.speak(message);
    }

    // Utility methods for integration
    triggerStockAlert(symbol, confidence) {
        document.dispatchEvent(new CustomEvent('highConfidenceStock', {
            detail: { symbol, confidence }
        }));
    }

    triggerPatternAlert(symbol, pattern) {
        document.dispatchEvent(new CustomEvent('patternDetected', {
            detail: { symbol, pattern }
        }));
    }

    triggerScanComplete(stocksFound) {
        document.dispatchEvent(new CustomEvent('stockScanned', {
            detail: { stocksFound }
        }));
    }
}

// Initialize CandleCast Mascot when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.candleMascot = new CandleCastMascot();
    window.candleMascot.show();
});