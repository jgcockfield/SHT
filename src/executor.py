import time
from py_clob_client.clob_types import OrderArgs, OrderType
from src.logger import log_info, log_error, log_warning, log_trade
from config.settings import (
    MAX_POSITION_SIZE,
    PAPER_TRADING_MODE,
    SELL_TIMEOUT_SECONDS,
    BREAKEVEN_TIMEOUT_SECONDS
)


def place_limit_order(client, token_id, price, size, side):
    """
    Place a limit order on the CLOB.
    side: 'BUY' or 'SELL'
    """
    try:
        if PAPER_TRADING_MODE:
            log_info(
                f"PAPER | {side} | token={token_id[:8]}... | "
                f"price={price} | size={size}"
            )
            return {"paper": True, "price": price, "size": size, "side": side}

        order_args = OrderArgs(
            token_id=token_id,
            price=price,
            size=size,
            side=side,
            order_type=OrderType.LIMIT
        )
        result = client.create_and_post_order(order_args)
        log_info(
            f"EXECUTOR | {side} placed | token={token_id[:8]}... | "
            f"price={price} | size={size}"
        )
        return result

    except Exception as e:
        log_error(f"executor.place_limit_order.{side}", e)
        return None


def execute_mm_trade(client, mm_order):
    """
    Execute market making trade:
    1. Place limit BUY just above best bid
    2. Place limit SELL just below best ask
    3. Wait for fills — profit when both sides fill
    """
    token_id = mm_order["token_id"]
    buy_price = mm_order["buy_price"]
    sell_price = mm_order["sell_price"]
    profit_per_share = mm_order["profit_per_share"]
    size = round(min(MAX_POSITION_SIZE, mm_order["bid_depth"] / 10), 2)
    size = max(size, 5.0)  # minimum 5 USDC

    log_info(
        f"EXECUTOR | MM trade starting | "
        f"token={token_id[:8]}... | "
        f"buy={buy_price} sell={sell_price} | "
        f"size={size} | profit_per_share={profit_per_share}"
    )

    # Place both sides simultaneously
    buy_result = place_limit_order(client, token_id, buy_price, size, "BUY")
    sell_result = place_limit_order(client, token_id, sell_price, size, "SELL")

    if buy_result is None or sell_result is None:
        log_error("executor.execute_mm_trade", "Failed to place one or both orders")
        return

    expected_profit = round(profit_per_share * size, 4)

    log_trade(
        market_id=mm_order["market_id"][:16],
        token_id=token_id,
        buy_price=buy_price,
        sell_price=sell_price,
        spread_at_entry=mm_order["spread"],
        order_size=size,
        profit_expected=expected_profit,
        profit_realized=0,
        exit_type="mm_maker",
        status="placed" if not PAPER_TRADING_MODE else "paper"
    )

    log_info(
        f"EXECUTOR | MM orders live | "
        f"expected_profit={expected_profit} USDC | "
        f"token={token_id[:8]}..."
    )


def execute_trade(client, token_id, orderbook, signal):
    """Compatibility stub."""
    log_warning("execute_trade called directly — use execute_mm_trade")


def execute_arb(client, yes_token, no_token, yes_price, no_price, edge):
    """Compatibility stub."""
    log_warning("execute_arb called directly — use execute_mm_trade")
