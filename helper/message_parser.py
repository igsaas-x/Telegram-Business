import re

def extract_amount_and_currency(text: str):
    match = re.search(r'([៛$€£])\s?([\d,]+(?:\.\d+)?)', text)
    if match:
        currency = match.group(1)
        amount_str = match.group(2).replace(',', '')
        try:
            amount = float(amount_str) if '.' in amount_str else int(amount_str)
        except ValueError:
            return None, None
        return currency, amount
    return None, None

def extract_trx_id(message_text: str) -> str | None:
    match = re.search(r'Trx\. ID:\s*([0-9]+)', message_text)
    if match:
        return match.group(1)
    return None