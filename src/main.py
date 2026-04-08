import time
from src.logger import log_info, log_warning, log_error
from src.scanner import find_market_making_opportunities
from src.filter import get_mm_orders
from src.executor import execute_mm_trade
from src.wallet import get_client, has_sufficient_balance
from config.settings import (
    SCAN_INTERVAL_SECONDS,
    MAX_POSITION_SIZE,
    PAPER_TRADING_MODE
)


def main():
    log_info("=" * 60)
    log_info("SHT - Market Making Agent Starting")
    log_info(f"Mode: {'PAPER TRADING' if PAPER_TRADING_MODE else 'LIVE TRADING'}")
    log_info("Strategy: Place buy/sell limit orders around CLOB spread")
    log_info("=" * 60)

    client = get_client()
    if client is None:
        log_error("main", "Failed to initialize CLOB client. Exiting.")
        return

    trade_count = 0
    error_count = 0
    active_tokens = set()

    while True:
        try:
            log_info(f"MAIN | Scan #{trade_count + 1} starting...")

            opportunities = find_market_making_opportunities()

            if not opportunities:
                log_info("MAIN | No MM opportunities found this scan")
            else:
                for opp in opportunities:
                    token_id = opp["token_id"]

                    # Skip tokens already have active orders on
                    if token_id in active_tokens:
                        log_info(
                            f"MAIN | Already active | "
                            f"token={token_id[:8]}..."
                        )
                        continue

                    # Calculate order prices
                    mm_order = get_mm_orders(opp)
                    if mm_order is None:
                        continue

                    # Check balance
                    if not has_sufficient_balance(client, MAX_POSITION_SIZE):
                        log_warning("MAIN | Insufficient balance - skipping")
                        continue

                    # Execute
                    log_info(
                        f"MAIN | Executing MM trade | "
                        f"{mm_order['market_question']} | "
                        f"buy={mm_order['buy_price']} "
                        f"sell={mm_order['sell_price']} | "
                        f"edge={mm_order['profit_pct']}%"
                    )

                    execute_mm_trade(client, mm_order)
                    active_tokens.add(token_id)
                    trade_count += 1

        except KeyboardInterrupt:
            log_info("MAIN | Shutdown requested by user")
            break

        except Exception as e:
            error_count += 1
            log_error("main.loop", e)
            if error_count >= 10:
                log_error("main.loop", "Too many errors - shutting down")
                break

        log_info(
            f"MAIN | Scan complete | "
            f"trades={trade_count} | "
            f"active_tokens={len(active_tokens)} | "
            f"errors={error_count} | "
            f"sleeping {SCAN_INTERVAL_SECONDS}s"
        )
        time.sleep(SCAN_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
