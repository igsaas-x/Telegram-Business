# Custom Report Framework Blueprint

## Overview
A framework that allows business package groups to create and execute custom SQL-based reports. Reports can be triggered manually via menu or automatically via scheduler. The framework will execute SQL queries that return `income_balance` records, aggregate the results, and format them into a summary report.

## Requirements

### Business Rules
1. **Package Requirement**: Only available for groups with BUSINESS package
2. **Feature Flag**: `CUSTOM_REPORT` feature flag must be enabled in `group_package.feature_flags`
3. **SQL Constraint**: SQL queries must return records compatible with `income_balance` structure (at minimum: `amount`, `currency` fields)
4. **Multi-Group Support**: A group can have multiple custom report queries
5. **Execution Modes**:
   - Manual: User clicks report name from menu
   - Automatic: Scheduler runs at configured time

### Report Output Format
```
━━━━━━━━━━━━━━━━━━━━━━
📊 Test Report 🔄
Test Description
━━━━━━━━━━━━━━━━━━━━━━

📅 កាលបរិច្ឆេទ: 15-10-2025
⚡ ប្រភេទ: Auto

📈 សង្ខេបសរុប
──────────────────────────────

💰 KHR
   • ចំនួនទឹកប្រាក់: 626,000 ៛
   • ប្រតិបត្តិការ: 161 លើក

💰 USD
   • ចំនួនទឹកប្រាក់: 8.50 $
   • ប្រតិបត្តិការ: 10 លើក

━━━━━━━━━━━━━━━━━━━━━━
📊 សរុប: 171 ប្រតិបត្តិការ
```

## Database Schema

### Table: `custom_reports`
Stores custom SQL queries for each group.

```sql
CREATE TABLE custom_reports (
    id INT PRIMARY KEY AUTO_INCREMENT,
    chat_group_id INT NOT NULL,
    report_name VARCHAR(100) NOT NULL,
    description TEXT NULL,
    sql_query TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    schedule_time VARCHAR(5) NULL,  -- Format: "HH:MM" (e.g., "09:00") - NULL means manual only
    schedule_enabled BOOLEAN DEFAULT FALSE,
    last_run_at DATETIME NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,

    FOREIGN KEY (chat_group_id) REFERENCES chat_group(id) ON DELETE CASCADE,
    INDEX idx_chat_group_id (chat_group_id),
    INDEX idx_chat_group_id_active (chat_group_id, is_active),
    UNIQUE KEY unique_group_report_name (chat_group_id, report_name)
);
```

**Field Descriptions**:
- `chat_group_id`: Foreign key to `chat_group.id` table
- `report_name`: Display name shown in menu (e.g., "Daily Sales Report", "Weekly Summary")
- `description`: Optional description for the report
- `sql_query`: SQL query that returns income_balance compatible records
- `is_active`: Whether the report is active (inactive reports don't show in menu)
- `schedule_time`: Time to run report automatically (ICT timezone), NULL for manual-only
- `schedule_enabled`: Whether automatic scheduling is enabled for this report
- `last_run_at`: Last time the report was executed (for debugging/monitoring)

### Example SQL Queries

```sql
-- Example 1: Today's transactions
SELECT * FROM income_balance
WHERE chat_id = :group_id
AND DATE(income_date) = CURRENT_DATE();

-- Example 2: Yesterday's transactions
SELECT * FROM income_balance
WHERE chat_id = :group_id
AND DATE(income_date) = DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY);

-- Example 3: Last 7 days
SELECT * FROM income_balance
WHERE chat_id = :group_id
AND income_date >= DATE_SUB(NOW(), INTERVAL 7 DAY);

-- Example 4: Current month
SELECT * FROM income_balance
WHERE chat_id = :group_id
AND YEAR(income_date) = YEAR(CURRENT_DATE())
AND MONTH(income_date) = MONTH(CURRENT_DATE());
```

## Implementation Components

### 1. Database Migration
**File**: `migrations/versions/xxxx_create_custom_reports_table.py`

- Create `custom_reports` table
- Add indexes for performance

### 2. Model
**File**: `models/custom_report_model.py`

```python
class CustomReport(BaseModel):
    __tablename__ = "custom_reports"

    id: Mapped[int]
    chat_group_id: Mapped[int]
    report_name: Mapped[str]
    description: Mapped[str | None]
    sql_query: Mapped[str]
    is_active: Mapped[bool]
    schedule_time: Mapped[str | None]
    schedule_enabled: Mapped[bool]
    last_run_at: Mapped[datetime | None]

    # Relationship
    chat_group: Mapped["Chat"] = relationship("Chat", backref="custom_reports")
```

### 3. Service
**File**: `services/custom_report_service.py`

**Methods**:
- `get_active_reports_by_chat_id(chat_id: int) -> list[CustomReport]`
  - Gets chat_group_id from chat_id, then fetches active reports
- `get_active_reports_by_chat_group_id(chat_group_id: int) -> list[CustomReport]`
- `get_report_by_id(report_id: int) -> CustomReport | None`
- `execute_report(report_id: int) -> dict`
  - Executes SQL query with safety checks
  - Returns aggregated results by currency
- `create_report(...) -> CustomReport`
- `update_report(...) -> CustomReport`
- `delete_report(report_id: int) -> bool`
- `get_scheduled_reports() -> list[CustomReport]`
  - Returns all reports with `schedule_enabled=True`

**Security Considerations**:
- Validate SQL query before execution (read-only, no DDL/DML operations)
- Use parameterized queries (`:group_id` parameter)
- Limit query execution time
- Prevent SQL injection

### 4. Menu Handler Extension
**File**: `services/handlers/menu_handler.py` (modify existing)

**Changes**:
1. Add "របាយការណ៍ផ្ទាល់ខ្លួន" (Custom Reports) button when:
   - Package is BUSINESS
   - `CUSTOM_REPORT` feature flag is enabled

2. New callback handler: `custom_reports_menu`
   - Shows list of active reports for the chat
   - Each report name is a button

3. New callback handler: `execute_custom_report_{report_id}`
   - Executes the selected report
   - Formats and displays results

**Menu Flow**:
```
Main Menu
  ├─ Custom Reports (if enabled)
      ├─ Report Name 1
      ├─ Report Name 2
      ├─ Report Name 3
      └─ Back
```

### 5. Report Formatter Helper
**File**: `helper/custom_report_helper.py`

**Function**: `format_custom_report_result(report_name: str, results: dict, execution_date: datetime) -> str`

**Input** (results dict):
```json
{
    "currencies": {
        "KHR": {"amount": 8339200, "count": 109},
        "USD": {"amount": 30834.78, "count": 1179}
    },
    "total_count": 1288
}
```

**Output** (formatted message):
```
━━━━━━━━━━━━━━━━━━━━━━
📊 Daily Sales Report 🔄
Report Description
━━━━━━━━━━━━━━━━━━━━━━

📅 កាលបរិច្ឆេទ: 13-10-2025
⚡ ប្រភេទ: Auto

📈 សង្ខេបសរុប
──────────────────────────────

💰 KHR
   • ចំនួនទឹកប្រាក់: 8,339,200 ៛
   • ប្រតិបត្តិការ: 109 លើក

💰 USD
   • ចំនួនទឹកប្រាក់: 30,834.78 $
   • ប្រតិបត្តិការ: 1,179 លើក

━━━━━━━━━━━━━━━━━━━━━━
📊 សរុប: 1,288 ប្រតិបត្តិការ
```

### 6. Scheduler
**File**: `schedulers/custom_report_scheduler.py`

Similar pattern to `daily_summary_scheduler.py`:
- Use `schedule` library
- Run scheduled reports at configured times
- Send results to the group via bot
- Update `last_run_at` timestamp
- Handle timezone conversion (ICT to server time)

**Class**: `CustomReportScheduler`

**Methods**:
- `start_scheduler()` - Start the scheduler loop
- `stop_scheduler()` - Stop the scheduler
- `_setup_schedules()` - Load all scheduled reports and create jobs
- `_execute_scheduled_report(report_id: int)` - Execute and send report

### 7. Admin Commands (Optional but Recommended)
**File**: `services/handlers/custom_report_handler.py`

Admin commands for managing custom reports:
- `/create_report` - Create a new custom report
- `/edit_report` - Edit existing report
- `/delete_report` - Delete a report
- `/list_reports` - List all reports for the group
- `/test_report` - Test a report SQL query

## Implementation Flow

### Manual Report Execution Flow
```
1. User clicks /menu
2. Menu shows "Custom Reports" (if BUSINESS + flag enabled)
3. User clicks "Custom Reports"
4. System:
   - Gets chat_group_id from chat_id
   - Queries active reports for chat_group_id
5. Display report names as buttons
6. User clicks a report name
7. System:
   - Fetches report by ID (includes chat_group relationship)
   - Gets chat_id from chat_group
   - Validates permissions
   - Executes SQL query (replaces :group_id with chat_id)
   - Aggregates results by currency
   - Formats results
   - Updates last_run_at
   - Sends formatted message
```

### Automatic Report Execution Flow
```
1. Scheduler starts on bot startup
2. Loads all reports where schedule_enabled=True (with chat_group relationship)
3. For each report, creates a scheduled job at schedule_time
4. At scheduled time:
   - Get chat_id from chat_group
   - Execute SQL query (replace :group_id with chat_id)
   - Aggregate results
   - Format results
   - Send to chat_id via bot
   - Update last_run_at
5. Refresh schedules every 10 minutes (to pick up new/modified reports)
```

## SQL Query Execution Strategy

### Safety Measures
1. **Read-Only**: Enforce SELECT-only queries
2. **Timeout**: Set max execution time (e.g., 30 seconds)
3. **Parameterization**: Replace `:group_id` placeholder with actual value
4. **Validation**: Block dangerous keywords (DROP, INSERT, UPDATE, DELETE, ALTER, etc.)
5. **Row Limit**: Consider adding LIMIT if needed for performance

### Execution Steps
```python
def execute_report(report_id: int) -> dict:
    1. Fetch report from database (with chat_group relationship)
    2. Get chat_id from report.chat_group.chat_id
    3. Validate SQL query (check for dangerous keywords)
    4. Replace :group_id parameter with actual chat_id
    5. Execute query with timeout
    6. Fetch results as list of income_balance-like objects
    7. Aggregate by currency:
       - Group by currency
       - SUM(amount) per currency
       - COUNT(*) per currency
    8. Return aggregated results
```

## Integration Points

### 1. Main Bot Service
**File**: `main_bots_only.py` or similar

- Register custom report scheduler
- Start scheduler on bot startup

### 2. Menu Handler
**File**: `services/handlers/menu_handler.py`

- Add custom reports button to main menu (conditional)
- Add callback handlers for custom report flows

### 3. Feature Flag
**File**: `common/enums/feature_flags_enum.py`

- `CUSTOM_REPORT` flag already exists (line 16)

## Testing Strategy

### Unit Tests
1. `CustomReportService`
   - Test SQL validation logic
   - Test query execution with mock data
   - Test aggregation logic

2. `CustomReportFormatter`
   - Test output formatting with various inputs
   - Test edge cases (no results, single currency, etc.)

### Integration Tests
1. End-to-end manual report execution
2. End-to-end scheduled report execution
3. Permission checks (BUSINESS package + feature flag)
4. SQL injection prevention

### Test Data
```sql
-- First, get the chat_group_id for a test group
-- Assuming chat_group with id=1 exists for chat_id=-1001234567890

-- Test report 1: Simple daily report
INSERT INTO custom_reports (chat_group_id, report_name, sql_query, is_active, created_at, updated_at)
VALUES (1, 'Today Sales',
        'SELECT * FROM income_balance WHERE chat_id = :group_id AND DATE(income_date) = CURRENT_DATE()',
        TRUE, NOW(), NOW());

-- Test report 2: Scheduled weekly report
INSERT INTO custom_reports (chat_group_id, report_name, sql_query, is_active, schedule_time, schedule_enabled, created_at, updated_at)
VALUES (1, 'Weekly Summary',
        'SELECT * FROM income_balance WHERE chat_id = :group_id AND income_date >= DATE_SUB(NOW(), INTERVAL 7 DAY)',
        TRUE, '09:00', TRUE, NOW(), NOW());
```

## Rollout Plan

### Phase 1: Basic Functions ✅ COMPLETED
- [x] Database migration
- [x] Model creation
- [x] Service implementation (CRUD + execute)
- [x] Scheduler implementation
- [x] Report formatter helper
- [x] Menu integration
- [x] Callback handlers
- [x] Testing with real data

### Phase 2: Admin Tools (Optional)
- [ ] Admin command handlers
- [ ] Report management UI
- [ ] Testing and refinement
- [ ] Documentation

## Security Considerations

### 1. SQL Injection Prevention
- Whitelist allowed SQL keywords (SELECT, FROM, WHERE, etc.)
- Block dangerous keywords
- Use parameterized queries for group_id
- Consider using SQL parser library for validation

### 2. Performance
- Set query execution timeout
- Existing indexes on income_balance (chat_id, income_date) support queries
- Consider caching for frequently run reports
- Monitor query performance

### 3. Access Control
- Verify BUSINESS package before showing menu
- Verify CUSTOM_REPORT flag before execution
- Ensure report belongs to requesting chat_group_id
- Use foreign key constraints to maintain referential integrity

### 4. Error Handling
- Graceful handling of SQL errors
- User-friendly error messages
- Logging for debugging
- Prevent exposure of database structure in errors

## Monitoring and Logging

### Metrics to Track
- Report execution count per day
- Average execution time per report
- Failed executions (with error types)
- Most used reports

### Logging Points
- Report creation/modification/deletion
- Report execution start/end
- SQL query validation failures
- Scheduler job execution
- Errors and exceptions

## Future Enhancements (Post-MVP)

1. **Report Parameters**: Allow dynamic parameters in SQL (date range, amount threshold)
2. **Report Templates**: Predefined templates users can customize
3. **Export Options**: CSV, PDF export of results
4. **Visualizations**: Charts and graphs
5. **Report Sharing**: Share reports between groups
6. **Detailed Results**: Option to show line items instead of just summary
7. **Multi-Channel Delivery**: Send reports to multiple chats or private messages
8. **Report History**: Store historical report results

## Open Questions

1. **SQL Validation Library**: Should we use a library like `sqlparse` for better SQL validation?
2. **Result Limit**: Should we enforce a maximum number of rows returned?
3. **Report Permissions**: Should individual users have different access levels to reports?
4. **Error Notifications**: Where should scheduler errors be sent? (Admin group? Logs only?)
5. **Report Naming**: Should we enforce unique report names per group?
6. **Query Complexity**: Should we limit query complexity (no subqueries, joins, etc.)?

## Dependencies

### Python Packages
- `sqlalchemy` - Already in use
- `schedule` - Already in use
- `sqlparse` - Optional, for SQL validation
- `python-telegram-bot` - Already in use

### Database
- MySQL/MariaDB - Already in use
- Requires migration support - Already available (Alembic)

## Risks and Mitigation

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| SQL injection | High | Medium | Strict SQL validation, parameterization |
| Performance issues | Medium | Medium | Timeouts, query optimization, caching |
| Scheduler failures | Medium | Low | Error handling, logging, monitoring |
| User confusion | Low | High | Clear UI/UX, documentation, examples |
| Feature abuse | Medium | Low | Rate limiting, admin oversight |

## Success Criteria

1. **Functional**:
   - Users can create and execute custom reports
   - Reports display correct aggregated data
   - Scheduled reports run at correct times

2. **Performance**:
   - Report execution < 5 seconds for typical queries
   - No impact on bot responsiveness
   - Scheduler overhead < 1% CPU

3. **User Experience**:
   - Intuitive menu navigation
   - Clear report output formatting
   - Helpful error messages

4. **Reliability**:
   - 99.9% successful report executions
   - Zero data corruption incidents
   - Graceful degradation on errors
