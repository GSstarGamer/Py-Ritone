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

- `wait_for_task(task_id)` waits for matching terminal task events (`task.completed`, `task.failed`, `task.canceled`).
- `goto_wait(...)` keeps responsiveness fast paths for `baritone.path_event` hints:
  - `AT_GOAL` -> synthetic `task.completed`
  - `CANCELED` -> synthetic `task.canceled`
- When bridge pause is active (`bridge.pause_state.paused=true`) or the tracked
  task is paused, `CANCELED` hints do not fast-complete the wait.
- Those path-hint fast paths can resolve before later bridge terminal events.

### Bridge pause-state events and request behavior

- Bridge emits `bridge.pause_state` with:
  - `paused`
  - `operator_paused`
  - `game_paused`
  - `reason`
  - `seq`
- On RPC error `PAUSED`, Python client transparently waits for resumed
  (`bridge.pause_state.paused=false`) and retries the same request.
- If websocket closes while waiting for resume, pending request raises
  `ConnectionError`.

### `goto_entity(..., wait=True)` retarget behavior

- If pause/resume transitions occur while waiting, `goto_entity(..., wait=True)`
  refreshes that same entity id/type and re-dispatches to latest rounded
  coordinates before returning.
- If the entity is no longer visible after resume, client raises
  `BridgeError(code="ENTITY_NOT_VISIBLE", ...)` so caller can skip intentionally.

### Logging of states and pathing

- By default, logger `pyritone` focuses on command-send logs at `INFO`.
- Task/status/path transition details are emitted at `DEBUG`.
- `baritone.path_event` values are inferred into pathing states at `DEBUG`:
  - `*CALC*START*` -> `calculating`
  - `*CALC*FINISH*` / success-like events -> `best_path_ready`
  - `*CALC*FAIL*` -> `calculation_failed`
  - `AT_GOAL` -> `at_goal`
  - `CANCELED` -> `canceled`
- Typed Baritone wait handles also log transition-focused `moving` / `calculating` state changes and completion summaries at `DEBUG`.

### Hard stop from in-game

- Use `#pyritone end` (or `/pyritone end`) to close authenticated Python websocket sessions.
- This operator stop control is separate from API task cancellation (`task.cancel`).

### Common mistakes

- Ignoring `task.failed` and assuming all terminal events are success.
- Waiting for the wrong task ID in multi-command flows.
- Dropping events by not reading them during long-running sessions.

### Related methods

- `async-client.md`
- `commands/navigation.md`
- `status_subscribe` / `status_unsubscribe`
