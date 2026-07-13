# Blog API (FastAPI)

Async JSON REST API for a blog. Port of a Flask version onto FastAPI + async SQLAlchemy. No HTML/templates — every response is JSON. Python 3.14 on Windows, PostgreSQL via asyncpg.

## Commands
- Dependencies via **uv** (`pyproject.toml` + `uv.lock`). Never bare pip.
- Setup/reproduce: `uv sync`
- Add dependency: `uv add <pkg>` (runtime) / `uv add --dev <pkg>` (dev)
- Run: `uv run uvicorn app.main:app --reload --port 5003` (docs at `/docs`)
- Start Postgres: `docker compose up -d` (runs the Postgres container defined in `docker-compose.yaml`)
- Migrations: `uv run alembic revision --autogenerate -m "<message>"` (create a migration) / `uv run alembic upgrade head` (apply migrations)
- Commit `pyproject.toml` and `uv.lock`; never commit `.venv/`, `.env`, or `blog.db`.
- `src` layout + hatchling: the package is importable because it's installed (via `uv sync`); `import app...` resolves from the installed package, not the cwd.

## Architecture
Layered: **router → service → repository**. Session injected top-down.
- **Routers** (`routers/*.py`, one `APIRouter` each, included in `main.py`) translate HTTP only: typed params (path/query/body), dependency injection, call service, return. `response_model` handles serialization. No business logic, no DB access.
- **Services** (`service.py`) own business logic; `async`; take `session` as first param; raise domain exceptions; build and return typed Pydantic response objects (e.g. `PostResponse.model_validate(obj)`). NEVER import `HTTPException`/`fastapi` — services are HTTP-agnostic.
- **Repositories** (`repository.py`) own all async DB access; `async`; take `session` as first param.
- Import hierarchy is one-directional toward `base.py`: `base` (defines `Base`, imports nothing of app) ← `models`/`database` ← everything else. Do NOT make `base.py` import from the app package. `main.py` imports `models` (`# noqa: F401`) so its SQLAlchemy mappings (e.g. relationships) are registered; `alembic/env.py` imports `models` separately so autogenerate sees the tables.

## Async rules (the recurring bite)
- Every call to an `async def` MUST be `await`ed — including service→repository and internal repository calls.
- `await` binds looser than `.` — `await session.execute(...).scalars().all()` is WRONG. Split into two lines.
- Anything serialized with a relationship must eager-load it or lazy loading fails outside the session context. Reads use `.options(selectinload(BlogPost.author))`; `add_post`/`patch_post` use `await session.refresh(post, ["author"])`.
- Transaction rollback is centralized in `get_db` (try/yield/except-rollback-raise). Repository writes just `commit()`.

## Conventions
- **Validation split**: request shape validation is automatic via Pydantic schemas (bad input → 422). Business rules live in the service and raise domain exceptions.
- **Errors**: domain exceptions (`exceptions.py`); global handlers (`exception_handlers.py`, registered in `main`) map each to a status: NotFound→404, Forbidden→403, Unauthorized→401, InvalidCredentials→401, EmailAlreadyExists→409, PostTitleAlreadyExists→409, ValueError→400. An `HTTPException` handler normalizes to `{"error": ...}`. Pydantic 422s keep FastAPI's `{"detail": ...}` shape.
- **Serialization**: two-class split — SQLAlchemy models for storage, Pydantic schemas for the API boundary. Response schemas use `ConfigDict(from_attributes=True)`. `UserResponse` has no `password`; `PostResponse` nests `author` as `{id, name}` only. Services build response objects; don't return raw ORM.
- **Dates**: date fields use `datetime.date` (qualified import) — NOT `from datetime import date`, which shadows the field name and breaks annotation evaluation. Posts sort newest-first.
- **Passwords**: `bcrypt` via `security.hash_password`/`verify_password`. Stored as text; bytes↔str encode/decode is contained in those two helpers only.
- **Auth**: JWT via PyJWT. Tokens carry `sub` (str user id), `exp`, `type` ("access"/"refresh"). `auth.py` has a `require_token_type(type)` factory producing `get_current_user_id` and `get_refresh_user_id`; the `type` check enforces token-type separation. Identity is a string in the token; `int()` it for DB use.
- **Authorship never from the body**: `PostCreate` has no `author_id`; set from the token. `require_ownership` allows author OR admin, else ForbiddenError.
- **Login anti-enumeration**: unknown-email and wrong-password return the identical vague 401. A `DUMMY_HASH` verify runs on the user-missing path to equalize timing. Do NOT remove it or make the messages distinct.
- **DI style**: use `Annotated` aliases (`SessionDependency`, `CurrentUserDependency`, `RefreshUserDependency`) as param types, not repeated `= Depends(...)`. Aliases are `PascalCase` (they're types).
- **Refactor duplication** the idiomatic way (dependency factory, shared helper, Annotated alias) rather than copy-paste — but don't over-abstract things that merely look similar and will diverge.
- **Database**: Postgres (async via `asyncpg`); the app does not create its schema — Alembic migrations do. After changing a model, generate a migration (`uv run alembic revision --autogenerate -m "<message>"`) and review the generated file before applying it — autogenerate is not always complete.

## Known tech debt
- Login timing equalized on the dominant hash path but not fully constant-time. Noted.
- Pydantic 422 errors use `{"detail": ...}` while domain errors use `{"error": ...}` — minor shape inconsistency, not yet normalized.

## Working style
The human writes the code and wants review, problem-identification, and concept explanation — not generated fixes unless asked. (Applies to the review assistant; an execution agent may be directed to make changes directly.)
