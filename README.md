# Oracle Database Performance Tuning Tool

A comprehensive web-based tool for analyzing and tuning Oracle database performance. Provides deep insights into query performance, execution plans, resource usage, deadlocks, and actionable tuning recommendations.

## Features

### Query Performance Analysis
- 🔍 **Long-Running Query Detection** - Identify queries consuming excessive resources
- 📊 **Detailed Performance Metrics** - Elapsed time, CPU time, I/O statistics, executions
- 🎯 **Query Ranking** - Sort and filter queries by performance impact
- 📈 **Historical Trending** - Track query performance over time using AWR/ASH data

### Execution Plan Analysis
- 🌳 **Interactive Plan Visualization** - Visual tree representation of execution plans
- 💰 **Cost Analysis** - Identify expensive operations in execution plans
- 🔄 **Plan Comparison** - Compare current vs historical execution plans
- ⚠️ **Plan Regression Detection** - Detect when execution plans change negatively
- 📋 **Plan Baseline Suggestions** - Recommend plan baselines for stable queries

### Wait Event Analysis
- ⏱️ **Wait Event Breakdown** - Understand where queries spend time
- 📊 **Wait Event Categories** - Group by I/O, CPU, concurrency, network
- 📉 **Wait Event Timeline** - Visualize wait events over time
- 💡 **Wait Event Recommendations** - Actionable advice for reducing waits

### Resource Usage Analysis
- 👤 **User Resource Consumption** - Identify users consuming most resources
- 💻 **Session Analysis** - Active sessions and their resource usage
- 🔥 **Blocking Session Detection** - Find sessions causing blocks
- 📊 **CPU/Memory/I/O Breakdown** - Resource consumption by type

### Deadlock Detection
- 🔒 **Deadlock Identification** - Detect and analyze deadlocks
- 🕸️ **Deadlock Graph Visualization** - Visual representation of deadlock cycles
- 📝 **Deadlock History** - Track deadlocks over time
- 💡 **Resolution Recommendations** - Suggestions for preventing deadlocks

### Statistics Health Monitoring
- 📊 **Stale Statistics Detection** - Identify tables with outdated statistics
- 🔍 **Statistics Verification** - Check if statistics are being collected
- ⏰ **Statistics Job Monitoring** - Monitor automated statistics gathering
- 💡 **Statistics Recommendations** - When and how to gather statistics

### Oracle Bug Detection
- 🐛 **Bug Pattern Matching** - Detect known Oracle bugs from SQL_ID patterns
- 📋 **Alert Log Scanning** - Parse alert logs for bug signatures
- 🔬 **Trace File Analysis** - Analyze trace files for bug indicators
- 🔧 **Workarounds and Patches** - Provide bug fixes and workarounds

### Recommendation Engine
- 💡 **Index Suggestions** - Recommend indexes to improve performance
- ✍️ **SQL Rewrite Recommendations** - Suggest query optimizations
- 🎯 **Hint Suggestions** - Optimizer hints for better execution plans
- 📊 **Statistics Recommendations** - When to gather or refresh statistics
- 🔒 **Plan Baseline Recommendations** - Stabilize execution plans

## Technology Stack

### Backend
- **Python 3.11+** - Modern Python with type hints
- **FastAPI** - High-performance async web framework
- **cx_Oracle / python-oracledb** - Oracle database connectivity
- **Celery** - Background task processing
- **Redis** - Caching and task queue
- **pytest** - Testing framework

### Frontend
- **React 18+** - Modern React with hooks
- **TypeScript** - Type-safe JavaScript
- **React Query (TanStack Query)** - Server state management
- **Ant Design / Material-UI** - UI component library
- **Recharts / Apache ECharts** - Data visualizations
- **Vite** - Fast build tool

### Deployment
- **Docker** - Containerization
- **Docker Compose** - Multi-container orchestration
- **Nginx** - Reverse proxy
- **Kubernetes** - Production orchestration (optional)

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker and Docker Compose
- Oracle Instant Client
- Access to Oracle Database (11g+)

### Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd query_tuner_tool
   ```

2. **Set up environment variables**
   ```bash
   cp config/config.yaml.example config/config.yaml
   # Edit config.yaml with your Oracle connection details
   ```

3. **Start with Docker Compose**
   ```bash
   docker-compose -f deployment/docker/docker-compose.yml up
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Manual Setup

#### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements/dev.txt

# Set environment variables
export ORACLE_USER=monitor_user
export ORACLE_PASSWORD=your_password
export ORACLE_DSN=host:1521/service_name

# Run migrations (if any)
alembic upgrade head

# Start backend server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

#### Redis (for caching)

```bash
docker run -d -p 6379:6379 redis:7-alpine
```

## Oracle Database Setup

### Create Monitoring User

```sql
-- Create dedicated monitoring user
CREATE USER query_monitor IDENTIFIED BY secure_password;

-- Grant necessary privileges
GRANT CREATE SESSION TO query_monitor;
GRANT SELECT ANY DICTIONARY TO query_monitor;
GRANT SELECT_CATALOG_ROLE TO query_monitor;

-- Grant access to V$ views
GRANT SELECT ON v_$sql TO query_monitor;
GRANT SELECT ON v_$sql_plan TO query_monitor;
GRANT SELECT ON v_$session TO query_monitor;
GRANT SELECT ON v_$active_session_history TO query_monitor;
GRANT SELECT ON v_$session_wait TO query_monitor;
GRANT SELECT ON v_$lock TO query_monitor;
GRANT SELECT ON v_$sesstat TO query_monitor;
GRANT SELECT ON v_$statname TO query_monitor;
GRANT SELECT ON v_$version TO query_monitor;

-- Grant access to DBA_ views
GRANT SELECT ON dba_tab_statistics TO query_monitor;
GRANT SELECT ON dba_ind_statistics TO query_monitor;
GRANT SELECT ON dba_tables TO query_monitor;
GRANT SELECT ON dba_indexes TO query_monitor;
GRANT SELECT ON dba_scheduler_jobs TO query_monitor;

-- Grant AWR/ASH access (requires Diagnostics Pack license)
GRANT SELECT ON dba_hist_sqlstat TO query_monitor;
GRANT SELECT ON dba_hist_sql_plan TO query_monitor;
GRANT SELECT ON dba_hist_active_sess_history TO query_monitor;
GRANT SELECT ON dba_hist_snapshot TO query_monitor;
```

See [docs/oracle/PRIVILEGES.md](docs/oracle/PRIVILEGES.md) for detailed privilege information.

## Usage

### Connect to Database

1. Navigate to connection page
2. Enter Oracle connection details:
   - Host
   - Port
   - Service Name
   - Username
   - Password
3. Test connection
4. Save connection

### View Top Queries

1. After connecting, navigate to Queries page
2. View top queries sorted by elapsed time
3. Filter by:
   - Elapsed time threshold
   - Execution count
   - Schema/user
   - Time range
4. Click on a query to view details

### Analyze Query Performance

1. Click on a query to view details
2. View:
   - Full SQL text
   - Performance metrics (elapsed time, CPU, I/O)
   - Execution plan with cost breakdown
   - Wait events and their categories
   - Historical performance trends
3. Review recommendations for tuning

### Compare Execution Plans

1. From query details, navigate to execution plan
2. Select "Compare Plans"
3. Choose historical plan to compare
4. View side-by-side comparison highlighting changes

### Monitor Deadlocks

1. Navigate to Deadlocks page
2. View active and historical deadlocks
3. Click on deadlock to view:
   - Sessions involved
   - Locks held and waited for
   - Deadlock graph visualization
   - Resolution recommendations

## Configuration

### Environment Variables

```bash
# Oracle Connection
ORACLE_USER=monitor_user
ORACLE_PASSWORD=your_password
ORACLE_DSN=host:1521/service_name

# Application
SECRET_KEY=your-secret-key
JWT_SECRET=jwt-secret-key
ENVIRONMENT=development  # or production

# Redis
REDIS_URL=redis://localhost:6379

# Logging
LOG_LEVEL=INFO
```

### Configuration Files

- `config/config.yaml` - Main configuration
- `config/logging.yaml` - Logging configuration
- `config/oracle_queries.yaml` - Predefined Oracle queries

## API Documentation

Interactive API documentation available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

See [docs/api/API_REFERENCE.md](docs/api/API_REFERENCE.md) for complete API documentation.

## Testing

### Backend Tests

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/unit/test_connection.py

# Run specific test
pytest tests/unit/test_connection.py::TestConnectionManager::test_create_pool
```

### Frontend Tests

```bash
cd frontend

# Run unit tests
npm test

# Run with coverage
npm run test:coverage

# Run E2E tests
npm run test:e2e
```

## Documentation

- **[Architecture Documentation](docs/architecture/ARCHITECTURE.md)** - System architecture and design
- **[API Reference](docs/api/API_REFERENCE.md)** - Complete API documentation
- **[Development Guide](docs/development/SETUP.md)** - Development environment setup
- **[Deployment Guide](docs/deployment/DEPLOYMENT_GUIDE.md)** - Deployment instructions
- **[Oracle Documentation](docs/oracle/SYSTEM_VIEWS.md)** - Oracle-specific documentation
- **[User Guide](docs/user/USER_GUIDE.md)** - End-user documentation
- **[Coding Standards](standards/README.md)** - Code style and conventions

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](docs/development/CONTRIBUTING.md) for details on:
- Code of conduct
- Development process
- Submitting pull requests
- Coding standards

## License

[MIT License](LICENSE)

## Security

For security vulnerabilities, please see [SECURITY.md](SECURITY.md) for our security policy and how to report issues.

## Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/your-org/query-tuner-tool/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/query-tuner-tool/discussions)

## Roadmap

See [ROADMAP.md](ROADMAP.md) for planned features and future enhancements.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and release notes.

## Acknowledgments

- Oracle Database documentation and community
- FastAPI framework
- React and TypeScript communities
- All contributors to this project

## Screenshots

### Query List
![Query List](docs/screenshots/query_list.png)

### Execution Plan Visualization
![Execution Plan](docs/screenshots/execution_plan.png)

### Wait Event Analysis
![Wait Events](docs/screenshots/wait_events.png)

### Recommendations
![Recommendations](docs/screenshots/recommendations.png)

---

**Built with ❤️ for Oracle Database Administrators and Developers**
