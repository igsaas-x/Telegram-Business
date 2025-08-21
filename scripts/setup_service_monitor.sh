#!/bin/bash

# Setup script for Telethon Service Monitor
# This script sets up the service monitor to run as a systemd service

set -e

echo "Setting up Telethon Service Monitor..."

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root (use sudo)" 
   exit 1
fi

# Define paths
SERVICE_DIR="/root/telegram-listener"
SERVICE_FILE="/etc/systemd/system/telethon-service-monitor.service"
CURRENT_DIR=$(pwd)

# Check if service directory exists
if [ ! -d "$SERVICE_DIR" ]; then
    echo "Error: Service directory $SERVICE_DIR does not exist"
    echo "Please ensure your telegram listener is installed in $SERVICE_DIR"
    exit 1
fi

# Copy service monitor script to service directory
echo "Copying service monitor to $SERVICE_DIR..."
cp "$CURRENT_DIR/service_monitor.py" "$SERVICE_DIR/"
chmod +x "$SERVICE_DIR/service_monitor.py"

# Copy systemd service file
echo "Installing systemd service..."
cp "$CURRENT_DIR/.github/service/telethon-service-monitor.service" "$SERVICE_FILE"

# Reload systemd and enable service
echo "Enabling and starting service monitor..."
systemctl daemon-reload
systemctl enable telethon-service-monitor.service

# Check if main telethon service exists and is enabled
if systemctl list-unit-files | grep -q "mytelethon.service"; then
    echo "Found main telethon service (mytelethon.service)"
else
    echo "Warning: Main telethon service (mytelethon.service) not found"
    echo "Make sure to set up the main service first"
fi

echo ""
echo "Service monitor setup complete!"
echo ""
echo "Important: Before starting the service, make sure to:"
echo "1. Add ADMIN_ALERT_CHAT_ID to your .env file"
echo "2. Ensure ADMIN_BOT_TOKEN is set in your .env file"
echo ""
echo "Environment variables needed in /root/telegram-listener/.env:"
echo "  ADMIN_BOT_TOKEN=your_admin_bot_token_here"
echo "  ADMIN_ALERT_CHAT_ID=your_admin_group_chat_id_here"
echo ""
echo "Commands to manage the service monitor:"
echo "  sudo systemctl start telethon-service-monitor    # Start the monitor"
echo "  sudo systemctl stop telethon-service-monitor     # Stop the monitor"
echo "  sudo systemctl status telethon-service-monitor   # Check status"
echo "  sudo journalctl -u telethon-service-monitor -f   # View logs"
echo ""
echo "The monitor will:"
echo "  - Check every 60 seconds if main telethon service is running"
echo "  - Send alerts to admin group if service goes down"
echo "  - Rate limit alerts (max once every 30 minutes)"
echo "  - Send recovery notification when service comes back up"