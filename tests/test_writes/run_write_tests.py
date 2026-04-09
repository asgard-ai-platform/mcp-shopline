"""
寫入工具測試統一入口

使用: SHOPLINE_TEST_WRITES=1 python tests/test_writes/run_write_tests.py
"""
import os
import sys
import subprocess

if os.environ.get("SHOPLINE_TEST_WRITES", "").lower() not in ("1", "true", "yes"):
    print("⚠ Write tests skipped. Set SHOPLINE_TEST_WRITES=1 to run.")
    sys.exit(0)

test_dir = os.path.dirname(os.path.abspath(__file__))

test_files = sorted(
    f for f in os.listdir(test_dir)
    if f.startswith("test_") and f.endswith(".py")
)

print(f"Found {len(test_files)} write test files\n")

failed = []
for tf in test_files:
    print(f"\n{'=' * 60}")
    print(f"Running {tf}")
    print(f"{'=' * 60}")
    result = subprocess.run([sys.executable, os.path.join(test_dir, tf)])
    if result.returncode != 0:
        failed.append(tf)

print(f"\n{'=' * 60}")
if failed:
    print(f"❌ {len(failed)} test file(s) failed: {failed}")
    sys.exit(1)
else:
    print(f"✅ All {len(test_files)} write test files passed")
