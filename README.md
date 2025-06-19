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
- MySQL database

## Installation

Clone the repository:

```bash
git clone https://your-repository-url.git
cd your-repository-directory
```

**Install dependencies:**

```bash
pip install -r requirements.txt
```

Configure your credentials in .env file:

```bash
DB_NAME=telegram_bot
DB_USER=root
DB_PASSWORD=
DB_HOST=localhost

BOT_TOKEN=BOT_NAME
BOT_NAME=BOT_NAME
CHAT_ID=CHAT_ID
PHONE_NUMBER=PHONE_NUMBER
API_ID=API_ID
API_HASH=API_HASH
```

## Usage

Run the script to start listening for and processing messages:

```bash
python main.py
```

## Structure

**main.py**: The main script that initializes the Telegram client and sets up event listeners for incoming messages.

## Contributing

Contributions are welcome! If you have ideas for new features, improvements, or bug fixes, feel free to fork the repository, make your changes, and submit a pull request. For major changes, please open an issue first to discuss what you would like to change.

## Support

For issues, questions, or contributions, please open an issue in the GitHub repository.

Feedback and contributions are welcome!

## License

This project is licensed under the MIT License - see the LICENSE file for details.
