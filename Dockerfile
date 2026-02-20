# 多阶段构建
FROM python:3.10-slim as builder

# 安装 uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# 设置工作目录
WORKDIR /app

# 复制项目文件
COPY pyproject.toml uv.lock ./

# 创建虚拟环境并安装依赖
RUN uv venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN uv sync --frozen --no-dev

# 生产镜像
FROM python:3.10-slim

# 安装运行时依赖
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ca-certificates curl && \
    rm -rf /var/lib/apt/lists/*

# 从构建阶段复制虚拟环境
COPY --from=builder /opt/venv /opt/venv

# 设置工作目录
WORKDIR /app

# 复制源代码
COPY src/ ./src/

# 创建非 root 用户
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /opt/venv /app
USER appuser

# 设置环境变量
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

# 暴露端口
EXPOSE 8080

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# 启动 HTTP 服务器
CMD ["dingtalk-http-server"]
