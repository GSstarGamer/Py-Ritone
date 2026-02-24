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
- Only one authenticated Python session is allowed at a time per Minecraft client.
  - Additional `auth.login` attempts are rejected with `UNAUTHORIZED` while another authenticated session is active.

## Methods

- `auth.login {token}`
- `ping {}`
- `status.get {}`
- `status.subscribe {}`
- `status.unsubscribe {}`
- `api.metadata.get {target?}`
- `api.construct {type,args,parameter_types?}`
- `api.invoke {target,method,args,parameter_types?}`
- `entities.list {types?}`
- `baritone.execute {command,label?}`
- `task.cancel {task_id?}`

### `entities.list` payloads

Request:

- `types` (optional): `string[]`
- Supported entries:
  - Explicit entity IDs like `minecraft:zombie`
  - Group tokens: `group:players`, `group:mobs`

Response:

- `entities`: nearest-first array (ascending `distance_sq`) of:
  - `id`: entity UUID string
  - `type_id`: registry ID (`namespace:path`)
  - `category`: entity spawn-group category string
  - `x`, `y`, `z`: position snapshot coordinates
  - `distance_sq`: squared distance from local player

Behavior notes:

- Excludes the local player from the result set.
- Defaults to all visible world entities when `types` is omitted.

### `baritone.execute` payload notes

- `command` (required): raw Baritone command text.
- `label` (optional): human-readable notice string shown in the in-game
  `Python execute: ...` bridge message while still executing `command`.

### `status.get` / `status.update` status fields

- `status.player`:
  - object with local player identity when available:
    - `uuid`
    - `name`
    - `self` (`true` for local player snapshot)
  - `null` when local player identity is unavailable (not in-world / disconnected state).

## Events

- `task.started`
- `task.progress`
- `task.paused`
- `task.resumed`
- `task.completed`
- `task.failed`
- `task.canceled`
- `baritone.path_event`
- `bridge.pause_state`
- `chat.match` (optional watch pattern signal)
- `minecraft.chat_message`
- `minecraft.system_message`
- `minecraft.player_join`
- `minecraft.player_leave`
- `minecraft.player_death`
- `minecraft.player_respawn`
- `status.update`

### Status update payload (`status.update`)

- `data.reason`: `change` or `heartbeat`
- `data.seq`: session-local increasing sequence for status updates
- `data.status`: same shape as `status.get` result

### Chat message payload (`minecraft.chat_message`)

- `data.message`: chat text
- `data.author`:
  - object with:
    - `uuid` (nullable)
    - `name`
    - `self`
  - `null` when sender identity is unavailable
- Event stream notes:
  - Emitted from received global chat lines (single stream, no inbound/outbound split).
  - Includes local-player messages when the server echoes them to the client chat feed.

### System message payload (`minecraft.system_message`)

- `data.message`: system text
- `data.overlay`: whether this was action-bar style overlay text

### Player lifecycle payloads

- `minecraft.player_join`
- `minecraft.player_leave`
- `minecraft.player_death`
- `minecraft.player_respawn`
- Shared payload shape:
  - `data.player`:
    - `uuid` (nullable)
    - `name`
    - `self`
- Lifecycle notes:
  - Events include the local player (`self=true`), including world-enter (`player_join`) and world-exit (`player_leave`) transitions.
  - `player_leave` is debounced for a short tick window to avoid false leave/join pairs during transient entity unloads.
  - `player_respawn` is emitted only on a known dead->alive transition; unknown alive snapshots do not force respawn.

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

### Bridge pause-state payload (`bridge.pause_state`)

- `data.paused`: whether the bridge currently rejects Java-bound methods with `PAUSED`.
- `data.operator_paused`: `true` while `#pyritone pause` / `/pyritone pause` is active.
- `data.game_paused`: `true` while Minecraft reports game pause state.
- `data.reason`: one of:
  - `operator_pause`
  - `game_pause`
  - `operator_and_game_pause`
  - `resumed`
- `data.seq`: monotonic bridge pause-state transition sequence.

### Task terminal timing

- `task.completed`, `task.failed`, and `task.canceled` are emitted only after stable terminal resolution.
- Raw `baritone.path_event` hints (for example `AT_GOAL`, `CANCELED`, `CALC_FAILED`) do not immediately terminate the task.
- The bridge waits for a short quiescence window so `wait_for_task(...)` does not end early on recalculation churn.

### Hard end command semantics

- `#pyritone end` (Baritone hash command) and `/pyritone end` (Fabric command) force-close authenticated Python websocket sessions.
- This is an operator stop control and is independent from `task.cancel`.

### Operator pause/resume command semantics

- `#pyritone pause` and `/pyritone pause` enable operator pause.
- `#pyritone resume` and `/pyritone resume` clear operator pause.
- Effective pause state is `operator_paused || game_paused`.
- On each pause/resume transition, bridge publishes `bridge.pause_state`.
- While paused:
  - Java-bound methods return immediate error `PAUSED` with pause snapshot in `error.data`.
  - Gated methods:
    - `status.get`, `status.subscribe`, `status.unsubscribe`
    - `entities.list`
    - `api.metadata.get`, `api.construct`, `api.invoke`
    - `baritone.execute`
    - `task.cancel`
  - Non-gated methods remain available:
    - `auth.login`
    - `ping`

## Error Codes

- `UNAUTHORIZED`
- `BAD_REQUEST`
- `METHOD_NOT_FOUND`
- `PAUSED`
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
