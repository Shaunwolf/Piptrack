// Forecast and Spaghetti Model Chart functionality

// Global forecast state
window.forecastState = {
    currentChart: null,
    chartStoryMode: false,
    activePaths: []
};

// Initialize forecast functionality
document.addEventListener('DOMContentLoaded', function() {
    initializeForecastCharts();
});

// Initialize forecast charts
function initializeForecastCharts() {
    // Check if we're on the forecast page
    const forecastChart = document.getElementById('forecastChart');
    if (forecastChart) {
        // Initialize main forecast chart
        setupForecastChart();
    }
    
    // Check for modal forecast chart
    const modalChart = document.getElementById('modalForecastChart');
    if (modalChart) {
        setupModalForecastChart();
    }
}

// Setup main forecast chart
function setupForecastChart() {
    const container = document.getElementById('forecastChart');
    if (!container) return;
    
    // Default empty chart
    renderEmptyForecastChart(container);
}

// Setup modal forecast chart
function setupModalForecastChart() {
    const container = document.getElementById('modalForecastChart');
    if (!container) return;
    
    // Default empty chart
    renderEmptyForecastChart(container);
}

// Render spaghetti model chart
function renderSpaghettiChart(paths, stockData, containerId = 'forecastChart') {
    const container = document.getElementById(containerId);
    if (!container || !paths || !stockData) return;
    
    try {
        // Prepare data for Plotly
        const traces = [];
        const currentPrice = stockData.price;
        const symbol = stockData.symbol;
        
        // Create base price line (current price)
        const baseLine = {
            x: [0, 1, 2, 3, 4, 5],
            y: Array(6).fill(currentPrice),
            mode: 'lines',
            name: 'Current Price',
            line: {
                color: '#6B7280',
                width: 2,
                dash: 'dash'
            },
            hovertemplate: `<b>Current Price</b><br>$${currentPrice}<extra></extra>`
        };
        traces.push(baseLine);
        
        // Add each forecast path
        paths.forEach((path, index) => {
            const pathTrace = {
                x: [0, 1, 2, 3, 4, 5],
                y: [currentPrice, ...path.targets],
                mode: 'lines+markers',
                name: `${path.type.charAt(0).toUpperCase() + path.type.slice(1)} (${Math.round(path.probability * 100)}%)`,
                line: {
                    color: path.color,
                    width: 3,
                    shape: 'spline'
                },
                marker: {
                    size: 6,
                    color: path.color
                },
                opacity: 0.8,
                hovertemplate: `<b>${path.description}</b><br>` +
                              `Day %{x}: $%{y}<br>` +
                              `Probability: ${Math.round(path.probability * 100)}%<extra></extra>`
            };
            traces.push(pathTrace);
            
            // Add risk zones as filled areas
            if (path.risk_zones && path.risk_zones.length >= 2) {
                const riskZone = {
                    x: [0, 1, 2, 3, 4, 5, 5, 4, 3, 2, 1, 0],
                    y: [
                        ...Array(6).fill(path.risk_zones[1]), // Upper bound
                        ...Array(6).fill(path.risk_zones[0]).reverse() // Lower bound
                    ],
                    fill: 'toself',
                    fillcolor: path.color + '20', // 20% opacity
                    line: { color: 'transparent' },
                    name: `${path.type} Risk Zone`,
                    showlegend: false,
                    hoverinfo: 'skip'
                };
                traces.push(riskZone);
            }
        });
        
        // Chart layout
        const layout = {
            title: {
                text: `${symbol} - 5-Day Spaghetti Forecast`,
                font: { color: '#FFFFFF', size: 18 }
            },
            xaxis: {
                title: 'Days',
                gridcolor: '#374151',
                tickcolor: '#6B7280',
                color: '#9CA3AF',
                range: [-0.5, 5.5]
            },
            yaxis: {
                title: 'Price ($)',
                gridcolor: '#374151',
                tickcolor: '#6B7280',
                color: '#9CA3AF',
                tickformat: '$.2f'
            },
            plot_bgcolor: '#1A1F29',
            paper_bgcolor: '#1A1F29',
            font: { color: '#FFFFFF' },
            legend: {
                orientation: 'h',
                y: -0.2,
                font: { color: '#9CA3AF' }
            },
            hovermode: 'closest',
            margin: { t: 50, b: 80, l: 60, r: 20 }
        };
        
        // Chart configuration
        const config = {
            responsive: true,
            displayModeBar: true,
            modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d'],
            displaylogo: false,
            toImageButtonOptions: {
                format: 'png',
                filename: `${symbol}_forecast`,
                height: 500,
                width: 800,
                scale: 1
            }
        };
        
        // Render the chart
        Plotly.newPlot(container, traces, layout, config);
        
        // Store reference
        window.forecastState.currentChart = { container, traces, layout, config };
        window.forecastState.activePaths = paths;
        
        console.log(`Rendered spaghetti chart for ${symbol} with ${paths.length} paths`);
        
    } catch (error) {
        console.error('Error rendering spaghetti chart:', error);
        renderErrorChart(container, 'Error rendering forecast chart');
    }
}

// Render modal spaghetti chart
function renderModalSpaghettiChart(paths, stockData) {
    renderSpaghettiChart(paths, stockData, 'modalForecastChart');
}

// Render empty forecast chart
function renderEmptyForecastChart(container) {
    const traces = [{
        x: [0, 1, 2, 3, 4, 5],
        y: [100, 100, 100, 100, 100, 100],
        mode: 'lines',
        name: 'No Data',
        line: { color: '#6B7280', width: 2, dash: 'dash' },
        hovertemplate: 'No forecast data available<extra></extra>'
    }];
    
    const layout = {
        title: {
            text: 'Spaghetti Forecast - No Data',
            font: { color: '#6B7280', size: 16 }
        },
        xaxis: {
            title: 'Days',
            gridcolor: '#374151',
            tickcolor: '#6B7280',
            color: '#6B7280'
        },
        yaxis: {
            title: 'Price ($)',
            gridcolor: '#374151',
            tickcolor: '#6B7280',
            color: '#6B7280'
        },
        plot_bgcolor: '#1A1F29',
        paper_bgcolor: '#1A1F29',
        font: { color: '#6B7280' },
        showlegend: false
    };
    
    const config = {
        responsive: true,
        displayModeBar: false
    };
    
    Plotly.newPlot(container, traces, layout, config);
}

// Render error chart
function renderErrorChart(container, message) {
    container.innerHTML = `
        <div class="flex items-center justify-center h-full">
            <div class="text-center text-gray-400">
                <i class="fas fa-exclamation-triangle text-4xl mb-4"></i>
                <p>${message}</p>
            </div>
        </div>
    `;
}

// Render chart story mode
function renderChartStoryMode(storyData, stockData) {
    const container = document.getElementById('priceChart');
    if (!container || !storyData) return;
    
    try {
        // Prepare price data
        const dates = storyData.map(point => point.date);
        const prices = storyData.map(point => point.price);
        const comments = storyData.map(point => point.comment);
        
        const trace = {
            x: dates,
            y: prices,
            mode: 'lines+markers',
            name: `${stockData.symbol} Price`,
            line: { color: '#3B82F6', width: 2 },
            marker: { size: 6, color: '#3B82F6' },
            text: comments,
            hovertemplate: '<b>%{text}</b><br>Date: %{x}<br>Price: $%{y}<extra></extra>'
        };
        
        const layout = {
            title: {
                text: `${stockData.symbol} - Chart Story Mode`,
                font: { color: '#FFFFFF', size: 16 }
            },
            xaxis: {
                title: 'Date',
                gridcolor: '#374151',
                tickcolor: '#6B7280',
                color: '#9CA3AF'
            },
            yaxis: {
                title: 'Price ($)',
                gridcolor: '#374151',
                tickcolor: '#6B7280',
                color: '#9CA3AF',
                tickformat: '$.2f'
            },
            plot_bgcolor: '#1A1F29',
            paper_bgcolor: '#1A1F29',
            font: { color: '#FFFFFF' },
            showlegend: false,
            margin: { t: 50, b: 50, l: 60, r: 20 }
        };
        
        const config = {
            responsive: true,
            displayModeBar: false
        };
        
        Plotly.newPlot(container, [trace], layout, config);
        
        // Update comments display
        updateChartComments(storyData);
        
    } catch (error) {
        console.error('Error rendering chart story:', error);
    }
}

// Update chart comments display
function updateChartComments(storyData) {
    const commentsContainer = document.getElementById('chartComments');
    if (!commentsContainer) return;
    
    const commentsHtml = storyData.map(point => `
        <div class="flex items-start space-x-3 p-3 bg-dark-accent rounded-lg">
            <div class="text-xs text-gray-400 whitespace-nowrap">${point.date}</div>
            <div class="text-sm text-gray-300">${point.comment}</div>
            <div class="text-xs text-accent-blue font-semibold">$${point.price}</div>
        </div>
    `).join('');
    
    commentsContainer.innerHTML = commentsHtml;
}

// Generate forecast paths (called from backend)
async function generateForecastPaths(symbol) {
    try {
        showLoading();
        
        const response = await fetch('/generate_forecast', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ symbol })
        });
        
        const data = await response.json();
        
        if (data.success) {
            return data.paths;
        } else {
            throw new Error(data.error || 'Failed to generate forecast');
        }
        
    } catch (error) {
        console.error('Error generating forecast paths:', error);
        showAlert('Error generating forecast: ' + error.message, 'error');
        return [];
    } finally {
        hideLoading();
    }
}

// Update forecast display
function updateForecastDisplay(paths, stockData) {
    // Update the main chart
    renderSpaghettiChart(paths, stockData);
    
    // Update path cards
    updatePathCards(paths);
    
    // Update key levels
    updateKeyLevels(paths, stockData);
}

// Update path cards
function updatePathCards(paths) {
    paths.forEach(path => {
        const cardId = path.type + 'Scenario';
        const card = document.getElementById(cardId);
        
        if (card) {
            const probabilityElement = card.querySelector('.scenario-probability');
            const targetsElement = card.querySelector(`#${path.type}Targets`);
            
            if (probabilityElement) {
                probabilityElement.textContent = `${Math.round(path.probability * 100)}%`;
            }
            
            if (targetsElement && path.targets && path.targets.length > 0) {
                const minTarget = Math.min(...path.targets);
                const maxTarget = Math.max(...path.targets);
                targetsElement.textContent = `$${minTarget.toFixed(2)} - $${maxTarget.toFixed(2)}`;
            }
        }
    });
}

// Update key levels display
function updateKeyLevels(paths, stockData) {
    const currentPriceEl = document.getElementById('currentPrice');
    const resistanceLevelEl = document.getElementById('resistanceLevel');
    const supportLevelEl = document.getElementById('supportLevel');
    const volatilityLevelEl = document.getElementById('volatilityLevel');
    const riskZoneEl = document.getElementById('riskZone');
    
    if (currentPriceEl) {
        currentPriceEl.textContent = `$${stockData.price}`;
    }
    
    // Calculate resistance and support from paths
    const allTargets = paths.flatMap(path => path.targets || []);
    const maxTarget = Math.max(...allTargets, stockData.price);
    const minTarget = Math.min(...allTargets, stockData.price);
    
    if (resistanceLevelEl) {
        resistanceLevelEl.textContent = `$${maxTarget.toFixed(2)}`;
    }
    
    if (supportLevelEl) {
        supportLevelEl.textContent = `$${minTarget.toFixed(2)}`;
    }
    
    if (volatilityLevelEl) {
        const volatility = ((maxTarget - minTarget) / stockData.price * 100).toFixed(1);
        volatilityLevelEl.textContent = `${volatility}%`;
    }
    
    if (riskZoneEl) {
        const riskRange = (maxTarget - minTarget).toFixed(2);
        riskZoneEl.textContent = `±$${riskRange}`;
    }
}

// Export forecast chart
function exportForecastChart() {
    if (!window.forecastState.currentChart) {
        showAlert('No chart to export', 'error');
        return;
    }
    
    try {
        const { container } = window.forecastState.currentChart;
        
        Plotly.toImage(container, {
            format: 'png',
            width: 1200,
            height: 600,
            scale: 2
        }).then(function(url) {
            const link = document.createElement('a');
            link.download = 'forecast_chart.png';
            link.href = url;
            link.click();
            
            showAlert('Chart exported successfully', 'success');
        });
        
    } catch (error) {
        console.error('Error exporting chart:', error);
        showAlert('Error exporting chart', 'error');
    }
}

// Animate path highlighting
function highlightForecastPath(pathType) {
    if (!window.forecastState.currentChart) return;
    
    const { container } = window.forecastState.currentChart;
    
    // Find the trace for this path type
    const traces = container.data;
    const pathTrace = traces.find(trace => 
        trace.name && trace.name.toLowerCase().includes(pathType.toLowerCase())
    );
    
    if (pathTrace) {
        // Temporarily increase line width and opacity
        const originalWidth = pathTrace.line.width;
        const originalOpacity = pathTrace.opacity;
        
        Plotly.restyle(container, {
            'line.width': pathTrace.line.width * 1.5,
            'opacity': 1
        }, [traces.indexOf(pathTrace)]);
        
        // Reset after 2 seconds
        setTimeout(() => {
            Plotly.restyle(container, {
                'line.width': originalWidth,
                'opacity': originalOpacity
            }, [traces.indexOf(pathTrace)]);
        }, 2000);
    }
}

// Forecast comparison functionality
function compareForecastWithActual(symbol, forecastDate) {
    // This would fetch actual price data and compare with forecast
    // For now, just show a placeholder
    showAlert('Forecast comparison feature coming soon', 'info');
}

// Export functions for global access
window.renderSpaghettiChart = renderSpaghettiChart;
window.renderModalSpaghettiChart = renderModalSpaghettiChart;
window.renderChartStoryMode = renderChartStoryMode;
window.generateForecastPaths = generateForecastPaths;
window.updateForecastDisplay = updateForecastDisplay;
window.exportForecastChart = exportForecastChart;
window.highlightForecastPath = highlightForecastPath;
