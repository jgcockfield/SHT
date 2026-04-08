import time
import requests
from src.logger import log_info
from config.settings import CLOB_API_URL

price_history = {}

def get_clob_midpoint(token_id):
    try:
        r = requests.get(
            f"{CLOB_API_URL}/book",
            params={"token_id": token_id},
            timeout=10
        )
        r.raise_for_status()
        data = r.json()
        bids = data.get("bids", [])
        asks = data.get("asks", [])
        if not bids or not asks:
            return None
        return round((float(bids[0]["price"]) + float(asks[0]["price"])) / 2, 4)
    except Exception:
        return None

def record_price(token_id, gamma_mid):
    now = time.time()
    clob_mid = get_clob_midpoint(token_id)
    price = clob_mid if clob_mid is not None else gamma_mid
    if token_id not in price_history:
        price_history[token_id] = []
    price_history[token_id].append((now, price))
    price_history[token_id] = price_history[token_id][-20:]

def get_momentum(token_id, lookback_seconds=60, min_move=0.005):
    history = price_history.get(token_id, [])
    if len(history) < 2:
        return None
    now = time.time()
    cutoff = now - lookback_seconds
    window = [(t, p) for t, p in history if t >= cutoff]
    if len(window) < 2:
        return None
    oldest = window[0][1]
    latest = window[-1][1]
    change = latest - oldest
    if change >= min_move:
        log_info(
            f"MOMENTUM | UP | token={token_id[:8]}... | "
            f"{oldest} -> {latest} | change={change:+.4f}"
        )
        return "up"
    elif change <= -min_move:
        log_info(
            f"MOMENTUM | DOWN | token={token_id[:8]}... | "
            f"{oldest} -> {latest} | change={change:+.4f}"
        )
        return "down"
    return None

def is_in_discovery_zone(orderbook, min_price=0.35, max_price=0.65):
    mid = (orderbook["best_bid"] + orderbook["best_ask"]) / 2
    return min_price <= mid <= max_price
