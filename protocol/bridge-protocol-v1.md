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
- `task.completed`
- `task.failed`
- `task.canceled`
- `baritone.path_event`
- `chat.match` (optional watch pattern signal)

## Error Codes

- `UNAUTHORIZED`
- `BAD_REQUEST`
- `METHOD_NOT_FOUND`
- `NOT_IN_WORLD`
- `BARITONE_UNAVAILABLE`
- `EXECUTION_FAILED`
- `INTERNAL_ERROR`
