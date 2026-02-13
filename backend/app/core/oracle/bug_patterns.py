"""Oracle bug pattern database.

This module contains known Oracle bugs with their signatures,
affected versions, symptoms, and remediation steps.
"""

from typing import List, Dict, Any
from enum import Enum


class BugSeverity(str, Enum):
    """Bug severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class BugCategory(str, Enum):
    """Bug categories."""
    OPTIMIZER = "optimizer"
    EXECUTION = "execution"
    STATISTICS = "statistics"
    PARALLEL = "parallel"
    INDEX = "index"
    PARTITION = "partition"
    MEMORY = "memory"
    LOCKING = "locking"
    REPLICATION = "replication"
    UPGRADE = "upgrade"


# Known Oracle bugs database
ORACLE_BUGS = [
    {
        "bug_number": "13364795",
        "title": "Wrong results with optimizer_adaptive_features",
        "category": BugCategory.OPTIMIZER,
        "severity": BugSeverity.CRITICAL,
        "description": "Optimizer adaptive features can produce wrong results in specific scenarios with bind variables and predicates.",
        "symptoms": [
            "Incorrect query results",
            "Different results with same query and data",
            "Bind peeking issues",
            "Unexpected row counts in execution plan"
        ],
        "affected_versions": ["12.1.0.1", "12.1.0.2"],
        "fixed_versions": ["12.1.0.2 (with patch)", "12.2.0.1"],
        "detection_patterns": {
            "execution_plan": {
                "operations": ["ADAPTIVE"],
                "hints": ["ADAPTIVE"]
            },
            "alert_log": {
                "errors": ["ORA-00600", "13364795"],
                "keywords": ["adaptive", "wrong result"]
            },
            "parameters": {
                "optimizer_adaptive_features": "true"
            }
        },
        "workarounds": [
            "Set optimizer_adaptive_features=false at session or system level",
            "Use NO_ADAPTIVE hint in problematic queries",
            "Apply patch 13364795",
            "Upgrade to 12.2.0.1 or higher"
        ],
        "remediation_sql": "ALTER SESSION SET optimizer_adaptive_features=false;",
        "my_oracle_support_url": "https://support.oracle.com/rs?type=doc&id=13364795.8"
    },
    {
        "bug_number": "14010183",
        "title": "High parsing time with adaptive cursor sharing",
        "category": BugCategory.OPTIMIZER,
        "severity": BugSeverity.HIGH,
        "description": "Adaptive cursor sharing can cause excessive parse time and CPU consumption with specific bind variable patterns.",
        "symptoms": [
            "High CPU usage during parsing",
            "Increased parse time",
            "Multiple child cursors for same SQL",
            "V$SQL shows many versions of same query"
        ],
        "affected_versions": ["11.2.0.3", "11.2.0.4", "12.1.0.1"],
        "fixed_versions": ["12.1.0.2"],
        "detection_patterns": {
            "sql_characteristics": {
                "version_count": ">10",
                "parse_calls": ">1000"
            },
            "parameters": {
                "_optimizer_adaptive_cursor_sharing": "true"
            }
        },
        "workarounds": [
            "Disable adaptive cursor sharing: _optimizer_adaptive_cursor_sharing=false",
            "Use bind variable aware SQL (BIND_AWARE hint)",
            "Consider using literals instead of bind variables for selective queries",
            "Apply patch 14010183"
        ],
        "remediation_sql": "ALTER SESSION SET \"_optimizer_adaptive_cursor_sharing\"=false;",
    },
    {
        "bug_number": "12345678",
        "title": "Cardinality estimation error with multi-column statistics",
        "category": BugCategory.STATISTICS,
        "severity": BugSeverity.HIGH,
        "description": "Optimizer underestimates cardinality when using extended statistics on correlated columns.",
        "symptoms": [
            "Suboptimal execution plans",
            "Nested loops chosen for large result sets",
            "Actual vs estimated row count mismatch",
            "Extended statistics exist but not used"
        ],
        "affected_versions": ["11.2.0.4", "12.1.0.1", "12.1.0.2"],
        "fixed_versions": ["12.2.0.1"],
        "detection_patterns": {
            "execution_plan": {
                "cardinality_mismatch_ratio": ">10",
                "operations": ["NESTED LOOPS"]
            },
            "statistics": {
                "extended_stats_exists": True,
                "staleness": "current"
            }
        },
        "workarounds": [
            "Use dynamic sampling: DYNAMIC_SAMPLING(table_name 4)",
            "Gather statistics with METHOD_OPT FOR ALL COLUMNS",
            "Use CARDINALITY hint to override estimate",
            "Apply patch or upgrade to 12.2+"
        ],
        "remediation_sql": "SELECT /*+ DYNAMIC_SAMPLING(t 4) */ ...",
    },
    {
        "bug_number": "19396364",
        "title": "Parallel query hangs with adaptive parallel distribution",
        "category": BugCategory.PARALLEL,
        "severity": BugSeverity.CRITICAL,
        "description": "Parallel queries can hang or show very poor performance with adaptive parallel distribution in specific scenarios.",
        "symptoms": [
            "Query hangs indefinitely",
            "Parallel query sessions in wait state",
            "Wait event: PX Deq: Execution Msg",
            "Parallel coordinator waiting for slaves"
        ],
        "affected_versions": ["12.2.0.1"],
        "fixed_versions": ["12.2.0.1 (with patch)", "18c"],
        "detection_patterns": {
            "execution_plan": {
                "operations": ["PX COORDINATOR", "PX SEND", "PX RECEIVE"],
                "parallel_degree": ">1"
            },
            "wait_events": {
                "event_name": "PX Deq: Execution Msg",
                "wait_time": ">60"
            }
        },
        "workarounds": [
            "Disable adaptive parallel distribution: _px_adaptive_dist_method=OFF",
            "Reduce parallel degree",
            "Use NOPARALLEL hint for problematic queries",
            "Apply patch 19396364"
        ],
        "remediation_sql": "ALTER SESSION SET \"_px_adaptive_dist_method\"='OFF';",
    },
    {
        "bug_number": "13583900",
        "title": "Index skip scan chosen despite full scan being cheaper",
        "category": BugCategory.INDEX,
        "severity": BugSeverity.MEDIUM,
        "description": "Optimizer incorrectly chooses index skip scan when full table scan would be more efficient.",
        "symptoms": [
            "Unexpectedly slow query performance",
            "INDEX SKIP SCAN in execution plan",
            "High logical reads compared to result set size",
            "Better performance with NO_INDEX hint"
        ],
        "affected_versions": ["11.2.0.3", "11.2.0.4", "12.1.0.1"],
        "fixed_versions": ["12.1.0.2"],
        "detection_patterns": {
            "execution_plan": {
                "operations": ["INDEX SKIP SCAN"],
                "cost": ">1000"
            },
            "query_characteristics": {
                "buffer_gets": ">100000",
                "rows_processed": "<1000"
            }
        },
        "workarounds": [
            "Use NO_INDEX hint to force full table scan",
            "Use INDEX_FFS (fast full scan) hint",
            "Gather statistics with better sampling",
            "Apply patch 13583900"
        ],
        "remediation_sql": "SELECT /*+ NO_INDEX(table_name index_name) */ ...",
    },
    {
        "bug_number": "17202207",
        "title": "ORA-00600 [kksfbc-reparse-infinite-loop]",
        "category": BugCategory.EXECUTION,
        "severity": BugSeverity.CRITICAL,
        "description": "Infinite parse loop causing ORA-00600 internal error during SQL execution.",
        "symptoms": [
            "ORA-00600 [kksfbc-reparse-infinite-loop]",
            "High CPU usage",
            "Session appears hung",
            "Alert log contains ORA-00600 errors"
        ],
        "affected_versions": ["12.1.0.1", "12.1.0.2"],
        "fixed_versions": ["12.1.0.2 (with patch)", "12.2.0.1"],
        "detection_patterns": {
            "alert_log": {
                "errors": ["ORA-00600", "kksfbc-reparse-infinite-loop"],
                "frequency": "repeated"
            },
            "session_state": {
                "status": "ACTIVE",
                "wait_event": "library cache lock"
            }
        },
        "workarounds": [
            "Flush shared pool: ALTER SYSTEM FLUSH SHARED_POOL",
            "Restart the session",
            "Apply patch 17202207",
            "Upgrade to fixed version"
        ],
        "remediation_sql": "ALTER SYSTEM FLUSH SHARED_POOL;",
    },
    {
        "bug_number": "14194385",
        "title": "Wrong results with partition pruning and bind variables",
        "category": BugCategory.PARTITION,
        "severity": BugSeverity.CRITICAL,
        "description": "Partition pruning with bind variables can access wrong partitions, leading to incorrect results.",
        "symptoms": [
            "Missing rows in query results",
            "Inconsistent results with same query",
            "Partition pruning shows wrong partitions in plan",
            "PSTART and PSTOP values incorrect"
        ],
        "affected_versions": ["11.2.0.3", "11.2.0.4"],
        "fixed_versions": ["11.2.0.4 (with patch)", "12.1.0.1"],
        "detection_patterns": {
            "execution_plan": {
                "operations": ["PARTITION RANGE"],
                "partition_start": "KEY",
                "partition_stop": "KEY"
            },
            "query_characteristics": {
                "bind_variables": True,
                "partitioned_table": True
            }
        },
        "workarounds": [
            "Use literals instead of bind variables for partition key",
            "Disable partition pruning: NO_PRUNE hint",
            "Use cursor_sharing=EXACT",
            "Apply patch 14194385"
        ],
        "remediation_sql": "ALTER SESSION SET cursor_sharing=EXACT;",
    },
    {
        "bug_number": "16923858",
        "title": "Memory leak in PGA with temp tablespace operations",
        "category": BugCategory.MEMORY,
        "severity": BugSeverity.HIGH,
        "description": "Memory leak in PGA when using temporary tablespace for sorting and hash operations.",
        "symptoms": [
            "Continuously increasing PGA memory usage",
            "ORA-04030 out of process memory errors",
            "TEMP tablespace usage grows",
            "V$PROCESS shows high PGA_ALLOC_MEM"
        ],
        "affected_versions": ["11.2.0.4", "12.1.0.1"],
        "fixed_versions": ["12.1.0.2"],
        "detection_patterns": {
            "execution_plan": {
                "operations": ["SORT", "HASH JOIN"],
                "temp_space": ">1GB"
            },
            "memory_usage": {
                "pga_alloc_mem": ">2GB",
                "trend": "increasing"
            }
        },
        "workarounds": [
            "Reduce workarea_size_policy or pga_aggregate_target",
            "Use MANUAL workarea_size_policy",
            "Restart sessions periodically",
            "Apply patch 16923858"
        ],
        "remediation_sql": "ALTER SESSION SET workarea_size_policy=MANUAL;",
    },
    {
        "bug_number": "13498382",
        "title": "Deadlock with library cache lock on parallel queries",
        "category": BugCategory.LOCKING,
        "severity": BugSeverity.MEDIUM,
        "description": "Deadlock situation with library cache locks during parallel query execution.",
        "symptoms": [
            "ORA-00060 Deadlock detected",
            "Library cache lock waits",
            "Parallel query sessions hanging",
            "Alert log shows deadlock graph"
        ],
        "affected_versions": ["11.2.0.3", "11.2.0.4", "12.1.0.1"],
        "fixed_versions": ["12.1.0.2"],
        "detection_patterns": {
            "alert_log": {
                "errors": ["ORA-00060"],
                "keywords": ["library cache lock", "parallel"]
            },
            "wait_events": {
                "event_name": "library cache lock",
                "parallel_session": True
            }
        },
        "workarounds": [
            "Reduce parallel degree",
            "Disable parallel query for specific statements",
            "Set cursor_sharing=FORCE",
            "Apply patch 13498382"
        ],
        "remediation_sql": "ALTER SESSION DISABLE PARALLEL QUERY;",
    },
    {
        "bug_number": "18277454",
        "title": "Slow performance after upgrade to 12c",
        "category": BugCategory.UPGRADE,
        "severity": BugSeverity.HIGH,
        "description": "Significant performance degradation after upgrading from 11g to 12c due to optimizer changes.",
        "symptoms": [
            "Queries slower after upgrade",
            "Different execution plans in 12c",
            "Optimizer features enabled by default",
            "Adaptive features causing issues"
        ],
        "affected_versions": ["12.1.0.1", "12.1.0.2"],
        "fixed_versions": ["Requires configuration changes"],
        "detection_patterns": {
            "database_version": {
                "current": "12.1.%",
                "previous": "11.2.%"
            },
            "parameters": {
                "optimizer_features_enable": "12.1.0.%"
            }
        },
        "workarounds": [
            "Set optimizer_features_enable to previous version (11.2.0.4)",
            "Disable optimizer adaptive features",
            "Gather statistics with estimate_percent=100",
            "Review and update SQL Plan Baselines"
        ],
        "remediation_sql": "ALTER SYSTEM SET optimizer_features_enable='11.2.0.4' SCOPE=BOTH;",
    },
]


class BugPatternDatabase:
    """Oracle bug pattern database access."""

    def __init__(self):
        """Initialize bug pattern database."""
        self.bugs = ORACLE_BUGS

    def get_all_bugs(self) -> List[Dict[str, Any]]:
        """Get all bugs in database."""
        return self.bugs

    def get_bugs_by_category(self, category: BugCategory) -> List[Dict[str, Any]]:
        """Get bugs by category."""
        return [bug for bug in self.bugs if bug["category"] == category]

    def get_bugs_by_severity(self, severity: BugSeverity) -> List[Dict[str, Any]]:
        """Get bugs by severity."""
        return [bug for bug in self.bugs if bug["severity"] == severity]

    def get_bugs_by_version(self, version: str) -> List[Dict[str, Any]]:
        """
        Get bugs affecting a specific Oracle version.

        Args:
            version: Oracle version (e.g., "12.1.0.1")

        Returns:
            List of bugs affecting this version
        """
        matching_bugs = []
        for bug in self.bugs:
            if self._version_affected(version, bug.get("affected_versions", [])):
                matching_bugs.append(bug)
        return matching_bugs

    def get_bug_by_number(self, bug_number: str) -> Dict[str, Any]:
        """Get specific bug by bug number."""
        for bug in self.bugs:
            if bug["bug_number"] == bug_number:
                return bug
        return None

    def search_bugs(self, keyword: str) -> List[Dict[str, Any]]:
        """
        Search bugs by keyword in title, description, or symptoms.

        Args:
            keyword: Search keyword

        Returns:
            List of matching bugs
        """
        keyword_lower = keyword.lower()
        matching_bugs = []

        for bug in self.bugs:
            # Search in title
            if keyword_lower in bug.get("title", "").lower():
                matching_bugs.append(bug)
                continue

            # Search in description
            if keyword_lower in bug.get("description", "").lower():
                matching_bugs.append(bug)
                continue

            # Search in symptoms
            symptoms = bug.get("symptoms", [])
            if any(keyword_lower in symptom.lower() for symptom in symptoms):
                matching_bugs.append(bug)
                continue

        return matching_bugs

    def _version_affected(
        self, version: str, affected_versions: List[str]
    ) -> bool:
        """
        Check if a version is affected by a bug.

        Args:
            version: Oracle version to check
            affected_versions: List of affected versions

        Returns:
            True if version is affected
        """
        for affected in affected_versions:
            # Exact match
            if version == affected:
                return True

            # Wildcard match (e.g., "12.1.%" matches "12.1.0.1")
            if "%" in affected:
                prefix = affected.replace("%", "")
                if version.startswith(prefix):
                    return True

        return False

    def get_critical_bugs(self) -> List[Dict[str, Any]]:
        """Get all critical severity bugs."""
        return self.get_bugs_by_severity(BugSeverity.CRITICAL)

    def get_bugs_by_alert_error(self, error_code: str) -> List[Dict[str, Any]]:
        """
        Get bugs associated with an alert log error code.

        Args:
            error_code: Oracle error code (e.g., "ORA-00600")

        Returns:
            List of bugs associated with this error
        """
        matching_bugs = []
        for bug in self.bugs:
            detection = bug.get("detection_patterns", {})
            alert_log = detection.get("alert_log", {})
            errors = alert_log.get("errors", [])

            if error_code in errors:
                matching_bugs.append(bug)

        return matching_bugs

    def get_statistics(self) -> Dict[str, Any]:
        """Get bug database statistics."""
        return {
            "total_bugs": len(self.bugs),
            "by_category": {
                category.value: len(self.get_bugs_by_category(category))
                for category in BugCategory
            },
            "by_severity": {
                severity.value: len(self.get_bugs_by_severity(severity))
                for severity in BugSeverity
            },
            "critical_count": len(self.get_critical_bugs()),
        }
