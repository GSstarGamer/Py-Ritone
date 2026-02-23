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

## Tag Policy Decision (v0.2.0)

- Keep compatibility aliases in public exports for `v0.2.x`:
  - `PyritoneClient -> Client`
  - `AsyncPyritoneClient -> Client`
- Keep generated sync command shim modules for `v0.2.x`:
  - `python/src/pyritone/commands/sync_*.py`
- Treat both as soft-deprecated migration cushions and keep debt ceilings flat:
  - alias assignments `<= 3`
  - sync shim modules `<= 6`
- Keep `client.execute(...)` public for advanced command interop and CLI usage, but position it as advanced-only in docs.
- Prefer generated command wrappers and typed `client.baritone.*` APIs in user-facing examples.
- Removal target for aliases + sync shims: no earlier than `v0.3.0`.

## Release Readiness Notes

- Docs and demos now present `pyritone.Client` as the primary client.
- Sync-labeled usage guides/examples were removed from user-facing docs.
- Migration guidance is isolated in `python/docs/migration-from-legacy-aliases.md`.
