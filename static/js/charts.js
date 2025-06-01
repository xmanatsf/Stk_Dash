// static/js/charts.js

function renderChart(canvasId, data, labels, lineColor = '#007bff') {
  // (a) Grab the canvas by ID
  const canvasEl = document.getElementById(canvasId);
  if (!canvasEl) {
    console.error(`[charts.js] renderChart: Canvas '${canvasId}' not found.`);
    return;
  }
  const ctx = canvasEl.getContext('2d');
  if (!ctx) {
    console.error(`[charts.js] renderChart: 2D context for '${canvasId}' missing.`);
    return;
  }

  // (b) Destroy any existing Chart instance so we start fresh
  if (!window.charts) window.charts = {};
  if (window.charts[canvasId] instanceof Chart) {
    window.charts[canvasId].destroy();
    window.charts[canvasId] = null;
  }

  // (c) Determine the dataset label & chart title using the global ticker
  const ticker     = window.currentTicker || ''; 
  // Turn the canvas ID “relativePerformanceChart” → “Relative Performance”
  const metricName = canvasId
                      .replace('Chart', '')
                      .replace(/([A-Z])/g, ' $1')
                      .trim();        // e.g. “relative Performance” → “relative Performance”
  const prettyName = metricName.charAt(0).toUpperCase() + metricName.slice(1); 
  // e.g. “relative Performance” → “Relative Performance”
  const chartTitle = ticker ? `${ticker} ${prettyName}` : prettyName;

  // (d) Build the Chart.js config
  const cfg = {
    type: 'line',
    data: {
      labels: Array.isArray(labels) ? labels : [],
      datasets: [{
        label: chartTitle,
        data: Array.isArray(data) ? data : [],
        borderColor: lineColor,
        borderWidth: 1.5,
        pointRadius: (data && data.length < 10) ? 2 : 0,
        fill: false,
        tension: 0.1
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          display: true,
          grid: { display: false },
          ticks: {
            display: true,
            font: { size: 10 },
            maxRotation: 45,
            minRotation: 0,
            autoSkip: true,
            maxTicksLimit: 6
          }
        },
        y: {
          display: true,
          grid: { color: 'rgba(255, 255, 255, 0.1)' },
          ticks: {
            display: true,
            font: { size: 10 }
          }
        }
      },
      plugins: {
        legend: { display: false },
        title: {
          display: true,
          text: chartTitle,            // ← e.g. “TSLA Relative Performance”
          font: { size: 14 },
          padding: { top: 10, bottom: 10 }
        },
        tooltip: {
          enabled: true,
          mode: 'index',
          intersect: false,
          titleFont: { size: 12 },
          bodyFont: { size: 12 },
          padding: 8,
          cornerRadius: 4
        }
      },
      interaction: {
        mode: 'nearest',
        intersect: false
      },
      animation: false
    }
  };

  // (e) Finally, build the Chart instance and store it for cleanup next time
  try {
    window.charts[canvasId] = new Chart(ctx, cfg);
    console.log(`[charts.js] renderChart: Created '${canvasId}' titled '${chartTitle}'`);
  }
  catch (error) {
    console.error(`[charts.js] renderChart: Chart.js instantiation failed for '${canvasId}':`, error);
  }
}
