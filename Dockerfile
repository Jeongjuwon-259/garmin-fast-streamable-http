# Garmin Connect MCP Server (streamable-http) — Dockerfile
# 사용법: docker build -t garmin-mcp:latest .

FROM python:3.12-slim

# UV 사용 (pip보다 빠름, pyproject.toml과 호환)
RUN pip install --no-cache-dir uv

WORKDIR /app

# 소스 전체 먼저 복사 (editable install은 src/ 트리가 있어야 동작함 —
# pyproject.toml만 먼저 COPY하면 src/garmin_mcp가 없어서 빌드 실패함)
COPY . .

# hatchling 빌드 시스템 + editable 설치 (pyproject.toml 호환)
RUN uv pip install --system -e .

# python:3.12-slim은 root로 실행되므로 $HOME=/root
ENV GARMIN_TOKEN_DIR=/root/.garminconnect

# streamable-http 모드로 전환 (main()이 CLI 인자를 안 읽으므로 반드시 env var로 설정)
ENV MCP_TRANSPORT=streamable-http
ENV MCP_HOST=0.0.0.0
ENV MCP_PORT=8000

EXPOSE 8000

ENTRYPOINT ["garmin-mcp"]
