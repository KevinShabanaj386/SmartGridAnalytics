// Kosovo Prices JavaScript
let pricesChart = null;

async function loadPricesData() {
    try {
        const response = await fetch('/api/kosovo/prices');
        const data = await response.json();
        
        if (data.status === 'success' && data.data && data.data.length > 0) {
            updatePricesChart(data.data);
            updatePricesDetails(data.data);
        } else {
            document.getElementById('pricesDetails').innerHTML = '<p>Nuk ka çmime të disponueshme</p>';
        }
    } catch (error) {
        console.error('Error loading prices:', error);
        document.getElementById('pricesDetails').innerHTML = '<p style="color: #ef4444;">Gabim në ngarkim</p>';
    }
}

function updatePricesChart(pricesData) {
    const ctx = document.getElementById('pricesChart');
    if (!ctx) return;
    
    if (pricesChart) {
        pricesChart.destroy();
    }
    
    // Extract all prices
    const datasets = [];
    const labels = new Set();
    
    pricesData.forEach(source => {
        if (source.prices) {
            Object.entries(source.prices).forEach(([type, priceInfo]) => {
                labels.add(`${source.source} - ${type}`);
            });
        }
    });
    
    const allLabels = Array.from(labels);
    const allPrices = [];
    
    pricesData.forEach(source => {
        if (source.prices) {
            Object.entries(source.prices).forEach(([type, priceInfo]) => {
                const label = `${source.source} - ${type}`;
                const index = allLabels.indexOf(label);
                if (index !== -1) {
                    allPrices[index] = priceInfo.price_eur_per_kwh;
                }
            });
        }
    });
    
    pricesChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: allLabels,
            datasets: [{
                label: 'Çmimi (€/kWh)',
                data: allPrices,
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

function updatePricesDetails(pricesData) {
    const container = document.getElementById('pricesDetails');
    
    let html = '';
    pricesData.forEach(source => {
        if (source.prices && Object.keys(source.prices).length > 0) {
            html += `<div style="margin-bottom: 20px;">
                <h4 style="color: var(--neon-cyan); margin-bottom: 10px;">${source.source}</h4>`;
            
            Object.entries(source.prices).forEach(([type, priceInfo]) => {
                html += `
                    <div class="price-item">
                        <div><strong>${type.charAt(0).toUpperCase() + type.slice(1)}</strong></div>
                        <div class="price-value">${priceInfo.price_eur_per_kwh.toFixed(4)} €/kWh</div>
                        ${priceInfo.extracted_from ? `<small style="color: #6b7280;">${priceInfo.extracted_from.substring(0, 50)}...</small>` : ''}
                    </div>
                `;
            });
            
            html += `<small style="color: #6b7280; display: block; margin-top: 10px;">
                🕐 ${new Date(source.scraped_at).toLocaleString('sq-AL')}
            </small></div>`;
        }
    });
    
    if (!html) {
        html = '<p>Nuk ka çmime të disponueshme</p>';
    }
    
    container.innerHTML = html;
}

function refreshData() {
    loadPricesData();
}

window.addEventListener('load', () => {
    loadPricesData();
    setInterval(loadPricesData, 300000); // Refresh every 5 minutes
});
