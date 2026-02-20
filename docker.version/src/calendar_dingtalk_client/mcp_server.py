"""
MCP Server Implementation
"""
from typing import Optional, Dict, Any
from datetime import datetime
from mcp.server.fastmcp import FastMCP
from .config import get_config
from .caldav.client import CalDAVClient

mcp = FastMCP("dingtalk-caldav-calendar")
_client_cache: Optional[CalDAVClient] = None

async def get_caldav_client() -> CalDAVClient:
    global _client_cache
    if _client_cache is None:
        config = get_config()
        config.validate()
        _client_cache = CalDAVClient(config.caldav_base_url, config.caldav_username, config.caldav_password)
        await _client_cache.__aenter__()
    return _client_cache

async def find_calendar_url(calendar_name: str) -> str:
    client = await get_caldav_client()
    calendars = await client.list_calendars()
    for calendar in calendars:
        if calendar["displayname"] == calendar_name or calendar["name"] == calendar_name:
            return calendar["url"]
    available = ", ".join([c["displayname"] for c in calendars])
    raise ValueError(f"Calendar '{calendar_name}' not found. Available: {available}")

@mcp.tool()
async def list_calendars() -> str:
    """List all calendars"""
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
async def create_event(calendar_name: str, summary: str, start: str, end: str, location: Optional[str] = None, description: Optional[str] = None) -> str:
    """Create new event"""
    client = await get_caldav_client()
    calendar_url = await find_calendar_url(calendar_name)
    
    import uuid
    uid = str(uuid.uuid4())
    
    from icalendar import Calendar, Event as IEvent
    cal = Calendar()
    cal.add('prodid', '-//DingTalk Calendar Client//EN')
    cal.add('version', '2.0')
    
    ie = IEvent()
    ie.add('uid', uid)
    ie.add('summary', summary)
    ie.add('dtstart', datetime.fromisoformat(start.replace('Z', '+00:00')))
    ie.add('dtend', datetime.fromisoformat(end.replace('Z', '+00:00')))
    if location:
        ie.add('location', location)
    if description:
        ie.add('description', description)
    
    cal.add_component(ie)
    ical_data = cal.to_ical().decode('utf-8')
    
    event_url = await client.create_object(calendar_url, uid, ical_data)
    return f"Event created successfully. URL: {event_url}, UID: {uid}"

def main():
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
