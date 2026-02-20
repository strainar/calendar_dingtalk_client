"""
配置管理模块
从 .env 文件加载配置
"""
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
import os


class Config:
    """配置类"""

    def __init__(self):
        """加载 .env 文件"""
        load_dotenv()

    @property
    def caldav_base_url(self) -> str:
        """CALDAV 基础 URL"""
        return os.getenv("CALDAV_BASE_URL", "https://calendar.dingtalk.com")

    @property
    def caldav_username(self) -> Optional[str]:
        """CALDAV 用户名"""
        return os.getenv("CALDAV_USERNAME")

    @property
    def caldav_password(self) -> Optional[str]:
        """CALDAV 密码"""
        return os.getenv("CALDAV_PASSWORD")

    @property
    def caldav_timeout(self) -> int:
        """CALDAV 超时时间（秒）"""
        return int(os.getenv("CALDAV_TIMEOUT", "30"))

    @property
    def http_host(self) -> str:
        """HTTP 服务器主机"""
        return os.getenv("HTTP_HOST", "0.0.0.0")

    @property
    def http_port(self) -> int:
        """HTTP 服务器端口"""
        return int(os.getenv("HTTP_PORT", "8080"))

    @property
    def http_workers(self) -> int:
        """HTTP 服务器工作进程数"""
        return int(os.getenv("HTTP_WORKERS", "4"))

    @property
    def api_key(self) -> Optional[str]:
        """API 密钥"""
        return os.getenv("API_KEY")

    @property
    def log_level(self) -> str:
        """日志级别"""
        return os.getenv("LOG_LEVEL", "INFO")

    @property
    def log_format(self) -> str:
        """日志格式"""
        return os.getenv("LOG_FORMAT", "json")

    @property
    def mcp_server_name(self) -> str:
        """MCP 服务器名称"""
        return os.getenv("MCP_SERVER_NAME", "dingtalk-caldav-calendar")

    @property
    def mcp_server_version(self) -> str:
        """MCP 服务器版本"""
        return os.getenv("MCP_SERVER_VERSION", "0.1.0")

    def validate(self) -> bool:
        """验证配置是否完整"""
        if not self.caldav_username or not self.caldav_password:
            raise ValueError("CALDAV_USERNAME and CALDAV_PASSWORD must be set in .env file")
        return True


# 全局配置实例
_config: Optional[Config] = None


def get_config() -> Config:
    """获取配置实例（单例）"""
    global _config
    if _config is None:
        _config = Config()
    return _config
