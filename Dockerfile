FROM python:3.14-slim AS build
COPY --from=ghcr.io/astral-sh/uv:0.9.2 /uv /uvx /bin/
WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY backend/pyproject.toml backend/pyproject.toml
COPY backend/src backend/src
RUN uv sync --frozen --no-dev --package backend --no-editable

FROM python:3.14-slim
WORKDIR /app
COPY --from=build /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH" \
    TRAININGOS_HOST=0.0.0.0 \
    PYTHONUNBUFFERED=1
USER 10001:10001
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)"]
CMD ["trainingos-api"]
