import requests
import json
import socket
from contextlib import contextmanager

@contextmanager
def force_ipv4_connections():
    """Context manager to temporarily force IPv4 for socket.getaddrinfo."""
    original_getaddrinfo = socket.getaddrinfo
    def ipv4_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
        # Force AF_INET (IPv4)
        return original_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)
    
    socket.getaddrinfo = ipv4_getaddrinfo
    try:
        yield
    finally:
        socket.getaddrinfo = original_getaddrinfo

def handle_direct_address_message(event):
    """
    Simple listener that prints the incoming Telegram message.
    Args:
        event: The event received from Telegram.
    """
    print(f"[Direct Address Listener] Received message: {event.message.text}")
    print(f"[Direct Address Listener] chat_id: {event.chat_id}")

    url = "http://localhost:8080/api/message"
    # url = "https://www.google.com/"
    payload = {
        "chatId": event.chat_id,
        "message": event.message.text
    }
    headers = {
        'Content-Type': 'application/json'
    }

    try:
        print(f"[Direct Address Listener] Attempting API call to: {url}")
        with force_ipv4_connections():
            response = requests.post(url, data=json.dumps(payload), headers=headers)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4XX or 5XX)
        print(f"[Direct Address Listener] API call successful: {response.status_code}")
        # print(f"[Direct Address Listener] API response: {response.text}") # Uncomment to see response body
    except requests.exceptions.RequestException as e:
        print(f"[Direct Address Listener] API call failed: {e}")
