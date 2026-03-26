#!/usr/bin/env python3
"""
Shopline API MCP Server — 供 Claude Code / Claude Cowork 調用

透過 stdio 傳輸的 JSON-RPC 2.0 MCP 協定，暴露 19 個 Shopline API 工具。

使用方式:
  1. 在 .mcp.json 中設定（見專案根目錄範例）
  2. 或手動啟動: python mcp_server.py
"""
import sys
import os
import json
import traceback

# 確保能 import tools 模組
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tools.tool_registry import get_tool_schemas, execute_tool


SERVER_NAME = "shopline-api-tools"
SERVER_VERSION = "1.0.0"
PROTOCOL_VERSION = "2024-11-05"


def handle_initialize(params):
    """處理 initialize 請求"""
    return {
        "protocolVersion": PROTOCOL_VERSION,
        "capabilities": {
            "tools": {"listChanged": False},
        },
        "serverInfo": {
            "name": SERVER_NAME,
            "version": SERVER_VERSION,
        },
    }


def handle_tools_list(params):
    """處理 tools/list 請求 — 回傳所有可用工具的 schema"""
    schemas = get_tool_schemas()
    tools = []
    for s in schemas:
        tools.append({
            "name": s["name"],
            "description": s.get("description", ""),
            "inputSchema": s.get("input_schema", {"type": "object", "properties": {}}),
        })
    return {"tools": tools}


def handle_tools_call(params):
    """處理 tools/call 請求 — 執行指定工具"""
    tool_name = params.get("name")
    arguments = params.get("arguments", {})

    if not tool_name:
        return make_error(-32602, "Missing tool name")

    try:
        result = execute_tool(tool_name, **arguments)

        # 如果結果包含 error key，回傳為 isError
        if isinstance(result, dict) and "error" in result and result["error"]:
            return {
                "content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False)}],
                "isError": True,
            }

        return {
            "content": [{
                "type": "text",
                "text": json.dumps(result, ensure_ascii=False, default=str),
            }],
        }
    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Error: {str(e)}\n{traceback.format_exc()}"}],
            "isError": True,
        }


def make_error(code, message):
    """建立 JSON-RPC error 物件"""
    return {"__error__": True, "code": code, "message": message}


def process_message(message):
    """處理單一 JSON-RPC 訊息"""
    method = message.get("method")
    params = message.get("params", {})

    handlers = {
        "initialize": handle_initialize,
        "notifications/initialized": lambda p: None,  # 通知，不需回應
        "tools/list": handle_tools_list,
        "tools/call": handle_tools_call,
        "ping": lambda p: {},
    }

    handler = handlers.get(method)
    if handler is None:
        return make_error(-32601, f"Method not found: {method}")

    return handler(params)


def main():
    """主迴圈 — 從 stdin 讀取 JSON-RPC 訊息，寫回 stdout"""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            message = json.loads(line)
        except json.JSONDecodeError as e:
            response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": f"Parse error: {e}"},
            }
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()
            continue

        msg_id = message.get("id")
        result = process_message(message)

        # 通知（無 id）不需回應
        if msg_id is None:
            continue

        # 錯誤回應
        if isinstance(result, dict) and result.get("__error__"):
            response = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": result["code"], "message": result["message"]},
            }
        else:
            response = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": result,
            }

        sys.stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
