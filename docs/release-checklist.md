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

## 4. Versioning + Changelog

- Record user-facing changes in changelog under an `Unreleased` (or release) section.
- If compatibility aliases/shims are removed, treat as a breaking change release.
- Ensure release notes call out websocket v2 + async-only client direction.

## 5. Publish Readiness

- Build Python package:
  - `cd python && python -m build`
  - `cd python && python -m twine check dist/*`
- Validate release artifacts and docs links before tagging.
