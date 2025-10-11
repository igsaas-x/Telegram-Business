"""
Bot-specific parser functions for optimized message parsing.
Each bot has a dedicated parser that returns (currency, amount, datetime).
"""

from datetime import datetime, time as dt_time
from typing import Tuple, Optional

import pytz

from helper.message_patterns import (
    # Bot-specific patterns
    ACLEDA_RECEIVED, ABA_SYMBOL_START, PLB_CREDITED, CANADIA_PAID,
    HLB_IS_PAID, VATTANAC_IS_PAID, CPBANK_RECEIVED, SATHAPANA_AMOUNT,
    CHIPMONG_IS_PAID, PRASAC_PAYMENT_AMOUNT, AMK_BOLD_AMOUNT, PRINCE_AMOUNT_BOLD,
    S7POS_FINAL_AMOUNT, S7DAYS_USD_VALUES,
    # Universal patterns
    KHMER_RIEL_PATTERN, KHMER_DOLLAR_PATTERN,
    CURRENCY_SYMBOL_BEFORE, AMOUNT_BEFORE_CODE, CODE_BEFORE_AMOUNT, AMOUNT_WITH_LABEL,
    # Time patterns
    TIME_PATTERNS, MONTH_MAP,
    # Helpers
    CURRENCY_MAP,
)


# ========================================
# Time Extraction Helper
# ========================================

def extract_transaction_time(text: str) -> Optional[datetime]:
    """
    Extract transaction timestamp from message.

    Args:
        text: Payment message text

    Returns:
        datetime object in ICT timezone, or None if not found
    """
    ict = pytz.timezone('Asia/Phnom_Penh')

    # Try Sathapana format: "2025-10-04 08.58.45 AM"
    match = TIME_PATTERNS['datetime_iso_dots_12h'].search(text)
    if match:
        try:
            year = int(match.group(1))
            month = int(match.group(2))
            day = int(match.group(3))
            hour = int(match.group(4))
            minute = int(match.group(5))
            second = int(match.group(6))
            am_pm = match.group(7).upper()

            # Convert 12-hour to 24-hour
            if am_pm == 'PM' and hour != 12:
                hour += 12
            elif am_pm == 'AM' and hour == 12:
                hour = 0

            dt = datetime(year, month, day, hour, minute, second)
            return ict.localize(dt)
        except (ValueError, AttributeError):
            pass

    # Try CP Bank format: "11-10-2025 10:52:51 AM"
    match = TIME_PATTERNS['datetime_dmy_dash_12h'].search(text)
    if match:
        try:
            day = int(match.group(1))
            month = int(match.group(2))
            year = int(match.group(3))
            hour = int(match.group(4))
            minute = int(match.group(5))
            second = int(match.group(6))
            am_pm = match.group(7).upper()

            # Convert 12-hour to 24-hour
            if am_pm == 'PM' and hour != 12:
                hour += 12
            elif am_pm == 'AM' and hour == 12:
                hour = 0

            dt = datetime(year, month, day, hour, minute, second)
            return ict.localize(dt)
        except (ValueError, AttributeError):
            pass

    # Try CP Bank/AMK format: "15-09-2025 04:17 PM" (no seconds)
    match = TIME_PATTERNS['datetime_dmy_dash_12h_nosec'].search(text)
    if match:
        try:
            day = int(match.group(1))
            month = int(match.group(2))
            year = int(match.group(3))
            hour = int(match.group(4))
            minute = int(match.group(5))
            am_pm = match.group(6).upper()

            # Convert 12-hour to 24-hour
            if am_pm == 'PM' and hour != 12:
                hour += 12
            elif am_pm == 'AM' and hour == 12:
                hour = 0

            dt = datetime(year, month, day, hour, minute, 0)
            return ict.localize(dt)
        except (ValueError, AttributeError):
            pass

    # Try Vattanac format: "04/10/2025 09:32 PM"
    match = TIME_PATTERNS['datetime_dmy_slash_12h'].search(text)
    if match:
        try:
            day = int(match.group(1))
            month = int(match.group(2))
            year = int(match.group(3))
            hour = int(match.group(4))
            minute = int(match.group(5))
            am_pm = match.group(6).upper()

            # Convert 12-hour to 24-hour
            if am_pm == 'PM' and hour != 12:
                hour += 12
            elif am_pm == 'AM' and hour == 12:
                hour = 0

            dt = datetime(year, month, day, hour, minute, 0)
            return ict.localize(dt)
        except (ValueError, AttributeError):
            pass

    # Try ACLEDA format: "11-Oct-2025 10:12AM" (no space before AM/PM)
    match = TIME_PATTERNS['datetime_month_name_nospace'].search(text)
    if match:
        try:
            day = int(match.group(1))
            month_name = match.group(2).lower()
            year = int(match.group(3))
            hour = int(match.group(4))
            minute = int(match.group(5))
            am_pm = match.group(6).upper()
            month = MONTH_MAP.get(month_name[:3], None)

            if month:
                # Convert 12-hour to 24-hour
                if am_pm == 'PM' and hour != 12:
                    hour += 12
                elif am_pm == 'AM' and hour == 12:
                    hour = 0

                dt = datetime(year, month, day, hour, minute, 0)
                return ict.localize(dt)
        except (ValueError, AttributeError):
            pass

    # Try datetime_at pattern: "11-Oct-2025 @10:23:23"
    match = TIME_PATTERNS['datetime_at'].search(text)
    if match:
        try:
            day = int(match.group(1))
            month_name = match.group(2).lower()
            year = int(match.group(3))
            hour = int(match.group(4))
            minute = int(match.group(5))
            second = int(match.group(6))
            month = MONTH_MAP.get(month_name[:3], None)
            if month:
                dt = datetime(year, month, day, hour, minute, second)
                return ict.localize(dt)
        except (ValueError, AttributeError):
            pass

    # Try datetime_month_name: "11 OCT 2025 at 10:08:53"
    match = TIME_PATTERNS['datetime_month_name'].search(text)
    if match:
        try:
            day = int(match.group(1))
            month_name = match.group(2).lower()
            year = int(match.group(3))
            hour = int(match.group(4))
            minute = int(match.group(5))
            second = int(match.group(6))
            month = MONTH_MAP.get(month_name[:3], None)
            if month:
                dt = datetime(year, month, day, hour, minute, second)
                return ict.localize(dt)
        except (ValueError, AttributeError):
            pass

    # Try datetime_month_name_short: "11-Oct-25 09:43.44 AM"
    match = TIME_PATTERNS['datetime_month_name_short'].search(text)
    if match:
        try:
            day = int(match.group(1))
            month_name = match.group(2).lower()
            year_short = int(match.group(3))
            year = 2000 + year_short if year_short < 100 else year_short
            hour = int(match.group(4))
            minute = int(match.group(5))
            second = int(match.group(6))
            am_pm = match.group(7).upper()
            month = MONTH_MAP.get(month_name[:3], None)

            if month:
                # Convert 12-hour to 24-hour
                if am_pm == 'PM' and hour != 12:
                    hour += 12
                elif am_pm == 'AM' and hour == 12:
                    hour = 0

                dt = datetime(year, month, day, hour, minute, second)
                return ict.localize(dt)
        except (ValueError, AttributeError):
            pass

    # Try datetime_comma: "Oct 11, 2025 10:21 AM" or "Oct 11, 10:21 AM"
    match = TIME_PATTERNS['datetime_comma'].search(text)
    if match:
        try:
            month_name = match.group(1).lower()
            day = int(match.group(2))
            year_str = match.group(3)
            year = int(year_str) if year_str else datetime.now(ict).year
            hour = int(match.group(4))
            minute = int(match.group(5))
            am_pm = match.group(6).upper()
            month = MONTH_MAP.get(month_name[:3], None)

            if month:
                # Convert 12-hour to 24-hour
                if am_pm == 'PM' and hour != 12:
                    hour += 12
                elif am_pm == 'AM' and hour == 12:
                    hour = 0

                dt = datetime(year, month, day, hour, minute, 0)
                return ict.localize(dt)
        except (ValueError, AttributeError):
            pass

    # Try datetime_slash_12h: "2025/09/26, 10:07 pm"
    match = TIME_PATTERNS['datetime_slash_12h'].search(text)
    if match:
        try:
            year = int(match.group(1))
            month = int(match.group(2))
            day = int(match.group(3))
            hour = int(match.group(4))
            minute = int(match.group(5))
            am_pm = match.group(6).upper()

            # Convert 12-hour to 24-hour
            if am_pm == 'PM' and hour != 12:
                hour += 12
            elif am_pm == 'AM' and hour == 12:
                hour = 0

            dt = datetime(year, month, day, hour, minute, 0)
            return ict.localize(dt)
        except (ValueError, AttributeError):
            pass

    # Try datetime_iso: "2025-10-10 14:35:22"
    match = TIME_PATTERNS['datetime_iso'].search(text)
    if match:
        try:
            year = int(match.group(1))
            month = int(match.group(2))
            day = int(match.group(3))
            hour = int(match.group(4))
            minute = int(match.group(5))
            second = int(match.group(6)) if match.group(6) else 0
            dt = datetime(year, month, day, hour, minute, second)
            return ict.localize(dt)
        except (ValueError, AttributeError):
            pass

    # Try datetime_slash: "10/10/2025 14:35"
    match = TIME_PATTERNS['datetime_slash'].search(text)
    if match:
        try:
            day = int(match.group(1))
            month = int(match.group(2))
            year = int(match.group(3))
            hour = int(match.group(4))
            minute = int(match.group(5))
            second = int(match.group(6)) if match.group(6) else 0
            dt = datetime(year, month, day, hour, minute, second)
            return ict.localize(dt)
        except (ValueError, AttributeError):
            pass

    # Try time_dots: "08.58.45" (time only, combine with today)
    match = TIME_PATTERNS['time_dots'].search(text)
    if match:
        try:
            hour = int(match.group(1))
            minute = int(match.group(2))
            second = int(match.group(3))
            today = datetime.now(ict).date()
            dt = datetime.combine(today, dt_time(hour, minute, second))
            return ict.localize(dt)
        except (ValueError, AttributeError):
            pass

    return None


# ========================================
# Bot-Specific Parsers
# ========================================

def parse_acleda(text: str) -> Tuple[Optional[str], Optional[float], Optional[datetime]]:
    """Parse ACLEDA Bank messages (English + Khmer)"""
    # Try bot-specific pattern first: "Received X.XX USD" or "បានទទួល X.XX ដុល្លារ"
    match = ACLEDA_RECEIVED.search(text)
    if match:
        amount_str = match.group(1).replace(',', '')
        currency_raw = match.group(2)
        # Convert Khmer currency to symbol
        if currency_raw in ['ដុល្លារ', 'USD']:
            currency = '$'
        elif currency_raw in ['រៀល', 'KHR']:
            currency = '៛'
        else:
            currency = currency_raw
        amount = float(amount_str) if '.' in amount_str else int(amount_str)
        trx_time = extract_transaction_time(text)
        return currency, amount, trx_time

    # Fallback to universal parser
    return parse_universal(text)


def parse_aba(text: str) -> Tuple[Optional[str], Optional[float], Optional[datetime]]:
    """Parse ABA Bank messages (English + Khmer)"""
    # Try bot-specific pattern: "៛X,XXX paid" or "$X.XX paid" (symbol at start of line)
    match = ABA_SYMBOL_START.search(text)
    if match:
        currency = match.group(1)
        amount_str = match.group(2).replace(',', '')
        amount = float(amount_str) if '.' in amount_str else int(amount_str)
        trx_time = extract_transaction_time(text)
        return currency, amount, trx_time

    # Fallback to universal parser
    return parse_universal(text)


def parse_plb(text: str) -> Tuple[Optional[str], Optional[float], Optional[datetime]]:
    """Parse PLB Bank messages (English)"""
    # Try bot-specific pattern: "X,XXX KHR was credited"
    match = PLB_CREDITED.search(text)
    if match:
        amount_str = match.group(1).replace(',', '')
        currency_code = match.group(2).upper()
        currency = '$' if currency_code == 'USD' else '៛'
        amount = float(amount_str) if '.' in amount_str else int(amount_str)
        trx_time = extract_transaction_time(text)
        return currency, amount, trx_time

    # Fallback to universal parser
    return parse_universal(text)


def parse_canadia(text: str) -> Tuple[Optional[str], Optional[float], Optional[datetime]]:
    """Parse Canadia Bank messages (English)"""
    # Try bot-specific pattern: "X.XX USD was paid"
    match = CANADIA_PAID.search(text)
    if match:
        amount_str = match.group(1).replace(',', '')
        currency_code = match.group(2).upper()
        currency = '$' if currency_code == 'USD' else '៛'
        amount = float(amount_str) if '.' in amount_str else int(amount_str)
        trx_time = extract_transaction_time(text)
        return currency, amount, trx_time

    # Fallback to universal parser
    return parse_universal(text)


def parse_hlb(text: str) -> Tuple[Optional[str], Optional[float], Optional[datetime]]:
    """Parse Hong Leong Bank messages (English)"""
    # Try bot-specific pattern: "KHR X,XXX.XX is paid"
    match = HLB_IS_PAID.search(text)
    if match:
        currency_code = match.group(1).upper()
        amount_str = match.group(2).replace(',', '')
        currency = '$' if currency_code == 'USD' else '៛'
        amount = float(amount_str) if '.' in amount_str else int(amount_str)
        trx_time = extract_transaction_time(text)
        return currency, amount, trx_time

    # Fallback to universal parser
    return parse_universal(text)


def parse_vattanac(text: str) -> Tuple[Optional[str], Optional[float], Optional[datetime]]:
    """Parse Vattanac Bank messages (English)"""
    # Try bot-specific pattern: "USD X.XX is paid by"
    match = VATTANAC_IS_PAID.search(text)
    if match:
        currency_code = match.group(1).upper()
        amount_str = match.group(2).replace(',', '')
        currency = '$' if currency_code == 'USD' else '៛'
        amount = float(amount_str) if '.' in amount_str else int(amount_str)
        trx_time = extract_transaction_time(text)
        return currency, amount, trx_time

    # Fallback to universal parser
    return parse_universal(text)


def parse_cpbank(text: str) -> Tuple[Optional[str], Optional[float], Optional[datetime]]:
    """Parse CP Bank messages (English)"""
    # Try bot-specific pattern: "received KHR X,XXX" or "amount USD X.XX"
    match = CPBANK_RECEIVED.search(text)
    if match:
        currency_code = match.group(1).upper()
        amount_str = match.group(2).replace(',', '')
        currency = '$' if currency_code == 'USD' else '៛'
        amount = float(amount_str) if '.' in amount_str else int(amount_str)
        trx_time = extract_transaction_time(text)
        return currency, amount, trx_time

    # Fallback to universal parser
    return parse_universal(text)


def parse_sathapana(text: str) -> Tuple[Optional[str], Optional[float], Optional[datetime]]:
    """Parse Sathapana Bank messages (English)"""
    # Try bot-specific pattern: "The amount X.XX USD"
    match = SATHAPANA_AMOUNT.search(text)
    if match:
        amount_str = match.group(1).replace(',', '')
        currency_code = match.group(2).upper()
        currency = '$' if currency_code == 'USD' else '៛'
        amount = float(amount_str) if '.' in amount_str else int(amount_str)
        trx_time = extract_transaction_time(text)
        return currency, amount, trx_time

    # Fallback to universal parser
    return parse_universal(text)


def parse_chipmong(text: str) -> Tuple[Optional[str], Optional[float], Optional[datetime]]:
    """Parse Chip Mong Bank messages (English)"""
    # Try bot-specific pattern: "KHR X,XXX is paid"
    match = CHIPMONG_IS_PAID.search(text)
    if match:
        currency_code = match.group(1).upper()
        amount_str = match.group(2).replace(',', '')
        currency = '$' if currency_code == 'USD' else '៛'
        amount = float(amount_str) if '.' in amount_str else int(amount_str)
        trx_time = extract_transaction_time(text)
        return currency, amount, trx_time

    # Fallback to universal parser
    return parse_universal(text)


def parse_prasac(text: str) -> Tuple[Optional[str], Optional[float], Optional[datetime]]:
    """Parse PRASAC Bank messages (English)"""
    # Try bot-specific pattern: "Payment Amount X.XX USD"
    match = PRASAC_PAYMENT_AMOUNT.search(text)
    if match:
        amount_str = match.group(1).replace(',', '')
        currency_code = match.group(2).upper()
        currency = '$' if currency_code == 'USD' else '៛'
        amount = float(amount_str) if '.' in amount_str else int(amount_str)
        trx_time = extract_transaction_time(text)
        return currency, amount, trx_time

    # Fallback to universal parser
    return parse_universal(text)


def parse_amk(text: str) -> Tuple[Optional[str], Optional[float], Optional[datetime]]:
    """Parse Advanced Bank of Asia messages (English)"""
    # Try bot-specific pattern: "**KHR X,XXX**"
    match = AMK_BOLD_AMOUNT.search(text)
    if match:
        currency_code = match.group(1).upper()
        amount_str = match.group(2).replace(',', '')
        currency = '$' if currency_code == 'USD' else '៛'
        amount = float(amount_str) if '.' in amount_str else int(amount_str)
        trx_time = extract_transaction_time(text)
        return currency, amount, trx_time

    # Fallback to universal parser
    return parse_universal(text)


def parse_prince(text: str) -> Tuple[Optional[str], Optional[float], Optional[datetime]]:
    """Parse Prince Bank messages (English)"""
    # Try bot-specific pattern: "Amount: **USD X.XX**"
    match = PRINCE_AMOUNT_BOLD.search(text)
    if match:
        currency_code = match.group(1).upper()
        amount_str = match.group(2).replace(',', '')
        currency = '$' if currency_code == 'USD' else '៛'
        amount = float(amount_str) if '.' in amount_str else int(amount_str)
        trx_time = extract_transaction_time(text)
        return currency, amount, trx_time

    # Fallback to universal parser
    return parse_universal(text)


def parse_s7pos(text: str) -> Tuple[Optional[str], Optional[float], Optional[datetime]]:
    """Parse s7pos_bot messages (Khmer)"""
    match = S7POS_FINAL_AMOUNT.search(text)
    if match:
        amount_str = match.group(1).replace(',', '')
        amount = float(amount_str) if '.' in amount_str else int(amount_str)
        trx_time = extract_transaction_time(text)
        return '$', amount, trx_time
    return None, None, None


def parse_s7days(text: str) -> Tuple[Optional[str], Optional[float], Optional[datetime]]:
    """Parse S7days777 messages (English)"""
    matches = S7DAYS_USD_VALUES.findall(text)
    if not matches:
        return None, None, None
    total = round(sum(float(value) for value in matches), 2)
    if total == int(total):
        total = int(total)
    trx_time = extract_transaction_time(text)
    return '$', total, trx_time


def parse_payment_bk(text: str) -> Tuple[Optional[str], Optional[float], Optional[datetime]]:
    """Parse payment_bk_bot messages (English)"""
    # No specific pattern yet, use universal parser
    return parse_universal(text)


# ========================================
# Universal Fallback Parser
# ========================================

def parse_universal(text: str) -> Tuple[Optional[str], Optional[float], Optional[datetime]]:
    """
    Universal fallback parser - tries all common patterns
    Used for unknown bots or when bot-specific parser fails
    """
    # Try Khmer patterns first
    match = KHMER_DOLLAR_PATTERN.search(text)
    if match:
        amount_str = match.group(1).replace(',', '')
        amount = float(amount_str) if '.' in amount_str else int(amount_str)
        trx_time = extract_transaction_time(text)
        return '$', amount, trx_time

    match = KHMER_RIEL_PATTERN.search(text)
    if match:
        amount_str = match.group(1).replace(',', '')
        amount = float(amount_str) if '.' in amount_str else int(amount_str)
        trx_time = extract_transaction_time(text)
        return '៛', amount, trx_time

    # Try currency symbol before amount
    match = CURRENCY_SYMBOL_BEFORE.search(text)
    if match:
        currency = match.group(1)
        amount_str = match.group(2).replace(',', '')
        amount = float(amount_str) if '.' in amount_str else int(amount_str)
        trx_time = extract_transaction_time(text)
        return currency, amount, trx_time

    # Try amount before currency code
    match = AMOUNT_BEFORE_CODE.search(text)
    if match:
        amount_str = match.group(1).replace(',', '')
        currency_code = match.group(2).upper()
        currency = CURRENCY_MAP.get(currency_code, currency_code)
        amount = float(amount_str) if '.' in amount_str else int(amount_str)
        trx_time = extract_transaction_time(text)
        return currency, amount, trx_time

    # Try currency code before amount
    match = CODE_BEFORE_AMOUNT.search(text)
    if match:
        currency_code = match.group(1).upper()
        amount_str = match.group(2).replace(',', '')
        currency = CURRENCY_MAP.get(currency_code, currency_code)
        amount = float(amount_str) if '.' in amount_str else int(amount_str)
        trx_time = extract_transaction_time(text)
        return currency, amount, trx_time

    # Try amount with label
    match = AMOUNT_WITH_LABEL.search(text)
    if match:
        currency_code = match.group(1).upper()
        amount_str = match.group(2).replace(',', '')
        currency = CURRENCY_MAP.get(currency_code, currency_code)
        amount = float(amount_str) if '.' in amount_str else int(amount_str)
        trx_time = extract_transaction_time(text)
        return currency, amount, trx_time

    # No match found
    return None, None, None
