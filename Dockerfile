# syntax=docker/dockerfile:1.7

# ---- Stage 1: vendor assets -----------------------------------------------
FROM oven/bun:1-alpine AS vendor
WORKDIR /build
COPY package.json bun.lock* ./
RUN bun install --production --frozen-lockfile
RUN mkdir -p vendor/htmx vendor/bootstrap-show-password \
    && cp -a node_modules/htmx.org/dist/. vendor/htmx/ \
    && cp -a node_modules/bootstrap-show-password/dist/. vendor/bootstrap-show-password/


# ---- Stage 2: python builder ----------------------------------------------
FROM python:3.14-slim-bookworm AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/app/.venv

WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

COPY src ./src
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev


# ---- Stage 3: runtime -----------------------------------------------------
FROM python:3.14-slim-bookworm AS runtime

# OCI image annotations — registries (GHCR, Docker Hub, Harbor) surface
# these in their UI and security scanners use them for SBOM linkage.
LABEL org.opencontainers.image.title="not-just-a-todo-app" \
    org.opencontainers.image.description="Flask-Admin task sequence tracker" \
    org.opencontainers.image.url="https://github.com/hasansezertasan/not-just-a-todo-app" \
    org.opencontainers.image.source="https://github.com/hasansezertasan/not-just-a-todo-app" \
    org.opencontainers.image.licenses="MIT" \
    org.opencontainers.image.authors="Hasan Sezer Taşan <hasansezertasan@gmail.com>" \
    org.opencontainers.image.base.name="docker.io/library/python:3.14-slim-bookworm"

RUN groupadd --system app \
    && useradd --system --gid app --home-dir /home/app --shell /bin/bash app \
    && mkdir -p /home/app /app/instance \
    && chown -R app:app /home/app /app

WORKDIR /app

COPY --from=builder --chown=app:app /app/.venv /app/.venv
COPY --from=builder --chown=app:app /app/src /app/src
COPY --from=vendor  --chown=app:app /build/vendor /app/src/app/static/vendor
COPY --chown=app:app gunicorn.conf.py /app/gunicorn.conf.py
COPY --chown=app:app docker/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

ARG GIT_SHA=""

ENV PATH="/app/.venv/bin:${PATH}" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    FLASK_APP=app.wsgi \
    APP_ENV=production \
    LOG_LEVEL=INFO \
    WEB_CONCURRENCY=2 \
    PORT=8000 \
    GIT_SHA=${GIT_SHA}

USER app
EXPOSE 8000

# Standalone HEALTHCHECK so plain `docker run` (without compose) reports
# health. Compose overrides via its own healthcheck block.
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/readyz').status==200 else 1)" || exit 1

ENTRYPOINT ["entrypoint.sh"]
CMD ["gunicorn", "--config", "/app/gunicorn.conf.py", "app.wsgi:app"]
