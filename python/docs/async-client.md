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
    async with Client() as client:
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
Wave 5 typed Baritone wrappers:
- client.baritone.goals.* constructors for Goal objects
- await client.baritone.custom_goal_process() / mine_process() / get_to_block_process() / explore_process()
- minecraft ID constants:
  - from pyritone.minecraft import blocks, items, entities
  - e.g. await client.baritone.mine_process().mine_by_name(16, blocks.COAL_ORE)
- task-producing typed wrappers wait by default
- *_dispatch variants return TypedTaskHandle for manual wait control
Wave 7 typed wrappers add:
- cache: world provider/data/cache/waypoint wrappers + world scanner access
- selection: selection manager and selection geometry wrappers
- command: command manager/system/parser-manager/registry wrappers
- schematic: schematic-system/format wrappers plus typed schematic + mask constructors
- utils + event: player context, input override, and event-bus listener wrappers
- parity matrix: python/docs/baritone-typed-parity.md

Build helpers:
- await build_file(...) -> CommandDispatchResult
- await build_file_wait(...) -> terminal event envelope dict[str, Any]
```

### Common mistakes

- Calling command methods before entering `async with Client()`.
- Leaking client sessions by skipping context management.
- Passing 1 or 2 coordinates to `build_file` (must be 0 or 3).
- Assuming relative paths are from cwd; default is caller file directory.
- Blocking event-loop threads with sync operations while waiting for events.

### Related methods

- `tasks-events-and-waiting.md`
- `settings-api.md`
- `baritone-typed-parity.md`
