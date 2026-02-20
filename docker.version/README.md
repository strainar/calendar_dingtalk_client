# DingTalk CaLVDAV Calendar Client - Docker Version

这是主项目 `../` (uv专用版本) 的 Docker 部署版本，已优化为纯pip管理，专门用于容器化环境。

## 🚀 快速开始

### 方法1: Docker Compose（推荐）

```bash
# 设置配置文件
cp .env.example .env
# 编辑 .env 文件，填入钉钉凭证

# 构建并启动
docker-compose up -d

# 查看日志
docker-compose logs -f

# 验证运行
curl http://localhost:8080/health
```

### 方法2: 直接 Docker 命令

```bash
# 设置配置文件
cp .env.example .env
# 编辑 .env 文件，填入钉钉凭证

# 构建镜像
docker build -t dingtalk-calendar .

# 运行容器
docker run -d -p 8080:8080 --env-file .env --name calendar-app dingtalk-calendar

# 查看日志
docker logs -f calendar-app

# 验证运行
curl http://localhost:8080/health
```

### 方法3: 本地直接运行（检查代码）

```bash
# 安装依赖
pip install -r requirements.txt

# 运行应用
./run.sh

# 或直接使用 uvicorn
cd src
uvicorn calendar_dingtalk_client.http_server:app --host 0.0.0.0 --port 8080 --reload
```

## 📡 API 接口

### 健康检查
```bash
GET /health
# 返回: {"status": "healthy", "version": "0.1.0"}
```

### 日历列表
```bash
GET /api/calendars
# 返回: {"calendars": [...]}
```

### 创建事件
```bash
POST /api/calendars/primary/events
Content-Type: application/json

{
  "summary": "测试事件",
  "start": "2024-02-07T10:00:00Z",
  "end": "2024-02-07T11:00:00Z",
  "location": "会议室",
  "description": "这是一个测试事件"
}
```

## 🔧 与主项目的关系

### 目录结构
```
/d/CodeSpaces/calendar_dingtalk_client/
├── pyproject.toml          # 主项目 (uv + Python 3.12)
├── src/                    # 主要代码
├── docker.version/         # 当前目录 (Docker + Python 3.10)
│   ├── Dockerfile          # 优化的 Docker 配置
│   ├── requirements.txt    # pip 依赖
│   ├── docker-compose.yml  # 部署配置
│   └── src/                # 代码副本
```

### 同步策略
- **手工同步**: 修改主项目后，手动复制 `src/` 到 `docker.version/src/`
- **时间记录**: 更新 `SYNC_CHECKLIST.md` 标记同步事件
- **测试验证**: 每次同步后运行 `docker build` 测试

## 🐳 Docker 优化

### 构建优势
- **快速**: < 30秒 (vs 主项目可能失败的网络依赖)
- **轻量**: ~350MB 镜像 (vs uv版本的1GB+)
- **稳定**: 无外部网络依赖

### 安全特性
- 运行于非 root 用户 (appuser)
- 单独的 logs 卷挂载
- 健康检查和自动重启

## ⚙️ 配置

### 环境变量
```bash
CALDAV_BASE_URL=https://calendar.dingtalk.com/dav/u_zakdeoez
CALDAV_USERNAME=u_zakdeoez
CALDAV_PASSWORD=your_password
HTTP_HOST=0.0.0.0
HTTP_PORT=8080
```

### 调试模式
```bash
# 启用调试日志
docker run -e LOG_LEVEL=DEBUG [...]
```

## 🔄 从主项目同步

```bash
# 从主项目同步源码
cp -r ../src .

# 更新配置文件
cp ../.env.example .

# 更新依赖 (如果需要)
./install_deps.sh

# 测试构建
docker build .
```

## 🚨 问题排查

### 容器无法启动
```bash
# 检查日志
docker-compose logs

# 检查配置文件
cat .env

# 手动测试
docker run --rm -it --env-file .env dingtalk-calendar /bin/bash
```

### 端口冲突
```bash
# 修改端口
docker run -p 8081:8080 [...]
# 或修改 docker-compose.yml
```

### 网络问题
```bash
# 使用不同DNS
docker run --dns 8.8.8.8 [...]
```

## 📊 技术规格

- **Python**: 3.10 (与Docker镜像兼容)
- **Web框架**: FastAPI + Uvicorn
- **包管理**: pip + requirements.txt
- **容器化**: Docker + Docker Compose
- **健康检查**: HTTP请求监控
- **日志管理**: JSON格式日志

## 🎯 使用场景

- ✅ **生产部署**: 企业级容器环境
- ✅ **开发验证**: 测试CALDAV功能
- ✅ **CI/CD**: 自动化构建和测试
- ✅ **快速演示**: 向用户展示功能

此Docker版本完全独立于主uv项目，可单独维护和部署。
