# Async Client

Guide for `AsyncPyritoneClient` in asyncio code.

### When to use this

- Your app already uses asyncio.
- You want event-stream friendly control flow.

### Sync example

```python
# Use PyritoneClient instead; see sync-client.md.
```

### Async example

```python
import asyncio
from pyritone import AsyncPyritoneClient


async def main() -> None:
    client = AsyncPyritoneClient()
    await client.connect()
    try:
        print(await client.ping())
        print(await client.status_get())

        dispatch = await client.build_file("schematics/base.schem", 100, 70, 100)
        print(dispatch)

        task_id = dispatch.get("task_id")
        if task_id:
            terminal = await client.wait_for_task(task_id)
            print(terminal)

        # Convenience helper that dispatches + waits in one call
        print(await client.build_file_wait("schematics/base.schem", 100, 70, 100))
    finally:
        await client.close()


asyncio.run(main())
```

### Return shape

```text
Async low-level methods return awaitable dict[str, Any] payloads.
Command wrappers return awaitable CommandDispatchResult.
events()/next_event() return event envelope dictionaries.

Build helpers:
- await build_file(...) -> CommandDispatchResult
- await build_file_wait(...) -> terminal event envelope dict[str, Any]
```

### Common mistakes

- Calling command methods before `await client.connect()`.
- Not closing the client in `finally`.
- Passing 1 or 2 coordinates to `build_file` (must be 0 or 3).
- Assuming relative paths are from cwd; default is caller file directory.
- Blocking event-loop threads with sync operations while waiting for events.

### Related methods

- `sync-client.md`
- `tasks-events-and-waiting.md`
- `settings-api.md`
