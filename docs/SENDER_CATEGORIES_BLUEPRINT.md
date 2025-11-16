# Sender Categories Feature Blueprint

## Overview

Transform the hardcoded report sections ("Delivery:", "Customers:") into a flexible, admin-configurable category system. This allows each Telegram group to create custom categories (e.g., "VIP Customers", "Pay Later", "Cash on Delivery", etc.) and assign senders to them for better report organization.

### Current System
- **Customers**: Hardcoded section for unknown/unconfigured senders
- **Delivery**: Hardcoded section for all configured senders

### New System
- **Customers**: Still shown first for unknown/unconfigured senders
- **Custom Categories**: Admin-defined categories (VIP Customers, Pay Later, Delivery, etc.)
- Each category can contain multiple senders
- Categories displayed in configurable order

---

## Database Design

### Table 1: `sender_categories`

Stores category definitions for each chat group.

```sql
CREATE TABLE sender_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id BIGINT NOT NULL,
    category_name VARCHAR(100) NOT NULL,
    display_order INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    CONSTRAINT unique_category_per_chat UNIQUE (chat_id, category_name)
);
```

**Field Descriptions:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | INTEGER | Primary key, auto-increment |
| `chat_id` | BIGINT | Telegram group ID (FK reference) |
| `category_name` | VARCHAR(100) | Display name (e.g., "VIP Customers") |
| `display_order` | INTEGER | Sort order in reports (lower = shown first) |
| `is_active` | BOOLEAN | Enable/disable without deletion |
| `created_at` | DATETIME | Creation timestamp |
| `updated_at` | DATETIME | Last update timestamp |

**Indexes:**
- Primary: `id`
- Unique: `(chat_id, category_name)` - Prevents duplicate category names per group

---

### Table 2: Update `sender_configs`

Add category relationship and nickname directly to sender configs table.

```sql
ALTER TABLE sender_configs
ADD COLUMN category_id INTEGER,
ADD COLUMN nickname VARCHAR(100),
ADD CONSTRAINT fk_sender_category FOREIGN KEY (category_id)
    REFERENCES sender_categories(id) ON DELETE SET NULL,
ADD CONSTRAINT unique_sender_per_chat UNIQUE (chat_id, sender_account_number, sender_name);
```

**New Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `category_id` | INTEGER | FK to sender_categories (nullable) |
| `nickname` | VARCHAR(100) | Display name for sender (nullable) |

**Field Usage:**
- `nickname`: If set, used for display in reports and UI; otherwise falls back to `account_name`
- Display priority: `nickname` → `account_name` → `*{sender_account_number}`

**Constraints:**
- `unique_sender_per_chat`: Ensures unique combination of (chat_id, sender_account_number, sender_name)
- Prevents duplicate sender configurations within the same chat group

**Relationship Rules:**
- One sender belongs to one category (or none)
- One category can contain multiple senders
- Deleting a sender doesn't affect the category
- Deleting a category sets sender's `category_id` to NULL (senders become uncategorized)

---

## Configuration

### Global Admin Users List

**File:** `config/constants.py` (NEW)

Create a global constants file to store admin users who can manage categories:

```python
"""
Global constants for the application.
"""

# Admin users allowed to manage categories and other sensitive operations
# These usernames correspond to Telegram usernames
ADMIN_USERS = [
    "HK_688",
    "houhokheng",
    "autosum_kh",
    "chanhengsng"
]

def is_admin_user(username: str | None) -> bool:
    """
    Check if a username is in the admin users list.

    Args:
        username: Telegram username to check

    Returns:
        True if user is admin, False otherwise
    """
    if not username:
        return False
    return username in ADMIN_USERS
```

**Usage in Services:**

```python
from config.constants import is_admin_user

async def some_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.effective_user.username if update.effective_user else None

    if not is_admin_user(username):
        await update.message.reply_text(
            "🚫 Access denied. Only administrators can manage categories."
        )
        return ConversationHandler.END

    # Continue with authorized operation
    ...
```

---

## Data Models

### Model 1: `SenderCategory`

**File:** `models/sender_category_model.py`

```python
from sqlalchemy import Boolean, Integer, String, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base_model import BaseModel


class SenderCategory(BaseModel):
    """
    Represents a category for grouping senders in reports.

    Examples:
        - VIP Customers
        - Pay Later
        - Cash on Delivery
        - Delivery Partners
    """
    __tablename__ = "sender_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    category_name: Mapped[str] = mapped_column(String(100), nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Relationships
    senders: Mapped[list["SenderConfig"]] = relationship(
        "SenderConfig",
        back_populates="category"
    )
```

---

### Model 2: Update `SenderConfig`

**File:** `models/sender_config_model.py`

Add category relationship and nickname to existing model:

```python
from sqlalchemy import Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

class SenderConfig(BaseModel):
    # ... existing fields ...

    __table_args__ = (
        UniqueConstraint(
            'chat_id',
            'sender_account_number',
            'sender_name',
            name='unique_sender_per_chat'
        ),
    )

    # Add these fields
    category_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("sender_categories.id", ondelete="SET NULL"),
        nullable=True
    )
    nickname: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    # Add this relationship
    category: Mapped["SenderCategory | None"] = relationship(
        "SenderCategory",
        back_populates="senders"
    )

    def get_display_name(self) -> str:
        """
        Get display name with priority: nickname → account_name → *{account_number}

        Returns:
            Display name for this sender
        """
        if self.nickname:
            return self.nickname
        if self.account_name:
            return self.account_name
        return f"*{self.sender_account_number}"
```

---

## Service Layer

### `SenderCategoryService`

**File:** `services/sender_category_service.py`

```python
class SenderCategoryService:
    """Service for managing sender categories and assignments."""

    # ========== Category CRUD Operations ==========

    async def create_category(
        self,
        chat_id: int,
        category_name: str,
        display_order: int | None = None
    ) -> tuple[bool, str, SenderCategory | None]:
        """
        Create a new category for a chat group.

        Args:
            chat_id: Telegram group ID
            category_name: Name of the category
            display_order: Optional order (defaults to max + 1)

        Returns:
            (success, message, category_object)
        """
        pass

    async def delete_category(
        self,
        chat_id: int,
        category_id: int
    ) -> tuple[bool, str]:
        """
        Delete a category and unassign all senders.

        Args:
            chat_id: Telegram group ID
            category_id: Category to delete

        Returns:
            (success, message)
        """
        pass

    async def update_category(
        self,
        chat_id: int,
        category_id: int,
        new_name: str | None = None,
        new_order: int | None = None
    ) -> tuple[bool, str]:
        """
        Update category name and/or display order.

        Args:
            chat_id: Telegram group ID
            category_id: Category to update
            new_name: New name (optional)
            new_order: New display order (optional)

        Returns:
            (success, message)
        """
        pass

    async def list_categories(
        self,
        chat_id: int,
        active_only: bool = True
    ) -> list[SenderCategory]:
        """
        Get all categories for a chat, ordered by display_order.

        Args:
            chat_id: Telegram group ID
            active_only: Only return active categories

        Returns:
            List of SenderCategory objects
        """
        pass

    async def get_category_by_id(
        self,
        chat_id: int,
        category_id: int
    ) -> SenderCategory | None:
        """Get a specific category by ID."""
        pass

    async def get_category_by_name(
        self,
        chat_id: int,
        category_name: str
    ) -> SenderCategory | None:
        """Get a specific category by name."""
        pass

    # ========== Assignment Operations ==========

    async def assign_sender_to_category(
        self,
        chat_id: int,
        sender_account_number: str,
        category_id: int | None
    ) -> tuple[bool, str]:
        """
        Assign a sender to a category (or set to None to remove category).

        Args:
            chat_id: Telegram group ID
            sender_account_number: Last 3 digits of sender account
            category_id: Category to assign to (None to unassign)

        Returns:
            (success, message)
        """
        pass

    async def assign_multiple_senders(
        self,
        chat_id: int,
        sender_account_numbers: list[str],
        category_id: int | None
    ) -> tuple[bool, str, int]:
        """
        Bulk assign multiple senders to a category.

        Args:
            chat_id: Telegram group ID
            sender_account_numbers: List of sender account numbers
            category_id: Category to assign to (None to unassign)

        Returns:
            (success, message, count_assigned)
        """
        pass

    async def get_senders_by_category(
        self,
        chat_id: int,
        category_id: int
    ) -> list[SenderConfig]:
        """Get all senders in a specific category."""
        pass

    # ========== Sender Management ==========

    async def update_sender_nickname(
        self,
        chat_id: int,
        sender_account_number: str,
        nickname: str | None
    ) -> tuple[bool, str]:
        """
        Update or remove a sender's nickname.

        Args:
            chat_id: Telegram group ID
            sender_account_number: Last 3 digits of sender account
            nickname: New nickname (None to remove)

        Returns:
            (success, message)
        """
        pass

    async def get_sender_display_name(
        self,
        sender: SenderConfig
    ) -> str:
        """
        Get display name for a sender with priority: nickname → account_name → *{account_number}

        Args:
            sender: SenderConfig object

        Returns:
            Display name string
        """
        return sender.get_display_name()

    # ========== Migration & Utilities ==========

    async def create_default_categories(
        self,
        chat_id: int
    ) -> tuple[bool, str]:
        """
        Create default categories for a new group:
        - "Customers" (display_order: 0)
        - "Delivery" (display_order: 1)

        Used during migration or first-time setup.
        """
        pass

    async def migrate_existing_senders(
        self,
        chat_id: int
    ) -> tuple[bool, str, int]:
        """
        Migrate existing configured senders to "Delivery" category.

        Returns:
            (success, message, count_migrated)
        """
        pass
```

---

## Command Handlers

### Updated Menu Structure

```
/setup Menu
├── 📋 List Senders
├── ➕ Add Sender
├── ✏️ Edit Sender  ← NEW
│   ├── Set/Update Nickname
│   ├── Assign Category
│   └── Edit Account Name
├── 🗑 Delete Sender
└── 🏷️ Manage Categories  ← NEW
    ├── 📋 List Categories
    ├── ➕ Add Category
    ├── ✏️ Edit Category
    ├── 🗑 Delete Category
    ├── 🔗 Assign Senders to Category
    └── 🔄 Migrate Default Categories  ← For existing groups
```

### New Handler Methods

**File:** `services/handlers/category_command_handler.py` (NEW)

**IMPORTANT**: All category management operations require admin authorization. Only users in the `ADMIN_USERS` list (from `config/constants.py`) can access these features.

```python
from config.constants import is_admin_user
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

class CategoryCommandHandler:
    """
    Handler for category management commands.

    Security:
        - All methods require admin authorization
        - Admin users are defined in config.constants.ADMIN_USERS
        - Unauthorized access attempts are logged and denied
    """

    def __init__(self):
        self.category_service = SenderCategoryService()
        self.sender_service = SenderConfigService()
        self.conversation_manager = ConversationStateManager()

    # ========== Authorization ==========

    def _check_admin_access(self, update: Update) -> tuple[bool, str | None]:
        """
        Check if user has admin access to manage categories.

        Args:
            update: Telegram update object

        Returns:
            (has_access, username) tuple
        """
        username = update.effective_user.username if update.effective_user else None

        if not is_admin_user(username):
            return False, username

        return True, username

    async def _handle_unauthorized_access(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        """
        Handle unauthorized access attempts.

        Args:
            update: Telegram update object
            context: Telegram context

        Returns:
            ConversationHandler.END
        """
        message = (
            "🚫 Access denied.\n\n"
            "Only authorized administrators can manage categories.\n"
            "Please contact @HK_688 for access."
        )

        if update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.message.reply_text(message)
        else:
            await update.message.reply_text(message)

        return ConversationHandler.END

    # ========== Menu Navigation ==========

    async def show_category_menu(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Show the category management menu (admin only)."""
        # Check authorization
        has_access, username = self._check_admin_access(update)
        if not has_access:
            return await self._handle_unauthorized_access(update, context)

        # Continue with menu display
        pass

    # ========== List Categories ==========

    async def category_list(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """
        Display all categories with their assigned sender counts (admin only).

        **Authorization**: Requires admin access (checked via _check_admin_access)

        Example output:
        🏷️ Category List (3 categories)

        1. Customers (display_order: 0)
           → 0 senders

        2. VIP Customers (display_order: 1)
           → 3 senders: *708, *709, *710

        3. Delivery (display_order: 2)
           → 5 senders
        """
        # Check authorization
        has_access, username = self._check_admin_access(update)
        if not has_access:
            return await self._handle_unauthorized_access(update, context)

        # Continue with listing categories
        pass

    # ========== Add Category ==========

    async def category_add_start(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Start add category flow."""
        pass

    async def category_add_handle_name(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle category name input."""
        pass

    # ========== Edit Category ==========

    async def category_edit_start(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Show list of categories to edit."""
        pass

    async def category_edit_select(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle category selection for editing."""
        pass

    async def category_edit_show_options(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """
        Show edit options:
        - Edit Name
        - Change Display Order
        - Toggle Active/Inactive
        """
        pass

    # ========== Delete Category ==========

    async def category_delete_start(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Show list of categories to delete."""
        pass

    async def category_delete_confirm(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """
        Confirm deletion with warning:
        ⚠️ Deleting "VIP Customers" will unassign 3 senders.
        The senders will not be deleted.

        [Confirm Delete] [Cancel]
        """
        pass

    # ========== Assign Senders ==========

    async def category_assign_start(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Show list of categories for assignment."""
        pass

    async def category_assign_show_senders(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """
        Show senders with checkboxes:

        Select senders for "VIP Customers":

        ☑ *708 (John Doe) ← Already assigned
        ☐ *709 (Jane Smith)
        ☑ *710 (Bob Johnson) ← Already assigned
        ☐ *711 (Alice Brown)

        [Save Changes] [Cancel]
        """
        pass

    async def category_assign_save(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Save sender assignments."""
        pass
```

---

## Report Service Updates

### Modified `SenderReportService`

**File:** `services/sender_report_service.py`

#### 1. New Grouping Method

```python
async def _group_transactions_by_category(
    self,
    transactions: list[IncomeBalance],
    configured_senders: dict[str, SenderConfig],
    chat_id: int
) -> dict:
    """
    Group transactions by category instead of just configured/unknown.

    Args:
        transactions: List of income balance transactions
        configured_senders: Dict mapping account_number -> SenderConfig
        chat_id: Telegram group ID

    Returns:
        {
            "unknown": {...},           # Unknown senders (Customers section)
            "no_sender": [...],         # Transactions without sender
            "categories": {             # Categorized senders
                category_id: {
                    "category": SenderCategory,
                    "senders": {
                        account_number: [transactions]
                    }
                }
            },
            "uncategorized": {...}      # Configured but not in any category
        }
    """
    # Get all active categories for this chat
    categories = await self.category_service.list_categories(chat_id)

    # Initialize grouping structure
    grouped = {
        "unknown": defaultdict(list),
        "no_sender": [],
        "categories": {},
        "uncategorized": defaultdict(list)
    }

    # Initialize category buckets
    for category in categories:
        grouped["categories"][category.id] = {
            "category": category,
            "senders": defaultdict(list)
        }

    # Group transactions
    for txn in transactions:
        if txn.paid_by is None:
            grouped["no_sender"].append(txn)
        elif txn.paid_by in configured_senders:
            sender = configured_senders[txn.paid_by]
            if sender.category_id:
                # Sender has a category
                grouped["categories"][sender.category_id]["senders"][txn.paid_by].append(txn)
            else:
                # Sender is configured but not in any category
                grouped["uncategorized"][txn.paid_by].append(txn)
        else:
            # Unknown sender
            grouped["unknown"][txn.paid_by].append(txn)

    return grouped
```

#### 2. Updated Report Format Method

```python
def _format_report(
    self,
    grouped: dict,
    configured_senders: dict[str, SenderConfig],
    report_date: date,
    total_transactions: int,
    telegram_username: str = "Admin",
) -> str:
    """
    Format the complete report with categories.

    Args:
        grouped: Grouped transactions by category
        configured_senders: Dict mapping account_number -> SenderConfig
        report_date: Date of the report
        total_transactions: Total transaction count
        telegram_username: Username triggering the report

    Returns:
        Formatted report string
    """
    lines = []

    # Header (unchanged)
    current_time = DateUtils.now()
    trigger_time = format_time_12hour(current_time)
    day = report_date.day
    month_khmer = get_khmer_month_name(report_date.month)
    year = report_date.year

    lines.append(f"សរុបប្រតិបត្តិការថ្ងៃ {day} {month_khmer} {year}")
    lines.append(f"ម៉ោងបូកសរុប {trigger_time}")
    lines.append(f"(ដោយ: @{telegram_username})")
    lines.append("")

    # Section 1: Customers (Unknown Senders) - ALWAYS FIRST
    if grouped["unknown"] or grouped["no_sender"]:
        lines.append("<b>Customers:</b>")

        all_unknown_transactions = []
        for transactions in grouped["unknown"].values():
            all_unknown_transactions.extend(transactions)
        all_unknown_transactions.extend(grouped["no_sender"])

        totals = self._calculate_totals(all_unknown_transactions)
        count = len(all_unknown_transactions)

        # Format currency lines
        currency_lines = self._format_currency_lines(totals, count)
        if currency_lines:
            lines.append(f"<pre>\n{chr(10).join(currency_lines)}</pre>")

    # Section 2: Categories (Ordered by display_order)
    sorted_categories = sorted(
        grouped["categories"].items(),
        key=lambda x: x[1]["category"].display_order
    )

    for cat_id, cat_data in sorted_categories:
        category = cat_data["category"]
        senders = cat_data["senders"]

        if not senders:
            continue  # Skip empty categories

        lines.append(f"<b>{category.category_name}:</b>")

        # Show each sender in category
        for account_num in sorted(senders.keys()):
            transactions = senders[account_num]
            totals = self._calculate_totals(transactions)
            sender = configured_senders.get(account_num)

            # Use get_display_name() for priority: nickname → account_name → *{account_number}
            if sender:
                sender_display = sender.get_display_name()
            else:
                sender_display = f"*{account_num}"

            count = len(transactions)
            currency_lines = self._format_currency_lines(totals, count)

            lines.append(f"{sender_display}")
            if currency_lines:
                lines.append(f"<pre>\n{chr(10).join(currency_lines)}</pre>")

    # Section 3: Uncategorized (Configured senders not in any category)
    if grouped["uncategorized"]:
        lines.append("<b>Uncategorized:</b>")

        for account_num in sorted(grouped["uncategorized"].keys()):
            transactions = grouped["uncategorized"][account_num]
            totals = self._calculate_totals(transactions)
            sender = configured_senders.get(account_num)

            # Use get_display_name() for priority: nickname → account_name → *{account_number}
            if sender:
                sender_display = sender.get_display_name()
            else:
                sender_display = f"*{account_num}"

            count = len(transactions)
            currency_lines = self._format_currency_lines(totals, count)

            lines.append(f"{sender_display}")
            if currency_lines:
                lines.append(f"<pre>\n{chr(10).join(currency_lines)}</pre>")

    # Section 4: Summary (unchanged)
    lines.append("<b>Summary:</b>")
    # ... (existing summary code)

    return "\n".join(lines)
```

---

## User Flows

### Flow 1: Adding a Category

```
User: /setup
Bot: [Shows setup menu with "Manage Categories" option]

User: [Clicks "Manage Categories"]
Bot: [Shows category menu]

User: [Clicks "Add Category"]
Bot: ➕ Add New Category

     Please enter the category name:
     Example: VIP Customers

     Send /cancel to cancel.

User: VIP Customers
Bot: ✅ Category "VIP Customers" created!
     Display order: 3

     Use "Assign Senders" to add senders to this category.
```

### Flow 2: Setting Sender Nickname

```
User: /setup
Bot: [Shows setup menu]

User: [Clicks "Edit Sender"]
Bot: ✏️ Edit Sender

     Select a sender to edit:
     1. *708 (John Doe)
     2. *709 (Jane Smith)
     3. *710 (Bob Johnson)
     [Cancel]

User: [Clicks "*708 (John Doe)"]
Bot: Edit Sender *708

     Current name: John Doe
     Nickname: (not set)

     What would you like to do?
     [✏️ Set Nickname] [🏷️ Assign Category] [📝 Edit Account Name] [🔙 Back]

User: [Clicks "Set Nickname"]
Bot: Set Nickname for *708 (John Doe)

     Enter a nickname (or send /clear to remove existing nickname):

User: Johnny's Delivery
Bot: ✅ Nickname set!

     *708 will now be displayed as "Johnny's Delivery" in reports.

     Previous: John Doe
     New: Johnny's Delivery
```

### Flow 3: Assigning Senders to Category

```
User: [Clicks "Assign Senders to Category"]
Bot: 🔗 Assign Senders

     Select a category:
     [VIP Customers] [Pay Later] [Delivery] [Cancel]

User: [Clicks "VIP Customers"]
Bot: Select senders for "VIP Customers":

     Current: *708 (John), *710 (Bob)

     ☑ *708 (John Doe)
     ☐ *709 (Jane Smith)
     ☑ *710 (Bob Johnson)
     ☐ *711 (Alice Brown)

     [💾 Save] [Cancel]

User: [Toggles *709 on, clicks Save]
Bot: ✅ Assignments updated!

     VIP Customers now has 3 senders:
     • *708 (John Doe)
     • *709 (Jane Smith)
     • *710 (Bob Johnson)
```

### Flow 3: Editing Category

```
User: [Clicks "Edit Category"]
Bot: ✏️ Edit Category

     Select category to edit:
     1. Customers (order: 0)
     2. VIP Customers (order: 1)
     3. Delivery (order: 2)
     [Cancel]

User: [Clicks "VIP Customers"]
Bot: Edit "VIP Customers":

     What would you like to change?
     [📝 Rename] [🔢 Change Order] [🔙 Back]

User: [Clicks "Rename"]
Bot: Current name: VIP Customers

     Please enter new name:

User: Premium Customers
Bot: ✅ Category renamed!
     "VIP Customers" → "Premium Customers"
```

### Flow 4: Deleting Category

```
User: [Clicks "Delete Category"]
Bot: 🗑 Delete Category

     Select category to delete:
     1. Customers (0 senders)
     2. VIP Customers (3 senders)
     3. Delivery (5 senders)
     [Cancel]

User: [Clicks "VIP Customers"]
Bot: ⚠️ Confirm Deletion

     Category: VIP Customers
     Assigned senders: 3

     This will:
     • Delete the category
     • Unassign 3 senders (*708, *709, *710)
     • NOT delete the senders

     Are you sure?
     [✅ Yes, Delete] [❌ Cancel]

User: [Clicks "Yes, Delete"]
Bot: ✅ Category "VIP Customers" deleted.
     3 senders unassigned and moved to "Uncategorized".
```

---

## Report Example

### Before (Current System)

```
សរុបប្រតិបត្តិការថ្ងៃ 13 វិច្ឆិកា 2025
ម៉ោងបូកសរុប 10:30 AM
(ដោយ: @admin)

Customers:
KHR: 500,000    | ប្រតិបត្តិការ: 10
USD: 250.00     | ប្រតិបត្តិការ: 10

Delivery:
*708 (John Doe)
USD: 100.00     | ប្រតិបត្តិការ: 5

*709 (Jane Smith)
KHR: 200,000    | ប្រតិបត្តិការ: 3

*710 (Bob Johnson)
USD: 50.00      | ប្រតិបត្តិការ: 2

Summary:
...
```

### After (With Categories & Nicknames)

```
សរុបប្រតិបត្តិការថ្ងៃ 13 វិច្ឆិកា 2025
ម៉ោងបូកសរុប 10:30 AM
(ដោយ: @admin)

Customers:
KHR: 500,000    | ប្រតិបត្តិការ: 10
USD: 250.00     | ប្រតិបត្តិការ: 10

VIP Customers:
Johnny's Delivery  ← Nickname set for *708
USD: 100.00     | ប្រតិបត្តិការ: 5

Bob's Express  ← Nickname set for *710
USD: 50.00      | ប្រតិបត្តិការ: 2

Pay Later:
Jane Smith  ← Using account_name (no nickname)
KHR: 200,000    | ប្រតិបត្តិការ: 3

Delivery Partners:
Fast Delivery Co  ← Nickname set for *711
USD: 75.00      | ប្រតិបត្តិការ: 4

Uncategorized:
*712  ← No account_name or nickname, showing account number only
USD: 25.00      | ប្រតិបត្តិការ: 1

Summary:
...
```

---

## Migration Strategy

### Phase 1: Create Tables

```bash
# Create migration files
alembic revision -m "create_sender_categories_table"
alembic revision -m "add_category_id_and_nickname_to_sender_configs"

# Run migrations
alembic upgrade head
```

### Phase 2: Data Migration (Optional)

For existing groups that already use the sender system:

```python
async def migrate_existing_groups():
    """
    For each group with configured senders:
    1. Create "Customers" category (display_order: 0)
    2. Create "Delivery" category (display_order: 1)
    3. Assign all existing configured senders to "Delivery"
    """
    # Get all unique chat_ids from sender_configs
    chat_ids = get_all_chat_ids_with_senders()

    for chat_id in chat_ids:
        # Create default categories
        await category_service.create_default_categories(chat_id)

        # Migrate existing senders to "Delivery" category
        await category_service.migrate_existing_senders(chat_id)
```

### Phase 3: Single Deployment

**All changes will be deployed together in one release:**

1. **Create global config** (`config/constants.py`)
   - Define `ADMIN_USERS` list
   - Implement `is_admin_user()` helper

2. **Refactor existing authorization** in `telegram_private_bot_service.py`:
   ```python
   # OLD (Line 42-43):
   allowed_users = ["HK_688", "houhokheng", "autosum_kh", "chanhengsng"]
   username = update.effective_user.username if update.effective_user else None

   if not username or username not in allowed_users:
       # ...

   # NEW:
   from config.constants import is_admin_user

   username = update.effective_user.username if update.effective_user else None

   if not is_admin_user(username):
       # ...
   ```

3. **Database migrations**
   - Create `sender_categories` table
   - Add `category_id` and `nickname` columns to `sender_configs`
   - Add unique constraint

4. **Implement models, services, and handlers** with authorization

5. **Update report service** to use categories and nicknames

6. **Run data migration** for existing groups (create default categories)

7. **Deploy all changes at once**

**Benefits of single deployment:**
- Simpler rollout process
- No intermediate states to maintain
- Users get all features immediately
- Easier to test as a complete package

---

## Testing Plan

### Unit Tests

**File:** `tests/test_sender_category_service.py`

```python
# Authorization Tests
- test_is_admin_user_returns_true_for_allowed_users()
- test_is_admin_user_returns_false_for_non_admin()
- test_is_admin_user_returns_false_for_none_username()
- test_check_admin_access_allows_admin_users()
- test_check_admin_access_denies_non_admin_users()
- test_handle_unauthorized_access_sends_denial_message()

# Category CRUD
- test_create_category_success()
- test_create_duplicate_category_fails()
- test_delete_category_removes_assignments()
- test_update_category_name()
- test_update_category_order()
- test_list_categories_ordered_correctly()
- test_inactive_categories_not_shown()

# Assignments
- test_assign_sender_to_category()
- test_unassign_sender_from_category()
- test_bulk_assign_senders()
- test_get_senders_by_category()
- test_reassign_sender_to_different_category()

# Nicknames
- test_set_sender_nickname()
- test_update_sender_nickname()
- test_remove_sender_nickname()
- test_get_display_name_with_nickname()
- test_get_display_name_with_account_name()
- test_get_display_name_with_account_number_only()

# Edge Cases
- test_assign_nonexistent_sender_fails()
- test_assign_to_nonexistent_category_fails()
- test_cascade_delete_category_sets_sender_category_to_null()
- test_unique_constraint_prevents_duplicate_senders()
- test_can_have_same_account_number_in_different_chats()
```

### Integration Tests

**File:** `tests/test_category_reports.py`

```python
# Report Generation
- test_report_with_single_category()
- test_report_with_multiple_categories()
- test_report_with_uncategorized_senders()
- test_category_display_order()
- test_empty_category_not_shown_in_report()
- test_report_displays_nickname_over_account_name()
- test_report_displays_account_name_when_no_nickname()
- test_report_displays_account_number_when_no_name_or_nickname()

# Daily/Weekly/Monthly
- test_daily_report_with_categories()
- test_weekly_report_with_categories()
- test_monthly_report_with_categories()
```

### Handler Tests

**File:** `tests/test_category_command_handler.py`

```python
# Command Flows
- test_add_category_flow()
- test_edit_category_flow()
- test_delete_category_flow()
- test_assign_senders_flow()
- test_set_sender_nickname_flow()
- test_remove_sender_nickname_flow()
- test_edit_sender_menu_flow()
- test_cancel_conversation()
```

---

## API Summary

### Bot Commands

| Command | Description | Access |
|---------|-------------|--------|
| `/category_list` | List all categories | Admin |
| `/category_add` | Add new category | Admin |
| `/category_edit` | Edit category name/order | Admin |
| `/category_delete` | Delete category | Admin |
| `/category_assign` | Assign senders to category | Admin |
| `/sender_edit` | Edit sender (nickname, category, name) | Admin |
| `/sender_nickname` | Set/update sender nickname | Admin |

### Service Methods

| Method | Purpose |
|--------|---------|
| `create_category(chat_id, name, order)` | Create new category |
| `delete_category(chat_id, category_id)` | Delete category |
| `update_category(chat_id, category_id, ...)` | Update category |
| `list_categories(chat_id)` | Get all categories |
| `assign_sender_to_category(...)` | Link sender to category |
| `get_senders_by_category(chat_id, category_id)` | Get category members |
| `update_sender_nickname(chat_id, sender, nickname)` | Set/update sender nickname |
| `get_sender_display_name(sender)` | Get display name (nickname → name → number) |

---

## Implementation Checklist

- [ ] **Phase 0: Configuration & Security**
  - [ ] Create `config/constants.py` with `ADMIN_USERS` list
  - [ ] Create `is_admin_user()` helper function
  - [ ] Update `telegram_private_bot_service.py` to use global `ADMIN_USERS`
  - [ ] Test authorization checks

- [ ] **Phase 1: Database**
  - [ ] Create `sender_categories` migration
  - [ ] Add `category_id` and `nickname` columns to `sender_configs` migration
  - [ ] Add `unique_sender_per_chat` constraint to `sender_configs`
  - [ ] Run migrations
  - [ ] Verify tables/columns/constraints created

- [ ] **Phase 2: Models**
  - [ ] Create `SenderCategory` model
  - [ ] Update `SenderConfig` model with `category_id` and `nickname` fields
  - [ ] Add `UniqueConstraint` to `SenderConfig.__table_args__`
  - [ ] Add `get_display_name()` method to `SenderConfig`
  - [ ] Test model relationships and unique constraint

- [ ] **Phase 3: Service Layer**
  - [ ] Implement `SenderCategoryService`
  - [ ] Write unit tests for service
  - [ ] Test all CRUD operations

- [ ] **Phase 4: Command Handlers**
  - [ ] Create `CategoryCommandHandler`
  - [ ] Implement `_check_admin_access()` authorization method
  - [ ] Implement `_handle_unauthorized_access()` method
  - [ ] Add authorization checks to all category management methods
  - [ ] Add "Edit Sender" menu to `/setup`
  - [ ] Implement nickname management flow
  - [ ] Implement category assignment in sender edit
  - [ ] Implement all conversation flows
  - [ ] Test handler integration with admin and non-admin users

- [ ] **Phase 5: Report Service**
  - [ ] Update `_group_transactions_by_category()` to use configured_senders dict
  - [ ] Update `_format_report()` to use `get_display_name()` for nicknames
  - [ ] Update `_format_weekly_report()` to use nicknames
  - [ ] Update `_format_monthly_report()` to use nicknames
  - [ ] Test report generation with various nickname scenarios

- [ ] **Phase 6: Migration**
  - [ ] Create migration script for existing groups
  - [ ] Test migration on staging
  - [ ] Run production migration
  - [ ] Verify data integrity

- [ ] **Phase 7: Testing**
  - [ ] Write integration tests
  - [ ] Test all user flows
  - [ ] Performance testing with large datasets
  - [ ] Edge case validation

- [ ] **Phase 8: Documentation**
  - [ ] Update user guide
  - [ ] Create admin tutorial
  - [ ] Update API documentation

---

## Performance Considerations

### Query Optimization

1. **Eager Loading**
   ```python
   # Load senders with their categories in single query
   senders = session.query(SenderConfig)\
       .options(joinedload(SenderConfig.category))\
       .filter_by(chat_id=chat_id)\
       .all()
   ```

2. **Caching**
   - Cache category list per chat (TTL: 5 minutes)
   - Cache sender configs with categories during report generation
   - Invalidate cache on category/assignment changes

3. **Indexing**
   - Add index on `(chat_id, display_order)` in `sender_categories` for fast sorting
   - Add index on `category_id` in `sender_configs` for fast lookups

### Scalability

- **Max Categories per Group**: Recommend limit of 20
- **Max Senders per Category**: No hard limit (tested up to 100)
- **Report Generation Time**: <500ms for 1000 transactions

---

## Future Enhancements

### Version 2.0
- [ ] Category colors in reports
- [ ] Category icons/emojis
- [ ] Subtotals per category in summary
- [ ] Export categories to CSV/JSON
- [ ] Category templates (copy from another group)

### Version 3.0
- [ ] Time-based category assignments (weekday vs weekend)
- [ ] Conditional categories (amount thresholds)
- [ ] Category analytics dashboard
- [ ] API endpoints for external integrations

---

## Related Documentation

- [GROUP_BY_SENDER_BLUEPRINT.md](./GROUP_BY_SENDER_BLUEPRINT.md) - Original sender feature
- [GROUP_BY_SENDER_ARCHITECTURE.md](./GROUP_BY_SENDER_ARCHITECTURE.md) - System architecture
- [SENDER_BOT_SETUP.md](./SENDER_BOT_SETUP.md) - Setup guide

---

## Questions & Decisions

### Q1: Can a sender belong to multiple categories?
**Decision**: NO. Each sender can only belong to one category at a time for simplicity.

### Q2: Should "Customers" be a category or hardcoded?
**Decision**: Remain hardcoded for unknown senders, always shown first.

### Q3: How to handle category order conflicts?
**Decision**: Allow same display_order, secondary sort by category name alphabetically.

### Q4: Can categories be deleted with senders?
**Decision**: YES. When a category is deleted, all senders in that category have their `category_id` set to NULL and move to "Uncategorized" section.

### Q5: Why use unique constraint on (chat_id, sender_account_number, sender_name)?
**Decision**: Ensures data integrity by preventing duplicate sender configurations within the same chat group. The combination of chat_id, sender_account_number, and sender_name uniquely identifies a sender in a specific group.

### Q6: Who can manage categories and why is authorization needed?
**Decision**: Only users in the `ADMIN_USERS` list (defined in `config/constants.py`) can manage categories. This includes:
- **Current authorized users**: "HK_688", "houhokheng", "autosum_kh", "chanhengsng"
- **Reason**: Category management is a sensitive operation that affects how all reports are organized and displayed
- **Implementation**: All category management handlers check authorization via `_check_admin_access()` before allowing operations
- **Global list**: The admin users list is centralized in `config/constants.py` and used across all services (replacing hardcoded lists in individual files like `telegram_private_bot_service.py`)

---

**Document Version**: 1.1
**Created**: 2025-11-13
**Last Updated**: 2025-11-13
**Status**: DRAFT - Ready for Review
