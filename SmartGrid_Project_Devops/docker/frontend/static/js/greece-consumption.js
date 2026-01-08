// Greece Consumption JavaScript
let consumptionChart = null;
let historicalChart = null;

async function loadConsumptionData() {
    try {
        const response = await fetch('/api/greece/consumption');
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
        const response = await fetch(`/api/greece/consumption/historical?hours=${hours}`);
        const data = await response.json();
        
        if (data.status === 'success' && data.data && data.data.length > 0) {
            updateHistoricalChart(data.data);
        }
    } catch (error) {
        console.error('Error loading historical:', error);
    }
}

async function loadYearlyHistory() {
    try {
        const response = await fetch('/api/greece/consumption/yearly?from_year=2010');
        const data = await response.json();

        if (data.status === 'success' && data.data && data.data.length > 0) {
            updateHistoricalChart(data.data.map(d => ({
                timestamp: `${d.year}-01-01T00:00:00`,
                total_consumption_mw: d.consumption_mwh / 1000
            })));
            updateConsumptionTrendSummary(data.data);
        }
    } catch (error) {
        console.error('Error loading yearly consumption history:', error);
    }
}

function updateConsumptionChart(consumption) {
    const ctx = document.getElementById('consumptionChart');
    if (!ctx) return;
    
    if (consumptionChart) {
        consumptionChart.destroy();
    }
    
    const regions = consumption.regions || [];
    const labels = regions.map(r => r.region);
    const values = regions.map(r => r.consumption_mwh);
    const total = consumption.total_consumption_mwh || 0;
    
    if (labels.length === 0) return;
    
    const allLabels = ['Total', ...labels];
    const allValues = [total, ...values];
    
    consumptionChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: allLabels,
            datasets: [{
                label: 'Konsum (MWh)',
                data: allValues,
                backgroundColor: [
                    'rgba(0, 255, 136, 0.8)',
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

function updateHistoricalChart(historicalData) {
    const ctx = document.getElementById('historicalChart');
    if (!ctx) return;
    
    if (historicalChart) {
        historicalChart.destroy();
    }
    
    const reversed = [...historicalData].reverse();
    const labels = reversed.map(d => new Date(d.timestamp).toLocaleString('sq-AL'));
    const values = reversed.map(d => d.total_consumption_mw || d.consumption_mwh || 0);
    
    historicalChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Konsum Total (MWh)',
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
                        text: 'Konsum (MWh)'
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

function updateConsumptionTrendSummary(historyData) {
    const summary = document.getElementById('consumptionTrendSummary');
    if (!summary || !historyData || historyData.length === 0) return;

    const sorted = [...historyData].sort((a, b) => a.year - b.year);
    const first = sorted[0];
    const last = sorted[sorted.length - 1];

    const firstVal = first.consumption_mwh || 0;
    const lastVal = last.consumption_mwh || 0;

    if (!firstVal || !lastVal) {
        return;
    }

    const diffPct = ((lastVal - firstVal) / firstVal) * 100;

    summary.innerHTML = `
        <p>
            Që nga viti <strong>${first.year}</strong> deri në <strong>${last.year}</strong>,
            konsumi total është
            <strong>${diffPct >= 0 ? 'rritur' : 'ulur'} me ${Math.abs(diffPct).toFixed(1)}%</strong>
            (${firstVal.toFixed(1)} → ${lastVal.toFixed(1)} MWh).
        </p>
    `;
}

function updateRegionsDetails(consumption) {
    const container = document.getElementById('regionsDetails');
    const regions = consumption.regions || [];
    
    if (regions.length === 0) {
        container.innerHTML = '<p>Nuk ka të dhëna rajonale</p>';
        return;
    }
    
    container.innerHTML = regions.map(region => `
        <div class="region-consumption">
            <div>
                <div class="region-name">${region.region}</div>
            </div>
            <div style="text-align: right;">
                <div class="consumption-value">${region.consumption_mwh} MWh</div>
            </div>
        </div>
    `).join('');
    
    if (consumption.total_consumption_mwh) {
        container.innerHTML = `
            <div class="region-consumption" style="background: rgba(0, 255, 136, 0.1); border-left: 3px solid var(--neon-green); margin-bottom: 15px;">
                <div>
                    <div class="region-name" style="font-size: 1.2rem;">Total për Greqinë</div>
                </div>
                <div style="text-align: right;">
                    <div class="consumption-value" style="font-size: 1.5rem;">${consumption.total_consumption_mwh} MWh</div>
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
    setInterval(loadConsumptionData, 60000);
});
