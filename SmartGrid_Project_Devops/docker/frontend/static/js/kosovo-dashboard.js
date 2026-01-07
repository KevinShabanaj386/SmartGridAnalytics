// Kosovo Dashboard JavaScript
let consumptionChart = null;
let priceSparklineChart = null;
let refreshInterval = null;

// Load all Kosovo data
async function loadKosovoDashboard() {
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
            statusMsg.textContent = `${servicesDown} shërbim(e) nuk janë të disponueshme. Kontrolloni që Kosovo collectors janë running.`;
        } else if (statusEl) {
            statusEl.style.display = 'none';
        }
    } catch (error) {
        console.error('Error loading Kosovo dashboard:', error);
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
        const response = await fetch('/api/kosovo/weather');
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ error: `HTTP ${response.status}` }));
            throw new Error(errorData.error || `HTTP ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Weather API response:', data);
        
        // Handle different response formats
        let weatherData = [];
        if (data.status === 'success' && data.data) {
            weatherData = Array.isArray(data.data) ? data.data : [data.data];
        } else if (Array.isArray(data)) {
            weatherData = data;
        } else if (data.cities_collected && data.data) {
            weatherData = Array.isArray(data.data) ? data.data : [data.data];
        }
        
        if (weatherData.length > 0) {
            // Calculate average temperature
            const avgTemp = weatherData.reduce((sum, w) => sum + (parseFloat(w.temperature) || 0), 0) / weatherData.length;
            const avgTempEl = document.getElementById('avgTemperature');
            const citiesCountEl = document.getElementById('citiesCount');
            
            if (avgTempEl) avgTempEl.textContent = `${avgTemp.toFixed(1)}°C`;
            if (citiesCountEl) citiesCountEl.textContent = weatherData.length;
            
            // Display summary
            container.innerHTML = weatherData.slice(0, 3).map(w => `
                <div class="city-weather-item">
                    <div>
                        <strong>${w.city_name || w.city || 'Unknown'}</strong>
                        <span class="source-badge">${w.data_source || 'API'}</span>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 1.2rem; font-weight: bold;">${w.temperature || 'N/A'}°C</div>
                        <small>${w.weather_condition || 'N/A'}</small>
                    </div>
                </div>
            `).join('');
        } else {
            container.innerHTML = '<p style="color: #f59e0b;">⚠️ Nuk ka të dhëna të disponueshme. Shërbimi mund të mos jetë aktiv.</p>';
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
        const response = await fetch('/api/kosovo/prices');
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ error: `HTTP ${response.status}` }));
            throw new Error(errorData.error || `HTTP ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Prices API response:', data);
        
        // Handle different response formats
        let sources = [];
        if (data.status === 'success' && data.data) {
            sources = Array.isArray(data.data) ? data.data : [data.data];
        } else if (Array.isArray(data)) {
            sources = data;
        } else if (data.sources_collected && data.data) {
            sources = Array.isArray(data.data) ? data.data : [data.data];
        }
        
        if (sources.length > 0) {
            let allPrices = [];
            
            sources.forEach(source => {
                if (source.prices && typeof source.prices === 'object') {
                    Object.entries(source.prices).forEach(([type, priceInfo]) => {
                        if (priceInfo && priceInfo.price_eur_per_kwh) {
                            allPrices.push({
                                source: source.source || 'Unknown',
                                type: type,
                                price: parseFloat(priceInfo.price_eur_per_kwh)
                            });
                        }
                    });
                }
            });
            
            if (allPrices.length > 0) {
                const avgPrice = allPrices.reduce((sum, p) => sum + p.price, 0) / allPrices.length;
                const avgPriceEl = document.getElementById('avgPrice');
                if (avgPriceEl) avgPriceEl.textContent = `${avgPrice.toFixed(4)} €/kWh`;
                
                container.innerHTML = allPrices.slice(0, 3).map(p => `
                    <div class="price-item">
                        <div><strong>${p.source}</strong> - ${p.type}</div>
                        <div class="price-value">${p.price.toFixed(4)} €/kWh</div>
                    </div>
                `).join('');
            } else {
                container.innerHTML = '<p style="color: #f59e0b;">⚠️ Nuk ka çmime të disponueshme. Shërbimi mund të mos jetë aktiv.</p>';
            }
        } else {
            container.innerHTML = '<p style="color: #f59e0b;">⚠️ Nuk ka të dhëna të disponueshme. Shërbimi mund të mos jetë aktiv.</p>';
        }
    } catch (error) {
        console.error('Error loading prices:', error);
        container.innerHTML = `<p style=\"color: #ef4444;\">❌ Gabim: ${error.message || 'Service unavailable'}</p>`;
    }
}

// Load long-term price trends (2010–sot)
async function loadPricesLongTermSummary() {
    const container = document.getElementById('pricesLongTermSummary');
    if (!container) return;

    try {
        const response = await fetch('/api/kosovo/prices/historical?from_year=2010');
        const data = await response.json();

        if (data.status !== 'success' || !data.data || !data.data.length) {
            container.innerHTML = '<p>Nuk ka të dhëna historike të disponueshme.</p>';
            return;
        }

        const sorted = [...data.data].sort((a, b) => a.year - b.year);
        const first = sorted[0];
        const last = sorted[sorted.length - 1];

        if (!first || !last || !first.import_price_eur_per_mwh || !last.import_price_eur_per_mwh) {
            container.innerHTML = '<p>Nuk mund të llogariten trendet afatgjata.</p>';
            return;
        }

        const importChangeAbs = last.import_price_eur_per_mwh - first.import_price_eur_per_mwh;
        const importChangePct = first.import_price_eur_per_mwh > 0
            ? (importChangeAbs / first.import_price_eur_per_mwh) * 100
            : 0;
        const importShareChange = (last.import_share_percent || 0) - (first.import_share_percent || 0);

        container.innerHTML = `
            <p>
                Që nga <strong>${first.year}</strong> deri në <strong>${last.year}</strong>,
                çmimi mesatar i importit është
                <strong>${importChangeAbs >= 0 ? 'rritur' : 'ulur'} me ${Math.abs(importChangePct).toFixed(1)}%</strong>.
            </p>
            <p>
                Pjesëmarrja e importit në furnizim ka ndryshuar me
                <strong>${importShareChange >= 0 ? '+' : ''}${importShareChange.toFixed(1)} pp</strong>.
            </p>
        `;
    } catch (error) {
        console.error('Error loading long-term price trends:', error);
        container.innerHTML = '<p style="color: #ef4444;">Gabim në ngarkimin e trendeve afatgjata.</p>';
    }
}

// Small sparkline chart for import prices (last years)
async function loadPriceSparkline() {
    const canvas = document.getElementById('priceSparkline');
    if (!canvas) return;

    try {
        const response = await fetch('/api/kosovo/prices/historical?from_year=2015');
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

    const sorted = [...historyData].sort((a, b) => a.year - b.year);
    const labels = sorted.map(d => d.year);
    const importPrices = sorted.map(d => d.import_price_eur_per_mwh);

    priceSparklineChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels,
            datasets: [{
                label: 'Import (€/MWh)',
                data: importPrices,
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
        const response = await fetch('/api/kosovo/consumption');
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ error: `HTTP ${response.status}` }));
            throw new Error(errorData.error || `HTTP ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Consumption API response:', data);
        
        // Handle different response formats
        let consumption = null;
        if (data.status === 'success' && data.data) {
            consumption = data.data;
        } else if (data.total_consumption_mw) {
            consumption = data;
        }
        
        if (consumption && consumption.total_consumption_mw) {
            const total = parseFloat(consumption.total_consumption_mw);
            const totalEl = document.getElementById('totalConsumption');
            if (totalEl) totalEl.textContent = `${total} MW`;
            
            // Update chart
            updateConsumptionChart(consumption);
        } else {
            const totalEl = document.getElementById('totalConsumption');
            if (totalEl) totalEl.textContent = 'N/A';
            console.warn('No consumption data available');
        }
    } catch (error) {
        console.error('Error loading consumption:', error);
        const totalEl = document.getElementById('totalConsumption');
        if (totalEl) totalEl.textContent = 'Error';
    }
}

// Load long-term consumption trends (2010–sot)
async function loadConsumptionLongTermSummary() {
    const container = document.getElementById('consumptionLongTermSummary');
    if (!container) return;

    try {
        const response = await fetch('/api/kosovo/consumption/yearly?from_year=2010');
        const data = await response.json();

        if (data.status !== 'success' || !data.data || !data.data.length) {
            container.innerHTML = '<p>Nuk ka të dhëna historike të disponueshme.</p>';
            return;
        }

        const sorted = [...data.data].sort((a, b) => a.year - b.year);
        const first = sorted[0];
        const last = sorted[sorted.length - 1];

        const firstVal = first.total_consumption_gwh || first.total_consumption_mw || 0;
        const lastVal = last.total_consumption_gwh || last.total_consumption_mw || 0;

        if (!firstVal || !lastVal) {
            container.innerHTML = '<p>Nuk mund të llogariten trendet afatgjata të konsumit.</p>';
            return;
        }

        const diffPct = ((lastVal - firstVal) / firstVal) * 100;
        const importShareChange = (last.import_share_percent || 0) - (first.import_share_percent || 0);
        const unit = first.total_consumption_gwh ? 'GWh' : 'MW';

        container.innerHTML = `
            <p>
                Që nga <strong>${first.year}</strong> deri në <strong>${last.year}</strong>,
                konsumi total është
                <strong>${diffPct >= 0 ? 'rritur' : 'ulur'} me ${Math.abs(diffPct).toFixed(1)}%</strong>
                (${firstVal.toFixed(1)} → ${lastVal.toFixed(1)} ${unit}).
            </p>
            <p>
                Pjesëmarrja e importit në konsum ka ndryshuar me
                <strong>${importShareChange >= 0 ? '+' : ''}${importShareChange.toFixed(1)} pp</strong>.
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
    loadPricesLongTermSummary();
    loadPriceSparkline();
}

function refreshConsumption() {
    loadConsumptionSummary();
    loadConsumptionLongTermSummary();
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
