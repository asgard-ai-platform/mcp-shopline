"""
Shopline MCP 應用實例 — MCPServer 單例

由 mcp_server.py（入口）和各 tools 模組共同匯入，避免循環依賴。
此模組只建立 MCPServer 實例，不匯入任何 tool 模組。
"""
from mcp.server.mcpserver import MCPServer

mcp = MCPServer("mcp-shopline", version="0.2.0")
