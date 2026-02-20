# Calendar DingTalk MCP Server

MCP server for DingTalk CalDAV Calendar - provides 8 MCP tools for calendar operations.

## Quick Start

```bash
# Install dependencies
cd mcp.version && uv sync

# Configure environment
cp .env.example .env
# Edit .env with your DingTalk CalDAV credentials

# Run MCP server
uv run dingtalk-mcp-server
```

## MCP Tools

- `list_calendars` - List all calendars
- `get_events` - Get events from a calendar
- `create_event` - Create a new event
- `update_event` - Update an existing event
- `delete_event` - Delete an event
- `get_todos` - Get todo items from a calendar
- `create_todo` - Create a new todo
- `delete_todo` - Delete a todo

## Configuration

Set environment variables:
- `CALDAV_BASE_URL` - DingTalk CalDAV server URL
- `CALDAV_USERNAME` - Your DingTalk username/email
- `CALDAV_PASSWORD` - Your DingTalk password
