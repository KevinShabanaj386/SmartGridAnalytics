// JavaScript për dashboard page
let authToken = localStorage.getItem('authToken');

if (!authToken) {
    window.location.href = '/';
}

async function loadDetailedStats() {
    try {
        const response = await fetch('/api/sensor-stats?hours=48', {
            headers: {'Authorization': `Bearer ${authToken}`}
        });
        const data = await response.json();
        
        if (data.status === 'success') {
            displayDetailedStats(data.data);
        }
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

function displayDetailedStats(stats) {
    const container = document.getElementById('detailedStats');
    // Implementimi i detajuar...
}

loadDetailedStats();

