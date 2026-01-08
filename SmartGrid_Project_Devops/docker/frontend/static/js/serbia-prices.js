// Serbia Prices JavaScript
let pricesChart = null;
let pricesHistoryChart = null;

async function loadPricesData() {
    try {
        const response = await fetch('/api/serbia/prices');
        const data = await response.json();
        
        if (data.status === 'success' && data.data) {
            updatePricesChart([data.data]);
            updatePricesDetails([data.data]);
        } else {
            document.getElementById('pricesDetails').innerHTML = '<p>Nuk ka çmime të disponueshme</p>';
        }
    } catch (error) {
        console.error('Error loading prices:', error);
        document.getElementById('pricesDetails').innerHTML = '<p style="color: #ef4444;">Gabim në ngarkim</p>';
    }
}

async function loadPricesHistory() {
    try {
        const response = await fetch('/api/serbia/prices/historical');
        const data = await response.json();
        
        if (data.status === 'success' && data.data && data.data.length > 0) {
            updatePricesHistoryChart(data.data);
            updatePricesTrendSummary(data.data);
        } else {
            const summary = document.getElementById('pricesTrendSummary');
            if (summary) {
                summary.innerHTML = '<p>Nuk ka të dhëna historike të disponueshme</p>';
            }
        }
    } catch (error) {
        console.error('Error loading price history:', error);
        const summary = document.getElementById('pricesTrendSummary');
        if (summary) {
            summary.innerHTML = '<p style="color: #ef4444;">Gabim në ngarkim të trendit historik</p>';
        }
    }
}

function updatePricesChart(pricesData) {
    const ctx = document.getElementById('pricesChart');
    if (!ctx) return;
    
    if (pricesChart) {
        pricesChart.destroy();
    }
    
    const price = pricesData[0]?.price_eur_per_kwh || 0;
    
    pricesChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Çmim Aktual'],
            datasets: [{
                label: 'Çmimi (€/kWh)',
                data: [price],
                backgroundColor: 'rgba(0, 255, 136, 0.8)',
                borderColor: 'rgb(0, 255, 136)',
                borderWidth: 2
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
                        text: 'Çmimi (€/kWh)'
                    }
                }
            }
        }
    });
}

function updatePricesHistoryChart(historyData) {
    const ctx = document.getElementById('pricesTrendChart');
    if (!ctx) return;

    if (pricesHistoryChart) {
        pricesHistoryChart.destroy();
    }

    const sorted = [...historyData].sort((a, b) => new Date(a.date) - new Date(b.date));
    const labels = sorted.map(d => d.date);
    const prices = sorted.map(d => d.price_eur_per_kwh);

    pricesHistoryChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels,
            datasets: [{
                label: 'Çmimi (€/kWh)',
                data: prices,
                borderColor: 'rgb(239, 68, 68)',
                backgroundColor: 'rgba(239, 68, 68, 0.1)',
                tension: 0.3,
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
                        text: 'Çmimi (€/kWh)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Data'
                    }
                }
            }
        }
    });
}

function updatePricesDetails(pricesData) {
    const container = document.getElementById('pricesDetails');
    
    const price = pricesData[0]?.price_eur_per_kwh || 0;
    const source = pricesData[0]?.source || 'Simulated';
    
    container.innerHTML = `
        <div class="price-item">
            <div><strong>${source}</strong></div>
            <div class="price-value">${price.toFixed(4)} €/kWh</div>
            <small style="color: #6b7280;">🕐 ${new Date(pricesData[0]?.timestamp || Date.now()).toLocaleString('sq-AL')}</small>
        </div>
    `;
}

function updatePricesTrendSummary(historyData) {
    const summary = document.getElementById('pricesTrendSummary');
    if (!summary || !historyData || historyData.length === 0) return;

    const sorted = [...historyData].sort((a, b) => new Date(a.date) - new Date(b.date));
    const first = sorted[0];
    const last = sorted[sorted.length - 1];

    if (!first || !last) {
        return;
    }

    const priceChange = last.price_eur_per_kwh - first.price_eur_per_kwh;
    const priceChangePct = first.price_eur_per_kwh > 0
        ? (priceChange / first.price_eur_per_kwh) * 100
        : 0;

    summary.innerHTML = `
        <p>
            Në 14 ditët e fundit, çmimi ka
            <strong>${priceChange >= 0 ? 'rritur' : 'ulur'} me ${Math.abs(priceChangePct).toFixed(1)}%</strong>.
        </p>
    `;
}

function refreshData() {
    loadPricesData();
    loadPricesHistory();
}

window.addEventListener('load', () => {
    loadPricesData();
    loadPricesHistory();
    setInterval(loadPricesData, 300000);
});
