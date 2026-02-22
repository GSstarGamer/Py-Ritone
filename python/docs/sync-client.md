# Sync Client

Guide for `PyritoneClient` in synchronous Python code.

### When to use this

- Your project is not asyncio-based.
- You want context-manager style usage.

### Sync example

```python
from pyritone import PyritoneClient

with PyritoneClient() as client:
    print(client.ping())
    print(client.status_get())

    dispatch = client.build_file("schematics/base.schem", 100, 70, 100)
    print(dispatch)

    task_id = dispatch.get("task_id")
    if task_id:
        terminal = client.wait_for_task(task_id)
        print(terminal)

    # Convenience helper that dispatches + waits in one call
    print(client.build_file_wait("schematics/base.schem", 100, 70, 100))
```

### Async example

```python
# Use AsyncPyritoneClient instead; see async-client.md.
```

### Return shape

```text
Low-level methods:
- ping/status_get/execute/cancel -> dict[str, Any]
- next_event/wait_for_task -> event envelope dict[str, Any]

Command methods:
- CommandDispatchResult

build helpers:
- build_file(...) -> CommandDispatchResult
- build_file_wait(...) -> terminal event envelope dict[str, Any]
```

### Common mistakes

- Creating a sync client and forgetting to close it outside a `with` block.
- Assuming command wrappers block until completion by default.
- Passing 1 or 2 coordinates to `build_file` (must be 0 or 3).
- Assuming relative paths are from cwd; default is caller file directory.
- Passing invalid argument shapes to command wrappers.

### Related methods

- `async-client.md`
- `tasks-events-and-waiting.md`
- `settings-api.md`
