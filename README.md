# Telegram Restaurant Management Bot

A comprehensive Telegram bot system for restaurant management with multi-bot architecture, income tracking, shift management, package subscription, and automated reporting capabilities.

## Architecture Overview

This project implements a **multi-bot architecture** with specialized bots for different purposes:

- **Standard Bot**: Core bot handling general operations, income tracking, and basic features
- **Business Bot**: Advanced features for BUSINESS package subscribers (custom reports, advanced analytics)
- **Admin Bot**: Administrative operations and system management
- **Private Bot**: Handle private conversations and user-specific operations
- **Utils Bot**: Utility functions and helper operations
- **Custom Business Bot**: Optional customizable business operations (configurable)

All bots work together through a centralized **BotRegistry** that enables cross-bot communication and coordination.

## Key Features

### Income & Balance Management
- Real-time income message processing from multiple currencies (USD, KHR, THB)
- Automated balance calculations and tracking
- Income history with detailed transaction logs
- Multi-shift income tracking and reporting

### Shift Management System
- Multiple shifts per day with customizable schedules
- Shift permissions and access control
- Automatic shift closing based on schedule
- Shift-based income reporting and summaries
- Real-time shift status tracking

### Package Management
- **TRIAL**: 7-day trial with basic features
- **STANDARD**: Standard subscription with core features
- **BUSINESS**: Premium subscription with advanced features
  - Custom report creation and scheduling
  - Advanced analytics and insights
  - Extended data retention

### Custom Report Framework
- Create custom SQL-based reports for data analysis
- Schedule reports to run automatically at specific times (ICT timezone)
- Manual execution via menu interface
- SQL injection protection with query validation
- Support for multi-currency aggregation
- Formatted output in Khmer language with icons and styling

### Automated Schedulers
- **Daily Summary Scheduler**: Sends daily income summaries at configured times
- **Auto Close Scheduler**: Automatically closes shifts based on schedule
- **Package Expiry Scheduler**: Monitors and notifies about package expirations
- **Trial Expiry Scheduler**: Tracks trial period expirations
- **Custom Report Scheduler**: Executes scheduled custom reports

### Menu-Driven Interface
- Interactive inline keyboard menus
- Context-aware menu options based on package type
- Feature flag system for package-based functionality
- Multi-language support (Khmer primary)

### Additional Features
- Threshold warning system for income monitoring
- QR code generation for payments and references
- User and group management
- Conversation state tracking
- Comprehensive logging with force-write capability

## Project Structure

```
tg-message-listener-main/
├── models/                      # Database models (SQLAlchemy)
│   ├── chat_model.py
│   ├── user_model.py
│   ├── income_balance_model.py
│   ├── shift_model.py
│   ├── group_package_model.py
│   ├── custom_report_model.py
│   └── ...
├── services/                    # Business logic services
│   ├── handlers/               # Message and callback handlers
│   │   └── menu_handler.py    # Main menu system
│   ├── telegram_standard_bot_service.py
│   ├── telegram_business_bot_service.py
│   ├── telegram_admin_bot_service.py
│   ├── telegram_private_bot_service.py
│   ├── telegram_utils_bot_service.py
│   ├── custom_report_service.py
│   ├── income_balance_service.py
│   ├── shift_service.py
│   ├── group_package_service.py
│   ├── bot_registry.py        # Central bot registry
│   └── ...
├── schedulers/                  # Automated task schedulers
│   ├── auto_close_scheduler.py
│   ├── daily_summary_scheduler.py
│   ├── trial_expiry_scheduler.py
│   ├── package_expiry_scheduler.py
│   ├── custom_report_scheduler.py
│   └── ...
├── helper/                      # Helper functions and utilities
│   ├── date_utils.py
│   ├── logger_utils.py
│   ├── custom_report_helper.py
│   └── ...
├── migrations/                  # Database migrations (Alembic)
│   └── versions/
├── config/                      # Configuration management
├── common/                      # Common utilities and enums
├── handlers/                    # Legacy handlers
├── listeners/                   # Telethon listeners (optional)
├── docs/                        # Documentation
│   └── custom-report-framework-blueprint.md
├── logs/                        # Application logs
├── scripts/                     # Utility scripts
├── tests/                       # Test files
├── main_bots_only.py           # Main entry point (bot-only mode)
├── main_telethon_only.py       # Telethon client mode (optional)
├── alembic.ini                 # Alembic configuration
├── requirements.txt            # Python dependencies
└── .env                        # Environment variables
```

## Technology Stack

- **Python**: 3.6+
- **Bot Framework**: python-telegram-bot 22.2
- **ORM**: SQLAlchemy 2.0+
- **Database**: MySQL with mysql-connector-python
- **Migrations**: Alembic 1.12+
- **Scheduling**: schedule library
- **Async**: asyncio for concurrent operations
- **Telethon**: 1.40+ (optional, for client operations)
- **Monitoring**: New Relic APM (optional)
- **Additional**: pytz, qrcode, Pillow, reportlab

## Prerequisites

- Python 3.6 or higher
- MySQL database server
- Telegram Bot API tokens (obtain from [@BotFather](https://t.me/BotFather))
  - Standard bot token (required)
  - Business bot token (optional)
  - Admin bot token (optional)
  - Private bot token (optional)
  - Utils bot token (optional)
- (Optional) Telegram API credentials for Telethon client mode

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/your-repository-url.git
cd tg-message-listener-main
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file in the project root:

```bash
# Database Configuration
DB_NAME=telegram_bot
DB_USER=root
DB_PASSWORD=your_password
DB_HOST=localhost

# Bot Tokens (required)
BOT_TOKEN=your_standard_bot_token
BOT_NAME=YourBotName

# Optional Bot Tokens
ADMIN_BOT_TOKEN=your_admin_bot_token
AUTOSUM_BUSINESS_BOT_TOKEN=your_business_bot_token
PRIVATE_CHAT_BOT_TOKEN=your_private_bot_token
UTILS_BOT_TOKEN=your_utils_bot_token
AUTOSUM_BUSINESS_CUSTOM_BOT_TOKEN=your_custom_business_bot_token

# Telethon (optional, for client mode)
PHONE_NUMBER=+1234567890
API_ID=your_api_id
API_HASH=your_api_hash

# Optional Configuration
CHAT_ID=your_default_chat_id
```

### 4. Initialize the database

The application will automatically run migrations on startup using Alembic. Ensure your MySQL database is created and accessible.

Alternatively, run migrations manually:

```bash
alembic upgrade head
```

## Usage

### Running Bot-Only Mode (Recommended)

Start all configured bots:

```bash
python main_bots_only.py
```

This will:
1. Run database migrations automatically
2. Start all configured bot services
3. Initialize all schedulers
4. Register signal handlers for graceful shutdown

### Running Telethon Client Mode (Optional)

For Telethon-based operations:

```bash
python main_telethon_only.py
```

### Service Management

The application runs continuously. To stop:
- Press `Ctrl+C` for graceful shutdown
- Or send `SIGTERM` / `SIGINT` signal

Logs are written to:
- `telegram_bots.log` (bot-only mode)
- `logs/telegram_bot_YYYYMMDD_HH.log` (hourly rotation)

## Custom Reports

### Creating Custom Reports

1. Navigate to the bot menu (BUSINESS package required)
2. Select "Custom Reports" (ការបញ្ជាក់របាយការណ៍ផ្ទាល់ខ្លួន)
3. Create a new report with:
   - Report name
   - Description (optional)
   - SQL query (SELECT statements only)
   - Schedule time (optional, format: HH:MM in ICT)
   - Enable/disable scheduling

### SQL Query Format

Queries must:
- Use `SELECT` statements only (no INSERT, UPDATE, DELETE, etc.)
- Use `:group_id` placeholder for current group's chat_id
- Return columns: `amount`, `currency`

Example:
```sql
SELECT amount, currency
FROM income_balance
JOIN shifts ON income_balance.shift_id = shifts.id
WHERE income_balance.chat_id = :group_id
  AND shifts.shift_date = CURDATE()
```

### Report Scheduling

- Schedules use ICT (Indochina Time) timezone
- Format: HH:MM (24-hour format)
- Reports execute daily at the specified time
- Results are sent automatically to the group

## Package Features Matrix

| Feature | TRIAL | STANDARD | BUSINESS |
|---------|-------|----------|----------|
| Income Tracking | ✓ | ✓ | ✓ |
| Shift Management | ✓ | ✓ | ✓ |
| Daily Summaries | ✓ | ✓ | ✓ |
| Basic Menus | ✓ | ✓ | ✓ |
| Custom Reports | ✗ | ✗ | ✓ |
| Report Scheduling | ✗ | ✗ | ✓ |
| Advanced Analytics | ✗ | ✗ | ✓ |

## Development

### Database Migrations

Create a new migration:
```bash
alembic revision -m "description of changes"
```

Apply migrations:
```bash
alembic upgrade head
```

Rollback migration:
```bash
alembic downgrade -1
```

### Adding New Features

1. Create model in `models/` if needed
2. Create migration with Alembic
3. Implement service in `services/`
4. Add handler in `services/handlers/`
5. Update menu in `menu_handler.py`
6. Add scheduler if automation needed

### Testing

Run tests:
```bash
python -m pytest tests/
```

## Deployment

### Production Setup

1. Configure environment variables in production
2. Set up MySQL database with proper credentials
3. Configure systemd service or supervisor for process management
4. Set up log rotation for application logs
5. (Optional) Configure New Relic for APM monitoring

### Example Systemd Service

Create `/etc/systemd/system/telegram-bot.service`:

```ini
[Unit]
Description=Telegram Restaurant Bot
After=network.target mysql.service

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/tg-message-listener-main
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/python main_bots_only.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable telegram-bot
sudo systemctl start telegram-bot
sudo systemctl status telegram-bot
```

View logs:
```bash
sudo journalctl -u telegram-bot -f
```

## Security Considerations

- **SQL Injection Prevention**: Custom report queries are validated against dangerous keywords
- **Query Timeout**: All queries have a 30-second timeout limit
- **Feature Flags**: Advanced features require proper package subscription
- **Environment Variables**: Sensitive credentials stored in `.env` (never commit)
- **Session Management**: SQLAlchemy sessions properly managed with context managers

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

For major changes, please open an issue first to discuss what you would like to change.

## Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Check existing documentation in `docs/`
- Review logs in `logs/` directory

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- python-telegram-bot library for the excellent Telegram Bot API wrapper
- SQLAlchemy for robust ORM capabilities
- Alembic for database migration management
- The Telegram Bot API team for comprehensive documentation
