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
from .memory_manager import EpisodicMemory, SemanticMemory
from .tool_creator import ToolCreator
from .document_manager import DocumentManager
from .chat_service import ChatService
from ..prompts import get_persona_prompt
import re

# ... [imports]



BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
SERVER_SCRIPT = BASE_DIR / "backend" / "scripts" / "filesystem_server.py"
TOOLS_DIR = BASE_DIR / "tools"
TOOL_DEFINITIONS_FILE = BASE_DIR / "tool_definitions.json"

CHROMA_HOST = "localhost"
CHROMA_PORT = 8000

class PromptManager:
    def __init__(self, semantic_memory):
        self.mode = "Work" # Default mode
        self.persona = "Generalist" # Default persona
        self.semantic_memory = semantic_memory
    
    def set_mode(self, mode):
        if mode in ["Work", "Personal"]:
            self.mode = mode
            return f"Mode switched to: {mode}"
        return f"Invalid mode. Available: Work, Personal"

    def set_persona(self, persona):
        from ..prompts import PERSONAS
        if persona in PERSONAS:
            self.persona = persona
            return f"Persona switched to: {persona}"
        return f"Invalid persona. Available: {list(PERSONAS.keys())}"

    def get_system_prompt(self, user_id="default"):
        relevant_facts = []
        # Strict isolation: Only get facts for the current mode
        relevant_facts.extend(self.semantic_memory.get_all_facts(mode=self.mode, user_id=user_id))
        
        relevant_facts = list(set([f['fact'] for f in relevant_facts])) # Extract fact strings

        prompt = f"""
{get_persona_prompt(self.persona)}

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

[SCRATCHPAD]
Waiting for input...
"""
        return prompt

class JarvisOrchestrator:
    def __init__(self):
        self.episodic_memory = EpisodicMemory()
        self.semantic_memory = SemanticMemory()
        self.chat_service = ChatService()
        self.prompt_manager = PromptManager(self.semantic_memory)
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

    def _sanitize_response(self, text):
        """
        Removes raw model tokens or tags (e.g. <|start|>, <|message|>) that might leak into the output.
        """
        if not text:
            return ""
        # Remove <|...|> patterns
        cleaned = re.sub(r"<\|.*?\|>", "", text)
        return cleaned.strip()

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
            for msg in chat_doc.get("messages", []):
                current_history.append({"role": msg["role"], "content": msg["content"]})
        else:
            # Fallback (should have been created via API)
            print(f"Warning: Chat {chat_id} not found locally, creating ephemeral context")

        # Add episodic context (Partitioned by MODE and USER)
        relevant_episodes = self.episodic_memory.search_episodes(user_input, mode=current_mode, n=2, user_id=user_id)
        
        # DOCUMENT SEARCH (RAG)
        relevant_docs = self.document_manager.search_documents(user_input)
        
        context_msg = ""
        if relevant_episodes:
             context_msg = f"\n[Historical Context (May be outdated) in {current_mode} mode]:\n" + "\n".join(relevant_episodes)
             
        if relevant_docs:
             context_msg += f"\n[Document Context]:\n" + "\n".join(relevant_docs)
        
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

        # Dynamic Retrieval from ChromaDB
        # We NO LONGER append all self.dynamic_tool_definitions
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
                
        else:
            # Fallback if DB is down: load everything to be safe, or just helpers?
            # User accepted "create them" if missing, so maybe just helpers is risky.
            # But "fallback" implies something went wrong. Let's dump everything so it still works.
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
                            "parameters": tool.inputSchema
                        }
                    } 
                    for tool in mcp_tools_list.tools
                ])
            except Exception as e:
                print(f"Error listing MCP tools: {e}")

        try:
            response = completion(
                model=os.getenv("LLM_MODEL", "openai/local-model"),
                api_base=os.getenv("LLM_API_BASE", "http://localhost:1234/v1"),
                api_key=os.getenv("LLM_API_KEY", "lm-studio"),
                messages=payload_messages,
                tools=current_tool_definitions,
            )
            response_message = response.choices[0].message
        except Exception as e:
            return f"Error calling LLM: {e}"

        # Note: We don't append to self.messages anymore
        
        if response_message.tool_calls:
            print(f"\n[Tool Call Detected]: {response_message.tool_calls[0].function.name}")
            
            # Temporary list to hold this turn's tool interaction
            # We need to construct a new payload because 'payload_messages' already has the user input
            # We need to append the ASSISTANT's tool_call message, then the TOOL results.
            
            payload_messages.append(response_message) # Add assistant's tool call

            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                function_args = eval(tool_call.function.arguments) 
                
                result_content = ""
                
                if function_name == "save_fact":
                    print(f"Executing INTERNAL tool: {function_name}")
                    # Default to current mode if not specified
                    target_mode = function_args.get("mode", current_mode)
                    result_content = self.semantic_memory.save_fact(function_args["fact"], mode=target_mode, user_id=user_id)
                    
                elif function_name == "set_mode":
                    print(f"Executing INTERNAL tool: {function_name}")
                    result_content = self.prompt_manager.set_mode(function_args["mode"])
                    
                elif function_name == "delete_mode":
                    print(f"Executing INTERNAL tool: {function_name}")
                    mode_del = function_args["mode"]
                    # Delete from Mongo and Pinecone
                    sem_del = self.semantic_memory.delete_mode(mode_del, user_id=user_id)
                    epi_del = self.episodic_memory.delete_mode_memory(mode_del, user_id=user_id)
                    result_content = f"Deleted mode '{mode_del}' for user {user_id}. Semantic: {sem_del}, Episodic: {epi_del}"
                    if self.prompt_manager.mode == mode_del:
                        self.prompt_manager.set_mode("Work") # Fallback
                        result_content += ". Switched to 'Work'."

                elif function_name == "switch_persona":
                    print(f"Executing INTERNAL tool: {function_name}")
                    result_content = self.prompt_manager.set_persona(function_args["persona"])
                
                elif function_name in ["read_pdf", "read_docx", "read_image", "read_text_file", "read_file"]:
                    print(f"Executing INTERNAL tool: {function_name}")
                    # All file tools map to the unified ingest_file method
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
                             # Make it available immediately for the follow-up response
                             if self.dynamic_tool_definitions:
                                 current_tool_definitions.append(self.dynamic_tool_definitions[-1])
                    else:
                        result_content = str(result)
                        
                elif function_name in self.dynamic_tools:
                    print(f"Executing DYNAMIC tool: {function_name}")
                    try:
                        func = self.dynamic_tools[function_name]
                        # Assume func takes kwargs matching the args
                        result_content = str(func(**function_args))
                    except Exception as e:
                        result_content = f"Error executing tool {function_name}: {e}"

                elif function_name in self.real_tool_names:
                    print(f"Executing REAL tool: {function_name}")
                    result = await self.session.call_tool(function_name, function_args)
                    result_content = str(result.content)
                else:
                    print(f"Simulating MOCK tool: {function_name}")
                    result_content = f"Mock success: {function_name} executed with {function_args}"
                
                payload_messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result_content
                })
            
            # Final Follow-up Response
            # Note: If mode changed mid-tools, prompts should reflect new mode?
            # Ideally re-fetch prompt.
            payload_messages[0] = {"role": "system", "content": self.prompt_manager.get_system_prompt(user_id=user_id)}
            
            second_response = completion(
                model=os.getenv("LLM_MODEL", "openai/local-model"),
                api_base=os.getenv("LLM_API_BASE", "http://localhost:1234/v1"),
                api_key=os.getenv("LLM_API_KEY", "lm-studio"),
                messages=payload_messages,
            )
            final_message = second_response.choices[0].message
            final_text = self._sanitize_response(final_message.content)
            print(f"Jarvis: {final_text}")
            
            # Save Episodic Memory (Partitioned)
            self.episodic_memory.add_episode(
                content=f"User: {user_input}\nJarvis: {final_text}",
                mode=self.prompt_manager.mode,
                user_id=user_id
            )
            
            # Save Assistant Response to DB
            self.chat_service.add_message(chat_id, user_id, "assistant", final_text)
            
            return final_text
        
        else:
            final_text = self._sanitize_response(response_message.content)
            print(f"Jarvis: {final_text}")
            self.episodic_memory.add_episode(
                content=f"User: {user_input}\nJarvis: {final_text}",
                mode=self.prompt_manager.mode,
                user_id=user_id
            )
            # Save Assistant Response to DB
            self.chat_service.add_message(chat_id, user_id, "assistant", final_text)

            return final_text
