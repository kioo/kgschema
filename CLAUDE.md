# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Knowledge Graph Schema Management System - A full-stack application for managing entity and relation schemas with versioning and audit capabilities.

**Tech Stack:**
- Backend: FastAPI + SQLAlchemy 2.0 (async) + Alembic + PostgreSQL
- Frontend: React 19 + TypeScript + Vite + Ant Design + TanStack Query
- Auth: JWT (python-jose) with Bearer token authentication

## Common Commands

### Backend Development

```bash
# Start all services (PostgreSQL + backend)
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down

# Run backend directly (requires PostgreSQL running)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Create and apply database migrations
alembic revision --autogenerate -m "description"
alembic upgrade head

# Rollback migration
alembic downgrade -1

# Create admin user
python -m app.scripts.create_admin
```

### Frontend Development

```bash
cd frontend
npm install          # Install dependencies
npm run dev          # Start dev server (proxies /api to localhost:8000)
npm run build        # Production build
npm run lint         # Run ESLint
```

### Testing

```bash
# Backend (pytest not currently configured - add to requirements.txt if needed)
pytest

# Frontend tests (not currently configured)
cd frontend && npm test
```

## Architecture

### Backend Structure

```
app/
├── main.py              # FastAPI app entry point, CORS middleware
├── api/                 # Route handlers (auth, health, users)
├── core/
│   ├── config.py        # Pydantic-settings for env vars
│   ├── deps.py          # FastAPI dependencies (CurrentUser, CurrentAdmin, DbSession)
│   └── security.py      # JWT utilities, password hashing (bcrypt)
├── models/              # SQLAlchemy ORM models
│   ├── base.py          # Base, UUIDMixin, TimestampMixin
│   ├── entity.py        # Entity, EntityProperty
│   ├── relation.py      # Relation, RelationProperty
│   ├── user.py          # User model
│   ├── version.py       # SchemaVersion
│   └── audit.py         # AuditLog
├── schemas/             # Pydantic models for request/response
├── db/
│   ├── session.py       # Async engine and session factory
│   └── migrations/      # Alembic migrations (app/db/migrations/versions/)
└── services/            # Business logic layer (currently sparse)
```

### Key Architecture Patterns

**Async/Await Everywhere**: All database operations use SQLAlchemy async with `AsyncSession`. Use `db.get(Model, id)` for simple fetches, or construct queries with `select(Model)`.

**Dependency Injection**: FastAPI dependencies in [core/deps.py](app/core/deps.py) provide:
- `DbSession` - Async database session with auto-commit/rollback
- `CurrentUser` - Authenticated user from JWT Bearer token
- `CurrentAdmin` - Requires admin role

**Model Mixins**: All models inherit from `UUIDMixin` (UUID primary key) and `TimestampMixin` (created_at, updated_at). Defined in [models/base.py](app/models/base.py).

**Schema Versioning**: The system supports publishing schema versions with snapshots stored as JSONB. See [models/version.py](app/models/version.py).

**Audit Logging**: All mutations should create AuditLog entries with batch_id for grouping related changes. See [models/audit.py](app/models/audit.py).

### Frontend Structure

```
frontend/src/
├── main.tsx             # Entry point
├── App.tsx              # Root component
├── api/                 # API client functions (axios)
├── components/          # Reusable components
├── pages/               # Page components
└── lib/                 # Utilities
```

**Vite Proxy**: Dev server proxies `/api` to `localhost:8000` - see [vite.config.ts](frontend/vite.config.ts).

**Data Fetching**: Uses TanStack Query for server state management.

## Environment Variables

Backend uses [pydantic-settings](app/core/config.py) - copy [`.env.example`](.env.example) to `.env`:

```bash
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/kgschema
JWT_SECRET=change-this-in-production
DEBUG=true
```

## Database

**Connection**: PostgreSQL 15+ on port 5433 (mapped from 5432 in Docker).

**Alembic Config**: Migrations location is `app/db/migrations`. Use `alembic.ini` for configuration.

**Initial Schema**: See [001_initial.py](app/db/migrations/versions/001_initial.py) for complete table definitions including entities, relations, versions, and audit logs.

## Authentication Flow

1. POST `/api/v1/auth/login` with `{username, password}` returns `{access_token, refresh_token}`
2. Include `Authorization: Bearer <access_token>` header for protected routes
3. Tokens are JWT HS256 signed with `JWT_SECRET`
4. Access tokens expire in 30 minutes, refresh tokens in 7 days

## Code Conventions

- **Python**: Python 3.11+, use type hints consistently
- **SQLAlchemy**: Use async API, 2.0 style (`select()`, `session.get()`)
- **FastAPI**: Use Annotated dependencies (`DbSession`, `CurrentUser`)
- **Frontend**: Functional components with hooks, Ant Design for UI

## Pending Implementation

The API router placeholder comments in [api/__init__.py](app/api/__init__.py) indicate these modules are not yet implemented:
- Entities CRUD (`/api/v1/entities`)
- Relations CRUD (`/api/v1/relations`)
- Schema versions (`/api/v1/versions`)
- Audit logs (`/api/v1/audit`)
- Import/Export (Excel upload/download)
