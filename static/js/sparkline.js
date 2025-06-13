// Animated Stock Performance Sparkline
// Creates mini animated price charts for stock cards

// Global sparkline state
window.sparklineState = {
    charts: new Map(),
    animationSpeed: 1000,
    updateInterval: null,
    colors: {
        positive: '#10b981', // green-500
        negative: '#ef4444', // red-500
        neutral: '#6b7280'   // gray-500
    }
};

// Initialize sparklines when DOM loads
document.addEventListener('DOMContentLoaded', function() {
    initializeSparklines();
    setupSparklineUpdates();
});

// Initialize all sparklines on the page
function initializeSparklines() {
    console.log('Initializing sparklines');
    
    // Find all stock cards and add sparklines
    document.querySelectorAll('.stock-card').forEach(card => {
        const symbol = card.dataset.symbol;
        if (symbol) {
            addSparklineToCard(card, symbol);
        }
    });
}

// Add sparkline to a stock card
function addSparklineToCard(card, symbol) {
    // Check if sparkline already exists
    if (card.querySelector('.sparkline-container')) {
        return;
    }
    
    // Create sparkline container
    const sparklineContainer = document.createElement('div');
    sparklineContainer.className = 'sparkline-container mb-4';
    sparklineContainer.innerHTML = `
        <div class="flex justify-between items-center mb-2">
            <span class="text-xs text-gray-400 font-medium">7-Day Trend</span>
            <span id="sparkline-change-${symbol}" class="text-xs font-semibold">
                <i class="fas fa-chart-line mr-1"></i>Loading...
            </span>
        </div>
        <div class="relative h-12 bg-gray-800/50 rounded-lg overflow-hidden">
            <canvas id="sparkline-${symbol}" class="w-full h-full"></canvas>
            <div class="absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent sparkline-shimmer"></div>
        </div>
    `;
    
    // Insert sparkline before the metrics grid
    const metricsGrid = card.querySelector('.grid.grid-cols-2');
    if (metricsGrid) {
        metricsGrid.parentNode.insertBefore(sparklineContainer, metricsGrid);
    }
    
    // Initialize the sparkline chart
    initializeSparklineChart(symbol);
}

// Initialize individual sparkline chart
async function initializeSparklineChart(symbol) {
    try {
        // Fetch sparkline data for the symbol
        const data = await fetchSparklineData(symbol);
        
        if (data && !data.error && data.prices && data.prices.length > 0) {
            createSparklineChart(symbol, data);
            updateSparklineChange(symbol, data);
            
            // Add enhanced CandleCast features if available
            if (data.candle_guy_mood) {
                addCandleGuyToSparkline(symbol, createCandleGuyAnimation(data.candle_guy_mood, data.animation_speed || 1.0));
            }
        } else {
            console.error(`No valid data for ${symbol}:`, data);
            showSparklineError(symbol, data?.error || 'No data available');
        }
    } catch (error) {
        console.error(`Error initializing sparkline for ${symbol}:`, error);
        showSparklineError(symbol, 'Failed to load');
    }
}

// Fetch sparkline data from backend
async function fetchSparklineData(symbol) {
    try {
        const response = await fetch(`/api/sparkline/${symbol}`);
        if (!response.ok) {
            console.log(`Failed to fetch sparkline data for ${symbol}: ${response.status}`);
            return null;
        }
        const data = await response.json();
        
        if (data.error) {
            console.log(`Sparkline error for ${symbol}:`, data.error);
            return null;
        }
        
        // Ensure we have basic required data
        if (!data.prices || !Array.isArray(data.prices) || data.prices.length === 0) {
            console.log(`No valid price data for ${symbol}`);
            return null;
        }
        
        return data;
    } catch (error) {
        console.log(`Network error fetching sparkline for ${symbol}:`, error.message);
        return null;
    }
}

// Generate mock sparkline data (temporary for development)
function generateMockSparklineData(symbol) {
    const basePrice = Math.random() * 100 + 50;
    const prices = [];
    const dates = [];
    
    // Generate 7 days of price data
    for (let i = 6; i >= 0; i--) {
        const date = new Date();
        date.setDate(date.getDate() - i);
        dates.push(date.toISOString().split('T')[0]);
        
        // Simulate price movement
        const change = (Math.random() - 0.5) * 0.1; // -5% to +5%
        const price = i === 6 ? basePrice : prices[prices.length - 1] * (1 + change);
        prices.push(Math.max(price, 1)); // Ensure positive price
    }
    
    const change = ((prices[prices.length - 1] - prices[0]) / prices[0]) * 100;
    
    return {
        symbol: symbol,
        prices: prices,
        dates: dates,
        change: change,
        high: Math.max(...prices),
        low: Math.min(...prices)
    };
}

// Create sparkline chart using Canvas
function createSparklineChart(symbol, data) {
    const canvas = document.getElementById(`sparkline-${symbol}`);
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    const rect = canvas.getBoundingClientRect();
    
    // Set canvas size
    canvas.width = rect.width * window.devicePixelRatio;
    canvas.height = rect.height * window.devicePixelRatio;
    ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
    
    const width = rect.width;
    const height = rect.height;
    const padding = 4;
    
    // Calculate chart dimensions
    const chartWidth = width - (padding * 2);
    const chartHeight = height - (padding * 2);
    
    // Normalize price data
    const prices = data.prices;
    const minPrice = Math.min(...prices);
    const maxPrice = Math.max(...prices);
    const priceRange = maxPrice - minPrice || 1;
    
    // Create points
    const points = prices.map((price, index) => ({
        x: padding + (index / (prices.length - 1)) * chartWidth,
        y: padding + (1 - (price - minPrice) / priceRange) * chartHeight
    }));
    
    // Determine color based on overall change
    const change = data.price_change_pct || data.change || 0;
    const color = change >= 0 ? window.sparklineState.colors.positive : window.sparklineState.colors.negative;
    
    // Clear canvas
    ctx.clearRect(0, 0, width, height);
    
    // Draw gradient fill
    const gradient = ctx.createLinearGradient(0, 0, 0, height);
    gradient.addColorStop(0, color + '40'); // 25% opacity
    gradient.addColorStop(1, color + '00'); // 0% opacity
    
    // Draw filled area
    ctx.beginPath();
    ctx.moveTo(points[0].x, height - padding);
    points.forEach(point => ctx.lineTo(point.x, point.y));
    ctx.lineTo(points[points.length - 1].x, height - padding);
    ctx.closePath();
    ctx.fillStyle = gradient;
    ctx.fill();
    
    // Draw line
    ctx.beginPath();
    ctx.moveTo(points[0].x, points[0].y);
    points.forEach(point => ctx.lineTo(point.x, point.y));
    ctx.strokeStyle = color;
    ctx.lineWidth = 1.5;
    ctx.stroke();
    
    // Draw dots with animation
    animateSparklineDots(ctx, points, color);
    
    // Update change indicator
    updateSparklineChange(symbol, data);
    
    // Store chart data for updates
    window.sparklineState.charts.set(symbol, {
        canvas: canvas,
        ctx: ctx,
        data: data,
        points: points,
        color: color
    });
}

// Animate sparkline dots
function animateSparklineDots(ctx, points, color) {
    let currentDot = 0;
    
    function drawNextDot() {
        if (currentDot < points.length) {
            const point = points[currentDot];
            
            // Draw dot
            ctx.beginPath();
            ctx.arc(point.x, point.y, 2, 0, 2 * Math.PI);
            ctx.fillStyle = color;
            ctx.fill();
            
            // Draw glow
            ctx.beginPath();
            ctx.arc(point.x, point.y, 4, 0, 2 * Math.PI);
            ctx.fillStyle = color + '20';
            ctx.fill();
            
            currentDot++;
            setTimeout(drawNextDot, 100);
        }
    }
    
    drawNextDot();
}

// Update sparkline change indicator
function updateSparklineChange(symbol, data) {
    const changeElement = document.getElementById(`sparkline-change-${symbol}`);
    if (!changeElement) return;
    
    const change = data.price_change_pct || data.change || 0;
    const changeText = `${change >= 0 ? '+' : ''}${change.toFixed(2)}%`;
    const icon = change >= 0 ? 'fa-arrow-up' : 'fa-arrow-down';
    const colorClass = change >= 0 ? 'text-green-400' : 'text-red-400';
    
    changeElement.className = `text-xs font-semibold ${colorClass}`;
    changeElement.innerHTML = `<i class="fas ${icon} mr-1"></i>${changeText}`;
    
    // Add candle guy mood indicator
    if (data.candle_guy_mood) {
        const container = changeElement.parentElement;
        if (container && !container.querySelector('.mood-indicator')) {
            const moodDiv = document.createElement('div');
            moodDiv.className = 'mood-indicator text-xs text-gray-400 mt-1';
            moodDiv.innerHTML = `<i class="fas fa-smile mr-1"></i>Mood: ${data.candle_guy_mood}`;
            container.appendChild(moodDiv);
        }
    }
}

// Show sparkline error
function showSparklineError(symbol, message) {
    const changeElement = document.getElementById(`sparkline-change-${symbol}`);
    if (changeElement) {
        changeElement.className = 'text-xs text-gray-500';
        changeElement.innerHTML = `<i class="fas fa-exclamation-triangle mr-1"></i>${message}`;
    }
    
    const canvas = document.getElementById(`sparkline-${symbol}`);
    if (canvas) {
        const ctx = canvas.getContext('2d');
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        // Draw error placeholder
        ctx.fillStyle = '#374151';
        ctx.fillRect(0, canvas.height / 2 - 1, canvas.width, 2);
    }
}

// Setup periodic sparkline updates
function setupSparklineUpdates() {
    // Update sparklines every 5 minutes
    window.sparklineState.updateInterval = setInterval(() => {
        updateAllSparklines();
    }, 300000);
}

// Update all sparklines with fresh data
async function updateAllSparklines() {
    const symbols = Array.from(window.sparklineState.charts.keys());
    
    for (const symbol of symbols) {
        try {
            const data = await fetchSparklineData(symbol);
            if (data) {
                createSparklineChart(symbol, data);
            }
        } catch (error) {
            console.error(`Error updating sparkline for ${symbol}:`, error);
        }
    }
}

// Add sparkline to new stock cards dynamically
function addSparklineToNewCard(card, symbol) {
    addSparklineToCard(card, symbol);
}

// Enhanced Animation Functions for CandleCast Integration

// Enhance sparkline data with animation features
function enhanceSparklineWithAnimation(data) {
    // Add candle guy character integration
    data.candleGuyAnimation = createCandleGuyAnimation(data.candle_guy_mood, data.animation_speed);
    
    // Add momentum-based sparkle effects
    if (data.momentum_indicators && data.momentum_indicators.rsi > 70) {
        data.sparkleEffect = 'bullish';
    } else if (data.momentum_indicators && data.momentum_indicators.rsi < 30) {
        data.sparkleEffect = 'bearish';
    } else {
        data.sparkleEffect = 'neutral';
    }
    
    return data;
}

// Create candle guy animation based on mood
function createCandleGuyAnimation(mood, speed = 1.0) {
    const animations = {
        'bullish': {
            emoji: '📈',
            color: '#10b981',
            bounce: true,
            sparkles: true
        },
        'bearish': {
            emoji: '📉',
            color: '#ef4444',
            shake: true,
            storm: true
        },
        'neutral': {
            emoji: '📊',
            color: '#6b7280',
            pulse: true
        },
        'excited': {
            emoji: '🚀',
            color: '#3b82f6',
            rocket: true,
            trail: true
        },
        'confused': {
            emoji: '🤔',
            color: '#f59e0b',
            wobble: true
        }
    };
    
    return animations[mood] || animations['neutral'];
}

// Add candle guy to sparkline container
function addCandleGuyToSparkline(symbol, animation) {
    const container = document.querySelector(`#sparkline-${symbol}`).parentElement;
    
    // Remove existing candle guy
    const existing = container.querySelector('.candle-guy');
    if (existing) existing.remove();
    
    // Create new candle guy element
    const candleGuy = document.createElement('div');
    candleGuy.className = 'candle-guy absolute top-0 right-0 text-lg z-10';
    candleGuy.innerHTML = animation.emoji;
    candleGuy.style.color = animation.color;
    
    // Apply animation based on mood
    if (animation.bounce) {
        candleGuy.style.animation = 'bounce 1s infinite';
    } else if (animation.shake) {
        candleGuy.style.animation = 'shake 0.5s infinite';
    } else if (animation.pulse) {
        candleGuy.style.animation = 'pulse 2s infinite';
    } else if (animation.rocket) {
        candleGuy.style.animation = 'rocket 2s ease-in-out infinite';
    } else if (animation.wobble) {
        candleGuy.style.animation = 'wobble 1s ease-in-out infinite';
    }
    
    container.appendChild(candleGuy);
    
    // Add sparkle effects if enabled
    if (animation.sparkles) {
        addSparkleEffect(container, animation.color);
    }
}

// Add sparkle effect around sparkline
function addSparkleEffect(container, color) {
    for (let i = 0; i < 3; i++) {
        setTimeout(() => {
            const sparkle = document.createElement('div');
            sparkle.className = 'absolute text-xs opacity-80';
            sparkle.innerHTML = '✨';
            sparkle.style.left = Math.random() * 100 + '%';
            sparkle.style.top = Math.random() * 100 + '%';
            sparkle.style.animation = 'sparkle 1.5s ease-out forwards';
            
            container.appendChild(sparkle);
            
            setTimeout(() => sparkle.remove(), 1500);
        }, i * 200);
    }
}

// Enhanced chart creation with animation features
function createEnhancedSparklineChart(symbol, data) {
    // Create base chart
    createSparklineChart(symbol, data);
    
    // Add enhanced animation features if available
    if (data.candleGuyAnimation) {
        addCandleGuyToSparkline(symbol, data.candleGuyAnimation);
    }
    
    // Add volatility bands visualization
    if (data.volatility_bands) {
        addVolatilityBands(symbol, data.volatility_bands);
    }
    
    // Add price event markers
    if (data.price_events && data.price_events.length > 0) {
        addPriceEventMarkers(symbol, data.price_events);
    }
}

// Add volatility bands to chart
function addVolatilityBands(symbol, bands) {
    const canvas = document.getElementById(`sparkline-${symbol}`);
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    const rect = canvas.getBoundingClientRect();
    
    // Draw volatility bands as subtle background
    ctx.globalAlpha = 0.1;
    ctx.fillStyle = bands.trend === 'expanding' ? '#ef4444' : '#10b981';
    ctx.fillRect(0, rect.height * 0.2, rect.width, rect.height * 0.6);
    ctx.globalAlpha = 1.0;
}

// Add price event markers
function addPriceEventMarkers(symbol, events) {
    const container = document.querySelector(`#sparkline-${symbol}`).parentElement;
    
    events.forEach((event, index) => {
        const marker = document.createElement('div');
        marker.className = 'absolute w-2 h-2 rounded-full animate-ping';
        marker.style.background = event.type === 'spike' ? '#10b981' : '#ef4444';
        marker.style.left = (event.position * 100) + '%';
        marker.style.top = '50%';
        marker.title = `${event.type}: ${event.magnitude.toFixed(2)}%`;
        
        container.appendChild(marker);
        
        // Remove marker after animation
        setTimeout(() => marker.remove(), 3000);
    });
}

// Update sparkline creation function
const originalCreateSparklineChart = createSparklineChart;
createSparklineChart = function(symbol, data) {
    // Use enhanced version if animation data is available
    if (data.candleGuyAnimation || data.volatility_bands || data.price_events) {
        createEnhancedSparklineChart(symbol, data);
    } else {
        originalCreateSparklineChart(symbol, data);
    }
};

// Export functions for global access
window.addSparklineToNewCard = addSparklineToNewCard;
window.updateAllSparklines = updateAllSparklines;
window.sparklineState = window.sparklineState;
window.enhanceSparklineWithAnimation = enhanceSparklineWithAnimation;