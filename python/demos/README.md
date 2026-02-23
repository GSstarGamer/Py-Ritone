# Pyritone Demo Suite

Beginner-friendly demos for the current Python feature set.

## Prerequisites

1. Install the package (editable install is easiest from repo root):

```bash
python -m pip install -e ./python
```

2. Start Minecraft with the `pyritone_bridge` mod and Baritone installed.
3. Join a world for world-dependent demos (`goto`, `explore`, build commands).

## How To Run

From repo root:

```bash
cd python
python demos/01_connect_discovery.py
```

Each demo uses default discovery (`bridge-info.json` / `PYRITONE_*`) and fails gracefully when the bridge is not ready.

## Demo Catalog

| Script | What this demo proves | Run command | Suggested video filename | Video URL |
|---|---|---|---|---|
| `01_connect_discovery.py` | Zero-setup discovery + connection/auth + baseline ping/status | `python demos/01_connect_discovery.py` | `01-connect-discovery.mp4.mp4` | [Watch](https://github.com/GSstarGamer/Py-Ritone/blob/main/python/demos/01-connect-discovery.mp4.mp4) |
| `02_basic_commands.py` | High-level wrappers plus raw `execute(...)` fallback | `python demos/02_basic_commands.py` | `02-basic-commands.mp4` | [Watch](https://github.com/GSstarGamer/Py-Ritone/blob/main/python/demos/02-basic-commands.mp4) |
| `03_goto_completion.py` | `goto(...)` dispatch + `wait_for_task(...)` with pause/resume update logs | `python demos/03_goto_completion.py 100 70 100` | `03-goto-completion.mp4` | [Watch](https://github.com/GSstarGamer/Py-Ritone/blob/main/python/demos/03-goto-completion.mp4) |
| `04_live_event_feed.py` | Auto-dispatches a high-Y `goto`, then prints concise live task/path event lines | `python demos/04_live_event_feed.py --x 0 --y 1000 --z 0 --max-events 30` | `04-live-event-feed.mp4` | [Watch](https://github.com/GSstarGamer/Py-Ritone/blob/main/python/demos/04-live-event-feed.mp4) |
| `05_cancel_task.py` | Start task, cancel by task id, observe terminal event | `python demos/05_cancel_task.py --delay 1.5` | `05-cancel-task.mp4` | [Watch](https://github.com/GSstarGamer/Py-Ritone/blob/main/python/demos/05-cancel-task.mp4) |
| `06_settings_mode_switch.py` | Sync settings API: property assignment + get/set/toggle/reset + presets | `python demos/06_settings_mode_switch.py --mode builder` | `06-settings-mode-switch.mp4` | [Watch](https://github.com/GSstarGamer/Py-Ritone/blob/main/python/demos/06-settings-mode-switch.mp4) |
| `07_mini_console.py` | Interactive mini console with dynamic wrapper dispatch | `python demos/07_mini_console.py` | `07-mini-console.mp4` | [Watch](https://github.com/GSstarGamer/Py-Ritone/blob/main/python/demos/07-mini-console.mp4) |
| `08_async_workflow.py` | Async-only concurrency: heartbeat pings while `wait_for_task(...)` prints pause/resume updates | `python demos/08_async_workflow.py 0 1000 0 --cancel-after 6 --heartbeat-interval 1.5` | `08-async-workflow.mp4` | [Watch](https://github.com/GSstarGamer/Py-Ritone/blob/main/python/demos/08-async-workflow.mp4) |
| `09_build_file_local_path.py` | `build_file(...)` + local path resolution + pause-aware wait logs | `python demos/09_build_file_local_path.py "schematics/base" --coords 100 70 100 --wait` | `09-build-file-local-path.mp4` | [Watch](https://github.com/GSstarGamer/Py-Ritone/blob/main/python/demos/09-build-file-local-path.mp4) |
| `10_cli_entrypoints.py` | CLI usage via subprocess (`ping`, `status`, `exec`, `cancel`) | `python demos/10_cli_entrypoints.py` | `10-cli-entrypoints.mp4` | [Watch](https://github.com/GSstarGamer/Py-Ritone/blob/main/python/demos/10-cli-entrypoints.mp4) |

## Feature Coverage Matrix

| Feature | Covered by |
|---|---|
| Connect + discovery + auth | `01_connect_discovery.py`, `08_async_workflow.py` |
| Sync client | `01`, `02`, `03`, `04`, `05`, `06`, `07`, `09` |
| Async client | `08_async_workflow.py` |
| High-level command wrappers | `02`, `03`, `05`, `08`, `09` |
| Raw `execute(...)` | `02`, `07` |
| Task IDs + `wait_for_task(...)` | `03`, `05`, `08` |
| Event feed / `next_event(...)` | `04`, `07`, `08` |
| Canceling | `05`, `07`, `10` |
| Settings API (`set/get/toggle/reset`) | `06`, `07`, `08` |
| Local schematic helper (`build_file`) | `09` |
| CLI entrypoint | `10` |
| Error handling / graceful failure | all demos via shared `_common.py` (except `10`, which reports subprocess failures directly) |

## Graceful Failure Behavior

- If discovery fails (`DiscoveryError`), demos explain how to start Minecraft once or set `PYRITONE_TOKEN` / `PYRITONE_BRIDGE_INFO`.
- If bridge socket is unreachable, demos explain that Minecraft + bridge must be running.
- If `NOT_IN_WORLD` is returned, demos explain to join a world before running world-dependent commands.
- If `BARITONE_UNAVAILABLE` is returned, demos explain to install/load the Baritone mod.

## Hard Cancel Tip

- To force-end the active tracked task from in-game and immediately unblock waiting Python scripts, run `#pyritone cancel`.
- Fallback command: `/pyritone cancel`.

## Good Recording Order

1. `01_connect_discovery.py`
2. `02_basic_commands.py`
3. `06_settings_mode_switch.py`
4. `03_goto_completion.py`
5. `04_live_event_feed.py`
6. `05_cancel_task.py`
7. `09_build_file_local_path.py`
8. `08_async_workflow.py`
9. `07_mini_console.py`
10. `10_cli_entrypoints.py`
