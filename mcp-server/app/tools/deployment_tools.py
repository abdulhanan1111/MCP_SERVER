"""Deployment Tools — exposed as MCP tools for Claude. Integrates with AWS MCP."""

from fastmcp import FastMCP
from app.services.deployment_service import DeploymentService


def register_deployment_tools(mcp: FastMCP):

    @mcp.tool(
        name="run_validations",
        description="Run pre-deployment validations (tests, linting, type checks)."
    )
    def run_validations(plan_id: str) -> dict:
        """Runs all validations and returns pass/fail status."""
        return DeploymentService.run_validations(plan_id)

    @mcp.tool(
        name="gate_deployment",
        description="Check deployment gate — verify all conditions are met before deploying."
    )
    def gate_deployment(plan_id: str) -> dict:
        """Returns whether deployment is allowed based on validation and approval status."""
        return DeploymentService.gate_deployment(plan_id)

    @mcp.tool(
        name="deploy",
        description="Deploy the approved and validated changes. Integrates with AWS MCP for actual deployment."
    )
    def deploy(plan_id: str) -> dict:
        """Triggers deployment via AWS MCP integration. MUST only be called after gate_deployment passes."""
        return DeploymentService.deploy(plan_id)

    @mcp.tool(
        name="verify_deployment",
        description="Verify that a deployment is healthy and functioning correctly."
    )
    def verify_deployment(plan_id: str) -> dict:
        """Runs post-deployment health checks and returns verification status."""
        return DeploymentService.verify_deployment(plan_id)

    @mcp.tool(
        name="promote_or_stop",
        description="Promote a verified deployment to stable, or stop/rollback a failed one."
    )
    def promote_or_stop(plan_id: str, action: str) -> dict:
        """Action must be 'promote' or 'stop'. Promotes to stable or triggers rollback."""
        return DeploymentService.promote_or_stop_raw(plan_id, action)
