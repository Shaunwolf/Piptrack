// Enhanced Stock Widgets with Fibonacci Scalers
// Replaces sparklines with colored Fibonacci-style visualization

class EnhancedStockWidgets {
    constructor() {
        this.widgets = new Map();
        this.chartTypes = {
            'rsi_momentum': 'RSI Momentum',
            'bollinger_squeeze': 'Bollinger Squeeze',
            'macd_divergence': 'MACD Divergence',
            'volume_profile': 'Volume Profile',
            'support_resistance': 'Support & Resistance'
        };
        this.colors = {
            extreme_oversold: '#ff4444',
            oversold: '#ff8800',
            neutral_low: '#ffcc00',
            neutral: '#00ff88',
            neutral_high: '#00ccff',
            overbought: '#4488ff',
            extreme_overbought: '#8844ff'
        };
    }

    async initializeWidgets() {
        console.log('Initializing enhanced stock widgets');
        
        // Find all stock cards and add enhanced widgets
        document.querySelectorAll('.stock-card').forEach(card => {
            const symbol = card.dataset.symbol;
            if (symbol) {
                this.addWidgetToCard(card, symbol);
            }
        });
    }

    async addWidgetToCard(card, symbol) {
        // Check if widget already exists
        if (card.querySelector('.fibonacci-widget')) {
            return;
        }

        // Create widget container with sleek design
        const widgetContainer = document.createElement('div');
        widgetContainer.className = 'fibonacci-widget mb-4 bg-gradient-to-br from-gray-900 to-gray-800 rounded-xl p-4 border border-gray-700/50 shadow-xl';
        widgetContainer.innerHTML = `
            <div class="flex justify-between items-center mb-3">
                <div class="flex items-center space-x-2">
                    <div class="w-2 h-2 bg-accent-blue rounded-full animate-pulse"></div>
                    <span class="text-sm font-semibold text-white">Market Analysis</span>
                </div>
                <select class="chart-type-selector text-xs bg-gradient-to-r from-gray-800 to-gray-700 border border-gray-600/50 rounded-md px-2 py-1 text-white focus:ring-1 focus:ring-accent-blue focus:border-transparent transition-all duration-200 shadow-md hover:shadow-lg max-w-32" data-symbol="${symbol}">
                    <option value="rsi_momentum">RSI</option>
                    <option value="bollinger_squeeze">Squeeze</option>
                    <option value="macd_divergence">MACD</option>
                    <option value="volume_profile" selected>Volume</option>
                    <option value="support_resistance">S&R</option>
                </select>
            </div>
            <div class="fibonacci-scaler mb-4" id="fibonacci-${symbol}">
                <div class="scaler-bar bg-gradient-to-r from-gray-800 via-gray-700 to-gray-800 rounded-xl h-8 relative overflow-hidden shadow-inner border border-gray-600/30">
                    <div class="scaler-fill h-full rounded-xl transition-all duration-700 ease-out shadow-lg" id="scaler-fill-${symbol}" style="background: linear-gradient(90deg, #ff4444, #ff8800, #ffcc00, #00ff88, #00ccff, #4488ff, #8844ff);"></div>
                    <div class="scaler-indicator absolute top-0 h-full w-1 bg-white rounded-full shadow-2xl transition-all duration-700 ease-out" id="scaler-indicator-${symbol}" style="box-shadow: 0 0 10px rgba(255,255,255,0.8);"></div>
                    <div class="absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent"></div>
                </div>
                <div class="flex justify-between text-xs text-gray-400 mt-2 font-medium">
                    <span class="text-red-400">Oversold</span>
                    <span id="fibonacci-label-${symbol}" class="text-white font-semibold px-2 py-1 bg-gray-800/60 rounded-lg backdrop-blur-sm">Loading...</span>
                    <span class="text-purple-400">Overbought</span>
                </div>
            </div>
            <div class="chart-container bg-gradient-to-br from-gray-800/40 to-gray-900/40 rounded-xl p-4 border border-gray-600/30 backdrop-blur-sm" id="chart-${symbol}">
                <div class="chart-loading text-center text-gray-400 py-6">
                    <div class="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-accent-blue mb-2"></div>
                    <div class="text-sm">Loading indicators...</div>
                </div>
            </div>
        `;

        // Insert widget before the metrics grid
        const metricsGrid = card.querySelector('.grid.grid-cols-2');
        if (metricsGrid) {
            metricsGrid.parentNode.insertBefore(widgetContainer, metricsGrid);
        }

        // Add chart type selector event listener
        const selector = widgetContainer.querySelector('.chart-type-selector');
        selector.addEventListener('change', (e) => {
            this.updateWidget(symbol, e.target.value);
        });

        // Load initial widget data
        await this.updateWidget(symbol, 'volume_profile');
    }

    async updateWidget(symbol, chartType) {
        try {
            const response = await fetch(`/api/widget/${symbol}?chart_type=${chartType}`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const result = await response.json();
            if (!result.success) {
                throw new Error(result.error || 'Unknown error');
            }

            const data = result.data;
            this.renderFibonacciScaler(symbol, data.fibonacci);
            this.renderChart(symbol, data.chart, chartType);
            
            // Update widget data in memory
            this.widgets.set(symbol, data);

        } catch (error) {
            console.error(`Error updating widget for ${symbol}:`, error);
            this.showWidgetError(symbol, error.message);
        }
    }

    renderFibonacciScaler(symbol, fibonacciData) {
        const scalerFill = document.getElementById(`scaler-fill-${symbol}`);
        const scalerIndicator = document.getElementById(`scaler-indicator-${symbol}`);
        const label = document.getElementById(`fibonacci-label-${symbol}`);

        if (!scalerFill || !scalerIndicator || !label) return;

        const position = fibonacciData.position * 100; // Convert to percentage
        const color = fibonacciData.color;

        // Update scaler fill
        scalerFill.style.width = `${position}%`;
        scalerFill.style.backgroundColor = color;

        // Update indicator position
        scalerIndicator.style.left = `${Math.max(0, Math.min(100, position))}%`;

        // Update label
        label.textContent = `${fibonacciData.label} (${fibonacciData.percentage}%)`;
        label.style.color = color;

        // Add subtle glow effect
        scalerFill.style.boxShadow = `0 0 10px ${color}40`;
    }

    renderChart(symbol, chartData, chartType) {
        const chartContainer = document.getElementById(`chart-${symbol}`);
        if (!chartContainer || !chartData) return;

        // Clear existing chart
        chartContainer.innerHTML = '';

        // Create chart based on type
        switch (chartType) {
            case 'rsi_momentum':
                this.renderRSIChart(chartContainer, chartData);
                break;
            case 'bollinger_squeeze':
                this.renderBollingerChart(chartContainer, chartData);
                break;
            case 'macd_divergence':
                this.renderMACDChart(chartContainer, chartData);
                break;
            case 'volume_profile':
                this.renderVolumeChart(chartContainer, chartData);
                break;
            case 'support_resistance':
                this.renderSRChart(chartContainer, chartData);
                break;
            default:
                this.renderDefaultChart(chartContainer, chartData);
        }
    }

    renderRSIChart(container, data) {
        const canvas = document.createElement('canvas');
        canvas.width = 300;
        canvas.height = 120;
        canvas.className = 'w-full h-24';
        container.appendChild(canvas);

        const ctx = canvas.getContext('2d');
        
        // Draw RSI line chart
        const values = data.data[0].y;
        const labels = data.data[0].x;
        
        this.drawLineChart(ctx, values, labels, {
            color: '#00ff88',
            min: 0,
            max: 100,
            overboughtLine: 70,
            oversoldLine: 30
        });

        // Add signal indicator
        const signalDiv = document.createElement('div');
        signalDiv.className = `text-xs font-semibold mt-2 ${data.signal === 'BUY' ? 'text-green-400' : data.signal === 'SELL' ? 'text-red-400' : 'text-gray-400'}`;
        signalDiv.innerHTML = `<i class="fas fa-${data.signal === 'BUY' ? 'arrow-up' : data.signal === 'SELL' ? 'arrow-down' : 'minus'}"></i> ${data.signal} Signal`;
        container.appendChild(signalDiv);
    }

    renderBollingerChart(container, data) {
        const statusColor = data.squeeze_detected ? '#ffcc00' : '#6b7280';
        const breakoutColor = data.breakout_direction === 'UP' ? '#00ff88' : '#ff4444';
        
        container.innerHTML = `
            <div class="flex items-center justify-between mb-3">
                <div class="text-sm font-semibold text-white">${data.title}</div>
                <div class="flex items-center space-x-1">
                    <div class="w-2 h-2 rounded-full" style="background-color: ${statusColor}; box-shadow: 0 0 8px ${statusColor}40;"></div>
                    <span class="text-xs text-gray-300">${data.status}</span>
                </div>
            </div>
            <div class="grid grid-cols-2 gap-3">
                <div class="bg-gray-800/50 rounded-lg p-3 border border-gray-600/30">
                    <div class="text-xs text-gray-400 mb-1">Squeeze Status</div>
                    <div class="flex items-center space-x-2">
                        <div class="w-3 h-3 rounded-full ${data.squeeze_detected ? 'bg-yellow-400 animate-pulse' : 'bg-gray-500'}" style="box-shadow: ${data.squeeze_detected ? '0 0 10px #ffcc0060' : 'none'};"></div>
                        <span class="text-sm font-semibold" style="color: ${statusColor};">${data.squeeze_detected ? 'ACTIVE' : 'NORMAL'}</span>
                    </div>
                </div>
                <div class="bg-gray-800/50 rounded-lg p-3 border border-gray-600/30">
                    <div class="text-xs text-gray-400 mb-1">Breakout Direction</div>
                    <div class="flex items-center space-x-2">
                        <i class="fas fa-arrow-${data.breakout_direction === 'UP' ? 'up' : 'down'} text-sm" style="color: ${breakoutColor};"></i>
                        <span class="text-sm font-semibold" style="color: ${breakoutColor};">${data.breakout_direction}</span>
                    </div>
                </div>
            </div>
        `;
    }

    renderMACDChart(container, data) {
        container.innerHTML = `
            <div class="text-sm font-semibold text-white mb-3">${data.title}</div>
            <div class="grid grid-cols-2 gap-3">
                <div class="bg-gradient-to-br from-green-900/30 to-green-800/20 rounded-lg p-3 border border-green-500/30">
                    <div class="flex items-center space-x-2 mb-2">
                        <div class="w-2 h-2 bg-green-400 rounded-full ${data.bullish_divergence ? 'animate-pulse' : 'opacity-30'}"></div>
                        <span class="text-xs text-gray-300">Bullish Signal</span>
                    </div>
                    <div class="text-lg font-bold ${data.bullish_divergence ? 'text-green-400' : 'text-gray-500'}">${data.bullish_divergence ? 'ACTIVE' : 'NONE'}</div>
                </div>
                <div class="bg-gradient-to-br from-red-900/30 to-red-800/20 rounded-lg p-3 border border-red-500/30">
                    <div class="flex items-center space-x-2 mb-2">
                        <div class="w-2 h-2 bg-red-400 rounded-full ${data.bearish_divergence ? 'animate-pulse' : 'opacity-30'}"></div>
                        <span class="text-xs text-gray-300">Bearish Signal</span>
                    </div>
                    <div class="text-lg font-bold ${data.bearish_divergence ? 'text-red-400' : 'text-gray-500'}">${data.bearish_divergence ? 'ACTIVE' : 'NONE'}</div>
                </div>
            </div>
        `;
    }

    renderVolumeChart(container, data) {
        const trendColor = data.volume_trend === 'INCREASING' ? '#00ff88' : data.volume_trend === 'DECREASING' ? '#ff4444' : '#6b7280';
        const trendIcon = data.volume_trend === 'INCREASING' ? 'trending-up' : data.volume_trend === 'DECREASING' ? 'trending-down' : 'minus';
        
        container.innerHTML = `
            <div class="text-sm font-semibold text-white mb-3">${data.title}</div>
            <div class="space-y-3">
                <div class="bg-gray-800/50 rounded-lg p-3 border border-gray-600/30">
                    <div class="flex items-center justify-between">
                        <span class="text-xs text-gray-400">Volume Trend</span>
                        <div class="flex items-center space-x-2">
                            <i class="fas fa-${trendIcon}" style="color: ${trendColor};"></i>
                            <span class="text-sm font-semibold" style="color: ${trendColor};">${data.volume_trend}</span>
                        </div>
                    </div>
                </div>
                <div class="bg-gray-800/50 rounded-lg p-3 border border-gray-600/30">
                    <div class="flex items-center justify-between">
                        <span class="text-xs text-gray-400">Unusual Activity</span>
                        <div class="flex items-center space-x-2">
                            <div class="w-3 h-3 rounded-full ${data.unusual_volume ? 'bg-yellow-400 animate-pulse' : 'bg-gray-500'}" style="box-shadow: ${data.unusual_volume ? '0 0 10px #ffcc0060' : 'none'};"></div>
                            <span class="text-sm font-semibold ${data.unusual_volume ? 'text-yellow-400' : 'text-gray-500'}">${data.unusual_volume ? 'DETECTED' : 'NORMAL'}</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    renderSRChart(container, data) {
        container.innerHTML = `
            <div class="text-sm font-semibold text-white mb-3">${data.title}</div>
            <div class="grid grid-cols-2 gap-3">
                <div class="bg-gradient-to-br from-green-900/30 to-green-800/20 rounded-lg p-3 border border-green-500/30">
                    <div class="text-xs text-gray-300 mb-1">Support Level</div>
                    <div class="flex items-center space-x-2">
                        <i class="fas fa-arrow-down text-green-400"></i>
                        <span class="text-lg font-bold text-green-400">${data.key_level_distance.support_distance}%</span>
                    </div>
                    <div class="text-xs text-gray-400 mt-1">Distance below</div>
                </div>
                <div class="bg-gradient-to-br from-red-900/30 to-red-800/20 rounded-lg p-3 border border-red-500/30">
                    <div class="text-xs text-gray-300 mb-1">Resistance Level</div>
                    <div class="flex items-center space-x-2">
                        <i class="fas fa-arrow-up text-red-400"></i>
                        <span class="text-lg font-bold text-red-400">${data.key_level_distance.resistance_distance}%</span>
                    </div>
                    <div class="text-xs text-gray-400 mt-1">Distance above</div>
                </div>
            </div>
        `;
    }

    drawLineChart(ctx, values, labels, options = {}) {
        const { color = '#00ff88', min = 0, max = 100, overboughtLine, oversoldLine } = options;
        const width = ctx.canvas.width;
        const height = ctx.canvas.height;
        const padding = 20;
        
        // Clear canvas
        ctx.clearRect(0, 0, width, height);
        
        // Draw horizontal reference lines
        if (overboughtLine !== undefined) {
            const y = height - padding - ((overboughtLine - min) / (max - min)) * (height - 2 * padding);
            ctx.strokeStyle = '#ff4444';
            ctx.setLineDash([5, 5]);
            ctx.beginPath();
            ctx.moveTo(padding, y);
            ctx.lineTo(width - padding, y);
            ctx.stroke();
        }
        
        if (oversoldLine !== undefined) {
            const y = height - padding - ((oversoldLine - min) / (max - min)) * (height - 2 * padding);
            ctx.strokeStyle = '#00ff88';
            ctx.setLineDash([5, 5]);
            ctx.beginPath();
            ctx.moveTo(padding, y);
            ctx.lineTo(width - padding, y);
            ctx.stroke();
        }
        
        // Draw main line
        ctx.setLineDash([]);
        ctx.strokeStyle = color;
        ctx.lineWidth = 2;
        ctx.beginPath();
        
        values.forEach((value, index) => {
            const x = padding + (index / (values.length - 1)) * (width - 2 * padding);
            const y = height - padding - ((value - min) / (max - min)) * (height - 2 * padding);
            
            if (index === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
        });
        
        ctx.stroke();
    }

    showWidgetError(symbol, message) {
        const scalerFill = document.getElementById(`scaler-fill-${symbol}`);
        const label = document.getElementById(`fibonacci-label-${symbol}`);
        const chartContainer = document.getElementById(`chart-${symbol}`);

        if (scalerFill) {
            scalerFill.style.width = '0%';
            scalerFill.style.backgroundColor = '#374151';
        }

        if (label) {
            label.textContent = 'Error loading data';
            label.style.color = '#ef4444';
        }

        if (chartContainer) {
            chartContainer.innerHTML = `
                <div class="text-center text-red-400 py-4">
                    <i class="fas fa-exclamation-triangle mr-2"></i>${message}
                </div>
            `;
        }
    }

    async updateAllWidgets() {
        for (const [symbol] of this.widgets) {
            const selector = document.querySelector(`.chart-type-selector[data-symbol="${symbol}"]`);
            const chartType = selector ? selector.value : 'rsi_momentum';
            await this.updateWidget(symbol, chartType);
        }
    }
}

// Global instance
window.enhancedWidgets = new EnhancedStockWidgets();

// Initialize when DOM loads
document.addEventListener('DOMContentLoaded', function() {
    window.enhancedWidgets.initializeWidgets();
    
    // Update widgets every 5 minutes
    setInterval(() => {
        window.enhancedWidgets.updateAllWidgets();
    }, 300000);
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = EnhancedStockWidgets;
}