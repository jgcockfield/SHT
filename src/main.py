import time
from src.logger import log_info, log_warning, log_error
from src.scanner import get_new_markets
from src.filter import get_tradeable_tokens
from src.executor import execute_arb
from src.wallet import get_client, has_sufficient_balance
from config.settings import (
    SCAN_INTERVAL_SECONDS,
    MAX_POSITION_SIZE,
    PAPER_TRADING_MODE
)


def main():
    log_info("=" * 60)
    log_info("SHT - Binary Mispricing Arb Agent Starting")
    log_info(f"Mode: {'PAPER TRADING' if PAPER_TRADING_MODE else 'LIVE TRADING'}")
    log_info("Strategy: Buy YES + NO when combined price < 0.97")
    log_info("=" * 60)

    client = get_client()
    if client is None:
        log_error("main", "Failed to initialize CLOB client. Exiting.")
        return

    trade_count = 0
    error_count = 0
    seen_markets = set()

    while True:
        try:
            log_info(f"MAIN | Scan #{trade_count + 1} starting...")

            markets = get_new_markets()

            if not markets:
                log_info("MAIN | No mispriced markets found this scan")
            else:
                for market in markets:
                    market_id = market.get("id", "")

                    # Skip already traded markets this session
                    if market_id in seen_markets:
                        continue

                    question = market.get("question", "N/A")
                    yes_price = market.get("yes_price")
                    no_price = market.get("no_price")
                    edge = market.get("edge")

                    log_info(
                        f"MAIN | Mispriced market: {question[:50]} | "
                        f"edge={edge:.4f}"
                    )

                    tokens = get_tradeable_tokens(market)

                    if len(tokens) < 2:
                        log_warning(f"MAIN | Could not get both tokens for: {question[:50]}")
                        continue

                    yes_token = tokens[0]["token_id"]
                    no_token = tokens[1]["token_id"]

                    # Check balance for both legs
                    required = (yes_price + no_price) * MAX_POSITION_SIZE
                    if not has_sufficient_balance(client, required):
                        log_warning("MAIN | Insufficient balance - skipping")
                        continue

                    # Execute arb
                    execute_arb(
                        client,
                        yes_token,
                        no_token,
                        yes_price,
                        no_price,
                        edge
                    )

                    seen_markets.add(market_id)
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
            f"errors={error_count} | "
            f"sleeping {SCAN_INTERVAL_SECONDS}s"
        )
        time.sleep(SCAN_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
