import re

def extract_amount_and_currency(text: str):
    # Pattern 1: Currency symbol before amount (e.g., "$100", "៛50.25")
    match = re.search(r'([៛$])\s?([\d,]+(?:\.\d+)?)', text)
    if match:
        currency = match.group(1)
        amount_str = match.group(2).replace(',', '')
        try:
            amount = float(amount_str) if '.' in amount_str else int(amount_str)
        except ValueError:
            return None, None
        return currency, amount
    
    # Pattern 2: Amount before currency code (e.g., "65.00 USD", "100.50 KHR")
    match = re.search(r'([\d,]+(?:\.\d+)?)\s+(USD|KHR)', text, re.IGNORECASE)
    if match:
        amount_str = match.group(1).replace(',', '')
        currency_code = match.group(2).upper()
        
        # Convert currency codes to symbols
        currency_map = {
            'USD': '$',
            'KHR': '៛'
        }
        currency = currency_map.get(currency_code, currency_code)
        
        try:
            amount = float(amount_str) if '.' in amount_str else int(amount_str)
        except ValueError:
            return None, None
        return currency, amount
    
    return None, None

def extract_trx_id(message_text: str) -> str | None:
    # Pattern 1: Traditional format "Trx. ID: 123456"
    match = re.search(r'Trx\. ID:\s*([0-9]+)', message_text)
    if match:
        return match.group(1)
    
    # Pattern 2: Hash format "(Hash. abc123def)"
    match = re.search(r'\(Hash\.\s*([a-f0-9]+)\)', message_text, re.IGNORECASE)
    if match:
        return match.group(1)
    
    return None