# Tasks, Events, And Waiting

How to handle dispatch, task IDs, and terminal task events.

### When to use this

- You need completion/failure state, not just dispatch success.
- You want to consume bridge events (`task.*`, `baritone.path_event`, etc.).

### Sync example

```python
from pyritone import PyritoneClient

with PyritoneClient() as client:
    dispatch = client.goto(100, 70, 100)
    print(dispatch)

    task_id = dispatch.get("task_id")
    if task_id:
        terminal = client.wait_for_task(task_id)
        print(terminal["event"], terminal["data"])
```

### Async example

```python
from pyritone import AsyncPyritoneClient

client = AsyncPyritoneClient()
await client.connect()
try:
    dispatch = await client.goto(100, 70, 100)
    task_id = dispatch.get("task_id")
    if task_id:
        terminal = await client.wait_for_task(task_id)
        print(terminal["event"], terminal["data"])
finally:
    await client.close()
```

### Return shape

```text
Task terminal event envelope:
- type: "event"
- event: one of task.completed/task.failed/task.canceled
- data: includes task_id and optional reason/detail
- ts: ISO-8601 timestamp
```

### Terminal timing semantics

- `wait_for_task(task_id)` now waits for stable terminal state, not the first raw path hint.
- Internal Baritone recalculations can emit temporary `baritone.path_event` values like `CANCELED` or `CALC_FAILED`; those are treated as hints until the task is truly idle.
- This prevents early exits during long `goto`, `build`, and recalculation-heavy flows.

### Common mistakes

- Ignoring `task.failed` and assuming all terminal events are success.
- Waiting for the wrong task ID in multi-command flows.
- Dropping events by not reading them during long-running sessions.

### Related methods

- `sync-client.md`
- `async-client.md`
- `commands/navigation.md`
