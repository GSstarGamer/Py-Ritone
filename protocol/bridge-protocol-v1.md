# Py-Ritone Bridge Protocol v1

## Transport

- TCP socket on `127.0.0.1:27841`
- UTF-8 NDJSON (one JSON object per line)

## Envelope Types

### Request

```json
{"type":"request","id":"uuid","method":"status.get","params":{}}
```

### Response (success)

```json
{"type":"response","id":"uuid","ok":true,"result":{}}
```

### Response (error)

```json
{"type":"response","id":"uuid","ok":false,"error":{"code":"UNAUTHORIZED","message":"..."}}
```

### Event

```json
{"type":"event","event":"task.progress","data":{},"ts":"2026-01-01T00:00:00Z"}
```

## Methods

- `auth.login {token}`
- `ping {}`
- `status.get {}`
- `baritone.execute {command}`
- `task.cancel {task_id?}`

## Events

- `task.started`
- `task.progress`
- `task.paused`
- `task.resumed`
- `task.completed`
- `task.failed`
- `task.canceled`
- `baritone.path_event`
- `chat.match` (optional watch pattern signal)

### Pause event payload (`task.paused`)

- `data.pause.reason_code`
- `data.pause.source_process`
- `data.pause.command_type`

### Task terminal timing

- `task.completed`, `task.failed`, and `task.canceled` are emitted only after stable terminal resolution.
- Raw `baritone.path_event` hints (for example `AT_GOAL`, `CANCELED`, `CALC_FAILED`) do not immediately terminate the task.
- The bridge waits for a short quiescence window so internal recalculation churn does not end `wait_for_task(...)` early.

### Hard cancel command semantics

- `#pyritone cancel` (Baritone hash command) and `/pyritone cancel` (Fabric command) trigger a hard cancel path.
- Hard cancel force-terminates the active tracked task with `task.canceled` stage `pyritone_cancel_command`, so waiting Python clients exit immediately.

## Error Codes

- `UNAUTHORIZED`
- `BAD_REQUEST`
- `METHOD_NOT_FOUND`
- `NOT_IN_WORLD`
- `BARITONE_UNAVAILABLE`
- `EXECUTION_FAILED`
- `INTERNAL_ERROR`
