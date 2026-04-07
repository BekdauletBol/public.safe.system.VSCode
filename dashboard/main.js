let audioEnabled = false;
const alertSound = new Audio('https://actions.google.com/sounds/v1/alarms/beep_short.ogg');

// ── CLOCK ──
setInterval(() => {
    document.getElementById('clock').innerText =
        new Date().toISOString().replace('T', ' ').slice(0, 19);
}, 1000);

// ── CHART ──
const ctx = document.getElementById('healthChart').getContext('2d');
const healthChart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: Array(40).fill(""),
        datasets: [{
            label: 'Intensity',
            data: [],
            borderColor: 'rgba(200,255,0,0.8)',
            borderWidth: 1.5,
            fill: true,
            backgroundColor: 'rgba(200,255,0,0.04)',
            pointRadius: 0,
            tension: 0.4
        }]
    },
    options: {
        scales: {
            y: {
                display: true,
                min: 0, max: 400,
                grid: { color: 'rgba(255,255,255,0.04)' },
                ticks: { color: '#333', font: { size: 9, family: 'DM Mono' } }
            },
            x: { display: false }
        },
        plugins: { legend: { display: false } },
        animation: false
    }
});

// ── WEBSOCKET ──
const ws = new WebSocket(`wss://${location.host}/ws/data`);
ws.onmessage = (e) => {
    const data = JSON.parse(e.data);
    const streamEl = document.getElementById('stream');
    const awaiting = document.querySelector('.awaiting');

    streamEl.src = "data:image/jpeg;base64," + data.img;
    if (awaiting) awaiting.style.display = 'none';

    document.getElementById('cpu').innerText = data.cpu + "%";
    document.getElementById('viol').innerText = data.v;

    const dataset = healthChart.data.datasets[0];
    if (data.v > 0) {
        document.getElementById('monitor-card').classList.add('alert-active');
        if (audioEnabled) alertSound.play();
        dataset.borderColor = 'rgba(255,49,49,0.9)';
        dataset.backgroundColor = 'rgba(255,49,49,0.05)';
    } else {
        document.getElementById('monitor-card').classList.remove('alert-active');
        dataset.borderColor = 'rgba(200,255,0,0.8)';
        dataset.backgroundColor = 'rgba(200,255,0,0.04)';
    }

    dataset.data.push(data.lat);
    if (dataset.data.length > 40) dataset.data.shift();
    healthChart.update();
};

// ── AUDIO TOGGLE ──
function toggleAudio() {
    audioEnabled = !audioEnabled;
    const btn = document.getElementById('audioBtn');
    btn.querySelector('span').innerText = audioEnabled ? "Sound: on" : "Sound: off";
    btn.classList.toggle('active', audioEnabled);
}

// ── GENERATE REPORT ──
async function generateReport() {
    const btn = document.getElementById('genBtn');
    btn.innerText = "Compiling...";
    btn.disabled = true;

    const res = await fetch('/api/build_analytics');
    const data = await res.json();

    if (data.status === 'success') {
        const preview = document.getElementById('reportPreview');
        preview.style.display = 'block';
        document.getElementById('finalImg').src = data.url + "?t=" + Date.now();
        document.getElementById('reportTs').innerText =
            new Date().toISOString().replace('T', ' ').slice(0, 19);
        btn.innerText = "Regenerate report (.png)";
    } else {
        alert("Wait a bit more for data collection");
        btn.innerText = "Generate report (.png)";
    }

    btn.disabled = false;
}