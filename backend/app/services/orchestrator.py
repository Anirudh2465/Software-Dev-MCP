import asyncio
import os
import sys
import json
import chromadb
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from litellm import completion
from pathlib import Path
from .memory_manager import EpisodicMemory, SemanticMemory
from .tool_creator import ToolCreator

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
SERVER_SCRIPT = BASE_DIR / "backend" / "scripts" / "filesystem_server.py"

CHROMA_HOST = "localhost"
CHROMA_PORT = 8000

class PromptManager:
    def __init__(self, semantic_memory):
        self.mode = "Work" # Default mode
        self.semantic_memory = semantic_memory
    
    def set_mode(self, mode):
        # Allow any mode, but verify if it exists or just switch to it (implicitly creating it)
        # For better UX, we might want to ensure it exists or confirm creation. 
        # But here flexible is better.
        self.mode = mode
        return f"Mode switched to: {mode}"

    def get_system_prompt(self):
        relevant_facts = self.semantic_memory.get_all_facts(mode=self.mode) # Replaced 'category' with 'mode'
        relevant_facts = list(set(relevant_facts))

        prompt = f"""
[PERSONALITY]
You are Jarvis, an intelligent system designed to be helpful, precise, and context-aware.

[CURRENT_MODE]
Current Mode: {self.mode}
(Focus your responses and tool usage according to this mode context.)

[RELEVANT_MEMORIES ({self.mode})]
{chr(10).join("- " + f for f in relevant_facts) if relevant_facts else "No relevant memories found."}

[INSTRUCTIONS]
1. You have access to local tools and memory.
2. You MUST use the <thinking> tag to plan your actions step-by-step before executing ANY tools.
3. If a complex request requires multiple steps, outline them in your thinking block.
4. "Who am I?" questions should count on the memories provided above.

[SCRATCHPAD]
Waiting for input...
"""
        return prompt

class JarvisOrchestrator:
    def __init__(self):
        self.episodic_memory = EpisodicMemory()
        self.semantic_memory = SemanticMemory()
        self.prompt_manager = PromptManager(self.semantic_memory)
        self.tool_creator = ToolCreator()
        self.tool_collection = None
        self.session = None
        self.read_stream = None
        self.write_stream = None
        self.exit_stack = None
        self.messages = []
        self.real_tool_names = set()
        self.helper_tools = self._define_internal_tools()

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
                            "mode": {"type": "string", "description": "Name of the mode to switch to."}
                        },
                        "required": ["mode"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_tool",
                    "description": "Create a new Python tool for a missing capability. Generates code, validates in Docker, and registers it.",
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
            }
        ]

    async def start(self):
        print("DEBUG: Starting Jarvis Orchestrator...", flush=True)
        # Connect to ChromaDB for TOOLS (Librarian) - keeping this local for now or could move to Pinecone too.
        # User request was specifically for "memory" (episodic/semantic) separation.
        # Tools are global capabilities usually.
        try:
            chroma_client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
            self.tool_collection = chroma_client.get_collection("tools")
            print("Connected to ChromaDB 'tools' collection.")
        except Exception as e:
            print(f"Warning: Could not connect to ChromaDB for tools: {e}")
            self.tool_collection = None

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

    async def process_message(self, user_input: str):
        # Update System Prompt Dynamically
        current_mode = self.prompt_manager.mode
        system_prompt = self.prompt_manager.get_system_prompt()
        
        system_prompt += """
[TOOL_CREATION]
If you lack a specific tool to fulfill a request (e.g., specific file conversion, calculation), use 'create_tool' to build it.
After creating a tool, you may need to ask the user to 'reload' or just wait for the next turn for it to be available (in this prototype).
"""
        
        current_history = [m for m in self.messages if m["role"] != "system"]
        
        # Add episodic context (Partitioned by MODE)
        relevant_episodes = self.episodic_memory.search_episodes(user_input, mode=current_mode, n=2)
        context_msg = ""
        if relevant_episodes:
             context_msg = f"\n[Relevant past conversations in {current_mode} mode]:\n" + "\n".join(relevant_episodes)
        
        payload_messages = [{"role": "system", "content": system_prompt}] + current_history
        payload_messages.append({"role": "user", "content": user_input + context_msg})

        # Tool Definitions
        current_tool_definitions = self.helper_tools.copy()

        # Dynamic Retrieval from ChromaDB
        if self.tool_collection is not None:
            results = self.tool_collection.query(
                query_texts=[user_input],
                n_results=3 
            )
            for meta in results['metadatas'][0]:
                tool_def = json.loads(meta['json'])
                current_tool_definitions.append({
                    "type": "function",
                    "function": {
                        "name": tool_def["name"],
                        "description": tool_def["description"],
                        "parameters": tool_def["inputSchema"]
                    }
                })
        else:
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

        try:
            response = completion(
                model="openai/local-model",
                api_base="http://127.0.0.1:1234/v1",
                api_key="lm-studio",
                messages=payload_messages,
                tools=current_tool_definitions,
            )
            response_message = response.choices[0].message
        except Exception as e:
            return f"Error calling LLM: {e}"

        self.messages.append({"role": "user", "content": user_input})
        self.messages.append(response_message)

        if response_message.tool_calls:
            print(f"\n[Tool Call Detected]: {response_message.tool_calls[0].function.name}")
            
            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                function_args = eval(tool_call.function.arguments) 
                
                result_content = ""
                
                if function_name == "save_fact":
                    print(f"Executing INTERNAL tool: {function_name}")
                    # Default to current mode if not specified
                    target_mode = function_args.get("mode", current_mode)
                    result_content = self.semantic_memory.save_fact(function_args["fact"], mode=target_mode)
                    
                elif function_name == "set_mode":
                    print(f"Executing INTERNAL tool: {function_name}")
                    result_content = self.prompt_manager.set_mode(function_args["mode"])
                    
                elif function_name == "delete_mode":
                    print(f"Executing INTERNAL tool: {function_name}")
                    mode_del = function_args["mode"]
                    # Delete from Mongo and Pinecone
                    sem_del = self.semantic_memory.delete_mode(mode_del)
                    epi_del = self.episodic_memory.delete_mode_memory(mode_del)
                    result_content = f"Deleted mode '{mode_del}'. Semantic: {sem_del}, Episodic: {epi_del}"
                    if self.prompt_manager.mode == mode_del:
                        self.prompt_manager.set_mode("Work") # Fallback
                        result_content += ". Switched to 'Work'."

                elif function_name == "create_tool":
                    print(f"Executing CREATION tool: {function_name}")
                    result_content = self.tool_creator.create_tool(function_args["tool_name"], function_args["description"])
                    result_content += "\n(Note: You may need to restart the server or session to use this tool if it's not hot-loaded.)"
                    
                elif function_name in self.real_tool_names:
                    print(f"Executing REAL tool: {function_name}")
                    result = await self.session.call_tool(function_name, function_args)
                    result_content = str(result.content)
                else:
                    print(f"Simulating MOCK tool: {function_name}")
                    result_content = f"Mock success: {function_name} executed with {function_args}"
                
                self.messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result_content
                })
            
            # Final Follow-up Response
            # Note: If mode changed mid-tools, prompts should reflect new mode?
            # Ideally re-fetch prompt.
            payload_messages = [{"role": "system", "content": self.prompt_manager.get_system_prompt()}] + [m for m in self.messages if m["role"] != "system"]
            
            second_response = completion(
                model="openai/local-model",
                api_base="http://127.0.0.1:1234/v1",
                api_key="lm-studio",
                messages=payload_messages,
            )
            final_message = second_response.choices[0].message
            self.messages.append(final_message)
            
            final_text = final_message.content
            print(f"Jarvis: {final_text}")
            
            # Save Episodic Memory (Partitioned)
            self.episodic_memory.add_episode(
                content=f"User: {user_input}\nJarvis: {final_text}",
                mode=self.prompt_manager.mode
            )
            return final_text
        
        else:
            final_text = response_message.content
            print(f"Jarvis: {final_text}")
            self.episodic_memory.add_episode(
                content=f"User: {user_input}\nJarvis: {final_text}",
                mode=self.prompt_manager.mode
            )
            return final_text
