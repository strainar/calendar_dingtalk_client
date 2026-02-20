"""
Smoke tests for MCP server
Tests that the MCP server module can be loaded.
"""

import sys
from pathlib import Path

# Add parent project src to path (same logic as mcp_server.py)
_project_src_dir = Path(__file__).resolve().parent.parent.parent / "src"
if str(_project_src_dir) not in sys.path:
    sys.path.insert(0, str(_project_src_dir))


def test_mcp_server_file_parses():
    """Test that mcp_server.py can be parsed without syntax errors"""
    mcp_server_path = (
        Path(__file__).resolve().parent.parent
        / "src"
        / "calendar_dingtalk_mcp"
        / "mcp_server.py"
    )

    with open(mcp_server_path, "r", encoding="utf-8") as f:
        code = f.read()

    compile(code, str(mcp_server_path), "exec")
    assert True


def test_mcp_has_tools_defined():
    """Test that the MCP server has tools defined by checking the source code"""
    mcp_server_path = (
        Path(__file__).resolve().parent.parent
        / "src"
        / "calendar_dingtalk_mcp"
        / "mcp_server.py"
    )

    with open(mcp_server_path, "r", encoding="utf-8") as f:
        code = f.read()

    # Check for the 8 tool function definitions
    expected_tools = [
        "list_calendars",
        "get_events",
        "create_event",
        "update_event",
        "delete_event",
        "get_todos",
        "create_todo",
        "delete_todo",
    ]

    for tool in expected_tools:
        assert f"async def {tool}(" in code, f"Tool {tool} not found in source"

    assert code.count("@mcp.tool()") == 8, (
        f"Expected 8 @mcp.tool() decorators, found {code.count('@mcp.tool()')}"
    )


def test_fastmcp_instance():
    """Test that FastMCP instance is properly configured"""
    mcp_server_path = (
        Path(__file__).resolve().parent.parent
        / "src"
        / "calendar_dingtalk_mcp"
        / "mcp_server.py"
    )

    with open(mcp_server_path, "r", encoding="utf-8") as f:
        code = f.read()

    assert 'FastMCP("dingtalk-caldav-calendar")' in code
    assert 'mcp.run(transport="stdio")' in code


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])
