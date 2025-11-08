"""
Optimized message parser with bot-specific routing.

This module provides optimized parsing by routing messages to bot-specific parsers,
reducing unnecessary regex pattern attempts from 17 to 1-3 per message.

Returns: Tuple of (currency, amount, transaction_time)
- currency: str (e.g., '$', '៛')
- amount: float or int
- transaction_time: datetime object or None
"""

from datetime import datetime
from typing import Tuple, Optional

from helper.bot_parsers import (
    parse_acleda, parse_aba, parse_plb, parse_canadia,
    parse_hlb, parse_vattanac, parse_cpbank, parse_sathapana,
    parse_chipmong, parse_prasac, parse_amk, parse_prince,
    parse_ccu, parse_s7pos, parse_s7days, parse_payment_bk,
    parse_universal
)
from helper.bot_parsers_registry import get_parser_name

# Parser function lookup table
PARSER_FUNCTIONS = {
    "parse_acleda": parse_acleda,
    "parse_aba": parse_aba,
    "parse_plb": parse_plb,
    "parse_canadia": parse_canadia,
    "parse_hlb": parse_hlb,
    "parse_vattanac": parse_vattanac,
    "parse_cpbank": parse_cpbank,
    "parse_sathapana": parse_sathapana,
    "parse_chipmong": parse_chipmong,
    "parse_prasac": parse_prasac,
    "parse_amk": parse_amk,
    "parse_prince": parse_prince,
    "parse_ccu": parse_ccu,
    "parse_s7pos": parse_s7pos,
    "parse_s7days": parse_s7days,
    "parse_payment_bk": parse_payment_bk,
    "parse_universal": parse_universal,
}


def extract_amount_currency_and_time(
    text: str,
    bot_username: str | None = None
) -> Tuple[Optional[str], Optional[float], Optional[datetime]]:
    """
    Extract amount, currency, and transaction time from payment message.
    Routes to bot-specific parser for optimized performance.

    Args:
        text: Payment message text
        bot_username: Username of the bot that sent the message

    Returns:
        Tuple of (currency, amount, transaction_time)
        - currency: str like '$' or '៛', or None if not found
        - amount: float or int, or None if not found
        - transaction_time: datetime object in ICT timezone, or None if not found

    Example:
        >>> text = "Received 10.50 USD from John Doe, 11-Oct-2025 10:12AM."
        >>> currency, amount, trx_time = extract_amount_currency_and_time(text, "ACLEDABankBot")
        >>> print(currency, amount, trx_time)
        $ 10.5 2025-10-11 10:12:00+07:00
    """
    # Get the parser function name for this bot
    parser_name = get_parser_name(bot_username)

    # Get the actual parser function
    parser_func = PARSER_FUNCTIONS.get(parser_name, parse_universal)

    # Call the bot-specific parser
    return parser_func(text)


# Convenience function for backward compatibility
def extract_amount_and_currency_optimized(
    text: str,
    bot_username: str | None = None
) -> Tuple[Optional[str], Optional[float]]:
    """
    Extract amount and currency only (without time).
    Wrapper around extract_amount_currency_and_time for backward compatibility.

    Args:
        text: Payment message text
        bot_username: Username of the bot that sent the message

    Returns:
        Tuple of (currency, amount)
    """
    currency, amount, _ = extract_amount_currency_and_time(text, bot_username)
    return currency, amount
