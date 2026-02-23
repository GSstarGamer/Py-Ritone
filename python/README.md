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

## Public API Map

- Clients:
  - `Client` (primary)
  - `PyritoneClient`
  - `AsyncPyritoneClient`
  - `PyritoneClient` and `AsyncPyritoneClient` are temporary async aliases of `Client`.
- Low-level methods:
  - `ping`, `status_get`, `status_subscribe`, `status_unsubscribe`, `execute`, `cancel`, `next_event`, `wait_for`, `wait_for_task`
  - Typed API substrate: `api_metadata_get`, `api_construct`, `api_invoke`
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

## Auto-Discovery (Zero-Setup)

By default, `pyritone` discovers bridge metadata from:

- `<minecraft>/config/pyritone_bridge/bridge-info.json`

Override precedence:

1. Explicit constructor args
2. Environment variables: `PYRITONE_BRIDGE_INFO`, `PYRITONE_TOKEN`, `PYRITONE_HOST`, `PYRITONE_PORT`
3. Auto-discovered bridge info file
