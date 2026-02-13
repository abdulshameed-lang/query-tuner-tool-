# Performance Reports (AWR) Page - Ready for Testing! 🎉

## What's New

The **Performance Reports (AWR) Page** is now complete! This page provides Automatic Workload Repository reports for historical performance analysis.

## Features Implemented

### 1. Snapshot Browser
View available AWR snapshots:
- **Days selector** dropdown (1/3/7/14/30 days)
- **Refresh button** to reload snapshots
- **Snapshots table** showing:
  - Snapshot ID
  - Begin Time
  - End Time
- **Info alert** showing total snapshot count
- Hourly snapshots (24 per day)

### 2. Report Period Selection
Interactive controls to select report period:

**Begin Snapshot Selector:**
- Dropdown with all available snapshots
- Shows: #ID - Timestamp
- Auto-selects second-to-last snapshot

**End Snapshot Selector:**
- Dropdown with all available snapshots
- Shows: #ID - Timestamp
- Auto-selects last snapshot

**Generate Button:**
- Large primary button
- Icon: 📄 FileTextOutlined
- Disabled until both snapshots selected
- Shows loading spinner when generating

**Validation:**
- Alerts if begin/end not selected
- Alerts if begin >= end (invalid)

### 3. AWR Report Display
Once generated, shows comprehensive report:

**Report Information Card:**
- Database Name (blue tag)
- Instance Name (purple tag)
- Begin Snapshot #
- End Snapshot #
- Elapsed Time (formatted as h:m:s)

**Load Profile Card:**
Three rows of statistics:
- **DB Time** - Total database time (⏰)
- **DB CPU** - CPU time consumed (⚡ orange)
- **Redo Size** - Redo log volume (💾)
- **Logical Reads** - Buffer gets
- **Physical Reads** - Disk reads
- **User Calls** - User requests

**Efficiency Metrics Card:**
Three progress bars with status indicators:

1. **Buffer Hit Ratio**
   - Green bar if > 95% (Excellent ✓)
   - Orange bar if 90-95% (Good ⚠)
   - Red bar if < 90% (Needs improvement ✗)

2. **Library Cache Hit Ratio**
   - Green bar if > 95% (Excellent ✓)
   - Orange bar if < 95% (Good ⚠)

3. **Soft Parse Ratio**
   - Green bar if > 95% (Excellent ✓)
   - Orange bar if < 95% (Consider bind variables ⚠)

**Top SQL by Elapsed Time Table:**
- SQL_ID (monospace, blue)
- Elapsed Time (red tag with h:m:s format)
- Executions (formatted K/M)
- SQL Text (truncated to 80 chars)
- Shows top 10 queries from the report period

**Top Wait Events Table:**
- Event name
- Wait Class (blue tag)
- Total Waits (formatted)
- Time Waited (bold, formatted)
- Shows top 10 wait events

**Success Alert:**
- Green success message
- Checkmark icon
- Instructions to review metrics

## Sample AWR Report Data

### Report Info
```
Database: TESTDB
Instance: testdb1
Period: Snapshot #1000 to #1001
Elapsed Time: 1h 0m 0s
```

### Load Profile
```
DB Time: 1h 0m 0s
DB CPU: 40m 0s
Redo Size: 125.00M
Logical Reads: 5.00M
Physical Reads: 125.00K
User Calls: 85.00K
```

### Efficiency Metrics
```
Buffer Hit Ratio: 97.5% ✓ Excellent (Green)
Library Cache Hit Ratio: 99.2% ✓ Excellent (Green)
Soft Parse Ratio: 98.5% ✓ Excellent (Green)
```

### Top 10 SQL
1. DELETE FROM temp_data - 47.86M μs
2. MERGE INTO inventory - 38.59M μs
3. SELECT /*+ INDEX */ employee - 34.67M μs
4. SELECT employee JOIN departments - 33.55M μs
5. INSERT INTO orders - 33.52M μs
...and 5 more

### Top 10 Wait Events
1. db file sequential read - 1.25M waits, 125K cs
2. db file scattered read - 85K waits, 42.5K cs
3. log file sync - 95K waits, 9.5K cs
4. SQL*Net message from client - 500K waits, 2.5M cs
...and 6 more

## How to Test

### Step 1: Navigate to Performance Reports
1. Open browser: **http://localhost:5173**
2. Click **"Performance Reports"** card on dashboard (purple chart icon)
3. You'll navigate to `/performance` page

### Step 2: Review Available Snapshots
You'll see:
- ℹ️ Info alert: "Found 168 snapshots" (7 days × 24 hours)
- Table with snapshots showing IDs 1000-1167
- Each row shows: Snap ID, Begin Time, End Time
- Pagination controls at bottom

### Step 3: Select Report Period

**Default Selection (Auto):**
- Begin Snapshot: #1166 (automatically selected)
- End Snapshot: #1167 (automatically selected)

**Or Select Manually:**
- Click "Begin Snapshot" dropdown
- Select any snapshot (e.g., #1000)
- Click "End Snapshot" dropdown
- Select a later snapshot (e.g., #1001)

### Step 4: Generate AWR Report
1. Click **"Generate AWR Report"** button (blue, large)
2. See loading spinner: "Generating report..."
3. Report appears below after 1-2 seconds

### Step 5: Review Report Sections

**Report Information:**
- See TESTDB, testdb1, snapshot range, 1 hour elapsed

**Load Profile:**
- 6 statistics displayed in grid
- DB Time: 1h, DB CPU: 40m, etc.

**Efficiency Metrics:**
- Three progress bars all green (97.5%, 99.2%, 98.5%)
- All showing "✓ Excellent"

**Top SQL:**
- Table with 10 queries
- See SQL_IDs, elapsed times, executions
- Read truncated SQL text

**Top Wait Events:**
- Table with 10 events
- See I/O waits, commit waits, idle waits

**Success Message:**
- Green alert at bottom
- "Report Generated Successfully"

### Step 6: Test Different Periods

**Try Different Days:**
- Change dropdown to "Last 1 Day"
- See fewer snapshots (24)
- Generate new report

**Try Custom Range:**
- Select begin snapshot from morning
- Select end snapshot from afternoon
- Generate report for that time range

**Refresh Data:**
- Click Refresh button
- Snapshots reload
- Selection resets to last 2 snapshots

## Visual Design

### Color Scheme
- **Blue** - Database tags, SQL_IDs, primary buttons
- **Purple** - Instance tags, chart icon
- **Red** - Elapsed time tags (critical metric)
- **Orange** - CPU metrics (performance)
- **Green** - Success indicators, excellent metrics

### Layout
- **Clean cards** for each section
- **Bordered descriptions** for report info
- **Grid layouts** for statistics (3 columns)
- **Progress bars** for efficiency metrics
- **Tables** for top SQL and wait events
- **Proper spacing** between sections with dividers

### Icons
- 📊 Bar chart for main title
- 🔄 Reload for refresh
- 📄 File for generate report
- ⏰ Clock for time metrics
- ⚡ Bolt for CPU
- 💾 Database for storage
- ✅ Check for success

## API Endpoints Used

The page fetches data from:

**Get Snapshots:**
```
GET /api/v1/awr-ash/snapshots?days_back={days}
```

**Generate Report:**
```
GET /api/v1/awr-ash/report?begin_snap_id={begin}&end_snap_id={end}
```

## Understanding AWR Metrics

**DB Time:**
- Total time database spent working
- Includes CPU + Wait Time
- Higher = more database activity

**DB CPU:**
- Time spent on CPU
- Should be 50-70% of DB Time
- Too high = CPU-bound, too low = wait-bound

**Buffer Hit Ratio:**
- % of data found in memory
- > 95% is excellent
- < 90% suggests need for more memory

**Library Cache Hit Ratio:**
- % of SQL found in cache (no parse needed)
- > 95% is excellent
- < 90% suggests hard parse issues

**Soft Parse Ratio:**
- % of executions that avoided hard parse
- > 95% is excellent
- Low = use bind variables

## What's Working

✅ AWR snapshot browsing (7 days default)
✅ Days selector (1/3/7/14/30 days)
✅ Snapshot table with pagination
✅ Begin/End snapshot selection
✅ Auto-selection of last 2 snapshots
✅ Report generation with loading state
✅ Report information display
✅ Load profile statistics (6 metrics)
✅ Efficiency metrics (3 progress bars)
✅ Top SQL table (10 queries)
✅ Top wait events table (10 events)
✅ Success/error alerts
✅ Validation (begin < end)
✅ Time formatting (hours:minutes:seconds)
✅ Number formatting (K/M/B)
✅ Mock data integration complete

## Empty States

**Before Report Generated:**
- Shows snapshot selection UI
- Shows available snapshots table
- "Generate AWR Report" button prominent

**After Report Generated:**
- All sections visible
- Scrollable content
- Can generate new report with different periods

## Next Steps

Now that Performance Reports is complete, you can:

1. **Test the complete flow**: Dashboard → Performance Reports
2. **Browse snapshots** for different time periods
3. **Generate reports** for various snapshot ranges
4. **Review metrics** to identify performance issues
5. **Compare** different time periods
6. All feature pages now complete! 🎉

## Quick Test Commands

Test backend endpoints:
```bash
# Get snapshots
curl "http://localhost:8000/api/v1/awr-ash/snapshots?days_back=7" | python3 -m json.tool | head -50

# Generate report
curl "http://localhost:8000/api/v1/awr-ash/report?begin_snap_id=1000&end_snap_id=1001" | python3 -m json.tool | head -100
```

## Current Status

✅ Authentication system
✅ Database connection management
✅ Dashboard with feature cards
✅ Queries list page
✅ Query detail page
✅ Wait events page
✅ Bug detection page
✅ **Performance reports page** ← **YOU ARE HERE!**
✅ **All major feature pages complete!** 🎉

---

**Go test it now!** Open http://localhost:5173, click "Performance Reports", browse snapshots, and generate your first AWR report! 📊✨
