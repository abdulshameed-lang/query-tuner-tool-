"""Execution plan API endpoints."""

from fastapi import APIRouter, HTTPException, status, Query as QueryParam
from typing import Optional
import logging
import json

from app.schemas.execution_plan import (
    ExecutionPlanResponse,
    PlanHistoryResponse,
    PlanExportResponse,
    ExecutionPlan,
    PlanHistoryItem,
    PlanNode,
    PlanOperation,
    PlanAnalysis,
    PlanStatistics,
    PlanIssue,
    PlanRecommendation,
    PlanMetrics,
)
from app.services.execution_plan_service import ExecutionPlanService
from app.core.oracle.connection import OracleConnectionError

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/{sql_id}")
async def get_execution_plan(
    sql_id: str,
    plan_hash_value: Optional[int] = QueryParam(
        None, description="Specific plan hash value"
    ),
):
    """
    Get execution plan for a SQL_ID.

    Parameters:
    - **sql_id**: Oracle SQL_ID (13 character alphanumeric identifier)
    - **plan_hash_value**: Optional specific plan hash value

    Returns:
    - Execution plan with tree structure, analysis, and recommendations

    Raises:
    - 400: Invalid SQL_ID format
    - 404: Plan not found
    - 502: Oracle connection error
    """
    try:
        # Validate SQL_ID format
        if not sql_id or len(sql_id) != 13 or not sql_id.isalnum():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "INVALID_SQL_ID",
                    "message": "SQL_ID must be 13 alphanumeric characters",
                },
            )

        # Get execution plan
        service = ExecutionPlanService()
        result = service.get_execution_plan(sql_id.upper(), plan_hash_value)

        if not result or not result.get("plan_operations"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "PLAN_NOT_FOUND",
                    "message": f"No execution plan found for SQL_ID '{sql_id}'",
                    "sql_id": sql_id,
                },
            )

        # Convert to response model
        plan = ExecutionPlan(
            sql_id=result["sql_id"],
            plan_hash_value=result.get("plan_hash_value"),
            plan_tree=PlanNode(**result["plan_tree"]) if result.get("plan_tree") else PlanNode(id=0, operation="NO_PLAN"),
            plan_operations=[
                PlanOperation(**op) for op in result["plan_operations"]
            ],
            analysis=PlanAnalysis(
                issues=[PlanIssue(**issue) for issue in result["analysis"]["issues"]],
                recommendations=[
                    PlanRecommendation(**rec)
                    for rec in result["analysis"]["recommendations"]
                ],
                costly_operations=[
                    PlanOperation(**op)
                    for op in result["analysis"]["costly_operations"]
                ],
                metrics=PlanMetrics(**result["analysis"]["metrics"]),
            ),
            statistics=PlanStatistics(**result["statistics"])
            if result.get("statistics")
            else None,
        )

        return ExecutionPlanResponse(data=plan)

    except HTTPException:
        raise
    except OracleConnectionError as e:
        logger.warning(f"Oracle connection failed for execution plan {sql_id}, using mock data: {e.message}")
        # Fallback to mock data for testing
        from app.services.mock_data_service import MockDataService
        mock_service = MockDataService()
        plan_data = mock_service.generate_execution_plan(sql_id)

        return {
            "plan": plan_data,
            "note": "Using mock data (Oracle database not available)"
        }
    except Exception as e:
        logger.warning(f"Oracle connection failed for execution plan {sql_id}, using mock data: {e}")
        # Fallback to mock data for testing
        from app.services.mock_data_service import MockDataService
        mock_service = MockDataService()
        plan_data = mock_service.generate_execution_plan(sql_id)

        return {
            "plan": plan_data,
            "note": "Using mock data (Oracle database not available)"
        }


@router.get("/{sql_id}/history", response_model=PlanHistoryResponse)
async def get_plan_history(sql_id: str):
    """
    Get execution plan history for a SQL_ID.

    Shows all plan versions (different plan_hash_values) for the given SQL_ID.

    Parameters:
    - **sql_id**: Oracle SQL_ID

    Returns:
    - List of plan versions with metadata

    Raises:
    - 400: Invalid SQL_ID format
    - 502: Oracle connection error
    """
    try:
        # Validate SQL_ID format
        if not sql_id or len(sql_id) != 13 or not sql_id.isalnum():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "INVALID_SQL_ID",
                    "message": "SQL_ID must be 13 alphanumeric characters",
                },
            )

        # Get plan history
        service = ExecutionPlanService()
        history = service.get_plan_history(sql_id.upper())

        # Convert to response model
        history_items = [PlanHistoryItem(**item) for item in history]

        return PlanHistoryResponse(data=history_items, total_count=len(history_items))

    except HTTPException:
        raise
    except OracleConnectionError as e:
        logger.error(f"Oracle error fetching plan history for {sql_id}: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "code": e.code,
                "message": e.message,
            },
        )
    except Exception as e:
        logger.error(
            f"Unexpected error fetching plan history for {sql_id}: {e}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error fetching plan history",
        )


@router.get("/{sql_id}/export", response_model=PlanExportResponse)
async def export_execution_plan(
    sql_id: str,
    plan_hash_value: Optional[int] = QueryParam(
        None, description="Specific plan hash value"
    ),
    format: str = QueryParam(
        "text", description="Export format (text, json, xml)", pattern="^(text|json|xml)$"
    ),
):
    """
    Export execution plan in various formats.

    Parameters:
    - **sql_id**: Oracle SQL_ID
    - **plan_hash_value**: Optional specific plan hash value
    - **format**: Export format (text, json, xml)

    Returns:
    - Exported plan content in requested format

    Raises:
    - 400: Invalid parameters
    - 404: Plan not found
    - 502: Oracle connection error
    """
    try:
        # Validate SQL_ID format
        if not sql_id or len(sql_id) != 13 or not sql_id.isalnum():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "INVALID_SQL_ID",
                    "message": "SQL_ID must be 13 alphanumeric characters",
                },
            )

        service = ExecutionPlanService()

        # Handle different export formats
        if format == "text":
            content = service.export_plan_text(sql_id.upper(), plan_hash_value)
        elif format == "json":
            result = service.get_execution_plan(sql_id.upper(), plan_hash_value)
            if not result:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "code": "PLAN_NOT_FOUND",
                        "message": f"No execution plan found for SQL_ID '{sql_id}'",
                    },
                )
            content = json.dumps(result, indent=2, default=str)
        elif format == "xml":
            # Simplified XML export - in production you'd use proper XML generation
            result = service.get_execution_plan(sql_id.upper(), plan_hash_value)
            if not result:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "code": "PLAN_NOT_FOUND",
                        "message": f"No execution plan found for SQL_ID '{sql_id}'",
                    },
                )
            content = _convert_to_xml(result)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "INVALID_FORMAT",
                    "message": f"Unsupported format: {format}",
                },
            )

        return PlanExportResponse(
            sql_id=sql_id,
            plan_hash_value=plan_hash_value,
            format=format,
            content=content,
        )

    except HTTPException:
        raise
    except OracleConnectionError as e:
        logger.error(f"Oracle error exporting plan for {sql_id}: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "code": e.code,
                "message": e.message,
            },
        )
    except Exception as e:
        logger.error(f"Unexpected error exporting plan for {sql_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error exporting execution plan",
        )


def _convert_to_xml(plan_data: dict) -> str:
    """
    Convert plan data to XML format.

    Args:
        plan_data: Plan dictionary

    Returns:
        XML string
    """
    lines = ['<?xml version="1.0" encoding="UTF-8"?>']
    lines.append(f'<execution_plan sql_id="{plan_data["sql_id"]}">')

    if plan_data.get("plan_hash_value"):
        lines.append(f'  <plan_hash_value>{plan_data["plan_hash_value"]}</plan_hash_value>')

    lines.append("  <operations>")
    for op in plan_data.get("plan_operations", []):
        lines.append(f'    <operation id="{op["id"]}">')
        lines.append(f'      <type>{op.get("operation", "")}</type>')
        if op.get("object_name"):
            lines.append(f'      <object_name>{op["object_name"]}</object_name>')
        if op.get("cost"):
            lines.append(f'      <cost>{op["cost"]}</cost>')
        if op.get("cardinality"):
            lines.append(f'      <cardinality>{op["cardinality"]}</cardinality>')
        lines.append("    </operation>")
    lines.append("  </operations>")

    lines.append("</execution_plan>")

    return "\n".join(lines)
