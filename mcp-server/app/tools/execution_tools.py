"""Execution Tools — exposed as MCP tools for Claude."""

from fastmcp import FastMCP
from app.services.execution_service import ExecutionService


def register_execution_tools(mcp: FastMCP):

    @mcp.tool(
        name="apply_change",
        description="Apply an approved change plan. MUST only be called after approval."
    )
    def apply_change(plan_id: str) -> dict:
        """Applies the change plan to the codebase. Requires prior approval."""
        return ExecutionService.apply_change(plan_id)

    @mcp.tool(
        name="create_rollback",
        description="Create a rollback snapshot before applying changes. ALWAYS call before apply_change."
    )
    def create_rollback(plan_id: str) -> dict:
        """Creates and stores a rollback point, returning a rollback_id."""
        return ExecutionService.create_rollback(plan_id)

    @mcp.tool(
        name="rollback",
        description="Execute a rollback to undo applied changes."
    )
    def rollback(rollback_id: str) -> dict:
        """Rolls back the codebase to the state captured by the rollback_id."""
        return ExecutionService.rollback(rollback_id)

    @mcp.tool(
        name="audit_log",
        description="Log an action to the audit trail. ALWAYS call after every significant operation."
    )
    def audit_log(action: str, details: dict) -> dict:
        """Records an audit log entry with the action name and details."""
        return ExecutionService.audit_log_raw(action, details)
