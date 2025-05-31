import os
import requests
import logging
import pandas as pd
from datetime import datetime, timedelta

# Configure logger
logger = logging.getLogger(__name__)

ALPHA_VANTAGE_BASE_URL = "https://www.alphavantage.co/query"

def fetch_alpha_vantage_data(function, symbol, interval=None, outputsize='compact'):
    """
    Generic function to fetch data from Alpha Vantage.
    """
    api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
    if not api_key:
        logger.error("ALPHA_VANTAGE_API_KEY environment variable not set.")
        return None

    params = {
        "function": function,
        "symbol": symbol,
        "apikey": api_key,
        "datatype": "json"
    }
    if interval:
        params["interval"] = interval
    if outputsize:
        params["outputsize"] = outputsize

    try:
        response = requests.get(ALPHA_VANTAGE_BASE_URL, params=params)
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
        data = response.json()

        if "Error Message" in data:
            logger.error(f"Alpha Vantage API Error for {symbol} ({function}): {data['Error Message']}")
            return None
        if "Note" in data and "rate limit" in data["Note"].lower():
            logger.warning(f"Alpha Vantage API rate limit hit for {symbol} ({function}).")
            return None
        if not data:
            logger.warning(f"No data returned from Alpha Vantage for {symbol} ({function}).")
            return None

        return data
    except requests.exceptions.RequestException as e:
        logger.error(f"Network or API request error for {symbol} ({function}): {e}")
        return None
    except ValueError as e:
        logger.error(f"JSON decoding error for {symbol} ({function}): {e}")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred while fetching {symbol} ({function}): {e}")
        return None

def fetch_daily_adjusted_data(symbol):
    """
    Fetches daily adjusted stock data for a given symbol.
    Returns a pandas DataFrame.
    """
    logger.info(f"Fetching daily adjusted data for {symbol}...")
    data = fetch_alpha_vantage_data("TIME_SERIES_DAILY_ADJUSTED", symbol, outputsize='full')

    if data and "Time Series (Daily)" in data:
        df = pd.DataFrame.from_dict(data["Time Series (Daily)"], orient='index')
        df = df.rename(columns={
            "1. open": "open",
            "2. high": "high",
            "3. low": "low",
            "4. close": "close",
            "5. adjusted close": "adjusted_close",
            "6. volume": "volume",
            "7. dividend amount": "dividend_amount",
            "8. split coefficient": "split_coefficient"
        })
        df.index = pd.to_datetime(df.index)
        df = df.apply(pd.to_numeric, errors='coerce')
        df = df.sort_index()
        logger.info(f"Successfully fetched daily adjusted data for {symbol}.")
        return df
    logger.warning(f"Could not fetch daily adjusted data for {symbol}.")
    return None

def fetch_company_overview(symbol):
    """
    Fetches company overview data for a given symbol.
    """
    logger.info(f"Fetching company overview for {symbol}...")
    data = fetch_alpha_vantage_data("OVERVIEW", symbol)
    if data:
        logger.info(f"Successfully fetched company overview for {symbol}.")
        return data
    logger.warning(f"Could not fetch company overview for {symbol}.")
    return None

def get_realtime_price(symbol):
    """
    Fetches the latest real-time price for a given symbol.
    Note: Alpha Vantage free tier might not offer true real-time,
    often it's delayed or end-of-day data.
    """
    logger.info(f"Fetching real-time price for {symbol}...")
    data = fetch_alpha_vantage_data("GLOBAL_QUOTE", symbol)
    if data and "Global Quote" in data:
        quote = data["Global Quote"]
        if "05. price" in quote:
            try:
                price = float(quote["05. price"])
                logger.info(f"Real-time price for {symbol}: {price}")
                return price
            except ValueError:
                logger.error(f"Could not parse price for {symbol}: {quote['05. price']}")
                return None
    logger.warning(f"Could not fetch real-time price for {symbol}.")
    return None