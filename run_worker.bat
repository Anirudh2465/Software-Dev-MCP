@echo off
cd backend
uv run celery -A app.celery_app worker --loglevel=info --pool=solo
