"""
命令行工具
"""
import asyncio
from .config import get_config
from .caldav.client import CalDAVClient

async def main():
    config = get_config()
    config.validate()
    
    async with CalDAVClient(config.caldav_base_url, config.caldav_username, config.caldav_password) as client:
        calendars = await client.list_calendars()
        print(f"找到 {len(calendars)} 个日历:")
        for cal in calendars:
            print(f"  - {cal['displayname']}: {cal['url']}")

if __name__ == "__main__":
    asyncio.run(main())
