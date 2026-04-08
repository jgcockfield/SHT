import time
import requests
from src.logger import log_info, log_warning
from config.settings import CLOB_API_URL

price_history = {}

def get_midpoint(token_id):
    try:
        url = f"{CLOB_API_URL}/book"
        r = requests.get(url, params={"token_id": token_id}, timeout=10)
        r.raise_for_status()
        data = r.json()
        bids = data.get("bids", [])
        asks = data.get("asks", [])
        if not bids or not asks:
            return None
        best_bid = float(bids[0]["price"])
        best_ask = float(asks[0]["price"])
        return round((best_bid + best_ask) / 2, 4)
    except Exception:
        return None

def record_price(token_id, price):
    now = time.time()
    if token_id not in price_history:
        price_history[token_id] = []
    price_history[token_id].append((now, price))
    price_history[token_id] = price_history[token_id][-10:]

def get_momentum(token_id, lookback_seconds=60, min_move=0.02):
    history = price_history.get(token_id, [])
    if len(history) < 2:
        return None
    now = time.time()
    cutoff = now - lookback_seconds
    window = [(t, p) for t, p in history if t >= cutoff]
    if len(window) < 2:
        return None
    oldest_price = window[0][1]
    latest_price = window[-1][1]
    change = latest_price - oldest_price
    if change >= min_move:
        log_info(f"MOMENTUM | UP signal | token={token_id[:8]}... | change={change:+.4f} | from={oldest_price} to={latest_price}")
        return "up"
    elif change <= -min_move:
        log_info(f"MOMENTUM | DOWN signal | token={token_id[:8]}... | change={change:+.4f} | from={oldest_price} to={latest_price}")
        return "down"
    return None

def is_in_discovery_zone(orderbook, min_price=0.10, max_price=0.90):
    mid = (orderbook["best_bid"] + orderbook["best_ask"]) / 2
    return min_price <= mid <= max_price
