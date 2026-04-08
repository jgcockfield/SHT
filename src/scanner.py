import requests
from src.logger import log_info, log_error
from config.settings import CLOB_API_URL, GAMMA_API_URL


def get_market_candidates():
    """
    Find markets with real CLOB liquidity on both sides.
    Uses Gamma API to get candidate markets, then validates
    against actual CLOB orderbook data.
    """
    try:
        url = f"{GAMMA_API_URL}/markets"
        params = {
            "active": "true",
            "closed": "false",
            "limit": 100,
            "order": "volume24hr",
            "ascending": "false"
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        markets = response.json()

        qualifying = []

        for market in markets:
            try:
                liquidity = float(market.get("liquidityNum") or 0)
                volume = float(market.get("volume24hr") or 0)
                accepting = market.get("acceptingOrders", False)

                if not accepting:
                    continue
                if liquidity < 5000:
                    continue
                if volume < 500:
                    continue

                qualifying.append(market)

            except (KeyError, ValueError) as e:
                log_error("scanner.parse_market", e)
                continue

        log_info(
            f"SCANNER | {len(qualifying)} candidate markets found"
        )
        return qualifying

    except requests.RequestException as e:
        log_error("scanner.get_market_candidates", e)
        return []


def get_clob_orderbook(token_id):
    """
    Fetch real CLOB orderbook for a token.
    Returns orderbook dict or None.
    """
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

        best_bid = float(bids[0]["price"])
        best_ask = float(asks[0]["price"])
        spread = round(best_ask - best_bid, 4)

        bid_depth = sum(float(b["size"]) for b in bids[:5])
        ask_depth = sum(float(a["size"]) for a in asks[:5])

        return {
            "token_id": token_id,
            "best_bid": best_bid,
            "best_ask": best_ask,
            "spread": spread,
            "bid_depth": bid_depth,
            "ask_depth": ask_depth,
            "bids": bids[:5],
            "asks": asks[:5]
        }

    except Exception as e:
        log_error("scanner.get_clob_orderbook", e)
        return None


def find_market_making_opportunities():
    """
    Find tokens with real two-sided CLOB liquidity and
    profitable spread for market making.
    Min spread: 0.04 (4 cents) to ensure profit after
    two limit orders.
    """
    candidates = get_market_candidates()
    opportunities = []

    for market in candidates:
        import json
        raw_ids = market.get("clobTokenIds", "[]")
        if isinstance(raw_ids, str):
            token_ids = json.loads(raw_ids)
        else:
            token_ids = raw_ids

        for token_id in token_ids:
            ob = get_clob_orderbook(token_id)

            if ob is None:
                continue

            # Need real two-sided liquidity
            if ob["bid_depth"] < 100:
                continue
            if ob["ask_depth"] < 100:
                continue

            # Need meaningful spread to profit from
            if ob["spread"] < 0.04:
                continue

            # Price must be in active trading zone
            mid = (ob["best_bid"] + ob["best_ask"]) / 2
            if not (0.10 <= mid <= 0.90):
                continue

            ob["market_question"] = market.get("question", "N/A")[:50]
            ob["market_id"] = market.get("id", "")
            opportunities.append(ob)

            log_info(
                f"SCANNER | MM opportunity: "
                f"{ob['market_question']} | "
                f"bid={ob['best_bid']} ask={ob['best_ask']} "
                f"spread={ob['spread']} | "
                f"bid_depth={ob['bid_depth']:.0f} "
                f"ask_depth={ob['ask_depth']:.0f}"
            )

    log_info(f"SCANNER | {len(opportunities)} MM opportunities found")
    return opportunities
