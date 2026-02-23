# Wave 9 Release Parity And Fallback Debt Report

Final migration-prep snapshot for the async-only `pyritone.Client` docs release.

## Baritone Parity Snapshot

### Command wrapper parity

- Canonical command wrappers: `42` (`pyritone.commands.COMMAND_SPECS`)
- Alias wrappers: `21` (`pyritone.commands.ALIAS_TO_CANONICAL`)
- Generated command docs are now async-only and use `Client` examples.

### Typed wrapper parity

- Wave 5/6/7 typed wrapper surfaces are published under `client.baritone.*` and `pyritone.minecraft.*`.
- Package-level matrix and deferred inventory remain tracked in:
  - `python/docs/baritone-typed-parity.md`
- Current parity strategy is interface-first (high-value API interfaces wrapped, low-value concrete/internal classes deferred).

## Fallback Debt Snapshot

Measured against `python/tests/test_fallback_debt.py`:

- Compatibility alias assignments (`PyritoneClient` / `AsyncPyritoneClient` -> `Client`): `3`
- Generated sync command shim modules (`python/src/pyritone/commands/sync_*.py`): `6`
- Legacy socket bridge server code path: removed and guarded
- Cancel fallback `"stop"` command path: removed and guarded (direct `forceCancel()` path required)

Remaining intentional debt:

- Compatibility aliases are still exported for downstream migration cushioning.
- Sync command shim modules are still generated for compatibility surfaces.
- Raw command transport (`baritone.execute`) is retained for command-wrapper interop and edge usage.

## Release Readiness Notes

- Docs and demos now present `pyritone.Client` as the primary client.
- Sync-labeled usage guides/examples were removed from user-facing docs.
- Migration guidance is isolated in `python/docs/migration-from-legacy-aliases.md`.

## Recommended Next Cleanup Before Major Release

1. Remove compatibility aliases from public exports.
2. Stop generating sync command shim modules.
3. Re-evaluate whether `baritone.execute` should remain public or move to advanced-only guidance.
