// Kosovo Prices JavaScript
let pricesChart = null;
let pricesHistoryChart = null;

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

async function loadPricesHistory() {
    try {
        const response = await fetch('/api/kosovo/prices/historical?from_year=2010');
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

function updatePricesHistoryChart(historyData) {
    const ctx = document.getElementById('pricesTrendChart');
    if (!ctx) return;

    if (pricesHistoryChart) {
        pricesHistoryChart.destroy();
    }

    const sorted = [...historyData].sort((a, b) => a.year - b.year);
    const labels = sorted.map(d => d.year);
    const importPrices = sorted.map(d => d.import_price_eur_per_mwh);
    const domesticPrices = sorted.map(d => d.domestic_price_eur_per_mwh);

    pricesHistoryChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels,
            datasets: [
                {
                    label: 'Import (€/MWh)',
                    data: importPrices,
                    borderColor: 'rgb(239, 68, 68)',
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    tension: 0.3,
                    fill: true
                },
                {
                    label: 'Vendor i brendshëm (€/MWh)',
                    data: domesticPrices,
                    borderColor: 'rgb(59, 130, 246)',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    tension: 0.3,
                    fill: true
                }
            ]
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
                        text: 'Çmimi (€/MWh)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Viti'
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

            if (typeof source.import_price_eur_per_mwh === 'number' && typeof source.domestic_price_eur_per_mwh === 'number') {
                const share = typeof source.import_share_percent === 'number' ? source.import_share_percent.toFixed(1) : 'N/A';
                const ch24 = typeof source.change_24h_percent === 'number' ? source.change_24h_percent.toFixed(1) : '0.0';
                const ch7d = typeof source.change_7d_percent === 'number' ? source.change_7d_percent.toFixed(1) : '0.0';
                html += `
                    <div class="price-item" style="margin-bottom: 8px;">
                        <div><strong>Import:</strong> ${source.import_price_eur_per_mwh.toFixed(2)} €/MWh</div>
                        <div><strong>Vendor i brendshëm:</strong> ${source.domestic_price_eur_per_mwh.toFixed(2)} €/MWh</div>
                        <small style="color: #6b7280;">Pjesëmarrja e importit: ${share}% | 24h: ${ch24}% | 7 ditë: ${ch7d}%</small>
                    </div>
                `;
            }
            
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

function updatePricesTrendSummary(historyData) {
    const summary = document.getElementById('pricesTrendSummary');
    if (!summary || !historyData || historyData.length === 0) return;

    const sorted = [...historyData].sort((a, b) => a.year - b.year);
    const first = sorted[0];
    const last = sorted[sorted.length - 1];

    if (!first || !last || !first.import_price_eur_per_mwh || !last.import_price_eur_per_mwh) {
        return;
    }

    const importChangeAbs = last.import_price_eur_per_mwh - first.import_price_eur_per_mwh;
    const importChangePct = first.import_price_eur_per_mwh > 0
        ? (importChangeAbs / first.import_price_eur_per_mwh) * 100
        : 0;

    const importShareChange = (last.import_share_percent || 0) - (first.import_share_percent || 0);

    summary.innerHTML = `
        <p>
            Që nga viti <strong>${first.year}</strong> deri në <strong>${last.year}</strong>,
            çmimi mesatar i importit është
            <strong>${importChangeAbs >= 0 ? 'rritur' : 'ulur'} me ${Math.abs(importChangePct).toFixed(1)}%</strong>.
        </p>
        <p>
            Pjesëmarrja e importit në furnizim ka ndryshuar me
            <strong>${importShareChange >= 0 ? '+' : ''}${importShareChange.toFixed(1)} pikë përqindje</strong>,
            duke sinjalizuar ${importShareChange >= 0 ? 'varësi më të lartë nga importi' : 'varësi më të ulët nga importi'}.
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
    setInterval(loadPricesData, 300000); // Refresh every 5 minutes
});
