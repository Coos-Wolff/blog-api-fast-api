# Blog API (FastAPI)

An async RESTful blog post API built with FastAPI, SQLAlchemy 2.x (async), and PostgreSQL (async via asyncpg), with JWT authentication (access + refresh tokens) and author/admin ownership rules. This is a port of an equivalent Flask API, rebuilt on FastAPI's async stack.

## Stack

- **FastAPI** — async web framework
- **SQLAlchemy 2.x (async)** — ORM, via `asyncpg` for async PostgreSQL
- **Pydantic v2** — request/response schemas and validation
- **PyJWT** — JWT creation/verification
- **bcrypt** — password hashing
- **pydantic-settings** — typed configuration from the environment
- **[uv](https://docs.astral.sh/uv/)** — dependency management and virtual environments
- **hatchling** — build backend (`src` layout)

## Getting Started

### 1. Install uv

See [uv's installation guide](https://docs.astral.sh/uv/getting-started/installation/).

### 2. Install dependencies

```bash
uv sync
```

Creates a `.venv` and installs the locked dependency versions from `uv.lock`.

### 3. Configure environment variables

```bash
cp .env.example .env
```

Set the values in `.env`:

- `DATABASE_URL` — async Postgres URL, e.g. `postgresql+asyncpg://blog:blog@localhost:5432/blogdb`
- `JWT_SECRET_KEY` — signing key for JWTs (generate with `python -c "import secrets; print(secrets.token_hex(32))"`)
- `APP_ENV`, `DEBUG` — environment name and debug flag

Optional (have defaults): `JWT_ALGORITHM` (HS256), `ACCESS_TOKEN_EXPIRE_MINUTES` (15), `REFRESH_TOKEN_EXPIRE_DAYS` (30).

### 4. Start Postgres

```bash
docker compose up -d
```

Starts the Postgres container defined in `docker-compose.yaml`.

### 5. Apply database migrations

```bash
uv run alembic upgrade head
```

Creates the schema. The app does not create tables on startup.

### 6. Run

```bash
uv run uvicorn app.main:app --reload --port 5003
```

The API serves at `http://localhost:5003`. Interactive docs (auto-generated) are at `http://localhost:5003/docs`.

## Authentication

Stateless JWT via `Authorization: Bearer <token>`. Two token types:

- **Access token** — short-lived, sent on every protected request.
- **Refresh token** — long-lived, used only at `/auth/refresh` to obtain a new access token.

The two are not interchangeable: a protected route rejects a refresh token, and `/auth/refresh` rejects an access token (enforced by the token's `type` claim).

Flow:

1. `POST /auth/register` to create a user, then `POST /auth/login` for an `access_token` + `refresh_token`.
2. Send the access token as `Authorization: Bearer <access_token>` on protected routes.
3. When it expires (401 with "Token expired"), `POST /auth/refresh` with the refresh token to get a new access token.

Mutating a post (`PATCH`/`DELETE`) requires being its author **or** an admin (`is_admin`, provisioned manually — no self-service admin signup). Authorship is always taken from the token, never the request body.

## API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/auth/register` | — | Create a user account (201) |
| `POST` | `/auth/login` | — | Log in; returns access + refresh tokens |
| `POST` | `/auth/refresh` | Bearer (refresh token) | Exchange a refresh token for a new access token |
| `GET` | `/post/` | — | List posts, paginated, newest-first |
| `GET` | `/post/{id}` | — | Get a single post |
| `POST` | `/post/add` | Bearer (access) | Create a post (201) |
| `PATCH` | `/post/{id}` | Bearer + owner/admin | Update fields on a post |
| `DELETE` | `/post/{id}` | Bearer + owner/admin | Delete a post (204) |

### `GET /post/` query parameters

| Param | Default | Description |
|-------|---------|-------------|
| `page` | `1` | Page number |
| `per_page` | `5` | Results per page |

Returns `items`, `total`, `page`, `per_page`, `total_pages`.

### Request bodies

`POST /auth/register`:
```json
{ "email": "jane@example.com", "name": "Jane Doe", "password": "a-strong-password" }
```

`POST /auth/login`:
```json
{ "email": "jane@example.com", "password": "a-strong-password" }
```

`POST /post/add` (author taken from the token, not the body):
```json
{ "title": "My First Post", "subtitle": "A brief intro", "date": "2026-06-30", "body": "Content.", "img_url": "https://example.com/image.jpg" }
```

`PATCH /post/{id}` — any subset of `title`, `subtitle`, `body`, `date`, `img_url`; omitted fields are unchanged.

## Error Responses

Domain errors return `{"error": "message"}` with an appropriate status. FastAPI request-validation failures return `422` in Pydantic's default `{"detail": [...]}` shape.

| Status | Meaning |
|--------|---------|
| `400` | Bad input surfaced as a `ValueError` |
| `401` | Not authenticated (missing/invalid/expired token; bad credentials) |
| `403` | Authenticated but not the post's author or an admin |
| `404` | Resource not found |
| `409` | Conflict (duplicate email or post title) |
| `422` | Request-body/param validation failure (Pydantic) |

## Project Structure

```
src/app/
├── main.py            # FastAPI app, lifespan, router + handler registration
├── config.py          # pydantic-settings Settings, loaded from .env
├── base.py            # SQLAlchemy DeclarativeBase (foundation, imports nothing of app)
├── database.py        # async engine, session factory, get_db dependency, SessionDependency
├── models.py          # SQLAlchemy models (User, BlogPost)
├── security.py        # auth primitives: hash/verify password, create/decode JWT
├── auth.py            # token-type dependency factory + CurrentUserDependency / RefreshUserDependency
├── repository.py      # async DB access (reads with selectinload, writes with commit/refresh)
├── service.py         # business logic; raises domain exceptions; builds Pydantic responses
├── exceptions.py      # domain exception classes
├── exception_handlers.py  # maps domain exceptions -> status codes (registered in main)
├── schemas/           # Pydantic schemas (post, user, auth)
└── routers/           # APIRouters (post, auth)
```

## Architecture

Layered: **router → service → repository**, with the session injected top-down via `Depends(get_db)`.

- **Routers** translate HTTP: declare typed params (path, query, body via Pydantic), inject session/current-user via dependencies, call the service, return the result. `response_model` drives serialization. No business logic.
- **Services** own business logic and rules; async; take `session` as a parameter; raise domain exceptions; build typed Pydantic response objects. No HTTP knowledge.
- **Repositories** own all async DB access. Reads eager-load the `author` relationship (`selectinload`) since responses serialize it. Writes commit and refresh. Transaction rollback is centralized in `get_db`.
