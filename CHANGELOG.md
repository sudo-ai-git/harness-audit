# Changelog

## v0.1.1 (2026-08-28)
- **CI fix**: the release workflow sanity-check imported `mcp_server` (copied from a
  sibling MCP-server repo); harness-audit is a CLI with module `harness_audit`. The
  wheel built fine but the post-install sanity-check crashed with
  `ModuleNotFoundError: No module named 'mcp_server'`. Fixed to reference
  `harness_audit` and filter console scripts by `harness`/`audit`. Supersedes the
  failed v0.1.0 CI run; v0.1.0 release asset remains valid.
- No functional/API change; behavior identical to v0.1.0.

## v0.1.0 (2026-08-28)
- Initial release of the deterministic, zero-dependency agent-eval / benchmark
  grading hygiene audit CLI.
- Checks: C1 pytest `--cov` addopts leakage (high), C2 abort/strict gates (medium),
  C3 pytest `--collect-only` probe.
