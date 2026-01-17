# Jarvis: The Digital Synapse

Jarvis is an intelligent agentic system designed to bridge the gap between Large Language Models (LLMs) and local machine capabilities using the **Model Context Protocol (MCP)**. It features a "Digital Synapse" for direct tool execution, a "Librarian" system for context-aware tool retrieval, and an advanced **Agentic Memory** system.

## 🧠 Core Architecture

1.  **Orchestrator (`orchestrator.py`)**: The central brain. It maintains the chat loop, manages conversation history (Episodic Memory), and connects the LLM (Gemini) to local tools.
2.  **MCP Server (`filesystem_server.py`)**: A standardized server built with `FastMCP` that exposes local filesystem operations.
3.  **The Librarian (RAG)**: Uses **ChromaDB** to semantically search and retrieve relevant tools.
4.  **Memory Vault**: 
    - **MongoDB (Semantic Memory)**: Stores permanent user facts (e.g., "User prefers dark mode").
    - **ChromaDB (Episodic Memory)**: Stores conversation history for context retrieval.

## 🛠️ Prerequisites

-   **Docker Desktop**: Required for running MongoDB and ChromaDB.
-   **Python 3.12+**
-   **uv** (Recommended) or **pip**: For dependency management.

## 🚀 Installation & Setup

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd jarvis
```

### 2. Environment Setup

**Option A: Using `uv` (Recommended)**
```bash
# Initialize and sync dependencies
uv sync
```

**Option B: Using `pip`**
```bash
python -m venv .venv
# Activate venv:
# Windows: .venv\Scripts\activate
# Linux/Mac: source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Configure Secrets
Create a `.env` file in the root directory and add your Google Gemini API key:
```ini
GEMINI_API_KEY=your_api_key_here
```

### 4. Start Infrastructure
Launch the database services (MongoDB & ChromaDB) using Docker:
```bash
docker compose up -d
```
*   **MongoDB**: `localhost:27017`
*   **ChromaDB**: `localhost:8000`

## ✅ Verification & Initialization

Before running the agent, verify your setup:

1.  **Verify Connections**:
    ```bash
    uv run verification_script.py
    # OR
    python verification_script.py
    ```

2.  **Populate Tool Index (The Librarian)**:
    Run this **once** to index the dummy tools.
    ```bash
    uv run tool_indexer.py
    # OR
    python tool_indexer.py
    ```

3.  **Verify Memory System (Optional)**:
    ```bash
    uv run test_phase4.py
    ```

## 🎮 How to Run "Jarvis"

Start the agent:
```bash
uv run orchestrator.py
# OR
python orchestrator.py
```

### Feature Usage Guide

#### 1. Agentic Memory ("Who am I?")
Jarvis remembers facts about you across sessions.
-   **Tell Jarvis a fact**: "I am a Python developer living in Seattle."
-   **Ask about it later**: "Where do I live?" (Even after restarting the agent).

#### 2. Mode Switching
Control Jarvis's personality and context using modes.
-   **Work Mode** (Default): Focuses on productivity and work-related facts.
-   **Personal Mode**: Focuses on personal interests and casual conversation.
-   **Switching**: 
    -   *User*: "Switch to Personal mod."
    -   *Jarvis*: "Mode switched to: Personal"

#### 3. Standard Tools
-   **Filesystem**: "List files in the current directory."
-   **RAG Retrieval**: "Add a meeting to my calendar." (retrieves relevant calendar tools).

## 📂 Troubleshooting

-   **Database Connection Errors**: Ensure Docker Desktop is running and containers are up (`docker ps`).
-   **Import Errors**: Ensure you have installed dependencies (`uv sync` or `pip install -r requirements.txt`).
-   **API Key Error**: Double-check your `.env` file.
