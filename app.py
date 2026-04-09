"""
Shopline MCP 應用實例 — FastMCP 單例

由 mcp_server.py（入口）和各 tools 模組共同匯入，避免循環依賴。
此模組只建立 FastMCP 實例，不匯入任何 tool 模組。
"""
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("mcp-shopline")
