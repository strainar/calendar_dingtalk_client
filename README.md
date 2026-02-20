# 钉钉 CALDAV 日历客户端

基于 RFC 4791、RFC 5545 标准的钉钉 CALDAV 日历客户端，支持 MCP 和 HTTP 服务器模式。

## 功能特性

- ✅ 支持 VEVENT（事件）- 完整 CRUD 操作
- ✅ 支持 VTODO（待办）- 完整 CRUD 操作
- ✅ 支持 VFREEBUSY（忙闲）- 查询功能
- ✅ MCP 服务器模式（与 Claude Desktop 集成）
- ✅ HTTP RESTful API 模式
- ✅ 完整遵循 RFC 4791 (CalDAV) 标准
- ✅ 完整遵循 RFC 5545 (iCalendar) 标准
- ✅ 使用 uv 进行 Python 环境管理
- ✅ Docker 容器化支持

## 快速开始

### 1. 环境要求

- Python 3.10+
- uv（包管理器）
- Docker（可选）

### 2. 安装依赖

```bash
# 使用 uv 安装依赖
uv sync --all-extras
```

### 3. 配置环境变量

复制 `.env.example` 到 `.env` 并填入您的钉钉 CALDAV 凭证：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
CALDAV_BASE_URL=https://calendar.dingtalk.com/dav/u_ksskwe9a
CALDAV_USERNAME=your_dingtalk_username_or_email
CALDAV_PASSWORD=your_dingtalk_password
```

### 4. 测试连接

```bash
# 使用 uv 运行测试脚本
uv run python test_connection.py
```

### 5. 运行服务

#### MCP 模式（与 Claude Desktop 集成）

```bash
uv run dingtalk-mcp-server
```

在 Claude Desktop 的配置文件中添加：

```json
{
  "mcpServers": {
    "dingtalk-calendar": {
      "command": "uv",
      "args": ["--directory", "/absolute/path/to/calendar_dingtalk_client", "run", "dingtalk-mcp-server"]
    }
  }
}
```

#### HTTP 服务器模式

```bash
uv run dingtalk-http-server
```

访问 API 文档：http://localhost:8080/docs

#### Docker 模式

```bash
# 构建镜像
docker build -t calendar-dingtalk-client:latest .

# 运行容器
docker run -p 8080:8080 --env-file .env calendar-dingtalk-client:latest

# 或使用 docker-compose
docker-compose up -d
```

## MCP 工具

MCP 服务器提供以下工具：

- `list_calendars` - 列出所有可用的日历
- `get_events` - 获取指定时间范围内的事件
- `get_todos` - 获取指定时间范围内的待办事项
- `create_event` - 创建新事件
- `update_event` - 更新现有事件
- `delete_event` - 删除事件
- `create_todo` - 创建新待办事项
- `update_todo` - 更新现有待办事项
- `delete_todo` - 删除待办事项
- `get_freebusy` - 获取忙闲状态

## HTTP API 端点

- `GET /health` - 健康检查
- `GET /api/calendars` - 列出所有日历
- `GET /api/calendars/{calendar_name}/events` - 获取事件列表
- `POST /api/calendars/{calendar_name}/events` - 创建新事件
- `PUT /api/calendars/{calendar_name}/events/{event_uid}` - 更新事件
- `DELETE /api/calendars/{calendar_name}/events/{event_uid}` - 删除事件
- `GET /api/calendars/{calendar_name}/todos` - 获取待办事项列表
- `POST /api/calendars/{calendar_name}/todos` - 创建新待办事项
- `PUT /api/calendars/{calendar_name}/todos/{todo_uid}` - 更新待办事项
- `DELETE /api/calendars/{calendar_name}/todos/{todo_uid}` - 删除待办事项
- `GET /api/calendars/{calendar_name}/freebusy` - 获取忙闲状态

## 开发

### 运行测试

```bash
# 所有测试
uv run pytest

# 单元测试
uv run pytest tests/unit/ -m "not integration"

# 集成测试（需要真实凭证）
uv run pytest tests/integration/ -m "live"

# 覆盖率
uv run pytest --cov
```

### 代码质量

```bash
# 格式化代码
uv run black src/ tests/

# 代码检查
uv run ruff check src/ tests/ --fix

# 类型检查
uv run mypy src/
```

## 项目结构

```
calendar_dingtalk_client/
├── src/
│   └── calendar_dingtalk_client/
│       ├── __init__.py
│       ├── config.py              # 配置管理
│       ├── mcp_server.py         # MCP 服务器
│       ├── http_server.py        # HTTP 服务器
│       ├── cli.py               # 命令行工具
│       ├── caldav/
│       │   ├── __init__.py
│       │   └── client.py        # CALDAV 客户端
│       └── icalendar/
│           ├── __init__.py
│           ├── parser.py         # iCalendar 解析器
│           └── builder.py        # iCalendar 构建器
├── tests/
│   ├── unit/                  # 单元测试
│   ├── integration/           # 集成测试
│   └── rfc_compliance/        # RFC 合规性测试
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── .env.example
└── README.md
```

## 技术栈

- **语言**: Python 3.10+
- **包管理**: uv
- **HTTP 客户端**: httpx
- **MCP 框架**: mcp[cli]
- **iCalendar**: icalendar
- **HTTP 服务器**: FastAPI + Uvicorn
- **XML 解析**: lxml
- **环境配置**: python-dotenv

## RFC 合规性

### RFC 4791 (CalDAV)
- ✅ WebDAV Class 1 和扩展
- ✅ 日历集合发现和属性查询
- ✅ 支持所有必需的 REPORT 操作
- ✅ ETag 并发控制
- ✅ 时间范围过滤

### RFC 5545 (iCalendar)
- ✅ iCalendar 2.0 格式
- ✅ 正确处理行折叠（75 octets）
- ✅ UTF-8 编码
- ✅ 正确转义特殊字符
- ✅ 支持重复规则

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

## 作者

Your Name <your.email@example.com>
