document.addEventListener('DOMContentLoaded', () => {
    // Helper function to generate dummy chart data for demonstration
    function generateDummyChartData(initialValue, fluctuationFactor = 0.1, length = 6, positiveTrend = false) {
        const data = [];
        let currentValue = initialValue;
        for (let i = 0; i < length; i++) {
            if (positiveTrend) {
                // Ensure a general upward trend for cumulative values
                currentValue += (Math.random() * 0.5 + 0.05) * initialValue * fluctuationFactor;
            } else {
                // Simulate fluctuation around the value
                currentValue += (Math.random() - 0.5) * initialValue * fluctuationFactor * 2;
            }
            // Prevent values from going too low, especially for percentages/scores
            currentValue = Math.max(currentValue, initialValue * 0.5);
            data.push(parseFloat(currentValue.toFixed(2)));
        }
        return data;
    }

    // Chart labels (months)
    const chartLabels = ['Jan', 'Mar', 'May', 'Jul', 'Sep', 'Nov'];

    // Function to load market news
    async function loadMarketNews() {
        const container = document.getElementById('market-news-container');
        try {
            const response = await fetch('/api/market_news');
            const newsItems = await response.json();

            container.innerHTML = ''; // Clear previous content
            newsItems.forEach(news => {
                const newsHtml = `
                    <div class="news-item">
                        <div class="news-item-content">
                            <h3>${news.title}</h3>
                            <p>${news.description}</p>
                        </div>
                        <img src="${news.image}" alt="${news.title}">
                    </div>
                `;
                container.insertAdjacentHTML('beforeend', newsHtml);
            });
        } catch (error) {
            console.error('Error loading market news:', error);
            container.innerHTML = '<p>Failed to load market news. Please try again later.</p>';
        }
    }

    // Function to load stock-specific news
    async function loadStockSpecificNews(ticker) {
        const container = document.getElementById('stock-specific-news-container');
        try {
            container.innerHTML = '<p>Loading stock news...</p>'; // Loading indicator
            const response = await fetch(`/api/stock_specific_news?ticker=${ticker}`);
            const newsItem = await response.json();

            container.innerHTML = ''; // Clear loading indicator
            if (newsItem.error) {
                container.innerHTML = `<p>${newsItem.error}</p>`;
                return;
            }

            const newsHtml = `
                <div class="news-item">
                    <div class="news-item-content">
                        <h3>${newsItem.title}</h3>
                        <p>${newsItem.description}</p>
                    </div>
                    <img src="${newsItem.image}" alt="${newsItem.title}">
                </div>
            `;
            container.insertAdjacentHTML('beforeend', newsHtml);
        } catch (error) {
            console.error('Error loading stock-specific news:', error);
            container.innerHTML = '<p>Failed to load stock-specific news. Please try again later.</p>';
        }
    }

    // Function to load performance charts data
    async function loadPerformanceCharts(ticker = 'IBM') { // Default to IBM or a common ticker for API calls
        const relativePerformanceValue = document.getElementById('rp-value');
        const relativePerformanceChange = document.getElementById('rp-change');
        const zScoreValue = document.getElementById('zscore-value');
        const zScoreChange = document.getElementById('zscore-change');
        const alphaValue = document.getElementById('alpha-value');
        const alphaChange = document.getElementById('alpha-change');
        const cumulativeAlphaValue = document.getElementById('cumulative-alpha-value');
        const cumulativeAlphaChange = document.getElementById('cumulative-alpha-change');

        try {
            const response = await fetch(`/api/performance_charts?ticker=${ticker}`);
            const data = await response.json();

            if (data.error) {
                console.error('Error loading performance data:', data.error);
                return;
            }

            // Update numerical values from API response
            relativePerformanceValue.textContent = data.relative_performance.value.replace('+', '');
            relativePerformanceChange.textContent = data.relative_performance.change.replace('+', '');
            // Update color class for relative performance
            const rpChangeSpan = relativePerformanceChange.closest('span');
            rpChangeSpan.classList.toggle('positive', data.relative_performance.value.startsWith('+'));
            rpChangeSpan.classList.toggle('negative', data.relative_performance.value.startsWith('-'));


            zScoreValue.textContent = data.moving_z_score.value;
            zScoreChange.textContent = data.moving_z_score.change.replace('-', '');
            // Update color class for Z-score
            const zScoreChangeSpan = zScoreChange.closest('span');
            zScoreChangeSpan.classList.toggle('positive', !data.moving_z_score.change.startsWith('-')); // Z-score positive if not negative
            zScoreChangeSpan.classList.toggle('negative', data.moving_z_score.change.startsWith('-'));


            alphaValue.textContent = data.alpha.value;
            alphaChange.textContent = data.alpha.change.replace('+', '');
            // Update color class for Alpha
            const alphaChangeSpan = alphaChange.closest('span');
            alphaChangeSpan.classList.toggle('positive', data.alpha.change.startsWith('+'));
            alphaChangeSpan.classList.toggle('negative', data.alpha.change.startsWith('-'));


            cumulativeAlphaValue.textContent = data.cumulative_alpha.value;
            cumulativeAlphaChange.textContent = data.cumulative_alpha.change.replace('+', '');
            // Update color class for Cumulative Alpha
            const cumulativeAlphaChangeSpan = cumulativeAlphaChange.closest('span');
            cumulativeAlphaChangeSpan.classList.toggle('positive', data.cumulative_alpha.change.startsWith('+'));
            cumulativeAlphaChangeSpan.classList.toggle('negative', data.cumulative_alpha.change.startsWith('-'));


            // Render charts with dummy historical data (based on fetched current values)
            renderChart('relativePerformanceChart', generateDummyChartData(parseFloat(data.relative_performance.value.replace('%', '')), 0.1), chartLabels, '#007bff');
            renderChart('movingZScoreChart', generateDummyChartData(parseFloat(data.moving_z_score.value), 0.1), chartLabels, '#ffc107'); // Yellow for Z-score
            renderChart('alphaChart', generateDummyChartData(parseFloat(data.alpha.value), 0.5), chartLabels, '#28a745'); // Green for Alpha
            renderChart('cumulativeAlphaChart', generateDummyChartData(parseFloat(data.cumulative_alpha.value), 0.2, 6, true), chartLabels, '#17a2b8'); // Cyan for Cumulative Alpha

        } catch (error) {
            console.error('Error loading performance charts:', error);
        }
    }

    // Initial loads
    loadMarketNews();
    loadStockSpecificNews('XYZ'); // Load default XYZ news on page load
    loadPerformanceCharts('IBM'); // Load performance for IBM initially, or any default ticker

    // Event listener for stock ticker input
    const stockTickerInput = document.getElementById('stock-ticker-input');
    const fetchStockNewsBtn = document.getElementById('fetch-stock-news-btn');

    fetchStockNewsBtn.addEventListener('click', () => {
        const ticker = stockTickerInput.value.trim().toUpperCase();
        if (ticker) {
            loadStockSpecificNews(ticker);
            loadPerformanceCharts(ticker); // Load performance charts for the new ticker
        } else {
            alert('Please enter a stock ticker.');
        }
    });

    // Handle Enter key for stock ticker input
    stockTickerInput.addEventListener('keypress', (event) => {
        if (event.key === 'Enter') {
            fetchStockNewsBtn.click();
        }
    });
});
