// AI Coach functionality for stock analysis and setup evaluation

// Global AI coach state
window.aiCoachState = {
    analysisCache: new Map(),
    currentAnalysis: null,
    gutCheckMode: false,
    chartStoryActive: false
};

// Initialize AI Coach functionality
document.addEventListener('DOMContentLoaded', function() {
    initializeAICoach();
    setupAICoachEventListeners();
    
    // Export functions to global scope after DOM load
    window.getAIReview = getAIReview;
    window.performGutCheck = performGutCheck;
    window.exportAnalysis = exportAnalysis;
    window.speakAnalysis = speakAnalysis;
    window.testButtonClick = function() {
        console.log('=== TESTING AI REVIEW BUTTON ===');
        getAIReview('RSLS');
    };
    
    console.log('Global AI functions exported successfully');
});

// Initialize AI Coach
function initializeAICoach() {
    console.log('AI Coach initialized');
    
    // Check for existing analysis cache in localStorage
    const cachedAnalyses = localStorage.getItem('aiAnalysisCache');
    if (cachedAnalyses) {
        try {
            const parsed = JSON.parse(cachedAnalyses);
            window.aiCoachState.analysisCache = new Map(Object.entries(parsed));
        } catch (error) {
            console.error('Error loading cached analyses:', error);
        }
    }
    
    // Initialize AI coach UI elements
    initializeAICoachUI();
}

// Setup AI Coach event listeners
function setupAICoachEventListeners() {
    // Global function to handle AI review clicks
    window.getAIReview = getAIReview;
    
    // Also handle direct button clicks
    document.addEventListener('click', function(e) {
        let target = e.target;
        
        // Check if clicked element or parent has AI review functionality
        while (target && target !== document) {
            if (target.classList && target.classList.contains('ai-review-btn')) {
                e.preventDefault();
                const symbol = target.getAttribute('data-symbol');
                if (symbol) {
                    getAIReview(symbol);
                }
                return;
            }
            
            // Check onclick attribute for getAIReview calls
            if (target.getAttribute && target.getAttribute('onclick')) {
                const onclick = target.getAttribute('onclick');
                if (onclick.includes('getAIReview')) {
                    e.preventDefault();
                    const match = onclick.match(/getAIReview\(['"]([^'"]+)['"]\)/);
                    if (match) {
                        getAIReview(match[1]);
                    }
                    return;
                }
            }
            
            target = target.parentNode;
        }
    });
    
    // Gut check buttons
    document.addEventListener('click', function(e) {
        let target = e.target;
        while (target && target !== document) {
            if (target.classList && target.classList.contains('gut-check-btn')) {
                e.preventDefault();
                const symbol = target.getAttribute('data-symbol');
                if (symbol) {
                    performGutCheck(symbol);
                }
                return;
            }
            target = target.parentNode;
        }
    });
    
    // Chart story hover events
    document.addEventListener('mouseenter', function(e) {
        let target = e.target;
        while (target && target !== document) {
            if (target.classList && target.classList.contains('chart-hover-zone') && window.aiCoachState.chartStoryActive) {
                showChartStoryTooltip(e);
                return;
            }
            target = target.parentNode;
        }
    }, true);
    
    document.addEventListener('mouseleave', function(e) {
        let target = e.target;
        while (target && target !== document) {
            if (target.classList && target.classList.contains('chart-hover-zone')) {
                hideChartStoryTooltip();
                return;
            }
            target = target.parentNode;
        }
    }, true);
}

// Initialize AI Coach UI elements
function initializeAICoachUI() {
    // Add AI coach buttons to stock cards that don't have them
    document.querySelectorAll('.stock-card').forEach(card => {
        const symbol = card.dataset.symbol;
        if (symbol && !card.querySelector('.ai-coach-btn') && !card.querySelector('[onclick*="getAIReview"]')) {
            addAICoachButton(card, symbol);
        }
    });
    
    // Add gut check prompts if on forecast page
    if (window.location.pathname.includes('/forecast/')) {
        addGutCheckPrompts();
    }
}

// Add AI coach button to stock card
function addAICoachButton(card, symbol) {
    const buttonContainer = card.querySelector('.flex.space-x-2');
    if (buttonContainer) {
        const aiButton = document.createElement('button');
        aiButton.className = 'btn-secondary ai-coach-btn';
        aiButton.dataset.symbol = symbol;
        aiButton.title = 'AI Setup Analysis';
        aiButton.innerHTML = '<i class="fas fa-robot"></i>';
        aiButton.addEventListener('click', () => getAIReview(symbol));
        
        buttonContainer.appendChild(aiButton);
    }
}

// Add gut check prompts to forecast page
function addGutCheckPrompts() {
    const symbol = extractSymbolFromPath();
    if (!symbol) return;
    
    const gutCheckContainer = document.createElement('div');
    gutCheckContainer.className = 'card mt-8';
    gutCheckContainer.innerHTML = `
        <div class="card-header">
            <h2 class="text-xl font-bold flex items-center">
                <i class="fas fa-brain text-purple-500 mr-2"></i>
                AI Gut Check
            </h2>
            <button onclick="performGutCheck('${symbol}')" class="btn-primary gut-check-btn" data-symbol="${symbol}">
                <i class="fas fa-search mr-1"></i>Get Gut Check
            </button>
        </div>
        <div id="gutCheckResults" class="card-body hidden">
            <!-- Gut check results will be populated here -->
        </div>
    `;
    
    // Insert before the last element on the page
    const mainContent = document.querySelector('main > div');
    if (mainContent) {
        mainContent.appendChild(gutCheckContainer);
    }
}

// Get AI review for a stock
async function getAIReview(symbol) {
    console.log('=== AI REVIEW FUNCTION CALLED ===');
    console.log('Symbol:', symbol);
    if (!symbol) {
        showAlert('Symbol is required for AI analysis', 'error');
        return;
    }
    
    // Check cache first
    const cacheKey = `${symbol}_${new Date().toDateString()}`;
    if (window.aiCoachState.analysisCache.has(cacheKey)) {
        const cachedAnalysis = window.aiCoachState.analysisCache.get(cacheKey);
        displayAIAnalysis(cachedAnalysis, symbol);
        return;
    }
    
    try {
        showLoading();
        
        const response = await fetch(`/ai_review/${symbol}`);
        const data = await response.json();
        console.log('AI Review API response:', data);
        
        if (data.success) {
            const analysis = data.analysis;
            console.log('Analysis data received:', analysis);
            
            // Cache the analysis
            window.aiCoachState.analysisCache.set(cacheKey, analysis);
            saveCacheToLocalStorage();
            
            // Display the analysis
            displayAIAnalysis(analysis, symbol);
            
            // Store current analysis
            window.aiCoachState.currentAnalysis = analysis;
            
            // Focus on the modal instead of scrolling
            setTimeout(() => {
                const modal = document.getElementById('aiReviewModal');
                if (modal) {
                    modal.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            }, 100);
            
        } else {
            showAlert('Error getting AI analysis: ' + data.error, 'error');
        }
        
    } catch (error) {
        console.error('Error getting AI review:', error);
        showAlert('Error connecting to AI analysis service', 'error');
    } finally {
        hideLoading();
    }
}

// Display AI analysis in modal
function displayAIAnalysis(analysis, symbol) {
    // Get the modal and show it
    const modal = document.getElementById('aiReviewModal');
    if (!modal) {
        console.error('AI Review modal not found');
        return;
    }
    
    // Show the modal
    modal.classList.add('show');
    
    const content = document.getElementById('aiReviewContent');
    if (!content) {
        console.error('AI Review content container not found');
        return;
    }
    
    const moodEmoji = getMoodEmoji(analysis.mood_tag);
    const confidenceColor = getConfidenceColor(analysis.confidence_factors);
    
    content.innerHTML = `
        <div class="space-y-6">
            <!-- Header with mood and pattern -->
            <div class="flex items-center justify-between">
                <div class="flex items-center space-x-3">
                    <span class="text-4xl">${moodEmoji}</span>
                    <div>
                        <h4 class="text-2xl font-bold">${symbol}</h4>
                        <span class="px-3 py-1 rounded-full text-sm font-semibold bg-accent-blue bg-opacity-20 text-accent-blue">
                            ${analysis.pattern || 'Pattern Analysis'}
                        </span>
                    </div>
                </div>
                <button onclick="speakAnalysis('${escapeForJS(analysis.analysis_text)}')" class="btn-secondary">
                    <i class="fas fa-volume-up mr-1"></i>Listen
                </button>
            </div>
            
            <!-- Confidence Factors -->
            ${analysis.confidence_factors ? renderConfidenceFactors(analysis.confidence_factors) : ''}
            
            <!-- Main Analysis -->
            <div class="bg-dark-accent rounded-lg p-4">
                <h5 class="font-semibold text-accent-blue mb-2">AI Analysis</h5>
                <p class="text-gray-300 leading-relaxed">${analysis.analysis_text}</p>
            </div>
            
            <!-- Historical Comparison -->
            <div class="bg-dark-accent rounded-lg p-4">
                <h5 class="font-semibold text-accent-blue mb-2">Historical Context</h5>
                <p class="text-gray-300 leading-relaxed">${typeof analysis.historical_comparison === 'object' ? analysis.historical_comparison.text : analysis.historical_comparison}</p>
                
                <!-- Historical Chart Container -->
                <div id="historical-chart-container-${symbol}"></div>
            </div>
            
            <!-- Key Insights -->
            ${renderKeyInsights(analysis)}
            
            <!-- Action Buttons -->
            <div class="flex space-x-3">
                <a href="/forecast/${symbol}" class="btn-primary flex-1">
                    <i class="fas fa-chart-area mr-1"></i>View Forecast
                </a>
                <button onclick="performGutCheck('${symbol}')" class="btn-secondary flex-1">
                    <i class="fas fa-brain mr-1"></i>Gut Check
                </button>
                <button onclick="exportAnalysis('${symbol}')" class="btn-secondary">
                    <i class="fas fa-download"></i>
                </button>
            </div>
        </div>
    `;
    
    // Show the modal
    modal.classList.remove('hidden');
    
    // Render historical chart if chart data is available
    setTimeout(() => {
        const chartContainer = document.getElementById(`historical-chart-container-${symbol}`);
        if (chartContainer && analysis.historical_comparison) {
            console.log('Historical comparison data:', analysis.historical_comparison);
            console.log('Type:', typeof analysis.historical_comparison);
            
            // Handle the historical comparison data properly
            let historicalData = analysis.historical_comparison;
            console.log('Historical data structure:', historicalData);
            
            // If it's an object with chart_data, render the chart
            if (historicalData && typeof historicalData === 'object' && historicalData.chart_data) {
                console.log('Chart data found, rendering...');
                chartContainer.innerHTML = renderHistoricalChart(historicalData.chart_data);
            } else {
                console.log('No chart data available - checking structure:', typeof historicalData);
                console.log('Has chart_data property:', historicalData && historicalData.chart_data);
            }
        }
    }, 300);
    modal.classList.add('show');
    
    // Prevent body scrolling
    document.body.style.overflow = 'hidden';
}

// Create AI review modal if it doesn't exist
function createAIReviewModal() {
    const modal = document.createElement('div');
    modal.id = 'aiReviewModal';
    modal.className = 'modal';
    modal.innerHTML = `
        <div class="modal-content max-w-2xl">
            <div class="modal-header">
                <h3 class="text-xl font-bold">AI Setup Analysis</h3>
                <button onclick="closeModal('aiReviewModal')" class="modal-close">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div id="aiReviewContent" class="modal-body">
                <div class="text-center py-8">
                    <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-accent-blue"></div>
                    <p class="mt-2">Analyzing setup...</p>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    return modal;
}

// Render confidence factors visualization
function renderConfidenceFactors(factors) {
    const factorItems = Object.entries(factors)
        .filter(([key, value]) => key !== 'timestamp')
        .map(([key, value]) => {
            const label = formatFactorLabel(key);
            const score = typeof value === 'number' ? value : (value.score || 0);
            const color = getFactorColor(score);
            
            return `
                <div class="flex items-center justify-between py-2">
                    <span class="text-sm text-gray-400">${label}</span>
                    <div class="flex items-center space-x-2">
                        <div class="w-16 h-2 bg-gray-600 rounded-full overflow-hidden">
                            <div class="h-full ${color}" style="width: ${Math.abs(score)}%"></div>
                        </div>
                        <span class="text-sm font-semibold w-12 text-right">${score}${typeof score === 'number' && Math.abs(score) <= 100 ? '%' : ''}</span>
                    </div>
                </div>
            `;
        }).join('');
    
    return `
        <div class="bg-dark-accent rounded-lg p-4">
            <h5 class="font-semibold text-accent-blue mb-3">Confidence Factors</h5>
            <div class="space-y-1">
                ${factorItems}
            </div>
        </div>
    `;
}

// Render key insights section
function renderKeyInsights(analysis) {
    const insights = [];
    
    if (analysis.confidence_factors) {
        const factors = analysis.confidence_factors;
        
        // RSI insights
        if (factors.rsi && factors.rsi !== 50) {
            if (factors.rsi > 70) {
                insights.push({ type: 'warning', text: 'RSI indicates overbought conditions - consider waiting for pullback' });
            } else if (factors.rsi < 30) {
                insights.push({ type: 'opportunity', text: 'RSI shows oversold levels - potential bounce opportunity' });
            } else {
                insights.push({ type: 'neutral', text: 'RSI in healthy range for continuation moves' });
            }
        }
        
        // Volume insights
        if (factors.volume_surge && factors.volume_surge > 50) {
            insights.push({ type: 'bullish', text: `Strong volume surge of ${factors.volume_surge}% confirms institutional interest` });
        }
        
        // Momentum insights
        if (factors.momentum && Math.abs(factors.momentum) > 0.01) {
            if (factors.momentum > 0) {
                insights.push({ type: 'bullish', text: 'Positive momentum supports upward movement' });
            } else {
                insights.push({ type: 'bearish', text: 'Negative momentum suggests caution on long positions' });
            }
        }
    }
    
    if (insights.length === 0) {
        return '';
    }
    
    const insightItems = insights.map(insight => {
        const iconMap = {
            bullish: 'fas fa-arrow-up text-accent-green',
            bearish: 'fas fa-arrow-down text-accent-red',
            warning: 'fas fa-exclamation-triangle text-yellow-500',
            opportunity: 'fas fa-lightbulb text-accent-blue',
            neutral: 'fas fa-minus text-gray-400'
        };
        
        return `
            <div class="flex items-start space-x-3 p-3 bg-dark-surface rounded-lg">
                <i class="${iconMap[insight.type] || iconMap.neutral}"></i>
                <span class="text-sm text-gray-300">${insight.text}</span>
            </div>
        `;
    }).join('');
    
    return `
        <div class="bg-dark-accent rounded-lg p-4">
            <h5 class="font-semibold text-accent-blue mb-3">Key Insights</h5>
            <div class="space-y-2">
                ${insightItems}
            </div>
        </div>
    `;
}

// Perform gut check analysis
async function performGutCheck(symbol) {
    try {
        showLoading();
        
        // Get fresh AI analysis
        const response = await fetch(`/ai_review/${symbol}`);
        const data = await response.json();
        
        if (data.success) {
            const analysis = data.analysis;
            showGutCheckDialog(symbol, analysis);
        } else {
            showAlert('Error performing gut check: ' + data.error, 'error');
        }
        
    } catch (error) {
        console.error('Error performing gut check:', error);
        showAlert('Error performing gut check', 'error');
    } finally {
        hideLoading();
    }
}

// Show gut check dialog
function showGutCheckDialog(symbol, analysis) {
    const questions = generateGutCheckQuestions(symbol, analysis);
    
    const modal = document.createElement('div');
    modal.id = 'gutCheckModal';
    modal.className = 'modal';
    modal.innerHTML = `
        <div class="modal-content max-w-xl">
            <div class="modal-header">
                <h3 class="text-xl font-bold flex items-center">
                    <i class="fas fa-brain text-purple-500 mr-2"></i>
                    Gut Check - ${symbol}
                </h3>
                <button onclick="closeGutCheckModal()" class="modal-close">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="modal-body">
                <div class="space-y-4">
                    <p class="text-gray-400 text-sm">
                        Answer these questions honestly to validate your trading thesis:
                    </p>
                    ${questions.map((q, i) => `
                        <div class="gut-check-question p-4 bg-dark-accent rounded-lg">
                            <p class="font-semibold mb-2">${i + 1}. ${q.question}</p>
                            <div class="flex space-x-3">
                                <button class="gut-answer-btn btn-secondary" data-answer="yes" data-question="${i}">
                                    <i class="fas fa-check mr-1"></i>Yes
                                </button>
                                <button class="gut-answer-btn btn-secondary" data-answer="no" data-question="${i}">
                                    <i class="fas fa-times mr-1"></i>No
                                </button>
                            </div>
                        </div>
                    `).join('')}
                    
                    <div class="flex space-x-3 mt-6">
                        <button onclick="processGutCheckResults('${symbol}')" class="btn-primary flex-1" id="gutCheckSubmit" disabled>
                            <i class="fas fa-brain mr-1"></i>Get Gut Check Results
                        </button>
                        <button onclick="closeGutCheckModal()" class="btn-secondary">
                            Cancel
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    showModal('gutCheckModal');
    
    // Add event listeners for answers
    modal.addEventListener('click', function(e) {
        if (e.target.classList.contains('gut-answer-btn')) {
            handleGutCheckAnswer(e.target);
        }
    });
}

// Generate gut check questions based on analysis
function generateGutCheckQuestions(symbol, analysis) {
    const baseQuestions = [
        { question: "Do you understand why you want to trade this stock?", weight: 1 },
        { question: "Have you defined your risk and position size?", weight: 1 },
        { question: "Are you trading based on analysis or emotion?", weight: 1 },
        { question: "Would you take this trade with your own money?", weight: 1 }
    ];
    
    const analysisQuestions = [];
    
    // Add questions based on analysis
    if (analysis.confidence_factors) {
        const factors = analysis.confidence_factors;
        
        if (factors.rsi && factors.rsi > 70) {
            analysisQuestions.push({
                question: "Are you comfortable entering with RSI in overbought territory?",
                weight: 0.8
            });
        }
        
        if (factors.volume_surge && factors.volume_surge < 25) {
            analysisQuestions.push({
                question: "Are you okay with the relatively low volume confirmation?",
                weight: 0.9
            });
        }
        
        if (analysis.pattern && analysis.pattern.includes('reversal')) {
            analysisQuestions.push({
                question: "Do you have a plan if this reversal pattern fails?",
                weight: 0.9
            });
        }
    }
    
    return [...baseQuestions, ...analysisQuestions.slice(0, 2)]; // Max 6 questions
}

// Handle gut check answer selection
function handleGutCheckAnswer(button) {
    const question = button.dataset.question;
    const answer = button.dataset.answer;
    
    // Remove selection from other buttons in this question
    const questionContainer = button.closest('.gut-check-question');
    questionContainer.querySelectorAll('.gut-answer-btn').forEach(btn => {
        btn.classList.remove('btn-primary');
        btn.classList.add('btn-secondary');
    });
    
    // Highlight selected answer
    button.classList.remove('btn-secondary');
    button.classList.add('btn-primary');
    
    // Store answer
    button.closest('#gutCheckModal').dataset[`answer_${question}`] = answer;
    
    // Check if all questions are answered
    const totalQuestions = questionContainer.parentElement.querySelectorAll('.gut-check-question').length;
    const answeredQuestions = Object.keys(button.closest('#gutCheckModal').dataset)
        .filter(key => key.startsWith('answer_')).length;
    
    const submitButton = document.getElementById('gutCheckSubmit');
    if (answeredQuestions === totalQuestions) {
        submitButton.disabled = false;
        submitButton.classList.remove('opacity-50');
    }
}

// Process gut check results
function processGutCheckResults(symbol) {
    const modal = document.getElementById('gutCheckModal');
    const answers = Object.keys(modal.dataset)
        .filter(key => key.startsWith('answer_'))
        .map(key => modal.dataset[key]);
    
    const yesCount = answers.filter(answer => answer === 'yes').length;
    const totalQuestions = answers.length;
    const score = (yesCount / totalQuestions) * 100;
    
    let recommendation, color, icon;
    
    if (score >= 80) {
        recommendation = "Strong setup - proceed with confidence";
        color = "text-accent-green";
        icon = "fas fa-check-circle";
    } else if (score >= 60) {
        recommendation = "Decent setup - consider reducing position size";
        color = "text-accent-blue";
        icon = "fas fa-info-circle";
    } else if (score >= 40) {
        recommendation = "Questionable setup - high caution advised";
        color = "text-yellow-500";
        icon = "fas fa-exclamation-triangle";
    } else {
        recommendation = "Poor setup - consider avoiding this trade";
        color = "text-accent-red";
        icon = "fas fa-times-circle";
    }
    
    // Update modal content with results
    const modalBody = modal.querySelector('.modal-body');
    modalBody.innerHTML = `
        <div class="text-center space-y-6">
            <div class="text-6xl ${color}">
                <i class="${icon}"></i>
            </div>
            
            <div>
                <h4 class="text-2xl font-bold mb-2">Gut Check Score: ${score.toFixed(0)}%</h4>
                <p class="text-lg ${color} font-semibold">${recommendation}</p>
            </div>
            
            <div class="bg-dark-accent rounded-lg p-4">
                <h5 class="font-semibold mb-2">Results Breakdown</h5>
                <p class="text-gray-300">You answered "Yes" to ${yesCount} out of ${totalQuestions} questions.</p>
                ${score < 60 ? `
                    <p class="text-yellow-400 text-sm mt-2">
                        Consider reviewing your analysis and risk management before proceeding.
                    </p>
                ` : ''}
            </div>
            
            <div class="flex space-x-3">
                <button onclick="closeGutCheckModal()" class="btn-primary flex-1">
                    <i class="fas fa-check mr-1"></i>Got it
                </button>
                <a href="/journal?symbol=${symbol}" class="btn-secondary flex-1">
                    <i class="fas fa-book mr-1"></i>Journal Trade
                </a>
            </div>
        </div>
    `;
    
    // Speak the result if voice is enabled
    if (window.appState && window.appState.voiceEnabled) {
        speak(`Gut check complete. ${recommendation}`);
    }
}

// Close gut check modal
function closeGutCheckModal() {
    const modal = document.getElementById('gutCheckModal');
    if (modal) {
        modal.remove();
    }
}

// Export analysis to clipboard or file
function exportAnalysis(symbol) {
    if (!window.aiCoachState.currentAnalysis) {
        showAlert('No analysis to export', 'error');
        return;
    }
    
    const analysis = window.aiCoachState.currentAnalysis;
    const exportText = `
AI Analysis for ${symbol}
Generated: ${new Date().toLocaleString()}

Pattern: ${analysis.pattern || 'N/A'}
Mood: ${analysis.mood_tag || 'N/A'}

Analysis:
${analysis.analysis_text}

Historical Comparison:
${analysis.historical_comparison}

Confidence Factors:
${analysis.confidence_factors ? Object.entries(analysis.confidence_factors)
    .filter(([key]) => key !== 'timestamp')
    .map(([key, value]) => `${formatFactorLabel(key)}: ${typeof value === 'number' ? value : value.score || 'N/A'}`)
    .join('\n') : 'N/A'}
    `.trim();
    
    navigator.clipboard.writeText(exportText).then(() => {
        showAlert('Analysis copied to clipboard', 'success');
    }).catch(() => {
        showAlert('Failed to copy analysis', 'error');
    });
}

// Utility functions
function getMoodEmoji(moodTag) {
    const emojis = {
        'breakout': '💥',
        'reversal': '🔄',
        'risky': '⚠️',
        'confirmed': '🔒',
        'neutral': '📊'
    };
    return emojis[moodTag] || '📊';
}

function getConfidenceColor(factors) {
    if (!factors) return 'text-gray-400';
    
    const avgScore = Object.values(factors)
        .filter(val => typeof val === 'number')
        .reduce((sum, val, _, arr) => sum + val / arr.length, 0);
    
    if (avgScore >= 70) return 'text-accent-green';
    if (avgScore >= 40) return 'text-accent-blue';
    return 'text-accent-red';
}

function formatFactorLabel(key) {
    const labelMap = {
        'rsi': 'RSI Level',
        'volume_surge': 'Volume Surge',
        'momentum': 'Price Momentum',
        'price_vs_sma20': 'vs 20-day MA',
        'price_vs_sma50': 'vs 50-day MA',
        'distance_from_high': 'Distance from High',
        'distance_from_low': 'Distance from Low'
    };
    return labelMap[key] || key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}

function getFactorColor(score) {
    if (score >= 70) return 'bg-accent-green';
    if (score >= 40) return 'bg-accent-blue';
    if (score >= 0) return 'bg-accent-red';
    return 'bg-gray-500';
}

function extractSymbolFromOnClick(element) {
    const onclickAttr = element.getAttribute('onclick');
    if (onclickAttr) {
        const match = onclickAttr.match(/getAIReview\(['"]([^'"]+)['"]\)/);
        return match ? match[1] : null;
    }
    return null;
}

function extractSymbolFromPath() {
    const pathMatch = window.location.pathname.match(/\/forecast\/([A-Z]+)/);
    return pathMatch ? pathMatch[1] : null;
}

function escapeForJS(text) {
    if (!text) return '';
    return text.replace(/'/g, "\\'").replace(/"/g, '\\"').replace(/\n/g, '\\n');
}

// Save cache to localStorage
function saveCacheToLocalStorage() {
    try {
        const cacheObj = Object.fromEntries(window.aiCoachState.analysisCache);
        localStorage.setItem('aiAnalysisCache', JSON.stringify(cacheObj));
    } catch (error) {
        console.error('Error saving cache to localStorage:', error);
    }
}

// Speak analysis using voice alerts
function speakAnalysis(text) {
    if (window.speak && typeof window.speak === 'function') {
        window.speak(text);
    } else {
        showAlert('Voice synthesis not available', 'warning');
    }
}

// Export functions for global access immediately - fix scope issue
if (typeof window !== 'undefined') {
    window.getAIReview = getAIReview;
    window.performGutCheck = performGutCheck;
    window.exportAnalysis = exportAnalysis;
    window.speakAnalysis = speakAnalysis;
    window.aiCoachState = window.aiCoachState;
}

// Test function to verify AI review functionality
if (typeof window !== 'undefined') {
    window.testAIFunction = function() {
        console.log('AI function test - getAIReview available:', typeof window.getAIReview);
        console.log('Calling getAIReview with test symbol...');
        if (typeof window.getAIReview === 'function') {
            window.getAIReview('RSLS');
        }
    };

    // Add direct button click test
    window.testButtonClick = function() {
        console.log('Testing button click directly...');
        if (typeof getAIReview === 'function') {
            getAIReview('RSLS');
        } else {
            console.error('getAIReview function not available');
        }
    };
}

// Render historical comparison chart
function renderHistoricalChart(chartData) {
    console.log('renderHistoricalChart called with data:', chartData);
    
    if (!chartData || !chartData.dates || !chartData.prices) {
        console.log('Missing required chart data:', {
            hasData: !!chartData,
            hasDates: chartData && !!chartData.dates,
            hasPrices: chartData && !!chartData.prices
        });
        return '<div class="mt-4 text-gray-400 text-sm">No historical chart data available</div>';
    }
    
    const chartId = `historicalChart_${Date.now()}`;
    console.log('Creating chart with ID:', chartId);
    
    // Create chart container
    const chartHtml = `
        <div class="mt-4">
            <h6 class="text-sm font-medium text-gray-400 mb-2">Historical Pattern Comparison</h6>
            <div id="${chartId}" class="h-64 bg-gray-800 rounded-lg border border-gray-600"></div>
        </div>
    `;
    
    // Render chart after DOM update
    setTimeout(() => {
        console.log('Rendering chart for element:', chartId);
        renderHistoricalPlotlyChart(chartId, chartData);
    }, 200);
    
    return chartHtml;
}

// Render the actual Plotly chart
function renderHistoricalPlotlyChart(chartId, chartData) {
    console.log('renderHistoricalPlotlyChart called with:', chartId, chartData);
    
    const element = document.getElementById(chartId);
    if (!element) {
        console.error('Chart element not found:', chartId);
        return;
    }
    
    console.log('Chart element found, preparing data...');
    
    // Create candlestick chart if we have OHLC data
    const trace = (chartData.chart_type === 'candlestick' || chartData.chart_type === 'daily_candlestick') ? {
        x: chartData.dates,
        open: chartData.opens,
        high: chartData.highs,
        low: chartData.lows,
        close: chartData.closes,
        type: 'candlestick',
        name: chartData.symbol || 'Historical Pattern',
        increasing: {
            line: { color: '#10b981', width: 1 },
            fillcolor: '#10b981'
        },
        decreasing: {
            line: { color: '#ef4444', width: 1 },
            fillcolor: '#ef4444'
        }
    } : {
        x: chartData.dates,
        y: chartData.closes || chartData.prices,
        type: 'scatter',
        mode: 'lines',
        name: chartData.symbol || 'Historical Pattern',
        line: {
            color: '#3b82f6',
            width: 2
        }
    };
    
    const layout = {
        title: {
            text: 'Historical Pattern Comparison',
            font: { color: '#d1d5db', size: 14 }
        },
        paper_bgcolor: '#1f2937',
        plot_bgcolor: '#1f2937',
        xaxis: {
            gridcolor: '#374151',
            color: '#9ca3af',
            tickfont: { size: 10 },
            showline: true,
            linecolor: '#374151'
        },
        yaxis: {
            gridcolor: '#374151',
            color: '#9ca3af',
            tickfont: { size: 10 },
            title: { text: 'Price ($)', font: { color: '#9ca3af', size: 12 } }
        },
        margin: { l: 50, r: 20, t: 40, b: 40 },
        showlegend: false,
        hovermode: 'x unified'
    };
    
    const config = {
        displayModeBar: false,
        responsive: true
    };
    
    try {
        // Add enhanced pattern similarity overlay for META
        if (chartData.symbol === 'META' && chartData.pattern_stages) {
            const stages = chartData.pattern_stages;
            layout.shapes = [];
            layout.annotations = [];
            
            // Add highlighting for each pattern stage
            if (stages.bottom) {
                const bottomIdx = chartData.dates.findIndex(d => d.includes(stages.bottom));
                if (bottomIdx >= 0) {
                    layout.shapes.push({
                        type: 'circle',
                        xref: 'x',
                        yref: 'y',
                        x0: chartData.dates[Math.max(0, bottomIdx-2)],
                        y0: chartData.closes[bottomIdx] * 0.95,
                        x1: chartData.dates[Math.min(chartData.dates.length-1, bottomIdx+2)],
                        y1: chartData.closes[bottomIdx] * 1.05,
                        fillcolor: 'rgba(239, 68, 68, 0.3)',
                        line: { color: '#ef4444', width: 2 }
                    });
                    
                    layout.annotations.push({
                        x: chartData.dates[bottomIdx],
                        y: chartData.closes[bottomIdx],
                        text: `Pattern Bottom - Current stage`,
                        showarrow: true,
                        arrowhead: 2,
                        arrowcolor: '#ef4444',
                        font: { color: '#ef4444', size: 9 },
                        bgcolor: 'rgba(0,0,0,0.8)',
                        bordercolor: '#ef4444',
                        borderwidth: 1
                    });
                }
            }
            
            if (stages.accumulation) {
                const accumIdx = chartData.dates.findIndex(d => d.includes(stages.accumulation));
                if (accumIdx >= 0) {
                    layout.shapes.push({
                        type: 'rect',
                        xref: 'x',
                        yref: 'paper',
                        x0: chartData.dates[accumIdx],
                        y0: 0,
                        x1: chartData.dates[Math.min(chartData.dates.length-1, accumIdx+8)],
                        y1: 1,
                        fillcolor: 'rgba(251, 191, 36, 0.2)',
                        line: { width: 0 }
                    });
                    
                    layout.annotations.push({
                        x: chartData.dates[accumIdx+4],
                        y: chartData.closes[accumIdx],
                        text: `Accumulation Phase`,
                        showarrow: true,
                        arrowhead: 2,
                        arrowcolor: '#fbbf24',
                        font: { color: '#fbbf24', size: 9 },
                        bgcolor: 'rgba(0,0,0,0.8)',
                        bordercolor: '#fbbf24',
                        borderwidth: 1
                    });
                }
            }
            
            if (stages.first_breakout) {
                const breakoutIdx = chartData.dates.findIndex(d => d.includes(stages.first_breakout));
                if (breakoutIdx >= 0) {
                    layout.annotations.push({
                        x: chartData.dates[breakoutIdx],
                        y: chartData.closes[breakoutIdx],
                        text: `First Breakout Target`,
                        showarrow: true,
                        arrowhead: 2,
                        arrowcolor: '#10b981',
                        font: { color: '#10b981', size: 9 },
                        bgcolor: 'rgba(0,0,0,0.8)',
                        bordercolor: '#10b981',
                        borderwidth: 1
                    });
                }
            }
        } else if (chartData.symbol === 'META') {
            // Fallback highlighting
            const bottomStart = chartData.dates.findIndex(d => d.includes('2022-11'));
            const bottomEnd = chartData.dates.findIndex(d => d.includes('2022-12'));
            
            if (bottomStart >= 0 && bottomEnd >= 0) {
                layout.shapes = [{
                    type: 'rect',
                    xref: 'x',
                    yref: 'paper',
                    x0: chartData.dates[bottomStart],
                    y0: 0,
                    x1: chartData.dates[bottomEnd],
                    y1: 1,
                    fillcolor: 'rgba(251, 191, 36, 0.2)',
                    line: { width: 0 }
                }];
                
                layout.annotations = [{
                    x: chartData.dates[Math.floor((bottomStart + bottomEnd) / 2)],
                    y: Math.min(...chartData.closes.slice(bottomStart, bottomEnd)),
                    text: `Similar Pattern Area`,
                    showarrow: true,
                    arrowhead: 2,
                    arrowcolor: '#fbbf24',
                    font: { color: '#fbbf24', size: 9 },
                    bgcolor: 'rgba(0,0,0,0.8)',
                    bordercolor: '#fbbf24',
                    borderwidth: 1
                }];
            }
        }
        
        Plotly.newPlot(chartId, [trace], layout, config);
        
        // Add click-to-enlarge functionality
        element.style.cursor = 'pointer';
        element.title = 'Click to enlarge';
        element.addEventListener('click', () => {
            openAICoachChartModal(chartData, [trace], layout);
        });
        
        console.log('Historical comparison chart with similarity highlighting rendered successfully');
    } catch (error) {
        console.error('Error rendering historical chart:', error);
        element.innerHTML = '<div class="text-center text-gray-500 py-8">Chart unavailable</div>';
    }
}

// Open AI coach chart in enlarged modal
function openAICoachChartModal(chartData, traces, layout) {
    // Create modal overlay
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-[60]';
    modal.style.backdropFilter = 'blur(4px)';
    
    // Create modal content
    const modalContent = document.createElement('div');
    modalContent.className = 'bg-gray-900 rounded-lg p-6 max-w-6xl w-full mx-4 max-h-[90vh] overflow-auto';
    
    // Create modal header
    const header = document.createElement('div');
    header.className = 'flex justify-between items-center mb-4';
    header.innerHTML = `
        <h3 class="text-xl font-bold text-white">${chartData.title || 'Historical Pattern Analysis'}</h3>
        <button id="closeAIChartModal" class="text-gray-400 hover:text-white text-2xl font-bold">×</button>
    `;
    
    // Create enlarged chart container
    const enlargedChart = document.createElement('div');
    enlargedChart.id = 'enlargedAIChart';
    enlargedChart.style.height = '600px';
    enlargedChart.style.width = '100%';
    
    // Create pattern legend
    const legendPanel = document.createElement('div');
    legendPanel.className = 'mt-4 bg-gray-800 rounded-lg p-4';
    legendPanel.innerHTML = `
        <h4 class="text-lg font-semibold text-white mb-3">Pattern Recognition Guide</h4>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
            <div class="flex items-center space-x-2">
                <div class="w-4 h-4 rounded-full bg-red-500"></div>
                <span class="text-gray-300">Pattern Bottom - Reversal zone</span>
            </div>
            <div class="flex items-center space-x-2">
                <div class="w-4 h-4 bg-yellow-500"></div>
                <span class="text-gray-300">Accumulation - Base building</span>
            </div>
            <div class="flex items-center space-x-2">
                <div class="w-4 h-4 rounded-full bg-green-500"></div>
                <span class="text-gray-300">Breakout - Momentum target</span>
            </div>
            <div class="flex items-center space-x-2">
                <div class="w-4 h-4 rounded-full bg-purple-500"></div>
                <span class="text-gray-300">Confirmation - Final target</span>
            </div>
        </div>
        <div class="mt-4 p-3 bg-gray-700 rounded">
            <p class="text-gray-300 text-sm">
                <strong class="text-white">Trading Insight:</strong> This ${chartData.symbol} pattern demonstrates 
                a complete reversal cycle. Look for similar price action, volume patterns, and technical 
                indicators in current market conditions to identify high-probability setups.
            </p>
        </div>
    `;
    
    // Assemble modal
    modalContent.appendChild(header);
    modalContent.appendChild(enlargedChart);
    modalContent.appendChild(legendPanel);
    modal.appendChild(modalContent);
    
    // Add to page
    document.body.appendChild(modal);
    
    // Enhanced layout for larger chart
    const enlargedLayout = {
        ...layout,
        height: 600,
        title: {
            ...layout.title,
            font: { color: '#d1d5db', size: 18 }
        },
        margin: { l: 80, r: 40, t: 80, b: 80 }
    };
    
    const enlargedConfig = {
        displayModeBar: true,
        displaylogo: false,
        modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d'],
        responsive: true
    };
    
    // Render enlarged chart
    try {
        Plotly.newPlot(enlargedChart, traces, enlargedLayout, enlargedConfig);
    } catch (error) {
        console.error('Error rendering enlarged AI chart:', error);
        enlargedChart.innerHTML = '<div class="text-center text-gray-500 py-8">Chart rendering failed</div>';
    }
    
    // Close modal functionality
    const closeModal = () => {
        document.body.removeChild(modal);
    };
    
    document.getElementById('closeAIChartModal').addEventListener('click', closeModal);
    modal.addEventListener('click', (e) => {
        if (e.target === modal) closeModal();
    });
    
    // ESC key to close
    const handleEscape = (e) => {
        if (e.key === 'Escape') {
            closeModal();
            document.removeEventListener('keydown', handleEscape);
        }
    };
    document.addEventListener('keydown', handleEscape);
}

// Debug function to test AI review
window.testAIReview = function(symbol) {
    console.log('Testing AI review for:', symbol);
    if (typeof getAIReview === 'function') {
        console.log('getAIReview function found, calling...');
        getAIReview(symbol);
    } else {
        console.error('getAIReview function not found');
    }
};
