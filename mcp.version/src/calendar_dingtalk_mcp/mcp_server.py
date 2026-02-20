"""
MCP Server Implementation for DingTalk CalDAV Calendar
8 MCP tools: list_calendars, get_events, create_event, update_event, delete_event, get_todos, create_todo, delete_todo
"""

import os
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# Add parent project's src directory to path to import from calendar_dingtalk_client
# Path: mcp.version/src/calendar_dingtalk_mcp/mcp_server.py
#       mcp.version/ <-- 3 parents up
#       D:\CodeSpaces\calendar_dingtalk_client\  <-- project root (4 parents up)
#       D:\CodeSpaces\calendar_dingtalk_client\src\  <-- add src to path
_project_src_dir = Path(__file__).resolve().parent.parent.parent.parent / "src"
if str(_project_src_dir) not in sys.path:
    sys.path.insert(0, str(_project_src_dir))

# Import from calendar_dingtalk_client (via sys.path)
from calendar_dingtalk_client.caldav.client import CalDAVClient
from calendar_dingtalk_client.icalendar.builder import build_event, build_todo
from calendar_dingtalk_client.icalendar.parser import parse_event, parse_todo

mcp = FastMCP("dingtalk-caldav-calendar")
_client_cache: Optional[CalDAVClient] = None


def load_config(env_path: Optional[str] = None) -> None:
    """Load configuration from environment variables or .env file"""
    if env_path:
        load_dotenv(env_path)
    else:
        # Try to load from default .env in current directory
        load_dotenv()


async def get_caldav_client() -> CalDAVClient:
    """Get or create CalDAV client"""
    global _client_cache
    if _client_cache is None:
        base_url = os.getenv("CALDAV_BASE_URL", "https://calendar.dingtalk.com")
        username = os.getenv("CALDAV_USERNAME")
        password = os.getenv("CALDAV_PASSWORD")

        if not username or not password:
            raise ValueError("CALDAV_USERNAME and CALDAV_PASSWORD must be set")

        _client_cache = CalDAVClient(base_url, username, password)
        await _client_cache.__aenter__()
    return _client_cache


async def find_calendar_url(calendar_name: str) -> str:
    """Find calendar URL by name"""
    client = await get_caldav_client()
    calendars = await client.list_calendars()
    for calendar in calendars:
        if (
            calendar["displayname"] == calendar_name
            or calendar["name"] == calendar_name
        ):
            return calendar["url"]
    available = ", ".join([c["displayname"] for c in calendars])
    raise ValueError(f"Calendar '{calendar_name}' not found. Available: {available}")


async def find_event_url(calendar_name: str, uid: str) -> tuple[str, str]:
    """Find event/todo URL and etag by UID"""
    client = await get_caldav_client()
    calendar_url = await find_calendar_url(calendar_name)

    # Get all objects in the calendar
    xml = (
        '<?xml version="1.0" encoding="utf-8" ?>'
        '<D:propfind xmlns:D="DAV:" xmlns:C="urn:ietf:params:xml:ns:caldav">'
        "<D:prop><D:resourcetype/><D:getcontenttype/><D:getetag/></D:prop>"
        "</D:propfind>"
    )

    from lxml import etree

    response = await client._client.request(
        "PROPFIND",
        calendar_url,
        content=xml,
        headers={
            "Content-Type": "application/xml; charset=utf-8",
            "Depth": "1",
        },
    )

    root = etree.fromstring(response.text.encode())
    ns = {"D": "DAV:", "C": "urn:ietf:params:xml:ns:caldav"}

    for response_elem in root.findall(".//D:response", ns):
        href_elem = response_elem.find("D:href", ns)
        if href_elem is None or href_elem.text is None:
            continue

        href = href_elem.text
        if href.endswith("/"):
            continue

        from urllib.parse import urlparse

        parsed = urlparse(client.base_url)
        object_url = f"{parsed.scheme}://{parsed.netloc}{href}"

        # Get the actual iCalendar data
        try:
            ical_data, etag = await client.get_object(object_url)

            # Check if this is the UID we're looking for
            event_data = parse_event(ical_data)
            if event_data.get("uid") == uid:
                return object_url, etag

            todo_data = parse_todo(ical_data)
            if todo_data.get("uid") == uid:
                return object_url, etag
        except Exception:
            continue

    raise ValueError(f"Object with UID '{uid}' not found in calendar '{calendar_name}'")


# ============================================================
# MCP Tools
# ============================================================


@mcp.tool()
async def list_calendars() -> str:
    """
    List all calendars available on the CalDAV server.

    Returns:
        Formatted list of calendars with their names and URLs
    """
    client = await get_caldav_client()
    calendars = await client.list_calendars()

    if not calendars:
        return "No calendars found"

    result = "## Available Calendars\n\n"
    for i, cal in enumerate(calendars, 1):
        result += f"{i}. {cal['displayname']}\n"
        result += f"   URL: {cal['url']}\n\n"
    return result


@mcp.tool()
async def get_events(
    calendar_name: str, start: Optional[str] = None, end: Optional[str] = None
) -> str:
    """
    Get events from a specific calendar.

    Args:
        calendar_name: Name of the calendar (e.g., "Calendar", "工作日历")
        start: Start date/time in ISO format (optional, e.g., "2024-01-01T00:00:00Z")
        end: End date/time in ISO format (optional, e.g., "2024-12-31T23:59:59Z")

    Returns:
        Formatted list of events with their details
    """
    client = await get_caldav_client()
    calendar_url = await find_calendar_url(calendar_name)

    # Parse dates if provided
    start_dt = None
    end_dt = None
    if start:
        start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
    if end:
        end_dt = datetime.fromisoformat(end.replace("Z", "+00:00"))

    events = await client.get_calendar_events(calendar_url, start_dt, end_dt)

    if not events:
        return f"No events found in calendar '{calendar_name}'"

    result = f"## Events in '{calendar_name}'\n\n"
    for i, evt in enumerate(events, 1):
        result += f"{i}. {evt['summary']}\n"
        result += f"   UID: {evt['uid']}\n"
        if evt.get("dtstart"):
            result += f"   Start: {evt['dtstart']}\n"
        if evt.get("dtend"):
            result += f"   End: {evt['dtend']}\n"
        if evt.get("location"):
            result += f"   Location: {evt['location']}\n"
        if evt.get("description"):
            desc = (
                evt["description"][:100] + "..."
                if len(evt["description"]) > 100
                else evt["description"]
            )
            result += f"   Description: {desc}\n"
        result += "\n"
    return result


@mcp.tool()
async def create_event(
    calendar_name: str,
    summary: str,
    start: str,
    end: str,
    location: Optional[str] = None,
    description: Optional[str] = None,
) -> str:
    """
    Create a new event in a calendar.

    Args:
        calendar_name: Name of the calendar
        summary: Event title/summary
        start: Start date/time in ISO format (e.g., "2024-06-15T10:00:00Z")
        end: End date/time in ISO format (e.g., "2024-06-15T11:00:00Z")
        location: Optional location (e.g., "Conference Room A")
        description: Optional description

    Returns:
        Success message with event UID
    """
    client = await get_caldav_client()
    calendar_url = await find_calendar_url(calendar_name)

    uid = str(uuid.uuid4())

    # Build iCalendar data
    event = {
        "uid": uid,
        "summary": summary,
        "dtstart": datetime.fromisoformat(start.replace("Z", "+00:00")),
        "dtend": datetime.fromisoformat(end.replace("Z", "+00:00")),
    }
    if location:
        event["location"] = location
    if description:
        event["description"] = description

    ical_data = build_event(event)

    event_url = await client.create_object(calendar_url, uid, ical_data.decode("utf-8"))
    return f"Event created successfully.\n- UID: {uid}\n- URL: {event_url}\n- Summary: {summary}\n- Start: {start}\n- End: {end}"


@mcp.tool()
async def update_event(
    calendar_name: str,
    uid: str,
    summary: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    location: Optional[str] = None,
    description: Optional[str] = None,
) -> str:
    """
    Update an existing event in a calendar.

    Args:
        calendar_name: Name of the calendar
        uid: UID of the event to update
        summary: New summary/title (optional)
        start: New start date/time in ISO format (optional)
        end: New end date/time in ISO format (optional)
        location: New location (optional)
        description: New description (optional)

    Returns:
        Success message
    """
    client = await get_caldav_client()
    calendar_url = await find_calendar_url(calendar_name)
    event_url, etag = await find_event_url(calendar_name, uid)

    # Get existing event data
    ical_data, _ = await client.get_object(event_url)
    existing_event = parse_event(ical_data)

    if not existing_event:
        raise ValueError(f"Event with UID '{uid}' not found")

    # Build updated event
    updated_event = {
        "uid": uid,
        "summary": summary
        if summary is not None
        else existing_event.get("summary", ""),
        "dtstart": datetime.fromisoformat(start.replace("Z", "+00:00"))
        if start
        else existing_event.get("dtstart"),
        "dtend": datetime.fromisoformat(end.replace("Z", "+00:00"))
        if end
        else existing_event.get("dtend"),
    }
    if location is not None:
        updated_event["location"] = location
    else:
        updated_event["location"] = existing_event.get("location", "")

    if description is not None:
        updated_event["description"] = description
    else:
        updated_event["description"] = existing_event.get("description", "")

    ical_data = build_event(updated_event)

    await client.update_object(event_url, ical_data.decode("utf-8"), etag)
    return f"Event updated successfully.\n- UID: {uid}\n- Summary: {updated_event['summary']}"


@mcp.tool()
async def delete_event(calendar_name: str, uid: str) -> str:
    """
    Delete an event from a calendar.

    Args:
        calendar_name: Name of the calendar
        uid: UID of the event to delete

    Returns:
        Success message
    """
    client = await get_caldav_client()
    event_url, etag = await find_event_url(calendar_name, uid)

    await client.delete_object(event_url, etag)
    return f"Event deleted successfully.\n- UID: {uid}\n- Calendar: {calendar_name}"


@mcp.tool()
async def get_todos(
    calendar_name: str, start: Optional[str] = None, end: Optional[str] = None
) -> str:
    """
    Get todo items from a specific calendar.
    This fetches all items and filters for VTODO components.

    Args:
        calendar_name: Name of the calendar
        start: Start date/time in ISO format (optional)
        end: End date/time in ISO format (optional)

    Returns:
        Formatted list of todo items
    """
    client = await get_caldav_client()
    calendar_url = await find_calendar_url(calendar_name)

    # Get all events (we'll filter for VTODO manually)
    events = await client.get_calendar_events(calendar_url)

    # Filter for VTODO items by fetching content type
    todos = []

    # Get all calendar objects to check content type
    xml = (
        '<?xml version="1.0" encoding="utf-8" ?>'
        '<D:propfind xmlns:D="DAV:" xmlns:C="urn:ietf:params:xml:ns:caldav">'
        "<D:prop><D:resourcetype/><D:getcontenttype/><D:getetag/></D:prop>"
        "</D:propfind>"
    )

    from lxml import etree

    response = await client._client.request(
        "PROPFIND",
        calendar_url,
        content=xml,
        headers={
            "Content-Type": "application/xml; charset=utf-8",
            "Depth": "1",
        },
    )

    root = etree.fromstring(response.text.encode())
    ns = {"D": "DAV:", "C": "urn:ietf:params:xml:ns:caldav"}

    for response_elem in root.findall(".//D:response", ns):
        href_elem = response_elem.find("D:href", ns)
        if href_elem is None or href_elem.text is None:
            continue

        href = href_elem.text
        if href.endswith("/"):
            continue

        # Check content type
        ok_propstat = None
        for propstat in response_elem.findall("D:propstat", ns):
            status = propstat.find("D:status", ns)
            if status is not None and "200" in status.text:
                ok_propstat = propstat
                break

        if ok_propstat is None:
            continue

        prop = ok_propstat.find("D:prop", ns)
        if prop is None:
            continue

        contenttype_elem = prop.find("D:getcontenttype", ns)
        if contenttype_elem is None or contenttype_elem.text is None:
            continue

        # Filter for VTODO
        if "vtodo" not in contenttype_elem.text.lower():
            continue

        # Fetch the todo data
        from urllib.parse import urlparse

        parsed = urlparse(client.base_url)
        todo_url = f"{parsed.scheme}://{parsed.netloc}{href}"

        try:
            ical_data, etag = await client.get_object(todo_url)
            todo_data = parse_todo(ical_data)

            if todo_data:
                todo_data["url"] = todo_url
                todo_data["etag"] = etag
                todos.append(todo_data)
        except Exception:
            continue

    if not todos:
        return f"No todos found in calendar '{calendar_name}'"

    result = f"## Todos in '{calendar_name}'\n\n"
    for i, todo in enumerate(todos, 1):
        result += f"{i}. {todo['summary']}\n"
        result += f"   UID: {todo['uid']}\n"
        result += f"   Status: {todo.get('status', 'NEEDS-ACTION')}\n"
        if todo.get("due"):
            result += f"   Due: {todo['due']}\n"
        if todo.get("priority"):
            result += f"   Priority: {todo['priority']}\n"
        result += "\n"
    return result


@mcp.tool()
async def create_todo(
    calendar_name: str,
    summary: str,
    due: Optional[str] = None,
    priority: Optional[int] = None,
) -> str:
    """
    Create a new todo item in a calendar.

    Args:
        calendar_name: Name of the calendar
        summary: Todo title/summary
        due: Due date/time in ISO format (optional, e.g., "2024-06-15T23:59:59Z")
        priority: Priority (1=highest, 9=lowest, optional)

    Returns:
        Success message with todo UID
    """
    client = await get_caldav_client()
    calendar_url = await find_calendar_url(calendar_name)

    uid = str(uuid.uuid4())

    # Build iCalendar data
    todo = {
        "uid": uid,
        "summary": summary,
        "status": "NEEDS-ACTION",
    }
    if due:
        todo["due"] = datetime.fromisoformat(due.replace("Z", "+00:00"))
    if priority:
        todo["priority"] = priority

    ical_data = build_todo(todo)

    todo_url = await client.create_object(calendar_url, uid, ical_data.decode("utf-8"))
    return f"Todo created successfully.\n- UID: {uid}\n- URL: {todo_url}\n- Summary: {summary}\n- Due: {due or 'Not set'}\n- Priority: {priority or 'Not set'}"


@mcp.tool()
async def delete_todo(calendar_name: str, uid: str) -> str:
    """
    Delete a todo item from a calendar.

    Args:
        calendar_name: Name of the calendar
        uid: UID of the todo to delete

    Returns:
        Success message
    """
    client = await get_caldav_client()
    event_url, etag = await find_event_url(calendar_name, uid)

    await client.delete_object(event_url, etag)
    return f"Todo deleted successfully.\n- UID: {uid}\n- Calendar: {calendar_name}"


def main():
    """Main entry point"""
    # Load configuration from environment
    load_config()
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
