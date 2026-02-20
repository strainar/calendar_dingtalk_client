"""
HTTP 服务器实现
提供完整的 CalDAV REST API
"""

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.openapi.utils import get_openapi
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

from .config import get_config
from .caldav.client import CalDAVClient
from .icalendar.parser import parse_event, parse_todo
from .icalendar.builder import build_event, build_todo
import uvicorn

config = get_config()

app = FastAPI(
    title="钉钉 CalDAV 客户端",
    version="0.1.0",
    description="提供日历同步和管理功能的REST API服务",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

_caldav_client: Optional[CalDAVClient] = None
_calendars_cache: List[Dict[str, Any]] = []


def get_client() -> CalDAVClient:
    """获取CalDAV客户端实例"""
    global _caldav_client
    if _caldav_client is None:
        raise HTTPException(status_code=503, detail="CalDAV client not initialized")
    return _caldav_client


@app.on_event("startup")
async def startup():
    """服务启动时初始化CalDAV客户端"""
    global _caldav_client, _calendars_cache
    try:
        config.validate()
        _caldav_client = CalDAVClient(
            config.caldav_base_url,
            config.caldav_username,
            config.caldav_password,
            config.caldav_timeout,
        )
        await _caldav_client.__aenter__()  # 初始化 HTTP client
        _calendars_cache = await _caldav_client.list_calendars()
        print(f"CalDAV client initialized. Found {len(_calendars_cache)} calendars")
    except Exception as e:
        print(f"Warning: Failed to initialize CalDAV client: {e}")


@app.on_event("shutdown")
async def shutdown():
    """服务关闭时清理"""
    global _caldav_client
    if _caldav_client and _caldav_client._client:
        await _caldav_client._client.aclose()


@app.get("/health", tags=["系统"])
async def health_check():
    """健康检查"""
    return {"status": "healthy", "service": "calendar-dingtalk-client"}


@app.get("/api/calendars", tags=["日历"])
async def list_calendars() -> Dict[str, Any]:
    """获取日历列表"""
    global _calendars_cache
    if not _calendars_cache:
        client = get_client()
        _calendars_cache = await client.list_calendars()
    return {"calendars": _calendars_cache}


@app.get("/api/events", tags=["事件"])
async def list_events(
    start_date: Optional[str] = None, end_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    获取主日历下所有事件

    默认使用第一个日历（primary），支持按日期范围筛选
    """
    client = get_client()
    calendars = await list_calendars()

    if not calendars["calendars"]:
        return {"events": [], "count": 0}

    primary_calendar = calendars["calendars"][0]
    calendar_url = primary_calendar["url"]

    events = await client.get_calendar_events(
        calendar_url, start_date=start_date, end_date=end_date, component_type="VEVENT"
    )

    print(f"[DEBUG] list_events: got {len(events)} events from client")
    if events:
        print(f"[DEBUG] First event: {events[0]}")

    return {"events": events, "count": len(events)}


@app.get("/api/events/{event_uid}", tags=["事件"])
async def get_event(event_uid: str) -> Dict[str, Any]:
    """获取单个事件详情"""
    client = get_client()
    calendars = await list_calendars()

    for calendar in calendars["calendars"]:
        try:
            event_url = f"{calendar['url'].rstrip('/')}/{event_uid}.ics"
            ical_data, etag = await client.get_object(event_url)
            parsed = parse_event(ical_data)
            parsed["url"] = event_url
            parsed["etag"] = etag
            return {"event": parsed}
        except Exception:
            continue

    raise HTTPException(status_code=404, detail=f"Event '{event_uid}' not found")


@app.post("/api/events", tags=["事件"])
async def create_event(
    summary: str,
    dtstart: str,
    dtend: str,
    description: Optional[str] = None,
    location: Optional[str] = None,
    uid: Optional[str] = None,
) -> Dict[str, Any]:
    """
    创建新事件

    默认添加到第一个日历（primary）
    """
    client = get_client()
    calendars = await list_calendars()

    if not calendars["calendars"]:
        raise HTTPException(status_code=404, detail="No calendar available")

    primary_calendar = calendars["calendars"][0]
    calendar_url = primary_calendar["url"]

    event_uid = uid or str(uuid.uuid4())

    event_data = {
        "uid": event_uid,
        "summary": summary,
        "dtstart": datetime.fromisoformat(dtstart.replace("Z", "+00:00")),
        "dtend": datetime.fromisoformat(dtend.replace("Z", "+00:00")),
    }
    if description:
        event_data["description"] = description
    if location:
        event_data["location"] = location

    ical_data = build_event(event_data)
    event_url = await client.create_object(calendar_url, event_uid, ical_data)

    return {
        "success": True,
        "message": "Event created successfully",
        "event": {
            "uid": event_uid,
            "summary": summary,
            "dtstart": dtstart,
            "dtend": dtend,
        },
        "url": event_url,
    }


@app.put("/api/events/{event_uid}", tags=["事件"])
async def update_event(
    event_uid: str,
    summary: Optional[str] = None,
    dtstart: Optional[str] = None,
    dtend: Optional[str] = None,
    description: Optional[str] = None,
    location: Optional[str] = None,
    if_match: Optional[str] = Header(None),
) -> Dict[str, Any]:
    """更新事件"""
    client = get_client()
    calendars = await list_calendars()

    for calendar in calendars["calendars"]:
        try:
            event_url = f"{calendar['url'].rstrip('/')}/{event_uid}.ics"
            old_ical_data, old_etag = await client.get_object(event_url)
            parsed = parse_event(old_ical_data)

            update_data = {
                "uid": event_uid,
                "summary": summary or parsed.get("summary", ""),
                "dtstart": datetime.fromisoformat(dtstart.replace("Z", "+00:00"))
                if dtstart
                else parsed.get("dtstart"),
                "dtend": datetime.fromisoformat(dtend.replace("Z", "+00:00"))
                if dtend
                else parsed.get("dtend"),
            }
            if description is not None:
                update_data["description"] = description
            else:
                update_data["description"] = parsed.get("description", "")
            if location is not None:
                update_data["location"] = location
            else:
                update_data["location"] = parsed.get("location", "")

            etag = if_match or old_etag
            ical_data = build_event(update_data)
            await client.update_object(event_url, ical_data, etag)

            return {
                "success": True,
                "message": "Event updated successfully",
                "event": {"uid": event_uid, "summary": update_data["summary"]},
                "url": event_url,
            }
        except Exception:
            continue

    raise HTTPException(status_code=404, detail=f"Event '{event_uid}' not found")


@app.delete("/api/events/{event_uid}", tags=["事件"])
async def delete_event(event_uid: str, if_match: Optional[str] = Header(None)):
    """删除事件"""
    client = get_client()
    calendars = await list_calendars()

    for calendar in calendars["calendars"]:
        try:
            event_url = f"{calendar['url'].rstrip('/')}/{event_uid}.ics"
            _, etag = await client.get_object(event_url)
            final_etag = if_match or etag

            await client.delete_object(event_url, final_etag)
            return {"success": True, "message": "Event deleted successfully"}
        except Exception:
            continue

    raise HTTPException(status_code=404, detail=f"Event '{event_uid}' not found")


@app.get("/api/todos", tags=["待办"])
async def list_todos() -> Dict[str, Any]:
    """获取待办列表"""
    client = get_client()
    calendars = await list_calendars()

    if not calendars["calendars"]:
        return {"todos": [], "count": 0}

    primary_calendar = calendars["calendars"][0]
    calendar_url = primary_calendar["url"]

    todos = await client.get_calendar_events(calendar_url, component_type="VTODO")

    parsed_todos = []
    for todo in todos:
        try:
            ical_data, etag = await client.get_object(todo["url"])
            parsed = parse_todo(ical_data)
            parsed["url"] = todo["url"]
            parsed["etag"] = etag
            parsed_todos.append(parsed)
        except Exception:
            continue

    return {"todos": parsed_todos, "count": len(parsed_todos)}


@app.get("/api/todos/{todo_uid}", tags=["待办"])
async def get_todo(todo_uid: str) -> Dict[str, Any]:
    """获取待办详情"""
    client = get_client()
    calendars = await list_calendars()

    for calendar in calendars["calendars"]:
        try:
            todo_url = f"{calendar['url'].rstrip('/')}/{todo_uid}.ics"
            ical_data, etag = await client.get_object(todo_url)
            parsed = parse_todo(ical_data)
            parsed["url"] = todo_url
            parsed["etag"] = etag
            return {"todo": parsed}
        except Exception:
            continue

    raise HTTPException(status_code=404, detail=f"Todo '{todo_uid}' not found")


@app.post("/api/todos", tags=["待办"])
async def create_todo(
    summary: str,
    due: Optional[str] = None,
    priority: Optional[int] = None,
    status: Optional[str] = None,
    uid: Optional[str] = None,
) -> Dict[str, Any]:
    """创建待办"""
    client = get_client()
    calendars = await list_calendars()

    if not calendars["calendars"]:
        raise HTTPException(status_code=404, detail="No calendar available")

    primary_calendar = calendars["calendars"][0]
    calendar_url = primary_calendar["url"]

    todo_uid = uid or str(uuid.uuid4())

    todo_data = {"uid": todo_uid, "summary": summary}
    if due:
        todo_data["due"] = datetime.fromisoformat(due.replace("Z", "+00:00"))
    if priority:
        todo_data["priority"] = priority
    if status:
        todo_data["status"] = status

    ical_data = build_todo(todo_data)
    todo_url = await client.create_object(calendar_url, todo_uid, ical_data)

    return {
        "success": True,
        "message": "Todo created successfully",
        "todo": {"uid": todo_uid, "summary": summary},
        "url": todo_url,
    }


@app.put("/api/todos/{todo_uid}", tags=["待办"])
async def update_todo(
    todo_uid: str,
    summary: Optional[str] = None,
    due: Optional[str] = None,
    priority: Optional[int] = None,
    status: Optional[str] = None,
    if_match: Optional[str] = Header(None),
) -> Dict[str, Any]:
    """更新待办"""
    client = get_client()
    calendars = await list_calendars()

    for calendar in calendars["calendars"]:
        try:
            todo_url = f"{calendar['url'].rstrip('/')}/{todo_uid}.ics"
            old_ical_data, old_etag = await client.get_object(todo_url)
            parsed = parse_todo(old_ical_data)

            update_data = {
                "uid": todo_uid,
                "summary": summary or parsed.get("summary", ""),
            }
            if due:
                update_data["due"] = datetime.fromisoformat(due.replace("Z", "+00:00"))
            if priority is not None:
                update_data["priority"] = priority
            if status:
                update_data["status"] = status

            etag = if_match or old_etag
            ical_data = build_todo(update_data)
            await client.update_object(todo_url, ical_data, etag)

            return {
                "success": True,
                "message": "Todo updated successfully",
                "todo": {"uid": todo_uid, "summary": update_data["summary"]},
                "url": todo_url,
            }
        except Exception:
            continue

    raise HTTPException(status_code=404, detail=f"Todo '{todo_uid}' not found")


@app.delete("/api/todos/{todo_uid}", tags=["待办"])
async def delete_todo(todo_uid: str, if_match: Optional[str] = Header(None)):
    """删除待办"""
    client = get_client()
    calendars = await list_calendars()

    for calendar in calendars["calendars"]:
        try:
            todo_url = f"{calendar['url'].rstrip('/')}/{todo_uid}.ics"
            _, etag = await client.get_object(todo_url)
            final_etag = if_match or etag

            await client.delete_object(todo_url, final_etag)
            return {"success": True, "message": "Todo deleted successfully"}
        except Exception:
            continue

    raise HTTPException(status_code=404, detail=f"Todo '{todo_uid}' not found")


def custom_openapi():
    """生成自定义的 OpenAPI 3.0 Schema"""
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="钉钉 CalDAV 客户端 API",
        version="0.1.0",
        description="提供日历同步和管理功能的REST API服务",
        routes=app.routes,
        servers=[
            {"url": "http://localhost:8000", "description": "本地开发服务器"},
            {"url": "http://192.168.1.204:8000", "description": "生产服务器"},
        ],
    )

    openapi_schema["openapi"] = "3.1.0"

    openapi_schema["info"]["contact"] = {
        "name": "API Support",
        "url": "https://github.com/your-repo/calendar-dingtalk-client",
    }

    openapi_schema["info"]["license"] = {
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    }

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


def main():
    config.validate()
    global _caldav_client
    _caldav_client = CalDAVClient(
        config.caldav_base_url,
        config.caldav_username,
        config.caldav_password,
        config.caldav_timeout,
    )
    uvicorn.run(app, host=config.http_host, port=config.http_port)


if __name__ == "__main__":
    main()
