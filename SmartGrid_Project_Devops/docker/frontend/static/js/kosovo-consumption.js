// Kosovo Consumption JavaScript
let consumptionChart = null;
let historicalChart = null;

async function loadConsumptionData() {
    try {
        const response = await fetch('/api/kosovo/consumption');
        const data = await response.json();
        
        if (data.status === 'success' && data.data) {
            updateConsumptionChart(data.data);
            updateRegionsDetails(data.data);
        } else {
            document.getElementById('regionsDetails').innerHTML = '<p>Nuk ka të dhëna të disponueshme</p>';
        }
    } catch (error) {
        console.error('Error loading consumption:', error);
    }
}

async function loadHistoricalData() {
    try {
        const hours = document.getElementById('hoursInput').value || 24;
        const response = await fetch(`/api/kosovo/consumption/historical?hours=${hours}`);
        const data = await response.json();
        
        if (data.status === 'success' && data.data && data.data.length > 0) {
            updateHistoricalChart(data.data);
        }
    } catch (error) {
        console.error('Error loading historical:', error);
    }
}

function updateConsumptionChart(consumption) {
    const ctx = document.getElementById('consumptionChart');
    if (!ctx) return;
    
    if (consumptionChart) {
        consumptionChart.destroy();
    }
    
    const regions = consumption.regions || {};
    const labels = Object.keys(regions).map(k => regions[k].name);
    const values = Object.keys(regions).map(k => regions[k].consumption_mw);
    const total = consumption.total_consumption_mw || 0;
    
    if (labels.length === 0) return;
    
    // Add total to chart
    const allLabels = ['Total', ...labels];
    const allValues = [total, ...values];
    
    consumptionChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: allLabels,
            datasets: [{
                label: 'Konsum (MW)',
                data: allValues,
                backgroundColor: [
                    'rgba(0, 255, 136, 0.8)', // Total - green
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

function updateHistoricalChart(historicalData) {
    const ctx = document.getElementById('historicalChart');
    if (!ctx) return;
    
    if (historicalChart) {
        historicalChart.destroy();
    }
    
    // Reverse to show oldest first
    const reversed = [...historicalData].reverse();
    const labels = reversed.map(d => new Date(d.timestamp || d.scraped_at).toLocaleString('sq-AL'));
    const values = reversed.map(d => d.total_consumption_mw || 0);
    
    historicalChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Konsum Total (MW)',
                data: values,
                borderColor: 'rgb(0, 255, 136)',
                backgroundColor: 'rgba(0, 255, 136, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    title: {
                        display: true,
                        text: 'Konsum (MW)'
                    }
                },
                x: {
                    ticks: {
                        maxRotation: 45,
                        minRotation: 45
                    }
                }
            }
        }
    });
}

function updateRegionsDetails(consumption) {
    const container = document.getElementById('regionsDetails');
    const regions = consumption.regions || {};
    
    if (Object.keys(regions).length === 0) {
        container.innerHTML = '<p>Nuk ka të dhëna rajonale</p>';
        return;
    }
    
    container.innerHTML = Object.entries(regions).map(([key, region]) => `
        <div class="region-consumption">
            <div>
                <div class="region-name">${region.name}</div>
                <small style="color: #6b7280;">${region.region}</small>
            </div>
            <div style="text-align: right;">
                <div class="consumption-value">${region.consumption_mw} MW</div>
                <small style="color: #6b7280;">Popullata: ~${region.estimated_population?.toLocaleString() || 'N/A'}</small>
            </div>
        </div>
    `).join('');
    
    // Add total
    if (consumption.total_consumption_mw) {
        container.innerHTML = `
            <div class="region-consumption" style="background: rgba(0, 255, 136, 0.1); border-left: 3px solid var(--neon-green); margin-bottom: 15px;">
                <div>
                    <div class="region-name" style="font-size: 1.2rem;">Total për Kosovën</div>
                </div>
                <div style="text-align: right;">
                    <div class="consumption-value" style="font-size: 1.5rem;">${consumption.total_consumption_mw} MW</div>
                    ${consumption.peak_period ? '<small style="color: #f59e0b;">⏰ Peak Period</small>' : ''}
                </div>
            </div>
        ` + container.innerHTML;
    }
}

function refreshData() {
    loadConsumptionData();
}

function loadHistorical() {
    loadHistoricalData();
}

window.addEventListener('load', () => {
    loadConsumptionData();
    loadHistoricalData();
    setInterval(loadConsumptionData, 60000); // Refresh every minute
});
