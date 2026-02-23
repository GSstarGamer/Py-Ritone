# Pyritone Demo Suite

Beginner-friendly demos for learning and validating the current Python feature set.

## Who This Is For

This guide is for anyone using Pyritone, not just maintainers. Each demo is a runnable example you can use to learn the API and verify your local setup.

## Prerequisites

1. Install the package (editable install from repo root):

```bash
python -m pip install -e ./python
```

2. Start Minecraft with the `pyritone_bridge` mod and Baritone installed.
3. Join a world for world-dependent demos (`goto`, build, cancel, live task events).

## Quick Start

From repo root:

```bash
cd python
python demos/01_connect_discovery.py
```

All demos use default discovery (`bridge-info.json` / `PYRITONE_*`) and print helpful error hints if the bridge is not ready.

## Demo Catalog

| Script | What you learn | Needs world | Run command |
|---|---|---|---|
| `01_connect_discovery.py` | Discovery, connect/auth, baseline `ping` and `status` | No | `python demos/01_connect_discovery.py` |
| `02_basic_commands.py` | High-level wrappers and raw `execute(...)` fallback | Usually yes | `python demos/02_basic_commands.py` |
| `03_goto_completion.py` | `goto(...)` plus `wait_for_task(...)` with progress updates | Yes | `python demos/03_goto_completion.py 100 70 100` |
| `04_live_event_feed.py` | Streaming task/path events from live execution | Yes | `python demos/04_live_event_feed.py --x 0 --y 1000 --z 0 --max-events 30` |
| `05_cancel_task.py` | Cancel by task id and observe terminal event behavior | Yes | `python demos/05_cancel_task.py --delay 1.5` |
| `06_settings_mode_switch.py` | Settings API: assignment + get/set/toggle/reset + presets | No | `python demos/06_settings_mode_switch.py --mode builder` |
| `07_mini_console.py` | Interactive console workflow for manual command testing | Usually yes | `python demos/07_mini_console.py` |
| `08_async_workflow.py` | Async usage with concurrent heartbeat + task waiting | Yes | `python demos/08_async_workflow.py 0 1000 0 --cancel-after 6 --heartbeat-interval 1.5` |
| `09_build_file_local_path.py` | `build_file(...)` local path helper and pause-aware wait logs | Yes | `python demos/09_build_file_local_path.py "house.schem" --coords 100 -60 100 --wait` |
| `10_cli_entrypoints.py` | CLI usage (`ping`, `status`, `exec`, `cancel`) from Python subprocess calls | Depends on command | `python demos/10_cli_entrypoints.py` |

## Optional Demo Videos

If you prefer to watch before running, demo videos are available in the repo:
<https://github.com/GSstarGamer/Py-Ritone/tree/main/python/demos>

## Common Failure Cases

- `DiscoveryError`: start Minecraft once so bridge info exists, or set `PYRITONE_TOKEN` / `PYRITONE_BRIDGE_INFO`.
- Socket/connect errors: ensure Minecraft is running with `pyritone_bridge` and Baritone loaded.
- `NOT_IN_WORLD`: join a world before running world-dependent demos.
- `BARITONE_UNAVAILABLE`: install or load the Baritone mod.

## Hard Cancel Tip

To force-stop the active tracked task from in-game and immediately unblock waiting scripts, run `#pyritone cancel` (or `/pyritone cancel`).
