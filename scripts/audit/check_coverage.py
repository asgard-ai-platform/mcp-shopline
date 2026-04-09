#!/usr/bin/env python3
"""
Shopline API Coverage Audit — 檢查所有 API endpoint 是否已有對應工具覆蓋

用法: python scripts/audit/check_coverage.py

從 reference/shopline-api-inventory.md 讀取完整 endpoint 列表，
從 tools/**/*.py 的 docstring 中解析【呼叫的 Shopline API】段落，
比對兩者找出未覆蓋的 endpoint。
"""
import os
import re
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOLS_DIR = os.path.join(PROJECT_ROOT, "tools")
WRITES_DIR = os.path.join(PROJECT_ROOT, "tools", "writes")
INVENTORY_FILE = os.path.join(PROJECT_ROOT, "reference", "shopline-api-inventory.md")

ENDPOINT_PATTERN = re.compile(r"-\s+(GET|POST|PUT|PATCH|DELETE)\s+(/[\w/{}\-_.]+)")


def parse_inventory():
    """從 inventory markdown 解析所有 endpoint"""
    endpoints = set()
    with open(INVENTORY_FILE, "r", encoding="utf-8") as f:
        for line in f:
            m = ENDPOINT_PATTERN.search(line)
            if m:
                method, path = m.group(1), m.group(2)
                endpoints.add(f"{method} {path}")
    return endpoints


def parse_tool_docstrings():
    """從所有 tool 模組的 docstring 解析已覆蓋的 endpoint"""
    covered = set()
    tool_map = {}  # endpoint -> [tool_name, ...]

    dirs = [TOOLS_DIR, WRITES_DIR]
    for d in dirs:
        if not os.path.isdir(d):
            continue
        for fname in os.listdir(d):
            if not fname.endswith(".py") or fname.startswith("__"):
                continue
            fpath = os.path.join(d, fname)
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()

            # 找出所有 @mcp.tool() 裝飾的函數及其 docstring
            # 簡化做法：找 def xxx 後面的 docstring 中的【呼叫的 Shopline API】段落
            in_api_section = False
            current_func = None

            for line in content.split("\n"):
                func_match = re.match(r"^def (\w+)\(", line)
                if func_match:
                    current_func = func_match.group(1)
                    in_api_section = False

                if "【呼叫的 Shopline API】" in line:
                    in_api_section = True
                    continue

                if in_api_section:
                    if line.strip().startswith("【") or (line.strip() == '"""') or (line.strip() == "'''"):
                        in_api_section = False
                        continue

                    m = ENDPOINT_PATTERN.search(line)
                    if m:
                        method, path = m.group(1), m.group(2)
                        ep = f"{method} {path}"
                        covered.add(ep)
                        if ep not in tool_map:
                            tool_map[ep] = []
                        tool_map[ep].append(f"{fname}:{current_func}")

    return covered, tool_map


def main():
    print("=" * 60)
    print("Shopline API Coverage Audit")
    print("=" * 60)

    inventory = parse_inventory()
    covered, tool_map = parse_tool_docstrings()

    print(f"\nInventory endpoints: {len(inventory)}")
    print(f"Covered endpoints:  {len(covered)}")

    # 找出未覆蓋
    uncovered = inventory - covered
    extra = covered - inventory

    if uncovered:
        print(f"\n❌ Uncovered endpoints ({len(uncovered)}):")
        for ep in sorted(uncovered):
            print(f"   {ep}")

    if extra:
        print(f"\n⚠️  Extra endpoints in tools but not in inventory ({len(extra)}):")
        for ep in sorted(extra):
            tools = tool_map.get(ep, ["unknown"])
            print(f"   {ep} — {', '.join(tools)}")

    covered_in_inventory = inventory & covered
    coverage_pct = len(covered_in_inventory) / len(inventory) * 100 if inventory else 0

    print(f"\n{'=' * 60}")
    print(f"Coverage: {len(covered_in_inventory)}/{len(inventory)} ({coverage_pct:.1f}%)")

    if uncovered:
        print(f"❌ FAIL — {len(uncovered)} endpoint(s) uncovered")
        sys.exit(1)
    else:
        print("✅ PASS — All endpoints covered")
        sys.exit(0)


if __name__ == "__main__":
    main()
