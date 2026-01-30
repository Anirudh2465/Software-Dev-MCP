@echo off
REM Start Docker containers first and wait for them to be ready
echo Starting Docker containers...
docker compose up -d
REM Wait a few seconds for database to be ready for connections
timeout /t 5

REM Start Frontend
start "Frontend" cmd /k "call .venv\Scripts\activate && uv sync && cd frontend && npm install && npm run dev"

REM Start Backend
start "Backend" cmd /k "call .venv\Scripts\activate && lms server start && uv run uvicorn backend.app.main:app --reload --reload-dir backend --port 8001"

REM Start Celery Worker
start "Celery Worker" cmd /k "call .venv\Scripts\activate && uv run celery -A backend.app.celery_app worker --loglevel=info --pool=solo"
