# Group by Sender - System Architecture

## 🏗️ Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    TELEGRAM BOT                             │
│                  (business_plus_bot)                        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ Commands
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                  COMMAND HANDLERS                           │
│  /sender_add  /sender_delete  /sender_list  /sender_report  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │
                     │
        ┌────────────┴────────────┐
        ▼                         ▼
┌──────────────────┐    ┌──────────────────────┐
│ SenderConfig     │    │ SenderReport         │
│ Service          │    │ Service              │
├──────────────────┤    ├──────────────────────┤
│ - add_sender()   │    │ - generate_daily()   │
│ - delete_sender()│    │ - get_by_sender()    │
│ - get_senders()  │    │ - get_summary()      │
│ - update_sender()│    │ - format_report()    │
└────────┬─────────┘    └──────────┬───────────┘
         │                         │
         ▼                         ▼
┌─────────────────────────────────────────────────────────────┐
│                      DATABASE LAYER                         │
│  Note: chat_id = Telegram Group ID (no FK relationships)    │
├────────────────────────┬────────────────────────────────────┤
│  sender_configs        │  income_balance                    │
│  ├─ id (PK)            │  ├─ id (PK)                        │
│  ├─ chat_id (TG ID)    │  ├─ chat_id (TG ID)                │
│  ├─ sender_account_    │  ├─ amount                         │
│  │   number (3 digits) │  ├─ currency                       │
│  ├─ sender_name        │  ├─ paid_by (3 digits) ◄───┐       │
│  ├─ is_active          │  ├─ income_date            │       │
│  └─ created_at         │  └─ ...                    │       │
└────────────────────────┴────────────────────────────┼───────┘
                                                      │
        JOIN: chat_id = chat_id AND paid_by = sender_account_number
```

## 🔄 Data Flow

### 1. Adding a Sender
```
User: /sender_add
  │
  ├──> Bot: "Please reply with the account number (last 3 digits):"
  │
User: 708
  │
  ├──> Validate: Is it 3 digits?
  │     └─> Yes ✓
  │
  ├──> Check: Does sender already exist for this chat_id?
  │     └─> No ✓
  │
  ├──> Bot: "Please reply with the sender name:"
  │
User: John Doe
  │
  ├──> Insert into sender_configs
  │     chat_id: 123456 (Telegram Group ID)
  │     sender_account_number: "708"
  │     sender_name: "John Doe"
  │
  └──> Response: ✅ Sender added: 708 (John Doe)
```

### 2. Generating Daily Report
```
User: /sender_report
  │
  ├──> Get all configured senders for this Telegram group
  │     SELECT sender_account_number
  │     FROM sender_configs
  │     WHERE chat_id = 123456 (Telegram Group ID)
  │     └─> ["708", "332", "445"]
  │
  ├──> Query income_balance for today
  │     SELECT *
  │     FROM income_balance
  │     WHERE chat_id = 123456 (Telegram Group ID)
  │     AND DATE(income_date) = '2025-11-09'
  │
  ├──> Group transactions by paid_by
  │     ├─ "708": 5 transactions, $150, ៛50,000 (configured)
  │     ├─ "332": 3 transactions, $75, ៛0 (configured)
  │     ├─ "999": 2 transactions, $30, ៛0 (unknown - not in config)
  │     └─ NULL: 1 transaction, $15, ៛0 (no sender info)
  │
  ├──> Format report with blocks
  │     ├─ ✅ Configured senders (708, 332)
  │     ├─ ⚠️ Unknown senders (999)
  │     └─ ❓ No sender info (NULL)
  │
  └──> Send formatted message to chat
```

## 📊 Database Schema

**Note**: `chat_id` is the Telegram chat group ID (BigInteger), NOT a database foreign key.
There are no FK relationships - joins are based on matching `chat_id` values.

```sql
┌─────────────────────────────────────┐
│   sender_configs                    │
├─────────────────────────────────────┤
│  id (PK, AUTO_INCREMENT)            │
│  chat_id (BIGINT) ← Telegram ID     │
│  sender_account_number (VARCHAR(3)) │
│  sender_name (VARCHAR(100))         │
│  is_active (BOOLEAN)                │
│  created_at (DATETIME)              │
│  updated_at (DATETIME)              │
│                                     │
│  UNIQUE(chat_id, sender_account_number)
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│   income_balance                    │
├─────────────────────────────────────┤
│  id (PK, AUTO_INCREMENT)            │
│  chat_id (BIGINT) ← Telegram ID     │
│  amount (FLOAT)                     │
│  currency (VARCHAR(16))             │
│  paid_by (VARCHAR(10)) ← last 3 digits
│  income_date (DATETIME)             │
│  ...                                │
└─────────────────────────────────────┘

REPORT QUERY:
  -- Join on chat_id AND paid_by to get sender names
  SELECT
    ib.*,
    sc.sender_name,
    sc.sender_account_number
  FROM income_balance ib
  LEFT JOIN sender_configs sc
    ON ib.chat_id = sc.chat_id
    AND ib.paid_by = sc.sender_account_number
  WHERE ib.chat_id = ?              -- Telegram group ID
    AND DATE(ib.income_date) = ?
    AND sc.is_active = 1
```

## 🔐 Access Control

### Simple Bot-Based Access

```
                    ┌─────────────────┐
                    │  User Request   │
                    │  in Group       │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │ Is bot present  │
                    │ in this group?  │
                    └────┬───────┬────┘
                     NO  │       │  YES
                    ┌────▼────┐  │
                    │ IGNORE  │  │
                    │ (Silent)│  │
                    └─────────┘  │
                              ┌──▼────────┐
                              │  ALLOW ✓  │
                              │ Execute   │
                              │ Command   │
                              └───────────┘
```

**Access Model**:
- ✅ Bot is added to group → Features available
- ❌ Bot not in group → No response
- No package checks, no feature flags

## 📈 Reporting Logic

### Daily Summary Calculation
```python
def generate_daily_summary(chat_id, date):
    # 1. Get all configured senders
    configured = get_all_senders(chat_id)
    # → ["708", "332", "445"]

    # 2. Get all transactions for the date
    transactions = get_daily_transactions(chat_id, date)
    # → [
    #     {paid_by: "708", amount: 50, currency: "USD"},
    #     {paid_by: "708", amount: 30, currency: "USD"},
    #     {paid_by: "999", amount: 20, currency: "USD"},
    #     {paid_by: None, amount: 15, currency: "USD"},
    #   ]

    # 3. Group by paid_by
    grouped = {
        "configured": {},   # Senders in configuration
        "unknown": {},      # paid_by not in configuration
        "no_sender": []     # paid_by is NULL
    }

    for txn in transactions:
        if txn.paid_by is None:
            grouped["no_sender"].append(txn)
        elif txn.paid_by in configured:
            grouped["configured"][txn.paid_by].append(txn)
        else:
            grouped["unknown"][txn.paid_by].append(txn)

    # 4. Calculate totals for each group
    # 5. Format and return
    return format_report(grouped)
```

## 🎯 Implementation Checklist

### Phase 1: Database ✓
- [ ] Create `sender_configs` table migration
- [ ] Create `SenderConfig` model
- [ ] Run migrations on dev/staging/prod
- [ ] Test CRUD operations

### Phase 2: Core Services ✓
- [ ] `SenderConfigService` - CRUD operations
- [ ] `SenderReportService` - Reporting logic
- [ ] `ConversationStateManager` - State tracking
- [ ] Write unit tests (80%+ coverage)

### Phase 3: Bot Integration ✓
- [ ] Create `business_plus_bot.py` handler
- [ ] Implement conversation state management
- [ ] Implement `/sender_add` interactive command
- [ ] Implement `/sender_delete` interactive command
- [ ] Implement `/sender_list` command
- [ ] Implement `/sender_update` interactive command
- [ ] Implement `/sender_report` command

### Phase 4: Testing ✓
- [ ] Unit tests for all services
- [ ] Integration tests for bot commands
- [ ] Test with real payment messages
- [ ] Test report formatting
- [ ] Load testing (1000+ transactions)

### Phase 5: Documentation ✓
- [ ] Update README with new commands
- [ ] Create user guide
- [ ] API documentation
- [ ] Deployment guide

## 🚦 Ready to Implement?

Blueprint is complete! Next steps:

1. **Review**: Go through blueprint and confirm requirements
2. **Start Phase 1**: Create database migrations
3. **Continue sequentially**: Follow the 5-phase plan

---

**Status**: ✅ Blueprint Approved - Ready for Development
