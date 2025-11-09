# Sender Management Bot Setup

## 🤖 Overview

The Sender Management Bot is a **dedicated standalone bot** for managing sender configurations and generating sender reports. It runs independently from the business bot.

---

## 🔧 Setup Instructions

### 1. Create a New Bot with BotFather

1. Open Telegram and message [@BotFather](https://t.me/BotFather)
2. Send `/newbot`
3. Follow the prompts:
   - Bot name: `Sender Manager` (or your preferred name)
   - Username: `your_sender_bot` (must end with 'bot')
4. BotFather will give you a **bot token** - save this!

Example token: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`

### 2. Add Token to Environment

Add the bot token to your `.env` file:

```bash
# Sender Management Bot
SENDER_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
```

### 3. Restart the Application

```bash
# If running with systemd
sudo systemctl restart telegram-bots

# Or if running directly
python3 main_bots_only.py
```

### 4. Verify Bot is Running

Check the logs:

```bash
tail -f telegram_bots.log | grep "SenderManagementBot"
```

You should see:
```
Starting Sender Management bot...
SenderManagementBot setup completed
SenderManagementBot polling started successfully
```

---

## 📱 Adding Bot to Groups

1. Search for your bot in Telegram: `@your_sender_bot`
2. Add it to your group
3. Make sure the bot has permission to:
   - ✅ Read messages
   - ✅ Send messages
   - ✅ Delete messages (optional, for cleanup)

---

## 🎯 Available Commands

Once the bot is in your group, you can use:

| Command | Description |
|---------|-------------|
| `/start` | Welcome message and overview |
| `/help` | Detailed help message |
| `/sender_add` | Add new sender (interactive) |
| `/sender_delete` | Delete sender (interactive) |
| `/sender_update` | Update sender name (interactive) |
| `/sender_list` | List all configured senders |
| `/sender_report` | Generate today's report grouped by sender |
| `/cancel` | Cancel current operation |

---

## 📋 Usage Examples

### Adding a Sender

```
You: /sender_add
Bot: Please reply with the account number (last 3 digits):

You: 708
Bot: ✅ Account number: *708
     Please reply with the sender name:

You: John Doe
Bot: ✅ Sender added: 708 (John Doe)
```

### Viewing Reports

```
You: /sender_report
Bot:
  📊 Daily Sender Report - 2025-11-08
  Total Transactions: 12

  ✅ CONFIGURED SENDERS
  ────────────────────────────────────────
  *708 (John Doe)
    5 txn | $150.00 | ៛50,000

  *332 (Jane Smith)
    3 txn | $75.00

  ⚠️ UNKNOWN SENDERS
  ────────────────────────────────────────
  *999 (not configured)
    2 txn | $30.00

  ❓ NO SENDER INFO
  ────────────────────────────────────────
  2 txn | $45.00

  📈 OVERALL SUMMARY
  ────────────────────────────────────────
  Total: $300.00 | ៛50,000
```

---

## 🔐 Security Notes

- ✅ The bot only responds in groups where it's been added
- ✅ No special permissions or package checks required
- ✅ Each group has its own isolated sender configurations
- ✅ Conversation states timeout after 5 minutes

---

## 🐛 Troubleshooting

### Bot doesn't respond to commands

**Check:**
1. Bot token is correct in `.env`
2. Application was restarted after adding token
3. Bot is added to the group
4. Bot has permission to read/send messages

**Debug:**
```bash
# Check if bot is running
tail -f telegram_bots.log | grep "SenderManagementBot"

# Test bot token
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()
token = os.getenv('SENDER_BOT_TOKEN')
print(f'Token: {token[:10]}...' if token else 'Token not found')
"
```

### Commands work but conversations don't continue

**Possible causes:**
- Conversation timed out (5 minutes of inactivity)
- Bot was restarted (conversation state is in-memory)
- Multiple users trying to use commands simultaneously

**Solution:**
- Use `/cancel` and start over
- Ensure you reply within 5 minutes
- Each user has their own conversation state

### Report shows no data

**Check:**
1. Are there transactions for today?
2. Do transactions have `paid_by` field populated?
3. Are senders configured?

**Verify:**
```sql
-- Check if transactions exist for today
SELECT COUNT(*)
FROM income_balance
WHERE chat_id = YOUR_CHAT_ID
AND DATE(income_date) = CURDATE();

-- Check if paid_by is populated
SELECT paid_by, COUNT(*)
FROM income_balance
WHERE chat_id = YOUR_CHAT_ID
AND DATE(income_date) = CURDATE()
GROUP BY paid_by;
```

---

## 🔄 Updating the Bot

When you update the code:

```bash
# Pull latest code
git pull

# Restart the application
sudo systemctl restart telegram-bots

# Or if running directly
# Ctrl+C to stop, then:
python3 main_bots_only.py
```

**Note:** Conversation states are in-memory and will be lost on restart.

---

## 📊 Monitoring

### Check Bot Status

```bash
# View recent logs
tail -100 telegram_bots.log | grep "Sender"

# Monitor in real-time
tail -f telegram_bots.log | grep -E "Sender|ERROR"
```

### Performance

- ✅ Handles multiple groups simultaneously
- ✅ Each group has isolated configurations
- ✅ Conversation states auto-cleanup after 5 minutes
- ✅ Database queries are optimized with proper indexing

---

## 📞 Support

If you encounter issues:

1. Check the logs: `telegram_bots.log`
2. Verify `.env` configuration
3. Ensure database migration is applied: `python3 -m alembic upgrade head`
4. Test in a private test group first

---

## ✅ Checklist

Before using in production:

- [ ] Bot token added to `.env`
- [ ] Database migration applied
- [ ] Application restarted
- [ ] Bot added to test group
- [ ] Tested `/sender_add` flow
- [ ] Tested `/sender_report` command
- [ ] Verified reports are accurate
- [ ] Monitoring/logging configured
