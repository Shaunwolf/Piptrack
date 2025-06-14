/**
 * Enhanced Forecast Page JavaScript
 * Handles advanced forecasting features, interactive charts, and trading plan generation
 */

class EnhancedForecastManager {
    constructor() {
        this.probabilityMode = false;
        this.chartStoryEnabled = false;
        this.tooltips = new Map();
        this.initializeCharts();
        this.setupEventListeners();
    }

    initializeCharts() {
        this.forecastChart = null;
        this.priceChart = null;
        this.historicalChart = null;
    }

    setupEventListeners() {
        // Chart controls
        document.getElementById('showVolume')?.addEventListener('change', this.updateChartOptions.bind(this));
        document.getElementById('showSupport')?.addEventListener('change', this.updateChartOptions.bind(this));
        document.getElementById('showFib')?.addEventListener('change', this.updateChartOptions.bind(this));

        // Tooltip triggers
        document.querySelectorAll('.tooltip-trigger').forEach(trigger => {
            trigger.addEventListener('mouseenter', this.showTooltip.bind(this));
            trigger.addEventListener('mouseleave', this.hideTooltip.bind(this));
        });

        // Checklist interactions
        document.querySelectorAll('.checklist-item input').forEach(checkbox => {
            checkbox.addEventListener('change', this.updateChecklistProgress.bind(this));
        });
    }

    renderEnhancedSpaghettiChart(paths, stockData) {
        const chartContainer = document.getElementById('forecastChart');
        if (!chartContainer) return;

        // Generate time series for next 5 days
        const dates = this.generateForecastDates(5);
        const currentPrice = stockData.price;

        // Prepare traces for each path
        const traces = paths.map((path, index) => {
            const pathData = this.generatePathData(path, currentPrice, dates);
            
            return {
                x: dates,
                y: pathData.prices,
                mode: 'lines',
                name: path.type.replace('_', ' ').toUpperCase(),
                line: {
                    color: path.color,
                    width: path.probability > 0.3 ? 3 : 2,
                    dash: path.probability < 0.2 ? 'dash' : 'solid'
                },
                opacity: this.probabilityMode ? path.probability : 0.8,
                hovertemplate: `<b>${path.type.replace('_', ' ')}</b><br>` +
                              `Price: $%{y:.2f}<br>` +
                              `Probability: ${(path.probability * 100).toFixed(1)}%<br>` +
                              `<extra></extra>`
            };
        });

        // Add current price line
        traces.unshift({
            x: [dates[0], dates[0]],
            y: [currentPrice * 0.95, currentPrice * 1.05],
            mode: 'lines',
            name: 'Current Price',
            line: { color: 'white', width: 2, dash: 'dot' },
            showlegend: false
        });

        // Add support/resistance levels if enabled
        if (document.getElementById('showSupport')?.checked) {
            traces.push(...this.generateSupportResistanceTraces(stockData, dates));
        }

        // Add Fibonacci levels if enabled
        if (document.getElementById('showFib')?.checked) {
            traces.push(...this.generateFibonacciTraces(stockData, dates));
        }

        const layout = {
            title: {
                text: `${stockData.symbol} Multi-Path Forecast`,
                font: { color: 'white', size: 18 }
            },
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(17, 24, 39, 0.8)',
            font: { color: 'white' },
            xaxis: {
                title: 'Date',
                gridcolor: 'rgba(75, 85, 99, 0.3)',
                showgrid: true
            },
            yaxis: {
                title: 'Price ($)',
                gridcolor: 'rgba(75, 85, 99, 0.3)',
                showgrid: true
            },
            legend: {
                bgcolor: 'rgba(17, 24, 39, 0.8)',
                bordercolor: 'rgba(75, 85, 99, 0.5)',
                borderwidth: 1
            },
            hovermode: 'x unified'
        };

        const config = {
            responsive: true,
            displayModeBar: true,
            modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d'],
            displaylogo: false
        };

        Plotly.newPlot(chartContainer, traces, layout, config);
        this.forecastChart = chartContainer;
    }

    generatePathData(path, currentPrice, dates) {
        const prices = [currentPrice];
        const volatility = 0.02; // 2% daily volatility
        
        // Generate price movement based on path type
        for (let i = 1; i < dates.length; i++) {
            let drift = 0;
            
            switch (path.type) {
                case 'momentum':
                    drift = 0.01 * Math.pow(0.9, i-1); // Decreasing momentum
                    break;
                case 'retest':
                    drift = i < 3 ? -0.005 : 0.015; // Pullback then move
                    break;
                case 'breakdown':
                    drift = -0.008 * (1 + i * 0.1); // Accelerating decline
                    break;
                case 'sideways':
                    drift = (Math.random() - 0.5) * 0.005; // Random walk
                    break;
            }
            
            const randomComponent = (Math.random() - 0.5) * volatility;
            const priceChange = drift + randomComponent;
            prices.push(prices[i-1] * (1 + priceChange));
        }
        
        return { prices };
    }

    generateForecastDates(days) {
        const dates = [];
        const now = new Date();
        
        for (let i = 0; i < days; i++) {
            const date = new Date(now);
            date.setDate(date.getDate() + i);
            dates.push(date.toISOString().split('T')[0]);
        }
        
        return dates;
    }

    generateSupportResistanceTraces(stockData, dates) {
        const support = stockData.price * 0.95;
        const resistance = stockData.price * 1.08;
        
        return [
            {
                x: dates,
                y: new Array(dates.length).fill(support),
                mode: 'lines',
                name: 'Support',
                line: { color: 'rgba(34, 197, 94, 0.6)', width: 1, dash: 'dash' },
                showlegend: false
            },
            {
                x: dates,
                y: new Array(dates.length).fill(resistance),
                mode: 'lines',
                name: 'Resistance',
                line: { color: 'rgba(239, 68, 68, 0.6)', width: 1, dash: 'dash' },
                showlegend: false
            }
        ];
    }

    generateFibonacciTraces(stockData, dates) {
        const high = stockData.price * 1.1;
        const low = stockData.price * 0.9;
        const diff = high - low;
        
        const fibLevels = [0.236, 0.382, 0.5, 0.618, 0.786];
        
        return fibLevels.map(level => ({
            x: dates,
            y: new Array(dates.length).fill(high - (diff * level)),
            mode: 'lines',
            name: `Fib ${(level * 100).toFixed(1)}%`,
            line: { 
                color: `rgba(147, 51, 234, ${0.3 + level * 0.4})`, 
                width: 1, 
                dash: 'dot' 
            },
            showlegend: false
        }));
    }

    updateChartOptions() {
        if (this.forecastChart && window.forecastPaths && window.stockData) {
            this.renderEnhancedSpaghettiChart(window.forecastPaths, window.stockData);
        }
    }

    toggleProbabilityMode() {
        this.probabilityMode = !this.probabilityMode;
        this.updateChartOptions();
        
        const button = event.target;
        button.textContent = this.probabilityMode ? 'Standard View' : 'Probability View';
        button.classList.toggle('active');
    }

    async generateTradingPlan() {
        const button = event.target;
        const originalText = button.innerHTML;
        button.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Generating...';
        button.disabled = true;

        try {
            const response = await fetch('/generate_trading_plan', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    symbol: window.stockData.symbol,
                    paths: window.forecastPaths 
                })
            });

            const data = await response.json();
            
            if (data.success) {
                this.updateTradingPlanDisplay(data.plan);
                this.showNotification('Trading plan generated successfully', 'success');
            } else {
                this.showNotification('Error generating trading plan: ' + data.error, 'error');
            }
        } catch (error) {
            this.showNotification('Error generating trading plan', 'error');
        } finally {
            button.innerHTML = originalText;
            button.disabled = false;
        }
    }

    updateTradingPlanDisplay(plan) {
        // Update entry strategy
        const entryCard = document.querySelector('.trading-card .trading-card-content');
        if (entryCard && plan.entry) {
            this.updateStrategyDisplay(entryCard, plan.entry);
        }

        // Update exit strategy
        const exitCard = document.querySelectorAll('.trading-card .trading-card-content')[1];
        if (exitCard && plan.exit) {
            this.updateStrategyDisplay(exitCard, plan.exit);
        }
    }

    updateStrategyDisplay(container, data) {
        const items = container.querySelectorAll('.strategy-item .strategy-value');
        if (items.length >= 4) {
            items[0].textContent = data.zone || 'N/A';
            items[1].textContent = data.trigger || 'N/A';
            items[2].textContent = data.size || 'N/A';
            items[3].textContent = data.risk || 'N/A';
        }
    }

    async toggleChartStory() {
        const toggle = document.getElementById('chartStoryToggle');
        const container = document.getElementById('chartStoryContainer');

        if (toggle.checked) {
            container.classList.remove('hidden');
            await this.loadChartStoryData();
        } else {
            container.classList.add('hidden');
        }
    }

    async loadChartStoryData() {
        try {
            const response = await fetch(`/chart_story/${window.stockData.symbol}`);
            const data = await response.json();

            if (data.success) {
                this.renderChartStory(data.story);
            }
        } catch (error) {
            console.error('Error loading chart story:', error);
        }
    }

    renderChartStory(storyData) {
        const chartContainer = document.getElementById('priceChart');
        const commentsContainer = document.getElementById('chartComments');

        if (!chartContainer || !storyData) return;

        // Render price chart with story points
        const trace = {
            x: storyData.dates,
            y: storyData.prices,
            mode: 'lines+markers',
            name: 'Price',
            line: { color: '#60a5fa', width: 2 },
            marker: { 
                size: storyData.events.map(e => e.importance * 8 + 4),
                color: storyData.events.map(e => this.getEventColor(e.type))
            },
            hovertemplate: '<b>%{text}</b><br>Price: $%{y:.2f}<extra></extra>',
            text: storyData.events.map(e => e.title)
        };

        const layout = {
            title: { text: 'Chart Story Analysis', font: { color: 'white' } },
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(17, 24, 39, 0.8)',
            font: { color: 'white' },
            xaxis: { title: 'Date', gridcolor: 'rgba(75, 85, 99, 0.3)' },
            yaxis: { title: 'Price ($)', gridcolor: 'rgba(75, 85, 99, 0.3)' }
        };

        Plotly.newPlot(chartContainer, [trace], layout, { responsive: true });

        // Render story comments
        commentsContainer.innerHTML = storyData.events.map(event => `
            <div class="story-comment bg-gray-800/40 rounded-xl p-4 border border-gray-600/30">
                <div class="flex items-center space-x-2 mb-2">
                    <i class="fas fa-${this.getEventIcon(event.type)} text-${this.getEventColor(event.type)}-400"></i>
                    <span class="text-sm font-medium text-white">${event.title}</span>
                    <span class="text-xs text-gray-400">${event.date}</span>
                </div>
                <p class="text-sm text-gray-300">${event.description}</p>
                <div class="text-xs text-gray-500 mt-2">
                    Impact: ${event.importance}/5 | Type: ${event.type}
                </div>
            </div>
        `).join('');
    }

    getEventColor(type) {
        const colors = {
            'breakout': 'green',
            'resistance': 'red',
            'support': 'blue',
            'volume': 'purple',
            'news': 'yellow'
        };
        return colors[type] || 'gray';
    }

    getEventIcon(type) {
        const icons = {
            'breakout': 'arrow-up',
            'resistance': 'minus',
            'support': 'plus',
            'volume': 'volume-up',
            'news': 'newspaper'
        };
        return icons[type] || 'circle';
    }

    showTooltip(event) {
        const trigger = event.target;
        const tooltip = trigger.getAttribute('data-tooltip');
        
        if (!tooltip) return;

        const tooltipEl = document.createElement('div');
        tooltipEl.className = 'tooltip-popup';
        tooltipEl.innerHTML = tooltip;
        document.body.appendChild(tooltipEl);

        const rect = trigger.getBoundingClientRect();
        tooltipEl.style.left = rect.left + (rect.width / 2) - (tooltipEl.offsetWidth / 2) + 'px';
        tooltipEl.style.top = rect.top - tooltipEl.offsetHeight - 8 + 'px';

        this.tooltips.set(trigger, tooltipEl);
    }

    hideTooltip(event) {
        const trigger = event.target;
        const tooltipEl = this.tooltips.get(trigger);
        
        if (tooltipEl) {
            tooltipEl.remove();
            this.tooltips.delete(trigger);
        }
    }

    updateChecklistProgress() {
        const checkboxes = document.querySelectorAll('.checklist-item input[type="checkbox"]');
        const checked = document.querySelectorAll('.checklist-item input[type="checkbox"]:checked').length;
        const total = checkboxes.length;
        const percentage = Math.round((checked / total) * 100);

        // Update progress indicator if exists
        const progressIndicator = document.querySelector('.checklist-progress');
        if (progressIndicator) {
            progressIndicator.textContent = `${percentage}% Complete (${checked}/${total})`;
        }

        // Auto-save checklist state
        this.saveChecklistState();
    }

    saveChecklistState() {
        const checkboxes = document.querySelectorAll('.checklist-item input[type="checkbox"]');
        const state = Array.from(checkboxes).map(cb => cb.checked);
        localStorage.setItem(`checklist_${window.stockData.symbol}`, JSON.stringify(state));
    }

    loadChecklistState() {
        const saved = localStorage.getItem(`checklist_${window.stockData.symbol}`);
        if (saved) {
            const state = JSON.parse(saved);
            const checkboxes = document.querySelectorAll('.checklist-item input[type="checkbox"]');
            checkboxes.forEach((cb, index) => {
                if (state[index] !== undefined) {
                    cb.checked = state[index];
                }
            });
            this.updateChecklistProgress();
        }
    }

    async exportForecast() {
        const button = event.target.closest('button');
        const originalText = button.innerHTML;
        button.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Exporting...';
        button.disabled = true;

        try {
            const response = await fetch('/export_forecast_pdf', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    symbol: window.stockData.symbol,
                    includeCharts: true,
                    includeChecklist: true
                })
            });

            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `${window.stockData.symbol}_forecast_${new Date().toISOString().split('T')[0]}.pdf`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
                
                this.showNotification('Forecast exported successfully', 'success');
            } else {
                this.showNotification('Error exporting forecast', 'error');
            }
        } catch (error) {
            this.showNotification('Error exporting forecast', 'error');
        } finally {
            button.innerHTML = originalText;
            button.disabled = false;
        }
    }

    async shareAnalysis() {
        if (navigator.share) {
            try {
                await navigator.share({
                    title: `${window.stockData.symbol} Forecast Analysis`,
                    text: `Check out this comprehensive forecast analysis for ${window.stockData.symbol}`,
                    url: window.location.href
                });
            } catch (error) {
                this.fallbackShare();
            }
        } else {
            this.fallbackShare();
        }
    }

    fallbackShare() {
        const url = window.location.href;
        navigator.clipboard.writeText(url).then(() => {
            this.showNotification('Analysis URL copied to clipboard', 'success');
        });
    }

    async addToWatchlist() {
        try {
            const response = await fetch('/add_to_watchlist', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ symbol: window.stockData.symbol })
            });

            const data = await response.json();
            if (data.success) {
                this.showNotification('Added to watchlist', 'success');
                event.target.innerHTML = '<i class="fas fa-check"></i>';
                event.target.classList.add('bg-green-600');
            } else {
                this.showNotification('Error adding to watchlist', 'error');
            }
        } catch (error) {
            this.showNotification('Error adding to watchlist', 'error');
        }
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="flex items-center space-x-3">
                <i class="fas fa-${type === 'success' ? 'check' : type === 'error' ? 'exclamation-triangle' : 'info'}-circle"></i>
                <span>${message}</span>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.opacity = '0';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }
}

// Global functions for template compatibility
function initializeEnhancedForecast() {
    window.enhancedForecastManager = new EnhancedForecastManager();
    
    // Load saved checklist state
    window.enhancedForecastManager.loadChecklistState();
    
    // Render enhanced charts
    if (window.forecastPaths && window.stockData) {
        window.enhancedForecastManager.renderEnhancedSpaghettiChart(window.forecastPaths, window.stockData);
    }
}

function toggleProbabilityMode() {
    window.enhancedForecastManager?.toggleProbabilityMode();
}

function generateTradingPlan() {
    window.enhancedForecastManager?.generateTradingPlan();
}

function toggleChartStory() {
    window.enhancedForecastManager?.toggleChartStory();
}

function exportForecast() {
    window.enhancedForecastManager?.exportForecast();
}

function shareAnalysis() {
    window.enhancedForecastManager?.shareAnalysis();
}

function addToWatchlist() {
    window.enhancedForecastManager?.addToWatchlist();
}

// CSS for notifications and tooltips
const style = document.createElement('style');
style.textContent = `
.notification {
    position: fixed;
    top: 20px;
    right: 20px;
    z-index: 1000;
    padding: 12px 16px;
    border-radius: 8px;
    color: white;
    font-weight: 500;
    opacity: 1;
    transition: opacity 0.3s ease;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.notification-success {
    background-color: #10b981;
}

.notification-error {
    background-color: #ef4444;
}

.notification-info {
    background-color: #3b82f6;
}

.tooltip-popup {
    position: absolute;
    z-index: 1000;
    background-color: #1f2937;
    color: white;
    padding: 8px 12px;
    border-radius: 6px;
    font-size: 12px;
    max-width: 200px;
    border: 1px solid #374151;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.story-comment {
    transition: all 0.2s ease;
}

.story-comment:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}
`;
document.head.appendChild(style);