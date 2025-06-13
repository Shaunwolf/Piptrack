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
        
        if (data && data.prices && data.prices.length > 0) {
            createSparklineChart(symbol, data);
        } else {
            showSparklineError(symbol, 'No data available');
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
            throw new Error(`HTTP ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error(`Error fetching sparkline data for ${symbol}:`, error);
        // Return mock data for development - replace with real data
        return generateMockSparklineData(symbol);
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
    const change = data.change || 0;
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
    
    const change = data.change || 0;
    const changeText = `${change >= 0 ? '+' : ''}${change.toFixed(2)}%`;
    const icon = change >= 0 ? 'fa-arrow-up' : 'fa-arrow-down';
    const colorClass = change >= 0 ? 'text-green-400' : 'text-red-400';
    
    changeElement.className = `text-xs font-semibold ${colorClass}`;
    changeElement.innerHTML = `<i class="fas ${icon} mr-1"></i>${changeText}`;
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

// Export functions for global access
window.addSparklineToNewCard = addSparklineToNewCard;
window.updateAllSparklines = updateAllSparklines;
window.sparklineState = window.sparklineState;