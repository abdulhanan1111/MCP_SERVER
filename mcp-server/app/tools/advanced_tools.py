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
    def request_project_snapshot(requirement_id: str, root_path: str, mode: str = "full") -> dict:
        """Returns commands for the client to run locally and a snapshot ID."""
        return AdvancedService.request_project_snapshot(requirement_id, root_path, mode)

    @mcp.tool(
        name="submit_project_snapshot",
        description="Submit a client-generated project file list for analysis."
    )
    def submit_project_snapshot(snapshot_id: str, file_list: list[str]) -> dict:
        """Stores the snapshot and enriches the requirement via LLM analysis."""
        return AdvancedService.submit_project_snapshot(snapshot_id, file_list)

    @mcp.tool(
        name="start_project_interview",
        description="Start a structured client interview to describe a local project without file access."
    )
    def start_project_interview(requirement_id: str) -> dict:
        """Returns a structured questionnaire for the client to answer."""
        return AdvancedService.start_project_interview(requirement_id)

    @mcp.tool(
        name="submit_project_interview",
        description="Submit structured interview answers to enrich requirement analysis."
    )
    def submit_project_interview(requirement_id: str, answers: dict) -> dict:
        """Stores interview answers and enriches the requirement via LLM analysis."""
        return AdvancedService.submit_project_interview(requirement_id, answers)

    @mcp.tool(
        name="request_project_files",
        description="Request only specific file paths from the client for better context."
    )
    def request_project_files(requirement_id: str, reason: str = "", suggested_paths: list[str] | None = None) -> dict:
        """Returns a request for targeted file paths instead of full lists."""
        return AdvancedService.request_project_files(requirement_id, reason, suggested_paths)

    @mcp.tool(
        name="submit_project_files",
        description="Submit targeted file paths from the client."
    )
    def submit_project_files(requirement_id: str, files: list[str]) -> dict:
        """Stores targeted file paths and enriches the requirement via LLM analysis."""
        return AdvancedService.submit_project_files(requirement_id, files)

    @mcp.tool(
        name="request_file_contents",
        description="Request specific file contents (or excerpts) from the client."
    )
    def request_file_contents(requirement_id: str, paths: list[str], reason: str = "") -> dict:
        """Returns a request for specific file contents."""
        return AdvancedService.request_file_contents(requirement_id, paths, reason)

    @mcp.tool(
        name="submit_file_contents",
        description="Submit requested file contents from the client."
    )
    def submit_file_contents(requirement_id: str, files: dict) -> dict:
        """Stores file contents and enriches the requirement via LLM analysis."""
        return AdvancedService.submit_file_contents(requirement_id, files)
