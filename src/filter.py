import json
from src.logger import log_info, log_warning


def get_tradeable_tokens(market):
    """
    For mispricing strategy: return both YES and NO tokens
    with their respective buy prices.
    We buy YES at yes_price and NO at no_price.
    At resolution one side pays $1.00 — guaranteed profit.
    """
    raw_ids = market.get("clobTokenIds", "[]")
    if isinstance(raw_ids, str):
        token_ids = json.loads(raw_ids)
    else:
        token_ids = raw_ids

    if len(token_ids) < 2:
        log_warning(
            f"FILTER | Need 2 tokens, found {len(token_ids)} | "
            f"{market.get('question', 'N/A')[:50]}"
        )
        return []

    yes_price = market.get("yes_price")
    no_price = market.get("no_price")
    combined = market.get("combined")
    edge = market.get("edge")
    liquidity = float(market.get("liquidityNum") or 0)

    if yes_price is None or no_price is None:
        log_warning(f"FILTER | Missing price data for {market.get('question', 'N/A')[:50]}")
        return []

    # YES token is index 0, NO token is index 1
    yes_token = token_ids[0]
    no_token = token_ids[1]

    log_info(
        f"FILTER | Tradeable pair found | "
        f"YES={yes_price} token={yes_token[:8]}... | "
        f"NO={no_price} token={no_token[:8]}... | "
        f"combined={combined} | edge={edge:.4f} | liq={liquidity:.0f}"
    )

    orderbook = {
        "best_bid": yes_price,
        "best_ask": 1 - no_price,
        "spread": market.get("spread", 0),
        "bid_depth": liquidity / 2,
        "ask_depth": liquidity / 2,
    }

    return [
        {
            "token_id": yes_token,
            "outcome": "YES",
            "orderbook": orderbook,
            "buy_price": yes_price,
            "signal": "yes_leg"
        },
        {
            "token_id": no_token,
            "outcome": "NO",
            "orderbook": orderbook,
            "buy_price": no_price,
            "signal": "no_leg"
        }
    ]
