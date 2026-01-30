import asyncio
import os
import sys
import json
import chromadb
import importlib.util
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from litellm import completion
from pathlib import Path
from .memory_manager import EpisodicMemory, SemanticMemory, ModeManager, ToneManager
from .tool_creator import ToolCreator
from .document_manager import DocumentManager
from .chat_service import ChatService
from ..prompts import get_persona_prompt, generate_tone_prompt_template, DEFAULT_TONES

# ... [imports]



BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
SERVER_SCRIPT = BASE_DIR / "backend" / "scripts" / "filesystem_server.py"
TOOLS_DIR = BASE_DIR / "tools"
TOOL_DEFINITIONS_FILE = BASE_DIR / "tool_definitions.json"

CHROMA_HOST = "localhost"
CHROMA_PORT = 8000

class PromptManager:
    def __init__(self, semantic_memory, mode_manager, tone_manager):
        self.mode = "Work" # Default mode
        self.persona = "Generalist" # Default persona
        self.tone = "Professional" # Default tone
        self.semantic_memory = semantic_memory
        self.mode_manager = mode_manager
        self.tone_manager = tone_manager
    
    def set_mode(self, mode):
        # Check against DB modes
        mode_doc = self.mode_manager.get_mode(mode)
        if mode_doc:
            self.mode = mode
            return f"Mode switched to: {mode}"
        return f"Invalid mode. Available: {', '.join([m['name'] for m in self.mode_manager.get_all_modes()])}"

    def set_persona(self, persona):
        from ..prompts import PERSONAS
        if persona in PERSONAS:
            self.persona = persona
            return f"Persona switched to: {persona}"
        return f"Invalid persona. Available: {list(PERSONAS.keys())}"

    def set_tone(self, tone):
        # Check against DB
        tone_doc = self.tone_manager.get_tone(tone)
        if tone_doc:
            self.tone = tone
            return f"Tone switched to: {tone}"
        # Check defaults if DB fails?
        if tone in DEFAULT_TONES:
             self.tone = tone
             return f"Tone switched to: {tone} (Default)"
             
        return f"Invalid tone. Available: {', '.join([t['name'] for t in self.tone_manager.get_all_tones()])}"

    def get_system_prompt(self, user_id="default"):
        relevant_facts = []
        # Strict isolation: Only get facts for the current mode
        relevant_facts.extend(self.semantic_memory.get_all_facts(mode=self.mode, user_id=user_id))
        
        relevant_facts = list(set([f['fact'] for f in relevant_facts])) # Extract fact strings

        # Get Tone Prompt
        tone_doc = self.tone_manager.get_tone(self.tone)
        if tone_doc:
             tone_prompt = generate_tone_prompt_template(tone_doc["name"], tone_doc["description"])
        else:
             tone_prompt = DEFAULT_TONES.get(self.tone, DEFAULT_TONES["Professional"])

        prompt = f"""
{get_persona_prompt(self.persona)}

{tone_prompt}

[CURRENT_MODE]
Current Mode: {self.mode}
(In Work mode, focus on productivity and technical tasks. In Personal mode, be more casual and focus on personal interests.)

[RELEVANT_MEMORIES ({self.mode})]
{chr(10).join("- " + f for f in relevant_facts) if relevant_facts else "No relevant memories found."}

[INSTRUCTIONS]
1. You have access to local tools and memory.
2. You MUST use the <thinking> tag to plan your actions step-by-step before executing ANY tools.
3. If a complex request requires multiple steps, outline them in your thinking block.
4. "Who am I?" questions should count on the memories provided above.
5. [RELEVANT_MEMORIES] is the ONLY source of truth for active facts. If a fact is not listed there, do not consider it a current memory, even if it appears in [Historical Context].
6. Use 'save_fact' to remember important user details. Use 'edit_memory' if the user explicitly corrects a past fact.

[SCRATCHPAD]
Waiting for input...
"""
        return prompt

class JarvisOrchestrator:
    def __init__(self):
        self.episodic_memory = EpisodicMemory()
        self.semantic_memory = SemanticMemory()
        self.mode_manager = ModeManager()
        self.tone_manager = ToneManager()
        self.chat_service = ChatService()
        self.prompt_manager = PromptManager(self.semantic_memory, self.mode_manager, self.tone_manager)
        self.tool_creator = ToolCreator()
        self.document_manager = DocumentManager()
        self.tool_collection = None
        self.session = None
        self.read_stream = None
        self.write_stream = None
        self.exit_stack = None
        # self.messages = [] # REMOVED: History is now stateless per request
        self.real_tool_names = set()
        self.helper_tools = self._define_internal_tools()
        self.dynamic_tools = {} # Registry for hot-loaded tools
        self.dynamic_tool_definitions = [] # Definitions for hot-loaded tools
        
        # Initialize Tool DB Client
        try:
            print("Connecting to ChromaDB for Tools...")
            self.chroma_client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
            self.tool_collection = self.chroma_client.get_or_create_collection("tools")
            print("Connected to ChromaDB 'tools' collection.")
        except Exception as e:
            print(f"Warning: Could not connect to ChromaDB for tools: {e}")
            self.tool_collection = None
            
        self._load_all_existing_tools()

    def _load_all_existing_tools(self):
        """
        Loads all tools defined in tool_definitions.json on startup and indexes them.
        """
        if not TOOL_DEFINITIONS_FILE.exists():
            print("Warning: tool_definitions.json not found.", flush=True)
            return

        try:
            with open(TOOL_DEFINITIONS_FILE, "r") as f:
                defs = json.load(f)
            
            for tool_def in defs:
                name = tool_def["name"]
                filename = tool_def["filename"]
                file_path = TOOLS_DIR / filename
                
                if not file_path.exists():
                    print(f"Warning: Tool file {file_path} not found for {name}", flush=True)
                    continue
                    
                # Load module
                try:
                    spec = importlib.util.spec_from_file_location(name, str(file_path))
                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        
                        if hasattr(module, name):
                            func = getattr(module, name)
                            self.dynamic_tools[name] = func
                            
                            # Add definition
                            tool_definition_struct = {
                                "type": "function",
                                "function": {
                                    "name": name,
                                    "description": tool_def["description"],
                                    "parameters": tool_def["inputSchema"]
                                }
                            }
                            self.dynamic_tool_definitions.append(tool_definition_struct)
                            
                            # Index in ChromaDB
                            if self.tool_collection:
                                try:
                                    # Use description + name as document content
                                    doc_content = f"{name}: {tool_def['description']}"
                                    self.tool_collection.upsert(
                                        ids=[name],
                                        documents=[doc_content],
                                        metadatas=[{"json": json.dumps(tool_def)}]
                                    )
                                    print(f"DEBUG: Indexed tool '{name}' in ChromaDB", flush=True)
                                except Exception as idx_err:
                                    print(f"Error indexing tool {name}: {idx_err}", flush=True)
                                    
                            print(f"DEBUG: Loaded existing tool '{name}'", flush=True)
                        else:
                            print(f"Error: Function {name} not found in {filename}", flush=True)
                except Exception as e:
                    print(f"Error loading tool {name}: {e}", flush=True)
                    
        except Exception as e:
            print(f"Error reading tool definitions: {e}", flush=True)

    def _define_internal_tools(self):
        return [
            {
                "type": "function",
                "function": {
                    "name": "save_fact",
                    "description": "Save a permanent fact about the user.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "fact": {"type": "string"},
                            "mode": {"type": "string", "description": "The mode to save this fact to (defaults to current)."}
                        },
                        "required": ["fact"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "edit_memory",
                    "description": "Update an existing memory/fact about the user.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "old_content": {"type": "string", "description": "The old fact content to search for (partial match allowed)."},
                            "new_content": {"type": "string", "description": "The new content to replace it with."}
                        },
                        "required": ["old_content", "new_content"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "set_mode",
                    "description": "Switch the agent's mode.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "mode": {"type": "string", "enum": ["Work", "Personal"]}
                        },
                        "required": ["mode"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_tool",
                    "description": "REQUIRED: Use this tool to create new python tools for any missing capability. DO NOT write code in the chat response; call this tool instead.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "tool_name": {"type": "string", "description": "Snake_case name of the tool"},
                            "description": {"type": "string", "description": "Detailed description of what the tool should do."}
                        },
                        "required": ["tool_name", "description"]
                    }
                }
            },

             {
                "type": "function",
                "function": {
                    "name": "delete_mode",
                    "description": "Delete a mode and all associated memory.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "mode": {"type": "string"}
                        },
                        "required": ["mode"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "switch_persona",
                    "description": "Switch the agent's persona (role).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "persona": {"type": "string", "enum": ["Generalist", "Coder", "Architect", "Sentinel"]}
                        },
                        "required": ["persona"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "read_pdf",
                    "description": "Read and index a PDF file to extract text for querying.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string", "description": "Absolute path to the PDF file."}
                        },
                        "required": ["file_path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "read_docx",
                    "description": "Read and index a Word document (.docx) to extract text/tables for querying.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string", "description": "Absolute path to the .docx file."}
                        },
                        "required": ["file_path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "read_image",
                    "description": "Read and index text from an image (OCR). Supports PNG, JPG, BMP.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string", "description": "Absolute path to the image file."}
                        },
                        "required": ["file_path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "read_text_file",
                    "description": "Read and index a plain text or code file (txt, md, py, js, etc.).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string", "description": "Absolute path to the file."}
                        },
                        "required": ["file_path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_new_mode",
                    "description": "Create a new mode with specific allowed tools.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "Name of the new mode (e.g. 'Coding', 'Research')"},
                            "description": {"type": "string", "description": "Description of what this mode is for."},
                            "allowed_tools": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of tool names allowed in this mode. Use ['*'] for all tools."
                            }
                        },
                        "required": ["name", "description", "allowed_tools"]
                    }
                }
            }
        ]

    def _load_dynamic_tool(self, tool_name, file_path):
        """
        Dynamically loads a tool from a file path and registers it.
        """
        try:
            spec = importlib.util.spec_from_file_location(tool_name, file_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                if hasattr(module, tool_name):
                    func = getattr(module, tool_name)
                    self.dynamic_tools[tool_name] = func
                    
                    # Update definitions
                    # We read the file from disk to get the definition
                    # The tool_creator saves it to tool_definitions.json
                    # We can find it there.
                    try:
                        defs_path = TOOL_DEFINITIONS_FILE
                        if defs_path.exists():
                            with open(defs_path, "r") as f:
                                defs = json.load(f)
                                for d in defs:
                                    if d["name"] == tool_name:
                                        # Check if already exists to avoid duplicates
                                        if not any(td["function"]["name"] == tool_name for td in self.dynamic_tool_definitions):
                                            self.dynamic_tool_definitions.append({
                                                "type": "function",
                                                "function": {
                                                    "name": d["name"],
                                                    "description": d["description"],
                                                    "parameters": d["inputSchema"]
                                                }
                                            })
                                        break
                    except Exception as ex:
                        print(f"Error loading definition for {tool_name}: {ex}")

                    print(f"DEBUG: Dynamically loaded tool '{tool_name}'")
                    return True
        except Exception as e:
            print(f"Error loading dynamic tool {tool_name}: {e}")
            return False
        return False

    async def start(self):
        print("DEBUG: Starting Jarvis Orchestrator...", flush=True)
        # ChromaDB client is now initialized in __init__
        
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        server_params = StdioServerParameters(
            command=sys.executable,
            args=[str(SERVER_SCRIPT)], 
            env=env, 
        )

        from contextlib import AsyncExitStack
        self.exit_stack = AsyncExitStack()
        
        stdio_ctx = stdio_client(server_params)
        self.read_stream, self.write_stream = await self.exit_stack.enter_async_context(stdio_ctx)
        
        self.session = ClientSession(self.read_stream, self.write_stream)
        await self.exit_stack.enter_async_context(self.session)
        
        await self.session.initialize()
        
        mcp_tools_list = await self.session.list_tools()
        self.real_tool_names = {t.name for t in mcp_tools_list.tools}
        print(f"Connected to MCP Server. Real tools: {list(self.real_tool_names)}")

    async def stop(self):
        if self.exit_stack:
            await self.exit_stack.aclose()

    async def process_message(self, user_input: str, user_id: str, chat_id: str):
        # Update System Prompt Dynamically
        current_mode = self.prompt_manager.mode
        system_prompt = self.prompt_manager.get_system_prompt(user_id=user_id)
        
        system_prompt += """
[TOOL_CREATION]
If you lack a specific tool to fulfill a request (e.g., specific file conversion, any calculation, data processing), you MUST use 'create_tool' to build it.
DO NOT provide Python code snippets to start unless explicitly asked.
DO NOT calculate manually or simulate the result.
Always prefer expanding your capabilities by creating a reusable tool.
After creating a tool, it will be auto-loaded and available immediately.
"""
        
        # 1. Fetch Chat History (STATELESS)
        chat_doc = self.chat_service.get_chat(chat_id, user_id)
        current_history = []
        if chat_doc:
            # Convert DB messages to LLM format
            raw_msgs = chat_doc.get("messages", [])
            
            # --- CONTEXT MANAGEMENT: LIMIT HISTORY ---
            # Keep only last 10 messages to avoid overflow
            MAX_HISTORY = 2
            if len(raw_msgs) > MAX_HISTORY:
                raw_msgs = raw_msgs[-MAX_HISTORY:]
            
            for msg in raw_msgs:
                current_history.append({"role": msg["role"], "content": msg["content"]})
            
            # --- FEATURE: Dynamic Chat Naming & Proactive Tool Loading ---
            # If this is the FIRST message in the chat (check original length)
            if len(chat_doc.get("messages", [])) == 0:
                # 1. Generate Title
                await self._generate_chat_title(user_input, chat_id, user_id)
                # 2. Suggest Tools (Wait for it so we can use it in this turn)
                suggested_tools = await self._suggest_tools(user_input, chat_id, user_id)
                # Update local doc reference for this run
                chat_doc["suggested_tools"] = suggested_tools
        else:
            # Fallback (should have been created via API)
            print(f"Warning: Chat {chat_id} not found locally, creating ephemeral context")
            # Create it implicitly if missing? For now just log.

        # Add episodic context (Partitioned by MODE and USER)
        relevant_episodes = self.episodic_memory.search_episodes(user_input, mode=current_mode, n=2, user_id=user_id)
        
        # DOCUMENT SEARCH (RAG)
        relevant_docs = self.document_manager.search_documents(user_input)
        
        context_msg = ""
        
        # --- CONTEXT MANAGEMENT: TRUNCATE RAG ---
        MAX_CONTEXT_CHARS = 2000
        
        if relevant_episodes:
             episodes_str = "\n".join(relevant_episodes)
             if len(episodes_str) > MAX_CONTEXT_CHARS:
                 episodes_str = episodes_str[:MAX_CONTEXT_CHARS] + "...[TRUNCATED]"
             context_msg = f"\n[Historical Context (May be outdated) in {current_mode} mode]:\n" + episodes_str
             
        if relevant_docs:
             docs_str = "\n".join(relevant_docs)
             if len(docs_str) > MAX_CONTEXT_CHARS:
                 docs_str = docs_str[:MAX_CONTEXT_CHARS] + "...[TRUNCATED]"
             context_msg += f"\n[Document Context]:\n" + docs_str
        
        # STATE REMINDER: Force priority of Semantic Memory over Chat History
        # We re-fetch facts to ensure we have the absolute latest state
        active_facts = self.semantic_memory.get_all_facts(mode=current_mode, user_id=user_id)
        fact_strings = [f['fact'] for f in active_facts]
        
        state_reminder = f"""
\n[SYSTEM STATE REMINDER]
The following are the ONLY active facts. Ignore any conflicting information in the chat history above.
Active Memories:
{chr(10).join("- " + f for f in fact_strings) if fact_strings else "(No active memories)"}
"""

        payload_messages = [{"role": "system", "content": system_prompt}] + current_history
        # Append reminder to the User's input so it is the last thing the model sees
        payload_messages.append({"role": "user", "content": user_input + context_msg + state_reminder})

        # Save USER message to DB immediately (Without the hidden prompts)
        self.chat_service.add_message(chat_id, user_id, "user", user_input)

        # Tool Definitions
        # Start with core helper tools (create_tool, save_fact, etc.)
        current_tool_definitions = self.helper_tools.copy()

        # --- MODE RESTRICTION LOGIC ---
        mode_doc = self.mode_manager.get_mode(current_mode)
        allowed_tools = mode_doc.get("allowed_tools", ["*"]) if mode_doc else ["*"]
        
        # If not wild card, filter base helpers
        if "*" not in allowed_tools:
            # We ALWAYS allow 'set_mode', 'create_new_mode' to avoid locking out, 
            # and maybe 'save_fact'? Let's trust the configured list but force criticals.
            critical_tools = ["set_mode", "create_new_mode", "create_tool"] 
            # Only keep tools that are in allowed list OR critical
            current_tool_definitions = [
                t for t in current_tool_definitions 
                if t["function"]["name"] in allowed_tools or t["function"]["name"] in critical_tools
            ]

        # Dynamic Retrieval from ChromaDB
        if self.tool_collection is not None:
            print(f"DEBUG: Retrieving tools for query: '{user_input}'")
            try:
                results = self.tool_collection.query(
                    query_texts=[user_input],
                    n_results=5 # Retrieve top 5 relevant tools
                )
                
                if results['ids'] and results['ids'][0]:
                    print(f"DEBUG: Retrieved tools: {results['ids'][0]}")
                    for i, json_str in enumerate(results['metadatas'][0]):
                        try:
                            tool_def = json.loads(json_str['json'])
                            # Ensure we don't duplicate if it's somehow already in helpers (unlikely)
                            if not any(t['function']['name'] == tool_def['name'] for t in current_tool_definitions):
                                # FILTER DYNAMIC TOOLS TOO
                                if "*" in allowed_tools or tool_def["name"] in allowed_tools:
                                    current_tool_definitions.append({
                                        "type": "function",
                                        "function": {
                                            "name": tool_def["name"],
                                            "description": tool_def["description"],
                                            "parameters": tool_def["inputSchema"]
                                        }
                                    })
                        except Exception as e:
                            print(f"Error parsing tool metadata: {e}")
            except Exception as e:
                print(f"Error querying tools: {e}")
        
        # --- FEATURE: Proactive Tool Loading (Suggested Tools) ---
        if chat_doc and "suggested_tools" in chat_doc:
            print(f"DEBUG: Loading suggested tools: {chat_doc['suggested_tools']}")
            for tool_name in chat_doc["suggested_tools"]:
                # Check dynamic tools
                if tool_name in self.dynamic_tools:
                     # Find definition
                     t_def = next((alert for alert in self.dynamic_tool_definitions if alert["function"]["name"] == tool_name), None)
                     if t_def and not any(t['function']['name'] == tool_name for t in current_tool_definitions):
                         current_tool_definitions.append(t_def)
                # Check real MCP tools (handled below in MCP block? No, MCP tools not in definition list yet)
                # We handle MCP below.
                
        else:
            print("Warning: Tool DB unavailable, falling back to ALL tools.")
            current_tool_definitions.extend(self.dynamic_tool_definitions)

        # Add MCP tools (if any)
        if self.session:
            try:
                mcp_tools_list = await self.session.list_tools()
                current_tool_definitions.extend([
                    {
                        "type": "function",
                        "function": {
                            "name": tool.name,
                            "description": tool.description,
                        }
                    } 
                    for tool in mcp_tools_list.tools
                    if "*" in allowed_tools or tool.name in allowed_tools 
                ])
            except Exception as e:
                print(f"Error listing MCP tools: {e}")

        # --- MULTI-TURN EXECUTION LOOP ---
        final_text = ""
        MAX_TURNS = 20  # Increased to allow for complex multi-step tasks (e.g. create tool -> gen data -> process)
        turn_count = 0

        while turn_count < MAX_TURNS:
            turn_count += 1
            print(f"DEBUG: Turn {turn_count}/{MAX_TURNS}")
            
            # ... [Existing loop body] ...
            # I need to match the indentation and structure of the loop body content I'm *not* changing,
            # but replace_file_content requires exact match or complete replacement.
            # To avoid large replace blocks, I will do this in two steps or simply replace the loop set up 
            # and then the post-loop handling.
            
            # Actually, standard replace_file_content works on contiguous blocks.
            # I will target the variable init and the WHILE line first.

            turn_count += 1
            print(f"DEBUG: Turn {turn_count}/{MAX_TURNS}")

            try:
                # Force tools to be available in every turn
                response = completion(
                    model=os.getenv("LLM_MODEL", "openai/local-model"),
                    api_base=os.getenv("LLM_API_BASE", "http://localhost:1234/v1"),
                    api_key=os.getenv("LLM_API_KEY", "lm-studio"),
                    messages=payload_messages,
                    tools=current_tool_definitions if current_tool_definitions else None,
                )
                response_message = response.choices[0].message
            except Exception as e:
                return f"Error calling LLM: {e}"

            # Append the Assistant's response (content or tool call) to history
            # Explicitly convert to dict to avoid Pydantic serialization warnings/issues
            msg_dict = {"role": response_message.role, "content": response_message.content}
            if response_message.tool_calls:
                 msg_dict["tool_calls"] = [
                     {
                         "id": tc.id, 
                         "type": tc.type, 
                         "function": {
                             "name": tc.function.name, 
                             "arguments": tc.function.arguments
                         }
                     }
                     for tc in response_message.tool_calls
                 ]
            payload_messages.append(msg_dict)

            if response_message.tool_calls:
                print(f"\n[Tool Call Detected]: {response_message.tool_calls[0].function.name}")
                
                for tool_call in response_message.tool_calls:
                    function_name = tool_call.function.name
                    try:
                        function_args = json.loads(tool_call.function.arguments)
                    except json.JSONDecodeError:
                        print(f"Error parsing arguments for {function_name}: {tool_call.function.arguments}")
                        function_args = {} 
                    
                    result_content = ""
                    
                    if function_name == "save_fact":
                        print(f"Executing INTERNAL tool: {function_name}")
                        target_mode = function_args.get("mode", current_mode)
                        result_content = self.semantic_memory.save_fact(function_args["fact"], mode=target_mode, user_id=user_id)

                    elif function_name == "edit_memory":
                        print(f"Executing INTERNAL tool: {function_name}")
                        old_content = function_args.get("old_content")
                        new_content = function_args.get("new_content")
                        
                        # Search for candidates
                        candidates = self.semantic_memory.search_facts(old_content, mode=current_mode, user_id=user_id)
                        
                        if not candidates:
                             result_content = f"No memory found matching '{old_content}' in {current_mode} mode."
                        elif len(candidates) == 1:
                             success = self.semantic_memory.update_fact(candidates[0]['id'], new_content)
                             result_content = f"Memory updated: '{candidates[0]['fact']}' -> '{new_content}'" if success else "Error updating memory."
                        else:
                             # Multiple matches
                             result_content = f"Multiple memories found matching '{old_content}'. Please be more specific. Matches: " + ", ".join([f"'{c['fact']}'" for c in candidates])

                    elif function_name == "set_mode":
                        print(f"Executing INTERNAL tool: {function_name}")
                        result_content = self.prompt_manager.set_mode(function_args["mode"])
                        # Determine if we need to update system prompt for next turn?
                        # For simplicity, we keep current prompt but the tool result says mode changed.
                        
                    elif function_name == "delete_mode":
                        print(f"Executing INTERNAL tool: {function_name}")
                        mode_del = function_args["mode"]
                        sem_del = self.semantic_memory.delete_mode(mode_del, user_id=user_id)
                        epi_del = self.episodic_memory.delete_mode_memory(mode_del, user_id=user_id)
                        result_content = f"Deleted mode '{mode_del}' for user {user_id}. Semantic: {sem_del}, Episodic: {epi_del}"
                        if self.prompt_manager.mode == mode_del:
                            self.prompt_manager.set_mode("Work")
                            result_content += ". Switched to 'Work'."

                    elif function_name == "switch_persona":
                        print(f"Executing INTERNAL tool: {function_name}")
                        result_content = self.prompt_manager.set_persona(function_args["persona"])
                    
                    elif function_name in ["read_pdf", "read_docx", "read_image", "read_text_file", "read_file"]:
                        print(f"Executing INTERNAL tool: {function_name}")
                        result_content = self.document_manager.ingest_file(function_args["file_path"])
                            
                    elif function_name == "create_tool":
                        print(f"Executing CREATION tool: {function_name}")
                        result = self.tool_creator.create_tool(function_args["tool_name"], function_args["description"])
                        
                        if isinstance(result, dict) and result.get("status") == "success":
                            result_content = result["message"]
                            tool_name_created = result["tool_name"]
                            file_path = result["file_path"]
                            
                            # Dynamic Load
                            if self._load_dynamic_tool(tool_name_created, file_path):
                                 result_content += f"\nTool '{tool_name_created}' hot-loaded and ready."
                                 # UPDATE current_tool_definitions for the next turn
                                 if self.dynamic_tool_definitions:
                                     # Append the most recently added definition
                                     # We need to find the specific one we just added to be safe
                                     new_def = next((d for d in self.dynamic_tool_definitions if d['function']['name'] == tool_name_created), None)
                                     if new_def:
                                         current_tool_definitions.append(new_def)
                        else:
                            result_content = str(result)
                            
                    elif function_name in self.dynamic_tools:
                        print(f"Executing DYNAMIC tool: {function_name}")
                        try:
                            func = self.dynamic_tools[function_name]
                            result_content = str(func(**function_args))
                        except Exception as e:
                            result_content = f"Error executing tool {function_name}: {e}"

                    elif function_name in self.real_tool_names:
                        print(f"Executing REAL tool: {function_name}")
                        result = await self.session.call_tool(function_name, function_args)
                        result_content = str(result.content)
                        
                    elif function_name == "create_new_mode":
                        print(f"Executing INTERNAL tool: {function_name}")
                        res = self.mode_manager.create_mode(
                            function_args["name"], 
                            function_args.get("description", ""), 
                            function_args.get("allowed_tools", ["*"])
                        )
                        result_content = str(res)

                    else:
                        print(f"Simulating MOCK tool: {function_name}")
                        result_content = f"Mock success: {function_name} executed with {function_args}"

                    # Add Tool Result to History
                    payload_messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result_content
                    })
                
                # Loop continues to next turn to generate response based on tool results
            
            else:
                # No tool calls -> Final Answer
                final_text = response_message.content
                print(f"Jarvis: {final_text}")
                break

        # Post-Loop Fallback: If loop finished but no final text (e.g. max turns reached on a tool call)
        if not final_text:
            print("DEBUG: Max turns reached or loop exited without final text. Generating summary...")
            try:
                # Force a final response based on the accumulated history
                response = completion(
                    model=os.getenv("LLM_MODEL", "openai/local-model"),
                    api_base=os.getenv("LLM_API_BASE", "http://localhost:1234/v1"),
                    api_key=os.getenv("LLM_API_KEY", "lm-studio"),
                    messages=payload_messages,
                    # No tools this time, just want a text response
                )
                final_text = response.choices[0].message.content
                print(f"Jarvis (Fallback): {final_text}")
            except Exception as e:
                final_text = f"Error generating final response: {e}"

        # Post-Loop Logging and Saving
        
        # Save Episodic Memory
        self.episodic_memory.add_episode(
            content=f"User: {user_input}\nJarvis: {final_text}",
            mode=self.prompt_manager.mode,
            user_id=user_id
        )
        
        # Save Assistant Response to DB
        self.chat_service.add_message(chat_id, user_id, "assistant", final_text)

        return final_text

    async def _generate_chat_title(self, first_message, chat_id, user_id):
        print("DEBUG: Generating chat title...")
        try:
            response = completion(
                model=os.getenv("LLM_MODEL", "openai/local-model"),
                api_base=os.getenv("LLM_API_BASE", "http://localhost:1234/v1"),
                api_key=os.getenv("LLM_API_KEY", "lm-studio"),
                messages=[
                    {"role": "system", "content": "You are a helpful assistant. Generate a concise title (3-5 words) for this chat based on the user's first message. Return ONLY the title, no quotes."},
                    {"role": "user", "content": first_message}
                ]
            )
            title = response.choices[0].message.content.strip().replace('"', '')
            self.chat_service.update_chat_title(chat_id, user_id, title)
            print(f"DEBUG: Set chat title to '{title}'")
        except Exception as e:
            print(f"Error generating chat title: {e}")

    async def _suggest_tools(self, first_message, chat_id, user_id):
        print("DEBUG: Analyzing for proactive tools...")
        try:
             # Get all available tool names
            all_tool_names = list(self.dynamic_tools.keys()) + list(self.real_tool_names)
            
            prompt = f"""
You are an intelligent orchestrator. The user has just started a chat with this request:
"{first_message}"

Available Tools: {', '.join(all_tool_names)}

Which of these tools are HIGHLY LIKELY to be needed for this request?
Return a JSON array of tool names. Example: ["read_pdf", "calculator"].
If no specific tools are needed, return [].
Do NOT explain. Return ONLY JSON.
"""
            response = completion(
                model=os.getenv("LLM_MODEL", "openai/local-model"),
                api_base=os.getenv("LLM_API_BASE", "http://localhost:1234/v1"),
                api_key=os.getenv("LLM_API_KEY", "lm-studio"),
                messages=[{"role": "user", "content": prompt}]
            )
            content = response.choices[0].message.content
            # Cleanup code blocks if any
            if "```" in content:
                content = content.split("```")[1].replace("json", "").strip()
            
            tools = json.loads(content)
            if isinstance(tools, list):
                 self.chat_service.update_chat_field(chat_id, user_id, "suggested_tools", tools)
                 print(f"DEBUG: Suggested tools: {tools}")
                 return tools
            return []
        except Exception as e:
            print(f"Error suggesting tools: {e}")
            return []
