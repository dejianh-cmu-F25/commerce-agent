# syntax=docker/dockerfile:1

# --- frontend: build the React SPA (Vite) ---
FROM node:20-alpine AS frontend
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
# Optional npm registry mirror for slow networks, e.g.
#   --build-arg NPM_REGISTRY=https://registry.npmmirror.com
ARG NPM_REGISTRY=
RUN if [ -n "$NPM_REGISTRY" ]; then npm config set registry "$NPM_REGISTRY"; fi \
    && npm ci
COPY frontend/ ./
RUN npm run build

# --- builder: install python dependencies into a virtualenv ---
FROM python:3.12-slim AS builder
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
RUN pip install --no-cache-dir uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
# Optional Python index mirror for slow networks, e.g.
#   --build-arg UV_DEFAULT_INDEX=https://pypi.tuna.tsinghua.edu.cn/simple
ARG UV_DEFAULT_INDEX=
RUN if [ -n "$UV_DEFAULT_INDEX" ]; then \
        uv sync --frozen --no-dev --no-install-project --default-index "$UV_DEFAULT_INDEX"; \
    else \
        uv sync --frozen --no-dev --no-install-project; \
    fi
COPY . .
RUN uv sync --frozen --no-dev

# --- runtime: non-root, slim, with a healthcheck ---
FROM python:3.12-slim AS runtime
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
RUN useradd --create-home --uid 10001 appuser
COPY --from=builder /app /app
COPY --from=frontend /web/static/app /app/web/static/app
RUN mkdir -p /app/data/db /app/data/chroma /app/logs \
    && chown -R appuser:appuser /app
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz')" || exit 1
CMD ["uvicorn", "web.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
