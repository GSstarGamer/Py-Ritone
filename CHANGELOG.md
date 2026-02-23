# Changelog

All notable changes to this project are documented in this file.

This format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2026-02-23

### Added

- WebSocket v2 bridge protocol, transport metadata, and auth/session framing as the standard bridge path.
- Typed API substrate (`api.metadata.get`, `api.construct`, `api.invoke`) with Python typed wrappers under `client.baritone.*`.
- Minecraft identifier constants under `pyritone.minecraft.blocks`, `pyritone.minecraft.items`, and `pyritone.minecraft.entities`.
- Release parity and fallback debt report: `python/docs/release-parity-fallback-report.md`.
- Async-only release notes: `docs/release-notes-v0.2.0.md`.

### Changed

- Python client direction is async-only with `pyritone.Client` as the canonical entry point.
- Docs and demos were migrated to async class-oriented usage (`async with Client()`).
- Generated command docs now use async-only examples.
- Mod and Python package versions were bumped to `0.2.0` for this release line.

### Removed

- Legacy socket bridge server code path from the mod runtime.
- Legacy sync-labeled user docs/examples (`python/docs/sync-client.md`, `python/example_sync.py`).

### Compatibility Policy

- `PyritoneClient` and `AsyncPyritoneClient` remain exported in `v0.2.x` as soft-deprecated aliases to `Client`.
- Generated sync command shims (`python/src/pyritone/commands/sync_*.py`) remain in `v0.2.x` for migration cushioning.
- `client.execute(...)` remains public as an advanced raw command escape hatch; user-facing docs should prefer generated command wrappers and typed APIs.
- Planned removal target for alias/shim compatibility surfaces: no earlier than `v0.3.0`.

## [0.1.2]

- Last release before the async-only WebSocket v2 migration line.
