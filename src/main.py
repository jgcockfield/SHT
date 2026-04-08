import time
from src.logger import log_info, log_warning, log_error
from src.scanner import get_new_markets
from src.filter import get_tradeable_tokens
from src.executor import execute_trade
from src.fallback import print_unresolved_summary
from src.wallet import get_client, has_sufficient_balance
from config.settings import (
    SCAN_INTERVAL_SECONDS,
    MAX_POSITION_SIZE,
    PAPER_TRADING_MODE
)


def main():
    log_info("=" * 60)
    log_info("SHT - FirstMinute Trader Starting")
    log_info(f"Mode: {'PAPER TRADING' if PAPER_TRADING_MODE else 'LIVE TRADING'}")
    log_info("=" * 60)

    # Initialize client
    client = get_client()
    if client is None:
        log_error("main", "Failed to initialize CLOB client. Exiting.")
        return

    trade_count = 0
    error_count = 0

    while True:
        try:
            log_info(f"MAIN | Scan #{trade_count + 1} starting...")

            # Step 1 - scan for new markets
            markets = get_new_markets()

            if not markets:
                log_info("MAIN | No qualifying markets found this scan")
            else:
                for market in markets:
                    question = market.get("question", "N/A")
                    log_info(f"MAIN | Processing market: {question}")

                    # Step 2 - filter for tradeable tokens
                    tradeable_tokens = get_tradeable_tokens(market)

                    if not tradeable_tokens:
                        log_info(
                            f"MAIN | No tradeable tokens for: {question}"
                        )
                        continue

                    for token in tradeable_tokens:
                        token_id = token["token_id"]
                        orderbook = token["orderbook"]

                        # Step 3 - check balance
                        if not has_sufficient_balance(client, MAX_POSITION_SIZE):
                            log_warning("MAIN | Insufficient balance - skipping")
                            continue

                        # Step 4 - execute trade
                        signal = token.get("signal", "up")
                        log_info(
                            f"MAIN | Executing trade | "
                            f"token={token_id[:8]}... | "
                            f"outcome={token['outcome']} | "
                            f"signal={signal}"
                        )
                        execute_trade(client, token_id, orderbook, signal)
                        trade_count += 1

            # Print unresolved summary every 10 scans
            if trade_count > 0 and trade_count % 10 == 0:
                print_unresolved_summary()

        except KeyboardInterrupt:
            log_info("MAIN | Shutdown requested by user")
            print_unresolved_summary()
            break

        except Exception as e:
            error_count += 1
            log_error("main.loop", e)
            if error_count >= 10:
                log_error(
                    "main.loop",
                    "Too many errors - shutting down"
                )
                break

        log_info(
            f"MAIN | Scan complete | "
            f"trades={trade_count} | "
            f"errors={error_count} | "
            f"sleeping {SCAN_INTERVAL_SECONDS}s"
        )
        time.sleep(SCAN_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
