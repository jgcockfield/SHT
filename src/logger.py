import logging
import os
from datetime import datetime

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Log filename with date
log_filename = f"logs/sht_{datetime.now().strftime('%Y%m%d')}.log"

# Configure logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("SHT")

def log_trade(market_id, token_id, buy_price, sell_price,
              spread_at_entry, order_size, profit_expected,
              profit_realized, exit_type, status, error_message=""):
    logger.info(
        f"TRADE | market={market_id} | token={token_id} | "
        f"buy={buy_price} | sell={sell_price} | "
        f"spread={spread_at_entry} | size={order_size} | "
        f"expected={profit_expected} | realized={profit_realized} | "
        f"exit={exit_type} | status={status} | error={error_message}"
    )

def log_error(context, error):
    logger.error(f"ERROR | {context} | {error}")

def log_info(message):
    logger.info(message)

def log_warning(message):
    logger.warning(message)
