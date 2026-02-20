"""
iCalendar 构建器
"""
from typing import Dict, Any
from icalendar import Calendar, Event as IEvent, Todo as ITodo
from datetime import datetime

def build_event(event: Dict[str, Any]) -> str:
    """构建事件"""
    cal = Calendar()
    cal.add('prodid', '-//DingTalk CalDAV Client//CN')
    cal.add('version', '2.0')
    
    ie = IEvent()
    ie.add('uid', event['uid'])
    ie.add('summary', event['summary'])
    if event.get('dtstart'):
        ie.add('dtstart', event['dtstart'])
    if event.get('dtend'):
        ie.add('dtend', event['dtend'])
    if event.get('description'):
        ie.add('description', event['description'])
    if event.get('location'):
        ie.add('location', event['location'])
    
    cal.add_component(ie)
    return cal.to_ical()

def build_todo(todo: Dict[str, Any]) -> str:
    """构建待办"""
    cal = Calendar()
    cal.add('prodid', '-//DingTalk CalDAV Client//CN')
    cal.add('version', '2.0')
    
    it = ITodo()
    it.add('uid', todo['uid'])
    it.add('summary', todo['summary'])
    if todo.get('due'):
        it.add('due', todo['due'])
    if todo.get('priority'):
        it.add('priority', todo['priority'])
    if todo.get('status'):
        it.add('status', todo['status'])
    
    cal.add_component(it)
    return cal.to_ical()
