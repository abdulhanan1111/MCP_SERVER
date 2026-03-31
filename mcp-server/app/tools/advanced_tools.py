"""Advanced Tools — exposed as MCP tools for Claude."""

from fastmcp import FastMCP
from app.services.advanced_service import AdvancedService


def register_advanced_tools(mcp: FastMCP):

    @mcp.tool(
        name="map_business_context",
        description="Map a requirement to its business context and domain implications."
    )
    def map_business_context(requirement_id: str) -> dict:
        """Returns business context mapping for the requirement."""
        return AdvancedService.map_business_context(requirement_id)

    @mcp.tool(
        name="generate_tests",
        description="Auto-generate test cases for a change plan."
    )
    def generate_tests(plan_id: str) -> dict:
        """Generates test file names and test stubs for the plan."""
        return AdvancedService.generate_tests(plan_id)

    @mcp.tool(
        name="enforce_policy",
        description="Enforce organizational policies and coding standards on a change plan."
    )
    def enforce_policy(plan_id: str) -> dict:
        """Checks the plan against org policies and returns pass/fail."""
        return AdvancedService.enforce_policy(plan_id)

    @mcp.tool(
        name="request_project_snapshot",
        description="Request the client to generate a project file list for a local path."
    )
    def request_project_snapshot(requirement_id: str, root_path: str) -> dict:
        """Returns commands for the client to run locally and a snapshot ID."""
        return AdvancedService.request_project_snapshot(requirement_id, root_path)

    @mcp.tool(
        name="submit_project_snapshot",
        description="Submit a client-generated project file list for analysis."
    )
    def submit_project_snapshot(snapshot_id: str, file_list: list[str]) -> dict:
        """Stores the snapshot and enriches the requirement via LLM analysis."""
        return AdvancedService.submit_project_snapshot(snapshot_id, file_list)
