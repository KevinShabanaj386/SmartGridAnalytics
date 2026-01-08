// Serbia Weather Data JavaScript
let temperatureChart = null;
let windChart = null;

async function loadWeatherData() {
    try {
        const response = await fetch('/api/serbia/weather');
        const data = await response.json();
        
        if (data.status === 'success' && data.data && data.data.length > 0) {
            updateTemperatureChart(data.data);
            updateWindChart(data.data);
            updateCitiesDetails(data.data);
        } else {
            document.getElementById('citiesDetails').innerHTML = '<p>Nuk ka të dhëna të disponueshme</p>';
        }
    } catch (error) {
        console.error('Error loading weather:', error);
    }
}

function updateTemperatureChart(weatherData) {
    const ctx = document.getElementById('temperatureChart');
    if (!ctx) return;
    
    if (temperatureChart) {
        temperatureChart.destroy();
    }
    
    const cities = weatherData.map(w => w.city);
    const temps = weatherData.map(w => w.temperature);
    
    temperatureChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: cities,
            datasets: [{
                label: 'Temperatura',
                data: temps,
                backgroundColor: 'rgba(102, 126, 234, 0.8)',
                borderColor: 'rgb(102, 126, 234)',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    title: {
                        display: true,
                        text: 'Temperatura (°C)'
                    }
                }
            }
        }
    });
}

function updateWindChart(weatherData) {
    const ctx = document.getElementById('windChart');
    if (!ctx) return;
    
    if (windChart) {
        windChart.destroy();
    }
    
    const cities = weatherData.map(w => w.city);
    const windSpeeds = weatherData.map(w => w.wind_speed || 0);
    
    windChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: cities,
            datasets: [{
                label: 'Shpejtësia e Erës (km/h)',
                data: windSpeeds,
                borderColor: 'rgb(54, 162, 235)',
                backgroundColor: 'rgba(54, 162, 235, 0.1)',
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
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Shpejtësia (km/h)'
                    }
                }
            }
        }
    });
}

function updateCitiesDetails(weatherData) {
    const container = document.getElementById('citiesDetails');
    
    container.innerHTML = weatherData.map(w => `
        <div class="city-weather-item" style="margin-bottom: 15px;">
            <div>
                <strong style="font-size: 1.1rem;">${w.city}</strong>
                <span class="source-badge">${w.country || 'Serbia'}</span>
                <div style="margin-top: 8px; font-size: 0.9rem; color: #6b7280;">
                    <div>🌡️ ${w.temperature}°C</div>
                    <div>💧 Lagështia: ${w.humidity}%</div>
                    <div>🌬️ Erë: ${w.wind_speed || 0} km/h</div>
                    <div>☁️ ${w.description || 'N/A'}</div>
                    <div style="margin-top: 5px; font-size: 0.8rem;">🕐 ${new Date(w.timestamp).toLocaleString('sq-AL')}</div>
                </div>
            </div>
        </div>
    `).join('');
}

function refreshData() {
    loadWeatherData();
}

window.addEventListener('load', () => {
    loadWeatherData();
    setInterval(loadWeatherData, 60000);
});
