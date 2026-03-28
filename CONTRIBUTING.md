# Contributing to Shopline API MCP Server

Thank you for your interest in contributing! This guide will help you get started.

## Getting Started

1. Fork and clone the repository
2. Set up your environment:

```bash
pip install requests
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
2. Define a schema dict in Claude API `tool_use` format:

```python
MY_TOOL_SCHEMA = {
    "name": "my_tool_name",
    "description": "工具描述（繁體中文）",
    "input_schema": {
        "type": "object",
        "properties": { ... },
        "required": [ ... ]
    }
}
```

3. Implement the function using `api_get` / `fetch_all_pages` from `base_tool.py`
4. Append `{"schema": MY_TOOL_SCHEMA, "function": my_tool_fn}` to the module's tool list
5. Import the new tool list in `tool_registry.py` if you created a new module
6. Add a test case in `tests/test_all_tools.py`

Tools are auto-registered via `tool_registry.py` — no extra wiring needed for existing modules.

## Code Conventions

- **Language**: Code comments and tool descriptions are in Traditional Chinese (zh-Hant)
- **Dependencies**: Only `requests` as an external dependency. Avoid adding new ones unless absolutely necessary.
- **HTTP calls**: Use `api_get` / `fetch_all_pages` / `fetch_all_pages_by_date_segments` from `base_tool.py` — do not make raw HTTP calls in tools
- **Money values**: Use `money_to_float()` from `base_tool.py` for all monetary fields
- **Order filtering**: Use the `VALID_ORDER_STATUSES` set for filtering valid revenue orders

## Testing

All tests hit the live Shopline API and require a valid `SHOPLINE_API_TOKEN`.

```bash
# Run the full E2E test suite
python tests/test_all_tools.py

# Test API connectivity
python scripts/auth/test_connection.py
```

Ensure all 19 tools pass before submitting a PR. If you added a new tool, include its test.

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
