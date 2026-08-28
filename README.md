# harness-audit

**Deterministic agent-eval / benchmark-grading hygiene audit CLI.** Zero
dependencies, `<1s`, returns a JSON verdict. Detects the silent mis-scoring bug
class that makes an agent-benchmark report wrong numbers.

## The bug it catches

A repo-root `pyproject.toml` (or `pytest.ini`) with coverage/strict `addopts`
silently inherits into every `pytest` run inside that repo — including the
*workspace* runs a grading harness uses to judge an agent's code. The host's
coverage gate fails, pytest exits non-zero, and **functionally-passing code is
recorded as failed**. This is the exact bug documented in
**[sudo-ai-git/vulcanbench-findings](https://sudo-ai-git.github.io/vulcanbench-findings/)**:
a `--cov=harness --cov-fail-under=80` leak scored every functional task as `0.0` —
until re-scored with `-o addopts=`, where they all passed.

## Quick start

```bash
# pip install harness-audit   (once on PyPI)
uvx --from git+https://github.com/sudo-ai-git/harness-audit harness-audit .   # or:
python3 harness_audit.py /path/to/your/workspace
```

Any workspace whose grading runs under a repo root with test config gets a
`CORRUPTED` verdict with the exact fix:

```bash
python3 harness_audit.py /home/runner/my-eval/task-1
# => { "verdict": "CORRUPTED", "findings": [ { "id": "C1", "severity": "high",
#       "detail": "coverage gate(s) ['--cov', '--cov-fail-under'] in pyproject.toml ...",
#       "fix": "run grading with `-o addopts=` or `--cov-fail-under=0`" } ] }
```

Exit code `1` when corruption is found — so you can gate your own eval CI on it
and never publish (or hire against) a wrong number.

## Checks

| id | severity | what it flags |
|---|---|---|
| C1 | high | pytest `addopts` coverage gate leak (will non-zero a workspace run) |
| C2 | medium | abort/strict gate (`--maxfail`, `-x`, `--strict`, `--pdb`) |
| C3 | info | `pytest --collect-only` probe on `tests/` (dead/empty path noise) |

## Why this exists (and how it feeds the paid service)

This is the free first-pass. When an org runs it and finds a `CORRUPTED`
verdict, the natural next step is a full audit of their whole agent-eval
pipeline — config leakage, dead signal, false pass/fail, and leaderboard
integrity. Fixed-scope harness audits are offered through
**[agensi-builds](https://github.com/sudo-ai-git/agensi-builds)**. The CLI stays
free and MIT — the audit *service* is the product.

## License & provenance

MIT. Independently derived from the documented VulcanBench #79 finding
(morganlinton/VulcanBench issue #79 + sudo-ai-git/vulcanbench-findings). No
affiliation implied.
