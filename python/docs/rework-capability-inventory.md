# WS v2 Async Rework Capability Inventory (v0.2.0)

Exhaustive capability inventory for the `feat/ws-v2-async` rework, merged at `ffc9a4a` and released as `v0.2.0`.

## Scope

- Rework waves completed: Wave 1 through Wave 9.
- Release state: tag `v0.2.0` on commit `ffc9a4a`.
- Protocol baseline: WebSocket v2 (`protocol/bridge-protocol-v2.md`).

## 1. Transport and Protocol Capabilities

- Bridge transport migrated from TCP NDJSON to WebSocket JSON envelopes.
- WebSocket endpoint support (`/ws`) with auth handshake (`auth.login`).
- Structured request/response/event framing with request ID correlation.
- Event stream transport for task and status events.
- Session-scoped status streaming methods:
  - `status.subscribe`
  - `status.unsubscribe`
  - `status.update` events with change/heartbeat semantics.
- Typed API transport methods:
  - `api.metadata.get`
  - `api.construct`
  - `api.invoke`
- Discovery metadata supports:
  - `transport`
  - `ws_url`
  - `ws_path`
  - `protocol_version`
  - `server_version`

## 2. Discovery and Connection Capabilities

- Bridge resolution precedence supports:
  - explicit constructor args
  - environment variables
  - bridge-info file auto-discovery
- Environment inputs:
  - `PYRITONE_BRIDGE_INFO`
  - `PYRITONE_HOST`
  - `PYRITONE_PORT`
  - `PYRITONE_TOKEN`
  - `PYRITONE_WS_URL`
- WebSocket URL parsing/normalization with `ws://` and `wss://` support.
- Default discovery path support:
  - `<minecraft>/config/pyritone_bridge/bridge-info.json`
  - repo/dev fallback candidates under `mod/run/...`

## 3. Async Client Runtime Capabilities

Primary client: `pyritone.Client` (async-only semantics).

### Public client methods

- Lifecycle and wiring:
  - `connect`
  - `close`
  - `bridge_info`
- Core bridge requests:
  - `ping`
  - `status_get`
  - `status_subscribe`
  - `status_unsubscribe`
  - `execute` (advanced raw command path)
  - `cancel`
- Event consumption and waiting:
  - `on`
  - `off`
  - `next_event`
  - `events`
  - `wait_for`
  - `wait_for_task`
- Typed invocation substrate:
  - `api_metadata_get`
  - `api_construct`
  - `api_invoke`
- Local schematic helpers:
  - `build_file`
  - `build_file_wait`

### Event callback model

- Event listeners by explicit event name and wildcard `*`.
- Callback deregistration via returned unsubscribe function from `on(...)`.
- Supports sync and async callbacks.
- Buffered-event matching for `wait_for(...)` on already received queue data.

### State cache and task cache surfaces

- `client.state` (`ClientStateCache`):
  - `updated_at`
  - `snapshot`
  - `active_task`
  - `task_id`
  - `task_state`
  - `task_detail`
- `client.task` convenience namespace:
  - `id`
  - `state`
  - `detail`
  - `data`
  - `wait`

### Settings namespace

- `client.settings.<setting>.set(value)`
- `client.settings.<setting>.get()`
- `client.settings.<setting>.toggle()`
- `client.settings.<setting>.reset()`

## 4. Typed Invocation Substrate Capabilities

- Remote object reference model (`RemoteRef(ref_id, java_type)`).
- Typed target addressing supports:
  - root target (for example `baritone`)
  - type target (for static invocation / enum lookup)
  - ref target (remote object instance)
- Typed argument/return coercion supports nested lists/dicts and reference payloads.
- Overload disambiguation via explicit `parameter_types`.
- Typed error channel:
  - `TypedCallError`
  - structured `details` payload from bridge error data.

## 5. Typed Baritone Namespace Capabilities

`client.baritone` now exposes typed wrappers and constructors over typed API transport.

### `BaritoneNamespace` public methods

- `metadata`
- `pathing_behavior`
- `custom_goal_process`
- `get_to_block_process`
- `mine_process`
- `explore_process`
- `builder_process`
- `follow_process`
- `world_provider`
- `selection_manager`
- `command_manager`
- `player_context`
- `input_override_handler`
- `game_event_handler`
- `provider`
- `command_system`
- `schematic_system`
- `world_scanner`
- `block_pos`
- `better_block_pos`
- `block_optional_meta`
- `block_optional_meta_lookup`
- `direction`
- `axis_direction`
- `waypoint_tag`
- `input_key`
- `java_path`
- `java_file`
- `waypoint`
- `fill_schematic`
- `composite_schematic`
- `sphere_mask`
- `cylinder_mask`
- `mask_schematic`
- `open_click`

### Goal constructors (`client.baritone.goals`)

- `axis`
- `block`
- `xz`
- `y_level`
- `near`
- `composite`
- `inverted`
- `run_away`

### Typed task handles

- `_dispatch` methods return `TypedTaskHandle`.
- Non-dispatch typed process methods wait for completion by default.
- `TypedTaskHandle.wait(timeout=None, poll_interval=0.1, startup_timeout=1.0)`.
- Completion payload: `TypedTaskResult` with fields:
  - `handle_id`
  - `action`
  - `started`
  - `pathing`
  - `calculating`
  - `has_path`
  - `goal`
  - derived property: `busy`

## 6. Typed Wrapper Inventory (Public Methods)

### Pathing and process wrappers

- `GoalRef`: `is_in_goal`, `heuristic`, `heuristic_current`
- `PathRef`: `length`, `goal`, `num_nodes_considered`
- `PathCalculationResultRef`: `result_type`, `path`
- `PathFinderRef`: `goal`, `calculate`, `is_finished`, `best_path_so_far`
- `PathExecutorRef`: `path`, `position`
- `PathingBehaviorRef`: `is_pathing`, `has_path`, `cancel_everything`, `force_cancel`, `goal`, `path`, `in_progress`, `current`, `next`
- `CustomGoalProcessRef`: `set_goal`, `path_dispatch`, `path`, `set_goal_and_path_dispatch`, `set_goal_and_path`, `goal`
- `GetToBlockProcessRef`: `get_to_block_dispatch`, `get_to_block`
- `MineProcessRef`: `mine_by_name_dispatch`, `mine_by_name`, `cancel`
- `ExploreProcessRef`: `explore_dispatch`, `explore`, `apply_json_filter`
- `BuilderProcessRef`: `build_open_schematic_dispatch`, `build_open_schematic`, `build_open_litematic_dispatch`, `build_open_litematic`, `pause`, `resume`, `is_paused`
- `FollowProcessRef`: `follow_dispatch`, `follow`, `pickup_dispatch`, `pickup`, `current_filter`, `cancel`

### Cache wrappers

- `WaypointRef`: `name`, `tag`, `creation_timestamp`, `location`
- `WaypointCollectionRef`: `add_waypoint`, `remove_waypoint`, `most_recent_by_tag`, `by_tag`, `all`
- `CachedWorldRef`: `region`, `queue_for_packing`, `is_cached`, `locations_of`, `reload_all_from_disk`, `save`
- `WorldDataRef`: `cached_world`, `waypoints`
- `WorldProviderRef`: `current_world`, `if_world_loaded`
- `WorldScannerRef`: `repack`, `scan_chunk_radius`

### Selection wrappers

- `SelectionRef`: `pos1`, `pos2`, `min`, `max`, `size`, `aabb`, `expand`, `contract`, `shift`
- `SelectionManagerRef`: `add_selection`, `add_selection_points`, `remove_selection`, `remove_all`, `selections`, `only_selection`, `last_selection`, `expand`, `contract`, `shift`

### Schematic wrappers

- `SchematicRef`: `width_x`, `height_y`, `length_z`, `reset`
- `StaticSchematicRef`: `direct`, `column`
- `FillSchematicRef`: `block_optional_meta`
- `CompositeSchematicRef`: `put`
- `MaskRef`: `part_of_mask`, `width_x`, `height_y`, `length_z`
- `StaticMaskRef`: `part_of_mask_static`, `compute`
- `SchematicFormatRef`: `file_extensions`, `is_file_type`, `parse`
- `SchematicSystemRef`: `registry`, `by_file`, `file_extensions`

### Command wrappers (typed API side)

- `RegistryRef`: `registered`, `register`, `unregister`, `values`, `descending_values`
- `CommandRef`: `execute`, `tab_complete`, `short_desc`, `long_desc`, `names`, `hidden_from_help`
- `ArgParserManagerRef`: `registry`, `parser_stateless`, `parse_stateless`
- `CommandSystemRef`: `parser_manager`
- `CommandManagerRef`: `baritone`, `registry`, `command`, `execute`, `tab_complete`

### Utils and event wrappers

- `PlayerContextRef`: `world_data`, `minecraft`, `player`, `player_controller`, `world`, `object_mouse_over`, `viewer_pos`, `player_feet`, `selected_block`, `is_looking_at`
- `InputOverrideHandlerRef`: `is_input_forced_down`, `set_input_force_state`, `clear_all_keys`
- `GameEventListenerRef`: `on_tick`, `on_post_tick`, `on_path_event`, `on_player_death`
- `EventBusRef`: `register_event_listener`
- `BaritoneProviderRef`: `primary_baritone`, `all_baritones`, `command_system`, `schematic_system`, `world_scanner`

## 7. Minecraft Constants Capabilities

Typed identifier support under `pyritone.minecraft`.

### Identifier model

- Base identifier type: `MinecraftIdentifier`.
- Typed variants:
  - `BlockId`
  - `ItemId`
  - `EntityId`
- Typed aliases/coercers:
  - `BlockLike`, `ItemLike`, `EntityLike`
  - `coerce_block_id`, `coerce_item_id`, `coerce_entity_id`

### Generated constant modules

- `pyritone.minecraft.blocks`:
  - exported names: 1109
  - block constants: 1107
- `pyritone.minecraft.items`:
  - exported names: 1420
  - item constants: 1418
- `pyritone.minecraft.entities`:
  - exported names: 155
  - entity constants: 153

Constants are directly usable in typed wrappers, for example with `mine_by_name(...)` and block-based process helpers.

## 8. Command Wrapper Capabilities

Generated async command wrapper layer is fully available and documented.

### Canonical command wrappers (`42`)

- `axis`, `blacklist`, `build`, `cancel`, `click`, `come`, `elytra`, `eta`, `explore`, `explorefilter`, `farm`, `find`, `follow`, `forcecancel`, `gc`, `goal`, `goto`, `help`, `home`, `invert`, `litematica`, `mine`, `modified`, `path`, `pause`, `paused`, `pickup`, `proc`, `reloadall`, `render`, `repack`, `reset`, `resume`, `saveall`, `sel`, `set`, `sethome`, `surface`, `thisway`, `tunnel`, `version`, `waypoints`

### Alias wrappers (`21`)

- `? -> help`
- `baritone -> modified`
- `c -> cancel`
- `forward -> thisway`
- `highway -> axis`
- `mod -> modified`
- `modifiedsettings -> modified`
- `p -> pause`
- `paws -> pause`
- `r -> resume`
- `rescan -> repack`
- `s -> sel`
- `selection -> sel`
- `setting -> set`
- `settings -> set`
- `stop -> cancel`
- `top -> surface`
- `unpause -> resume`
- `unpaws -> resume`
- `waypoint -> waypoints`
- `wp -> waypoints`

### Command domain coverage

- `navigation`: 13
- `world`: 6
- `build`: 3
- `control`: 8
- `info`: 9
- `waypoints`: 3

## 9. CLI and Demo Capabilities

### CLI surface (`python -m pyritone`)

- `ping`
- `status`
- `exec <baritone_command>`
- `cancel [--task-id]`
- `events` (continuous stream)

### Async demo coverage (`python/demos`)

- `01_connect_discovery.py`: discovery + connect + ping/status
- `02_basic_commands.py`: wrapper calls + raw execute path
- `03_goto_completion.py`: goto plus completion wait behavior
- `04_live_event_feed.py`: live event stream consumption
- `05_cancel_task.py`: cancel workflow and terminal events
- `06_settings_mode_switch.py`: settings API operations
- `07_mini_console.py`: manual interactive command flow
- `08_async_workflow.py`: concurrent async heartbeat + task waiting
- `09_build_file_local_path.py`: local schematic helper flow
- `10_cli_entrypoints.py`: CLI subprocess integration flow

## 10. Compatibility and Migration Behavior

- Primary API is async-only `Client`.
- Compatibility aliases retained for `v0.2.x`:
  - `PyritoneClient`
  - `AsyncPyritoneClient`
- Generated sync command shim modules retained in `python/src/pyritone/commands/sync_*.py` for migration cushioning.
- Raw `execute(...)` remains intentionally available as advanced escape hatch.
- Legacy socket bridge transport path removed.
- Cancel fallback command string (`"stop"`) removed; direct force cancel path required.

## 11. Validation and Safety Guardrails Included In Rework

- Python tests validate client transport, typed API, wrappers, docs generation, constants, and fallback debt guardrails.
- Java tests validate WS bridge auth/protocol and typed runtime components.
- Fallback debt guard tests enforce:
  - no legacy socket bridge reintroduction
  - no `"stop"` cancel fallback reintroduction
  - compatibility debt ceilings stay flat

