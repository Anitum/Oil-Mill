{% extends "base.html" %}

{% block title %}Oil Mill Dashboard{% endblock %}

{% block extra_css %}
<style>
.camera-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1rem;
    margin-bottom: 2rem;
}

.camera-card {
    background: white;
    padding: 1rem;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    transition: transform 0.2s;
}

.camera-card:hover {
    transform: translateY(-2px);
}

.camera-active {
    border-left: 4px solid #28a745;
}

.camera-inactive {
    border-left: 4px solid #dc3545;
}

.chart-container {
    background: white;
    padding: 1rem;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    margin-bottom: 1.5rem;
}

.status-indicator {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    display: inline-block;
    margin-right: 8px;
}

.status-active {
    background: #28a745;
}

.status-inactive {
    background: #dc3545;
}
</style>
{% endblock %}

{% block content %}
<div class="container-fluid py-4">
    <!-- Camera Controls -->
    <div class="mb-4">
        <h2>Camera Controls</h2>
        <div class="camera-grid">
            <!-- Will be populated by JavaScript -->
        </div>
    </div>

    <!-- Charts Row -->
    <div class="row">
        <!-- People Count Chart -->
        <div class="col-md-4">
            <div class="chart-container">
                <h3>Aggregate People Count</h3>
                <canvas id="peopleChart"></canvas>
            </div>
        </div>

        <!-- Machine Usage Chart -->
        <div class="col-md-4">
            <div class="chart-container">
                <h3>Machine Usage</h3>
                <canvas id="machineChart"></canvas>
            </div>
        </div>

        <!-- Activity Chart -->
        <div class="col-md-4">
            <div class="chart-container">
                <h3>Activity Overview</h3>
                <canvas id="activityChart"></canvas>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script>
// Initialize charts and data
let peopleChart, machineChart, activityChart;

// Camera card template
function createCameraCard(camera) {
    return `
        <div class="camera-card camera-${camera.status}" id="camera-${camera.id}">
            <div class="d-flex justify-content-between align-items-center mb-2">
                <h5 class="mb-0">${camera.name}</h5>
                <span class="status-indicator status-${camera.status}"></span>
            </div>
            <p class="text-muted small mb-2">${camera.location}</p>
            <button class="btn btn-sm ${camera.status === 'active' ? 'btn-danger' : 'btn-success'} w-100"
                    onclick="toggleCamera('${camera.id}')">
                ${camera.status === 'active' ? 'Lock Camera' : 'Unlock Camera'}
            </button>
        </div>
    `;
}

// Toggle camera status
async function toggleCamera(cameraId) {
    try {
        const response = await fetch(`/api/toggle-camera/${cameraId}`, {
            method: 'POST'
        });
        const data = await response.json();
        if (data.success) {
            // Update UI
            const card = document.getElementById(`camera-${cameraId}`);
            card.className = `camera-card camera-${data.new_status}`;
            const button = card.querySelector('button');
            button.className = `btn btn-sm ${data.new_status === 'active' ? 'btn-danger' : 'btn-success'} w-100`;
            button.textContent = data.new_status === 'active' ? 'Lock Camera' : 'Unlock Camera';
        }
    } catch (error) {
        console.error('Error toggling camera:', error);
    }
}

// Initialize people count chart
async function initPeopleChart() {
    const response = await fetch('/api/people-count');
    const data = await response.json();
    
    const ctx = document.getElementById('peopleChart').getContext('2d');
    peopleChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.data.map(d => new Date(d.timestamp).toLocaleTimeString()),
            datasets: [{
                label: 'Total People',
                data: data.data.map(d => d.total_count),
                borderColor: '#007bff',
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

// Initialize machine usage chart
async function initMachineChart() {
    const response = await fetch('/api/machine-usage');
    const data = await response.json();
    
    const machines = Object.values(data.machines);
    const latestUsage = machines.map(m => ({
        name: m.name,
        usage: m.usage_data[m.usage_data.length - 1].usage_minutes
    }));

    const ctx = document.getElementById('machineChart').getContext('2d');
    machineChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: latestUsage.map(m => m.name),
            datasets: [{
                label: 'Usage (minutes)',
                data: latestUsage.map(m => m.usage),
                backgroundColor: '#28a745'
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

// Initialize activity chart
async function initActivityChart() {
    const response = await fetch('/api/activity-data');
    const data = await response.json();
    
    const activities = Object.values(data.activities);
    const latestActivity = activities.map(a => ({
        name: a.name,
        count: a.data[a.data.length - 1].count
    }));

    const ctx = document.getElementById('activityChart').getContext('2d');
    activityChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: latestActivity.map(a => a.name),
            datasets: [{
                label: 'Activity Count',
                data: latestActivity.map(a => a.count),
                backgroundColor: '#17a2b8'
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

// Initialize camera grid
async function initCameraGrid() {
    const response = await fetch('/api/camera-status');
    const data = await response.json();
    
    const grid = document.querySelector('.camera-grid');
    grid.innerHTML = Object.values(data.cameras)
        .map(camera => createCameraCard(camera))
        .join('');
}

// Initialize dashboard
async function initDashboard() {
    await Promise.all([
        initCameraGrid(),
        initPeopleChart(),
        initMachineChart(),
        initActivityChart()
    ]);
}

// Update data periodically
function startDataRefresh() {
    setInterval(async () => {
        // Update each chart with new data
        const peopleResponse = await fetch('/api/people-count');
        const peopleData = await peopleResponse.json();
        peopleChart.data.labels = peopleData.data.map(d => new Date(d.timestamp).toLocaleTimeString());
        peopleChart.data.datasets[0].data = peopleData.data.map(d => d.total_count);
        peopleChart.update();

        const machineResponse = await fetch('/api/machine-usage');
        const machineData = await machineResponse.json();
        // Update machine chart...

        const activityResponse = await fetch('/api/activity-data');
        const activityData = await activityResponse.json();
        // Update activity chart...
    }, 60000); // Refresh every minute
}

// Start dashboard
document.addEventListener('DOMContentLoaded', () => {
    initDashboard().then(() => {
        startDataRefresh();
    });
});
</script>
{% endblock %}
