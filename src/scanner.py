import requests
from src.logger import log_info, log_error
from config.settings import GAMMA_API_URL


def get_new_markets():
    """
    Fetch actively traded markets from Polymarket Gamma API.
    Uses Gamma API spread/bid/ask directly — no CLOB call needed for filtering.
    Targets markets in active price discovery (35-65% probability range).
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
                spread = float(market.get("spread") or 1)
                liquidity = float(market.get("liquidityNum") or 0)
                volume = float(market.get("volume24hr") or 0)
                accepting = market.get("acceptingOrders", False)

                # Must be accepting orders
                if not accepting:
                    continue

                # Must have tight spread
                if spread > 0.05:
                    continue

                # Must be in contested probability zone
                if not (0.35 <= best_bid <= 0.65):
                    continue

                # Must have real liquidity
                if liquidity < 1000:
                    continue

                # Must have real volume
                if volume < 100:
                    continue

                qualifying.append(market)
                log_info(
                    f"SCANNER | Qualifying market: "
                    f"{market.get('question', 'N/A')[:50]} | "
                    f"bid={best_bid} ask={best_ask} | "
                    f"spread={spread:.3f} | liq={liquidity:.0f}"
                )

            except (KeyError, ValueError) as e:
                log_error("scanner.parse_market", e)
                continue

        log_info(
            f"SCANNER | Scan complete | "
            f"{len(qualifying)} qualifying markets found"
        )
        return qualifying

    except requests.RequestException as e:
        log_error("scanner.get_new_markets", e)
        return []
