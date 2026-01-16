import asyncio
import os
import sys
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from litellm import completion

load_dotenv()

# Check for API Key
if not os.getenv("GEMINI_API_KEY"):
    print("Error: GEMINI_API_KEY not found in .env")
    sys.exit(1)

SERVER_SCRIPT = "filesystem_server.py"

async def run_chat_loop():
    # Define server connection parameters
    server_params = StdioServerParameters(
        command="uv",
        args=["run", SERVER_SCRIPT],
        env=os.environ.copy(), 
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize connection
            await session.initialize()
            
            # List available tools
            tools = await session.list_tools()
            tool_definitions = [
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.inputSchema
                    }
                } 
                for tool in tools.tools
            ]
            
            print(f"Connected to MCP Server. Available tools: {[t.name for t in tools.tools]}")
            
            messages = []
            
            while True:
                try:
                    user_input = input("\nUser: ")
                    if user_input.lower() in ["exit", "quit"]:
                        break
                    
                    messages.append({"role": "user", "content": user_input})
                    
                    # Call Gemini
                    response = completion(
                        model="gemini/gemini-2.0-flash-exp",
                        messages=messages,
                        tools=tool_definitions,
                        api_key=os.getenv("GEMINI_API_KEY")
                    )
                    
                    # Handle tool calls
                    message = response.choices[0].message
                    messages.append(message) # Add assistant response to history
                    
                    if message.tool_calls:
                        print(f"\n[Tool Call Detected]: {message.tool_calls[0].function.name}")
                        
                        for tool_call in message.tool_calls:
                            function_name = tool_call.function.name
                            function_args = eval(tool_call.function.arguments) # Simple eval for JSON-like string
                            
                            # Execute tool via MCP session
                            result = await session.call_tool(function_name, function_args)
                            
                            # Send result back to LLM
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": str(result.content)
                            })
                            
                        # Get final response
                        second_response = completion(
                            model="gemini/gemini-2.0-flash-exp",
                            messages=messages,
                            tools=tool_definitions, # Keep tools available
                            api_key=os.getenv("GEMINI_API_KEY")
                        )
                        final_message = second_response.choices[0].message
                        messages.append(final_message)
                        print(f"Jarvis: {final_message.content}")
                    
                    else:
                        print(f"Jarvis: {message.content}")

                except Exception as e:
                    print(f"Error: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(run_chat_loop())
    except KeyboardInterrupt:
        print("\nExiting...")
