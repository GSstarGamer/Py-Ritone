# Py-Ritone Bridge Protocol v2

## Transport

- WebSocket endpoint on loopback only.
- URL: `ws://127.0.0.1:27841/ws`
- UTF-8 JSON text messages (one JSON object per frame)

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

## Auth Model

- A client must authenticate first using `auth.login`.
- Allowed without authentication:
  - `auth.login`
  - `ping`
- All other methods return `UNAUTHORIZED` until session auth succeeds.

## Methods

- `auth.login {token}`
- `ping {}`
- `status.get {}`
- `status.subscribe {}`
- `status.unsubscribe {}`
- `api.metadata.get {target?}`
- `api.construct {type,args,parameter_types?}`
- `api.invoke {target,method,args,parameter_types?}`
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
- `status.update`

### Status update payload (`status.update`)

- `data.reason`: `change` or `heartbeat`
- `data.seq`: session-local increasing sequence for status updates
- `data.status`: same shape as `status.get` result

### Typed API payloads

- Target object (for `api.metadata.get` and `api.invoke`):
  - Root target: `{"kind":"root","name":"baritone"}`
  - Remote ref target: `{"kind":"ref","id":"ref-1"}`
  - Type target (static metadata/invoke): `{"kind":"type","name":"java.lang.Math"}`
- Remote reference value envelope:
  - `{"$pyritone_ref":"ref-1","java_type":"..."}`
- `api.construct` response:
  - `result.value`: encoded typed value (primitive/list/map/ref envelope)
  - `result.java_type`: JVM type name of constructed instance
- `api.invoke` response:
  - `result.value`: encoded typed return value
  - `result.return_type`: JVM return type name
- `api.metadata.get` response:
  - `result.metadata_version`
  - `result.roots` (when no target) and/or `result.type` descriptors (constructors/methods)

### Pause event payload (`task.paused`)

- `data.pause.reason_code`
- `data.pause.source_process`
- `data.pause.command_type`

### Task terminal timing

- `task.completed`, `task.failed`, and `task.canceled` are emitted only after stable terminal resolution.
- Raw `baritone.path_event` hints (for example `AT_GOAL`, `CANCELED`, `CALC_FAILED`) do not immediately terminate the task.
- The bridge waits for a short quiescence window so `wait_for_task(...)` does not end early on recalculation churn.

### Hard cancel command semantics

- `#pyritone cancel` (Baritone hash command) and `/pyritone cancel` (Fabric command) trigger a hard cancel path.
- Hard cancel force-terminates the active tracked task with `task.canceled` stage `pyritone_cancel_command`.

## Error Codes

- `UNAUTHORIZED`
- `BAD_REQUEST`
- `METHOD_NOT_FOUND`
- `NOT_IN_WORLD`
- `BARITONE_UNAVAILABLE`
- `EXECUTION_FAILED`
- `INTERNAL_ERROR`
- `API_TARGET_NOT_FOUND`
- `API_TARGET_UNAVAILABLE`
- `API_TYPE_NOT_FOUND`
- `API_REFERENCE_NOT_FOUND`
- `API_CONSTRUCTOR_NOT_FOUND`
- `API_METHOD_NOT_FOUND`
- `API_AMBIGUOUS_CALL`
- `API_ARGUMENT_COERCION_FAILED`
- `API_INVOCATION_ERROR`

Typed API errors may include structured details in `error.data`.
