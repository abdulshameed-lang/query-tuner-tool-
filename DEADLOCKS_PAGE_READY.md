# Deadlock Detection Page - Ready for Testing! 🎉

## What's New

The **Deadlock Detection Page** is now complete! This page helps you identify, visualize, and understand database deadlocks that occur when two or more sessions are waiting for resources held by each other.

## Features Implemented

### 1. Deadlock Overview Table
View all detected deadlocks in a comprehensive table:
- **Deadlock ID** - Unique identifier (#1, #2, #3...)
- **Detected Time** - When the deadlock was detected (with clock icon)
- **Type** - Deadlock type tag (TX-TX, TM-TM)
- **Sessions** - SID pairs involved (e.g., SID 145 ↔ SID 287)
- **Duration** - How long the deadlock lasted (in seconds)
- **Impact** - Severity level (HIGH/MEDIUM/LOW) with color coding
- **Action** - "View Details" button

**Impact Color Coding:**
- 🔴 **RED** - HIGH impact
- 🟠 **ORANGE** - MEDIUM impact
- 🟡 **YELLOW** - LOW impact

### 2. Interactive Deadlock Visualization
Visual representation of the deadlock cycle:

```
     [Session 1]          DEADLOCK          [Session 2]
    (Blue Circle)     ⚠️ Warning Icon      (Green Circle)
      SID 145              ⇄ Arrows           SID 287
    APP_USER          Waiting on each      APP_USER
  app-server-01           other           app-server-02
```

**Visual Features:**
- Two circular nodes representing each session
- Color-coded: Blue for Session 1, Green for Session 2
- Database icon inside each circle
- SID displayed prominently
- Username and machine below each circle
- Central warning icon and deadlock type
- Bidirectional arrows showing mutual waiting

### 3. Detailed Session Information
For each session involved in the deadlock:

**Session Card Shows:**
- Session ID (SID:SERIAL format, e.g., 145:1234)
- Username (blue tag)
- SQL ID (clickable link to Query Detail page)
- Program (e.g., "JDBC Thin Client", "python3", "sqlplus")
- Machine hostname
- Blocking Resource (e.g., "TX-00050018-00001234")

**Two Cards Side-by-Side:**
- Session 1 on the left
- Session 2 on the right

### 4. Deadlock Information Card
Comprehensive deadlock details:
- **Deadlock ID** - #1, #2, etc.
- **Detected Time** - Full timestamp
- **Deadlock Type** - TX-TX (Transaction), TM-TM (DML Lock)
- **Resource Type** - Transaction Lock, DML Lock
- **Duration** - Seconds with lightning icon
- **Impact** - HIGH/MEDIUM/LOW with color tag

### 5. Resolution Information
Shows how Oracle automatically resolved the deadlock:
- ✅ **Green success alert**
- Explains which session was chosen as deadlock victim
- States that the session was rolled back

### 6. Prevention Recommendations
Timeline of best practices to prevent deadlocks:

1. **Consistent Locking Order**
   - Ensure all sessions access resources in the same order
   - Prevents circular dependencies

2. **Keep Transactions Short**
   - Minimize transaction duration
   - Reduce lock holding time and deadlock probability

3. **Use Lower Isolation Levels**
   - Consider READ COMMITTED instead of SERIALIZABLE
   - If application logic permits

4. **Implement Retry Logic**
   - Add application-level retry logic
   - Handle ORA-00060 exceptions gracefully

### 7. Empty State
When no deadlocks are detected:
- ✅ Large green checkmark icon
- **"No Deadlocks Detected"** title
- Positive message: "Great news! No deadlocks have been detected recently."

### 8. Info Alert
Educational alert at the top:
- 💡 Explains what a deadlock is
- Notes that Oracle automatically detects and resolves deadlocks
- Describes the rollback mechanism

## Mock Data Details

The page displays 3 sample deadlock scenarios:

### Deadlock #1 - TX-TX (HIGH Impact)
- **Detected:** 2 hours ago
- **Type:** Transaction Lock (TX-TX)
- **Session 1:** SID 145 (APP_USER) on app-server-01
- **Session 2:** SID 287 (APP_USER) on app-server-02
- **Program:** JDBC Thin Client
- **Duration:** 12 seconds
- **Resolution:** Session 145 rolled back

### Deadlock #2 - TM-TM (MEDIUM Impact)
- **Detected:** 5 hours ago
- **Type:** DML Lock (TM-TM)
- **Session 1:** SID 201 (SALES_APP) on batch-server-01
- **Session 2:** SID 312 (SALES_APP) on batch-server-02
- **Program:** python3
- **Duration:** 8 seconds
- **Resolution:** Session 312 rolled back

### Deadlock #3 - TX-TX (HIGH Impact)
- **Detected:** 24 hours ago
- **Type:** Transaction Lock (TX-TX)
- **Session 1:** SID 89 (INVENTORY_APP) on inv-server-01
- **Session 2:** SID 156 (INVENTORY_APP) on inv-server-02
- **Program:** sqlplus
- **Duration:** 15 seconds
- **Resolution:** Session 89 rolled back

## How to Test

### Step 1: Navigate to Deadlock Detection
1. Open browser: **http://localhost:5173**
2. Click **"Deadlock Detection"** in the left sidebar (warning icon)
3. Or click the **"Deadlock Detection"** card on dashboard (if enabled)
4. You'll navigate to `/deadlocks` page

### Step 2: Review Deadlocks Table
You'll see:
- Table with 3 detected deadlocks
- Each row showing: ID, time, type, sessions, duration, impact
- Clickable rows (highlighted on selection)
- First deadlock auto-selected

### Step 3: Explore Deadlock Visualization
In the visualization area:
- **Left Circle (Blue)** - Session 1 with SID and username
- **Center Warning Icon** - Shows deadlock type (TX-TX or TM-TM)
- **Right Circle (Green)** - Session 2 with SID and username
- **Arrows** - Bidirectional showing mutual waiting
- **Machine Names** - Displayed below each circle

### Step 4: Review Session Details
Two cards side-by-side:
- **Session 1 Card:**
  - SID: 145:1234
  - Username: APP_USER (blue tag)
  - SQL ID: Clickable link (13 characters)
  - Program: JDBC Thin Client
  - Machine: app-server-01
  - Blocking Resource: TX-00050018-00001234 (code format)

- **Session 2 Card:**
  - Similar details for the second session

### Step 5: Click SQL ID Link
- Click the SQL_ID link in session details
- Should navigate to `/queries/{sql_id}` page
- Shows full query details (if query exists in system)

### Step 6: Review Deadlock Information
Card showing:
- Deadlock ID: #1
- Detected Time: Full timestamp with clock icon
- Type: TX-TX (purple tag)
- Resource Type: Transaction Lock (blue tag)
- Duration: 12 seconds (lightning icon)
- Impact: HIGH (red tag with exclamation icon)

### Step 7: Read Resolution
Green success alert:
- "Automatic Resolution"
- "Session 145 was chosen as deadlock victim and rolled back"

### Step 8: Review Prevention Recommendations
Timeline with 4 recommendations:
1. Consistent Locking Order
2. Keep Transactions Short
3. Use Lower Isolation Levels
4. Implement Retry Logic

Each with detailed explanation

### Step 9: Select Different Deadlocks
- Click on row #2 or #3 in the table
- Row highlights in light blue
- Details below update to show that deadlock
- Visualization updates with new sessions
- Try all 3 deadlocks

### Step 10: Test Refresh
- Click **"Refresh"** button (top right)
- See loading spinner briefly
- Data reloads with same deadlocks

## Visual Design

### Color Scheme
- **Blue** (#1890ff) - Session 1 circle, tags
- **Green** (#52c41a) - Session 2 circle, success alerts
- **Red** (#ff4d4f) - Warning icon, HIGH impact, deadlock emphasis
- **Orange** (#fa8c16) - MEDIUM impact
- **Purple** (#722ed1) - Deadlock type tags
- **Light Blue** (#e6f7ff) - Selected row background
- **Gray** (#f5f5f5) - Visualization background

### Icons
- ⚠️ **WarningOutlined** - Main page icon, deadlock indicator
- 🕒 **ClockCircleOutlined** - Detected time
- 💾 **DatabaseOutlined** - Session circles, menu
- 👤 **UserOutlined** - Username indicator
- ⚡ **ThunderboltOutlined** - Duration
- ✅ **CheckCircleOutlined** - Resolution, no deadlocks state
- ❗ **ExclamationCircleOutlined** - Impact severity
- 💡 **InfoCircleOutlined** - Info alerts, recommendations
- 🔄 **ReloadOutlined** - Refresh button

### Layout
- **Clean card-based design** for each section
- **Circular visualization** for intuitive understanding
- **Side-by-side session cards** for easy comparison
- **Timeline** for recommendations (vertical with dots)
- **Bordered descriptions** for structured data
- **Proper spacing** between sections with dividers

## API Endpoint Used

The page fetches data from:

**Get Deadlocks:**
```
GET /api/v1/deadlocks
```

**Response Format:**
```json
{
  "deadlocks": [
    {
      "deadlock_id": 1,
      "detected_time": "2026-02-12T18:31:57",
      "session1": {
        "sid": 145,
        "serial": 1234,
        "username": "APP_USER",
        "sql_id": "4h8d6870613g5",
        "program": "JDBC Thin Client",
        "machine": "app-server-01",
        "blocking_resource": "TX-00050018-00001234"
      },
      "session2": { ... },
      "resource_type": "Transaction Lock",
      "deadlock_type": "TX-TX",
      "resolution": "Session 145 was chosen as deadlock victim",
      "duration_seconds": 12,
      "impact": "HIGH"
    }
  ],
  "total_count": 3,
  "note": "Using mock data..."
}
```

## Understanding Deadlocks

### What is a Deadlock?
A deadlock occurs when two or more sessions are waiting for resources (locks) held by each other, creating a circular dependency that cannot be resolved without external intervention.

### Deadlock Types

**TX-TX (Transaction Lock):**
- Most common type
- Two sessions updating the same rows
- Each holds locks the other needs

**TM-TM (DML Lock):**
- Table-level lock deadlock
- Often involving DDL operations
- Can occur with foreign key constraints

### How Oracle Resolves Deadlocks

1. **Automatic Detection** - Oracle automatically detects deadlocks
2. **Choose Victim** - Selects one session as the deadlock victim
3. **Rollback** - Rolls back the victim session's transaction
4. **Error ORA-00060** - Returns error to victim session
5. **Other Session Continues** - Non-victim session proceeds

### Impact Levels

- **HIGH** - Long duration (>10s), affects critical transactions
- **MEDIUM** - Moderate duration (5-10s), affects batch processes
- **LOW** - Short duration (<5s), minimal impact

## What's Working

✅ Deadlock list table with 3 scenarios
✅ Interactive row selection with highlighting
✅ Visual deadlock representation (circles + arrows)
✅ Detailed session information cards
✅ Clickable SQL_ID links to query details
✅ Deadlock information display
✅ Resolution information with success alert
✅ Prevention recommendations timeline
✅ Empty state for no deadlocks
✅ Info alert explaining deadlocks
✅ Refresh functionality
✅ Color-coded impact severity
✅ Responsive layout
✅ Mock data integration complete

## Empty States

**When Deadlocks Exist:**
- Shows table with all deadlocks
- Auto-selects first deadlock
- Displays full details below

**When No Deadlocks:**
- Shows large green checkmark
- "No Deadlocks Detected" title
- Positive congratulatory message
- No table displayed

## Navigation Integration

**From Dashboard:**
- Click "Deadlock Detection" feature card
- Navigates to `/deadlocks`

**From Sidebar Menu:**
- Click "Deadlock Detection" menu item
- Warning icon visible
- Navigates to `/deadlocks`

**From Deadlock Page:**
- Click SQL_ID link → Navigate to `/queries/{sql_id}`
- View full query details for involved SQL

## Next Steps

Now that Deadlock Detection is complete, you can:

1. **Test the complete flow**: Dashboard → Deadlock Detection
2. **Review each deadlock** in the table
3. **Explore visualizations** for understanding relationships
4. **Click SQL_IDs** to investigate queries involved
5. **Read prevention recommendations** for best practices
6. All major feature pages now complete! 🎉

## Quick Test Commands

Test backend endpoint:
```bash
# Get all deadlocks
curl "http://localhost:8000/api/v1/deadlocks" | python3 -m json.tool | head -80

# Expected: 3 deadlocks with TX-TX and TM-TM types
```

## Current Status

✅ Authentication system
✅ Database connection management
✅ Dashboard with feature cards
✅ Queries list page
✅ Query detail page
✅ Wait events page
✅ Bug detection page
✅ Performance reports (AWR) page
✅ **Deadlock detection page** ← **YOU ARE HERE!**
✅ **All major feature pages complete!** 🎉🎉

---

**Go test it now!** Open http://localhost:5173, click "Deadlock Detection" in the sidebar, and explore the deadlock visualizations! ⚠️✨
