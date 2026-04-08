from py_clob_client.client import ClobClient
from src.logger import log_info, log_error, log_warning
from config.settings import (
    PRIVATE_KEY,
    WALLET_ADDRESS,
    CLOB_API_URL,
    CHAIN_ID,
    MIN_WALLET_BALANCE
)

def get_client():
    """
    Initialize and return authenticated Polymarket CLOB client.
    """
    try:
        client = ClobClient(
            host=CLOB_API_URL,
            key=PRIVATE_KEY,
            chain_id=CHAIN_ID
        )
        log_info("WALLET | CLOB client initialized")
        return client
    except Exception as e:
        log_error("wallet.get_client", e)
        return None


def get_balance(client):
    """
    Query USDC balance from Polymarket.
    Returns float balance or None on failure.
    """
    try:
        data = client.get_balance_allowance()
        balance = float(data.get("balance", 0))
        log_info(f"WALLET | Balance: {balance} USDC")
        return balance
    except Exception as e:
        log_error("wallet.get_balance", e)
        return None


def has_sufficient_balance(client, order_size):
    """
    Check wallet has enough USDC for trade plus minimum reserve.
    In paper trading mode always returns True.
    """
    from config.settings import PAPER_TRADING_MODE
    if PAPER_TRADING_MODE:
        return True

    balance = get_balance(client)

    if balance is None:
        log_warning("WALLET | Could not retrieve balance - skipping trade")
        return False

    required = order_size + MIN_WALLET_BALANCE

    if balance < required:
        log_warning(
            f"WALLET | Insufficient balance: {balance} USDC | "
            f"Required: {required} USDC"
        )
        return False

    return True
