# ── Builder stage ────────────────────────────────────────────────────────────
# Installs Poetry into a project-local venv, then discards the toolchain.
FROM python:3.14-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --no-cache-dir poetry

COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.in-project true \
    && poetry install --no-interaction --no-ansi --only main --no-root

# ── Final stage ───────────────────────────────────────────────────────────────
# Lean image: venv + application code only. No Poetry, no pip, no curl.
FROM python:3.14-slim AS final

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Copy the pre-built venv — no version-specific paths, no system Python pollution.
COPY --from=builder /app/.venv /app/.venv

# Copy only the application package.
COPY euvd_mcp ./euvd_mcp

# Non-root user — must run after COPY so chown covers all files.
RUN groupadd --system app \
    && useradd --system --gid app --no-create-home app \
    && chown -R app:app /app

USER app

EXPOSE 8000

# Liveness probe — hits the /health endpoint (HTTP transport only).
# If TRANSPORT=stdio is set, run the server as a local subprocess instead.
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=8)" || exit 1

CMD ["uvicorn", "euvd_mcp.main:app", "--host", "0.0.0.0", "--port", "8000"]
