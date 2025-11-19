# 使用官方 Python 3.11 镜像作为基础镜像
FROM mcr.microsoft.com/playwright/python:v1.50.0-jammy

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    SERVER_MODE=http \
    HTTP_PORT=8080 \
    HTTP_HOST=0.0.0.0 \
    UVICORN_WORKERS=1

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt pyproject.toml ./

# 安装 Python 依赖
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Playwright 浏览器已包含在基础镜像中，但再次安装可确保版本一致
RUN playwright install chromium

# 复制项目文件
COPY src/ ./src/
COPY examples/ ./examples/
COPY docker/entrypoint.sh /app/entrypoint.sh
COPY docker/healthcheck.sh /app/healthcheck.sh

RUN chmod +x /app/entrypoint.sh /app/healthcheck.sh

# 创建必要的目录
RUN mkdir -p /app/logs /app/cache /app/reports

# 创建非 root 用户（安全最佳实践）
RUN if ! id appuser >/dev/null 2>&1; then \
    useradd -m -u 1010 appuser; \
    fi && \
    chown -R appuser:appuser /app

# 切换到非 root 用户
USER appuser

# 暴露端口（默认 HTTP 服务端口）
EXPOSE 8080

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD ["/app/healthcheck.sh"]

# 入口命令
ENTRYPOINT ["/app/entrypoint.sh"]

