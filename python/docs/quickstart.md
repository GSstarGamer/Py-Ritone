# Quickstart

Go from install to first command in a few minutes.

### When to use this

- You just installed `pyritone`.
- You want the shortest path to a working call.

### Sync example

```python
from pyritone import PyritoneClient

with PyritoneClient() as client:
    print(client.ping())
    print(client.status_get())
    dispatch = client.goto(100, 70, 100)
    print(dispatch)
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
    finally:
        await client.close()


asyncio.run(main())
```

### Return shape

```text
ping/status_get return dict[str, Any] payloads.
goto and other command wrappers return CommandDispatchResult:
- command_text
- raw
- task_id (optional)
- accepted (optional)
```

### Common mistakes

- Running Python before Minecraft has started with `pyritone_bridge`.
- Calling command wrappers before joining a world (may return `NOT_IN_WORLD`).
- Treating dispatch as completion; use `wait_for_task` when `task_id` exists.

### Related methods

- `connection-and-discovery.md`
- `tasks-events-and-waiting.md`
- `commands/navigation.md`

