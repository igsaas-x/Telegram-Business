# Database Migration Scripts

This directory contains utility scripts for database migrations and data processing.

## Parse ABA Sender Names

Scripts to extract sender names from existing ABA bank messages and populate the `paid_by_name` column.

### Configuration

Both scripts target:
- **Chat ID**: `-1002875564121`
- **Time Range**: Last 3 days
- **Message Type**: ABA bank messages only (with `paid_by` field)

### Option 1: Python Script (Recommended)

The Python script uses the application's existing parser logic and provides better Unicode support for Khmer text.

**Prerequisites:**
- Python environment with application dependencies installed
- Database credentials configured in `.env` file

**Usage:**
```bash
# From project root
python3 migrations/scripts/parse_aba_sender_names.py
```

**Features:**
- ✅ Full Khmer Unicode support
- ✅ Uses the same parser as the main application
- ✅ Detailed logging and progress reporting
- ✅ Safe rollback on errors
- ✅ Shows before/after comparison
- ✅ Statistics summary

**Output:**
```
============================================================
Starting ABA sender name parsing
Chat ID: -1002875564121
Days back: 3
============================================================
Found 45 messages to process
ID 12345: Set name to 'ពៅ សុនី'
ID 12346: Set name to 'KHAN SAMBO'
...
============================================================
Processing complete!
Total messages processed: 45
Names updated: 42
Already set correctly: 2
Names not found: 1
Errors: 0
============================================================
```

### Option 2: SQL Script (Direct Database)

The SQL script runs directly on MySQL and uses REGEXP for extraction.

**Prerequisites:**
- MySQL 8.0+ (required for `REGEXP_SUBSTR` and `REGEXP_REPLACE`)
- Direct database access

**Usage:**
```bash
# Connect to MySQL and run the script
mysql -u your_user -p your_database < migrations/scripts/parse_aba_sender_names.sql

# Or run from MySQL console
mysql> source migrations/scripts/parse_aba_sender_names.sql
```

**Features:**
- ✅ Fast direct database updates
- ✅ Preview query to check before running
- ⚠️ Limited Khmer support (depends on MySQL collation)
- ✅ Summary statistics
- ✅ Sample results display

**Preview Before Running:**

Uncomment the preview `SELECT` statement in the SQL file to see what will be updated before running the `UPDATE`.

### Patterns Supported

Both scripts support these ABA message patterns:

1. **English with account number**: `paid by CHOR SEIHA (*655)`
2. **Khmer name, English format**: `paid by ពៅ សុនី (*670)`
3. **Khmer format with English name**: `ត្រូវបានបង់ដោយ KHAN SAMBO (*435)`
4. **Khmer format with Khmer name**: `ត្រូវបានបង់ដោយ ចាន់ ធីតា (*111)`
5. **With bank suffix**: `paid by SOYANUK SAMOEURN, ABA Bank`
6. **With bank in parentheses**: `credited by CHANRAINGSEY NORATH (ABA Bank)`
7. **Khmer with location marker**: `ត្រូវបានបង់ដោយ NAME នៅ LOCATION`

### Customization

To modify the target chat or date range:

**Python Script:**
Edit variables at the top of `parse_aba_sender_names.py`:
```python
CHAT_ID = -1002875564121  # Change chat ID
DAYS_BACK = 3             # Change number of days
```

**SQL Script:**
Edit variables at the top of `parse_aba_sender_names.sql`:
```sql
SET @chat_id = -1002875564121;  -- Change chat ID
SET @days_back = 3;              -- Change number of days
```

### Verification

After running, verify the results:

```sql
-- Check updated records
SELECT
    id,
    income_date,
    paid_by,
    paid_by_name,
    LEFT(message, 80) AS message_preview
FROM income_balance
WHERE chat_id = -1002875564121
    AND income_date >= DATE_SUB(NOW(), INTERVAL 3 DAY)
    AND paid_by IS NOT NULL
ORDER BY income_date DESC;

-- Statistics
SELECT
    COUNT(*) AS total_messages,
    COUNT(paid_by_name) AS names_extracted,
    COUNT(*) - COUNT(paid_by_name) AS names_missing
FROM income_balance
WHERE chat_id = -1002875564121
    AND income_date >= DATE_SUB(NOW(), INTERVAL 3 DAY)
    AND paid_by IS NOT NULL;
```

### Troubleshooting

**Names not extracting:**
- Check message format matches supported patterns
- Verify Khmer text encoding (UTF-8)
- For SQL: Ensure MySQL collation supports Unicode (`utf8mb4_unicode_ci`)

**Permission errors:**
- Ensure database user has UPDATE privileges
- For Python: Check `.env` file has correct credentials

**Python import errors:**
- Run from project root directory
- Ensure virtual environment is activated
- Install dependencies: `pip install -r requirements.txt`
