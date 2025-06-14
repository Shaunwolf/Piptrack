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

        // Create widget container
        const widgetContainer = document.createElement('div');
        widgetContainer.className = 'fibonacci-widget mb-4';
        widgetContainer.innerHTML = `
            <div class="flex justify-between items-center mb-2">
                <span class="text-xs text-gray-400 font-medium">Fibonacci Position</span>
                <select class="chart-type-selector text-xs bg-gray-800 border border-gray-600 rounded px-2 py-1" data-symbol="${symbol}">
                    <option value="rsi_momentum">RSI Momentum</option>
                    <option value="bollinger_squeeze">Bollinger Squeeze</option>
                    <option value="macd_divergence">MACD Divergence</option>
                    <option value="volume_profile">Volume Profile</option>
                    <option value="support_resistance">Support & Resistance</option>
                </select>
            </div>
            <div class="fibonacci-scaler mb-3" id="fibonacci-${symbol}">
                <div class="scaler-bar bg-gray-800 rounded-lg h-6 relative overflow-hidden">
                    <div class="scaler-fill h-full rounded-lg transition-all duration-500" id="scaler-fill-${symbol}"></div>
                    <div class="scaler-indicator absolute top-0 h-full w-1 bg-white shadow-lg transition-all duration-500" id="scaler-indicator-${symbol}"></div>
                </div>
                <div class="flex justify-between text-xs text-gray-500 mt-1">
                    <span>Oversold</span>
                    <span id="fibonacci-label-${symbol}">Loading...</span>
                    <span>Overbought</span>
                </div>
            </div>
            <div class="chart-container bg-gray-800/50 rounded-lg p-3" id="chart-${symbol}">
                <div class="chart-loading text-center text-gray-400 py-4">
                    <i class="fas fa-chart-line mr-2"></i>Loading chart...
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
        await this.updateWidget(symbol, 'rsi_momentum');
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
        container.innerHTML = `
            <div class="text-sm font-semibold mb-2">${data.title}</div>
            <div class="text-xs">
                <span class="text-gray-400">Squeeze: </span>
                <span class="${data.squeeze_detected ? 'text-yellow-400' : 'text-gray-500'}">${data.squeeze_detected ? 'Active' : 'None'}</span>
            </div>
            <div class="text-xs mt-1">
                <span class="text-gray-400">Breakout: </span>
                <span class="${data.breakout_direction === 'UP' ? 'text-green-400' : 'text-red-400'}">${data.breakout_direction}</span>
            </div>
        `;
    }

    renderMACDChart(container, data) {
        container.innerHTML = `
            <div class="text-sm font-semibold mb-2">${data.title}</div>
            <div class="text-xs">
                <span class="text-gray-400">Bullish Divergence: </span>
                <span class="${data.bullish_divergence ? 'text-green-400' : 'text-gray-500'}">${data.bullish_divergence ? 'Yes' : 'No'}</span>
            </div>
            <div class="text-xs mt-1">
                <span class="text-gray-400">Bearish Divergence: </span>
                <span class="${data.bearish_divergence ? 'text-red-400' : 'text-gray-500'}">${data.bearish_divergence ? 'Yes' : 'No'}</span>
            </div>
        `;
    }

    renderVolumeChart(container, data) {
        container.innerHTML = `
            <div class="text-sm font-semibold mb-2">${data.title}</div>
            <div class="text-xs">
                <span class="text-gray-400">Volume Trend: </span>
                <span class="${data.volume_trend === 'INCREASING' ? 'text-green-400' : data.volume_trend === 'DECREASING' ? 'text-red-400' : 'text-gray-400'}">${data.volume_trend}</span>
            </div>
            <div class="text-xs mt-1">
                <span class="text-gray-400">Unusual Volume: </span>
                <span class="${data.unusual_volume ? 'text-yellow-400' : 'text-gray-500'}">${data.unusual_volume ? 'Yes' : 'No'}</span>
            </div>
        `;
    }

    renderSRChart(container, data) {
        container.innerHTML = `
            <div class="text-sm font-semibold mb-2">${data.title}</div>
            <div class="text-xs">
                <span class="text-gray-400">Support Distance: </span>
                <span class="text-green-400">${data.key_level_distance.support_distance}%</span>
            </div>
            <div class="text-xs mt-1">
                <span class="text-gray-400">Resistance Distance: </span>
                <span class="text-red-400">${data.key_level_distance.resistance_distance}%</span>
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