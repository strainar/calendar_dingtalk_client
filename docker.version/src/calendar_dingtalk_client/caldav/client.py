"""
CALDAV 客户端核心类
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import httpx
import logging
from lxml import etree

logger = logging.getLogger(__name__)


class CalDAVClient:
    """钉钉 CALDAV 客户端"""

    def __init__(
        self, base_url: str, username: str, password: str, timeout: float = 30.0
    ):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None
        self.NS_DAV = "DAV:"
        self.NS_CALDAV = "urn:ietf:params:xml:ns:caldav"

    async def __aenter__(self):
        self._client = httpx.AsyncClient(
            auth=(self.username, self.password),
            timeout=self.timeout,
            headers={
                "User-Agent": "calendar-dingtalk-client/0.1.0",
                "Accept": "text/xml, application/xml, text/calendar",
            },
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.aclose()

    async def discover_calendar_home(self) -> str:
        """发现日历主页"""
        return self.base_url

    async def list_calendars(
        self, home_url: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """列出日历集合"""
        if not home_url:
            home_url = self.base_url

        print(f"[DEBUG] PROPFIND to: {home_url}")

        xml = (
            '<?xml version="1.0" encoding="utf-8" ?>'
            '<D:propfind xmlns:D="DAV:" xmlns:C="urn:ietf:params:xml:ns:caldav">'
            "<D:prop><D:resourcetype/><D:displayname/><C:calendar-description/></D:prop>"
            "</D:propfind>"
        )
        try:
            response = await self._client.request(
                "PROPFIND",
                home_url,
                content=xml,
                headers={
                    "Content-Type": "application/xml; charset=utf-8",
                    "Depth": "1",
                },
            )
            print(f"[DEBUG] PROPFIND response status: {response.status_code}")
            print(
                f"[DEBUG] PROPFIND response body (first 1000 chars):\n{response.text[:1000]}"
            )
            response.raise_for_status()
        except Exception as e:
            print(f"[ERROR] PROPFIND failed: {e}")
            return []

        return self._parse_calendars(response.text)

    async def get_calendar_events(
        self,
        calendar_url: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        component_type: str = "VEVENT",
    ) -> List[Dict[str, Any]]:
        """获取事件列表 - 使用 PROPFIND 代替 REPORT（钉钉服务器兼容性问题）"""
        logger.info(f"Fetching events from {calendar_url}")

        xml = (
            '<?xml version="1.0" encoding="utf-8" ?>'
            '<D:propfind xmlns:D="DAV:" xmlns:C="urn:ietf:params:xml:ns:caldav">'
            "<D:prop><D:resourcetype/><D:getcontenttype/><D:getetag/></D:prop>"
            "</D:propfind>"
        )

        try:
            response = await self._client.request(
                "PROPFIND",
                calendar_url,
                content=xml,
                headers={
                    "Content-Type": "application/xml; charset=utf-8",
                    "Depth": "1",
                },
            )
            response.raise_for_status()
            events = await self._parse_events_from_propfind(response.text, calendar_url)
            logger.info(f"Found {len(events)} events")
            return events
        except Exception as e:
            logger.error(f"Error fetching events: {e}")
            import traceback

            traceback.print_exc()
            return []

    async def get_object(self, object_url: str) -> tuple[str, str]:
        """获取单个对象"""
        response = await self._client.get(object_url)
        response.raise_for_status()
        return response.text, response.headers.get("ETag", "").strip('"')

    async def create_object(self, calendar_url: str, uid: str, ical_data: str) -> str:
        """创建对象"""
        object_url = f"{calendar_url}/{uid}.ics"
        response = await self._client.put(
            object_url,
            content=ical_data,
            headers={"Content-Type": "text/calendar; charset=utf-8"},
        )
        response.raise_for_status()
        return response.headers.get("Location", object_url)

    async def update_object(self, object_url: str, ical_data: str, etag: str) -> None:
        """更新对象"""
        await self._client.put(
            object_url,
            content=ical_data,
            headers={
                "Content-Type": "text/calendar; charset=utf-8",
                "If-Match": f'"{etag}"',
            },
        )

    async def delete_object(self, object_url: str, etag: str) -> None:
        """删除对象"""
        await self._client.delete(object_url, headers={"If-Match": f'"{etag}"'})

    def _parse_calendars(self, xml_text: str) -> List[Dict[str, Any]]:
        """解析日历响应"""
        calendars = []
        try:
            print(f"[DEBUG] Parsing calendars, XML length: {len(xml_text)}")
            root = etree.fromstring(xml_text.encode())
            ns = {"D": "DAV:", "C": "urn:ietf:params:xml:ns:caldav"}

            responses = root.findall(".//D:response", ns)
            print(f"[DEBUG] Found {len(responses)} D:response elements")

            for i, response in enumerate(responses):
                href_elem = response.find("D:href", ns)
                if href_elem is None or href_elem.text is None:
                    print(f"[DEBUG] Response {i}: no href, skipping")
                    continue

                href = href_elem.text
                print(f"[DEBUG] Response {i}: href={href}")

                if href == "/" or href == "":
                    print(f"[DEBUG] Response {i}: skipping root directory")
                    continue

                if not href.startswith("/"):
                    print(f"[DEBUG] Response {i}: href doesn't start with /, skipping")
                    continue

                ok_propstat = None
                for propstat in response.findall("D:propstat", ns):
                    status = propstat.find("D:status", ns)
                    if status is not None and "200" in status.text:
                        ok_propstat = propstat
                        print(f"[DEBUG] Response {i}: found 200 OK propstat")
                        break

                if ok_propstat is None:
                    print(f"[DEBUG] Response {i}: no 200 OK propstat, skipping")
                    continue

                prop = ok_propstat.find("D:prop", ns)
                if prop is None:
                    print(f"[DEBUG] Response {i}: no prop in 200 OK propstat, skipping")
                    continue

                resourcetype = prop.find("D:resourcetype", ns)
                if resourcetype is None:
                    print(f"[DEBUG] Response {i}: no resourcetype, skipping")
                    continue

                calendar_elem = resourcetype.find(f"{{{self.NS_CALDAV}}}calendar")

                print(
                    f"[DEBUG] Response {i}: calendar_elem found = {calendar_elem is not None}"
                )

                if calendar_elem is None:
                    print(f"[DEBUG] Response {i}: no C:calendar tag, skipping")
                    continue

                displayname_elem = prop.find("D:displayname", ns)
                description_elem = prop.find(
                    f"{{{self.NS_CALDAV}}}calendar-description"
                )

                from urllib.parse import urlparse

                parsed = urlparse(self.base_url)
                calendar_url = f"{parsed.scheme}://{parsed.netloc}{href}"

                calendar = {
                    "url": calendar_url,
                    "name": href.rstrip("/").split("/")[-1],
                    "displayname": displayname_elem.text
                    if displayname_elem is not None and displayname_elem.text
                    else href.rstrip("/").split("/")[-1],
                    "description": description_elem.text
                    if description_elem is not None and description_elem.text
                    else None,
                }
                calendars.append(calendar)
                print(
                    f"[DEBUG] Added calendar: {calendar['displayname']}, URL: {calendar['url']}"
                )

        except Exception as e:
            print(f"[ERROR] Parse calendars error: {e}")
            import traceback

            traceback.print_exc()

        logger.info(f"Returning {len(calendars)} calendars")
        return calendars

    async def _parse_events_from_propfind(
        self, xml_text: str, calendar_url: str
    ) -> List[Dict[str, Any]]:
        """从 PROPFIND 响应解析事件"""
        events = []
        try:
            print(f"[DEBUG] Parsing events from PROPFIND for calendar: {calendar_url}")
            root = etree.fromstring(xml_text.encode())
            ns = {"D": "DAV:", "C": "urn:ietf:params:xml:ns:caldav"}

            for response in root.findall(".//D:response", ns):
                href_elem = response.find("D:href", ns)
                if href_elem is None or href_elem.text is None:
                    continue

                href = href_elem.text

                if href == "/" or href.endswith("/"):
                    continue

                ok_propstat = None
                for propstat in response.findall("D:propstat", ns):
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

                if "text/calendar" not in contenttype_elem.text:
                    continue

                from urllib.parse import urlparse

                parsed = urlparse(self.base_url)
                event_url = f"{parsed.scheme}://{parsed.netloc}{href}"

                print(f"[DEBUG] Fetching event: {event_url}")
                etag_elem = prop.find("D:getetag", ns)

                try:
                    ical_data, etag_from_get = await self.get_object(event_url)
                    print(f"[DEBUG] Got iCalendar data for {event_url}")

                    from ..icalendar.parser import parse_event

                    event_data = parse_event(ical_data)

                    if event_data:
                        event = {
                            "url": event_url,
                            "etag": etag_elem.text if etag_elem is not None else None,
                            "uid": event_data.get("uid", ""),
                            "summary": str(event_data.get("summary", "")),
                            "dtstart": str(event_data.get("dtstart"))
                            if event_data.get("dtstart")
                            else None,
                            "dtend": str(event_data.get("dtend"))
                            if event_data.get("dtend")
                            else None,
                            "location": str(event_data.get("location", ""))
                            if event_data.get("location")
                            else None,
                            "description": str(event_data.get("description", ""))
                            if event_data.get("description")
                            else None,
                        }
                        events.append(event)
                        print(
                            f"[DEBUG] Parsed event: {event.get('summary', 'unknown')}, url: {event['url'][:50]}..."
                        )

                except Exception as e:
                    print(f"[ERROR] Error getting event {event_url}: {e}")
                    continue

        except Exception as e:
            print(f"[ERROR] Parse events from propfind error: {e}")
            import traceback

            traceback.print_exc()

        print(f"[DEBUG] Returning {len(events)} events")
        return events
