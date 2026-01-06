# Repository Guidelines

## Project Structure & Module Organization
`app/` holds the FastAPI backend (routers in `app/api/`, config/security in `app/core/`, ORM models in `app/models/`, Pydantic schemas in `app/schemas/`, and migrations in `app/db/migrations/`). `frontend/` contains the React + Vite UI (`frontend/src/` for components, pages, and API clients). Root files like `docker-compose.yml`, `Dockerfile`, and `alembic.ini` define runtime and migration setup.

## Build, Test, and Development Commands
- `docker-compose up -d`: start PostgreSQL and the backend API.
- `docker-compose logs -f backend`: tail backend logs.
- `docker-compose down`: stop services.
- `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`: run backend locally (requires PostgreSQL).
- `alembic revision --autogenerate -m "desc"` / `alembic upgrade head`: create and apply migrations.
- `python -m app.scripts.create_admin`: seed an admin user.
- `cd frontend && npm install`: install frontend dependencies.
- `cd frontend && npm run dev`: start Vite dev server (proxies `/api` to `localhost:8000`).
- `cd frontend && npm run build` / `npm run lint`: build or lint the UI.

## Coding Style & Naming Conventions
Python uses 4-space indentation, type hints, and async SQLAlchemy patterns (`select()`, `AsyncSession`). Frontend code uses 2-space indentation, functional React components, and Ant Design UI. Follow existing file naming and module boundaries; new API routes should live under `app/api/` and corresponding schemas under `app/schemas/`.

## Testing Guidelines
Automated tests are not currently configured. If you add tests, keep them close to the domain (e.g., `app/tests/` or `frontend/src/__tests__/`) and document how to run them. For now, verify API changes via `/docs` and UI changes via the Vite dev server.

## Commit & Pull Request Guidelines
The git history only contains an “Initial commit”, so there is no established commit convention. Use concise, imperative messages (e.g., “Add entity version endpoint”). PRs should include a clear description of changes, key commands run (if any), and screenshots for UI changes.

## Configuration & Secrets
Copy `.env.example` to `.env` for local settings. Avoid committing secrets; configure `DATABASE_URL` and `JWT_SECRET` via environment variables or `.env` for development.
