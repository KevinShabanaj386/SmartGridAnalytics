// Main Dashboard JavaScript - Simple & Clean
let authToken = null;
let forecastChart = null;
let sensorStatsChart = null;
let realtimeChart = null;
let refreshInterval = null;

// Global logout helper so we can clear tokens easily
function logout() {
    try { localStorage.removeItem('authToken'); } catch (e) {}
    try { sessionStorage.removeItem('authToken'); } catch (e) {}
    authToken = null;
    if (refreshInterval) {
        clearInterval(refreshInterval);
        refreshInterval = null;
    }
    window.location.href = '/';
}

// Make logout available globally
window.logout = logout;

// Check for saved token - run on page load to ensure DOM is ready
function checkAuthOnLoad() {
    const savedToken = localStorage.getItem('authToken') || sessionStorage.getItem('authToken');
    if (savedToken) {
        authToken = savedToken;
        const loginSection = document.getElementById('loginSection');
        const dashboardContent = document.getElementById('dashboardContent');
        if (loginSection) loginSection.classList.add('hidden');
        if (dashboardContent) dashboardContent.classList.remove('hidden');
        loadDashboard();
    } else {
        // No token - show login form
        const loginSection = document.getElementById('loginSection');
        const dashboardContent = document.getElementById('dashboardContent');
        if (loginSection) loginSection.classList.remove('hidden');
        if (dashboardContent) dashboardContent.classList.add('hidden');
    }
}

// Run check when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', checkAuthOnLoad);
} else {
    checkAuthOnLoad();
}

// Login form handler
document.getElementById('loginForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    
    const submitBtn = e.target.querySelector('button[type="submit"]');
    submitBtn.disabled = true;
    submitBtn.textContent = 'Duke hyrë...';
    
    try {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({username, password}),
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (data.success) {
            authToken = data.token;
            localStorage.setItem('authToken', authToken);
            sessionStorage.setItem('authToken', authToken);
            const loginSection = document.getElementById('loginSection');
            const dashboardContent = document.getElementById('dashboardContent');
            const userInfo = document.getElementById('userInfo');
            if (loginSection) loginSection.classList.add('hidden');
            if (dashboardContent) dashboardContent.classList.remove('hidden');
            if (userInfo) userInfo.textContent = `👤 ${data.user.username}`;
            loadDashboard();
        } else {
            showAlert('loginAlert', data.error || 'Login failed', 'danger');
        }
    } catch (error) {
        showAlert('loginAlert', 'Error: ' + error.message, 'danger');
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Hyr';
    }
});

// Load dashboard data
async function loadDashboard() {
    // Always refresh token before loading
    authToken = localStorage.getItem('authToken') || sessionStorage.getItem('authToken');
    if (!authToken) {
        console.warn('No auth token found');
        return;
    }
    
    try {
        await Promise.all([
            loadStats(),
            loadForecast(24),
            loadSensorStats(),
            loadAnomalies(),
            loadRecentData(10),
            loadRealtimeData()
        ]);
    } catch (error) {
        console.error('Error loading dashboard:', error);
    }
    
    // Auto-refresh every 10 seconds for real-time updates
    if (refreshInterval) clearInterval(refreshInterval);
    refreshInterval = setInterval(() => {
        loadDashboard();
    }, 10000);
}

// Load statistics
async function loadStats() {
    // Always refresh token before API call
    authToken = localStorage.getItem('authToken') || sessionStorage.getItem('authToken');
    if (!authToken) {
        console.warn('No auth token found');
        return;
    }
    
    try {
        // Refresh token again right before the call
        authToken = localStorage.getItem('authToken') || sessionStorage.getItem('authToken');
        const response = await fetch('/api/sensor-stats?hours=24', {
            headers: {'Authorization': `Bearer ${authToken}`}
        });
        
        // Check for auth errors
        if (response.status === 401) {
            console.error('❌ Authentication failed (401) - token may be expired');
            showAuthError('Session ka skaduar. Ju lutem hyni përsëri.');
            return;
        }
        
        if (!response.ok) {
            console.error(`❌ API error: ${response.status}`);
            return;
        }
        
        const data = await response.json();
        
        if (data.status === 'success' && data.data) {
            const stats = data.data;
            const totalSensors = new Set(stats.map(s => s.sensor_id)).size;
            const avgValue = stats.reduce((sum, s) => sum + parseFloat(s.avg_value || 0), 0) / stats.length;
            const totalReadings = stats.reduce((sum, s) => sum + parseInt(s.count || 0), 0);
            
            document.getElementById('activeSensors').textContent = totalSensors;
            document.getElementById('avgValue').textContent = avgValue.toFixed(2);
            document.getElementById('totalReadings').textContent = totalReadings.toLocaleString();
        } else if (data.error) {
            console.error('❌ API returned error:', data.error);
        }
    } catch (error) {
        console.error('❌ Error loading stats:', error);
    }
}

// Load forecast
async function loadForecast(hours = 24) {
    // Always refresh token before API call
    authToken = localStorage.getItem('authToken') || sessionStorage.getItem('authToken');
    if (!authToken) {
        console.warn('No auth token found');
        return;
    }
    
    try {
        // Refresh token again right before the call
        authToken = localStorage.getItem('authToken') || sessionStorage.getItem('authToken');
        const response = await fetch(`/api/load-forecast?hours_ahead=${hours}&use_ml=true`, {
            headers: {'Authorization': `Bearer ${authToken}`}
        });
        const data = await response.json();
        
        if (data.status === 'success' && data.forecast) {
            updateForecastChart(data.forecast);
        }
    } catch (error) {
        console.error('Error loading forecast:', error);
    }
}

// Update forecast chart
function updateForecastChart(forecast) {
    const ctx = document.getElementById('forecastChart');
    if (!ctx) return;
    
    if (forecastChart) forecastChart.destroy();
    
    forecastChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: forecast.map(f => new Date(f.timestamp).toLocaleTimeString()),
            datasets: [{
                label: 'Parashikim Ngarkese (kW)',
                data: forecast.map(f => f.predicted_load),
                borderColor: '#2563eb',
                backgroundColor: 'rgba(37, 99, 235, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: true }
            },
            scales: {
                y: { beginAtZero: true }
            }
        }
    });
}

// Load sensor stats
async function loadSensorStats() {
    // Always refresh token before API call
    authToken = localStorage.getItem('authToken') || sessionStorage.getItem('authToken');
    if (!authToken) {
        console.warn('No auth token found');
        return;
    }
    
    try {
        // Refresh token again right before the call
        authToken = localStorage.getItem('authToken') || sessionStorage.getItem('authToken');
        const response = await fetch('/api/sensor-stats?hours=24', {
            headers: {'Authorization': `Bearer ${authToken}`}
        });
        const data = await response.json();
        
        if (data.status === 'success' && data.data) {
            updateSensorStatsChart(data.data);
        }
    } catch (error) {
        console.error('Error loading sensor stats:', error);
    }
}

// Update sensor stats chart
function updateSensorStatsChart(stats) {
    const ctx = document.getElementById('sensorStatsChart');
    if (!ctx) return;
    
    if (sensorStatsChart) sensorStatsChart.destroy();
    
    const sensorTypes = [...new Set(stats.map(s => s.sensor_type))];
    const avgByType = sensorTypes.map(type => {
        const typeStats = stats.filter(s => s.sensor_type === type);
        return typeStats.reduce((sum, s) => sum + parseFloat(s.avg_value || 0), 0) / typeStats.length;
    });
    
    sensorStatsChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: sensorTypes,
            datasets: [{
                label: 'Mesatarja e Vlerave',
                data: avgByType,
                backgroundColor: ['#2563eb', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6']
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: { beginAtZero: true }
            }
        }
    });
}

// Load realtime data
async function loadRealtimeData() {
    // Always refresh token before API call
    authToken = localStorage.getItem('authToken') || sessionStorage.getItem('authToken');
    if (!authToken) {
        console.warn('No auth token found');
        return;
    }
    
    try {
        // Refresh token again right before the call
        authToken = localStorage.getItem('authToken') || sessionStorage.getItem('authToken');
        const response = await fetch('/api/sensor-stats?hours=1', {
            headers: {'Authorization': `Bearer ${authToken}`}
        });
        const data = await response.json();
        
        if (data.status === 'success' && data.data) {
            updateRealtimeChart(data.data);
        }
    } catch (error) {
        console.error('Error loading realtime data:', error);
    }
}

// Update realtime chart
function updateRealtimeChart(stats) {
    const ctx = document.getElementById('realtimeChart');
    if (!ctx) return;
    
    if (realtimeChart) realtimeChart.destroy();
    
    // Group by time
    const timeGroups = {};
    stats.forEach(s => {
        const time = new Date(s.timestamp || Date.now()).toLocaleTimeString();
        if (!timeGroups[time]) timeGroups[time] = [];
        timeGroups[time].push(parseFloat(s.avg_value || 0));
    });
    
    const labels = Object.keys(timeGroups).slice(-10);
    const values = labels.map(time => {
        const group = timeGroups[time];
        return group.reduce((sum, v) => sum + v, 0) / group.length;
    });
    
    realtimeChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Vlera në Kohë Reale',
                data: values,
                borderColor: '#10b981',
                backgroundColor: 'rgba(16, 185, 129, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: true }
            },
            scales: {
                y: { beginAtZero: true }
            }
        }
    });
}

// Load anomalies
async function loadAnomalies() {
    // Always refresh token before API call
    authToken = localStorage.getItem('authToken') || sessionStorage.getItem('authToken');
    if (!authToken) {
        console.warn('No auth token found');
        return;
    }
    
    try {
        // Refresh token again right before the call
        authToken = localStorage.getItem('authToken') || sessionStorage.getItem('authToken');
        const response = await fetch('/api/anomalies', {
            headers: {'Authorization': `Bearer ${authToken}`}
        });
        const data = await response.json();
        
        if (data.status === 'success') {
            updateAnomaliesList(data.anomalies);
            document.getElementById('anomaliesCount').textContent = data.anomalies?.length || 0;
        }
    } catch (error) {
        console.error('Error loading anomalies:', error);
    }
}

// Update anomalies list
function updateAnomaliesList(anomalies) {
    const list = document.getElementById('anomaliesList');
    if (!anomalies || anomalies.length === 0) {
        list.innerHTML = `
            <div class="alert alert-success">
                ✅ Nuk ka anomalitë. Sistemi funksionon normalisht.
            </div>
        `;
        return;
    }
    
    list.innerHTML = anomalies.slice(0, 5).map(a => `
        <div class="alert alert-${a.anomaly_type === 'very_high' ? 'danger' : 'warning'}" style="margin-bottom: 0.5rem;">
            <strong>${a.sensor_id}</strong> - ${a.sensor_type}<br>
            <small>Vlera: ${a.value.toFixed(2)} | Z-Score: ${(a.z_score || 0).toFixed(1)}</small><br>
            <small>🕐 ${new Date(a.timestamp).toLocaleString('sq-AL')}</small>
        </div>
    `).join('');
}

// Load recent data
async function loadRecentData(limit = 10) {
    // Always refresh token before API call
    authToken = localStorage.getItem('authToken') || sessionStorage.getItem('authToken');
    if (!authToken) {
        console.warn('No auth token found');
        return;
    }
    
    try {
        // Refresh token again right before the call
        authToken = localStorage.getItem('authToken') || sessionStorage.getItem('authToken');
        // Add cache-busting timestamp to ensure fresh data
        const cacheBuster = `&_t=${Date.now()}`;
        const response = await fetch(`/api/sensor-stats?hours=24${cacheBuster}`, {
            headers: {'Authorization': `Bearer ${authToken}`},
            cache: 'no-cache'  // Disable browser cache
        });
        
        // Check for auth errors
        if (response.status === 401) {
            console.error('❌ Authentication failed (401)');
            return;
        }
        
        if (!response.ok) {
            console.error(`❌ API error: ${response.status}`);
            return;
        }
        
        const data = await response.json();
        
        if (data.status === 'success' && data.data && data.data.length > 0) {
            updateDataTable(data.data.slice(0, limit));
        } else {
            // Show message if no data but API call succeeded
            const tbody = document.getElementById('dataTableBody');
            if (tbody) {
                tbody.innerHTML = '<tr><td colspan="5" class="text-center">Duke pritur të dhëna... (Të dhënat e reja shfaqen pas 30-60 sekondave)</td></tr>';
            }
        }
    } catch (error) {
        console.error('Error loading recent data:', error);
    }
}

// Update data table
function updateDataTable(data) {
    const tbody = document.getElementById('dataTableBody');
    if (!data || data.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center">Nuk ka të dhëna</td></tr>';
        return;
    }
    
    tbody.innerHTML = data.map(s => `
        <tr>
            <td>${s.sensor_id}</td>
            <td><span class="badge badge-primary">${s.sensor_type}</span></td>
            <td>${parseFloat(s.avg_value || 0).toFixed(2)}</td>
            <td>${new Date(s.timestamp || Date.now()).toLocaleString('sq-AL')}</td>
            <td><span class="badge badge-success">Aktiv</span></td>
        </tr>
    `).join('');
}

// Utility functions
function refreshAll() {
    loadDashboard();
}

function exportData() {
    alert('Export functionality - Coming soon!');
}

function showSettings() {
    alert('Settings - Coming soon!');
}

function showAlert(containerId, message, type) {
    const container = document.getElementById(containerId);
    container.innerHTML = `<div class="alert alert-${type}">${message}</div>`;
    setTimeout(() => {
        container.innerHTML = '';
    }, 5000);
}

function showAuthError(message) {
    // Show auth error at top of page
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-danger';
    alertDiv.style.cssText = 'position: fixed; top: 0; left: 0; right: 0; z-index: 9999; margin: 0; padding: 1rem; text-align: center; background: #ef4444; color: white; font-weight: bold;';
    alertDiv.textContent = `⚠️ ${message}`;
    document.body.insertBefore(alertDiv, document.body.firstChild);
    
    setTimeout(() => {
        alertDiv.remove();
    }, 10000);
}

// Cleanup
window.addEventListener('beforeunload', () => {
    if (refreshInterval) clearInterval(refreshInterval);
});
