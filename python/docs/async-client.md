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

        dispatch = await client.goto(100, 70, 100)
        print(dispatch)

        task_id = dispatch.get("task_id")
        if task_id:
            terminal = await client.wait_for_task(task_id)
            print(terminal)
    finally:
        await client.close()


asyncio.run(main())
```

### Return shape

```text
Async low-level methods return awaitable dict[str, Any] payloads.
Command wrappers return awaitable CommandDispatchResult.
events()/next_event() return event envelope dictionaries.
```

### Common mistakes

- Calling command methods before `await client.connect()`.
- Not closing the client in `finally`.
- Blocking event-loop threads with sync operations while waiting for events.

### Related methods

- `sync-client.md`
- `tasks-events-and-waiting.md`
- `settings-api.md`

