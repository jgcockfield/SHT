from src.logger import log_info, log_warning


# In-memory store for unresolved positions
unresolved_positions = []


def flag_for_review(token_id, buy_price, size):
    """
    Flag a position for manual review.
    Stores in memory and logs warning.
    """
    position = {
        "token_id": token_id,
        "buy_price": buy_price,
        "size": size,
        "status": "unresolved"
    }
    unresolved_positions.append(position)
    log_warning(
        f"FALLBACK | Position flagged for manual review | "
        f"token={token_id} | buy={buy_price} | size={size}"
    )


def get_unresolved():
    """
    Return all unresolved positions.
    """
    return unresolved_positions


def print_unresolved_summary():
    """
    Print summary of all unresolved positions.
    """
    if not unresolved_positions:
        log_info("FALLBACK | No unresolved positions")
        return

    log_warning(
        f"FALLBACK | {len(unresolved_positions)} unresolved position(s):"
    )
    for p in unresolved_positions:
        log_warning(
            f"  token={p['token_id']} | "
            f"buy={p['buy_price']} | "
            f"size={p['size']} | "
            f"status={p['status']}"
        )
