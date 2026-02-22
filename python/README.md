# pyritone

`pyritone` is the Python client for the Py-Ritone Fabric bridge.

## Install

```bash
pip install pyritone
```

## Beginner usage

```python
from pyritone import PyritoneClient

with PyritoneClient() as client:
    client.goto(100, 70, 100)
```

## Advanced usage

For developer workflows, lower-level APIs are still available:

- `execute("...")`
- `next_event()`
- `wait_for_task(task_id)`

## Zero-setup discovery

By default, `pyritone` discovers bridge details from:

- `<minecraft>/config/pyritone_bridge/bridge-info.json`

Override priority:

1. Explicit constructor args
2. Environment variables (`PYRITONE_BRIDGE_INFO`, `PYRITONE_TOKEN`, `PYRITONE_HOST`, `PYRITONE_PORT`)
3. Default bridge info file

## CLI

```bash
pyritone ping
pyritone status
pyritone exec "goto 100 70 100"
pyritone cancel
pyritone events
```

## End-to-End Dev Test

1. Start Minecraft dev client from the mod folder:

```powershell
cd ..\mod
.\gradlew.bat devClient
```

2. Join a world.
3. Run the example script:

```powershell
cd ..\python
python example.py --x 100 --y 70 --z 100
```
