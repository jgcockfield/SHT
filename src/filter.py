from src.logger import log_info


def get_mm_orders(opportunity):
    """
    Calculate market making order prices for a token.
    Places buy order just above best bid (to get filled first)
    and sell order just below best ask.
    Profit = sell_price - buy_price per share filled.
    """
    best_bid = opportunity["best_bid"]
    best_ask = opportunity["best_ask"]
    spread = opportunity["spread"]
    tick = 0.01

    # Place buy one tick above best bid
    buy_price = round(best_bid + tick, 2)

    # Place sell one tick below best ask
    sell_price = round(best_ask - tick, 2)

    # Verify still profitable after tick adjustments
    if sell_price <= buy_price:
        log_info(
            f"FILTER | Spread too tight after tick adjustment | "
            f"buy={buy_price} sell={sell_price}"
        )
        return None

    profit_per_share = round(sell_price - buy_price, 4)
    profit_pct = round(profit_per_share / buy_price * 100, 2)

    log_info(
        f"FILTER | MM orders calculated | "
        f"token={opportunity['token_id'][:8]}... | "
        f"buy={buy_price} sell={sell_price} | "
        f"profit_per_share={profit_per_share} ({profit_pct}%)"
    )

    return {
        "token_id": opportunity["token_id"],
        "market_question": opportunity["market_question"],
        "market_id": opportunity["market_id"],
        "buy_price": buy_price,
        "sell_price": sell_price,
        "profit_per_share": profit_per_share,
        "profit_pct": profit_pct,
        "spread": spread,
        "bid_depth": opportunity["bid_depth"],
        "ask_depth": opportunity["ask_depth"]
    }
