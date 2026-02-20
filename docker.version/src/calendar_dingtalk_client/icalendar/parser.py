"""
iCalendar 解析器
"""
from typing import Dict, Any
from icalendar import Calendar as ICalendar

def parse_event(ical_data: str) -> Dict[str, Any]:
    """解析事件"""
    cal = ICalendar.from_ical(ical_data)
    for component in cal.walk():
        if component.name == "VEVENT":
            return {
                'uid': str(component.get('uid', '')),
                'summary': str(component.get('summary', '')),
                'dtstart': component.get('dtstart').dt if component.get('dtstart') else None,
                'dtend': component.get('dtend').dt if component.get('dtend') else None,
                'description': str(component.get('description', '')),
                'location': str(component.get('location', '')),
            }
    return {}

def parse_todo(ical_data: str) -> Dict[str, Any]:
    """解析待办"""
    cal = ICalendar.from_ical(ical_data)
    for component in cal.walk():
        if component.name == "VTODO":
            return {
                'uid': str(component.get('uid', '')),
                'summary': str(component.get('summary', '')),
                'status': str(component.get('status', 'NEEDS-ACTION')),
                'due': component.get('due').dt if component.get('due') else None,
                'priority': component.get('priority', 5),
            }
    return {}
