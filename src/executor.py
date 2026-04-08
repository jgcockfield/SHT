import time
from py_clob_client.clob_types import OrderArgs, OrderType
from src.logger import log_info, log_error, log_warning, log_trade
from config.settings import (
    PROFIT_BUFFER,
    SELL_TIMEOUT_SECONDS,
    BREAKEVEN_TIMEOUT_SECONDS,
    MAX_POSITION_SIZE,
    PAPER_TRADING_MODE
)


def place_buy(client, token_id, price, size):
    """
    Place a limit buy order.
    In paper trading mode, simulates the order without submitting.
    """
    try:
        if PAPER_TRADING_MODE:
            log_info(
                f"PAPER | BUY | token={token_id} | "
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
            f"EXECUTOR | BUY placed | token={token_id} | "
            f"price={price} | size={size} | result={result}"
        )
        return result

    except Exception as e:
        log_error("executor.place_buy", e)
        return None


def place_sell(client, token_id, price, size):
    """
    Place a limit sell order.
    In paper trading mode, simulates the order without submitting.
    """
    try:
        if PAPER_TRADING_MODE:
            log_info(
                f"PAPER | SELL | token={token_id} | "
                f"price={price} | size={size}"
            )
            return {"paper": True, "price": price, "size": size}

        order_args = OrderArgs(
            token_id=token_id,
            price=price,
            size=size,
            side="SELL",
            order_type=OrderType.LIMIT
        )
        result = client.create_and_post_order(order_args)
        log_info(
            f"EXECUTOR | SELL placed | token={token_id} | "
            f"price={price} | size={size} | result={result}"
        )
        return result

    except Exception as e:
        log_error("executor.place_sell", e)
        return None


def execute_trade(client, token_id, orderbook):
    """
    Full trade execution flow:
    1. Place buy at best ask
    2. Place sell at buy_price + profit_buffer
    3. Apply break-even fallback if sell times out
    """
    best_ask = orderbook["best_ask"]
    best_bid = orderbook["best_bid"]
    spread = orderbook["spread"]
    size = min(MAX_POSITION_SIZE, orderbook["ask_depth"])
    size = round(size, 2)

    buy_price = best_ask
    sell_price = round(buy_price + PROFIT_BUFFER, 4)
    break_even = buy_price

    log_info(
        f"EXECUTOR | Starting trade | token={token_id} | "
        f"buy={buy_price} | sell={sell_price} | size={size}"
    )

    # Place buy
    buy_result = place_buy(client, token_id, buy_price, size)

    if buy_result is None:
        log_error("executor.execute_trade", "Buy order failed")
        return

    # Simulate fill in paper mode
    if PAPER_TRADING_MODE:
        log_info(f"PAPER | Buy filled at {buy_price}")
        filled = True
    else:
        filled = check_fill(client, buy_result, timeout=60)

    if not filled:
        log_warning(f"EXECUTOR | Buy not filled | token={token_id}")
        return

    # Place profit-buffer sell
    sell_result = place_sell(client, token_id, sell_price, size)
    exit_type = "profit_buffer"

    # Wait for sell fill
    if PAPER_TRADING_MODE:
        log_info(f"PAPER | Sell simulated at {sell_price}")
        sell_filled = True
    else:
        sell_filled = check_fill(
            client, sell_result, timeout=SELL_TIMEOUT_SECONDS
        )

    # Break-even fallback
    if not sell_filled:
        log_warning(
            f"EXECUTOR | Sell timeout | Dropping to break-even | "
            f"token={token_id}"
        )
        cancel_order(client, sell_result)
        sell_result = place_sell(client, token_id, break_even, size)
        exit_type = "break_even"

        sell_filled = check_fill(
            client, sell_result, timeout=BREAKEVEN_TIMEOUT_SECONDS
        )

        if not sell_filled:
            log_warning(
                f"EXECUTOR | Break-even not filled | "
                f"Flagging for manual review | token={token_id}"
            )
            exit_type = "unresolved"

    # Calculate profit
    actual_sell = sell_price if exit_type == "profit_buffer" else break_even
    profit_expected = round((sell_price - buy_price) * size, 4)
    profit_realized = round(
        (actual_sell - buy_price) * size, 4
    ) if sell_filled else 0

    log_trade(
        market_id="N/A",
        token_id=token_id,
        buy_price=buy_price,
        sell_price=actual_sell,
        spread_at_entry=spread,
        order_size=size,
        profit_expected=profit_expected,
        profit_realized=profit_realized,
        exit_type=exit_type,
        status="filled" if sell_filled else "unresolved"
    )


def check_fill(client, order_result, timeout=60):
    """
    Poll order status until filled or timeout.
    """
    if order_result is None:
        return False

    order_id = order_result.get("orderID") or order_result.get("id")
    if not order_id:
        return False

    start = time.time()
    while time.time() - start < timeout:
        try:
            status = client.get_order(order_id)
            if status.get("status") == "MATCHED":
                return True
        except Exception as e:
            log_error("executor.check_fill", e)
        time.sleep(5)

    return False


def cancel_order(client, order_result):
    """
    Cancel an open order.
    """
    if PAPER_TRADING_MODE or order_result is None:
        return

    try:
        order_id = order_result.get("orderID") or order_result.get("id")
        if order_id:
            client.cancel_order(order_id)
            log_info(f"EXECUTOR | Order cancelled | id={order_id}")
    except Exception as e:
        log_error("executor.cancel_order", e)
