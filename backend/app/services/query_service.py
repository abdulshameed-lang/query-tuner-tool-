"""Query analysis service with ranking and filtering logic."""

from typing import List, Dict, Any, Optional
import logging

from app.core.oracle.queries import QueryFetcher
from app.core.oracle.connection import get_connection_manager
from app.schemas.query import QueryFilters, QuerySort, PaginationParams

logger = logging.getLogger(__name__)


class QueryService:
    """Service for query analysis and ranking."""

    def __init__(self):
        """Initialize QueryService."""
        self.connection_manager = get_connection_manager()
        self.query_fetcher = QueryFetcher(self.connection_manager)

    def get_queries(
        self,
        filters: Optional[QueryFilters] = None,
        sort: Optional[QuerySort] = None,
        pagination: Optional[PaginationParams] = None,
    ) -> tuple[List[Dict[str, Any]], int]:
        """
        Get queries with filtering, sorting, and pagination.

        Args:
            filters: Query filters
            sort: Sort parameters
            pagination: Pagination parameters

        Returns:
            Tuple of (query list, total count)
        """
        # Set defaults
        if filters is None:
            filters = QueryFilters()
        if sort is None:
            sort = QuerySort()
        if pagination is None:
            pagination = PaginationParams()

        # Map sort field to Oracle column
        sort_column_map = {
            "elapsed_time": "elapsed_time",
            "cpu_time": "cpu_time",
            "executions": "executions",
            "buffer_gets": "buffer_gets",
            "disk_reads": "disk_reads",
            "rows_processed": "rows_processed",
            "avg_elapsed_time": "elapsed_time",  # Will calculate in query
        }
        order_by = sort_column_map.get(sort.sort_by, "elapsed_time")

        # Fetch more than needed for pagination (simple approach)
        # In production, you'd implement proper offset/limit in SQL
        top_n = pagination.page * pagination.page_size + 50

        # Fetch queries
        queries = self.query_fetcher.fetch_top_queries(
            top_n=min(top_n, 1000),  # Cap at 1000
            min_elapsed_time=filters.min_elapsed_time,
            min_executions=filters.min_executions,
            exclude_system_schemas=filters.exclude_system_schemas,
            order_by=order_by,
        )

        # Apply additional filters
        if filters.schema:
            queries = [q for q in queries if q.get('parsing_schema_name') == filters.schema]

        if filters.sql_text_contains:
            search_term = filters.sql_text_contains.lower()
            queries = [q for q in queries if search_term in q.get('sql_text', '').lower()]

        # Calculate performance impact score
        queries = [self._calculate_impact_score(q) for q in queries]

        # Apply sorting
        reverse = sort.order == "desc"
        if sort.sort_by in queries[0] if queries else {}:
            queries.sort(key=lambda x: x.get(sort.sort_by, 0) or 0, reverse=reverse)

        # Get total count before pagination
        total_count = len(queries)

        # Apply pagination
        start_idx = pagination.offset
        end_idx = start_idx + pagination.page_size
        paginated_queries = queries[start_idx:end_idx]

        logger.info(
            f"Fetched {len(paginated_queries)} queries "
            f"(page {pagination.page}, total {total_count})"
        )

        return paginated_queries, total_count

    def get_query_by_id(self, sql_id: str) -> Optional[Dict[str, Any]]:
        """
        Get query details by SQL_ID.

        Args:
            sql_id: Oracle SQL_ID

        Returns:
            Query dictionary or None if not found
        """
        query = self.query_fetcher.fetch_query_by_sql_id(sql_id)
        if query:
            query = self._calculate_impact_score(query)
            # Get additional statistics
            stats = self.query_fetcher.get_query_statistics(sql_id)
            return {"query": query, "statistics": stats}
        return None

    def _calculate_impact_score(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate performance impact score for a query.

        Score is based on:
        - Elapsed time (50% weight)
        - CPU time (20% weight)
        - Buffer gets (15% weight)
        - Disk reads (15% weight)

        Args:
            query: Query dictionary

        Returns:
            Query dictionary with added impact_score field
        """
        try:
            elapsed = float(query.get('elapsed_time', 0))
            cpu = float(query.get('cpu_time', 0))
            buffer_gets = float(query.get('buffer_gets', 0))
            disk_reads = float(query.get('disk_reads', 0))

            # Normalize values (simple approach)
            # In production, you'd use percentile-based normalization
            elapsed_score = min(elapsed / 1_000_000_000, 100) * 0.5  # Cap at 1 second
            cpu_score = min(cpu / 1_000_000_000, 100) * 0.2
            buffer_score = min(buffer_gets / 1_000_000, 100) * 0.15
            disk_score = min(disk_reads / 100_000, 100) * 0.15

            impact_score = elapsed_score + cpu_score + buffer_score + disk_score

            query['impact_score'] = round(impact_score, 2)
            query['needs_tuning'] = impact_score > 50

        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to calculate impact score: {e}")
            query['impact_score'] = 0
            query['needs_tuning'] = False

        return query

    def get_query_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics for all queries.

        Returns:
            Dictionary with summary statistics
        """
        queries = self.query_fetcher.fetch_top_queries(top_n=1000)

        if not queries:
            return {
                "total_queries": 0,
                "total_executions": 0,
                "total_elapsed_time": 0,
                "avg_elapsed_time": 0,
                "queries_needing_tuning": 0,
            }

        total_executions = sum(q.get('executions', 0) for q in queries)
        total_elapsed = sum(q.get('elapsed_time', 0) for q in queries)
        avg_elapsed = total_elapsed / len(queries) if queries else 0

        # Calculate queries needing tuning
        queries_with_score = [self._calculate_impact_score(q) for q in queries]
        queries_needing_tuning = sum(1 for q in queries_with_score if q.get('needs_tuning'))

        return {
            "total_queries": len(queries),
            "total_executions": total_executions,
            "total_elapsed_time": total_elapsed,
            "avg_elapsed_time": avg_elapsed,
            "queries_needing_tuning": queries_needing_tuning,
        }
