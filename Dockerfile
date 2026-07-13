# syntax=docker/dockerfile:1

# ---- Stage 1: builder -------------------------------------------------------
# Installs dependencies into a self-contained virtualenv using uv. Kept separate
# so the heavy build tooling never lands in the final image.
FROM python:3.14-slim AS builder

# uv is distributed as a static binary; copy it straight from the official image.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# - Don't let uv try to manage/download its own Python; use the image's.
# - Compile .pyc ahead of time for faster container startup.
# - Copy packages into .venv instead of symlinking to the uv cache.
ENV UV_PYTHON_DOWNLOADS=0 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

# Install dependencies FIRST, using only the lockfiles. This layer is cached and
# only rebuilds when your dependencies change - not on every source edit.
# --no-install-project: skip installing our own code here (it's not copied yet).
# --no-dev: exclude the dev dependency group (pytest, httpx, etc.).
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project --no-dev

# Now copy the source and install the project itself into the venv.
COPY src ./src
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev

# ---- Stage 2: runtime -------------------------------------------------------
# Minimal image: just Python + the built venv + our code + Alembic assets.
FROM python:3.14-slim AS runtime

# Create an unprivileged user so the app doesn't run as root.
RUN useradd --create-home --uid 1000 appuser

WORKDIR /app

# Bring over the fully-populated virtualenv and the application code.
COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv
COPY --chown=appuser:appuser src ./src
COPY --chown=appuser:appuser alembic ./alembic
COPY --chown=appuser:appuser alembic.ini ./alembic.ini
COPY --chown=appuser:appuser docker-entrypoint.sh ./docker-entrypoint.sh

# Put the venv on PATH so `python`, `uvicorn`, `alembic` resolve to it directly,
# and expose src so `import app...` works without uv at runtime.
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app/src" \
    PYTHONUNBUFFERED=1

USER appuser

EXPOSE 8000

ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
