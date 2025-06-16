def handle_direct_address_message(message):
    """
    Simple listener that prints the incoming Telegram message.
    Args:
        message (str): The message received from Telegram.
    """
    print(f"[Direct Address Listener] Received message: {message}")
