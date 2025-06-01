import logging
import requests # Using requests for FMP news
import os
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)
FMP_BASE_URL = "https://financialmodelingprep.com/api"

def get_fmp_api_key():
    """Retrieves the FMP API key from environment variables."""
    api_key = os.getenv("FMP_API_KEY")
    if not api_key:
        logger.error("FMP_API_KEY environment variable not set.")
    return api_key

def analyze_sentiment(text):
    """
    A very basic sentiment analysis. For a real application,
    integrate with a dedicated NLP sentiment model (e.g., NLTK, TextBlob, Hugging Face).
    This is a placeholder.
    """
    if not isinstance(text, str):
        return "neutral"
    
    text_lower = text.lower()
    positive_keywords = ["gain", "rise", "grow", "profit", "success", "optimistic", "boost", "exceed", "strong"]
    negative_keywords = ["fall", "drop", "lose", "decline", "miss", "uncertainty", "impact", "risk"]

    pos_count = sum(1 for kw in positive_keywords if kw in text_lower)
    neg_count = sum(1 for kw in negative_keywords if kw in text_lower)

    if pos_count > neg_count:
        return "positive"
    elif neg_count > pos_count:
        return "negative"
    else:
        return "neutral"

def fetch_financial_news_fmp(query_or_tickers, news_type="stock_news", limit=5, page=0):
    """
    Fetches financial news articles using the FMP API.

    Args:
        query_or_tickers (str or list): Stock ticker(s) as string (e.g., "AAPL") or list (e.g., ["AAPL", "MSFT"])
                                       or a general query string if news_type is 'fmp_articles'.
        news_type (str): "stock_news" for ticker-specific news, 
                         "fmp_articles" for general FMP articles.
        limit (int): Maximum number of articles to return.
        page (int): Page number for pagination (for stock_news).

    Returns:
        list: A list of dictionaries, each representing a news article.
              Returns an empty list if API key is missing or an error occurs.
    """
    api_key = get_fmp_api_key()
    if not api_key:
        return []

    articles_data = []

    if news_type == "stock_news":
        if not query_or_tickers:
            logger.warning("Tickers are required for stock_news type.")
            return []
        
        tickers_str = ",".join(query_or_tickers) if isinstance(query_or_tickers, list) else query_or_tickers
        # FMP stock_news endpoint often works best with specific tickers.
        # The 'query' parameter in the original Main.py for NewsAPI was more general.
        # For FMP, we'll use the tickers parameter for stock_news.
        # The 'query' in the Flask app might need to be interpreted as a ticker.
        
        # For stock_news, FMP API has 'limit' and 'page' parameters.
        # It also has 'from' and 'to' date parameters.
        today = datetime.today().date()
        thirty_days_ago = today - timedelta(days=30)
        
        url = f"{FMP_BASE_URL}/v3/stock_news"
        params = {
            "tickers": tickers_str,
            "limit": limit,
            "page": page, # FMP uses 'page' for pagination
            "from": thirty_days_ago.isoformat(),
            "to": today.isoformat(),
            "apikey": api_key
        }
        logger.info(f"Fetching stock news for tickers: '{tickers_str}' from FMP with params: {params}")

    elif news_type == "fmp_articles":
        # General FMP articles, 'query_or_tickers' can be a general search term if supported,
        # or ignored if the endpoint primarily provides latest articles.
        # The FMP /fmp/articles endpoint uses 'page' and 'size'.
        url = f"{FMP_BASE_URL}/v3/fmp/articles"
        params = {
            "page": page,
            "size": limit, # FMP uses 'size' for fmp/articles
            "apikey": api_key
        }
        # Note: 'query_or_tickers' is not directly used as a query param for /fmp/articles
        # This endpoint typically returns general financial news.
        logger.info(f"Fetching general FMP articles with params: {params}")
    else:
        logger.error(f"Unsupported news_type: {news_type}")
        return []

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        if isinstance(data, list): # FMP usually returns a list of articles
            articles_data = data
            # Adapt FMP article structure to a common structure if needed,
            # e.g., ensuring 'title', 'description', 'urlToImage' (or equivalents)
            # FMP stock_news fields: symbol, publishedDate, title, image, site, text, url
            # FMP fmp/articles fields: title, content, image, date, source, link, symbols
            
            processed_articles = []
            for article in articles_data:
                # Heuristic to map fields to what the frontend might expect
                # NewsAPI used: title, description, urlToImage
                # FMP stock_news: title, text (as description), image (as urlToImage)
                # FMP fmp/articles: title, content (as description), image (as urlToImage)
                
                title = article.get("title", "No Title")
                description = article.get("text") or article.get("content", "No description available.")
                image_url = article.get("image", "") # FMP provides 'image'
                
                # Ensure image_url is a valid URL, not a placeholder like "N/A" if FMP does that
                if not image_url or not image_url.startswith(('http://', 'https://')):
                    image_url = None # Set to None if invalid, frontend can use a fallback

                processed_articles.append({
                    "title": title,
                    "description": description,
                    "urlToImage": image_url, # Map FMP's 'image' to 'urlToImage'
                    "publishedAt": article.get("publishedDate") or article.get("date"),
                    "source_name": article.get("site") or article.get("source"),
                    "url": article.get("url") or article.get("link")
                })
            articles_data = processed_articles

            logger.info(f"Successfully fetched {len(articles_data)} news articles from FMP ({news_type}).")
        elif isinstance(data, dict) and "Error Message" in data:
            logger.error(f"FMP API Error for news ({news_type}): {data['Error Message']}")
            return []
        else:
            logger.warning(f"News from FMP ({news_type}) returned unexpected data type or empty: {type(data)}")
            return []

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching news from FMP ({news_type}): {e}")
        return []
    except ValueError as e: # Includes JSONDecodeError
        logger.error(f"JSON decoding error for news from FMP ({news_type}): {e}")
        return []
    except Exception as e:
        logger.error(f"An unexpected error occurred while fetching news from FMP ({news_type}): {e}")
        return []
        
    return articles_data

# For compatibility with existing Main.py, which calls fetch_financial_news
# The original fetch_financial_news took a 'query'. We need to decide how to map this.
# If the query is a ticker, use "stock_news". If general, use "fmp_articles".
# For simplicity, let's assume the query can be a ticker or a list of tickers for "stock_news".
# The Flask app's /api/market_news uses general queries, /api/stock_specific_news uses a ticker.

def fetch_financial_news(query, limit=5, news_type_hint=None):
    """
    Wrapper to decide which FMP news function to call based on query.
    `news_type_hint` can be 'stock_news' or 'fmp_articles'.
    If query looks like a ticker (e.g. "AAPL", "MSFT,GOOG"), use stock_news.
    Otherwise, or if news_type_hint is 'fmp_articles', use fmp_articles.
    """
    # Basic heuristic: if query is short, all caps, no spaces, assume it's a ticker or list of tickers
    is_ticker_like = isinstance(query, str) and query.replace(',', '').isalnum() and query.isupper() and ' ' not in query
    
    if news_type_hint == "stock_news" or (news_type_hint is None and is_ticker_like):
        # If query is "tech stocks earnings reports", this won't be treated as ticker.
        # The Flask app needs to be more specific or this function needs better routing.
        # For now, if it's ticker-like, pass it directly.
        # If it's a general query intended for stock news, FMP might not support it well via /stock_news.
        # The original Main_original.py uses search_stock_news with tickers.
        # And get_fmp_articles for general news.
        
        # Let's refine: Main.py calls fetch_financial_news(query="tech stocks earnings reports") for market_news
        # and fetch_financial_news(query=f"{ticker} earnings") for stock_specific_news.
        # FMP's /stock_news is ticker-based. FMP's /fmp/articles is general.
        
        # If a specific ticker is in the query for stock_specific_news, extract it.
        # For market_news, use fmp_articles.
        
        if news_type_hint == "stock_news": # Explicitly for a ticker
            return fetch_financial_news_fmp(query_or_tickers=query, news_type="stock_news", limit=limit)
        else: # General query for market news
             # FMP's /fmp/articles doesn't take a query string in the same way NewsAPI did.
             # It returns general articles. The `query` param here will be ignored by fetch_financial_news_fmp for 'fmp_articles'.
            logger.info(f"Fetching general market news (fmp_articles). Original query '{query}' will be ignored by FMP endpoint.")
            return fetch_financial_news_fmp(query_or_tickers=None, news_type="fmp_articles", limit=limit)

    elif news_type_hint == "fmp_articles" or (news_type_hint is None and not is_ticker_like):
        logger.info(f"Fetching general market news (fmp_articles) for query: '{query}'. Query will be ignored by FMP endpoint.")
        return fetch_financial_news_fmp(query_or_tickers=None, news_type="fmp_articles", limit=limit)
    else: # Fallback or if query is a ticker string
        return fetch_financial_news_fmp(query_or_tickers=query, news_type="stock_news", limit=limit)

