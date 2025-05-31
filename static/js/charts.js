// Function to render a Chart.js line chart
function renderChart(canvasId, data, labels, lineColor = '#007bff') {
    const ctx = document.getElementById(canvasId);
    if (!ctx) {
        console.error(`Canvas with ID ${canvasId} not found.`);
        return;
    }
    const chartContext = ctx.getContext('2d');

    // Destroy existing chart if it exists to prevent re-rendering issues
    if (window.charts && window.charts[canvasId]) {
        window.charts[canvasId].destroy();
    }
    
    // Gradient background for the chart area
    const gradient = chartContext.createLinearGradient(0, 0, 0, 150); // Adjust height for gradient
    gradient.addColorStop(0, `${lineColor}4D`); // Top color (e.g., blue with 30% opacity)
    gradient.addColorStop(1, `${lineColor}00`); // Bottom (transparent)

    const newChart = new Chart(chartContext, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                borderColor: lineColor,
                borderWidth: 2,
                pointRadius: 0, // No points on the line
                fill: true, // Fill the area under the line
                backgroundColor: gradient, // Use gradient for fill
                tension: 0.4, // Smooth the line
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    grid: {
                        display: false, // No vertical grid lines
                        drawBorder: false,
                    },
                    ticks: {
                        color: '#A0A0A0', // Text color for x-axis labels
                        font: {
                            size: 12
                        },
                        autoSkip: true,
                        maxRotation: 0,
                        minRotation: 0,
                    }
                },
                y: {
                    display: false, // No y-axis labels
                    grid: {
                        display: false, // No horizontal grid lines
                        drawBorder: false,
                    },
                    ticks: {
                        display: false
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    enabled: true,
                    mode: 'index',
                    intersect: false,
                    callbacks: {
                        title: function() { return ''; },
                        label: function(context) {
                            return `${context.dataset.label || ''} ${context.parsed.y.toFixed(2)}`;
                        }
                    },
                    backgroundColor: 'rgba(0,0,0,0.7)',
                    titleColor: '#fff',
                    bodyColor: '#fff',
                    borderColor: '#4A4C50',
                    borderWidth: 1,
                    cornerRadius: 4,
                }
            }
        }
    });

    // Store chart instance to destroy later
    if (!window.charts) {
        window.charts = {};
    }
    window.charts[canvasId] = newChart;
}
