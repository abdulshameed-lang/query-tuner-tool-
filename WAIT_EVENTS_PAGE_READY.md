# Wait Events Page - Ready for Testing! 🎉

## What's New

The **Wait Events Page** is now complete! This page provides system-wide analysis of Oracle database wait events to identify performance bottlenecks.

## Features Implemented

### 1. Summary Statistics Dashboard
Four key metrics displayed at the top:
- **Total Wait Events** - Number of different wait event types
- **Total Waits** - Cumulative count of all wait occurrences
- **Total Time Waited** - Total time spent waiting (in centiseconds)
- **Avg Wait Time** - Average wait duration (in milliseconds)

### 2. Wait Class Breakdown
Visual breakdown of wait events grouped by class:
- **User I/O** - Database file reads (blue icon)
- **System I/O** - Log file writes, control file operations (cyan)
- **Commit** - Log file sync waits (green)
- **CPU** - CPU time consumption (red)
- **Application** - Application-level locks (orange)
- **Concurrency** - Library cache locks, latches (purple)
- **Idle** - Idle wait events (default)
- **Network** - SQL*Net waits (geekblue)
- **Configuration** - Configuration issues (magenta)
- **Other** - Other wait types (gray)

Each wait class card shows:
- Number of events in that class
- Total time waited
- **Progress bar** showing percentage of total wait time
- Color-coded by severity (red > 30%, orange > 15%, green < 15%)

### 3. Intelligent Recommendations
Automated analysis with actionable recommendations:

**High I/O Wait Time Alert:**
- Triggers when I/O waits > 40% of total time
- Suggests query optimization, indexing, or storage upgrades

**Concurrency Issues Alert:**
- Triggers when lock/latch waits > 20% of total time
- Suggests reviewing application logic and transaction scope

**Slow Commit Performance Alert:**
- Triggers when log file sync > 10ms average
- Suggests faster storage for redo logs

**High CPU Usage Alert:**
- Triggers when CPU time > 60% of total time
- Suggests SQL tuning and execution plan review

**Healthy Status:**
- Shows success message when no issues detected

### 4. Comprehensive Wait Events Table
Sortable, filterable table with all wait events:

**Columns:**
- **Event** - Wait event name (bolded)
- **Wait Class** - Categorized with color-coded tags and icons
- **Total Waits** - Number of occurrences (formatted: K/M)
- **Time Waited** - Total time in centiseconds (red, formatted)
- **Avg Wait** - Average wait duration in milliseconds
- **Impact** - Progress bar showing % of total wait time
  - Red bar if > 20% impact
  - Orange if > 10%
  - Gold if > 5%
  - Green if < 5%

**Features:**
- Click column headers to sort
- Filter by wait class using dropdown filters
- Pagination (20 events per page, adjustable)
- Scroll horizontally if needed
- Shows total count

### 5. Configurable Display
Top-right controls:
- **Dropdown selector** to choose number of events:
  - Top 20 Events
  - Top 50 Events
  - Top 100 Events
- **Refresh button** to reload data
- Loading spinner during data fetch

## Sample Wait Events Data

The mock data includes 10 realistic wait events:

1. **db file sequential read** (User I/O)
   - 1.25M waits, 125K cs waited, 0.1ms avg
   - Most common I/O wait - single block reads

2. **db file scattered read** (User I/O)
   - 85K waits, 42.5K cs waited, 0.5ms avg
   - Multi-block reads (full table scans)

3. **log file sync** (Commit)
   - 95K waits, 9.5K cs waited, 0.1ms avg
   - Transaction commits waiting for redo

4. **SQL*Net message from client** (Idle)
   - 500K waits, 2.5M cs waited, 5.0ms avg
   - Idle time waiting for client

5. **CPU time** (CPU)
   - 450K cs total
   - Actual CPU consumption

6. **log file parallel write** (System I/O)
   - 45K waits, 4.5K cs waited, 0.1ms avg
   - LGWR writing to redo logs

7. **direct path read** (User I/O)
   - 12K waits, 3.6K cs waited, 0.3ms avg
   - Direct path reads (bypassing buffer cache)

8. **enq: TX - row lock contention** (Application)
   - 850 waits, 8.5K cs waited, 10.0ms avg
   - Row-level lock waits

9. **latch: cache buffers chains** (Concurrency)
   - 2.5K waits, 250 cs waited, 0.1ms avg
   - Buffer cache latch contention

10. **library cache lock** (Concurrency)
    - 450 waits, 900 cs waited, 2.0ms avg
    - Hard parse contention

## How to Test

### Step 1: Navigate to Wait Events Page
1. Open browser: **http://localhost:5173**
2. Login if not already logged in
3. Click **"Wait Events"** card on dashboard (orange icon)
4. You'll navigate to `/wait-events` page

### Step 2: Explore Summary Statistics
At the top you should see:
- Total Wait Events: 10
- Total Waits: 1.96M (formatted)
- Total Time Waited: 3.14M cs
- Avg Wait Time: 1.60ms

### Step 3: Review Wait Class Breakdown
You'll see a grid of cards, each showing:
- **User I/O**: 3 events, large time percentage (likely highest)
- **Commit**: 1 event
- **Idle**: 1 event (may be high %)
- **CPU**: 1 event
- **System I/O**: 1 event
- **Application**: 1 event
- **Concurrency**: 2 events

Each with a color-coded progress bar.

### Step 4: Check Recommendations
Based on the mock data, you might see recommendations like:
- ⚠️ High I/O Wait Time Detected
- ⚠️ Concurrency Issues Detected
- Or ✅ Wait Events Look Healthy

### Step 5: Interact with the Table
**Sorting:**
- Click "Total Waits" header → sorts by wait count
- Click "Time Waited" header → sorts by total time
- Click "Avg Wait" header → sorts by average duration

**Filtering:**
- Click "Wait Class" filter icon
- Select one or more wait classes
- Table updates to show only selected classes

**Pagination:**
- Use pagination controls at bottom
- Change page size (10/20/50/100 per page)
- See total count: "Total 10 wait events"

### Step 6: Try Different Views
**Change number of events:**
- Select "Top 100 Events" from dropdown
- Click Refresh
- Table updates (though mock data only has 10)

**Refresh data:**
- Click Refresh button
- See loading spinner
- Data reloads

## Visual Design

### Color Scheme
- **Blue/Cyan** - I/O related waits
- **Red** - CPU and critical issues
- **Orange** - Application issues
- **Purple** - Concurrency problems
- **Green** - Commits and healthy status
- **Gray** - Idle and other

### Layout
- **Clean cards** with proper spacing
- **Grid layout** for wait class breakdown (2 columns)
- **Progress bars** for visual impact analysis
- **Icons** next to wait classes for quick identification
- **Monospace font** for numbers (proper alignment)
- **Color-coded tags** for easy classification

### Responsive Design
- Cards stack on smaller screens
- Table scrolls horizontally when needed
- Statistics grid adapts to screen size

## API Endpoint Used

The page fetches data from:
```
GET /api/v1/wait-events/current/system?top_n={limit}
```

**Response format:**
```json
{
  "events": [
    {
      "event": "db file sequential read",
      "wait_class": "User I/O",
      "total_waits": 1250000,
      "time_waited": 125000,
      "average_wait": 0.1
    },
    ...
  ],
  "timestamp": "2026-02-12T19:53:14.602072",
  "note": "Using mock data (Oracle database not available)"
}
```

## Performance Insights

The page automatically calculates and displays:

1. **Wait Class Distribution** - Which categories consume most time
2. **Top Wait Events** - Sorted by impact
3. **Impact Analysis** - Percentage of each event
4. **Average Wait Times** - Identify slow operations
5. **Recommendations** - Automated problem detection

## What's Working

✅ System-wide wait events analysis
✅ Wait class breakdown with progress bars
✅ Intelligent recommendations based on thresholds
✅ Sortable and filterable table
✅ Impact percentage calculation
✅ Color-coded severity indicators
✅ Mock data integration complete
✅ Responsive layout
✅ Professional styling with Ant Design

## Next Steps

Now that Wait Events page is complete, you can:

1. **Test the complete flow**: Dashboard → Wait Events
2. **Explore wait class breakdown** to see distribution
3. **Review recommendations** for tuning suggestions
4. **Sort and filter** the events table
5. **Move on to other feature pages**:
   - ⏳ Bug Detection page
   - ⏳ Performance Reports (AWR) page
   - ⏳ Deadlock Detection page
   - ⏳ Execution Plans visualization page

## Quick Test Command

Test the backend endpoint directly:
```bash
curl "http://localhost:8000/api/v1/wait-events/current/system?top_n=20" | python3 -m json.tool
```

## Understanding Wait Events (Quick Guide)

**User I/O Waits:**
- Caused by: Slow storage, missing indexes, full table scans
- Fix: Add indexes, optimize queries, upgrade storage

**Concurrency Waits:**
- Caused by: Lock contention, latch waits, hot blocks
- Fix: Reduce transaction scope, optimize code, partition data

**Commit Waits:**
- Caused by: Slow redo log writes
- Fix: Faster storage for redo logs, reduce commit frequency

**CPU Time:**
- Caused by: Inefficient SQL, high parse rates
- Fix: SQL tuning, bind variables, optimizer statistics

## Current Status

✅ Authentication system
✅ Database connection management
✅ Dashboard with feature cards
✅ Queries list page
✅ Query detail page
✅ **Wait events page** ← **YOU ARE HERE!**
⏳ Other feature pages (next)

---

**Go test it now!** Open http://localhost:5173, click on the "Wait Events" card, and explore the system-wide wait event analysis! 🚀
