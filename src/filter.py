from src.orderbook import get_orderbook, is_tradeable
from src.logger import log_info, log_warning


def get_tradeable_tokens(market):
    """
    Extract tokens from a market and filter for tradeable ones.
    Returns list of tradeable tokens with orderbook data.
    """
    tokens = market.get("tokens", [])

    if not tokens:
        log_warning(
            f"FILTER | No tokens found for market: "
            f"{market.get('question', 'N/A')}"
        )
        return []

    tradeable = []

    for token in tokens:
        token_id = token.get("token_id")
        outcome = token.get("outcome", "N/A")

        if not token_id:
            continue

        orderbook = get_orderbook(token_id)

        if orderbook is None:
            continue

        if not is_tradeable(orderbook):
            log_info(
                f"FILTER | Token skipped: {outcome} | "
                f"token={token_id}"
            )
            continue

        tradeable.append({
            "token_id": token_id,
            "outcome": outcome,
            "orderbook": orderbook
        })

        log_info(
            f"FILTER | Token passed: {outcome} | "
            f"token={token_id} | "
            f"spread={orderbook['spread']} | "
            f"depth={orderbook['bid_depth']:.2f}"
        )

    return tradeable
