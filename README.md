# NexusTeam - Secure Task Operations Platform

**[繁體中文](./README.zh-TW.md)** | **English**

[![GitHub](https://img.shields.io/badge/GitHub-HrdZvezda%2FNexusTask-blue?logo=github)](https://github.com/HrdZvezda/NexusTask)

NexusTeam is a full-stack collaboration suite that prioritizes backend resiliency, security, and clean architecture. The Flask API exposes modular blueprints backed by a service layer, caching, background jobs, realtime events, and structured observability, while the React client consumes the API through React Query and Socket.IO.

---

## Table of Contents

- [Overview](#overview)
- [Feature Highlights](#feature-highlights)
- [Architecture Snapshot](#architecture-snapshot)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Backend Capabilities](#backend-capabilities)
- [Frontend Experience](#frontend-experience)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Quick Start](#quick-start)
  - [Manual Setup](#manual-setup)
  - [Environment Variables](#environment-variables)
- [API Documentation & Health](#api-documentation--health)
- [Unified API Responses](#unified-api-responses)
- [Testing & Quality Gates](#testing--quality-gates)
- [Deployment Checklist](#deployment-checklist)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)
- [Maintainer](#maintainer)

## Overview

- Secure workspace for teams that need task orchestration, audit trails, realtime awareness, and governance.
- Backend follows SRP/OCP/LSP/DIP via dedicated services, repositories, cache managers, validators, DTOs, and `ServiceResult` responses.
- Operational tooling spans rate limiting, Redis-backed caching, Celery workers/beat, structured logging, Swagger docs, and multi-stage health probes.
- React + React Query deliver an optimistic, offline-friendly client with optional Socket.IO hooks that hydrate caches whenever servers push updates.

## Feature Highlights

**Security & Compliance**
- Configurable password policy (`PASSWORD_MIN_LENGTH`, uppercase/digit/special flags) plus bcrypt hashing and JWT access/refresh tokens.
- LoginAttempt audit log, IP-aware rate limiting, and automatic account lockout after repeated failures guard authentication flows.
- Forgot/reset password flow issues signed tokens, queues transactional emails via Celery, and periodically purges expired/used tokens.
- Security headers (CSP, HSTS, X-Frame-Options, Referrer-Policy), request-size caps, maintenance mode middleware, and sanitized error responses.

**Performance & Scalability**
- Composite indexes on Task (`idx_task_assigned_due`, `idx_task_project_priority`, `idx_task_project_assigned`) and Notification tables accelerate filtering.
- Pagination plus comment-count subqueries eliminate N+1 queries on `/projects/:id/tasks`, `/tasks/all`, and `/tasks/my`.
- CacheKeyManager + CacheTimeout enums centralize key formats and TTLs, while invalidate helpers clear user, project, and notification caches on writes.
- Redis stores cache entries, rate-limit counters, Celery messages, and Socket.IO session data for horizontal scalability.

**Collaboration & Automation**
- Celery handlers cover emails, notification fan-out, overdue reminders, project snapshot generation, and multiple cleanup routines; beat schedules run them daily.
- Flask-SocketIO publishes notification/task/member/comment events and tracks online users, typing indicators, and project rooms.
- Unified API response builder, DTOs, and service-level validators keep every endpoint predictable and testable.

**Operational Excellence**
- Health blueprint exposes `/health`, `/health/live`, `/health/ready`, `/health/detailed`, `/health/metrics`, and `/health/version` for load balancers and monitors.
- Structlog + python-json-logger integrate with rotating file handlers, per-request IDs, and request/response logging hooks.
- Swagger/OpenAPI (`/api/docs` + `/api/docs/swagger.json`) documents every blueprint with tags, schemas, error codes, and rate limit notes.

## Architecture Snapshot

Requests flow from the React client into modular Flask blueprints, through the service layer, and into repositories that coordinate SQLAlchemy, caching, and background queues. Redis powers rate limiting, Celery, and Socket.IO, while health probes and structured logs expose system state.

```
┌────────────── Frontend (React + React Query + Socket.IO) ──────────────┐
│ AuthProvider · QueryProvider · useApi/useSocket hooks                  │
└────────────────────────────┬───────────────────────────────────────────┘
                             │ HTTPS / WebSocket
┌────────────────────────────┴───────────────────────────────────────────┐
│         Backend (Flask Blueprints + Services + Core Infrastructure)    │
│  api/* blueprints  →  services/*Service  →  repositories/models        │
│  core/cache · core/celery_tasks · core/socket_events · utils/response │
└────────────────────────────┬───────────────────────────────────────────┘
                             │
                 PostgreSQL/SQLite · Redis · Celery Workers/Beat
```

## Tech Stack

### Frontend

| Layer | Technology | Purpose |
| --- | --- | --- |
| UI Framework | React 19 + TypeScript 5.8 | Component model + static typing |
| Routing | React Router 7 (HashRouter) | SPA routing without backend rewrites |
| Server State | @tanstack/react-query 5 | Fetching, caching, optimistic updates |
| Charts & Visualization | Recharts 3 | Dashboard metrics |
| Icons | lucide-react 0.554 | Lightweight icon set |
| Build Tooling | Vite 6 | Dev server, HMR, bundling |
| Realtime | socket.io-client 4.7 | WebSocket transport to Flask-SocketIO |

### Backend

| Layer | Technology | Purpose |
| --- | --- | --- |
| Web Framework | Flask 3 | Blueprints, middleware, CLI |
| Auth & Security | Flask-JWT-Extended, Flask-Bcrypt, Flask-Limiter | JWT issuance, hashing, rate limiting |
| ORM & DB | Flask-SQLAlchemy 3 (SQLAlchemy 2) | Models, migrations-by-code |
| Validation | Marshmallow 3 | DTO/schema validation |
| Cache & Messaging | Redis 5, Flask-Caching 2, Celery 5, APScheduler 3 | In-memory acceleration + async work |
| Realtime | Flask-SocketIO 5 + python-socketio 5 + eventlet | Push notifications and task streams |
| API Docs | Flasgger + flask-swagger-ui | Swagger UI + OpenAPI JSON |
| Observability | structlog, python-json-logger, RotatingFileHandler | Structured logs + file retention |

### Infrastructure & Tooling

| Need | Choice | Notes |
| --- | --- | --- |
| Local workflow | `.start/dev` script | Boots backend + frontend after venv/npm install |
| Testing | pytest, pytest-cov | Unit/integration coverage |
| Quality gates | black, flake8, mypy | Formatting, linting, typing |
| Deployment runtime | Gunicorn 21 (eventlet workers) | Production WSGI + WebSocket support |
| Data stores | SQLite (dev) / PostgreSQL (prod) | Configurable via `DATABASE_URL` |
| Messaging/cache | Redis 5 | Rate limiting, Celery broker/result, cache store |

## Project Structure

```
nexusteam/
├── backend/
│   ├── api/                        # Blueprints (auth, projects, tasks, notifications, members, uploads, health)
│   ├── core/                       # Cache, Celery tasks, middleware, socket events, Swagger config
│   │   └── token_blacklist.py      # JWT token revocation system (Redis/memory)
│   ├── services/                   # Service layer (BaseService, auth/project/task/notification services)
│   │   └── permissions.py          # Centralized permission checking (avoids circular imports)
│   ├── utils/                      # Utility functions
│   │   ├── response.py             # ApiResponse factory, ErrorCode enum, ResponseBuilder
│   │   └── validators.py           # Shared validation (Marshmallow, password, date, email, pagination)
│   ├── models.py                   # Shim to models_legacy (backwards compatibility)
│   ├── models_legacy.py            # SQLAlchemy models + indexes (LoginAttempt, PasswordResetToken, etc.)
│   ├── config.py                   # Environment-driven settings
│   ├── app.py                      # Flask entrypoint, middleware wiring, blueprints, health routes
│   ├── requirements.txt            # Backend dependencies
│   └── tests/                      # pytest suites for auth/projects/tasks/notifications/members/uploads/tags
├── frontend/
│   ├── App.tsx                     # Auth-aware router + QueryProvider + NotificationProvider
│   ├── hooks/useApi.ts             # React Query hooks + optimistic updates
│   ├── hooks/useSocket.ts          # Socket.IO helper + room helpers
│   ├── providers/QueryProvider.tsx # React Query client bootstrap
│   ├── context/AuthContext.tsx     # Auth session state
│   ├── context/NotificationContext.tsx # Shared notification state (Dashboard + Notifications sync)
│   └── components/pages/...        # UI modules
├── .start/dev                      # Convenience script to boot both apps
├── ARCHITECTURE.md                 # Comprehensive system architecture documentation (Chinese)
├── CODE_REVIEW.md                  # Code review report with recommendations
└── README.md
```

## Backend Capabilities

### Service Layer Flow
- `api/*.py` blueprints validate input, attach rate limits, and delegate work to `services/*.py`.
- Services inherit from `BaseService`, return `ServiceResult`, and can compose repositories, validators (`SchemaValidator`), and permission helpers.
- Repositories wrap SQLAlchemy models, while the `UnitOfWork` keeps transactions tight and rollback-safe.
- `utils/response.ApiResponse` and `ResponseBuilder` convert `ServiceResult` objects into the unified payload envelope (success/data/meta or error/code/details).
- Cache invalidation helpers (`invalidate_user_cache`, `invalidate_project_stats`, etc.) are triggered next to DB writes to keep Redis in sync.

### Security Pillars
- Password requirements, bcrypt hashing, and JWT access/refresh tokens are configurable per environment.
- **Token blacklist** (`core/token_blacklist.py`) ensures logout actually invalidates tokens via Redis (production) or in-memory storage (development).
- LoginAttempt records and limiter decorators enforce lockouts; `/auth/login`, `/auth/register`, and `/auth/forgot-password` have stricter rate limits.
- Password reset tokens map to users, expire within one hour, and are consumed by Celery email handlers before being marked used.
- Middleware stack injects CSP, HSTS (when TLS + not debug), frame/XSS protections, request IDs, maintenance-mode gatekeeping, and request-size enforcement.
- JWT callbacks centralize error handling (expired, invalid, revoked, missing) to keep responses predictable.
- **Centralized permission checking** (`services/permissions.py`) provides consistent access control without circular import issues.

### Performance & Reliability
- Pagination defaults (`DEFAULT_PAGE_SIZE`, `MAX_PAGE_SIZE`) protect heavy task endpoints; query args `page` and `per_page` are honored everywhere.
- Comment counts are fetched via a single subquery and joined back into task payloads to eliminate N+1 comment lookups.
- CacheKeyManager and CacheTimeout enums codify key formats and TTLs for users, project stats, notifications, and member rosters.
- Redis is the single source of truth for caches, rate limits, Socket.IO state, and Celery broker/result backends, enabling future horizontal scaling.
- Database indexes and SQLAlchemy `text` usage keep filtering/resorting cheap even for large tables.

### Realtime & Background Work
- `core/socket_events.py` authenticates sockets via JWT, tracks connected users, exposes join/leave project rooms, typing indicators, and emits events (`task_created`, `task_updated`, `notification`, etc.) in response to service events.
- `core/celery_tasks.py` defines handlers for emails, password resets, notification broadcasts, login attempt cleanup, password reset cleanup, notification cleanup, activity pruning, overdue reminders, and project stat snapshots.
- Celery beat schedule runs cleanup and snapshot tasks daily; commands exist for ad-hoc enqueues.
- APScheduler-ready abstractions allow migrating schedules or mixing cron-style jobs alongside Celery beat if needed.

### Observability & Operations
- Health blueprint returns liveness, readiness, dependency diagnostics (DB, Redis, cache), aggregate metrics (users/projects/tasks/notifications), and version metadata.
- Middleware logs each request/response with timing, attaches `X-Request-ID`, and skips noisy health routes.
- `setup_structured_logging` (optional) enables JSON logs compatible with ELK/Datadog when you prefer machine-readable telemetry.
- Rotating file handlers write `logs/app.log` and `logs/error.log` in production mode; `LOG_LEVEL` drives verbosity.
- Maintenance mode (`MAINTENANCE_MODE=true`) instantly returns 503 responses (except health endpoints) for deployments.

## Frontend Experience

- `App.tsx` wraps the router with `QueryProvider`, `AuthProvider`, and `NotificationProvider`, so every route enforces authentication via `ProtectedRoute`.
- **NotificationContext** provides shared notification state between Dashboard and Notifications pages, ensuring "mark all as read" actions sync instantly across views.
- React Query hooks (`useApi.ts`) centralize fetching, caching, pagination, and optimistic updates for projects, tasks, comments, notifications, and profile settings.
- **Dashboard Recent Activity** items are clickable and navigate directly to the related project page (with optional task deep-linking).
- `useSocket.ts` manages the Socket.IO client, joins project rooms, watches notifications/tasks/members/comments, handles typing indicators, and invalidates caches when realtime events arrive.
- Layout/components supply consistent navigation, dashboards, project boards, and personal task lists, while query hooks ensure data stays in sync with the backend.

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+ and npm (or Yarn)
- Redis 5+ (required for rate limiting, caching, Celery, and Socket.IO)
- PostgreSQL 14+ (optional; SQLite is the default dev DB)
- OpenSSL for TLS keys if running HTTPS locally

### Quick Start

```
./.start/dev
```

The helper script frees ports 8888/5173, activates `backend/venv`, starts `python app.py`, then runs `npm run dev`. The first run still requires you to create the virtual environment and install dependencies (see below).

### Manual Setup

#### Backend API

1. `cd backend`
2. `python -m venv venv`
3. `source venv/bin/activate`
4. `pip install -r requirements.txt`
5. Create a `.env` file (see [Environment Variables](#environment-variables)) or export the variables in your shell.
6. Initialize the database (tables are auto-created on boot via `db.create_all()`).
7. Start the API:

```
FLASK_DEBUG=true FLASK_PORT=8888 python app.py
# or: FLASK_DEBUG=true flask --app app run --port 8888
```

#### Celery Workers & Scheduler

Celery relies on the same `.env` and Redis settings:

```
cd backend
source venv/bin/activate
celery -A core.celery_tasks.celery worker --loglevel=info
celery -A core.celery_tasks.celery beat --loglevel=info
```

Workers handle email/notification/cleanup tasks; beat triggers the daily schedules defined in `core/celery_tasks.py`.

#### Frontend

```
cd frontend
npm install
npm run dev    # serves http://localhost:5173
```

Set `VITE_API_URL` in `frontend/.env.local` if the backend runs on a different origin.

#### Supporting Services

- Redis: `brew services start redis` (macOS) or `docker run --name nexusteam-redis -p 6379:6379 redis:7`.
- PostgreSQL (optional): update `DATABASE_URL=postgresql://user:pass@localhost:5432/nexusteam`.
- Email (optional): provide `MAIL_SERVER`, `MAIL_USERNAME`, and `MAIL_PASSWORD` to enable password reset emails.

### Environment Variables

| Variable | Default | Description |
| --- | --- | --- |
| `FLASK_ENV` | `development` | Flask environment (`development`, `testing`, `production`) |
| `FLASK_DEBUG` | `False` | Enables auto-reload + verbose errors |
| `SECRET_KEY` | `dev-secret-key...` | Flask session secret |
| `JWT_SECRET_KEY` | mirrors `SECRET_KEY` | JWT signing secret |
| `DATABASE_URL` | `sqlite:///task_manager.db` | SQLAlchemy connection string |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis for cache, limiter, Celery, Socket.IO |
| `CELERY_BROKER_URL` | `REDIS_URL` | Celery broker |
| `CELERY_RESULT_BACKEND` | `REDIS_URL` | Celery result backend |
| `ENABLE_RATE_LIMIT` | `false` | Force rate limiting even in dev |
| `PASSWORD_MIN_LENGTH` | `8` | Password length requirement |
| `PASSWORD_REQUIRE_UPPERCASE/NUMBERS/SPECIAL` | `False` | Extra password constraints |
| `JWT_ACCESS_TOKEN_EXPIRES_HOURS` | `1` | Access token lifetime |
| `JWT_REFRESH_TOKEN_EXPIRES_DAYS` | `30` | Refresh token lifetime |
| `MAX_CONTENT_LENGTH` | `16777216` | Upload size (bytes) |
| `MAIL_*` | none | SMTP settings for password reset emails |
| `LOG_LEVEL` | `INFO` | Logging level |
| `API_VERSION` | `2.1.0` | Surface in `/` and health endpoints |
| `MAINTENANCE_MODE` | `False` | Return 503 for non-health routes |

Example `.env`:

```
FLASK_ENV=development
FLASK_DEBUG=true
SECRET_KEY=replace-this
JWT_SECRET_KEY=replace-this-too
DATABASE_URL=sqlite:///task_manager.db
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=${REDIS_URL}
CELERY_RESULT_BACKEND=${REDIS_URL}
ENABLE_RATE_LIMIT=false
PASSWORD_MIN_LENGTH=10
PASSWORD_REQUIRE_UPPERCASE=true
PASSWORD_REQUIRE_NUMBERS=true
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your@email.com
MAIL_PASSWORD=app-specific-password
MAIL_DEFAULT_SENDER=noreply@nexusteam.local
```

## API Documentation & Health

- Swagger UI: `http://localhost:8888/api/docs`
- OpenAPI JSON: `http://localhost:8888/api/docs/swagger.json`

Health endpoints:

| Endpoint | Purpose |
| --- | --- |
| `/health` | Basic health + DB ping |
| `/health/live` | Liveness probe |
| `/health/ready` | Readiness (checks DB connectivity) |
| `/health/detailed` | Full dependency check (DB, Redis, cache) + system info |
| `/health/metrics` | Aggregated counts for users/projects/tasks/notifications |
| `/health/version` | Build metadata and API version |

All routes emit the unified response format and attach `X-Request-ID` plus rate-limit headers when enabled.

## Unified API Responses

`utils/response.py` enforces a single payload shape:

```
# Success
{
  "success": true,
  "data": {... domain payload ...},
  "meta": {
    "pagination": {
      "page": 1,
      "per_page": 20,
      "total": 125,
      "total_pages": 7,
      "has_next": true
    }
  }
}

# Error
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Title is required",
    "details": {"title": ["Missing data for required field."]}
  }
}
```

Each blueprint builds responses via `ResponseBuilder` and `ErrorCode` enums, making it easy for clients to handle success/error branches without per-endpoint special casing.

## Testing & Quality Gates

```
cd backend
source venv/bin/activate

# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=term-missing

# Linting / formatting / typing
black .
flake8 .
mypy .
```

Front-end tests are not yet wired; add Vitest/React Testing Library in the roadmap section before enabling CI gates.

## Deployment Checklist

- Build the frontend (`cd frontend && npm install && npm run build`) and serve the static assets (or deploy separately).
- Set `FLASK_ENV=production`, `ENABLE_RATE_LIMIT=true`, `MAINTENANCE_MODE=false`, and configure strong secrets.
- Use PostgreSQL in production by pointing `DATABASE_URL` to your cluster.
- Start the API with Gunicorn + eventlet workers to keep Socket.IO functional:

```
cd backend
source venv/bin/activate
gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:8888 app:app
```

- Run at least one Celery worker and one beat instance under Supervisor/systemd.
- Ensure Redis is reachable to power caching, rate limits, Socket.IO, and Celery.
- Wire structured logging to your log shipper (call `setup_structured_logging(app)` during startup or configure handlers).
- Monitor `/health/*` endpoints and rate-limit headers; alert on slow DB/Redis checks or 5xx spikes.
- Terminate TLS at your proxy/load balancer and keep HSTS enabled for HTTPS traffic.

## Roadmap

| Area | Status | Notes |
| --- | --- | --- |
| Realtime task & notification streaming | Done | Flask-SocketIO + `useSocket` hooks |
| Password policy + account lockout | Done | Config-driven + LoginAttempt audit |
| Automated cleanup & project snapshots | Done | Celery beat schedule (daily jobs) |
| **Token blacklist for secure logout** | **Done** | Redis/memory-backed revocation in `core/token_blacklist.py` |
| **Centralized permission system** | **Done** | `services/permissions.py` prevents circular imports |
| **Shared validators** | **Done** | `utils/validators.py` for Marshmallow, password, date, email |
| **Comprehensive documentation** | **Done** | `ARCHITECTURE.md` with detailed Chinese explanations |
| **Email/notification digests** | In progress | Provide SMTP creds + extend Celery handlers |
| **Notification state sync** | **Done** | `NotificationContext.tsx` syncs Dashboard ↔ Notifications |
| **Clickable activity items** | **Done** | Dashboard Recent Activity links to projects/tasks |
| Dark mode & responsive polish | Planned | Requires updated design tokens |
| Docker / Compose packaging | Planned | Containerize API, Redis, worker, frontend |
| CI/CD & frontend unit tests | Planned | Add Vitest + pipeline-wide quality gates |

## Contributing

1. Fork the repo.
2. Create a feature branch: `git checkout -b feature/my-change`.
3. Make your changes and include tests/lint fixes.
4. Run `pytest`, `black .`, `flake8`, and `mypy` before pushing.
5. Open a pull request with screenshots/logs for any user-facing changes.

## License

MIT License. See `LICENSE` for full terms.

## Maintainer

**Howard Li**

- Email: `HrdZvezda@gmail.com`
- GitHub: [@HrdZvezda](https://github.com/HrdZvezda)
