# TG Message Listener Main

"tg_message_listener_main.py" is a Python script that serves as the core of a Telegram bot application, designed to listen for and process messages from Telegram chats, groups, or channels. It uses the Telethon library to interact with the Telegram API, providing an efficient, event-driven system for routing messages to specific handlers based on content or context.

## Features

Asynchronous Message Listening: Utilizes async I/O for real-time message listening without blocking.
Modular Design: Easily extendable with new message handlers for different types of content or commands.
Secure Authentication: Integrates with credentials_telegram.json for secure API key and bot token management.
Event-Driven Processing: Employs Telethon's event listener capabilities for effective message processing.

## Getting Started

## Prerequisites

- Python 3.6+
- Telethon library
- A valid Telegram API ID and hash, obtainable through my.telegram.org
- (Optional) A Telegram bot token, obtainable via BotFather if operating in bot mode.

## Installation

Clone the repository:

```bash
git clone https://your-repository-url.git
cd your-repository-directory
```

Install dependencies:

```bash
pip install telethon
```

Configure your credentials:

Rename credentials_telegram.json.example to credentials_telegram.json and fill in your Telegram API credentials and bot token (if using a bot).


```bash
{
  "api_id": "YOUR_API_ID",
  "api_hash": "YOUR_API_HASH",
  "bot_token": "YOUR_BOT_TOKEN" // Optional for bot use
}
```

## Usage

Run the script to start listening for and processing messages:

```bash
python tg_message_listener_main.py
```
## Structure

__tg_message_listener_main.py__: The main script that initializes the Telegram client and sets up event listeners for incoming messages.

Listener Modules: 

Separate scripts like __dexscreener_tg_message_listener.py__, __dextools_tg_message_listener.py__, and __direct_address_tg_listener.py__ that define specific processing logic for different message types.

## Contributing

Contributions are welcome! If you have ideas for new features, improvements, or bug fixes, feel free to fork the repository, make your changes, and submit a pull request. For major changes, please open an issue first to discuss what you would like to change.

## Support

For issues, questions, or contributions, please open an issue in the GitHub repository.

Feedback and contributions are welcome!

## License

This project is licensed under the MIT License - see the LICENSE file for details.
