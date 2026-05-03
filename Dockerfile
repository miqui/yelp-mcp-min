# syntax=docker/dockerfile:1

# ── builder stage ─────────────────────────────────────────────────────────────
FROM python:3.11.13-slim-bookworm AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:0.11.7 /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev --compile-bytecode

# ── runtime stage ─────────────────────────────────────────────────────────────
FROM python:3.11.13-slim-bookworm AS runtime

WORKDIR /app

# Strip setuid/setgid bits and remove common net tools to reduce attack surface
RUN find / -xdev -perm /6000 -exec chmod a-s {} + 2>/dev/null || true \
    && apt-get purge -y --auto-remove wget curl 2>/dev/null || true \
    && rm -rf /var/lib/apt/lists/*

RUN addgroup --gid 1001 appgroup && \
    adduser --disabled-password --gecos "" --uid 1001 --gid 1001 appuser

COPY --from=builder --chown=appuser:appgroup /app/.venv ./.venv
COPY --chown=appuser:appgroup server/ ./server/

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

LABEL org.opencontainers.image.base.name="python:3.11.13-slim-bookworm" \
      org.opencontainers.image.source="https://github.com/miqui/yelp-mcp-min"

USER appuser

CMD ["python", "-m", "server.main"]
