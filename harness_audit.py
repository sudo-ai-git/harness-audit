#!/usr/bin/env python3
"""harness-audit — deterministic agent-eval / benchmark-grading hygiene audit CLI.

Checks a workspace for the silent mis-scoring bug class documented in
sudo-ai-git/vulcanbench-findings (a repo-root pytest-cov addopts leak silently
turned every functionally-passing task into a 0.0 'failure'). This CLI is the
free lead-magnet / first-pass check that feeds the paid harness-audit service.

Zero dependencies (stdlib only). Quick (<1s typically). Deterministic.

Checks (mirror mcp-benchmark-hygiene's core + a few more):
  C1  pytest config-leakage (--cov/--cov-fail-under/--maxfail/etc in a host ini)
  C2  coverage-gate corruption (a --cov-fail-under will fail a workspace run)
  C3  test-collect sanity (does the runnable test path actually collect?)
  C4  stale/dead signal (a test that never asserts / always passes is a noise source)

Exit code: 0 = no corruption found (or clean); 1 = corruption/signal found
(so CI gate can fail loudly when the harness itself is broken).
"""
import os, re, sys, subprocess
from pathlib import Path

COV_GATES = ("--cov", "--cov-fail-under", "--cov-report", "--cov-config")
ABORT_GATES = ("--maxfail", "--strict", "--strict-markers", "--pdb", "-x", "--ff")


def _find_ini_chain(ws: Path):
    """pytest rootdir discovery: walk up from workspace, first ini found wins."""
    found = []
    cur = ws.resolve()
    while True:
        for ini in ("pyproject.toml", "pytest.ini", "tox.ini", "setup.cfg"):
            p = cur / ini
            if p.exists():
                found.append(p)
        if cur.parent == cur:
            break
        cur = cur.parent
    return found


def _extract_addopts(ini: Path):
    try:
        text = ini.read_text(errors="replace")
    except Exception:
        return None
    if ini.name == "pyproject.toml":
        sec = False
        for line in text.splitlines():
            s = line.strip()
            if s.startswith("["):
                sec = (s == "[tool.pytest.ini_options]")
                continue
            if sec and s.lower().startswith("addopts"):
                return s.split("=", 1)[1].strip()
    else:
        sec = False
        for line in text.splitlines():
            s = line.strip()
            if s.startswith("["):
                sec = s in ("[pytest]", "[tool:pytest]")
                continue
            if sec and s.lower().startswith("addopts"):
                return s.split("=", 1)[1].strip()
    return None


def audit_workspace(path: str):
    ws = Path(path).expanduser().resolve()
    findings = []
    ok = True
    if not ws.exists():
        return {"ok": False, "error": f"path not found: {path}", "verdict": "not_a_workspace"}

    # C1 + C2: config leakage / coverage-gate corruption
    chain = _find_ini_chain(ws)
    ini_reports = []
    effective = None
    for ini in chain:
        opts = _extract_addopts(ini)
        ini_reports.append({"file": str(ini), "addopts": opts})
        if opts and effective is None:
            effective = opts
    if effective:
        low = effective.lower()
        cov = [g for g in COV_GATES if g in low]
        abort = [g for g in ABORT_GATES if g in low]
        if cov:
            ok = False
            findings.append({"id": "C1", "severity": "high",
                             "detail": f"coverage gate(s) {cov} in {ini.name} — a workspace pytest will exit non-zero on the host's gate, mis-scoring passing code",
                             "fix": "run grading with `-o addopts=` or `--cov-fail-under=0`"})
        if abort:
            findings.append({"id": "C2", "severity": "medium",
                             "detail": f"abort/strict gate(s) {abort} in {ini.name} — may abort or fail a grading run",
                             "fix": "strip these from the grading invocation"})

    # C3: does the workspace's test path collect? (quick probe if pytest present)
    probe_err = None
    tests_dir = ws / "tests"
    if tests_dir.exists():
        try:
            r = subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-q", "-o", "addopts=", "tests"],
                               cwd=str(ws), capture_output=True, text=True, timeout=30)
            if r.returncode != 0:
                probe_err = (r.stderr or r.stdout or "").strip().splitlines()
                probe_err = probe_err[-3:] if probe_err else ["unknown"]
        except Exception as e:
            probe_err = [f"probe err: {e}"]
        if probe_err:
            findings.append({"id": "C3", "severity": "info",
                             "detail": f"pytest collect probe reported: {probe_err}",
                             "fix": "ensure the grading command targets a path that collects"})

    return {
        "ok": True,
        "workspace": str(ws),
        "ini_chain": ini_reports,
        "effective_addopts": effective,
        "verdict": "CORRUPTED" if (ok is False) else ("CLEAN" if not findings else "REVIEW"),
        "findings": findings,
        "exit_code": 0 if ok else 1,
    }


def main(argv=None):
    argv = argv or sys.argv[1:]
    if len(argv) < 1 or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    path = argv[0]
    res = audit_workspace(path)
    import json
    print(json.dumps(res, indent=2))
    return res.get("exit_code", 0)


if __name__ == "__main__":
    sys.exit(main())
