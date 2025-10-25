import os
import gc
import json
import torch
from dotenv import load_dotenv
from agents.mcp import MCPServerStdio
from contextlib import AsyncExitStack
from typing import List, Dict, TypedDict
from mcp.client.stdio import stdio_client
from mcp import ClientSession, StdioServerParameters

load_dotenv(override=True)

class ToolDefinition(TypedDict):
    name: str
    description: str
    input_schema: dict
      
class Multi_MCP_Server:
    
    def __init__(self):
        # Initialize session and client objects
        self.exit_stack = AsyncExitStack() # new
        self.available_tools: List[ToolDefinition] = [] # new
        self.mcp_servers: Dict[str, list[MCPServerStdio]] = {} # new
        self.tool_to_session: Dict[str, ClientSession] = {} # new
        
    async def connect_to_server(self, server_name: str, server_config: dict) -> None:
        """Connect to a single MCP server."""
        try:
            server_params = StdioServerParameters(**server_config)
            stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
            read, write = stdio_transport
            client_session = await self.exit_stack.enter_async_context(ClientSession(read, write))
            
            mcp_server = await self.exit_stack.enter_async_context(MCPServerStdio(server_config, client_session_timeout_seconds=360))
            self.mcp_servers[server_name]=[mcp_server] # Instead of using MCP tools directly we should give mcp_server function definitions for OpenAI support
            
            await client_session.initialize()
            response = await client_session.list_tools()
            
            tools = response.tools
            print(f"\nConnected to {server_name} with tools:", [t.name for t in tools])
            for tool in tools:
                self.tool_to_session[tool.name]=client_session
                self.available_tools.append(tool)
                
        except Exception as e:
            print(f"Failed to connect to server {server_name}: {e}")
    
    async def connect_to_servers(self): # new
        """Connect to all configured MCP servers."""
        try:
            with open(os.path.join(os.getcwd(), "mcp_server_config/", "server_config.json"), "r") as file:
                data = json.load(file)
            
            servers = data.get("mcpServers", {})
            for server_name, server_config in servers.items():
                await self.connect_to_server(server_name, server_config)
        except Exception as e:
            print(f"Error loading server configuration: {e}")
            raise
    
    async def cleanup(self): # new
        """Cleanly close all resources using AsyncExitStack."""
        await self.exit_stack.aclose()
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    
    async def call_tool(self, tool_name:str, tool_args:dict):
        # Call a tool
        session = self.tool_to_session[tool_name] # new
        tool_result = await session.call_tool(tool_name, arguments=tool_args)
        return tool_result
