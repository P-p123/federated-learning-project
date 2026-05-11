// Hospital data for display
const HOSPITAL_DATA = [
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

let chart;
let accuracyData = [];
let labels = [];

// ✅ INIT CHART
function initChart() {
    const ctx = document.getElementById('chart').getContext('2d');

    chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Federated Accuracy',
                data: accuracyData,
                borderWidth: 2,
                backgroundColor: 'rgba(59, 130, 246, 0.2)',
                borderColor: '#3b82f6',
                fill: true,
            }]
        },
        options: {
            scales: {
                y: {
                    min: 0,
                    max: 1
                }
            }
        }
    });
}

// 🚀 START TRAINING
async function startTraining() {
    const status = document.getElementById('status');
    const loader = document.getElementById('loader');

    status.innerText = 'Training Started...';
    loader.style.display = 'block';

    try {
        const res = await fetch('/start');
        if (!res.ok) throw new Error('Start failed');

        fetchUpdates();

    } catch (error) {
        console.error(error);
        status.innerText = 'Error occurred ❌';
        loader.style.display = 'none';
    }
}

// 🔄 FETCH LIVE UPDATES
function fetchUpdates() {
    let interval = setInterval(async () => {
        try {
            const res = await fetch('/results');
            const data = await res.json();

            if (!data) return;

            document.getElementById('privacy-status').innerText = data.privacy;

            document.getElementById('accuracy').innerText = data.accuracy.toFixed(3);
            document.getElementById('precision').innerText = data.precision.toFixed(3);
            document.getElementById('recall').innerText = data.recall.toFixed(3);
            document.getElementById('f1').innerText = data.f1.toFixed(3);
            document.getElementById('time').innerText = data.time.toFixed(2);

            document.getElementById('c-acc').innerText = data.c_accuracy.toFixed(3);
            document.getElementById('c-pre').innerText = data.c_precision.toFixed(3);
            document.getElementById('c-rec').innerText = data.c_recall.toFixed(3);
            document.getElementById('c-f1').innerText = data.c_f1.toFixed(3);
            document.getElementById('c-time').innerText = data.c_time.toFixed(2);

            document.getElementById('f-acc').innerText = data.accuracy.toFixed(3);
            document.getElementById('f-pre').innerText = data.precision.toFixed(3);
            document.getElementById('f-rec').innerText = data.recall.toFixed(3);
            document.getElementById('f-f1-table').innerText = data.f1.toFixed(3);
            document.getElementById('f-time-table').innerText = data.time.toFixed(2);

            // Calculate improvements
            const accDiff = ((data.accuracy - data.c_accuracy) / data.c_accuracy * 100).toFixed(1);
            const preDiff = ((data.precision - data.c_precision) / data.c_precision * 100).toFixed(1);
            const recDiff = ((data.recall - data.c_recall) / data.c_recall * 100).toFixed(1);
            const f1Diff = ((data.f1 - data.c_f1) / data.c_f1 * 100).toFixed(1);
            const timeDiff = ((data.c_time - data.time) / data.c_time * 100).toFixed(1);

            document.getElementById('acc-diff').innerText = (accDiff > 0 ? '+' : '') + accDiff + '%';
            document.getElementById('pre-diff').innerText = (preDiff > 0 ? '+' : '') + preDiff + '%';
            document.getElementById('rec-diff').innerText = (recDiff > 0 ? '+' : '') + recDiff + '%';
            document.getElementById('f1-diff').innerText = (f1Diff > 0 ? '+' : '') + f1Diff + '%';
            document.getElementById('time-diff').innerText = (timeDiff > 0 ? '+' : '') + timeDiff + '%';

            labels.push(labels.length + 1);
            accuracyData.push(data.accuracy);
            chart.update();

            fetchClients();

            if (data.status === 'done') {
                clearInterval(interval);
                document.getElementById('status').innerText = 'Training Completed ✅';
                document.getElementById('loader').style.display = 'none';
            }

        } catch (error) {
            console.error(error);
            document.getElementById('status').innerText = 'Error occurred ❌';
            document.getElementById('loader').style.display = 'none';
        }
    }, 2000);
}

// 🔄 FETCH CLIENT STATUS
async function fetchClients() {
    try {
        const res = await fetch('/clients');
        const data = await res.json();

        if (!data || !Array.isArray(data.clients)) return;

        updateClientTable(data.clients);
    } catch (error) {
        console.error(error);
    }
}

function updateClientTable(clients) {
    const tbody = document.getElementById('client-table-body');
    tbody.innerHTML = '';

    if (clients.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6">No client updates yet</td></tr>';
        return;
    }

    // Group clients by hospital ID
    const hospitalClients = {};
    clients.forEach(client => {
        const hospitalId = client.client_id || 0;
        if (!hospitalClients[hospitalId]) {
            hospitalClients[hospitalId] = [];
        }
        hospitalClients[hospitalId].push(client);
    });

    // Display each hospital
    Object.keys(hospitalClients).forEach(hospitalId => {
        const hospital = HOSPITAL_DATA[hospitalId] || { name: `Hospital ${hospitalId}`, location: 'Unknown', behavior: 'unknown' };
        const hospitalClientsList = hospitalClients[hospitalId];
        const latestClient = hospitalClientsList[hospitalClientsList.length - 1];

        const status = latestClient.skipped ? 'Skipped' : 'Active';
        const delay = latestClient.delay ? latestClient.delay.toFixed(1) + 's' : '0.0s';
        const accuracy = latestClient.accuracy ? latestClient.accuracy.toFixed(3) : '--';

        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${hospital.name}</td>
            <td>${hospital.location}</td>
            <td>${hospital.behavior}</td>
            <td>${status}</td>
            <td>${accuracy}</td>
            <td>${delay}</td>
        `;

        tbody.appendChild(row);
    });

    // Update active hospitals count
    const activeCount = Object.keys(hospitalClients).length;
    document.getElementById('active-hospitals').innerText = `${activeCount}/10`;
    document.getElementById('rounds-completed').innerText = clients.length > 0 ? Math.max(...clients.map(c => c.round || 0)) : 0;
}

// INIT
initChart();
fetchClients();