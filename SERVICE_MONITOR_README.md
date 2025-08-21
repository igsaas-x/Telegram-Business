# Telethon Service Monitor

A standalone monitoring service that watches the main Telethon client service and sends alerts via the admin bot when the service goes down.

## Features

- **Autonomous Monitoring**: Runs independently of the main Telethon service
- **Dual Detection**: Monitors both system processes and systemd service status  
- **Smart Alerting**: Rate-limited alerts (max once every 30 minutes) to prevent spam
- **Recovery Notifications**: Sends notification when service comes back online
- **Telegram Integration**: Uses your admin bot to send alerts to admin group

## Setup Instructions

### 1. Environment Configuration

Add these variables to your `/root/telegram-listener/.env` file:

```bash
# Admin bot token (should already exist)
ADMIN_BOT_TOKEN=your_admin_bot_token_here

# Admin group chat ID for alerts (new variable)
ADMIN_ALERT_CHAT_ID=your_admin_group_chat_id_here
```

**To find your admin group chat ID:**
1. Add your admin bot to the admin group
2. Send a message in the group
3. Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
4. Look for the `"chat":{"id":` value (it will be negative for groups)

### 2. Installation

Run the setup script as root:

```bash
cd /root/telegram-listener
sudo ./scripts/setup_service_monitor.sh
```

This will:
- Copy the monitor script to the service directory
- Install the systemd service
- Enable auto-start on boot

### 3. Start the Monitor

```bash
sudo systemctl start telethon-service-monitor
```

## Management Commands

```bash
# Check status
sudo systemctl status telethon-service-monitor

# View logs (live)
sudo journalctl -u telethon-service-monitor -f

# View logs (last 100 lines)
sudo journalctl -u telethon-service-monitor -n 100

# Stop monitor
sudo systemctl stop telethon-service-monitor

# Restart monitor
sudo systemctl restart telethon-service-monitor

# Disable auto-start
sudo systemctl disable telethon-service-monitor
```

## Testing

Test the monitor functionality before deployment:

```bash
cd /root/telegram-listener
python3 test_service_monitor.py
```

This will:
- Test service detection
- Verify bot configuration
- Send a test alert message
- Display configuration summary

## How It Works

The monitor performs these checks every 60 seconds:

1. **Process Check**: Searches for `python3 main_telethon_only.py` in running processes
2. **Systemd Check**: Checks if `mytelethon.service` is active
3. **Alert Logic**: 
   - Service is considered running if either check passes
   - Alerts only after 3 consecutive failures
   - Rate-limited to prevent spam
   - Sends recovery notification when service restarts

## Alert Examples

### Service Down Alert
```
🚨 **Telethon Service Down**

The main Telethon client service appears to be stopped or crashed.

**Details:**
- Service: main_telethon_only.py
- Check method: Process monitoring + Systemd
- Consecutive failures: 3
- Time: 2024-08-21 14:30:45

**Action Required:**
Please check the server and restart the service if necessary.

**Commands to check:**
```
sudo systemctl status mytelethon
sudo systemctl restart mytelethon
ps aux | grep main_telethon_only.py
```
```

### Recovery Alert
```
✅ **Service Monitor Alert**

🎉 **Telethon Service Recovered**

The main Telethon client service is now running normally.

⏰ 2024-08-21 14:35:22
```

## Configuration

Key settings in `service_monitor.py`:

- `check_interval = 60` - Check every 60 seconds
- `alert_cooldown = timedelta(minutes=30)` - Max one alert per 30 minutes  
- `max_consecutive_failures = 3` - Alert after 3 failed checks
- `service_command_pattern = "python3 main_telethon_only.py"` - Process to monitor

## Logs

Monitor logs are written to:
- **System journal**: `journalctl -u telethon-service-monitor`
- **File**: `/root/telegram-listener/service_monitor.log`

## Security

The systemd service runs with these security settings:
- `NoNewPrivileges=yes`
- `ProtectSystem=strict` 
- `ProtectHome=yes`
- `PrivateTmp=yes`
- Read/write access only to `/root/telegram-listener`

## Troubleshooting

### Monitor won't start
- Check environment variables are set in `.env`
- Verify admin bot token is valid
- Ensure admin chat ID is correct (negative number for groups)

### No alerts received
- Test with `python3 test_service_monitor.py`
- Check bot is added to admin group
- Verify admin group chat ID is correct
- Check monitor logs for errors

### False alarms
- Adjust `max_consecutive_failures` in the script
- Check if main service is actually running
- Verify systemd service name matches (`mytelethon`)

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Telethon Client │    │ Service Monitor  │    │ Admin Group     │
│ (main service)  │    │ (this monitor)   │    │ (alerts)        │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                        │
         │                        │                        │
         ▼                        ▼                        ▼
  ┌─────────────┐       ┌──────────────┐       ┌──────────────┐
  │ systemd     │◄──────│ Monitor      │──────►│ Admin Bot    │
  │ mytelethon  │       │ Checks       │       │ Messages     │
  └─────────────┘       └──────────────┘       └──────────────┘
```

The monitor runs independently and can detect when the main service fails, ensuring reliable monitoring even if the main application crashes.