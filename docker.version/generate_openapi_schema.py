#!/usr/bin/env python3
"""
生成 OpenAPI 3.1.0 Schema 文件
"""

import json
from pathlib import Path
from fastapi import FastAPI
from calendar_dingtalk_client.http_server import app


def generate_openapi_schema():
    """生成 OpenAPI 3.1.0 格式的 schema 文件"""

    schema = app.openapi()

    schema["openapi"] = "3.1.0"
    schema["info"] = {
        "title": "钉钉 CALDAV 客户端 API",
        "version": "0.1.0",
        "description": "Calendar DingTalk Client API - 提供日历同步和管理功能",
        "contact": {
            "name": "API Support",
            "url": "https://github.com/your-repo/calendar-dingtalk-client",
        },
        "license": {"name": "MIT", "url": "https://opensource.org/licenses/MIT"},
    }

    servers = [
        {"url": "http://localhost:8000", "description": "本地开发服务器"},
        {"url": "http://192.168.1.204:8000", "description": "生产服务器"},
    ]

    if "servers" not in schema:
        schema["servers"] = servers

    output_dir = Path(__file__).parent / "api_schema"
    output_dir.mkdir(exist_ok=True)

    json_path = output_dir / "openapi.json"
    yaml_path = output_dir / "openapi.yaml"

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(schema, f, ensure_ascii=False, indent=2)

    import yaml

    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(schema, f, allow_unicode=True, sort_keys=False)

    print(f"✅ OpenAPI Schema 生成完成:")
    print(f"   - JSON: {json_path}")
    print(f"   - YAML: {yaml_path}")
    print(f"   - 端点数量: {len(schema.get('paths', {}))}")
    print(f"   - OpenAPI 版本: {schema['openapi']}")

    return schema


if __name__ == "__main__":
    generate_openapi_schema()
