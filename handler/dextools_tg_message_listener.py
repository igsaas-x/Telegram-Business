def handle_dextools_message(message):
    """
    Simple listener that prints the incoming Telegram message.
    Args:
        message (str): The message received from Telegram.
    """
    print(f"[DexTools Listener] Received message: {message}")
