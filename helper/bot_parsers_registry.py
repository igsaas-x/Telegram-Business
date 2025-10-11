"""
Bot-specific parser registry for optimized message parsing.
Each bot has a dedicated parser function.
"""

from datetime import datetime
from typing import Callable, Tuple, Optional

# Type alias for parser functions
ParserFunction = Callable[[str], Tuple[Optional[str], Optional[float], Optional[datetime]]]

# Bot parser registry - maps bot username to parser function name
BOT_PARSERS: dict[str, str] = {
    # Khmer banks
    "ACLEDABankBot": "parse_acleda",
    "PayWayByABA_bot": "parse_aba",
    "PLBITBot": "parse_plb",
    "CanadiaMerchant_bot": "parse_canadia",
    "HLBCAM_Bot": "parse_hlb",
    "vattanac_bank_merchant_prod_bot": "parse_vattanac",
    "CPBankBot": "parse_cpbank",
    "SathapanaBank_bot": "parse_sathapana",
    "chipmongbankpaymentbot": "parse_chipmong",
    "prasac_merchant_payment_bot": "parse_prasac",
    "AMKPlc_bot": "parse_amk",
    "prince_pay_bot": "parse_prince",

    # Special format bots
    "s7pos_bot": "parse_s7pos",
    "S7days777": "parse_s7days",
    "payment_bk_bot": "parse_payment_bk",
}


def get_parser_name(bot_username: str | None) -> str:
    """Get the parser function name for a bot"""
    if not bot_username:
        return "parse_universal"
    return BOT_PARSERS.get(bot_username, "parse_universal")


def has_dedicated_parser(bot_username: str | None) -> bool:
    """Check if bot has a dedicated parser"""
    return bot_username in BOT_PARSERS if bot_username else False
