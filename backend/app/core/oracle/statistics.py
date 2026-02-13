"""Oracle statistics health checker.

This module provides functionality to check table and index statistics
health and detect stale or missing statistics.
"""

from typing import List, Dict, Any, Optional
import logging
from datetime import datetime, timedelta

from app.core.oracle.connection import ConnectionManager

logger = logging.getLogger(__name__)


class StatisticsChecker:
    """Checks Oracle statistics health for tables and indexes."""

    # System schemas to exclude
    SYSTEM_SCHEMAS = [
        "SYS", "SYSTEM", "DBSNMP", "SYSMAN", "OUTLN", "MDSYS", "ORDSYS",
        "EXFSYS", "WMSYS", "APPQOSSYS", "APEX_050000", "OWBSYS", "OWBSYS_AUDIT",
        "ORACLE_OCM", "XDB", "ANONYMOUS", "CTXSYS", "SI_INFORMTN_SCHEMA",
        "OLAPSYS", "ORDDATA", "ORDPLUGINS", "FLOWS_FILES", "APEX_PUBLIC_USER"
    ]

    def __init__(self, connection_manager: ConnectionManager):
        """
        Initialize StatisticsChecker.

        Args:
            connection_manager: Oracle connection manager instance
        """
        self.connection_manager = connection_manager

    def fetch_table_statistics(
        self, schema: Optional[str] = None, exclude_system: bool = True,
        stale_only: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Fetch table statistics from DBA_TAB_STATISTICS.

        Args:
            schema: Specific schema to check (None for all)
            exclude_system: Exclude system schemas
            stale_only: Only return tables with stale statistics

        Returns:
            List of table statistics
        """
        query = """
            SELECT
                owner,
                table_name,
                num_rows,
                blocks,
                avg_row_len,
                sample_size,
                last_analyzed,
                stale_stats,
                stattype_locked,
                avg_space,
                chain_cnt,
                avg_space_freelist_blocks
            FROM dba_tab_statistics
            WHERE partitioned = 'NO'
        """

        conditions = []
        bind_params = {}

        if exclude_system:
            placeholders = ", ".join([f":schema{i}" for i in range(len(self.SYSTEM_SCHEMAS))])
            conditions.append(f"owner NOT IN ({placeholders})")
            for i, sys_schema in enumerate(self.SYSTEM_SCHEMAS):
                bind_params[f"schema{i}"] = sys_schema

        if schema:
            conditions.append("owner = :owner")
            bind_params["owner"] = schema.upper()

        if stale_only:
            conditions.append("stale_stats = 'YES'")

        if conditions:
            query += " AND " + " AND ".join(conditions)

        query += " ORDER BY owner, table_name"

        with self.connection_manager.get_connection() as connection:
            cursor = connection.cursor()
            try:
                cursor.execute(query, bind_params)
                columns = [col[0].lower() for col in cursor.description]
                rows = cursor.fetchall()

                statistics = []
                for row in rows:
                    stat = dict(zip(columns, row))
                    stat = self._convert_oracle_types(stat)
                    # Calculate additional metrics
                    stat = self._enrich_table_statistics(stat)
                    statistics.append(stat)

                logger.info(f"Fetched {len(statistics)} table statistics")

                return statistics

            finally:
                cursor.close()

    def fetch_index_statistics(
        self, schema: Optional[str] = None, exclude_system: bool = True,
        stale_only: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Fetch index statistics from DBA_IND_STATISTICS.

        Args:
            schema: Specific schema to check
            exclude_system: Exclude system schemas
            stale_only: Only return indexes with stale statistics

        Returns:
            List of index statistics
        """
        query = """
            SELECT
                owner,
                index_name,
                table_name,
                num_rows,
                distinct_keys,
                leaf_blocks,
                clustering_factor,
                avg_leaf_blocks_per_key,
                avg_data_blocks_per_key,
                sample_size,
                last_analyzed,
                stale_stats,
                stattype_locked
            FROM dba_ind_statistics
            WHERE partitioned = 'NO'
        """

        conditions = []
        bind_params = {}

        if exclude_system:
            placeholders = ", ".join([f":schema{i}" for i in range(len(self.SYSTEM_SCHEMAS))])
            conditions.append(f"owner NOT IN ({placeholders})")
            for i, sys_schema in enumerate(self.SYSTEM_SCHEMAS):
                bind_params[f"schema{i}"] = sys_schema

        if schema:
            conditions.append("owner = :owner")
            bind_params["owner"] = schema.upper()

        if stale_only:
            conditions.append("stale_stats = 'YES'")

        if conditions:
            query += " AND " + " AND ".join(conditions)

        query += " ORDER BY owner, index_name"

        with self.connection_manager.get_connection() as connection:
            cursor = connection.cursor()
            try:
                cursor.execute(query, bind_params)
                columns = [col[0].lower() for col in cursor.description]
                rows = cursor.fetchall()

                statistics = []
                for row in rows:
                    stat = dict(zip(columns, row))
                    stat = self._convert_oracle_types(stat)
                    stat = self._enrich_index_statistics(stat)
                    statistics.append(stat)

                logger.info(f"Fetched {len(statistics)} index statistics")

                return statistics

            finally:
                cursor.close()

    def fetch_statistics_jobs(self) -> List[Dict[str, Any]]:
        """
        Fetch statistics gathering job information.

        Returns:
            List of statistics-related scheduler jobs
        """
        query = """
            SELECT
                job_name,
                job_type,
                job_action,
                enabled,
                state,
                last_start_date,
                last_run_duration,
                next_run_date,
                run_count,
                failure_count,
                job_priority
            FROM dba_scheduler_jobs
            WHERE job_name LIKE '%STATS%'
               OR job_name LIKE '%GATHER%'
            ORDER BY job_name
        """

        with self.connection_manager.get_connection() as connection:
            cursor = connection.cursor()
            try:
                cursor.execute(query)
                columns = [col[0].lower() for col in cursor.description]
                rows = cursor.fetchall()

                jobs = []
                for row in rows:
                    job = dict(zip(columns, row))
                    job = self._convert_oracle_types(job)
                    jobs.append(job)

                logger.info(f"Fetched {len(jobs)} statistics gathering jobs")

                return jobs

            finally:
                cursor.close()

    def fetch_autotask_client_status(self) -> List[Dict[str, Any]]:
        """
        Fetch auto statistics collection task status.

        Returns:
            List of autotask client information
        """
        query = """
            SELECT
                client_name,
                status,
                consumer_group,
                window_group,
                attributes
            FROM dba_autotask_client
            WHERE client_name = 'auto optimizer stats collection'
        """

        with self.connection_manager.get_connection() as connection:
            cursor = connection.cursor()
            try:
                cursor.execute(query)
                columns = [col[0].lower() for col in cursor.description]
                rows = cursor.fetchall()

                clients = []
                for row in rows:
                    client = dict(zip(columns, row))
                    client = self._convert_oracle_types(client)
                    clients.append(client)

                return clients

            finally:
                cursor.close()

    def check_statistics_health(
        self, schema: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Perform comprehensive statistics health check.

        Args:
            schema: Specific schema to check (None for all)

        Returns:
            Dictionary with health metrics
        """
        # Fetch all table statistics
        tables = self.fetch_table_statistics(schema=schema, exclude_system=True)

        # Fetch all index statistics
        indexes = self.fetch_index_statistics(schema=schema, exclude_system=True)

        # Categorize issues
        stale_tables = [t for t in tables if t.get("is_stale")]
        never_analyzed_tables = [t for t in tables if t.get("never_analyzed")]
        old_stats_tables = [t for t in tables if t.get("is_old")]
        low_sample_tables = [t for t in tables if t.get("low_sample_size")]

        stale_indexes = [i for i in indexes if i.get("is_stale")]
        never_analyzed_indexes = [i for i in indexes if i.get("never_analyzed")]

        # Calculate health score (0-100)
        health_score = self._calculate_health_score(
            total_tables=len(tables),
            stale_tables=len(stale_tables),
            never_analyzed_tables=len(never_analyzed_tables),
            old_stats_tables=len(old_stats_tables),
            total_indexes=len(indexes),
            stale_indexes=len(stale_indexes),
        )

        return {
            "health_score": health_score,
            "health_status": self._get_health_status(health_score),
            "total_tables": len(tables),
            "total_indexes": len(indexes),
            "stale_tables": len(stale_tables),
            "stale_indexes": len(stale_indexes),
            "never_analyzed_tables": len(never_analyzed_tables),
            "never_analyzed_indexes": len(never_analyzed_indexes),
            "old_statistics_tables": len(old_stats_tables),
            "low_sample_size_tables": len(low_sample_tables),
            "tables_needing_attention": stale_tables + never_analyzed_tables,
            "indexes_needing_attention": stale_indexes + never_analyzed_indexes,
        }

    def _enrich_table_statistics(self, stat: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add calculated fields to table statistics.

        Args:
            stat: Table statistics dictionary

        Returns:
            Enriched statistics
        """
        last_analyzed = stat.get("last_analyzed")

        # Check if never analyzed
        stat["never_analyzed"] = last_analyzed is None

        # Calculate age in days
        if last_analyzed:
            try:
                if isinstance(last_analyzed, str):
                    analyzed_date = datetime.fromisoformat(last_analyzed)
                else:
                    analyzed_date = last_analyzed
                age_days = (datetime.now() - analyzed_date).days
                stat["stats_age_days"] = age_days
                stat["is_old"] = age_days > 30
            except Exception:
                stat["stats_age_days"] = None
                stat["is_old"] = False
        else:
            stat["stats_age_days"] = None
            stat["is_old"] = False

        # Check if stale
        stat["is_stale"] = stat.get("stale_stats") == "YES"

        # Check sample size
        num_rows = stat.get("num_rows") or 0
        sample_size = stat.get("sample_size") or 0
        if num_rows > 0 and sample_size > 0:
            sample_percentage = (sample_size / num_rows) * 100
            stat["sample_percentage"] = round(sample_percentage, 2)
            stat["low_sample_size"] = sample_percentage < 10  # Less than 10%
        else:
            stat["sample_percentage"] = None
            stat["low_sample_size"] = False

        # Calculate priority
        stat["priority"] = self._calculate_priority(stat, "table")

        return stat

    def _enrich_index_statistics(self, stat: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add calculated fields to index statistics.

        Args:
            stat: Index statistics dictionary

        Returns:
            Enriched statistics
        """
        last_analyzed = stat.get("last_analyzed")

        # Check if never analyzed
        stat["never_analyzed"] = last_analyzed is None

        # Calculate age in days
        if last_analyzed:
            try:
                if isinstance(last_analyzed, str):
                    analyzed_date = datetime.fromisoformat(last_analyzed)
                else:
                    analyzed_date = last_analyzed
                age_days = (datetime.now() - analyzed_date).days
                stat["stats_age_days"] = age_days
                stat["is_old"] = age_days > 30
            except Exception:
                stat["stats_age_days"] = None
                stat["is_old"] = False
        else:
            stat["stats_age_days"] = None
            stat["is_old"] = False

        # Check if stale
        stat["is_stale"] = stat.get("stale_stats") == "YES"

        # Calculate priority
        stat["priority"] = self._calculate_priority(stat, "index")

        return stat

    def _calculate_priority(self, stat: Dict[str, Any], object_type: str) -> str:
        """
        Calculate priority for statistics gathering.

        Args:
            stat: Statistics dictionary
            object_type: "table" or "index"

        Returns:
            Priority level (critical, high, medium, low)
        """
        if stat.get("never_analyzed"):
            return "critical"

        if stat.get("is_stale"):
            return "high"

        if stat.get("is_old") and stat.get("stats_age_days", 0) > 90:
            return "high"

        if stat.get("is_old"):
            return "medium"

        if stat.get("low_sample_size"):
            return "medium"

        return "low"

    def _calculate_health_score(
        self,
        total_tables: int,
        stale_tables: int,
        never_analyzed_tables: int,
        old_stats_tables: int,
        total_indexes: int,
        stale_indexes: int,
    ) -> float:
        """
        Calculate overall statistics health score.

        Args:
            Various statistics counts

        Returns:
            Health score (0-100)
        """
        if total_tables == 0:
            return 100.0

        # Weighted scoring
        stale_penalty = (stale_tables / total_tables) * 40 if total_tables > 0 else 0
        never_analyzed_penalty = (never_analyzed_tables / total_tables) * 30 if total_tables > 0 else 0
        old_stats_penalty = (old_stats_tables / total_tables) * 20 if total_tables > 0 else 0
        stale_index_penalty = (stale_indexes / total_indexes) * 10 if total_indexes > 0 else 0

        score = 100 - (stale_penalty + never_analyzed_penalty + old_stats_penalty + stale_index_penalty)

        return max(0.0, round(score, 2))

    def _get_health_status(self, score: float) -> str:
        """
        Get health status from score.

        Args:
            score: Health score

        Returns:
            Status string
        """
        if score >= 90:
            return "excellent"
        elif score >= 75:
            return "good"
        elif score >= 50:
            return "fair"
        elif score >= 25:
            return "poor"
        else:
            return "critical"

    def _convert_oracle_types(self, row_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert Oracle-specific types to Python types.

        Args:
            row_dict: Dictionary with Oracle types

        Returns:
            Dictionary with converted types
        """
        converted = {}
        for key, value in row_dict.items():
            # Handle LOB objects
            if hasattr(value, "read"):
                try:
                    converted[key] = value.read()
                except Exception as e:
                    logger.warning(f"Failed to read LOB for {key}: {e}")
                    converted[key] = None
            # Handle datetime objects
            elif isinstance(value, datetime):
                converted[key] = value.isoformat()
            # Handle None/NULL
            elif value is None:
                converted[key] = None
            else:
                converted[key] = value

        return converted
