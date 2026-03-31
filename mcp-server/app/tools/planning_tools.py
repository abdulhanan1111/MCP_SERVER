"""Planning Tools — exposed as MCP tools for Claude."""

from fastmcp import FastMCP
from app.services.planning_service import PlanningService


def register_planning_tools(mcp: FastMCP):

    @mcp.tool(
        name="identify_impacted_components",
        description="Identify which codebase components are impacted by a requirement."
    )
    def identify_impacted_components(requirement_id: str) -> dict:
        """Returns a list of impacted components for the given requirement."""
        return PlanningService.identify_impacted_components(requirement_id)

    @mcp.tool(
        name="create_change_plan",
        description="Create a step-by-step change plan for implementing a requirement."
    )
    def create_change_plan(requirement_id: str, components: list[str]) -> dict:
        """Generates a plan with steps, targeting the specified components."""
        return PlanningService.create_change_plan_raw(requirement_id, components)

    @mcp.tool(
        name="estimate_risk",
        description="Estimate the risk level of a change plan."
    )
    def estimate_risk(plan_id: str) -> dict:
        """Returns risk level and contributing factors for the plan."""
        return PlanningService.estimate_risk(plan_id)

    @mcp.tool(
        name="validate_preconditions",
        description="Validate that all preconditions are met before executing a plan."
    )
    def validate_preconditions(plan_id: str) -> dict:
        """Returns whether preconditions are valid and details."""
        return PlanningService.validate_preconditions(plan_id)
