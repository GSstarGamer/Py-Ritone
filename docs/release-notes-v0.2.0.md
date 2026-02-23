# Release Notes v0.2.0 (Async-Only + WebSocket v2)

Release target for the `feat/ws-v2-async` migration line.

## Highlights

- WebSocket v2 is now the bridge transport baseline (`ws://127.0.0.1:27841/ws`).
- `pyritone.Client` is the canonical async client API.
- Typed Baritone wrappers are available under `client.baritone.*`.
- Minecraft constants are available under `pyritone.minecraft.*`.
- Docs/demos were rewritten to async-only usage.

## Breaking Direction Changes

- Sync runtime semantics were removed from the Python client path.
- Bridge usage is now websocket-first (legacy socket bridge path removed).
- New code should use:
  - generated command wrappers (for command dispatch),
  - typed wrappers (`client.baritone.*`) for richer API calls.

## Compatibility Policy For v0.2.x

- Keep compatibility aliases:
  - `PyritoneClient -> Client`
  - `AsyncPyritoneClient -> Client`
- Keep generated sync command shim modules:
  - `python/src/pyritone/commands/sync_*.py`
- Treat both as soft-deprecated migration cushions; removal target is no earlier than `v0.3.0`.
- Keep `client.execute(...)` available as an advanced raw-command escape hatch.
  - Guidance: prefer wrapper/typed APIs in user-facing docs and new application code.

## Parity + Debt Snapshot

- Canonical command wrappers: `42`
- Alias wrappers: `21`
- Compatibility alias assignments: `3`
- Sync command shim modules: `6`
- Legacy socket bridge path: removed (guarded by tests)
- Cancel fallback `"stop"` command path: removed (guarded by tests)

Primary references:

- `python/docs/release-parity-fallback-report.md`
- `python/docs/baritone-typed-parity.md`
- `docs/release-checklist.md`

## Upgrade Notes

1. Prefer importing `Client` from `pyritone`.
2. Move command calls to awaited async flows (`await client.goto(...)`, etc.).
3. Keep alias imports only as transitional compatibility while migrating existing codebases.
4. Use `client.execute(...)` only when wrapper/typed surfaces do not cover the needed command flow.
