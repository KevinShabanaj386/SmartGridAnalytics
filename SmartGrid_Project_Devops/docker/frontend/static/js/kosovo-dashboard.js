// Kosovo Dashboard JavaScript
let consumptionChart = null;
let refreshInterval = null;

// Load all Kosovo data
async function loadKosovoDashboard() {
    try {
        await Promise.all([
            loadWeatherSummary(),
            loadPricesSummary(),
            loadConsumptionSummary()
        ]);
    } catch (error) {
        console.error('Error loading Kosovo dashboard:', error);
    }
}

// Load weather summary
async function loadWeatherSummary() {
    try {
        const response = await fetch('/api/kosovo/weather');
        const data = await response.json();
        
        if (data.status === 'success' && data.data && data.data.length > 0) {
            const weatherData = data.data;
            const container = document.getElementById('weatherSummary');
            
            // Calculate average temperature
            const avgTemp = weatherData.reduce((sum, w) => sum + (w.temperature || 0), 0) / weatherData.length;
            document.getElementById('avgTemperature').textContent = `${avgTemp.toFixed(1)}°C`;
            document.getElementById('citiesCount').textContent = weatherData.length;
            
            // Display summary
            container.innerHTML = weatherData.slice(0, 3).map(w => `
                <div class="city-weather-item">
                    <div>
                        <strong>${w.city_name || w.city}</strong>
                        <span class="source-badge">${w.data_source || 'API'}</span>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 1.2rem; font-weight: bold;">${w.temperature}°C</div>
                        <small>${w.weather_condition || 'N/A'}</small>
                    </div>
                </div>
            `).join('');
        } else {
            document.getElementById('weatherSummary').innerHTML = '<p>Nuk ka të dhëna të disponueshme</p>';
        }
    } catch (error) {
        console.error('Error loading weather:', error);
        document.getElementById('weatherSummary').innerHTML = '<p style="color: #ef4444;">Gabim në ngarkim</p>';
    }
}

// Load prices summary
async function loadPricesSummary() {
    try {
        const response = await fetch('/api/kosovo/prices');
        const data = await response.json();
        
        if (data.status === 'success' && data.data && data.data.length > 0) {
            const container = document.getElementById('pricesSummary');
            let allPrices = [];
            
            data.data.forEach(source => {
                if (source.prices) {
                    Object.entries(source.prices).forEach(([type, priceInfo]) => {
                        allPrices.push({
                            source: source.source,
                            type: type,
                            price: priceInfo.price_eur_per_kwh
                        });
                    });
                }
            });
            
            if (allPrices.length > 0) {
                const avgPrice = allPrices.reduce((sum, p) => sum + p.price, 0) / allPrices.length;
                document.getElementById('avgPrice').textContent = `${avgPrice.toFixed(4)} €/kWh`;
                
                container.innerHTML = allPrices.slice(0, 3).map(p => `
                    <div class="price-item">
                        <div><strong>${p.source}</strong> - ${p.type}</div>
                        <div class="price-value">${p.price.toFixed(4)} €/kWh</div>
                    </div>
                `).join('');
            } else {
                container.innerHTML = '<p>Nuk ka çmime të disponueshme</p>';
            }
        } else {
            document.getElementById('pricesSummary').innerHTML = '<p>Nuk ka të dhëna të disponueshme</p>';
        }
    } catch (error) {
        console.error('Error loading prices:', error);
        document.getElementById('pricesSummary').innerHTML = '<p style="color: #ef4444;">Gabim në ngarkim</p>';
    }
}

// Load consumption summary
async function loadConsumptionSummary() {
    try {
        const response = await fetch('/api/kosovo/consumption');
        const data = await response.json();
        
        if (data.status === 'success' && data.data) {
            const consumption = data.data;
            const total = consumption.total_consumption_mw;
            
            if (total) {
                document.getElementById('totalConsumption').textContent = `${total} MW`;
                
                // Update chart
                updateConsumptionChart(consumption);
            }
        }
    } catch (error) {
        console.error('Error loading consumption:', error);
    }
}

// Update consumption chart
function updateConsumptionChart(consumption) {
    const ctx = document.getElementById('consumptionChart');
    if (!ctx) return;
    
    if (consumptionChart) {
        consumptionChart.destroy();
    }
    
    const regions = consumption.regions || {};
    const labels = Object.keys(regions).map(k => regions[k].name);
    const values = Object.keys(regions).map(k => regions[k].consumption_mw);
    
    if (labels.length === 0) return;
    
    consumptionChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Konsum (MW)',
                data: values,
                backgroundColor: [
                    'rgba(102, 126, 234, 0.8)',
                    'rgba(118, 75, 162, 0.8)',
                    'rgba(255, 99, 132, 0.8)',
                    'rgba(54, 162, 235, 0.8)',
                    'rgba(255, 206, 86, 0.8)'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Konsum (MW)'
                    }
                }
            }
        }
    });
}

// Refresh functions
function refreshWeather() {
    loadWeatherSummary();
}

function refreshPrices() {
    loadPricesSummary();
}

function refreshConsumption() {
    loadConsumptionSummary();
}

// Auto-refresh every 60 seconds
window.addEventListener('load', () => {
    loadKosovoDashboard();
    
    refreshInterval = setInterval(() => {
        loadKosovoDashboard();
    }, 60000);
});

window.addEventListener('beforeunload', () => {
    if (refreshInterval) {
        clearInterval(refreshInterval);
    }
});
