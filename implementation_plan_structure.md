# IMPLEMENTATION PLAN: Backend Restructuring

## Goal
Move all Python backend code into a structured `backend/` directory, following FastAPI best practices.

## Proposed Structure
```
jarvis/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI App instance & Middleware
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   └── routes.py        # /chat, /history, /mode
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   └── chat.py          # Pydantic models
│   │   └── services/
│   │       ├── __init__.py
│   │       ├── orchestrator.py  # JarvisOrchestrator class
│   │       ├── memory_manager.py
│   │       ├── tool_creator.py
│   │       ├── tool_indexer.py
│   │       └── verification_script.py (helpers)
│   ├── scripts/
│   │   └── filesystem_server.py # The MCP server script
│   ├── .env                     # Moved or copied? (Keep in root usually, but good for backend to have its own or load from root)
│   └── requirements.txt         # Specific to backend
├── frontend/ ...
└── README.md
```

## Migration Steps

1.  **Create Directories**: `backend/app/api`, `backend/app/schemas`, `backend/app/services`, `backend/scripts`.
2.  **Move & Refactor Files**:
    - `backend_api.py` -> `backend/app/main.py` + `backend/app/api/routes.py`
    - `orchestrator.py` -> `backend/app/services/orchestrator.py` (Update `SERVER_SCRIPT` path!)
    - `memory_manager.py` -> `backend/app/services/memory_manager.py`
    - `tool_creator.py` -> `backend/app/services/tool_creator.py`
    - `filesystem_server.py` -> `backend/scripts/filesystem_server.py`
3.  **Update Imports**:
    - Fix relative imports in `services/orchestrator.py`.
    - Fix imports in `main.py`.
4.  **Verification**:
    - Run `uvicorn app.main:app --reload` from `backend/` directory.
    - Test `/health` and `/chat`.

## Critical implementation Detail
`orchestrator.py` uses `subprocess` to run `filesystem_server.py`.
Old code: `SERVER_SCRIPT = "filesystem_server.py"`
New code: Needs absolute path or relative path from `orchestrator.py` to `../../scripts/filesystem_server.py`.
Best approach: Use `Path(__file__).parent.parent.parent / 'scripts' / 'filesystem_server.py'`.
