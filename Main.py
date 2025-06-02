
# main.py
# ────────────────────────────────────────────────────────────────────────────────

import os
import json
import math
import requests
import certifi
import logging
import pandas as pd   # ← Make sure pandas is imported

from datetime import datetime, timedelta
from urllib.request import urlopen

from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
from dotenv import load_dotenv

# ─── (1) Import your data‐processing helpers from utils.py ───────────────────────
# We assume that in utils.py you have calculate_daily_returns(...) and calculate_alpha_beta(...)
from utils import (
    calculate_daily_returns,   # Compute daily returns from price DataFrame
    calculate_alpha_beta       # Compute rolling alpha & beta from returns DataFrame
)

# ─── (2) Load environment & configure logging ────────────────────────────────────
load_dotenv()
logging.basicConfig(
    format="%(asctime)s %(levelname)s:%(name)s: %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ─── (3) Initialize Flask & CORS ────────────────────────────────────────────────
app = Flask(__name__)
CORS(app)

# ─── (4) Read API keys from .env ─────────────────────────────────────────────────
FMP_API_KEY = os.getenv("FMP_API_KEY")
FMP_API_KEY_EXISTS = bool(FMP_API_KEY)
if not FMP_API_KEY_EXISTS:
    logger.warning("FMP_API_KEY not set: /api_fmp_articles will return mock data.")

# ─── (5) Utility: Fetch JSON via urlopen + certifi ───────────────────────────────
def get_jsonparsed_data(url: str):
    """
    Perform a GET via urllib + certifi, parse the JSON response, and return it.
    Raises on HTTP errors.
    """
    with urlopen(url, cafile=certifi.where()) as resp:
        raw = resp.read().decode("utf-8")
    return json.loads(raw)

# ─── (6) Helper: Get general FMP market articles ─────────────────────────────────
def get_fmp_articles(page: int = 0, size: int = 5) -> dict:
    """
    Returns a JSON object from FMP containing a "content" array of market articles.
    Endpoint:
      https://financialmodelingprep.com/api/v3/fmp/articles?page={page}&size={size}&apikey={FMP_API_KEY}
    """
    url = (
        f"https://financialmodelingprep.com/api/v3/fmp/articles"
        f"?page={page}&size={size}&apikey={FMP_API_KEY}"
    )
    return get_jsonparsed_data(url)

# ─── (7) Helper: Get stock‐specific news from the last 30 days ───────────────────
def search_stock_news(
    tickers: list,
    page: int = 0,
    size: int = 5
) -> list:
    """
    Returns a list of up to `size` news items for `tickers` over the last 30 days:
      GET https://financialmodelingprep.com/api/v3/stock_news with params:
        { tickers, from, to, page, limit, apikey }
    """
    assert tickers, "tickers list must be non‐empty"

    today = datetime.today().date()
    month_ago = today - timedelta(days=30)

    params = {
        "tickers": ",".join([t.upper() for t in tickers]),
        "from":    month_ago.isoformat(),
        "to":      today.isoformat(),
        "page":    page,
        "limit":   size,
        "apikey":  FMP_API_KEY
    }

    resp = requests.get("https://financialmodelingprep.com/api/v3/stock_news", params=params)
    resp.raise_for_status()
    return resp.json()

# ─── (8) Route: Serve index.html ────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")

# ─── (9) Route: /api/fmp_articles?ticker=<optional> ──────────────────────────────
@app.route("/api/fmp_articles")
def api_fmp_articles():
    """
    If `?ticker=XYZ` is provided, return up to 5 stock-specific news items for XYZ (last 30 days),
    adapted so each item has the same shape as the general-articles endpoint
    (each has: title, date, content, image, link, author, site).
    Otherwise, return up to 5 general FMP market articles.
    Falls back to mock data if no FMP_API_KEY or on error.
    """
    ticker = request.args.get("ticker", default=None, type=str)

    if FMP_API_KEY_EXISTS:
        try:
            if not ticker:
                # ── (9.2) GENERAL FMP ARTICLES ─────────────────────────────────
                fmp_response = get_fmp_articles(page=0, size=5)
                # FMP returns a dict with "content" => [ { … }, { … }, … ]
                if isinstance(fmp_response, dict) and "content" in fmp_response:
                    articles_array = fmp_response["content"]
                    if isinstance(articles_array, list) and len(articles_array) > 0:
                        # Return exactly the first 5 items (already shaped correctly)
                        return jsonify(articles_array[:5])
                    else:
                        logger.warning("[api_fmp_articles] FMP returned an empty content array.")
                else:
                    logger.warning("[api_fmp_articles] Unexpected shape from FMP general articles.")
                # If we reach here, we'll fall back to mock below

            else:
                # ── (9.1) STOCK-SPECIFIC NEWS ──────────────────────────────────

                # 1) Call FMP’s stock_news endpoint for last 30 days
                raw_news = search_stock_news([ticker], page=0, size=5)

                adapted = []
                for item in raw_news[:5]:
                    # FMP’s stock_news returns fields: 
                    #   "symbol", "publishedDate", "title", "image", "site", "text", "url"
                    adapted.append({
                        "title":   item.get("title", "").strip(),
                        "date":    item.get("publishedDate", "").strip(),
                        "content": item.get("text", "").strip(),
                        "image":   item.get("image", "").strip(),
                        "link":    item.get("url", "").strip(),
                        # Note: FMP’s stock_news does not return an “author” field.
                        # We’ll leave it empty if unavailable.
                        "author":  "",  
                        "site":    item.get("site", "").strip()
                    })

                # If for some reason FMP returned fewer than 5, this will still return whatever exists
                return jsonify(adapted)

        except Exception as e:
            logger.error(f"[api_fmp_articles] Error fetching from FMP: {e}")

    # ── (9.3) FALLBACK to mock data if no API key or any error ────────────────────
    logger.warning(f"[api_fmp_articles] Returning MOCK fallback (ticker={'None' if not ticker else ticker}).")
    mock_list = []
    for idx in range(5):
        mock_list.append({
            "title":   ticker 
                        and f"Mock News #{idx+1} for {ticker.upper()}"
                        or    f"Mock Market Article #{idx+1}",
            "date":    "2025-01-01 12:00:00",
            "content": ticker 
                        and f"<p>This is a mock-news snippet for {ticker.upper()}. Replace with real snippet when FMP API works.</p>"
                        or    "<p>This is a mock-market article snippet. Replace with real snippet when FMP API works.</p>",
            "image":   "https://portal.financialmodelingprep.com/positions/default.png",
            "link":    "#",
            "author":  ticker and "Mock Author" or "FMP Mock",
            "site":    "mocksource.com"
        })
    return jsonify(mock_list)


# ─── (10) Route: /api/performance_charts?ticker=<optional> ───────────────────────
@app.route("/api/performance_charts")
def api_performance_charts():
    """
    Returns JSON with four keys:  “relative_performance”, “moving_z_score”,
    “alpha”, and “cumulative_alpha”. Each value is an object:
      {
        "value":  "<latest value (string)>",
        "change": "<day‐over‐day change (string)>",
        "dates":  ["YYYY-MM-DD", …],  # last 365 days
        "values": [float, float, …]
      }

    This version does the following:
      1) If no FMP_API_KEY is set, immediately return a 365‐point mock sine/cosine series.
      2) Otherwise, fetch ~500 days of historical prices from FMP’s
         /v3/historical-price-full/{symbol}?timeseries=500&apikey=… for both `ticker` and `SPY`.
      3) Rename FMP’s “close” columns to exactly the symbol names.
      4) Merge on date, trim to the most recent 365 calendar days.
      5) Compute:
         • relative_performance = (ticker / SPY) − 1
         • 23‐day rolling Z‐score of relative_performance
         • 23‐day rolling alpha via calculate_alpha_beta(...)
         • cumulative alpha = running sum of alpha
      6) Build the JSON payload for each metric.
      7) If anything breaks (e.g. missing data, network error), fall back
         to a 365‐point mock sine/cosine series instead of a crash.
    """
    ticker = request.args.get("ticker", default="IBM", type=str).upper()

    # Default “all-zero” structure
    data = {
        "relative_performance": {"value": "+0.00%", "change": "+0.00%", "dates": [], "values": []},
        "moving_z_score":       {"value": "+0.00",  "change": "+0.00",  "dates": [], "values": []},
        "alpha":                {"value": "+0.000","change": "+0.000","dates": [], "values": []},
        "cumulative_alpha":     {"value": "+0.00", "change": "+0.00", "dates": [], "values": []},
    }

    # ── (A) If no FMP key, immediately return 365-point mock sine/cosine wave
    if not FMP_API_KEY_EXISTS:
        logger.warning("[api_performance_charts] No FMP_API_KEY → returning mock series.")
        today = datetime.today()
        dates = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(364, -1, -1)]

        # Generate mock sine/cosine waves
        rel_vals   = [math.sin(2 * math.pi * i / 365) * 5   for i in range(365)]
        z_vals     = [math.cos(2 * math.pi * i / 365) * 1.5 for i in range(365)]
        alpha_vals = [math.sin(2 * math.pi * i / 180) * 0.01 for i in range(365)]
        cum_alpha  = []
        running = 0.0
        for a in alpha_vals:
            running += a
            cum_alpha.append(running)

        data["relative_performance"].update({
            "value":  f"{rel_vals[-1]:+.2f}%",
            "change": f"{(rel_vals[-1] - rel_vals[-2]):+.2f}%",
            "dates":  dates,
            "values": rel_vals
        })
        data["moving_z_score"].update({
            "value":  f"{z_vals[-1]:+.2f}",
            "change": f"{(z_vals[-1] - z_vals[-2]):+.2f}",
            "dates":  dates,
            "values": z_vals
        })
        data["alpha"].update({
            "value":  f"{alpha_vals[-1]:+.3f}",
            "change": f"{(alpha_vals[-1] - alpha_vals[-2]):+.3f}",
            "dates":  dates,
            "values": alpha_vals
        })
        data["cumulative_alpha"].update({
            "value":  f"{cum_alpha[-1]:+.2f}",
            "change": f"{(cum_alpha[-1] - cum_alpha[-2]):+.2f}",
            "dates":  dates,
            "values": cum_alpha
        })
        return jsonify(data)

    # ── (B) Otherwise, attempt to pull real price data from FMP ──────────────────
    try:
        def fetch_historical(symbol: str, timeseries: int = 500) -> list:
            """
            Returns the 'historical' list from:
              GET https://financialmodelingprep.com/api/v3/historical-price-full/{symbol}?timeseries={timeseries}&apikey={FMP_API_KEY}
            """
            url = (
                f"https://financialmodelingprep.com/api/v3/historical-price-full/"
                f"{symbol}?timeseries={timeseries}&apikey={FMP_API_KEY}"
            )
            resp = requests.get(url)
            resp.raise_for_status()
            js = resp.json()
            return js.get("historical", [])

        # 1) Fetch ~500 days of price history for ticker & SPY
        hist_ticker = fetch_historical(ticker, timeseries=500)
        hist_spy    = fetch_historical("SPY",    timeseries=500)
        if not hist_ticker or not hist_spy:
            raise ValueError("Empty historical data for ticker or SPY")

        # 2) Build DataFrames and rename `close` → symbol name (e.g. "IBM" & "SPY")
        df_t = pd.DataFrame(hist_ticker)[["date","close"]].rename(columns={"close": ticker})
        df_s = pd.DataFrame(hist_spy)[["date","close"]].rename(columns={"close": "SPY"})

        # 3) Merge on date, convert to datetime, sort ascending
        df_merge = pd.merge(df_t, df_s, on="date", how="inner")
        df_merge["date"] = pd.to_datetime(df_merge["date"])
        df_merge = df_merge.sort_values("date").reset_index(drop=True)

        # 4) Trim to last ~365 calendar days
        one_year_ago = df_merge["date"].max() - timedelta(days=365)
        df_1y = df_merge[df_merge["date"] >= one_year_ago].reset_index(drop=True)
        if df_1y.shape[0] < 10:
            raise ValueError("Not enough 1-year data; fallback to mock.")

        # 5) Compute relative performance = (ticker / SPY) - 1
        df_1y["rel_perf"] = df_1y[ticker] / df_1y["SPY"] - 1
        dates    = df_1y["date"].dt.strftime("%Y-%m-%d").tolist()
        rel_vals = df_1y["rel_perf"].fillna(0).tolist()

        # 6) Compute 40-day rolling Z-score of rel_perf
        df_1y["zscore"] = (
            df_1y["rel_perf"]
            .subtract(df_1y["rel_perf"].rolling(40).mean())
            .div(df_1y["rel_perf"].rolling(40).std())
        )
        z_vals = df_1y["zscore"].fillna(0).tolist()

        # 7) Compute rolling alpha using calculate_alpha_beta on the full 500-day DF
        df_prices_full = df_merge.copy().rename(columns={ticker: "close1", "SPY": "close2"})
        df_prices_full = df_prices_full[["date","close1","close2"]].rename(
            columns={"close1": ticker, "close2": "SPY"}
        )
        # Now df_prices_full has exactly columns: ["date", "<ticker>", "SPY"]
        df_ret = calculate_daily_returns(df_prices_full, ticker, "SPY")
        df_ab  = calculate_alpha_beta(df_ret, ticker, "SPY", window=30)
        df_ab["date"] = pd.to_datetime(df_ab["date"])
        df_ab_1y = df_ab[df_ab["date"] >= one_year_ago].reset_index(drop=True)
        alpha_vals = df_ab_1y["alpha"].fillna(0).tolist()
        if not alpha_vals:
            raise ValueError("Alpha series is empty; fallback to mock.")

        # 8) Build cumulative alpha (running sum)
        cum_alpha = []
        running = 0.0
        for a in alpha_vals:
            running += a
            cum_alpha.append(running)

        # 9) Fill in JSON for “relative_performance”
        val_rel = rel_vals[-1] * 100
        chg_rel = (rel_vals[-1] - rel_vals[-2]) * 100
        data["relative_performance"].update({
            "value":  f"{val_rel:+.2f}%",
            "change": f"{chg_rel:+.2f}%",
            "dates":  dates,
            "values": rel_vals
        })

        # 10) Fill in JSON for “moving_z_score”
        val_z = z_vals[-1]
        chg_z = z_vals[-1] - z_vals[-2]
        data["moving_z_score"].update({
            "value":  f"{val_z:+.2f}",
            "change": f"{chg_z:+.2f}",
            "dates":  dates,
            "values": z_vals
        })

        # 11) Fill in JSON for “alpha”
        val_alpha = alpha_vals[-1]
        chg_alpha = alpha_vals[-1] - alpha_vals[-2]
        data["alpha"].update({
            "value":  f"{val_alpha:+.3f}",
            "change": f"{chg_alpha:+.3f}",
            "dates":  dates,
            "values": alpha_vals
        })

        # 12) Fill in JSON for “cumulative_alpha”
        val_cum = cum_alpha[-1]
        chg_cum = cum_alpha[-1] - cum_alpha[-2]
        data["cumulative_alpha"].update({
            "value":  f"{val_cum:+.2f}",
            "change": f"{chg_cum:+.2f}",
            "dates":  dates,
            "values": cum_alpha
        })

    except Exception as e:
        # Any error → fall back to mock 365-point sine/cosine
        logger.error(f"[api_performance_charts] Falling back to mock due to error: {e!r}")

        today = datetime.today()
        dates = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(364, -1, -1)]
        rel_vals   = [math.sin(2 * math.pi * i / 365) * 5   for i in range(365)]
        z_vals     = [math.cos(2 * math.pi * i / 365) * 1.5 for i in range(365)]
        alpha_vals = [math.sin(2 * math.pi * i / 180) * 0.01 for i in range(365)]
        cum_alpha  = []
        running = 0.0
        for a in alpha_vals:
            running += a
            cum_alpha.append(running)

        data["relative_performance"].update({
            "value":  f"{rel_vals[-1]:+.2f}%",
            "change": f"{(rel_vals[-1] - rel_vals[-2]):+.2f}%",
            "dates":  dates,
            "values": rel_vals
        })
        data["moving_z_score"].update({
            "value":  f"{z_vals[-1]:+.2f}",
            "change": f"{(z_vals[-1] - z_vals[-2]):+.2f}",
            "dates":  dates,
            "values": z_vals
        })
        data["alpha"].update({
            "value":  f"{alpha_vals[-1]:+.3f}",
            "change": f"{(alpha_vals[-1] - alpha_vals[-2]):+.3f}",
            "dates":  dates,
            "values": alpha_vals
        })
        data["cumulative_alpha"].update({
            "value":  f"{cum_alpha[-1]:+.2f}",
            "change": f"{(cum_alpha[-1] - cum_alpha[-2]):+.2f}",
            "dates":  dates,
            "values": cum_alpha
        })

    return jsonify(data)

# ─── (11) Run Flask app ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    if not FMP_API_KEY_EXISTS:
        print("Warning: FMP_API_KEY is not set; /api_fmp_articles will return mock data.")
    app.run(debug=True, host="0.0.0.0", port=5000)

