# Release Checklist (Async-Only Client Era)

Use this checklist before publishing a release from `feat/ws-v2-async`.

## 1. Quality Gates

- `python -m pytest -q`
- `cd mod && .\gradlew.bat test --no-daemon`
- `python python/tools/generate_baritone_commands.py --check`

## 2. Documentation Gates

- Root docs show `pyritone.Client` as the primary client.
- Python docs/examples are async-only (`await` + `async with Client()` flows).
- Demo scripts run with async client helpers.
- Migration notes are confined to:
  - `python/docs/migration-from-legacy-aliases.md`

## 3. Parity + Debt Review

- Confirm typed parity matrix is current:
  - `python/docs/baritone-typed-parity.md`
- Confirm release parity/debt snapshot is current:
  - `python/docs/release-parity-fallback-report.md`
- Confirm fallback debt gates are green:
  - `python/tests/test_fallback_debt.py`

## 4. Compatibility Policy (v0.2.x Tag Decision)

- Keep compatibility aliases exported in `v0.2.x`:
  - `PyritoneClient -> Client`
  - `AsyncPyritoneClient -> Client`
- Keep generated sync command shim modules in `v0.2.x`:
  - `python/src/pyritone/commands/sync_*.py`
- Do not increase compatibility debt ceilings in `python/tests/test_fallback_debt.py`.
- Keep `client.execute(...)` public as an advanced escape hatch for command interop and CLI usage.
- Docs/quickstarts should prefer generated command wrappers and `client.baritone.*` typed APIs.
- Removal target for aliases + sync shims: no earlier than `v0.3.0`.

## 5. Versioning + Release Notes

- Bump Python package version in:
  - `python/pyproject.toml`
- Bump mod version in:
  - `mod/gradle.properties`
- Record user-facing changes in:
  - `CHANGELOG.md`
- Publish release notes from Wave 9 outputs in:
  - `docs/release-notes-v0.2.0.md`

## 6. Publish Readiness

- Build Python package:
  - `cd python && python -m build`
  - `cd python && python -m twine check dist/*`
- Validate release artifacts and docs links before tagging.
