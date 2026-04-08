import time
from py_clob_client.clob_types import OrderArgs, OrderType
from src.logger import log_info, log_error, log_warning, log_trade
from config.settings import (
    MAX_POSITION_SIZE,
    PAPER_TRADING_MODE
)


def place_buy(client, token_id, price, size):
    try:
        if PAPER_TRADING_MODE:
            log_info(
                f"PAPER | BUY | token={token_id[:8]}... | "
                f"price={price} | size={size}"
            )
            return {"paper": True, "price": price, "size": size}

        order_args = OrderArgs(
            token_id=token_id,
            price=price,
            size=size,
            side="BUY",
            order_type=OrderType.LIMIT
        )
        result = client.create_and_post_order(order_args)
        log_info(
            f"EXECUTOR | BUY placed | token={token_id[:8]}... | "
            f"price={price} | size={size}"
        )
        return result

    except Exception as e:
        log_error("executor.place_buy", e)
        return None


def execute_arb(client, yes_token, no_token, yes_price, no_price, edge):
    """
    Execute both legs of the binary mispricing trade.
    Buy YES at yes_price and NO at no_price.
    Combined cost < 1.00 — guaranteed profit at resolution.
    """
    size = round(min(MAX_POSITION_SIZE, 25), 2)
    cost = round((yes_price + no_price) * size, 4)
    expected_profit = round((1 - yes_price - no_price) * size, 4)

    log_info(
        f"EXECUTOR | Arb trade | "
        f"YES={yes_price} NO={no_price} | "
        f"size={size} | cost={cost} | "
        f"expected_profit={expected_profit}"
    )

    # Place YES leg
    yes_result = place_buy(client, yes_token, yes_price, size)
    if yes_result is None:
        log_error("executor.execute_arb", "YES leg failed")
        return

    # Place NO leg
    no_result = place_buy(client, no_token, no_price, size)
    if no_result is None:
        log_error("executor.execute_arb", "NO leg failed")
        return

    log_trade(
        market_id=yes_token[:16],
        token_id=yes_token,
        buy_price=yes_price + no_price,
        sell_price=1.0,
        spread_at_entry=edge,
        order_size=size,
        profit_expected=expected_profit,
        profit_realized=0,
        exit_type="arb_hold_to_resolution",
        status="placed" if not PAPER_TRADING_MODE else "paper"
    )


def execute_trade(client, token_id, orderbook, signal):
    """
    Compatibility wrapper — not used in arb strategy.
    """
    log_warning("executor.execute_trade called directly — use execute_arb instead")
