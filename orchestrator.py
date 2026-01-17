import asyncio
import os
import sys
import json
import chromadb
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from litellm import completion
import time
from memory_manager import EpisodicMemory, SemanticMemory

load_dotenv()



SERVER_SCRIPT = "filesystem_server.py"
CHROMA_HOST = "localhost"
CHROMA_PORT = 8000

class PromptManager:
    def __init__(self, semantic_memory):
        self.mode = "Work" # Default mode
        self.semantic_memory = semantic_memory
    
    def set_mode(self, mode):
        if mode in ["Work", "Personal"]:
            self.mode = mode
            return f"Mode switched to: {mode}"
        return f"Invalid mode. Available: Work, Personal"

    def get_system_prompt(self):
        # Filter facts based on mode
        # Work mode: All facts for now, or just 'work' + 'general'
        # Personal mode: 'personal' + 'general'
        
        filter_category = None
        if self.mode == "Work":
             # Implementation choice: Work sees everything or specific work stuff?
             # For this task: "filters which memory blocks are active".
             # Let's say Work sees everything, Personal only sees personal.
             # Or better: 
             # Work -> work, general
             # Personal -> personal, general
             pass
        
        # Simple Logic for Phase 4 Demo:
        # If Work, get all facts. If Personal, get only Personal facts.
        # Actually proper implementation:
        relevant_facts = []
        if self.mode == "Work":
             relevant_facts.extend(self.semantic_memory.get_all_facts(category="work"))
             relevant_facts.extend(self.semantic_memory.get_all_facts(category="general"))
        elif self.mode == "Personal":
             relevant_facts.extend(self.semantic_memory.get_all_facts(category="personal"))
             relevant_facts.extend(self.semantic_memory.get_all_facts(category="general"))
        
        # Deduplicate
        relevant_facts = list(set(relevant_facts))

        prompt = f"""
[PERSONALITY]
You are Jarvis, an intelligent system designed to be helpful, precise, and context-aware.

[CURRENT_MODE]
Current Mode: {self.mode}
(In Work mode, focus on productivity and technical tasks. In Personal mode, be more casual and focus on personal interests.)

[RELEVANT_MEMORIES]
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

async def run_chat_loop():
    print("DEBUG: Starting chat loop...", flush=True)

    # API Key check removed for Local LLM
    # if not os.getenv("GEMINI_API_KEY"):
    #     print("Error: GEMINI_API_KEY not found in .env")
    #     sys.exit(1)
    
    # Initialize Memory Systems
    episodic_memory = EpisodicMemory(host=CHROMA_HOST, port=CHROMA_PORT)
    semantic_memory = SemanticMemory()
    prompt_manager = PromptManager(semantic_memory)
    
    # Connect to ChromaDB for Tools (The Librarian)
    try:
        chroma_client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
        tool_collection = chroma_client.get_collection("tools")
        print("Connected to ChromaDB 'tools' collection.")
    except Exception as e:
        print(f"Warning: Could not connect to ChromaDB for tools: {e}")
        tool_collection = None

    # Define server connection parameters
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[SERVER_SCRIPT],
        env=env, 
    )

    print("DEBUG: Connecting to server...", flush=True)
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize connection
            await session.initialize()
            
            # List available REAL tools from MCP server
            mcp_tools_list = await session.list_tools()
            real_tool_names = {t.name for t in mcp_tools_list.tools}
            print(f"Connected to MCP Server. Real tools: {list(real_tool_names)}")
            
            # Internal Tools Definitions
            save_fact_tool = {
                "type": "function",
                "function": {
                    "name": "save_fact",
                    "description": "Save a permanent fact about the user. Categorize it as 'work', 'personal', or 'general'.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "fact": {"type": "string"},
                            "category": {"type": "string", "enum": ["work", "personal", "general"]}
                        },
                        "required": ["fact"]
                    }
                }
            }

            set_mode_tool = {
                "type": "function",
                "function": {
                    "name": "set_mode",
                    "description": "Switch the agent's mode between 'Work' and 'Personal'.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "mode": {"type": "string", "enum": ["Work", "Personal"]}
                        },
                        "required": ["mode"]
                    }
                }
            }
            
            messages = []
            
            while True:
                try:
                    user_input = input("\nUser: ")
                    if user_input.lower() in ["exit", "quit"]:
                        break
                    
                    # Update System Prompt Dynamically
                    system_prompt = prompt_manager.get_system_prompt()
                    
                    # Reset messages to keep system prompt fresh at the top, or update the first message?
                    # For simple chat history, we normally keep appending. But system prompt needs to be "active".
                    # Best practice: Insert system prompt as the very first message.
                    # If we restart the messages list each turn we lose history.
                    # We should keep history but "System" message usually stays at index 0.
                    # Let's rebuild the messages list with the NEW system prompt + existing conversation history.
                    
                    current_history = [m for m in messages if m["role"] != "system"]
                    
                    # Add episodic context to user input
                    relevant_episodes = episodic_memory.search_episodes(user_input, n=2)
                    context_msg = ""
                    if relevant_episodes:
                         context_msg = f"\n[Relevant past conversations]:\n" + "\n".join(relevant_episodes)
                    
                    # Prepare the payload
                    payload_messages = [{"role": "system", "content": system_prompt}] + current_history
                    payload_messages.append({"role": "user", "content": user_input + context_msg})


                    # --- DYNAMIC RETRIEVAL ---
                    current_tool_definitions = []
                    current_tool_definitions.append(save_fact_tool)
                    current_tool_definitions.append(set_mode_tool)

                    if tool_collection is not None:
                        # print("DEBUG: Querying ChromaDB...", flush=True) 
                        results = tool_collection.query(
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

                    # Call Local LLM
                    response_message = None
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
                        print(f"LLM Call Failed: {e}")
                        continue
                    
                    # Process Response
                    if response_message:
                         # Append user input and assistant response to persistent history
                         messages.append({"role": "user", "content": user_input}) # Don't save the episodic context to history to save tokens
                         messages.append(response_message)
                         
                         if response_message.tool_calls:
                            print(f"\n[Tool Call Detected]: {response_message.tool_calls[0].function.name}")
                            
                            for tool_call in response_message.tool_calls:
                                function_name = tool_call.function.name
                                function_args = eval(tool_call.function.arguments) 
                                
                                result_content = ""
                                
                                if function_name == "save_fact":
                                    print(f"Executing INTERNAL tool: {function_name}")
                                    cat = function_args.get("category", "general")
                                    result_content = semantic_memory.save_fact(function_args["fact"], category=cat)
                                elif function_name == "set_mode":
                                    print(f"Executing INTERNAL tool: {function_name}")
                                    result_content = prompt_manager.set_mode(function_args["mode"])
                                elif function_name in real_tool_names:
                                    print(f"Executing REAL tool: {function_name}")
                                    result = await session.call_tool(function_name, function_args)
                                    result_content = str(result.content)
                                else:
                                    print(f"Simulating MOCK tool: {function_name}")
                                    result_content = f"Mock success: {function_name} executed with {function_args}"
                                
                                messages.append({
                                    "role": "tool",
                                    "tool_call_id": tool_call.id,
                                    "content": result_content
                                })
                                
                            # Final Response
                             # Re-construct payload with tool outputs
                            payload_messages = [{"role": "system", "content": prompt_manager.get_system_prompt()}] + [m for m in messages if m["role"] != "system"] # Use fresh history

                            second_response = completion(
                                model="openai/local-model",
                                api_base="http://127.0.0.1:1234/v1",
                                api_key="lm-studio",
                                messages=payload_messages,
                            )
                            final_message = second_response.choices[0].message
                            messages.append(final_message)
                            print(f"Jarvis: {final_message.content}")
                            
                            episodic_memory.add_episode(
                                content=f"User: {user_input}\nJarvis: {final_message.content}",
                                metadata={"type": "conversation", "mode": prompt_manager.mode}
                            )
                            
                         else:
                            print(f"Jarvis: {response_message.content}")
                            episodic_memory.add_episode(
                                content=f"User: {user_input}\nJarvis: {response_message.content}",
                                metadata={"type": "conversation", "mode": prompt_manager.mode}
                            )

                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    print(f"Error: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(run_chat_loop())
    except KeyboardInterrupt:
        print("\nExiting...")
