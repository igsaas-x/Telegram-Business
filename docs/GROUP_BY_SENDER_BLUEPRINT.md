# Group by Sender Feature - Blueprint

## 📋 Overview
A feature flag-based system that allows business_plus_bot users to track and report income grouped by sender (using the last 3 digits of account numbers extracted from payment messages).

---

## 🎯 Requirements

### 1. Sender Configuration Management
- ✅ Add sender (last 3 digits + optional name/label)
- ✅ Delete sender from configuration
- ✅ List all configured senders
- ✅ Update sender details (name/label)

### 2. Daily Summary Reporting
- ✅ Generate daily income report grouped by sender
- ✅ Display each sender's income in separate blocks
- ✅ Show total for each sender
- ✅ Show unmatched/unknown senders separately
- ✅ Support multiple currencies (USD, KHR)

### 3. Access Control
- ✅ Available via dedicated business_plus_bot
- ✅ Bot must be added to group to use features

---

## 🗄️ Database Schema

### New Table: `sender_configs`

```sql
CREATE TABLE sender_configs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    chat_id BIGINT NOT NULL,
    sender_account_number VARCHAR(3) NOT NULL,  -- Last 3 digits (e.g., "708")
    sender_name VARCHAR(100),           -- Optional friendly name
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,

    UNIQUE KEY unique_sender_per_chat (chat_id, sender_account_number),
    INDEX idx_chat_id (chat_id),
    INDEX idx_sender_code (sender_account_number)
);
```

---

## 🔧 Service Layer Architecture

### 1. `SenderConfigService` (New)
**File**: `services/sender_config_service.py`

```python
class SenderConfigService:
    # CRUD Operations
    async def add_sender(chat_id, sender_code, sender_name=None) -> SenderConfig
    async def delete_sender(chat_id, sender_code) -> bool
    async def get_sender(chat_id, sender_code) -> SenderConfig | None
    async def get_all_senders(chat_id) -> list[SenderConfig]
    async def update_sender(chat_id, sender_code, sender_name) -> SenderConfig

    # Validation
    async def is_sender_configured(chat_id, sender_code) -> bool
    async def validate_sender_code(sender_code) -> bool  # Must be 3 digits
```

### 2. `SenderReportService` (New)
**File**: `services/sender_report_service.py`

```python
class SenderReportService:
    async def generate_daily_report(chat_id, target_date=None) -> str
    async def get_income_by_sender(chat_id, sender_code, start_date, end_date) -> list[IncomeBalance]
    async def get_daily_summary_by_sender(chat_id, target_date) -> dict
    # Returns: {
    #   "configured_senders": {
    #     "708": {"name": "John Doe", "transactions": [...], "total_usd": 100, "total_khr": 0},
    #     "332": {"name": "Jane Smith", "transactions": [...], "total_usd": 50, "total_khr": 50000}
    #   },
    #   "unknown_senders": {
    #     "999": {"transactions": [...], "total_usd": 25, "total_khr": 0}
    #   },
    #   "no_sender": {"transactions": [...], "total_usd": 10, "total_khr": 0}
    # }
```

### 3. `ConversationStateManager` (New)
**File**: `services/conversation_state_manager.py`

```python
from enum import Enum
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

class ConversationState(Enum):
    IDLE = "idle"
    WAITING_SENDER_CODE = "waiting_sender_code"
    WAITING_SENDER_NAME = "waiting_sender_name"
    WAITING_DELETE_CODE = "waiting_delete_code"
    WAITING_DELETE_CONFIRM = "waiting_delete_confirm"
    WAITING_UPDATE_CODE = "waiting_update_code"
    WAITING_UPDATE_NAME = "waiting_update_name"

class ConversationStateManager:
    def __init__(self):
        self.states: Dict[int, Dict[str, Any]] = {}
        self.timeout_seconds = 300  # 5 minutes

    def set_state(self, user_id: int, state: ConversationState, data: dict = None)
    def get_state(self, user_id: int) -> Optional[Dict[str, Any]]
    def clear_state(self, user_id: int)
    def update_data(self, user_id: int, key: str, value: Any)
    def get_data(self, user_id: int, key: str) -> Any
    def is_in_conversation(self, user_id: int) -> bool
    def cleanup_expired_states(self) -> int  # Returns number of cleaned states
```


---

## 🤖 Bot Commands (business_plus_bot)

### Command Structure

```
/sender_add                    - Start adding a sender (interactive)
/sender_delete                 - Start deleting a sender (interactive)
/sender_list                   - List all configured senders
/sender_update                 - Start updating a sender (interactive)
/sender_report [date]          - Generate grouped report
```

### Command Examples

#### Add Sender (Interactive Flow)

```bash
User: /sender_add

Bot: 👤 Add New Sender
     Please reply with the last 3 digits of the account number.

     Example: 708

User: 708

Bot: ✅ Account: 708

     Now, please provide a name for this sender (or type 'skip' to continue without a name).

     Example: John Doe

User: John Doe

Bot: ✅ Sender added successfully!

     Account: 708
     Name: John Doe
```

#### Add Sender (Skip Name)

```bash
User: /sender_add

Bot: 👤 Add New Sender
     Please reply with the last 3 digits of the account number.

User: 332

Bot: ✅ Account: 332

     Now, please provide a name for this sender (or type 'skip' to continue without a name).

User: skip

Bot: ✅ Sender added successfully!

     Account: 332
     Name: (not set)
```

#### Delete Sender (Interactive Flow)

```bash
User: /sender_delete

Bot: 🗑️ Delete Sender

     Current senders:
     1. 708 - John Doe
     2. 332 - Jane Smith
     3. 445 - Bob Wilson

     Please reply with the account number to delete (or 'cancel' to abort).

User: 708

Bot: ⚠️ Confirm Deletion

     Account: 708 (John Doe)

     Are you sure? Reply 'yes' to confirm or 'no' to cancel.

User: yes

Bot: ✅ Sender deleted successfully!
     Account 708 (John Doe) has been removed.
```

#### List Senders

```bash
User: /sender_list

Bot: 📋 Configured Senders (3)

     1. 708 - John Doe
     2. 332 - Jane Smith
     3. 445 - Bob Wilson

     Use /sender_add to add more senders.
```

#### Update Sender (Interactive Flow)

```bash
User: /sender_update

Bot: ✏️ Update Sender

     Current senders:
     1. 708 - John Doe
     2. 332 - Jane Smith
     3. 445 - Bob Wilson

     Please reply with the account number to update.

User: 708

Bot: ✏️ Update Sender: 708 (John Doe)

     Please reply with the new name for this sender.

User: John Smith

Bot: ✅ Sender updated successfully!

     Account: 708
     Old name: John Doe
     New name: John Smith
```

#### Generate Report

```bash
User: /sender_report

Bot: [Daily report for 2025-11-09 - see format below]

# Generate report for specific date
User: /sender_report 2025-11-08

Bot: [Daily report for 2025-11-08]
```

---

## 🔄 Conversation State Management

### Implementation Approach

To handle interactive multi-step conversations, we'll use **user session state tracking**:

```python
# In-memory conversation state (can be Redis for production)
conversation_states = {}
# Format: {user_id: {"state": "waiting_sender_code", "data": {...}}}

class ConversationState:
    IDLE = "idle"
    WAITING_SENDER_CODE = "waiting_sender_code"
    WAITING_SENDER_NAME = "waiting_sender_name"
    WAITING_DELETE_CODE = "waiting_delete_code"
    WAITING_DELETE_CONFIRM = "waiting_delete_confirm"
    WAITING_UPDATE_CODE = "waiting_update_code"
    WAITING_UPDATE_NAME = "waiting_update_name"

def set_user_state(user_id: int, state: str, data: dict = None):
    """Set conversation state for a user"""
    conversation_states[user_id] = {
        "state": state,
        "data": data or {},
        "timestamp": datetime.now()
    }

def get_user_state(user_id: int) -> dict | None:
    """Get conversation state for a user"""
    return conversation_states.get(user_id)

def clear_user_state(user_id: int):
    """Clear conversation state for a user"""
    conversation_states.pop(user_id, None)
```

### State Flow Examples

#### Add Sender Flow
```
User sends: /sender_add
  → Set state: WAITING_SENDER_CODE
  → Bot asks: "Please reply with account number"

User replies: 708
  → Get state: WAITING_SENDER_CODE ✓
  → Validate: 708 is 3 digits ✓
  → Store in state data: {"sender_code": "708"}
  → Set state: WAITING_SENDER_NAME
  → Bot asks: "Please provide name or skip"

User replies: John Doe
  → Get state: WAITING_SENDER_NAME ✓
  → Retrieve from state data: sender_code = "708"
  → Save to database: (708, "John Doe")
  → Clear state: IDLE
  → Bot confirms: "✅ Sender added"
```

#### Handling Cancellation
```
User sends: /sender_add
  → Set state: WAITING_SENDER_CODE

User sends: /sender_list (different command)
  → Clear previous state
  → Execute /sender_list normally

User sends: cancel
  → Clear state
  → Bot: "❌ Operation cancelled"
```

### State Timeout
```python
# Auto-clear state after 5 minutes of inactivity
STATE_TIMEOUT = 300  # seconds

def cleanup_expired_states():
    """Remove states older than timeout"""
    now = datetime.now()
    expired = [
        user_id for user_id, state_data in conversation_states.items()
        if (now - state_data["timestamp"]).seconds > STATE_TIMEOUT
    ]
    for user_id in expired:
        clear_user_state(user_id)
```

---

## 📊 Report Format

### Daily Sender Report

```
📊 Daily Income Report - Nov 09, 2025
Grouped by Sender

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👤 Sender: 708 (John Doe)
💵 Transactions: 5
💰 Total USD: $150.00
💴 Total KHR: ៛50,000

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👤 Sender: 332 (Jane Smith)
💵 Transactions: 3
💰 Total USD: $75.00
💴 Total KHR: ៛0

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

❓ Unknown Senders (3)
💵 Transactions: 4
💰 Total USD: $60.00
💴 Total KHR: ៛20,000

By Code:
• 999: $30.00 (2 transactions)
• 555: $20.00, ៛20,000 (2 transactions)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔍 No Sender Info (1)
💵 Transactions: 2
💰 Total USD: $15.00
💴 Total KHR: ៛0

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 GRAND TOTAL
💰 USD: $300.00
💴 KHR: ៛70,000
📊 Total Transactions: 14
```

---

## 🔐 Access Control

### Simple Bot-Based Access

Access is controlled by simply adding the `business_plus_bot` to groups that need the feature.

```python
# No complex feature gates needed - if bot is in the group, features are available
# Commands will only work when business_plus_bot is present in the group
```

**Note**: The bot should be configured to only respond to groups it's been explicitly added to. No additional package or feature flag checks needed.

---

## 🎨 Models

### `SenderConfig` Model

```python
# models/sender_config_model.py

from sqlalchemy import BigInteger, String, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column
from models.base_model import BaseModel

class SenderConfig(BaseModel):
    __tablename__ = "sender_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    sender_code: Mapped[str] = mapped_column(String(3), nullable=False)
    sender_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
```

---

## 📝 Migration Plan

### Migration: Create sender_configs table
**File**: `migrations/versions/xxx_create_sender_configs_table.py`

This will create the table for storing sender configurations per chat.

---

## 🧪 Testing Strategy

### Unit Tests

1. **`test_sender_config_service.py`**
   - Test add/delete/update/list operations
   - Test sender code validation (must be 3 digits)
   - Test duplicate prevention
   - Test cascade delete when chat is deleted

2. **`test_sender_report_service.py`**
   - Test daily summary generation
   - Test grouping by sender
   - Test unknown sender handling
   - Test multi-currency totals
   - Test date filtering

3. **`test_group_by_sender_commands.py`**
   - Test all bot commands
   - Test access control
   - Test error handling

### Integration Tests

1. Test full flow: add sender → receive payment → generate report
2. Test with mixed configured/unknown senders
3. Test report with no transactions for the day

---

## 🚀 Implementation Phases

### Phase 1: Database & Models ✅
- [x] Create migration for `sender_configs` table
- [x] Create `SenderConfig` model
- [x] Run migrations
- [x] Test CRUD operations on sender_configs

### Phase 2: Service Layer ✅
- [x] Implement `SenderConfigService` (CRUD operations)
- [x] Implement `SenderReportService` (reporting logic)
- [x] Create `ConversationStateManager` (state tracking)
- [x] Write unit tests for services

### Phase 3: Bot Infrastructure
- [ ] Create bot handler for sender commands
- [ ] Implement conversation state management
- [ ] Create message router for handling states
- [ ] Set up bot group detection

### Phase 4: Interactive Commands
- [ ] Implement `/sender_add` interactive flow
  - [ ] Step 1: Ask for account number
  - [ ] Step 2: Ask for name (with skip option)
  - [ ] Step 3: Confirmation
- [ ] Implement `/sender_delete` interactive flow
  - [ ] Step 1: Show list and ask for code
  - [ ] Step 2: Confirmation
- [ ] Implement `/sender_update` interactive flow
  - [ ] Step 1: Show list and ask for code
  - [ ] Step 2: Ask for new name
- [ ] Implement `/sender_list` command (non-interactive)
- [ ] Add cancellation handling

### Phase 5: Reporting
- [ ] Implement `/sender_report` command
- [ ] Create report formatter with blocks
- [ ] Handle edge cases (no data, no senders, etc.)
- [ ] Test with real payment data

### Phase 6: Testing & Polish
- [ ] Integration testing (end-to-end flows)
- [ ] Test conversation state timeouts
- [ ] Test concurrent users
- [ ] Error handling improvements
- [ ] Documentation updates

---

## 🎯 Success Criteria

✅ Users can add/delete/list senders with 3-digit codes
✅ Daily report groups income by configured senders
✅ Unknown senders are shown separately
✅ Bot only responds in groups where it's been added
✅ All commands work as expected
✅ Reports are clear and easy to read
✅ No performance degradation on large datasets

---

## 🔍 Edge Cases to Handle

1. **Sender code validation**
   - Must be exactly 3 digits
   - No letters or special characters
   - Handle leading zeros (e.g., "001", "007")

2. **Duplicate senders**
   - Prevent adding same sender_code twice for same chat
   - Clear error message on duplicate attempt

3. **Empty reports**
   - Handle days with no transactions
   - Handle senders with no transactions

4. **Multiple currencies**
   - Show separate totals for USD and KHR
   - Handle mixed currency transactions

5. **Unknown senders**
   - Show transactions from non-configured paid_by values
   - Group unknown senders together

6. **No paid_by field**
   - Handle transactions where paid_by is NULL
   - Show in separate "No Sender Info" section

7. **Deleted senders**
   - Historical data should remain intact
   - Reports should handle deleted senders gracefully

---

## 📚 Documentation Needs

1. User guide for sender management commands
2. API documentation for services
3. Database schema documentation
4. Feature flag configuration guide

---

## 🔄 Future Enhancements (Post-MVP)

- Weekly/Monthly sender reports
- Export sender reports to CSV/Excel
- Sender performance analytics
- Set transaction limits per sender
- Notification when sender exceeds threshold
- Bulk sender import from CSV
- Sender groups/categories

---

## ❓ Resolved Decisions

1. ✅ **Package requirement**: None - simple bot addition to group
2. ✅ **sender_code format**: 3 digits exactly (e.g., "708", "001")
3. ✅ **Sender name**: Optional field
4. ✅ **Delete behavior**: Hard delete
5. ✅ **Max senders**: No limit initially
6. ✅ **Editable fields**: Only sender_name (not sender_code)

---

**Created**: 2025-11-09
**Last Updated**: 2025-11-09
**Status**: Blueprint - Ready for Implementation
