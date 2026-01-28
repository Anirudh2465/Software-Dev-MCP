# Jarvis: The Digital Synapse

Jarvis is an intelligent agentic system designed to bridge the gap between Large Language Models (LLMs) and local machine capabilities using the **Model Context Protocol (MCP)**. It features a "Digital Synapse" for direct tool execution, a "Librarian" system for context-aware tool retrieval, an advanced **Agentic Memory** system, and a **Self-Evolution** engine for creating new tools.

## 🧠 Core Architecture

1.  **Orchestrator (Backend)**: built with **FastAPI**, serving as the central brain. It maintains the chat loop, manages conversation history (Episodic Memory), and connects the LLM (Local LM Studio) to local tools.
2.  **Frontend**: A modern Web UI built with **Next.js** and **Tailwind CSS**.
3.  **Task Queue**: **Celery** + **Redis** for background tool execution and heavy lifting.
4.  **Memory Vault**:
    *   **MongoDB (Semantic Memory)**: Stores permanent user facts.
    *   **ChromaDB (Episodic Memory)**: Stores conversation history for context retrieval.
    *   **Redis**: Caching and task brokerage.

---

## 🛠️ Prerequisites

Before you begin, ensure you have the following installed:

1.  **Docker Desktop** (Required for databases) - [Download](https://www.docker.com/products/docker-desktop/)
2.  **Python 3.12+** (Backend runtime)
3.  **uv** (Recommended Python package manager) - [Installation Guide](https://docs.astral.sh/uv/getting-started/installation/)
    *   *Alternative*: `pip` (standard).
4.  **Node.js 18+** & **npm** (Frontend runtime) - [Download](https://nodejs.org/)

---

## 🚀 Execution Instructions (From Scratch)

Follow these steps EXACTLY to run the system.

### 1. Start Infrastructure (Docker)
Launch the database services (MongoDB, ChromaDB, Redis).

```bash
# In the project root directory
docker compose up -d
```
*Wait for containers to be healthy.*

### 2. Backend Setup & Run

It is highly recommended to use `uv` for fast dependency management.

**A. Configure Environment**
Create a `.env` file in the **project root** directory (if not exists) and add your keys:
```ini
# Local LM Studio Configuration
LLM_API_BASE=http://localhost:1234/v1
LLM_MODEL=openai/local-model
LLM_API_KEY=lm-studio

# Database Configuration
REDIS_URL=redis://localhost:6379/0
MONGODB_URL=mongodb://localhost:27017/jarvis
CHROMA_DB_PATH=./data/chroma
```

**B. Install Dependencies**
```bash
# In the project root directory
uv sync
```

**C. Start Backend Server**
```bash
# In the project root directory
uv run uvicorn backend.app.main:app --reload --port 8001
```
*   Backend API will be running at: `http://localhost:8001`
*   API Docs: `http://localhost:8001/docs`

### 3. Start Background Worker (Celery)

The worker handles background tasks like tool validation and execution. Open a **new terminal**.

```bash
# In the project root directory
uv run celery -A backend.app.celery_app worker --loglevel=info --pool=solo
```
*Note for Windows users: `--pool=solo` is often required for Celery to work correctly.*

### 4. Frontend Setup & Run

Open a **new terminal**.

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```
*   Frontend will be accessible at: `http://localhost:3000`

---

## ✅ Verification

1.  Open `http://localhost:3000` in your browser.
2.  You should see the Chat Interface.
3.  Type "Hello" to check if the Backend is connected.
4.  If the backend is running, you will get a response from Jarvis.

---

## 📂 Troubleshooting

*   **Database Connection Failed**: Ensure Docker containers are running (`docker ps`).
*   **"Orchestrator not ready" error**: The backend server takes a moment to initialize the agent. Wait a few seconds after starting the backend.
*   **Celery Worker warnings**: If on Windows, ensure you used the `--pool=solo` flag.
*   **Frontend connection refused**: Ensure the backend is running on port `8000` and the frontend `.env` (if any) points to it.

---

## 🤝 Project Structure

*   `backend/`: FastAPI application and Python logic.
*   `frontend/`: Next.js web application.
*   `data/`: Persistent storage for databases (gitignored).
*   `docker-compose.yml`: Database orchestration.
