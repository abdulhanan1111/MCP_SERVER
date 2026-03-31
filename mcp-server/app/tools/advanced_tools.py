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
