#!/usr/bin/env python3
"""Verify harness-audit CLI: detects corruption correctly, passes clean, no crash."""
import os, sys, tempfile, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, "/home/sudosudo/harness-audit-cli")
from harness_audit import audit_workspace  # noqa

def write(p, t):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w").write(t)

results = []
def check(name, res, expect_corrupt, expect_verdict=None):
    corrupted = res.get("verdict") == "CORRUPTED"
    ok = (corrupted == expect_corrupt)
    if expect_verdict:
        ok = ok and res.get("verdict") == expect_verdict
    results.append((name, ok, res.get("verdict")))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: verdict={res.get('verdict')} findings={len(res.get('findings',[]))}")

# 1) VulcanBench-style corrupt workspace
t = tempfile.mkdtemp()
write(os.path.join(t, "pyproject.toml"),
      '[tool.pytest.ini_options]\naddopts = "--cov=harness --cov-report=term-missing:skip-covered --cov-fail-under=80"\n')
check("vulcanbench-style cov gate", audit_workspace(t), True)

# 2) nested workspace inheriting the gate (the real bug)
sub = os.path.join(t, "task-1", "src")
write(os.path.join(sub, "test_x.py"), "def test_x():\n    assert True\n")
check("nested inherits root gate", audit_workspace(sub), True)

# 3) truly clean workspace
t2 = tempfile.mkdtemp()
write(os.path.join(t2, "test_ok.py"), "def test_ok():\n    assert 1==1\n")
check("clean workspace", audit_workspace(t2), False)

# 4) missing path -> not_a_workspace, no crash
check("missing path", audit_workspace("/nonexistent/x"), False, "not_a_workspace")

# 5) abort gate (--maxfail)
t3 = tempfile.mkdtemp()
write(os.path.join(t3, "pytest.ini"), "[pytest]\naddopts = --maxfail=2\n")
check("abort gate", audit_workspace(t3), False)  # medium, not CORRUPTED

passed = sum(1 for _,ok,_ in results if ok)
print(f"\n{passed}/{len(results)} checks passed")
sys.exit(0 if passed == len(results) else 1)
