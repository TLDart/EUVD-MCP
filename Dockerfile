# ── Builder stage ────────────────────────────────────────────────────────────
# Installs Poetry and all production dependencies, then discards the toolchain.
FROM python:3.14-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && curl -sSL https://install.python-poetry.org | python3 -

ENV PATH="/root/.local/bin:$PATH"

COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --only main

# ── Final stage ───────────────────────────────────────────────────────────────
# Lean image: only installed packages + application code, no Poetry or curl.
FROM python:3.14-slim AS final

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copy site-packages and entry-point scripts installed by Poetry in the builder.
COPY --from=builder /usr/local/lib/python3.14/site-packages /usr/local/lib/python3.14/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy only the application package (not dev files, docs, etc.).
COPY euvd_mcp ./euvd_mcp
COPY pyproject.toml ./

# Non-root user — must run after COPY so chown covers all files.
RUN groupadd --system app \
    && useradd --system --gid app --no-create-home app \
    && chown -R app:app /app

USER app

EXPOSE 8000

# Liveness probe — hits the /health endpoint (HTTP transport only).
# This probe assumes TRANSPORT=http (the default). If you override TRANSPORT=stdio
# the container should not use this image; run the server as a local subprocess instead.
# Uses Python's stdlib so no extra tooling is needed in the final image.
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=8)" || exit 1

CMD ["python", "-m", "euvd_mcp.main"]
