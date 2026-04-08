import requests
from datetime import datetime, timezone
from src.logger import log_info, log_error
from config.settings import (
    GAMMA_API_URL,
    MARKET_MAX_AGE_SECONDS,
    MAX_RESOLUTION_WINDOW_HOURS
)


def get_new_markets():
    """
    Fetch markets from Polymarket Gamma API.
    Returns markets that are:
    - Created within the last MARKET_MAX_AGE_SECONDS
    - Resolving within MAX_RESOLUTION_WINDOW_HOURS
    - Active and open for trading
    """
    try:
        url = f"{GAMMA_API_URL}/markets"
        params = {
            "active": "true",
            "closed": "false",
            "limit": 100,
            "order": "createdAt",
            "ascending": "false"
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        markets = response.json()

        now = datetime.now(timezone.utc)
        qualifying = []

        for market in markets:
            try:
                # Check market age
                created_at = datetime.fromisoformat(
                    market["createdAt"].replace("Z", "+00:00")
                )
                age_seconds = (now - created_at).total_seconds()

                if age_seconds > MARKET_MAX_AGE_SECONDS:
                    continue

                # Check resolution window
                end_date = datetime.fromisoformat(
                    market["endDate"].replace("Z", "+00:00")
                )
                hours_to_resolution = (
                    end_date - now
                ).total_seconds() / 3600

                if hours_to_resolution > MAX_RESOLUTION_WINDOW_HOURS:
                    continue

                if hours_to_resolution <= 0:
                    continue

                qualifying.append(market)
                log_info(
                    f"SCANNER | Qualifying market found: "
                    f"{market.get('question', 'N/A')} | "
                    f"age={age_seconds:.0f}s | "
                    f"resolves_in={hours_to_resolution:.1f}h"
                )

            except (KeyError, ValueError) as e:
                log_error("scanner.parse_market", e)
                continue

        log_info(f"SCANNER | Scan complete | {len(qualifying)} qualifying markets found")
        return qualifying

    except requests.RequestException as e:
        log_error("scanner.get_new_markets", e)
        return []
