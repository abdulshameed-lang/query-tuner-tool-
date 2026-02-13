# Testing Guide - Oracle Query Tuner Tool

This guide will help you quickly get the application running so you can test all the features we've built (Phases 4-12).

## Current Status

**✅ Completed Phases (4-12):**
- Phase 4: Query Performance Analysis
- Phase 5: Execution Plan Analysis
- Phase 6: Wait Event Analysis
- Phase 7: Resource Usage & User Analysis
- Phase 8: Deadlock Detection
- Phase 9: Statistics Health Check
- Phase 10: Bug Detection
- Phase 11: AWR/ASH Integration (Historical Analysis)
- Phase 12: Real-Time Monitoring (WebSocket)

**⏳ Pending Phases (13-15):**
- Phase 13: Security & Authentication
- Phase 14: Testing & Quality Assurance
- Phase 15: Deployment & Documentation

## Quick Start (Recommended)

### Prerequisites
- Docker and Docker Compose installed
- Access to an Oracle Database (11g, 12c, 19c, or 21c)
- Oracle database user with monitoring privileges (see [Oracle Setup](#oracle-database-setup))

### Option 1: Docker Compose (Fastest)

1. **Navigate to project directory**
   ```bash
   cd /Users/abdul/dev/query_tuner_tool
   ```

2. **Create environment file**
   ```bash
   cd deployment/docker
   cp .env.example .env
   ```

3. **Edit `.env` file with your Oracle credentials**
   ```bash
   nano .env  # or use your preferred editor
   ```

   Update these values:
   ```env
   ORACLE_USER=your_monitoring_user
   ORACLE_PASSWORD=your_password
   ORACLE_DSN=your_oracle_host:1521/your_service_name
   SECRET_KEY=any-random-string-here
   JWT_SECRET=another-random-string-here
   ```

4. **Start all services**
   ```bash
   docker-compose up -d
   ```

5. **Access the application**
   - **Frontend (Main UI)**: http://localhost:3000
   - **Backend API**: http://localhost:8000
   - **API Documentation**: http://localhost:8000/docs
   - **Redis (Cache)**: localhost:6379

6. **View logs**
   ```bash
   # View all logs
   docker-compose logs -f

   # View specific service logs
   docker-compose logs -f backend
   docker-compose logs -f frontend
   ```

7. **Stop services**
   ```bash
   docker-compose down
   ```

### Option 2: Manual Setup (More Control)

This option gives you more control and is better for development/debugging.

#### Step 1: Set Up Backend

```bash
cd /Users/abdul/dev/query_tuner_tool/backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements/dev.txt

# Set environment variables
export ORACLE_USER="your_monitoring_user"
export ORACLE_PASSWORD="your_password"
export ORACLE_DSN="your_oracle_host:1521/your_service_name"
export REDIS_URL="redis://localhost:6379"
export ENVIRONMENT="development"
export DEBUG="true"

# Start backend server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Backend should now be running at:** http://localhost:8000

Test it:
```bash
curl http://localhost:8000/health
# Should return: {"status":"healthy","environment":"development"}
```

#### Step 2: Set Up Frontend

Open a new terminal window:

```bash
cd /Users/abdul/dev/query_tuner_tool/frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

**Frontend should now be running at:** http://localhost:5173 (Vite default) or http://localhost:3000

#### Step 3: Set Up Redis (Required for Caching)

Open a new terminal window:

```bash
# Using Docker (recommended)
docker run -d -p 6379:6379 --name query-tuner-redis redis:7-alpine

# OR install Redis locally and run
redis-server
```

## Oracle Database Setup

### Create Monitoring User

You need an Oracle user with specific privileges to monitor the database. Connect to your Oracle database as SYSDBA or a user with DBA privileges:

```sql
-- Create dedicated monitoring user
CREATE USER query_monitor IDENTIFIED BY secure_password;

-- Essential privileges
GRANT CREATE SESSION TO query_monitor;
GRANT SELECT ANY DICTIONARY TO query_monitor;
GRANT SELECT_CATALOG_ROLE TO query_monitor;

-- Grant access to V$ views (real-time monitoring)
GRANT SELECT ON v_$sql TO query_monitor;
GRANT SELECT ON v_$sql_plan TO query_monitor;
GRANT SELECT ON v_$session TO query_monitor;
GRANT SELECT ON v_$active_session_history TO query_monitor;
GRANT SELECT ON v_$session_wait TO query_monitor;
GRANT SELECT ON v_$system_event TO query_monitor;
GRANT SELECT ON v_$sysstat TO query_monitor;
GRANT SELECT ON v_$lock TO query_monitor;
GRANT SELECT ON v_$sesstat TO query_monitor;
GRANT SELECT ON v_$statname TO query_monitor;
GRANT SELECT ON v_$version TO query_monitor;

-- Grant access to DBA_ views (statistics and metadata)
GRANT SELECT ON dba_tab_statistics TO query_monitor;
GRANT SELECT ON dba_ind_statistics TO query_monitor;
GRANT SELECT ON dba_tables TO query_monitor;
GRANT SELECT ON dba_indexes TO query_monitor;
GRANT SELECT ON dba_scheduler_jobs TO query_monitor;
GRANT SELECT ON dba_registry_sqlpatch TO query_monitor;

-- Grant AWR/ASH access (OPTIONAL - requires Oracle Diagnostics Pack license)
-- If you don't have this license, the tool will work but historical analysis will be limited
GRANT SELECT ON dba_hist_sqlstat TO query_monitor;
GRANT SELECT ON dba_hist_sql_plan TO query_monitor;
GRANT SELECT ON dba_hist_active_sess_history TO query_monitor;
GRANT SELECT ON dba_hist_snapshot TO query_monitor;
GRANT SELECT ON dba_hist_sysstat TO query_monitor;
GRANT SELECT ON dba_hist_system_event TO query_monitor;
```

### Verify Oracle Connection

Test your Oracle connection before starting the application:

```bash
# Using sqlplus
sqlplus query_monitor/secure_password@//your_oracle_host:1521/your_service_name

# Or using Python
python3 << EOF
import oracledb
try:
    conn = oracledb.connect(
        user="query_monitor",
        password="secure_password",
        dsn="your_oracle_host:1521/your_service_name"
    )
    print("✅ Connection successful!")
    cursor = conn.cursor()
    cursor.execute("SELECT banner FROM v\$version WHERE rownum = 1")
    print(f"Oracle Version: {cursor.fetchone()[0]}")
    conn.close()
except Exception as e:
    print(f"❌ Connection failed: {e}")
EOF
```

## Testing the Application

### 1. Access the Frontend

Open your browser and navigate to:
- **http://localhost:3000** (if using Docker)
- **http://localhost:5173** (if using manual setup with Vite)

### 2. Test Database Connection

1. You should see a connection form on the home page
2. Enter your Oracle connection details:
   - **Host**: your_oracle_host
   - **Port**: 1521
   - **Service Name**: your_service_name
   - **Username**: query_monitor
   - **Password**: secure_password
3. Click **Test Connection**
4. If successful, you'll see a success message

### 3. Test Core Features (Phase 4-12)

#### A. Query Performance Analysis (Phase 4)
1. Navigate to **Queries** page
2. You should see a list of top queries from V$SQL
3. Test sorting by:
   - Elapsed time
   - CPU time
   - Executions
   - Last execution time
4. Click on any query to view details

#### B. Execution Plan Analysis (Phase 5)
1. From the query details page, scroll to **Execution Plan** section
2. You should see an interactive tree visualization
3. Hover over operations to see details
4. Look for highlighted costly operations
5. Test expanding/collapsing tree nodes

#### C. Wait Event Analysis (Phase 6)
1. From query details, scroll to **Wait Events** section
2. You should see wait event breakdown by category
3. Check the wait event timeline chart
4. Review wait event recommendations

#### D. Resource Usage Analysis (Phase 7)
1. Navigate to **Users** page
2. View top users by resource consumption (CPU, I/O, memory)
3. Click on a user to see their active sessions
4. Navigate to **Sessions** page
5. View active sessions with their SQL and wait events

#### E. Deadlock Detection (Phase 8)
1. Navigate to **Deadlocks** page
2. If any deadlocks exist, you'll see them listed
3. Click on a deadlock to view:
   - Deadlock graph visualization
   - Sessions involved
   - Locks held and waited for
   - Resolution recommendations

#### F. Statistics Health Check (Phase 9)
1. Navigate to **Statistics** page
2. View tables with stale or missing statistics
3. Check statistics gathering job status
4. Review recommendations for statistics collection

#### G. Bug Detection (Phase 10)
1. Navigate to **Bugs** page
2. View detected Oracle bugs from:
   - SQL_ID pattern matching
   - Execution plan analysis
   - Wait event patterns
3. Click on a bug to view:
   - Bug details and severity
   - Affected SQL statements
   - Workarounds and patches
   - Oracle Support links

#### H. AWR/ASH Integration (Phase 11)
1. Navigate to **Historical Analysis** page
2. Select a time range
3. View:
   - **AWR Report**: Top SQL, wait events, load profile
   - **ASH Activity**: Active session history over time
   - **Historical Comparison**: Compare current vs historical performance
4. Test time-series charts for performance trends

#### I. Real-Time Monitoring (Phase 12)
1. Navigate to **Real-Time Dashboard**
2. You should see live updates (WebSocket connection)
3. Monitor:
   - **Top Queries**: Live query activity with NEW badges
   - **Active Sessions**: Session count and status
   - **Wait Events**: Real-time wait event changes
   - **Database Metrics**: System statistics (commits, executions, I/O)
4. Test controls:
   - Click **Pause** to stop updates
   - Click **Resume** to restart
   - Click **Reconnect All** to force reconnection
5. Check connection status indicators (Connected/Disconnected)

### 4. Test API Endpoints Directly

You can also test the API directly using the interactive documentation:

**Open:** http://localhost:8000/docs

Available endpoint categories:
- **Connection**: Database connection management
- **Queries**: Query performance endpoints
- **Execution Plans**: Plan analysis and comparison
- **Wait Events**: Wait event analysis
- **Users**: Resource usage by user
- **Sessions**: Session monitoring
- **Deadlocks**: Deadlock detection
- **Statistics**: Statistics health check
- **Bugs**: Bug detection
- **AWR/ASH**: Historical analysis
- **WebSocket**: Real-time monitoring

Try some example API calls:
```bash
# Get top queries
curl http://localhost:8000/api/v1/queries?limit=10&order_by=elapsed_time

# Get execution plan
curl http://localhost:8000/api/v1/execution-plans/{sql_id}

# Get system wait events
curl http://localhost:8000/api/v1/wait-events/system?limit=20

# Get AWR snapshots
curl http://localhost:8000/api/v1/awr-ash/snapshots?days_back=7

# Health check
curl http://localhost:8000/health
```

## WebSocket Testing

Test WebSocket connections directly:

```javascript
// Open browser console on http://localhost:3000
const ws = new WebSocket('ws://localhost:8000/api/v1/ws/queries?poll_interval=5&min_elapsed_time=0.1&limit=10');

ws.onopen = () => console.log('Connected');
ws.onmessage = (event) => console.log('Message:', JSON.parse(event.data));
ws.onerror = (error) => console.error('Error:', error);

// Send ping
ws.send(JSON.stringify({ type: 'ping' }));

// Close connection
ws.close();
```

## Troubleshooting

### Backend Issues

**Problem: "ModuleNotFoundError: No module named 'oracledb'"**
```bash
# Make sure you're in the virtual environment
source venv/bin/activate
pip install -r requirements/dev.txt
```

**Problem: "DPI-1047: Cannot locate a 64-bit Oracle Client library"**
- Install Oracle Instant Client: https://www.oracle.com/database/technologies/instant-client/downloads.html
- Set environment variables:
  ```bash
  export LD_LIBRARY_PATH=/path/to/instantclient:$LD_LIBRARY_PATH
  ```

**Problem: "Connection refused" when connecting to Oracle**
- Verify Oracle listener is running: `lsnrctl status`
- Check firewall rules allow port 1521
- Verify DSN format: `host:port/service_name`

**Problem: "ORA-01017: invalid username/password"**
- Verify credentials are correct
- Check if user has required privileges
- Try connecting with sqlplus to verify

### Frontend Issues

**Problem: "npm ERR! code ENOENT"**
```bash
# Delete node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

**Problem: "Cannot connect to backend API"**
- Verify backend is running: `curl http://localhost:8000/health`
- Check CORS settings in `backend/app/config.py`
- Verify frontend API URL is correct

**Problem: "WebSocket connection failed"**
- Check if backend WebSocket endpoints are working: http://localhost:8000/docs
- Verify no proxy is blocking WebSocket connections
- Check browser console for errors

### Redis Issues

**Problem: "Connection refused" when connecting to Redis**
```bash
# Check if Redis is running
docker ps | grep redis
# OR
redis-cli ping  # Should return PONG
```

### Docker Issues

**Problem: "Cannot connect to the Docker daemon"**
```bash
# Start Docker Desktop (macOS) or Docker service (Linux)
sudo systemctl start docker  # Linux
```

**Problem: "Port already in use"**
```bash
# Find and kill process using the port
lsof -ti:8000 | xargs kill -9  # Backend
lsof -ti:3000 | xargs kill -9  # Frontend
lsof -ti:6379 | xargs kill -9  # Redis
```

## Providing Feedback

After testing, please provide feedback on:

### Functionality
- ✅ Works as expected
- ⚠️ Works but has issues (describe)
- ❌ Doesn't work (describe error)

### User Experience
- Is the UI intuitive?
- Are the visualizations clear?
- Is the information actionable?
- Any confusing areas?

### Performance
- How responsive is the application?
- Any slow-loading pages?
- WebSocket connection stability?

### Missing Features
- What additional features would be useful?
- Any Oracle-specific functionality missing?
- Integration with other tools?

### Bugs Found
- Steps to reproduce
- Expected vs actual behavior
- Screenshots/error messages
- Browser and environment details

## Next Steps

Based on your testing feedback, we can:
1. Fix any bugs discovered
2. Add missing features you identify
3. Improve UI/UX based on your input
4. Continue with Phases 13-15:
   - Phase 13: Security & Authentication (JWT, user management)
   - Phase 14: Testing & QA (comprehensive test suite)
   - Phase 15: Deployment (production-ready configuration)

## Contact & Support

- Review the code in: `/Users/abdul/dev/query_tuner_tool`
- Check logs for debugging
- Use API documentation: http://localhost:8000/docs

---

**Happy Testing! 🚀**
