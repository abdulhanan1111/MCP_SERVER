"""
Custom MCP Tool Server — Built with FastMCP.

This server exposes all automation tools via the MCP protocol.
Claude Desktop connects to this server and calls tools directly.

Run:
    python server.py
    OR
    fastmcp run server.py:mcp

Configure in Claude Desktop:
    %APPDATA%\\Claude\\claude_desktop_config.json
"""

from fastmcp import FastMCP
from app.config import settings

# --- Initialize the MCP Server ---
mcp = FastMCP(
    name=settings.PROJECT_NAME,
)

# --- Register all tool groups ---
from app.tools.requirement_tools import register_requirement_tools
from app.tools.planning_tools import register_planning_tools
from app.tools.review_tools import register_review_tools
from app.tools.execution_tools import register_execution_tools
from app.tools.deployment_tools import register_deployment_tools
from app.tools.advanced_tools import register_advanced_tools

register_requirement_tools(mcp)
register_planning_tools(mcp)
register_review_tools(mcp)
register_execution_tools(mcp)
register_deployment_tools(mcp)
register_advanced_tools(mcp)

if __name__ == "__main__":
    mcp.run(transport="stdio")
