@echo off
uv run uvicorn backend.app.main:app --reload --reload-dir backend --port 8001
