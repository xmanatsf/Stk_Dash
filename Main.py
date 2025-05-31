import os
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
from dotenv import load_dotenv

from src.setup_logger import setup_logging
from src.api_handler import fetch_financial_news, get_stock_alpha, get_stock_zscore, get_relative_performance
from src.stock_data_fetcher import fetch_company_overview

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
CORS(app) # Enable CORS for all routes

# Set up logging for the Flask app
setup_logging()

# Check if API keys are available for real data fetching
NEWS_API_KEY_EXISTS = os.getenv("NEWS_API_KEY") is not None
ALPHA_VANTAGE_API_KEY_EXISTS = os.getenv("ALPHA_VANTAGE_API_KEY") is not None

# --- Frontend Routes ---
@app.route('/')
def index():
    return render_template('index.html')

# --- API Endpoints for Frontend ---

@app.route('/api/market_news')
def api_market_news():
    """Fetches general market news. Uses actual API if keys exist, else mock data."""
    news_items = []
    
    if NEWS_API_KEY_EXISTS:
        try:
            # Fetch news for tech stocks
            tech_news_articles = fetch_financial_news(query="tech stocks earnings reports", limit=1)
            if tech_news_articles:
                news_items.append({
                    "title": tech_news_articles[0].get("title", "Tech Stocks Surge Amidst Positive Earnings Reports"),
                    "description": tech_news_articles[0].get("description", "The technology sector experienced a significant boost today, driven by strong earnings reports from several key players. Investors are optimistic about future growth, leading to increased trading activity and higher stock prices."),
                    "image": tech_news_articles[0].get("urlToImage", "/static/images/stock_chart.png") # Fallback to static image
                })
            else:
                app.logger.warning("No tech news found via API. Using mock.")
                news_items.append({
                    "title": "Tech Stocks Surge Amidst Positive Earnings Reports",
                    "description": "The technology sector experienced a significant boost today, driven by strong earnings reports from several key players. Investors are optimistic about future growth, leading to increased trading activity and higher stock prices.",
                    "image": "/static/images/stock_chart.png"
                })

            # Fetch news for global markets
            global_markets_articles = fetch_financial_news(query="global markets economic policy", limit=1)
            if global_markets_articles:
                news_items.append({
                    "title": global_markets_articles[0].get("title", "Global Markets React to Economic Policy Changes"),
                    "description": global_markets_articles[0].get("description", "Recent shifts in economic policies across major global markets have triggered varied responses from investors. While some regions show resilience, others face uncertainty, impacting international trade and investment flows."),
                    "image": global_markets_articles[0].get("urlToImage", "/static/images/world_map.png") # Fallback to static image
                })
            else:
                app.logger.warning("No global markets news found via API. Using mock.")
                news_items.append({
                    "title": "Global Markets React to Economic Policy Changes",
                    "description": "Recent shifts in economic policies across major global markets have triggered varied responses from investors. While some regions show resilience, others face uncertainty, impacting international trade and investment flows.",
                    "image": "/static/images/world_map.png"
                })
        except Exception as e:
            app.logger.error(f"Error fetching real market news: {e}. Serving mock data.")
            news_items = [
                {
                    "title": "Tech Stocks Surge Amidst Positive Earnings Reports",
                    "description": "The technology sector experienced a significant boost today, driven by strong earnings reports from several key players. Investors are optimistic about future growth, leading to increased trading activity and higher stock prices.",
                    "image": "/static/images/stock_chart.png"
                },
                {
                    "title": "Global Markets React to Economic Policy Changes",
                    "description": "Recent shifts in economic policies across major global markets have triggered varied responses from investors. While some regions show resilience, others face uncertainty, impacting international trade and investment flows.",
                    "image": "/static/images/world_map.png"
                }
            ]
    else:
        app.logger.warning("NEWS_API_KEY not set. Serving mock market news data.")
        news_items = [
            {
                "title": "Tech Stocks Surge Amidst Positive Earnings Reports",
                "description": "The technology sector experienced a significant boost today, driven by strong earnings reports from several key players. Investors are optimistic about future growth, leading to increased trading activity and higher stock prices.",
                "image": "/static/images/stock_chart.png"
            },
            {
                "title": "Global Markets React to Economic Policy Changes",
                "description": "Recent shifts in economic policies across major global markets have triggered varied responses from investors. While some regions show resilience, others face uncertainty, impacting international trade and investment flows.",
                "image": "/static/images/world_map.png"
            }
        ]
    return jsonify(news_items)

@app.route('/api/stock_specific_news')
def api_stock_specific_news():
    """Fetches news for a specific stock ticker. Uses actual API if keys exist, else mock data."""
    ticker = request.args.get('ticker', 'XYZ').upper() # Default for UI example

    if not ticker:
        return jsonify({"error": "Ticker parameter is required"}), 400

    news_item_data = {}
    if NEWS_API_KEY_EXISTS:
        try:
            company_name = f"{ticker} Corporation"
            # Try to get company overview for real name
            company_overview = fetch_company_overview(ticker)
            if company_overview and company_overview.get('Name'):
                company_name = company_overview['Name']
            
            news_articles = fetch_financial_news(query=f"{ticker} earnings", limit=1)

            if news_articles:
                news_item_data = {
                    "title": news_articles[0].get("title", f"{company_name} News Update"),
                    "description": news_articles[0].get("description", f"Recent news about {company_name}."),
                    "image": news_articles[0].get("urlToImage", "/static/images/xyz_logo.png")
                }
            else: # Fallback if no specific news from API
                app.logger.warning(f"No specific news found for {ticker} via API. Using generic mock.")
                news_item_data = {
                    "title": f"{company_name} Announces Quarterly Update",
                    "description": f"{company_name} reported its latest quarterly results. The company's performance reflects current market conditions and strategic initiatives.",
                    "image": "/static/images/xyz_logo.png"
                }
        except Exception as e:
            app.logger.error(f"Error fetching real stock specific news for {ticker}: {e}. Serving mock data.")
            # Fallback to hardcoded XYZ mock or generic if API fails
            pass # Continue to the general mock section
    
    # If API key not set, or if API call failed, serve mock data
    if not NEWS_API_KEY_EXISTS or not news_item_data:
        app.logger.warning("NEWS_API_KEY not set or API call failed. Serving mock stock specific news data.")
        # Always serve the specific UI text for XYZ, otherwise a generic one
        if ticker == 'XYZ':
            news_item_data = {
                "title": f"{ticker.upper()} Corporation Announces Record Quarterly Profits",
                "description": f"{ticker.upper()} Corporation reported its highest quarterly profits to date, exceeding analyst expectations. The company's success is attributed to increased sales and effective cost management, boosting investor confidence.",
                "image": "/static/images/xyz_logo.png"
            }
        else:
             news_item_data = {
                "title": f"{ticker.upper()} News Update",
                "description": f"No specific news found for {ticker.upper()}. Here is a generic update.",
                "image": "/static/images/xyz_logo.png"
            }

    return jsonify(news_item_data)

@app.route('/api/performance_charts')
def api_performance_charts():
    """Provides current performance metrics. Uses actual API if keys exist, else mock data."""
    ticker = request.args.get('ticker', 'IBM').upper() # Default to a real ticker for potential backend calls

    # Default mock data (from UI design)
    data = {
        "relative_performance": {"value": "+5.2%", "change": "+1.5%"},
        "moving_z_score": {"value": "1.8", "change": "-0.2"},
        "alpha": {"value": "0.03", "change": "+0.01"},
        "cumulative_alpha": {"value": "0.15", "change": "+0.05"},
    }

    if ALPHA_VANTAGE_API_KEY_EXISTS:
        try:
            # Fetch real data for current values if possible
            alpha_val = get_stock_alpha(ticker)
            if alpha_val is not None:
                data["alpha"]["value"] = f"{alpha_val:.2f}"
                # Change value remains hardcoded as your backend does not provide historical change

            zscore_val = get_stock_zscore(ticker)
            if zscore_val is not None:
                data["moving_z_score"]["value"] = f"{zscore_val:.1f}"

            relative_perf_val = get_relative_performance(ticker)
            if relative_perf_val is not None:
                data["relative_performance"]["value"] = f"{relative_perf_val:.1f}%" if relative_perf_val < 0 else f"+{relative_perf_val:.1f}%"

            # Cumulative Alpha is not directly exposed as a single value from your backend functions.
            # Keeping it hardcoded for UI consistency.

        except Exception as e:
            app.logger.error(f"Error fetching real performance data for {ticker}: {e}. Serving mock data.")
    else:
        app.logger.warning("ALPHA_VANTAGE_API_KEY not set. Serving mock performance data.")

    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True)
