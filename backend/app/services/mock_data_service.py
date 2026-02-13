"""Mock data service for testing without Oracle database."""

import random
from datetime import datetime, timedelta
from typing import List, Dict, Any


class MockDataService:
    """Generate realistic mock Oracle data for testing."""

    @staticmethod
    def generate_queries(limit: int = 20) -> List[Dict[str, Any]]:
        """Generate mock SQL queries."""
        sample_sqls = [
            "SELECT * FROM employees WHERE department_id = :dept_id AND salary > :min_sal ORDER BY hire_date DESC",
            "INSERT INTO orders (order_id, customer_id, order_date, total_amount) VALUES (:1, :2, :3, :4)",
            "UPDATE customers SET last_purchase_date = SYSDATE, total_spent = total_spent + :amount WHERE customer_id = :id",
            "SELECT e.employee_name, d.department_name, e.salary FROM employees e JOIN departments d ON e.department_id = d.department_id WHERE e.salary > 50000",
            "DELETE FROM temp_data WHERE created_date < SYSDATE - 30",
            "SELECT COUNT(*) as order_count, SUM(total_amount) as total_revenue FROM orders WHERE order_date >= TRUNC(SYSDATE, 'MM')",
            "SELECT product_id, product_name, (SELECT COUNT(*) FROM order_items WHERE product_id = p.product_id) as order_count FROM products p",
            "MERGE INTO inventory i USING (SELECT product_id, SUM(quantity) qty FROM shipments WHERE status = 'RECEIVED' GROUP BY product_id) s ON (i.product_id = s.product_id) WHEN MATCHED THEN UPDATE SET i.quantity = i.quantity + s.qty",
            "WITH monthly_sales AS (SELECT TRUNC(order_date, 'MM') month, SUM(total_amount) amount FROM orders GROUP BY TRUNC(order_date, 'MM')) SELECT * FROM monthly_sales WHERE amount > 100000",
            "SELECT /*+ INDEX(e emp_dept_idx) */ employee_id, employee_name FROM employees e WHERE department_id = :dept AND status = 'ACTIVE'",
        ]

        queries = []
        for i in range(min(limit, 50)):
            # Generate 13-character SQL_ID (Oracle standard format)
            sql_id = ''.join(random.choices('abcdefgh0123456789', k=13))
            queries.append({
                "sql_id": sql_id,
                "sql_text": random.choice(sample_sqls),
                "elapsed_time": random.randint(100000, 50000000),  # microseconds
                "cpu_time": random.randint(50000, 30000000),
                "executions": random.randint(1, 10000),
                "disk_reads": random.randint(0, 100000),
                "buffer_gets": random.randint(1000, 1000000),
                "rows_processed": random.randint(1, 50000),
                "first_load_time": (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat(),
                "last_active_time": (datetime.now() - timedelta(hours=random.randint(1, 24))).isoformat(),
                "plan_hash_value": random.randint(1000000000, 4000000000),
                "parsing_schema_name": random.choice(["HR", "SALES", "FINANCE", "INVENTORY"]),
            })

        # Sort by elapsed time descending
        queries.sort(key=lambda x: x["elapsed_time"], reverse=True)
        return queries

    @staticmethod
    def generate_execution_plan(sql_id: str) -> Dict[str, Any]:
        """Generate mock execution plan."""
        operations = [
            {
                "id": 0,
                "operation": "SELECT STATEMENT",
                "options": None,
                "object_name": None,
                "cost": 1234,
                "cardinality": 10000,
                "bytes": 500000,
                "time": 45,
                "parent_id": None,
            },
            {
                "id": 1,
                "operation": "SORT",
                "options": "ORDER BY",
                "object_name": None,
                "cost": 1233,
                "cardinality": 10000,
                "bytes": 500000,
                "time": 44,
                "parent_id": 0,
            },
            {
                "id": 2,
                "operation": "HASH JOIN",
                "options": None,
                "object_name": None,
                "cost": 850,
                "cardinality": 10000,
                "bytes": 500000,
                "time": 30,
                "parent_id": 1,
            },
            {
                "id": 3,
                "operation": "TABLE ACCESS",
                "options": "FULL",
                "object_name": "EMPLOYEES",
                "cost": 425,
                "cardinality": 5000,
                "bytes": 250000,
                "time": 15,
                "parent_id": 2,
            },
            {
                "id": 4,
                "operation": "INDEX",
                "options": "RANGE SCAN",
                "object_name": "DEPT_IDX",
                "cost": 425,
                "cardinality": 5000,
                "bytes": 250000,
                "time": 15,
                "parent_id": 2,
            },
        ]

        return {
            "sql_id": sql_id,
            "plan_hash_value": random.randint(1000000000, 4000000000),
            "operations": operations,
            "total_cost": 1234,
            "estimated_rows": 10000,
        }

    @staticmethod
    def generate_wait_events(limit: int = 20) -> List[Dict[str, Any]]:
        """Generate mock wait events."""
        events = [
            {"event": "db file sequential read", "wait_class": "User I/O", "total_waits": 1250000, "time_waited": 125000, "average_wait": 0.1},
            {"event": "db file scattered read", "wait_class": "User I/O", "total_waits": 85000, "time_waited": 42500, "average_wait": 0.5},
            {"event": "log file sync", "wait_class": "Commit", "total_waits": 95000, "time_waited": 9500, "average_wait": 0.1},
            {"event": "SQL*Net message from client", "wait_class": "Idle", "total_waits": 500000, "time_waited": 2500000, "average_wait": 5.0},
            {"event": "CPU time", "wait_class": "CPU", "total_waits": 0, "time_waited": 450000, "average_wait": 0},
            {"event": "log file parallel write", "wait_class": "System I/O", "total_waits": 45000, "time_waited": 4500, "average_wait": 0.1},
            {"event": "direct path read", "wait_class": "User I/O", "total_waits": 12000, "time_waited": 3600, "average_wait": 0.3},
            {"event": "enq: TX - row lock contention", "wait_class": "Application", "total_waits": 850, "time_waited": 8500, "average_wait": 10.0},
            {"event": "latch: cache buffers chains", "wait_class": "Concurrency", "total_waits": 2500, "time_waited": 250, "average_wait": 0.1},
            {"event": "library cache lock", "wait_class": "Concurrency", "total_waits": 450, "time_waited": 900, "average_wait": 2.0},
        ]
        return events[:limit]

    @staticmethod
    def generate_bugs() -> List[Dict[str, Any]]:
        """Generate mock bug detections."""
        return [
            {
                "bug_number": "13364795",
                "title": "Wrong results with optimizer_adaptive_features",
                "severity": "CRITICAL",
                "category": "OPTIMIZER",
                "description": "Query returns incorrect results when adaptive features are enabled",
                "workaround": "Set optimizer_adaptive_features=FALSE",
                "affected_versions": ["12.1.0.1", "12.1.0.2"],
                "affected_sql_ids": ["a1b2c3d4e5f6"],
                "confidence": 0.85,
                "detection_signals": ["execution_plan", "parameters"],
            },
            {
                "bug_number": "19692235",
                "title": "Performance degradation with adaptive joins",
                "severity": "HIGH",
                "category": "PERFORMANCE",
                "description": "Queries with hash joins show significant slowdown",
                "workaround": "Use /*+ NO_ADAPTIVE_PLAN */ hint",
                "affected_versions": ["12.2.0.1"],
                "affected_sql_ids": ["x9y8z7w6v5u4"],
                "confidence": 0.72,
                "detection_signals": ["wait_events", "execution_plan"],
            },
        ]

    @staticmethod
    def generate_awr_snapshots(days_back: int = 7) -> List[Dict[str, Any]]:
        """Generate mock AWR snapshots."""
        snapshots = []
        total_snapshots = days_back * 24  # hourly snapshots
        for i in range(total_snapshots):
            # Calculate hours ago: oldest snapshot first, newest last
            hours_ago = (total_snapshots - 1) - i
            snap_time = datetime.now() - timedelta(hours=hours_ago)
            snapshots.append({
                "snap_id": 1000 + i,
                "begin_time": snap_time.isoformat(),
                "end_time": (snap_time + timedelta(hours=1)).isoformat(),
                "startup_time": (datetime.now() - timedelta(days=30)).isoformat(),
            })
        return snapshots

    @staticmethod
    def generate_awr_report(begin_snap_id: int, end_snap_id: int) -> Dict[str, Any]:
        """Generate mock AWR report."""
        return {
            "report_info": {
                "db_name": "TESTDB",
                "instance_name": "testdb1",
                "begin_snap_id": begin_snap_id,
                "end_snap_id": end_snap_id,
                "elapsed_time": 3600,
            },
            "top_sql_by_elapsed_time": MockDataService.generate_queries(10),
            "wait_events": MockDataService.generate_wait_events(10),
            "load_profile": {
                "db_time": 3600,
                "db_cpu": 2400,
                "redo_size": 125000000,
                "logical_reads": 5000000,
                "physical_reads": 125000,
                "user_calls": 85000,
            },
            "efficiency_metrics": {
                "buffer_hit_ratio": 97.5,
                "library_cache_hit_ratio": 99.2,
                "soft_parse_ratio": 98.5,
            },
        }

    @staticmethod
    def generate_deadlocks() -> List[Dict[str, Any]]:
        """Generate mock deadlock data."""
        return [
            {
                "deadlock_id": 1,
                "detected_time": (datetime.now() - timedelta(hours=2)).isoformat(),
                "session1": {
                    "sid": 145,
                    "serial": 1234,
                    "username": "APP_USER",
                    "sql_id": ''.join(random.choices('abcdefgh0123456789', k=13)),
                    "program": "JDBC Thin Client",
                    "machine": "app-server-01",
                    "blocking_resource": "TX-00050018-00001234",
                },
                "session2": {
                    "sid": 287,
                    "serial": 5678,
                    "username": "APP_USER",
                    "sql_id": ''.join(random.choices('abcdefgh0123456789', k=13)),
                    "program": "JDBC Thin Client",
                    "machine": "app-server-02",
                    "blocking_resource": "TX-00060019-00005678",
                },
                "resource_type": "Transaction Lock",
                "deadlock_type": "TX-TX",
                "resolution": "Session 145 was chosen as deadlock victim and rolled back",
                "duration_seconds": 12,
                "impact": "HIGH",
            },
            {
                "deadlock_id": 2,
                "detected_time": (datetime.now() - timedelta(hours=5)).isoformat(),
                "session1": {
                    "sid": 201,
                    "serial": 3456,
                    "username": "SALES_APP",
                    "sql_id": ''.join(random.choices('abcdefgh0123456789', k=13)),
                    "program": "python3",
                    "machine": "batch-server-01",
                    "blocking_resource": "TM-00001234-00000001",
                },
                "session2": {
                    "sid": 312,
                    "serial": 7890,
                    "username": "SALES_APP",
                    "sql_id": ''.join(random.choices('abcdefgh0123456789', k=13)),
                    "program": "python3",
                    "machine": "batch-server-02",
                    "blocking_resource": "TM-00005678-00000002",
                },
                "resource_type": "DML Lock",
                "deadlock_type": "TM-TM",
                "resolution": "Session 312 was chosen as deadlock victim and rolled back",
                "duration_seconds": 8,
                "impact": "MEDIUM",
            },
            {
                "deadlock_id": 3,
                "detected_time": (datetime.now() - timedelta(hours=24)).isoformat(),
                "session1": {
                    "sid": 89,
                    "serial": 2341,
                    "username": "INVENTORY_APP",
                    "sql_id": ''.join(random.choices('abcdefgh0123456789', k=13)),
                    "program": "sqlplus@inv-server",
                    "machine": "inv-server-01",
                    "blocking_resource": "TX-00070020-00002345",
                },
                "session2": {
                    "sid": 156,
                    "serial": 4567,
                    "username": "INVENTORY_APP",
                    "sql_id": ''.join(random.choices('abcdefgh0123456789', k=13)),
                    "program": "sqlplus@inv-server",
                    "machine": "inv-server-02",
                    "blocking_resource": "TX-00080021-00006789",
                },
                "resource_type": "Transaction Lock",
                "deadlock_type": "TX-TX",
                "resolution": "Session 89 was chosen as deadlock victim and rolled back",
                "duration_seconds": 15,
                "impact": "HIGH",
            },
        ]

    @staticmethod
    def generate_recommendations(sql_id: str) -> Dict[str, Any]:
        """Generate mock tuning recommendations."""
        return {
            "sql_id": sql_id,
            "recommendations": [
                {
                    "type": "INDEX",
                    "priority": "HIGH",
                    "title": "Create index on EMPLOYEES(DEPARTMENT_ID, SALARY)",
                    "description": "Query is performing full table scan on EMPLOYEES table. Creating composite index will improve performance.",
                    "estimated_benefit": "75% reduction in elapsed time",
                    "sql": "CREATE INDEX emp_dept_sal_idx ON employees(department_id, salary);",
                },
                {
                    "type": "SQL_REWRITE",
                    "priority": "MEDIUM",
                    "title": "Use bind variables instead of literals",
                    "description": "Query uses literal values which prevents cursor sharing and increases hard parsing.",
                    "estimated_benefit": "Reduce library cache contention",
                    "sql": "Replace literals with bind variables like :dept_id",
                },
                {
                    "type": "STATISTICS",
                    "priority": "HIGH",
                    "title": "Gather table statistics",
                    "description": "Statistics on EMPLOYEES table are stale (last analyzed 45 days ago).",
                    "estimated_benefit": "Improve optimizer decisions",
                    "sql": "EXEC DBMS_STATS.GATHER_TABLE_STATS('HR', 'EMPLOYEES');",
                },
            ],
        }
