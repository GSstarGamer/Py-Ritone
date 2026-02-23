# Async Client

Guide for `Client` in asyncio code.

### When to use this

- Your app already uses asyncio.
- You want event-stream friendly control flow.

### Example

```python
import asyncio
from pyritone import Client


async def main() -> None:
    client = Client()
    await client.connect()
    try:
        print(await client.ping())
        print(await client.status_get())
        await client.status_subscribe()

        dispatch = await client.build_file("schematics/base.schem", 100, 70, 100)
        print(dispatch)

        task_id = dispatch.get("task_id")
        if task_id:
            terminal = await client.wait_for_task(task_id)
            print(terminal)

        # Convenience helper that dispatches + waits in one call
        print(await client.build_file_wait("schematics/base.schem", 100, 70, 100))

        # Cached state/task surfaces
        print(client.state.snapshot)
        print(client.task.id, client.task.state)
    finally:
        await client.close()


asyncio.run(main())
```

### Return shape

```text
Async low-level methods return awaitable dict[str, Any] payloads.
Command wrappers return awaitable CommandDispatchResult.
events()/next_event() return event envelope dictionaries.
client.state caches the latest known status payload.
client.task exposes active-task convenience accessors.
Typed API methods are available via:
- await api_metadata_get(...)
- await api_construct(...)
- await api_invoke(...)
Typed calls may return RemoteRef handles for non-JSON values.

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

- `tasks-events-and-waiting.md`
- `settings-api.md`
