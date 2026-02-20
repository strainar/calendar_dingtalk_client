"""
配置管理模块测试
"""
import os
import pytest
from calendar_dingtalk_client.config import Config, get_config


@pytest.fixture
def clean_env():
    """清理环境变量"""
    old_env = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(old_env)


def test_config_default_values(clean_env):
    """测试配置默认值"""
    config = Config()
    
    assert config.caldav_base_url == "https://calendar.dingtalk.com"
    assert config.caldav_timeout == 30
    assert config.http_host == "0.0.0.0"
    assert config.http_port == 8080
    assert config.http_workers == 4
    assert config.log_level == "INFO"
    assert config.log_format == "json"
    assert config.mcp_server_name == "dingtalk-caldav-calendar"
    assert config.mcp_server_version == "0.1.0"


def test_config_from_env(clean_env):
    """测试从环境变量加载配置"""
    os.environ["CALDAV_BASE_URL"] = "https://test.example.com"
    os.environ["CALDAV_USERNAME"] = "test_user"
    os.environ["CALDAV_PASSWORD"] = "test_pass"
    os.environ["CALDAV_TIMEOUT"] = "60"
    os.environ["HTTP_PORT"] = "9000"
    os.environ["LOG_LEVEL"] = "DEBUG"
    
    config = Config()
    
    assert config.caldav_base_url == "https://test.example.com"
    assert config.caldav_username == "test_user"
    assert config.caldav_password == "test_pass"
    assert config.caldav_timeout == 60
    assert config.http_port == 9000
    assert config.log_level == "DEBUG"


def test_config_validate_success(clean_env):
    """测试配置验证成功"""
    os.environ["CALDAV_USERNAME"] = "test_user"
    os.environ["CALDAV_PASSWORD"] = "test_pass"
    
    config = Config()
    assert config.validate() is True


def test_config_validate_failure(clean_env):
    """测试配置验证失败"""
    os.environ["CALDAV_USERNAME"] = ""
    os.environ["CALDAV_PASSWORD"] = ""
    
    config = Config()
    with pytest.raises(ValueError, match="CALDAV_USERNAME and CALDAV_PASSWORD must be set"):
        config.validate()


def test_config_singleton(clean_env):
    """测试配置单例模式"""
    os.environ["CALDAV_USERNAME"] = "user1"
    config1 = get_config()
    
    os.environ["CALDAV_USERNAME"] = "user2"
    config2 = get_config()
    
    # 应该是同一个实例
    assert config1 is config2
    assert config1.caldav_username == "user1"
