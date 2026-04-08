import json
from src.momentum import record_price, get_momentum, is_in_discovery_zone
from src.logger import log_info, log_warning


def get_tradeable_tokens(market):
    """
    Extract tokens from market using Gamma API data.
    Uses bestBid/bestAsk from Gamma directly — no CLOB orderbook call.
    Applies momentum filter before passing to executor.
    """
    raw_ids = market.get("clobTokenIds", "[]")
    if isinstance(raw_ids, str):
        token_ids = json.loads(raw_ids)
    else:
        token_ids = raw_ids

    if not token_ids:
        log_warning(
            f"FILTER | No token IDs for market: "
            f"{market.get('question', 'N/A')}"
        )
        return []

    best_bid = float(market.get("bestBid") or 0)
    best_ask = float(market.get("bestAsk") or 0)
    spread = float(market.get("spread") or 1)
    liquidity = float(market.get("liquidityNum") or 0)

    # Build orderbook-compatible dict from Gamma data
    orderbook = {
        "best_bid": best_bid,
        "best_ask": best_ask,
        "spread": spread,
        "bid_depth": liquidity / 2,
        "ask_depth": liquidity / 2,
    }

    # Check discovery zone
    if not is_in_discovery_zone(orderbook):
        log_info(
            f"FILTER | Market outside discovery zone | "
            f"bid={best_bid} | "
            f"{market.get('question', 'N/A')[:50]}"
        )
        return []

    tradeable = []

    for i, token_id in enumerate(token_ids):
        outcome = f"outcome_{i}"

        # Record price for momentum tracking
        mid = (best_bid + best_ask) / 2
        record_price(token_id, mid)

        # Check momentum signal
        signal = get_momentum(token_id)

        if signal is None:
            log_info(
                f"FILTER | Building momentum history | "
                f"outcome={outcome} | token={token_id[:8]}..."
            )
            continue

        tradeable.append({
            "token_id": token_id,
            "outcome": outcome,
            "orderbook": orderbook,
            "signal": signal
        })

        log_info(
            f"FILTER | Token passed | outcome={outcome} | "
            f"token={token_id[:8]}... | "
            f"signal={signal} | "
            f"spread={spread:.3f} | liq={liquidity:.0f}"
        )

    return tradeable
