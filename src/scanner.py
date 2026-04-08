import requests
from src.logger import log_info, log_error
from config.settings import GAMMA_API_URL


def get_new_markets():
    """
    Scan for binary markets where YES + NO price < 0.97.
    This indicates mispricing — buying both sides guarantees
    a profit at resolution since one side always pays $1.00.
    """
    try:
        url = f"{GAMMA_API_URL}/markets"
        params = {
            "active": "true",
            "closed": "false",
            "limit": 100,
            "order": "volume24hr",
            "ascending": "false"
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        markets = response.json()

        qualifying = []

        for market in markets:
            try:
                best_bid = float(market.get("bestBid") or 0)
                best_ask = float(market.get("bestAsk") or 0)
                liquidity = float(market.get("liquidityNum") or 0)
                volume = float(market.get("volume24hr") or 0)
                accepting = market.get("acceptingOrders", False)

                if not accepting:
                    continue

                if liquidity < 1000:
                    continue

                if volume < 100:
                    continue

                # Core mispricing check
                # In a binary market: YES + NO = 1.00
                # bestBid on YES = price of YES
                # bestBid on NO = 1 - bestAsk on YES
                yes_price = best_bid
                no_price = round(1 - best_ask, 4)
                combined = round(yes_price + no_price, 4)

                if combined >= 0.97:
                    continue

                edge = round(1 - combined, 4)

                qualifying.append({
                    **market,
                    "yes_price": yes_price,
                    "no_price": no_price,
                    "combined": combined,
                    "edge": edge
                })

                log_info(
                    f"SCANNER | Mispricing found: "
                    f"{market.get('question', 'N/A')[:50]} | "
                    f"YES={yes_price} NO={no_price} "
                    f"combined={combined} edge={edge:.4f}"
                )

            except (KeyError, ValueError) as e:
                log_error("scanner.parse_market", e)
                continue

        log_info(
            f"SCANNER | Scan complete | "
            f"{len(qualifying)} mispriced markets found"
        )
        return qualifying

    except requests.RequestException as e:
        log_error("scanner.get_new_markets", e)
        return []
