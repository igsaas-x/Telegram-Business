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

# Import directly from modules to avoid circular imports
from sqlalchemy import and_, create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

# Direct imports to avoid package __init__.py circular dependencies
import importlib.util

def load_module_from_path(module_name, file_path):
    """Load a module directly from file path"""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

# Get the project root
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))

# Load configuration
try:
    import dotenv
    dotenv.load_dotenv(os.path.join(PROJECT_ROOT, '.env'))
except ImportError:
    print("Warning: python-dotenv not installed. Make sure environment variables are set.")
    print("Install with: pip install python-dotenv")

# Database connection
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '3306')
DB_NAME = os.getenv('DB_NAME')

DATABASE_URL = f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Create engine and session
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@contextmanager
def get_db_session():
    """Context manager for database sessions"""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

# Load the IncomeBalance model directly
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, BigInteger, DateTime, Text

Base = declarative_base()

class IncomeBalance(Base):
    """Simplified IncomeBalance model for migration script"""
    __tablename__ = "income_balance"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    chat_id = Column(BigInteger, nullable=False)
    income_date = Column(DateTime, nullable=False)
    message = Column(Text, nullable=False)
    paid_by = Column(String(10), nullable=True)
    paid_by_name = Column(String(100), nullable=True)

    # Note: Only defining columns we need to read/update
    # This avoids foreign key issues with other tables

# Import the name extraction function
import re

# Khmer-aware name extraction pattern
# Supports: English letters, Khmer script, spaces, hyphens, apostrophes, dots
PAID_BY_NAME_PATTERN = re.compile(
    r'(?:paid|credited|ត្រូវបានបង់ដោយ)\s+(?:by\s+)?([A-Z\u1780-\u17FF][A-Z\u1780-\u17FF\s\-\'.]+?)(?:\s*\(\*\d{3}\)|\s*,\s*ABA Bank|\s*\(ABA Bank\)|\s+via|\s+នៅ)',
    re.IGNORECASE
)

def extract_paid_by_name(text: str):
    """Extract payer name from message"""
    match = PAID_BY_NAME_PATTERN.search(text)
    if match:
        name = match.group(1).strip()
        # Collapse multiple spaces into single space
        name = ' '.join(name.split())
        return name
    return None

def force_log(message: str, component: str = "Script", level: str = "INFO"):
    """Simple logging function"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] [{component}] {message}")


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
