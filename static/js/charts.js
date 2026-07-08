// StadiumGPT - Charting telemetry widgets
let attendanceChartInstance = null;
let incidentChartInstance = null;

window.initializeCharts = function() {
    const attendanceCanvas = document.getElementById('chart-attendance');
    const incidentCanvas = document.getElementById('chart-incidents');

    if (!attendanceCanvas || !incidentCanvas) return;

    // Destroy existing charts to prevent memory leak / overlay rendering bugs
    if (attendanceChartInstance) {
        attendanceChartInstance.destroy();
    }
    if (incidentChartInstance) {
        incidentChartInstance.destroy();
    }

    // 1. Attendance & Gate Traffic Flow Chart
    attendanceChartInstance = new Chart(attendanceCanvas, {
        type: 'line',
        data: {
            labels: ['15:00', '16:00', '17:00', '18:00', '19:00 (Kickoff)', '20:00', '21:00', '22:00 (Post-match)'],
            datasets: [
                {
                    label: 'Spectator Entry Flow Rate (Gate A/B/C)',
                    data: [4200, 12800, 31500, 68900, 78450, 78450, 76200, 12500],
                    borderColor: '#00df89',
                    backgroundColor: 'rgba(0, 223, 137, 0.08)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4
                },
                {
                    label: 'Rideshare Traffic Arrivals (Lot E)',
                    data: [850, 2100, 4800, 7600, 1200, 450, 950, 8900],
                    borderColor: '#00f0ff',
                    backgroundColor: 'rgba(0, 240, 255, 0.08)',
                    borderWidth: 2,
                    fill: false,
                    tension: 0.3
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: { color: '#f3f4f6', font: { family: 'Outfit' } }
                }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(255,255,255,0.05)' },
                    ticks: { color: '#9ca3af', font: { family: 'Outfit' } }
                },
                y: {
                    grid: { color: 'rgba(255,255,255,0.05)' },
                    ticks: { color: '#9ca3af', font: { family: 'Outfit' } }
                }
            }
        }
    });

    // 2. Safety Incident Split Chart
    incidentChartInstance = new Chart(incidentCanvas, {
        type: 'doughnut',
        data: {
            labels: ['Medical', 'Security', 'Fire Alarms', 'Lost Children', 'Equipment Faults'],
            datasets: [{
                data: [12, 5, 2, 3, 1],
                backgroundColor: [
                    '#ff2a5f', // Medical red
                    '#ffaa00', // Security orange
                    '#ff0000', // Fire
                    '#3b82f6', // Lost kids blue
                    '#9ca3af'  // Equipment grey
                ],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { color: '#f3f4f6', font: { family: 'Outfit' } }
                }
            }
        }
    });
};
