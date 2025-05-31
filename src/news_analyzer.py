import logging
from newsapi import NewsApiClient # Make sure 'newsapi-python' is in requirements.txt
import os
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

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

def fetch_financial_news(query, language='en', sort_by='relevancy', limit=5):
    """
    Fetches financial news articles using the News API.
    
    Args:
        query (str): The search query (e.g., "tech stocks", "TSLA earnings").
        language (str): Language of the news (e.g., 'en', 'es').
        sort_by (str): How to sort the articles ('relevancy', 'popularity', 'publishedAt').
        limit (int): Maximum number of articles to return.

    Returns:
        list: A list of dictionaries, each representing a news article.
              Returns an empty list if API key is missing or an error occurs.
    """
    api_key = os.getenv("NEWS_API_KEY")
    if not api_key:
        logger.error("NEWS_API_KEY environment variable not set. Cannot fetch news.")
        return []

    newsapi = NewsApiClient(api_key=api_key)
    
    # Calculate dates for the last 30 days
    to_date = datetime.now().strftime('%Y-%m-%d')
    from_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

    try:
        # Using 'everything' endpoint for more specific queries
        articles = newsapi.get_everything(
            q=query,
            language=language,
            sort_by=sort_by,
            from_param=from_date,
            to=to_date,
            page_size=limit # Number of results per page
        )

        if articles and articles['status'] == 'ok':
            logger.info(f"Successfully fetched {len(articles['articles'])} news articles for query: '{query}'")
            return articles['articles']
        else:
            logger.warning(f"News API returned status: {articles.get('status')} or no articles for query: '{query}'")
            if 'message' in articles:
                logger.error(f"News API error message: {articles['message']}")
            return []
    except Exception as e:
        logger.error(f"Error fetching news for query '{query}': {e}")
        return []