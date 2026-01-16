# Jarvis: The Digital Synapse

Jarvis is an intelligent agentic system designed to bridge the gap between Large Language Models (LLMs) and local machine capabilities using the **Model Context Protocol (MCP)**. It features a "Digital Synapse" for direct tool execution and a "Librarian" system for context-aware tool retrieval.

## 🧠 Core Architecture

1.  **Orchestrator (`orchestrator.py`)**: The central brain. It maintains the chat loop, manages conversation history, and connects the LLM (Gemini) to local tools.
2.  **MCP Server (`filesystem_server.py`)**: A standardized server built with `FastMCP` that exposes local filesystem operations (`read`, `write`, `list`) to the Orchestrator.
3.  **The Librarian (RAG)**: Uses **ChromaDB** to semantically search and retrieve only the most relevant tools for a user's query, preventing context window overload.
4.  **Memory Vault**: Uses **MongoDB** (upcoming) and **ChromaDB** for persistent data storage.

## 🛠️ Prerequisites

-   **Docker Desktop**: For running MongoDB and ChromaDB services.
-   **Python 3.12+**
-   **uv**: An extremely fast Python package and project manager.

## 🚀 Installation & Setup

### 1. Install `uv`
If you haven't installed `uv` yet, use one of the following commands:

**Windows (PowerShell):**
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Linux / macOS:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Project Setup
Navigate to the project directory:
```bash
cd jarvis
```

### 3. Environment Setup
We use `uv` to manage the virtual environment and dependencies. This ensures a reproducible environment across all platforms.

**Initialize and Sync (Windows & Linux):**
This command creates the virtual environment (`.venv`) and installs all dependencies lock-file.
```bash
uv sync
```

**Activating the Virtual Environment (Optional):**
While `uv run <script>` automatically uses the environment, you can activate it manually if you prefer.

*   **Windows:**
    ```powershell
    .venv\Scripts\activate
    ```
*   **Linux / macOS:**
    ```bash
    source .venv/bin/activate
    ```

### 4. Configure Secrets
Create a `.env` file in the root directory and add your Google Gemini API key:
```ini
GEMINI_API_KEY=your_api_key_here
```

### 5. Start Infrastructure
Launch the database services (MongoDB & ChromaDB) using Docker:
```bash
docker compose up -d
```
*   **MongoDB**: `localhost:27017`
*   **ChromaDB**: `localhost:8000`

## 📂 Code Files & Usage Guide

Here is a breakdown of the core files and how to run them.

| File | Description | Command to Run |
| :--- | :--- | :--- |
| **`verification_script.py`** | Verifies connectivity to MongoDB and ChromaDB. Run this first to ensure your infrastructure is ready. | `uv run verification_script.py` |
| **`tool_indexer.py`** | **(Phase 2)** Reads `dummy_tools.json` and indexes them into ChromaDB. Run this **once** to populate the "Librarian". | `uv run tool_indexer.py` |
| **`dummy_tools.json`** | A simulated dataset of 100+ tools (Calendar, Spotify, etc.) used for testing dynamic retrieval. | *Data file, not executable* |
| **`filesystem_server.py`** | The MCP server exposing `list_directory`, `read_file`, and `write_file`. | *Started automatically by Orchestrator* |
| **`orchestrator.py`** | **The Main App**. Connects to Gemini, queries The Librarian (ChromaDB), and executes tools via MCP. | `uv run orchestrator.py` |

## 🎮 How to Run "Jarvis"

1.  **Start Databases**:
    ```bash
    docker compose up -d
    ```

2.  **Populate Knowledge Base (The Librarian)**:
    ```bash
    uv run tool_indexer.py
    ```
    *You should see "Successfully indexed..." output.*

3.  **Run the Agent**:
    ```bash
    uv run orchestrator.py
    ```

4.  **Interact**:
    *   **Test local tools**: *"What's in my 'Notes' folder?"*
    *   **Test RAG Retrieval**: *"Add a meeting with John tomorrow."* (Use this to verify it finds calendar tools and ignores music tools).
