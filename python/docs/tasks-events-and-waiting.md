# Tasks, Events, And Waiting

How to handle dispatch, task IDs, and terminal task events.

### When to use this

- You need completion/failure state, not just dispatch success.
- You want to consume bridge events (`task.*`, `baritone.path_event`, etc.).
- You want cached status snapshots via `client.state` and `status.update`.

### Example

```python
import asyncio
from pyritone import Client


async def main() -> None:
    async with Client() as client:
        dispatch = await client.goto(100, 70, 100)
        task_id = dispatch.get("task_id")
        if task_id:
            terminal = await client.wait_for_task(task_id, on_update=lambda event: print("update:", event["event"]))
            print(terminal["event"], terminal["data"])


asyncio.run(main())
```

### Return shape

```text
Task terminal event envelope:
- type: "event"
- event: one of task.completed/task.failed/task.canceled
- data: includes task_id and optional reason/detail
- ts: ISO-8601 timestamp
```

```text
Non-terminal update events for the same task_id:
- task.progress
- task.paused
- task.resumed
```

### Terminal timing semantics

- `wait_for_task(task_id)` now waits for stable terminal state, not the first raw path hint.
- Internal Baritone recalculations can emit temporary `baritone.path_event` values like `CANCELED` or `CALC_FAILED`; those are treated as hints until the task is truly idle.
- This prevents early exits during long `goto`, `build`, and recalculation-heavy flows.
- During pause states (for example builder pause or user pause), `wait_for_task(...)` keeps waiting and can report updates through `on_update`.

### Hard stop from in-game

- Use `#pyritone cancel` (or `/pyritone cancel`) to hard-cancel the active tracked task.
- Hard cancel emits `task.canceled` immediately so waiting Python scripts end right away.

### Common mistakes

- Ignoring `task.failed` and assuming all terminal events are success.
- Waiting for the wrong task ID in multi-command flows.
- Dropping events by not reading them during long-running sessions.

### Related methods

- `async-client.md`
- `commands/navigation.md`
- `status_subscribe` / `status_unsubscribe`
