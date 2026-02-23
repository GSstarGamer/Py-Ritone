# Quickstart

Go from install to first command in a few minutes.

### When to use this

- You just installed `pyritone`.
- You want the shortest path to a working call.

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
        dispatch = await client.build_file("schematics/base.schem", 100, 70, 100)
        print(dispatch)

        task_id = dispatch.get("task_id")
        if task_id:
            print(await client.wait_for_task(task_id))
    finally:
        await client.close()


asyncio.run(main())
```

### Return shape

```text
ping/status_get return dict[str, Any] payloads.
build_file and other command wrappers return CommandDispatchResult:
- command_text
- raw
- task_id (optional)
- accepted (optional)
```

### Common mistakes

- Running Python before Minecraft has started with `pyritone_bridge`.
- Calling build commands before joining a world (may return `NOT_IN_WORLD`).
- Using relative paths that are not relative to your script file (set `base_dir` to override).
- Treating dispatch as completion; use `wait_for_task` when `task_id` exists.

### Related methods

- `connection-and-discovery.md`
- `tasks-events-and-waiting.md`
- `commands/navigation.md`
