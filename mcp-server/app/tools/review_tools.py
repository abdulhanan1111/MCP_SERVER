"""Review Tools — exposed as MCP tools for Claude."""

from fastmcp import FastMCP
from app.services.review_service import ReviewService


def register_review_tools(mcp: FastMCP):

    @mcp.tool(
        name="prepare_change_summary",
        description="Prepare a human-readable summary of all planned changes."
    )
    def prepare_change_summary(plan_id: str) -> dict:
        """Returns a summary string describing the change plan."""
        return ReviewService.prepare_change_summary(plan_id)

    @mcp.tool(
        name="prepare_diff_review",
        description="Generate a diff review showing affected files, impact analysis, and assumptions."
    )
    def prepare_diff_review(plan_id: str) -> dict:
        """Returns diff, files list, impact assessment, and assumptions."""
        return ReviewService.prepare_diff_review(plan_id)

    @mcp.tool(
        name="detect_sensitive_change",
        description="Detect if a diff contains sensitive changes (secrets, credentials, etc.)."
    )
    def detect_sensitive_change(diff: str) -> dict:
        """Scans the diff for sensitive patterns and returns findings."""
        return ReviewService.detect_sensitive_change(diff)

    @mcp.tool(
        name="request_approval",
        description="Request human approval before applying changes. NEVER skip this step."
    )
    def request_approval(plan_id: str) -> dict:
        """Requests approval for the plan. Returns approved status and optional feedback."""
        return ReviewService.request_approval(plan_id)
