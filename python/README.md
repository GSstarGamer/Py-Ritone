# pyritone

`pyritone` is the Python client for the Py-Ritone Fabric bridge.

## Install

```bash
pip install pyritone
```

## Fastest Working Async Example

```python
import asyncio
from pyritone import Client


async def main() -> None:
    client = Client()
    await client.connect()
    try:
        print(await client.ping())
        dispatch = await client.build_file("schematics/base.schem", 100, 70, 100)
        print(dispatch)
    finally:
        await client.close()


asyncio.run(main())
```

## Demos

The quick examples above are intentionally small.

For full, recordable feature walkthroughs, see:

- `python/demos/README.md`

Run from repo root:

```bash
python -m pip install -e ./python
cd python
python demos/01_connect_discovery.py
```

## Docs

- Full docs index: `python/docs/index.md`
- Quickstart: `python/docs/quickstart.md`
- Async client guide: `python/docs/async-client.md`
- Legacy import migration: `python/docs/migration-from-legacy-aliases.md`
- Settings API: `python/docs/settings-api.md`
- Tasks/events/waiting: `python/docs/tasks-events-and-waiting.md`
- Errors/troubleshooting: `python/docs/errors-and-troubleshooting.md`
- CLI usage: `python/docs/cli.md`
- Command docs:
  - `python/docs/commands/navigation.md`
  - `python/docs/commands/world.md`
  - `python/docs/commands/build.md`
  - `python/docs/commands/control.md`
  - `python/docs/commands/info.md`
  - `python/docs/commands/waypoints.md`
  - `python/docs/commands/aliases.md`
- Raw Baritone appendix: `python/docs/baritone-commands.md`
- Typed parity matrix: `python/docs/baritone-typed-parity.md`
- Release parity/debt report: `python/docs/release-parity-fallback-report.md`

## Public API Map

- Clients:
  - `Client` (primary async surface)
  - Legacy aliases (`PyritoneClient`, `AsyncPyritoneClient`) are compatibility-only; use `Client` in docs and new code.
- Low-level methods:
  - `ping`, `status_get`, `status_subscribe`, `status_unsubscribe`, `execute`, `cancel`, `next_event`, `wait_for`, `wait_for_task`
  - `execute(...)` is an advanced raw command path; prefer generated command wrappers and typed APIs in new code.
  - Typed API substrate: `api_metadata_get`, `api_construct`, `api_invoke`
- Typed Baritone wrappers:
  - `client.baritone` root namespace over Wave 4 typed calls
  - goal constructors under `client.baritone.goals.*`
  - typed process/behavior wrappers (`custom_goal_process`, `mine_process`, `get_to_block_process`, `explore_process`, `pathing_behavior`)
  - Wave 7 package wrappers:
    - cache (`world_provider`, `world_scanner`, `waypoint` helpers)
    - selection (`selection_manager`, `SelectionRef`)
    - command (`command_manager`, provider `command_system`)
    - schematic (`schematic_system`, `fill_schematic`, `composite_schematic`, mask helpers)
    - utils (`player_context`, `input_override_handler`, enum/position helpers)
    - event (`game_event_handler`, `EventBusRef`)
  - minecraft identifier constants accepted by typed wrappers:
    - `from pyritone.minecraft import blocks, items, entities`
    - e.g. `await mine_process.mine_by_name(64, blocks.DIAMOND_ORE)`
  - task-producing typed methods wait by default; `_dispatch` returns `TypedTaskHandle`
- Command wrappers:
  - All top-level Baritone commands exposed as methods.
- Local schematic helpers:
  - `build_file(path, *coords, base_dir=None)`
  - `build_file_wait(path, *coords, base_dir=None)`
- Settings namespace:
  - `await client.settings.allowPlace.set(True)`
- State/task cache:
  - `client.state.snapshot`, `client.task.id`, `client.task.state`, `await client.task.wait()`
- Typed remote references:
  - `RemoteRef(ref_id=..., java_type=...)` values returned by `api_construct` / `api_invoke`

## Compatibility Policy (v0.2.x)

- `PyritoneClient` and `AsyncPyritoneClient` remain exported as temporary compatibility aliases.
- Generated sync command shim modules (`python/src/pyritone/commands/sync_*.py`) remain for migration cushioning.
- Both compatibility surfaces are soft-deprecated and planned for removal no earlier than `v0.3.0`.
- Keep new docs/examples on `Client` + async command/typed APIs; use raw `execute(...)` only for advanced/interop cases.

## Auto-Discovery (Zero-Setup)

By default, `pyritone` discovers bridge metadata from:

- `<minecraft>/config/pyritone_bridge/bridge-info.json`

Override precedence:

1. Explicit constructor args
2. Environment variables: `PYRITONE_BRIDGE_INFO`, `PYRITONE_TOKEN`, `PYRITONE_HOST`, `PYRITONE_PORT`
3. Auto-discovered bridge info file
