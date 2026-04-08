import requests
from src.logger import log_info, log_error, log_warning
from config.settings import (
    CLOB_API_URL,
    MAX_SPREAD_THRESHOLD,
    MIN_LIQUIDITY_THRESHOLD
)


def get_orderbook(token_id):
    """
    Fetch orderbook for a given token ID.
    Returns best bid, best ask, spread and liquidity depth.
    """
    try:
        url = f"{CLOB_API_URL}/book"
        params = {"token_id": token_id}

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        bids = data.get("bids", [])
        asks = data.get("asks", [])

        if not bids or not asks:
            log_warning(f"ORDERBOOK | No bids or asks for token {token_id}")
            return None

        best_bid = float(bids[0]["price"])
        best_ask = float(asks[0]["price"])
        spread = round(best_ask - best_bid, 6)

        # Calculate liquidity depth
        bid_depth = sum(float(b["size"]) for b in bids)
        ask_depth = sum(float(a["size"]) for a in asks)

        log_info(
            f"ORDERBOOK | token={token_id} | "
            f"bid={best_bid} | ask={best_ask} | "
            f"spread={spread} | "
            f"bid_depth={bid_depth:.2f} | ask_depth={ask_depth:.2f}"
        )

        return {
            "token_id": token_id,
            "best_bid": best_bid,
            "best_ask": best_ask,
            "spread": spread,
            "bid_depth": bid_depth,
            "ask_depth": ask_depth
        }

    except requests.RequestException as e:
        log_error("orderbook.get_orderbook", e)
        return None


def is_tradeable(orderbook):
    """
    Check if a market passes spread and liquidity filters.
    """
    if orderbook is None:
        return False

    spread = orderbook["spread"]
    bid_depth = orderbook["bid_depth"]

    if spread > MAX_SPREAD_THRESHOLD:
        log_warning(
            f"FILTER | Spread too wide: {spread} > {MAX_SPREAD_THRESHOLD}"
        )
        return False

    if bid_depth < MIN_LIQUIDITY_THRESHOLD:
        log_warning(
            f"FILTER | Insufficient liquidity: {bid_depth} < {MIN_LIQUIDITY_THRESHOLD}"
        )
        return False

    # Also require minimum liquidity on both sides
    ask_depth = orderbook.get("ask_depth", 0)
    if ask_depth < MIN_LIQUIDITY_THRESHOLD:
        log_warning(
            f"FILTER | Insufficient ask depth: {ask_depth} < {MIN_LIQUIDITY_THRESHOLD}"
        )
        return False

    return True
