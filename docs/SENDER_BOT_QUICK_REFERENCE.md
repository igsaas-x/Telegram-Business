# Sender Bot - Quick Reference Card

## 🚀 Quick Setup

```bash
# 1. Create bot with @BotFather
# Get token from BotFather

# 2. Add to .env
echo "SENDER_BOT_TOKEN=your_token_here" >> .env

# 3. Restart application
python3 main_bots_only.py
```

## 📋 Bot Commands

| Command | Description | Type |
|---------|-------------|------|
| `/start` | Welcome message | Direct |
| `/help` | Show help | Direct |
| `/sender_add` | Add new sender | Interactive |
| `/sender_delete` | Delete sender | Interactive |
| `/sender_update` | Update sender name | Interactive |
| `/sender_list` | List all senders | Direct |
| `/sender_report` | Daily report | Direct |
| `/cancel` | Cancel operation | Direct |

## 🔄 Interactive Flows

### Add Sender
```
/sender_add → Account (3 digits) → Name → ✅ Done
```

### Delete Sender
```
/sender_delete → Shows list → Account to delete → ✅ Done
```

### Update Sender
```
/sender_update → Shows list → Account to update → New name → ✅ Done
```

## 📊 Report Format

```
📊 Daily Sender Report - 2025-11-08
Total Transactions: 12

✅ CONFIGURED SENDERS
*708 (John Doe): 5 txn | $150.00
*332 (Jane): 3 txn | $75.00

⚠️ UNKNOWN SENDERS
*999: 2 txn | $30.00

❓ NO SENDER INFO
2 txn | $45.00

📈 TOTAL: $300.00 | ៛50,000
```

## 🔧 Technical Details

**Service**: `services/telegram_sender_bot_service.py`
**Handler**: `services/handlers/sender_command_handler.py`
**Database**: `sender_configs` table
**Token**: `SENDER_BOT_TOKEN` environment variable
**Startup**: Integrated in `main_bots_only.py`

## 🐛 Troubleshooting

**Bot not responding?**
```bash
# Check if bot is running
tail -f telegram_bots.log | grep "SenderManagementBot"

# Should see:
# "SenderManagementBot polling started successfully"
```

**Commands not working?**
- Check bot has message permissions in group
- Verify conversation didn't timeout (5 min limit)
- Use `/cancel` and try again

**No data in reports?**
- Check if senders are configured: `/sender_list`
- Verify transactions have `paid_by` field populated
- Ensure date is today (reports are today only)

## 📁 Files

- `docs/SENDER_BOT_SETUP.md` - Full setup guide
- `docs/GROUP_BY_SENDER_IMPLEMENTATION_SUMMARY.md` - Implementation details
- `docs/GROUP_BY_SENDER_BLUEPRINT.md` - Feature specification
- `docs/GROUP_BY_SENDER_ARCHITECTURE.md` - System architecture

## ✅ Verification

```bash
# Test import
python3 -c "from services.telegram_sender_bot_service import SenderManagementBot; print('✅ OK')"

# Check logs
tail -20 telegram_bots.log | grep Sender
```

## 📞 Support

Environment variable not found? Check `.env` file.
Circular import errors? Restart Python shell.
Conversation stuck? Use `/cancel` command.

---

**Status**: ✅ Production Ready
**Version**: 1.0.0
**Last Updated**: 2025-11-08
