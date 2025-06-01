// static/js/main.js

document.addEventListener('DOMContentLoaded', () => {
    console.log("[main.js] DOMContentLoaded → initializing.");

    /**
     * ─── RENDER FMP ARTICLES (CARD LAYOUT) ───────────────────────────────────────
     * Fetches /api/fmp_articles (no ticker query) and builds a card for each of the
     * five returned items, showing image + date + author + headline + snippet + link.
     */
    async function loadFmpArticles() {
        console.log("[loadFmpArticles] Fetching general FMP articles...");
        const container = document.getElementById('fmp-articles-container');
        if (!container) {
            console.error("[loadFmpArticles] Container not found: #fmp-articles-container");
            return;
        }

        // Show a “loading” placeholder
        container.innerHTML = '<p>Loading latest market articles...</p>';

        let articles;
        try {
            const response = await fetch('/api/fmp_articles');
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            articles = await response.json();
        } catch (error) {
            console.error("[loadFmpArticles] Error fetching FMP articles:", error);
            container.innerHTML = '<p>Failed to load FMP articles.</p>';
            return;
        }

        // If we did not get a non‐empty array, show “no articles”
        if (!Array.isArray(articles) || articles.length === 0) {
            container.innerHTML = '<p>No FMP articles available.</p>';
            return;
        }

        // Clear the “loading” text
        container.innerHTML = '';

        // Build one <div class="fmp-article-card"> per article
        articles.forEach((article, idx) => {
            // Article fields we expect:
            // article.title, article.date, article.content, article.image,
            // article.link, article.author, article.site

            // 1) Create the outer card wrapper
            const card = document.createElement('div');
            card.className = 'fmp-article-card';

            // 2) LEFT COLUMN: Article image/logo (if provided)
            const leftDiv = document.createElement('div');
            leftDiv.className = 'fmp-article-image';
            const img = document.createElement('img');
            img.src = article.image || '/static/images/placeholder.png'; 
            // If article.image is empty, show a generic placeholder
            img.alt = (article.site || 'FMP') + ' logo';
            leftDiv.appendChild(img);

            // 3) RIGHT COLUMN: meta, headline, snippet, “Read More”
            const rightDiv = document.createElement('div');
            rightDiv.className = 'fmp-article-content';

            // 3a) Meta line: date and author
            const metaDiv = document.createElement('div');
            metaDiv.className = 'fmp-article-meta';
            // Format the date nicely: “May 30, 2025 2:00 PM”
            let formattedDate = article.date ? new Date(article.date).toLocaleString('en-US', {
                month: 'short', day: 'numeric', year: 'numeric',
                hour: 'numeric', minute: '2-digit', hour12: true
            }) : '';
            metaDiv.innerHTML = `
                <span class="date">${formattedDate}</span>
                ${article.author ? `&nbsp;—&nbsp;<span class="author">${article.author}</span>` : ''}
            `;
            rightDiv.appendChild(metaDiv);

            // 3b) Headline (as clickable link)
            const headline = document.createElement('h3');
            headline.className = 'fmp-article-headline';
            headline.innerHTML = `
                <a href="${article.link}" target="_blank" rel="noopener">
                    ${article.title}
                </a>`;
            rightDiv.appendChild(headline);

            // 3c) Snippet: FMP’s “content” field is already HTML. We can show the first
            //     paragraph or entire snippet. For safety, we’ll create a temp div and
            //     grab its innerHTML (so that any <ul>, <li>, <p> tags show up).
            const snippetDiv = document.createElement('div');
            snippetDiv.className = 'fmp-article-snippet';
            // We only want the first 200 characters (or the first <p> block). Let’s
            // strip tags beyond the first closing </p>. A simple approach is:
            let rawHtml = article.content || '';
            let firstParagraph = rawHtml;
            // Try to find the first closing </p> tag
            const closingP = rawHtml.indexOf('</p>');
            if (closingP > 0) {
                firstParagraph = rawHtml.slice(0, closingP + 4);
            }
            snippetDiv.innerHTML = firstParagraph;
            rightDiv.appendChild(snippetDiv);

            // 3d) “Read More →” link
            const readMoreDiv = document.createElement('div');
            readMoreDiv.className = 'fmp-article-readmore';
            readMoreDiv.innerHTML = `
                <a href="${article.link}" target="_blank" rel="noopener">Read More →</a>
            `;
            rightDiv.appendChild(readMoreDiv);

            // 4) Append left + right columns to the card
            card.appendChild(leftDiv);
            card.appendChild(rightDiv);

            // 5) Finally, append this card into the container
            container.appendChild(card);
        });
    }

    /**
     * Renders an <ul> list of stock‐specific news into #ticker-news-container
     * Uses /api/fmp_articles?ticker=XYZ
     */
async function loadTickerNews(ticker) {
    console.log(`[loadTickerNews] Fetching news for ticker='${ticker}'...`);
    const container = document.getElementById('ticker-news-container');
    const titleElement = document.getElementById('ticker-news-section-title');
    if (!container || !titleElement) {
        console.error("[loadTickerNews] Required elements not found");
        return;
    }

    titleElement.textContent = `News for ${ticker} (last 30 days):`;
    try {
        container.innerHTML = '<p>Loading...</p>';
        const response = await fetch(`/api/fmp_articles?ticker=${ticker}`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        const articles = await response.json();
        container.innerHTML = '';

        if (Array.isArray(articles) && articles.length > 0) {
            const ul = document.createElement('ul');
            ul.className = 'text-news-list';

            articles.forEach((article, index) => {
                const li = document.createElement('li');
                li.innerHTML = `
                  <strong>${index + 1}. 
                    <a href="${article.link}" target="_blank" rel="noopener">
                      ${article.title}
                    </a>
                  </strong>
                  <em>(${article.site})</em>
                `;
                ul.appendChild(li);
            });

            container.appendChild(ul);
        } else {
            container.innerHTML = `<p>No news found for ${ticker}.</p>`;
        }
    } catch (error) {
        console.error("[loadTickerNews] Error:", error);
        container.innerHTML = `<p>Failed to load news for ${ticker}.</p>`;
    }
}


    /**
     * Updates a chart‐card's text (value + change) without touching the canvas.
     */
    function updateChartCardTextOnly(valueElementId, changeElementId, valueStr, changeStr) {
        const valueEl = document.getElementById(valueElementId);
        const changeEl = document.getElementById(changeElementId);

        if (valueEl && typeof valueStr === 'string') {
            // ✅ Preserve sign and percentage as-is
            valueEl.textContent = valueStr.trim();
        }

        if (changeEl && typeof changeStr === 'string') {
            const changeOuterSpan = changeEl.parentElement;

            // ✅ Preserve sign and percentage as-is
            changeEl.textContent = changeStr.trim();

            // ✅ Add class based on sign
            if (changeOuterSpan) {
                changeOuterSpan.classList.remove('positive', 'negative');
                if (changeStr.startsWith('-')) {
                    changeOuterSpan.classList.add('negative');
                } else {
                    changeOuterSpan.classList.add('positive');
                }
            }
        }
    }


    /**
     * Fetches /api/performance_charts?ticker=XYZ, updates card text & draws 4 charts.
     * Expects returned JSON shape:
     *   {
     *     relative_performance: { value, change, dates:[...], values:[...] },
     *     moving_z_score: { ... },
     *     alpha: { ... },
     *     cumulative_alpha: { ... }
     *   }
     */
async function loadPerformanceDataAndRenderCharts(ticker = 'IBM') {
    console.log(`[loadPerformanceDataAndRenderCharts] For ticker='${ticker}'`);
    let apiData = null;

    try {
        const response = await fetch(`/api/performance_charts?ticker=${ticker}`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        apiData = await response.json();
        if (apiData.error) {
            console.error("[loadPerformanceDataAndRenderCharts] API returns error:", apiData.error);
            apiData = null;
        }
    } catch (error) {
        console.error("[loadPerformanceDataAndRenderCharts] Fetch error:", error);
        apiData = null;
    }

    // Fallback values if no valid API data
    const rpData  = apiData?.relative_performance  || { value: 0, change: 0, dates: [], values: [] };
    const zData   = apiData?.moving_z_score        || { value: 0, change: 0, dates: [], values: [] };
    const aData   = apiData?.alpha                 || { value: 0, change: 0, dates: [], values: [] };
    const caData  = apiData?.cumulative_alpha      || { value: 0, change: 0, dates: [], values: [] };

    // ─── 🔍 Debug raw data for Z-Score ───
    console.log("zData.value (raw):", zData.value);       // e.g. -0.50
    console.log("zData.change (raw):", zData.change);     // e.g. +0.10

    const formatSignedValue = (val, digits = 2, isPercent = false) => {
    const num = typeof val === "string" ? parseFloat(val.replace("%", "")) : val;
    if (isNaN(num)) return isPercent ? "+0.00%" : "+0.00";
    return `${num >= 0 ? "+" : ""}${num.toFixed(digits)}${isPercent ? "%" : ""}`;
    };


    // Format values safely using updated utility
    const rpVal = formatSignedValue(rpData.value, 2, true);   // Relative Performance
    const rpChg = formatSignedValue(rpData.change, 2, true);

    const zVal = formatSignedValue(zData.value, 2);     // Z-Score
    const zChg = formatSignedValue(zData.change, 2);

    const aVal = formatSignedValue(aData.value, 3, false);     // Alpha
    const aChg = formatSignedValue(aData.change, 3, false);

    const caVal = formatSignedValue(caData.value, 2, false);   // Cumulative Alpha
    const caChg = formatSignedValue(caData.change, 2, false);
    // Update text for chart cards
    updateChartCardTextOnly('rp-value', 'rp-change', rpVal, rpChg);
    updateChartCardTextOnly('zscore-value', 'zscore-change', zVal, zChg);
    updateChartCardTextOnly('alpha-value', 'alpha-change', aVal, aChg);
    updateChartCardTextOnly('cumulative-alpha-value', 'cumulative-alpha-change', caVal, caChg);

    // Set current ticker globally for chart titles
    window.currentTicker = ticker;

    // Render the line charts with raw numeric series
    renderChart('relativePerformanceChart',   rpData.values,   rpData.dates,   '#1E90FF');
    renderChart('movingZScoreChart',          zData.values,    zData.dates,    '#FFA500');
    renderChart('alphaChart',                 aData.values,    aData.dates,    '#32CD32');
    renderChart('cumulativeAlphaChart',       caData.values,   caData.dates,   '#9370DB');
}


    /**
     * renderChart(canvasId, data[], labels[], color) 
     * — Defined in charts.js. Draws a Chart.js line on the given <canvas>.
     */
    
    // ─── (A) Initial Load ─────────────────────────────────────────────────────────
    console.log("[main.js] Running initial page load functions.");
    loadFmpArticles();
    loadTickerNews('IBM'); 
    loadPerformanceDataAndRenderCharts('IBM');

    // ─── (B) Wire up “Fetch News” button ─────────────────────────────────────────
    const stockTickerInput = document.getElementById('stock-ticker-input');
    const fetchStockNewsBtn = document.getElementById('fetch-stock-news-btn');

    if (fetchStockNewsBtn && stockTickerInput) {
        fetchStockNewsBtn.addEventListener('click', () => {
            const ticker = stockTickerInput.value.trim().toUpperCase();
            console.log(`[Fetch News] clicked. Ticker='${ticker}'`);
            if (ticker) {
                loadTickerNews(ticker);
                loadPerformanceDataAndRenderCharts(ticker);
            } else {
                const container = document.getElementById('ticker-news-container');
                if (container) container.innerHTML = '<p>Please enter a stock ticker.</p>';
            }
        });
    }

    // ─── (C) Pressing “Enter” in the input triggers the same “click” ──────────────
    if (stockTickerInput) {
        stockTickerInput.addEventListener('keypress', (event) => {
            if (event.key === 'Enter') {
                console.log(`[Enter Key] Pressed in ticker input. Value='${stockTickerInput.value}'`);
                fetchStockNewsBtn.click();
            }
        });
    }

    console.log("[main.js] Initial setup complete. Waiting for user actions.");
});
