"""
Pre-compiled regex patterns for message parsing
Compiled once at module import for performance
"""

import re

# ========================================
# Amount & Currency Patterns
# ========================================

# Khmer patterns (used by multiple banks)
KHMER_RIEL_PATTERN = re.compile(r'([\d,]+(?:\.\d+)?)\s+រៀល')
KHMER_DOLLAR_PATTERN = re.compile(r'([\d,]+(?:\.\d+)?)\s+ដុល្លារ')

# Universal patterns
CURRENCY_SYMBOL_BEFORE = re.compile(r'([៛$])\s?([\d,]+(?:\.\d+)?)')
AMOUNT_BEFORE_CODE = re.compile(r'([\d,]+(?:\.\d+)?)\s+(USD|KHR)', re.IGNORECASE)
CODE_BEFORE_AMOUNT = re.compile(r'(USD|KHR)\s+([\d,]+(?:\.\d+)?)', re.IGNORECASE)
AMOUNT_WITH_LABEL = re.compile(r'Amount:\s+(USD|KHR)\s+([\d,]+(?:\.\d+)?)', re.IGNORECASE)

# Special format patterns
S7POS_FINAL_AMOUNT = re.compile(r'សរុបចុងក្រោយ:\s*([\d,]+(?:\.\d+)?)\s*\$')
S7DAYS_USD_VALUES = re.compile(r'[=:]\s*([\d]+(?:\.\d+)?)\s*\$')

# ========================================
# Bot-Specific Amount Patterns
# ========================================

# ACLEDA Bank - "Received X.XX USD" or "បានទទួល X.XX ដុល្លារ"
ACLEDA_RECEIVED = re.compile(r'(?:Received|បានទទួល)\s+([\d,]+(?:\.\d+)?)\s+(USD|KHR|ដុល្លារ|រៀល)', re.IGNORECASE)

# ABA Bank - "៛X,XXX paid" or "$X.XX paid" (symbol at start)
ABA_SYMBOL_START = re.compile(r'^([៛$])([\d,]+(?:\.\d+)?)\s+(?:paid|ត្រូវបានបង់)', re.MULTILINE)

# PLB Bank - "X,XXX KHR was credited" or "X.XX USD was credited"
PLB_CREDITED = re.compile(r'([\d,]+(?:\.\d+)?)\s+(USD|KHR)\s+was\s+credited', re.IGNORECASE)

# Canadia Bank - "X.XX USD was paid"
CANADIA_PAID = re.compile(r'([\d,]+(?:\.\d+)?)\s+(USD|KHR)\s+was\s+paid', re.IGNORECASE)

# HLB Bank - "KHR X,XXX.XX is paid" or "USD X.XX is paid"
HLB_IS_PAID = re.compile(r'(USD|KHR)\s+([\d,]+(?:\.\d+)?)\s+is\s+paid', re.IGNORECASE)

# Vattanac Bank - "USD X.XX is paid by" or "KHR X,XXX is paid by"
VATTANAC_IS_PAID = re.compile(r'(USD|KHR)\s+([\d,]+(?:\.\d+)?)\s+is\s+paid\s+by', re.IGNORECASE)

# CP Bank - "You have received KHR X,XXX" or "Transaction amount USD X.XX"
CPBANK_RECEIVED = re.compile(r'(?:received|amount)\s+(USD|KHR)\s+([\d,]+(?:\.\d+)?)', re.IGNORECASE)

# Sathapana Bank - "The amount X.XX USD is paid"
SATHAPANA_AMOUNT = re.compile(r'amount\s+([\d,]+(?:\.\d+)?)\s+(USD|KHR)', re.IGNORECASE)

# Chip Mong Bank - "KHR X,XXX is paid" or "USD X.XX is paid"
CHIPMONG_IS_PAID = re.compile(r'(USD|KHR)\s+([\d,]+(?:\.\d+)?)\s+is\s+paid', re.IGNORECASE)

# PRASAC Bank - "Received Payment Amount X.XX USD"
PRASAC_PAYMENT_AMOUNT = re.compile(r'Payment\s+Amount\s+([\d,]+(?:\.\d+)?)\s+(USD|KHR)', re.IGNORECASE)

# AMK Bank - "**KHR X,XXX** is paid" or "**USD X.XX** is paid"
AMK_BOLD_AMOUNT = re.compile(r'\*\*(USD|KHR)\s+([\d,]+(?:\.\d+)?)\*\*', re.IGNORECASE)

# Prince Bank - "Amount: **USD X.XX**" or "Amount: **KHR X,XXX**"
PRINCE_AMOUNT_BOLD = re.compile(r'Amount:\s+\*\*(USD|KHR)\s+([\d,]+(?:\.\d+)?)\*\*', re.IGNORECASE)

# ========================================
# Transaction ID Patterns
# ========================================

TRX_PATTERNS = {
    'trx_id': re.compile(r'Trx\.\s*ID:\s*([0-9]+)'),
    'hash_paren': re.compile(r'\(Hash\.\s*([a-f0-9]+)\)?', re.IGNORECASE),
    'khmer_ref': re.compile(r'លេខយោង\s+([0-9]+)'),
    'khmer_transaction': re.compile(r'លេខប្រតិបត្តិការ:\s*([0-9]+)'),
    'txn_hash': re.compile(r'Txn\s+Hash:\s*([a-f0-9]+)', re.IGNORECASE),
    'transaction_hash': re.compile(r'Transaction\s+Hash:\s*([a-f0-9]+)', re.IGNORECASE),
    'ref_id': re.compile(r'Ref\.ID:\s*([0-9]+)'),
    'transaction_id': re.compile(r'Transaction\s+ID:\s*([a-zA-Z0-9]+)'),
    'reference_no': re.compile(r'Reference\s+No:\s*([0-9]+)'),
    'hash': re.compile(r'Hash:\s*([a-f0-9]+)', re.IGNORECASE),
}

# Currency code mapping
CURRENCY_MAP = {
    'USD': '$',
    'KHR': '៛'
}

# ========================================
# Timestamp Patterns
# ========================================

# Common timestamp formats used by bank bots
TIME_PATTERNS = {
    # 24-hour format with seconds: "14:35:22", "09:05:00"
    'time_24h_full': re.compile(r'(\d{1,2}):(\d{2}):(\d{2})'),

    # 24-hour format without seconds: "14:35", "09:05"
    'time_24h_short': re.compile(r'(\d{1,2}):(\d{2})(?!:)'),

    # 12-hour format: "2:35 PM", "9:05 AM", "10:19AM" (no space)
    'time_12h': re.compile(r'(\d{1,2}):(\d{2})\s*(AM|PM|am|pm|ព្រឹក|ល្ងាច)', re.IGNORECASE),

    # Date with time: "2025-10-10 14:35:22", "10/10/2025 14:35"
    'datetime_iso': re.compile(r'(\d{4})-(\d{2})-(\d{2})\s+(\d{1,2}):(\d{2})(?::(\d{2}))?'),
    'datetime_slash': re.compile(r'(\d{2})/(\d{2})/(\d{4})\s+(\d{1,2}):(\d{2})(?::(\d{2}))?'),

    # Special time formats with dots: "08.58.45" (Sathapana Bank)
    'time_dots': re.compile(r'(\d{1,2})\.(\d{2})\.(\d{2})'),

    # Date-time with @ symbol: "11-Oct-2025 @10:23:23" (HLB Bank)
    'datetime_at': re.compile(r'(\d{2})-(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)-(\d{4})\s+@(\d{2}):(\d{2}):(\d{2})', re.IGNORECASE),

    # Date with month name: "11 OCT 2025 at 10:08:53", "11-Oct-25 09:43.44 AM"
    'datetime_month_name': re.compile(r'(\d{2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{4})\s+at\s+(\d{2}):(\d{2}):(\d{2})', re.IGNORECASE),
    'datetime_month_name_short': re.compile(r'(\d{2})-(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)-(\d{2})\s+(\d{2}):(\d{2})\.(\d{2})\s+(AM|PM)', re.IGNORECASE),

    # Date with comma: "Oct 11, 10:21 AM", "Oct 11, 2025 11:28 AM"
    'datetime_comma': re.compile(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2}),\s+(?:(\d{4})\s+)?(\d{1,2}):(\d{2})\s+(AM|PM)', re.IGNORECASE),

    # Date with slash and 12h time: "2025/09/26, 10:07 pm"
    'datetime_slash_12h': re.compile(r'(\d{4})/(\d{2})/(\d{2}),\s+(\d{1,2}):(\d{2})\s+(am|pm)', re.IGNORECASE),

    # ACLEDA format: "11-Oct-2025 10:12AM" (no space before AM/PM, no seconds)
    'datetime_month_name_nospace': re.compile(r'(\d{2})-(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)-(\d{4})\s+(\d{1,2}):(\d{2})(AM|PM)', re.IGNORECASE),

    # Vattanac format: "04/10/2025 09:32 PM" (slash date dd/mm/yyyy with 12h time)
    'datetime_dmy_slash_12h': re.compile(r'(\d{2})/(\d{2})/(\d{4})\s+(\d{1,2}):(\d{2})\s+(AM|PM)', re.IGNORECASE),

    # CP Bank format: "11-10-2025 10:52:51 AM" (dash date dd-mm-yyyy with 12h time and seconds)
    'datetime_dmy_dash_12h': re.compile(r'(\d{2})-(\d{2})-(\d{4})\s+(\d{1,2}):(\d{2}):(\d{2})\s+(AM|PM)', re.IGNORECASE),

    # CP Bank/AMK format: "15-09-2025 04:17 PM" (dash date dd-mm-yyyy with 12h time, no seconds)
    'datetime_dmy_dash_12h_nosec': re.compile(r'\*{0,2}(\d{2})-(\d{2})-(\d{4})\s+(\d{1,2}):(\d{2})\s+(AM|PM)\*{0,2}', re.IGNORECASE),

    # Sathapana format: "2025-10-04 08.58.45 AM" (ISO date with dot time and AM/PM)
    'datetime_iso_dots_12h': re.compile(r'(\d{4})-(\d{2})-(\d{2})\s+(\d{1,2})\.(\d{2})\.(\d{2})\s+(AM|PM)', re.IGNORECASE),

    # Khmer timestamp labels
    'khmer_time_label': re.compile(r'ម៉ោង[:\s]*(\d{1,2}):(\d{2})'),
    'khmer_datetime': re.compile(r'ថ្ងៃទី.*?(\d{1,2}):(\d{2})(AM|PM|ព្រឹក|ល្ងាច)?', re.IGNORECASE),
}

# Month name to number mapping
MONTH_MAP = {
    'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
    'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12,
    'january': 1, 'february': 2, 'march': 3, 'april': 4, 'may': 5, 'june': 6,
    'july': 7, 'august': 8, 'september': 9, 'october': 10, 'november': 11, 'december': 12,
}
