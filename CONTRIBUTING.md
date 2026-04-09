# Contributing to MCP Shopline

Thank you for your interest in contributing! This guide will help you get started.

## Getting Started

1. Fork and clone the repository
2. Set up your environment:

```bash
uv venv && source .venv/bin/activate
uv pip install -e .
cp .env.example .env
# Add your Shopline API access token to .env
export SHOPLINE_API_TOKEN=your_token_here
```

3. Verify the setup:

```bash
python scripts/auth/test_connection.py
python tests/test_all_tools.py
```

## Adding a New Tool

1. Choose the appropriate module in `tools/` (or create a new `{domain}_tools.py`)
2. At the top of the module, import the `mcp` singleton and helpers:

```python
from app import mcp
from pydantic import Field
from typing import Optional, Literal
from tools.base_tool import api_get, fetch_all_pages, money_to_float, get_translation
```

3. Define the tool with `@mcp.tool()`, typed parameters, `Field()` descriptions, and a docstring:

```python
@mcp.tool()
def my_tool_name(
    param1: str = Field(description="說明（繁體中文）"),
    param2: Optional[int] = Field(default=None, description="說明"),
) -> dict:
    """工具的整體說明（繁體中文），成為 MCP tools/list 中的 description。"""
    # implementation using api_get / fetch_all_pages
    ...
```

4. If you created a new module, import it in `mcp_server.py` to trigger registration:

```python
import tools.your_new_module  # noqa: F401
```

5. Add a test case in `tests/test_all_tools.py` (import and call the function directly)

No schema dict, no tool list, no extra wiring needed — `@mcp.tool()` handles registration automatically.

## Code Conventions

- **Language**: Code comments and tool descriptions are in Traditional Chinese (zh-Hant)
- **Dependencies**: `requests` and `mcp` are the only external dependencies. Avoid adding new ones unless absolutely necessary.
- **HTTP calls**: Use `api_get` / `api_post` / `api_put` / `api_patch` / `api_delete` / `fetch_all_pages` / `fetch_all_pages_by_date_segments` from `base_tool.py` — do not make raw HTTP calls in tools
- **Money values**: Use `money_to_float()` from `base_tool.py` for all monetary fields
- **Order filtering**: Use the `VALID_ORDER_STATUSES` set for filtering valid revenue orders

## Write Tool Conventions

When adding a tool that creates, updates, or deletes data (a "write tool"):

1. **Docstring prefix**: The docstring must start with `[WRITE]` so callers know the tool has side effects.
2. **副作用 section**: Include a `【副作用】` section in the docstring describing exactly what data will be created, modified, or deleted.
3. **HTTP helpers**: Use `api_post`, `api_put`, `api_patch`, or `api_delete` from `base_tool.py`. Never make raw HTTP calls.
4. **Return shape**: Return a standardised dict — `{"success": bool, "resource_id": str, "message": str}`.
5. **File location**: Place the tool in `tools/writes/{domain}_writes.py`.

Example:

```python
@mcp.tool()
def create_product(
    title: str = Field(description="商品名稱"),
) -> dict:
    """[WRITE] 建立新商品。

    【副作用】將在 Shopline 後台新增一筆商品記錄。
    """
    result = api_post("products", {"title": title})
    return {"success": True, "resource_id": str(result["id"]), "message": "商品建立成功"}
```

To run write tools during tests, set `SHOPLINE_TEST_WRITES=1` (disabled by default to avoid accidental mutations):

```bash
SHOPLINE_TEST_WRITES=1 python tests/test_all_tools.py
```

## Testing

All tests hit the live Shopline API and require a valid `SHOPLINE_API_TOKEN`.

```bash
# Run the full E2E test suite (read tools only by default)
python tests/test_all_tools.py

# Include write tool tests (creates/modifies real data)
SHOPLINE_TEST_WRITES=1 python tests/test_all_tools.py

# Test API connectivity
python scripts/auth/test_connection.py
```

Ensure all 143 tools pass before submitting a PR. If you added a new tool, include its test.

## Submitting Changes

1. Create a feature branch from `main`
2. Make your changes following the conventions above
3. Test with `python tests/test_all_tools.py`
4. Open a pull request with a clear description of what the tool does and why

## Reporting Issues

Open an issue on GitHub with:

- What you expected to happen
- What actually happened
- Steps to reproduce
- Your Python version and OS

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
