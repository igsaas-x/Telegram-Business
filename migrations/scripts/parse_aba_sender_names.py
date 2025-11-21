#!/usr/bin/env python3
"""
Parse ABA Sender Names from Existing Messages

This script extracts sender names from ABA bank messages in the database
and updates the paid_by_name column.

Target: Last 3 days of messages for chat_id = -1002875564121

Usage:
    python3 migrations/scripts/parse_aba_sender_names.py
"""

import os
import sys
from datetime import datetime, timedelta

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from config.database_config import get_db_session
from models.income_balance_model import IncomeBalance
from helper.bot_parsers import extract_paid_by_name
from helper.logger_utils import force_log
from sqlalchemy import and_


# Configuration
CHAT_ID = -1002875564121
DAYS_BACK = 3


def parse_sender_names():
    """Parse and update sender names from existing messages"""

    force_log("=" * 60, "ParseSenderNames")
    force_log("Starting ABA sender name parsing", "ParseSenderNames")
    force_log(f"Chat ID: {CHAT_ID}", "ParseSenderNames")
    force_log(f"Days back: {DAYS_BACK}", "ParseSenderNames")
    force_log("=" * 60, "ParseSenderNames")

    # Calculate date threshold
    date_threshold = datetime.now() - timedelta(days=DAYS_BACK)

    with get_db_session() as session:
        try:
            # Query messages from last N days that have paid_by but no paid_by_name
            messages = session.query(IncomeBalance).filter(
                and_(
                    IncomeBalance.chat_id == CHAT_ID,
                    IncomeBalance.income_date >= date_threshold,
                    IncomeBalance.paid_by.isnot(None),
                    # Optionally only update if paid_by_name is currently NULL
                    # IncomeBalance.paid_by_name.is_(None)
                )
            ).all()

            force_log(f"Found {len(messages)} messages to process", "ParseSenderNames")

            if len(messages) == 0:
                force_log("No messages to process", "ParseSenderNames")
                return

            # Statistics
            stats = {
                'total': len(messages),
                'updated': 0,
                'already_set': 0,
                'not_found': 0,
                'errors': 0
            }

            # Process each message
            for msg in messages:
                try:
                    # Extract sender name from message text
                    extracted_name = extract_paid_by_name(msg.message)

                    if extracted_name:
                        # Check if name already set and different
                        if msg.paid_by_name:
                            if msg.paid_by_name == extracted_name:
                                stats['already_set'] += 1
                                force_log(
                                    f"ID {msg.id}: Name already set correctly: '{extracted_name}'",
                                    "ParseSenderNames"
                                )
                            else:
                                # Update to new extracted name
                                old_name = msg.paid_by_name
                                msg.paid_by_name = extracted_name
                                stats['updated'] += 1
                                force_log(
                                    f"ID {msg.id}: Updated name from '{old_name}' to '{extracted_name}'",
                                    "ParseSenderNames"
                                )
                        else:
                            # Set name for first time
                            msg.paid_by_name = extracted_name
                            stats['updated'] += 1
                            force_log(
                                f"ID {msg.id}: Set name to '{extracted_name}'",
                                "ParseSenderNames"
                            )
                    else:
                        stats['not_found'] += 1
                        force_log(
                            f"ID {msg.id}: Could not extract name from: {msg.message[:80]}...",
                            "ParseSenderNames",
                            "WARNING"
                        )

                except Exception as e:
                    stats['errors'] += 1
                    force_log(
                        f"ID {msg.id}: Error processing message: {e}",
                        "ParseSenderNames",
                        "ERROR"
                    )

            # Commit changes
            session.commit()

            # Print summary
            force_log("=" * 60, "ParseSenderNames")
            force_log("Processing complete!", "ParseSenderNames")
            force_log(f"Total messages processed: {stats['total']}", "ParseSenderNames")
            force_log(f"Names updated: {stats['updated']}", "ParseSenderNames")
            force_log(f"Already set correctly: {stats['already_set']}", "ParseSenderNames")
            force_log(f"Names not found: {stats['not_found']}", "ParseSenderNames")
            force_log(f"Errors: {stats['errors']}", "ParseSenderNames")
            force_log("=" * 60, "ParseSenderNames")

            # Show sample results
            if stats['updated'] > 0:
                force_log("\nSample of updated records:", "ParseSenderNames")
                updated_msgs = session.query(IncomeBalance).filter(
                    and_(
                        IncomeBalance.chat_id == CHAT_ID,
                        IncomeBalance.income_date >= date_threshold,
                        IncomeBalance.paid_by_name.isnot(None)
                    )
                ).order_by(IncomeBalance.income_date.desc()).limit(10).all()

                for msg in updated_msgs:
                    force_log(
                        f"  ID {msg.id}: {msg.income_date} | "
                        f"Paid by: {msg.paid_by} | "
                        f"Name: {msg.paid_by_name}",
                        "ParseSenderNames"
                    )

        except Exception as e:
            session.rollback()
            force_log(f"Fatal error: {e}", "ParseSenderNames", "ERROR")
            import traceback
            force_log(f"Traceback: {traceback.format_exc()}", "ParseSenderNames", "ERROR")
            raise

        finally:
            session.close()


if __name__ == "__main__":
    try:
        parse_sender_names()
    except KeyboardInterrupt:
        force_log("\nScript interrupted by user", "ParseSenderNames", "WARNING")
        sys.exit(1)
    except Exception as e:
        force_log(f"Script failed: {e}", "ParseSenderNames", "ERROR")
        sys.exit(1)
