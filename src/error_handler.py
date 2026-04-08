import time
from src.logger import log_error, log_warning, log_info


MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 5


def with_retry(func, *args, context="", retries=MAX_RETRIES, **kwargs):
    """
    Execute a function with retry logic.
    Retries up to MAX_RETRIES times on failure.
    """
    attempt = 0
    while attempt < retries:
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            attempt += 1
            log_error(
                f"error_handler.with_retry | {context} | "
                f"attempt={attempt}/{retries}",
                e
            )
            if attempt < retries:
                log_warning(
                    f"ERROR_HANDLER | Retrying in "
                    f"{RETRY_DELAY_SECONDS}s..."
                )
                time.sleep(RETRY_DELAY_SECONDS)

    log_error(
        f"error_handler.with_retry | {context}",
        f"All {retries} attempts failed"
    )
    return None


def safe_call(func, *args, context="", default=None, **kwargs):
    """
    Execute a function safely, returning default on failure.
    Does not retry — use for non-critical operations.
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        log_error(f"error_handler.safe_call | {context}", e)
        return default


def handle_api_timeout(context):
    """
    Log and handle API timeout events.
    """
    log_warning(f"ERROR_HANDLER | API timeout | {context}")


def handle_connectivity_error(context):
    """
    Log connectivity interruptions.
    """
    log_error(
        f"error_handler.handle_connectivity_error | {context}",
        "Connectivity interrupted"
    )


def handle_stale_data(context):
    """
    Log stale market data warnings.
    """
    log_warning(f"ERROR_HANDLER | Stale market data | {context}")
