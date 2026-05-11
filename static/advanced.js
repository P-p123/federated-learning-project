// Hospital data
const HOSPITALS = [
    { name: "Mayo Clinic", location: "Rochester, MN", behavior: "honest" },
    { name: "Cleveland Clinic", location: "Cleveland, OH", behavior: "slow" },
    { name: "Johns Hopkins", location: "Baltimore, MD", behavior: "sleepy" },
    { name: "Mass General", location: "Boston, MA", behavior: "fast" },
    { name: "UCLA Medical", location: "Los Angeles, CA", behavior: "unreliable" },
    { name: "NYU Langone", location: "New York, NY", behavior: "honest" },
    { name: "Duke Hospital", location: "Durham, NC", behavior: "slow" },
    { name: "Stanford Hospital", location: "Stanford, CA", behavior: "sleepy" },
    { name: "Mount Sinai", location: "New York, NY", behavior: "fast" },
    { name: "Barnes-Jewish", location: "St. Louis, MO", behavior: "unreliable" }
];

// Chart instances
let accuracyChart, lossChart, contributionChart;

// Data storage
let accuracyData = { labels: [], federated: [], centralized: [] };
let lossData = { labels: [], federated: [], centralized: [] };
let trainingState = { isRunning: false, startTime: 0, elapsedTime: 0, round: 0 };

// Initialize all charts
function initCharts() {
    // Destroy existing charts if they exist
    if (accuracyChart) accuracyChart.destroy();
    if (lossChart) lossChart.destroy();
    if (contributionChart) contributionChart.destroy();
    
    // Accuracy Chart
    const accuracyCtx = document.getElementById('accuracy-chart').getContext('2d');
    accuracyChart = new Chart(accuracyCtx, {
        type: 'line',
        data: {
            labels: accuracyData.labels,
            datasets: [
                {
                    label: 'Federated Learning',
                    data: accuracyData.federated,
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 5,
                    pointBackgroundColor: '#3b82f6',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2
                },
                {
                    label: 'Centralized Learning',
                    data: accuracyData.centralized,
                    borderColor: '#ef4444',
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    borderWidth: 3,
                    borderDash: [5, 5],
                    fill: true,
                    tension: 0.4,
                    pointRadius: 5,
                    pointBackgroundColor: '#ef4444',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: { color: '#e2e8f0', font: { size: 12, weight: '600' } }
                }
            },
            scales: {
                y: {
                    min: 0,
                    max: 1,
                    ticks: { color: '#94a3b8' },
                    grid: { color: 'rgba(51, 65, 85, 0.5)' }
                },
                x: {
                    ticks: { color: '#94a3b8' },
                    grid: { color: 'rgba(51, 65, 85, 0.5)' }
                }
            }
        }
    });

    // Loss Chart
    const lossCtx = document.getElementById('loss-chart').getContext('2d');
    lossChart = new Chart(lossCtx, {
        type: 'line',
        data: {
            labels: lossData.labels,
            datasets: [
                {
                    label: 'Federated Loss',
                    data: lossData.federated,
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 5,
                    pointBackgroundColor: '#3b82f6'
                },
                {
                    label: 'Centralized Loss',
                    data: lossData.centralized,
                    borderColor: '#ef4444',
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    borderWidth: 3,
                    borderDash: [5, 5],
                    fill: true,
                    tension: 0.4,
                    pointRadius: 5,
                    pointBackgroundColor: '#ef4444'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: { color: '#e2e8f0', font: { size: 12, weight: '600' } }
                }
            },
            scales: {
                y: {
                    ticks: { color: '#94a3b8' },
                    grid: { color: 'rgba(51, 65, 85, 0.5)' }
                },
                x: {
                    ticks: { color: '#94a3b8' },
                    grid: { color: 'rgba(51, 65, 85, 0.5)' }
                }
            }
        }
    });

    // Contribution Chart (Pie)
    const contributionCtx = document.getElementById('contribution-chart').getContext('2d');
    contributionChart = new Chart(contributionCtx, {
        type: 'doughnut',
        data: {
            labels: HOSPITALS.map(h => h.name),
            datasets: [{
                data: new Array(10).fill(0),
                backgroundColor: [
                    '#3b82f6', '#06b6d4', '#10b981', '#f59e0b', '#ef4444',
                    '#8b5cf6', '#ec4899', '#14b8a6', '#f97316', '#6366f1'
                ],
                borderColor: '#1e293b',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: { color: '#e2e8f0', font: { size: 11 }, padding: 15 }
                }
            }
        }
    });
}

// Start training
async function startTraining() {
    if (trainingState.isRunning) return;
    
    trainingState.isRunning = true;
    trainingState.startTime = Date.now();
    trainingState.round = 0;
    
    document.getElementById('status-text').textContent = 'Training in Progress...';
    
    try {
        const res = await fetch('/start');
        if (!res.ok) throw new Error('Failed to start training');
        
        fetchUpdates();
    } catch (error) {
        console.error(error);
        document.getElementById('status-text').textContent = 'Error occurred';
        trainingState.isRunning = false;
    }
}

// Pause training
function pauseTraining() {
    trainingState.isRunning = false;
    document.getElementById('status-text').textContent = 'Paused';
}

// Reset training
function resetTraining() {
    trainingState.isRunning = false;
    trainingState.round = 0;
    trainingState.elapsedTime = 0;
    accuracyData = { labels: [], federated: [], centralized: [] };
    lossData = { labels: [], federated: [], centralized: [] };
    document.getElementById('status-text').textContent = 'Ready';
    document.getElementById('training-time').textContent = '00:00:00';
    document.getElementById('metric-round').textContent = '0';
    initCharts();
}

// Fetch live updates
let updateInterval;
function fetchUpdates() {
    updateInterval = setInterval(async () => {
        try {
            const res = await fetch('/results');
            const data = await res.json();
            
            if (!data) return;
            
            // Update main stats
            document.getElementById('accuracy-main').textContent = (data.accuracy * 100).toFixed(2) + '%';
            document.getElementById('accuracy-score').textContent = (data.c_accuracy * 100).toFixed(2) + '%';
            
            // Update metrics
            document.getElementById('metric-precision').textContent = (data.precision * 100).toFixed(2) + '%';
            document.getElementById('metric-recall').textContent = (data.recall * 100).toFixed(2) + '%';
            document.getElementById('metric-f1').textContent = (data.f1 * 100).toFixed(2) + '%';
            
            // Update comparison table
            document.getElementById('comp-f-acc').textContent = (data.accuracy * 100).toFixed(2) + '%';
            document.getElementById('comp-f-pre').textContent = (data.precision * 100).toFixed(2) + '%';
            document.getElementById('comp-f-rec').textContent = (data.recall * 100).toFixed(2) + '%';
            document.getElementById('comp-f-f1').textContent = (data.f1 * 100).toFixed(2) + '%';
            document.getElementById('comp-f-time').textContent = data.time.toFixed(2) + 's';
            
            document.getElementById('comp-c-acc').textContent = (data.c_accuracy * 100).toFixed(2) + '%';
            document.getElementById('comp-c-pre').textContent = (data.c_precision * 100).toFixed(2) + '%';
            document.getElementById('comp-c-rec').textContent = (data.c_recall * 100).toFixed(2) + '%';
            document.getElementById('comp-c-f1').textContent = (data.c_f1 * 100).toFixed(2) + '%';
            document.getElementById('comp-c-time').textContent = data.c_time.toFixed(2) + 's';
            document.getElementById('comp-f-rounds').textContent = trainingState.round;
            document.getElementById('comp-c-rounds').textContent = data.c_time > 0 ? 1 : '--';
            
            // Update time
            if (trainingState.isRunning) {
                trainingState.elapsedTime = Math.floor((Date.now() - trainingState.startTime) / 1000);
                const hours = Math.floor(trainingState.elapsedTime / 3600);
                const minutes = Math.floor((trainingState.elapsedTime % 3600) / 60);
                const seconds = trainingState.elapsedTime % 60;
                document.getElementById('training-time').textContent = 
                    String(hours).padStart(2, '0') + ':' +
                    String(minutes).padStart(2, '0') + ':' +
                    String(seconds).padStart(2, '0');
                document.getElementById('sidebar-time').textContent = document.getElementById('training-time').textContent;
            }
            
            // Add chart data
            trainingState.round++;
            accuracyData.labels.push(`Round ${trainingState.round}`);
            accuracyData.federated.push(data.accuracy);
            accuracyData.centralized.push(data.c_accuracy);
            lossData.labels.push(`Round ${trainingState.round}`);
            lossData.federated.push(Math.max(0.1, 1 - data.accuracy));
            lossData.centralized.push(Math.max(0.1, 1 - data.c_accuracy));
            
            document.getElementById('metric-round').textContent = trainingState.round;
            
            // Keep only last 20 rounds
            if (accuracyData.labels.length > 20) {
                accuracyData.labels.shift();
                accuracyData.federated.shift();
                accuracyData.centralized.shift();
                lossData.labels.shift();
                lossData.federated.shift();
                lossData.centralized.shift();
            }
            
            accuracyChart.update();
            lossChart.update();
            
            // Fetch clients
            await fetchClients();
            
            // Check if done
            if (data.status === 'done') {
                clearInterval(updateInterval);
                document.getElementById('status-text').textContent = 'Completed ✓';
                trainingState.isRunning = false;
            }
            
        } catch (error) {
            console.error(error);
        }
    }, 2000);
}

// Fetch client updates
async function fetchClients() {
    try {
        const res = await fetch('/clients');
        const data = await res.json();
        
        if (!data || !Array.isArray(data.clients)) return;
        
        updateClientTable(data.clients);
        updateContributionChart(data.clients);
        updateBehaviorSummary(data.clients);
        
    } catch (error) {
        console.error(error);
    }
}

// Behavior color mapping
const behaviorColors = {
    'honest': { bg: 'rgba(16, 185, 129, 0.1)', text: '#10b981', icon: '✓' },
    'slow': { bg: 'rgba(245, 158, 11, 0.1)', text: '#f59e0b', icon: '🐌' },
    'sleepy': { bg: 'rgba(139, 92, 246, 0.1)', text: '#8b5cf6', icon: '😴' },
    'fast': { bg: 'rgba(59, 130, 246, 0.1)', text: '#3b82f6', icon: '⚡' },
    'unreliable': { bg: 'rgba(239, 68, 68, 0.1)', text: '#ef4444', icon: '⚠️' }
};

function updateBehaviorSummary(clients) {
    const counts = {
        honest: 0,
        slow: 0,
        sleepy: 0,
        fast: 0,
        unreliable: 0
    };

    clients.forEach(client => {
        const behavior = client.behavior || 'honest';
        if (counts.hasOwnProperty(behavior)) {
            counts[behavior] += 1;
        }
    });

    const honest = counts.honest;
    const malicious = counts.unreliable;

    document.getElementById('honest-count').textContent = honest;
    document.getElementById('fast-count').textContent = counts.fast;
    document.getElementById('slow-count').textContent = counts.slow;
    document.getElementById('sleepy-count').textContent = counts.sleepy;
    document.getElementById('unreliable-count').textContent = malicious;
    document.getElementById('honest-vs-malicious').textContent = `${honest} / ${malicious}`;
}

// Update client table
function updateClientTable(clients) {
    const tbody = document.getElementById('clients-tbody');
    
    if (clients.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="loading-text">Waiting for clients...</td></tr>';
        return;
    }
    
    const hospitalClients = {};
    clients.forEach(client => {
        const hospitalId = client.client_id || 0;
        if (!hospitalClients[hospitalId]) {
            hospitalClients[hospitalId] = [];
        }
        hospitalClients[hospitalId].push(client);
    });
    
    tbody.innerHTML = '';
    
    Object.keys(hospitalClients).forEach(hospitalId => {
        const hospital = HOSPITALS[hospitalId] || { name: `Hospital ${hospitalId}` };
        const latestClient = hospitalClients[hospitalId][hospitalClients[hospitalId].length - 1];
        const behavior = hospital.behavior || 'unknown';
        const behaviorStyle = behaviorColors[behavior] || { bg: 'rgba(148, 163, 184, 0.1)', text: '#94a3b8', icon: '?' };
        
        const behaviorDesc = latestClient.behavior_desc || 'No additional info';
        const row = document.createElement('tr');
        row.style.borderLeft = `4px solid ${behaviorStyle.text}`;
        row.innerHTML = `
            <td><strong>${hospital.name}</strong></td>
            <td>
                <span class="behavior-badge" style="background: ${behaviorStyle.bg}; color: ${behaviorStyle.text};">
                    ${behaviorStyle.icon} ${behavior.toUpperCase()}
                </span>
            </td>
            <td>${behaviorDesc}</td>
            <td><span class="badge ${latestClient.skipped ? 'badge-inactive' : 'badge-active'}">
                ${latestClient.skipped ? '⊘ Skipped' : '✓ Active'}
            </span></td>
            <td>${latestClient.delay ? latestClient.delay.toFixed(1) + 's' : '0.0s'}</td>
            <td>${latestClient.contribution ? (latestClient.contribution * 100).toFixed(1) + '%' : '0%'}</td>
        `;
        
        tbody.appendChild(row);
    });
    
    const activeCount = Object.keys(hospitalClients).length;
    document.getElementById('active-clients-card').textContent = activeCount;
    document.getElementById('sidebar-clients').textContent = `${activeCount}/10`;
}

// Update contribution chart
function updateContributionChart(clients) {
    const contributions = new Array(10).fill(0);
    
    clients.forEach(client => {
        const hospitalId = client.client_id || 0;
        contributions[hospitalId] += (client.contribution || 0.1);
    });
    
    const total = contributions.reduce((a, b) => a + b, 0);
    const normalized = contributions.map(c => total > 0 ? c / total : 0.1);
    
    contributionChart.data.datasets[0].data = normalized;
    contributionChart.update();
}

// Navigation
document.querySelectorAll('.nav-item').forEach((item, index) => {
    item.addEventListener('click', function(e) {
        e.preventDefault();
        document.querySelectorAll('.nav-item').forEach(nav => nav.classList.remove('active'));
        this.classList.add('active');
        
        if (index === 0) resetTraining();
        if (index === 1) startTraining();
    });
});

// Initialize on load
window.addEventListener('DOMContentLoaded', function() {
    initCharts();
    fetchClients();
});