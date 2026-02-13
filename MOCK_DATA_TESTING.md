# Mock Data Testing Guide

## Overview
Mock data has been integrated into all API endpoints to allow testing without an Oracle database connection.

## What Was Implemented

### Backend Changes
All API endpoints now have fallback to mock data when Oracle connection fails:

1. **Queries API** (`/api/v1/queries/`)
   - Returns list of sample SQL queries with realistic metrics
   - Sorted by elapsed time (most expensive first)

2. **Execution Plans API** (`/api/v1/execution-plans/{sql_id}`)
   - Returns sample execution plan with operations tree
   - Includes table scans, joins, indexes

3. **Wait Events API** (`/api/v1/wait-events/`)
   - Returns sample wait events by category
   - Includes I/O, CPU, concurrency events

4. **Bugs API** (`/api/v1/bugs`)
   - Returns known Oracle bugs with workarounds
   - Includes severity levels and affected versions

5. **AWR/ASH API** (`/api/v1/awr-ash/`)
   - Returns sample AWR snapshots and reports
   - Includes historical performance data

6. **Deadlocks API** (`/api/v1/deadlocks`)
   - Returns sample deadlock scenarios
   - Includes session and resource information

7. **Recommendations API** (`/api/v1/recommendations/{sql_id}`)
   - Returns tuning recommendations
   - Includes index suggestions, SQL rewrites, hints

### Mock Data Service
Created `backend/app/services/mock_data_service.py` with methods:
- `generate_queries()` - 20+ sample SQL queries
- `generate_execution_plan()` - realistic execution plans
- `generate_wait_events()` - 10+ wait event types
- `generate_bugs()` - known Oracle bugs
- `generate_awr_snapshots()` - historical snapshots
- `generate_awr_report()` - complete AWR report
- `generate_deadlocks()` - deadlock scenarios
- `generate_recommendations()` - tuning suggestions

## How to Test

### 1. Login
- Navigate to http://localhost:5173
- Login or sign up with your credentials
- You should see "Login successful!"

### 2. Add Database Connection (if not already added)
- You'll be redirected to database connections page
- Fill in dummy Oracle connection details:
  - Connection Name: "TESTDB"
  - Database Type: Oracle
  - Host: localhost
  - Port: 1521
  - Service Name: XE
  - Username: test
  - Password: test
- Click "Save Connection"
- Connection will be saved (actual connection test will fail, but that's OK)

### 3. View Dashboard
- You should see the dashboard with feature cards
- All Oracle-supported features should show as "Available"

### 4. Test Query Analysis
- Click on "Query Tuning" card
- You'll navigate to `/queries` page
- Frontend will call `/api/v1/queries/?limit=50&order_by=elapsed_time`
- Backend will return mock data with 20 sample queries
- You should see a table with:
  - SQL_ID column (clickable)
  - SQL Text (truncated)
  - Elapsed Time (red tags)
  - CPU Time (orange tags)
  - Executions
  - Disk Reads
  - Buffer Gets
  - Actions button

### 5. Test Other Features
Click on other feature cards to test:
- **Execution Plans** - view query execution plans
- **Wait Events** - see wait event analysis
- **Bug Detection** - identify known bugs
- **Performance Reports** - view AWR reports
- **Deadlock Detection** - analyze deadlocks

## Verification

### Backend Logs
Check `backend.log` for mock data messages:
```bash
tail -f backend.log | grep "mock data"
```

You should see:
```
WARNING: Oracle connection failed, using mock data: Oracle connection not configured...
```

### API Testing with curl
Test any endpoint directly:

```bash
# Get queries
curl "http://localhost:8000/api/v1/queries/?limit=5" | python3 -m json.tool

# Get execution plan
curl "http://localhost:8000/api/v1/execution-plans/abc1234567890" | python3 -m json.tool

# Get wait events
curl "http://localhost:8000/api/v1/wait-events/system?top_n=10" | python3 -m json.tool

# Get bugs
curl "http://localhost:8000/api/v1/bugs" | python3 -m json.tool

# Get AWR snapshots
curl "http://localhost:8000/api/v1/awr-ash/snapshots?days_back=7" | python3 -m json.tool

# Get deadlocks
curl "http://localhost:8000/api/v1/deadlocks" | python3 -m json.tool

# Get recommendations
curl "http://localhost:8000/api/v1/recommendations/abc1234567890" | python3 -m json.tool
```

## Sample Mock Data

### Queries
- 20 realistic Oracle SQL queries
- SELECT, INSERT, UPDATE, DELETE, MERGE statements
- Includes bind variables, JOINs, subqueries, CTEs
- Realistic metrics (elapsed time, CPU, disk reads, buffer gets)
- Multiple schemas (HR, SALES, FINANCE, INVENTORY)

### Execution Plans
- Operation tree (SELECT STATEMENT, SORT, HASH JOIN, TABLE ACCESS, INDEX SCAN)
- Cost, cardinality, bytes, time estimates
- Object names (tables, indexes)

### Wait Events
- db file sequential read, db file scattered read
- log file sync, CPU time
- enq: TX - row lock contention
- latch: cache buffers chains

### Bugs
- Bug #13364795: Wrong results with optimizer_adaptive_features
- Bug #19692235: Performance degradation with adaptive joins
- Includes workarounds and affected versions

## Next Steps

### Phase 1: Complete Mock Data Integration ✅
- All API endpoints return mock data
- No Oracle database required for testing

### Phase 2: Frontend UI Completion (In Progress)
- Query detail page (click on SQL_ID)
- Execution plan visualization
- Wait event charts
- Bug detection page
- AWR report viewer

### Phase 3: Real Oracle Integration
- Connect to actual Oracle database
- Replace mock data with real V$SQL queries
- Test with Oracle XE Docker container

### Phase 4: Additional Features
- Real-time monitoring (WebSocket)
- Historical analysis
- Plan comparison
- Advanced recommendations

## Troubleshooting

### Backend not starting
```bash
cd backend
source venv/bin/activate
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend not starting
```bash
cd frontend
npm run dev
```

### Mock data not showing
1. Check backend logs: `tail -f backend.log`
2. Check browser console for errors (F12)
3. Verify API endpoint returns data: `curl "http://localhost:8000/api/v1/queries/?limit=5"`

### Authentication issues
1. Clear localStorage: Open browser console → `localStorage.clear()` → Refresh
2. Sign up with a new account
3. Check backend logs for authentication errors

## Current Status

✅ Backend mock data integration complete
✅ All API endpoints working with mock data
✅ Authentication system working
✅ Database connection management working
✅ Frontend routing configured
✅ Query list page functional
⏳ Query detail page (coming next)
⏳ Other feature pages (execution plans, wait events, etc.)

You can now test the complete UI flow from login → dashboard → query analysis with realistic mock data!
