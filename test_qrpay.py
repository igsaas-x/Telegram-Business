from helper.message_parser import extract_amount_and_currency, extract_trx_id

test_message = "QRPay: Received KHR 22900.00 on Jul 10, 2025 07:04:44 AM paid by SAMAN LY at រតន:ហ្គាស LPG with Transaction Hash: 371f33fe."

print("Testing QRPay message parsing:")
print(f"Message: {test_message}")

currency, amount = extract_amount_and_currency(test_message)
print(f"Currency: {currency}, Amount: {amount}")

trx_id = extract_trx_id(test_message)
print(f"Transaction ID: {trx_id}")
