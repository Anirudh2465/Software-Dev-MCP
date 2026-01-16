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

load_dotenv()

# Check for API Key
if not os.getenv("GEMINI_API_KEY"):
    print("Error: GEMINI_API_KEY not found in .env")
    sys.exit(1)

SERVER_SCRIPT = "filesystem_server.py"
CHROMA_HOST = "localhost"
CHROMA_PORT = 8000

async def run_chat_loop():
    print("DEBUG: Starting chat loop...", flush=True)
    
    # Connect to ChromaDB
    try:
        chroma_client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
        tool_collection = chroma_client.get_collection("tools")
        print("Connected to ChromaDB 'tools' collection.")
    except Exception as e:
        print(f"Warning: Could not connect to ChromaDB: {e}")
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
            
            messages = []
            
            while True:
                try:
                    user_input = input("\nUser: ")
                    if user_input.lower() in ["exit", "quit"]:
                        break
                    
                    messages.append({"role": "user", "content": user_input})
                    
                    # --- DYNAMIC RETRIEVAL ---
                    current_tool_definitions = []
                    if tool_collection:
                        print("DEBUG: Querying ChromaDB for relevant tools...", flush=True)
                        results = tool_collection.query(
                            query_texts=[user_input],
                            n_results=3 # Prune to Top 3
                        )
                        
                        retrieved_ids = results['ids'][0]
                        print(f"DEBUG: Retrieved tools: {retrieved_ids}")
                        
                        # Reconstruct tool definitions from metadata
                        for i, meta in enumerate(results['metadatas'][0]):
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
                         # Fallback if Chroma fails
                         print("DEBUG: Chroma unavailable, using only MCP tools.")
                         current_tool_definitions = [
                            {
                                "type": "function",
                                "function": {
                                    "name": tool.name,
                                    "description": tool.description,
                                    "parameters": tool.inputSchema
                                }
                            } 
                            for tool in mcp_tools_list.tools
                        ]

                    # Call Gemini
                    # gemini-2.0-flash-exp is the only one working, but rate limited.
                    retry_delay = 10
                    for attempt in range(3):
                        try:
                            response = completion(
                                model="gemini/gemini-2.0-flash-exp",
                                messages=messages,
                                tools=current_tool_definitions,
                                api_key=os.getenv("GEMINI_API_KEY")
                            )
                            break
                        except Exception as e:
                            if "429" in str(e) and attempt < 2:
                                print(f"Rate limited. Retrying in {retry_delay}s...")
                                time.sleep(retry_delay)
                                retry_delay *= 2
                            else:
                                raise e
                                
                    # Handle tool calls
                    message = response.choices[0].message
                    messages.append(message) # Add assistant response to history
                    
                    if message.tool_calls:
                        print(f"\n[Tool Call Detected]: {message.tool_calls[0].function.name}")
                        
                        for tool_call in message.tool_calls:
                            function_name = tool_call.function.name
                            function_args = eval(tool_call.function.arguments) 
                            
                            result_content = ""
                            
                            if function_name in real_tool_names:
                                # Execute REAL tool via MCP session
                                print(f"Executing REAL tool: {function_name}")
                                result = await session.call_tool(function_name, function_args)
                                result_content = str(result.content)
                            else:
                                # Mock execution for retrieved dummy tools
                                print(f"Simulating MOCK tool: {function_name}")
                                result_content = f"Mock success: {function_name} executed with {function_args}"
                            
                            # Send result back to LLM
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": result_content
                            })
                            
                        # Get final response
                        for attempt in range(3):
                            try:
                                second_response = completion(
                                    model="gemini/gemini-2.0-flash-exp",
                                    messages=messages,
                                    tools=current_tool_definitions, 
                                    api_key=os.getenv("GEMINI_API_KEY")
                                )
                                break
                            except Exception as e:
                                if "429" in str(e) and attempt < 2:
                                    print(f"Rate limited (2nd call). Retrying in {retry_delay}s...")
                                    time.sleep(retry_delay)
                                    retry_delay *= 2
                                else:
                                    raise e
                        final_message = second_response.choices[0].message
                        messages.append(final_message)
                        print(f"Jarvis: {final_message.content}")
                    
                    else:
                        print(f"Jarvis: {message.content}")

                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    print(f"Error: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(run_chat_loop())
    except KeyboardInterrupt:
        print("\nExiting...")
