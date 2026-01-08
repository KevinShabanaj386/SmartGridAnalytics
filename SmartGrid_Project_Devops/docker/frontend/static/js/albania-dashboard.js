// Albania Dashboard JavaScript
let consumptionChart = null;
let priceSparklineChart = null;
let refreshInterval = null;

// Load all Albania data
async function loadAlbaniaDashboard() {
    try {
        const results = await Promise.allSettled([
            loadWeatherSummary(),
            loadPricesSummary(),
            loadConsumptionSummary(),
            loadPricesLongTermSummary(),
            loadConsumptionLongTermSummary(),
            loadPriceSparkline()
        ]);
        
        // Check for service status
        let servicesDown = 0;
        results.forEach((result, index) => {
            if (result.status === 'rejected') {
                servicesDown++;
            }
        });
        
        // Show status message if services are down
        const statusEl = document.getElementById('serviceStatus');
        const statusMsg = document.getElementById('statusMessage');
        
        if (servicesDown > 0 && statusEl && statusMsg) {
            statusEl.style.display = 'block';
            statusEl.className = 'service-status warning';
            statusMsg.textContent = `${servicesDown} shërbim(e) nuk janë të disponueshme.`;
        } else if (statusEl) {
            statusEl.style.display = 'none';
        }
    } catch (error) {
        console.error('Error loading Albania dashboard:', error);
        const statusEl = document.getElementById('serviceStatus');
        const statusMsg = document.getElementById('statusMessage');
        if (statusEl && statusMsg) {
            statusEl.style.display = 'block';
            statusEl.className = 'service-status error';
            statusMsg.textContent = `Gabim: ${error.message}`;
        }
    }
}

// Load weather summary
async function loadWeatherSummary() {
    const container = document.getElementById('weatherSummary');
    if (!container) return;
    
    try {
        const response = await fetch('/api/albania/weather');
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ error: `HTTP ${response.status}` }));
            throw new Error(errorData.error || `HTTP ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Weather API response:', data);
        
        let weatherData = [];
        if (data.status === 'success' && data.data) {
            weatherData = Array.isArray(data.data) ? data.data : [data.data];
        } else if (Array.isArray(data)) {
            weatherData = data;
        }
        
        if (weatherData.length > 0) {
            const avgTemp = weatherData.reduce((sum, w) => sum + (parseFloat(w.temperature) || 0), 0) / weatherData.length;
            const avgTempEl = document.getElementById('avgTemperature');
            const citiesCountEl = document.getElementById('citiesCount');
            
            if (avgTempEl) avgTempEl.textContent = `${avgTemp.toFixed(1)}°C`;
            if (citiesCountEl) citiesCountEl.textContent = weatherData.length;
            
            container.innerHTML = weatherData.slice(0, 3).map(w => `
                <div class="city-weather-item">
                    <div>
                        <strong>${w.city || 'Unknown'}</strong>
                        <span class="source-badge">Simulated</span>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 1.2rem; font-weight: bold;">${w.temperature || 'N/A'}°C</div>
                        <small>${w.description || 'N/A'}</small>
                    </div>
                </div>
            `).join('');
        } else {
            container.innerHTML = '<p style="color: #f59e0b;">⚠️ Nuk ka të dhëna të disponueshme.</p>';
        }
    } catch (error) {
        console.error('Error loading weather:', error);
        container.innerHTML = `<p style="color: #ef4444;">❌ Gabim: ${error.message || 'Service unavailable'}</p>`;
    }
}

// Load prices summary
async function loadPricesSummary() {
    const container = document.getElementById('pricesSummary');
    if (!container) return;
    
    try {
        const response = await fetch('/api/albania/prices');
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ error: `HTTP ${response.status}` }));
            throw new Error(errorData.error || `HTTP ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Prices API response:', data);
        
        if (data.status === 'success' && data.data) {
            const price = parseFloat(data.data.price_eur_per_kwh);
            const avgPriceEl = document.getElementById('avgPrice');
            if (avgPriceEl) avgPriceEl.textContent = `${price.toFixed(4)} €/kWh`;
            
            container.innerHTML = `
                <div class="price-item">
                    <div><strong>${data.data.source || 'Simulated'}</strong></div>
                    <div class="price-value">${price.toFixed(4)} €/kWh</div>
                </div>
            `;
        } else {
            container.innerHTML = '<p style="color: #f59e0b;">⚠️ Nuk ka të dhëna të disponueshme.</p>';
        }
    } catch (error) {
        console.error('Error loading prices:', error);
        container.innerHTML = `<p style="color: #ef4444;">❌ Gabim: ${error.message || 'Service unavailable'}</p>`;
    }
}

// Load long-term price trends
async function loadPricesLongTermSummary() {
    const container = document.getElementById('pricesLongTermSummary');
    if (!container) return;

    try {
        const response = await fetch('/api/albania/prices/historical');
        const data = await response.json();

        if (data.status !== 'success' || !data.data || !data.data.length) {
            container.innerHTML = '<p>Nuk ka të dhëna historike të disponueshme.</p>';
            return;
        }

        const sorted = [...data.data].sort((a, b) => new Date(a.date) - new Date(b.date));
        const first = sorted[0];
        const last = sorted[sorted.length - 1];

        if (!first || !last) {
            container.innerHTML = '<p>Nuk mund të llogariten trendet afatgjata.</p>';
            return;
        }

        const priceChange = last.price_eur_per_kwh - first.price_eur_per_kwh;
        const priceChangePct = first.price_eur_per_kwh > 0
            ? (priceChange / first.price_eur_per_kwh) * 100
            : 0;

        container.innerHTML = `
            <p>
                Çmimi ka
                <strong>${priceChange >= 0 ? 'rritur' : 'ulur'} me ${Math.abs(priceChangePct).toFixed(1)}%</strong>
                në 14 ditët e fundit.
            </p>
        `;
    } catch (error) {
        console.error('Error loading long-term price trends:', error);
        container.innerHTML = '<p style="color: #ef4444;">Gabim në ngarkimin e trendeve afatgjata.</p>';
    }
}

// Small sparkline chart for prices
async function loadPriceSparkline() {
    const canvas = document.getElementById('priceSparkline');
    if (!canvas) return;

    try {
        const response = await fetch('/api/albania/prices/historical');
        const data = await response.json();

        if (data.status === 'success' && data.data && data.data.length) {
            updatePriceSparklineChart(data.data);
        }
    } catch (error) {
        console.error('Error loading price sparkline:', error);
    }
}

function updatePriceSparklineChart(historyData) {
    const ctx = document.getElementById('priceSparkline');
    if (!ctx) return;

    if (priceSparklineChart) {
        priceSparklineChart.destroy();
    }

    const sorted = [...historyData].sort((a, b) => new Date(a.date) - new Date(b.date));
    const labels = sorted.map(d => d.date);
    const prices = sorted.map(d => d.price_eur_per_kwh);

    priceSparklineChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels,
            datasets: [{
                label: 'Price (€/kWh)',
                data: prices,
                borderColor: 'rgb(37, 99, 235)',
                backgroundColor: 'rgba(37, 99, 235, 0.08)',
                tension: 0.3,
                fill: true,
                pointRadius: 0,
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    ticks: { display: false },
                    grid: { display: false }
                },
                x: {
                    ticks: { display: false },
                    grid: { display: false }
                }
            }
        }
    });
}

// Load consumption summary
async function loadConsumptionSummary() {
    try {
        const response = await fetch('/api/albania/consumption');
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ error: `HTTP ${response.status}` }));
            throw new Error(errorData.error || `HTTP ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Consumption API response:', data);
        
        let consumption = null;
        if (data.status === 'success' && data.data) {
            consumption = data.data;
        }
        
        if (consumption && consumption.total_consumption_mwh) {
            const total = parseFloat(consumption.total_consumption_mwh);
            const totalEl = document.getElementById('totalConsumption');
            if (totalEl) totalEl.textContent = `${total} MWh`;
            
            updateConsumptionChart(consumption);
        } else {
            const totalEl = document.getElementById('totalConsumption');
            if (totalEl) totalEl.textContent = 'N/A';
        }
    } catch (error) {
        console.error('Error loading consumption:', error);
        const totalEl = document.getElementById('totalConsumption');
        if (totalEl) totalEl.textContent = 'Error';
    }
}

// Load long-term consumption trends
async function loadConsumptionLongTermSummary() {
    const container = document.getElementById('consumptionLongTermSummary');
    if (!container) return;

    try {
        const response = await fetch('/api/albania/consumption/yearly?from_year=2010');
        const data = await response.json();

        if (data.status !== 'success' || !data.data || !data.data.length) {
            container.innerHTML = '<p>Nuk ka të dhëna historike të disponueshme.</p>';
            return;
        }

        const sorted = [...data.data].sort((a, b) => a.year - b.year);
        const first = sorted[0];
        const last = sorted[sorted.length - 1];

        const firstVal = first.consumption_mwh || 0;
        const lastVal = last.consumption_mwh || 0;

        if (!firstVal || !lastVal) {
            container.innerHTML = '<p>Nuk mund të llogariten trendet afatgjata të konsumit.</p>';
            return;
        }

        const diffPct = ((lastVal - firstVal) / firstVal) * 100;

        container.innerHTML = `
            <p>
                Që nga <strong>${first.year}</strong> deri në <strong>${last.year}</strong>,
                konsumi total është
                <strong>${diffPct >= 0 ? 'rritur' : 'ulur'} me ${Math.abs(diffPct).toFixed(1)}%</strong>
                (${firstVal.toFixed(1)} → ${lastVal.toFixed(1)} MWh).
            </p>
        `;
    } catch (error) {
        console.error('Error loading long-term consumption trends:', error);
        container.innerHTML = '<p style="color: #ef4444;">Gabim në ngarkimin e trendeve afatgjata të konsumit.</p>';
    }
}

// Update consumption chart
function updateConsumptionChart(consumption) {
    const ctx = document.getElementById('consumptionChart');
    if (!ctx) return;
    
    if (consumptionChart) {
        consumptionChart.destroy();
    }
    
    const regions = consumption.regions || [];
    const labels = regions.map(r => r.region);
    const values = regions.map(r => r.consumption_mwh);
    
    if (labels.length === 0) return;
    
    consumptionChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Konsum (MWh)',
                data: values,
                backgroundColor: [
                    'rgba(102, 126, 234, 0.8)',
                    'rgba(118, 75, 162, 0.8)',
                    'rgba(255, 99, 132, 0.8)',
                    'rgba(54, 162, 235, 0.8)'
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
                        text: 'Konsum (MWh)'
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
    loadPricesLongTermSummary();
    loadPriceSparkline();
}

function refreshConsumption() {
    loadConsumptionSummary();
    loadConsumptionLongTermSummary();
}

// Auto-refresh every 60 seconds
window.addEventListener('load', () => {
    loadAlbaniaDashboard();
    
    refreshInterval = setInterval(() => {
        loadAlbaniaDashboard();
    }, 60000);
});

window.addEventListener('beforeunload', () => {
    if (refreshInterval) {
        clearInterval(refreshInterval);
    }
});
