import os
from dotenv import load_dotenv

load_dotenv()

# Wallet
PRIVATE_KEY = os.getenv("POLYMARKET_PRIVATE_KEY")
WALLET_ADDRESS = os.getenv("POLYMARKET_WALLET_ADDRESS")

# Trading mode
PAPER_TRADING_MODE = os.getenv("PAPER_TRADING_MODE", "True") == "True"

# Strategy parameters
PROFIT_BUFFER = float(os.getenv("PROFIT_BUFFER", "0.02"))
SELL_TIMEOUT_SECONDS = int(os.getenv("SELL_TIMEOUT_SECONDS", "300"))
BREAKEVEN_TIMEOUT_SECONDS = int(os.getenv("BREAKEVEN_TIMEOUT_SECONDS", "120"))
MAX_SPREAD_THRESHOLD = float(os.getenv("MAX_SPREAD_THRESHOLD", "0.05"))
MIN_LIQUIDITY_THRESHOLD = float(os.getenv("MIN_LIQUIDITY_THRESHOLD", "100"))
MAX_POSITION_SIZE = float(os.getenv("MAX_POSITION_SIZE", "25"))
MIN_WALLET_BALANCE = float(os.getenv("MIN_WALLET_BALANCE", "50"))

# Polymarket API
CLOB_API_URL = "https://clob.polymarket.com"
GAMMA_API_URL = "https://gamma-api.polymarket.com"
CHAIN_ID = 137  # Polygon mainnet

# Scan settings
SCAN_INTERVAL_SECONDS = 3
MARKET_MAX_AGE_SECONDS = 60
MAX_RESOLUTION_WINDOW_HOURS = 48
