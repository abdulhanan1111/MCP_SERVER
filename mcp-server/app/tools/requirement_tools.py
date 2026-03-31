"""Requirement Tools — exposed as MCP tools for Claude."""

from fastmcp import FastMCP
from app.services.requirement_service import RequirementService


def register_requirement_tools(mcp: FastMCP):

    @mcp.tool(
        name="analyze_requirement",
        description="Analyze a user query and produce a structured requirement JSON."
    )
    def analyze_requirement(query: str) -> dict:
        """Accepts a raw user query and returns a structured requirement with ID, summary, and complexity."""
        result = RequirementService.analyze_requirement_raw(query)
        return result

    @mcp.tool(
        name="generate_clarification_questions",
        description="Generate clarification questions for an unclear requirement."
    )
    def generate_clarification_questions(requirement_id: str) -> dict:
        """Given a requirement ID, returns a list of clarification questions to ask the user."""
        result = RequirementService.generate_clarification_questions(requirement_id)
        return result

    @mcp.tool(
        name="merge_clarifications",
        description="Merge user answers back into the requirement to refine it."
    )
    def merge_clarifications(requirement_id: str, answers: dict) -> dict:
        """Merges clarification answers into the existing requirement."""
        result = RequirementService.merge_clarifications_raw(requirement_id, answers)
        return result

    @mcp.tool(
        name="classify_change_type",
        description="Classify a requirement as feature, bug, schema, or infra change."
    )
    def classify_change_type(requirement_id: str) -> dict:
        """Returns the change type classification for the given requirement."""
        result = RequirementService.classify_change_type(requirement_id)
        return result
