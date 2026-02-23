# Waypoints Commands

Usage-first command guide for `Waypoints` methods in `pyritone`.

### When to use this
- Waypoint save/list/goto helpers and aliases.
- Generated from Baritone `v1.15.0` command metadata.

### Commands in this page
- [`home`](#home)
- [`sethome`](#sethome)
- [`waypoints`](#waypoints)

### Return shape
```text
CommandDispatchResult
- command_text
- raw
- task_id (optional)
- accepted (optional)
```

### Common mistakes
- Assuming command dispatch means task completion. Use `wait_for_task` when `task_id` exists.
- Forgetting to connect the client before calling methods.

### Related methods
- [Tasks, events, and waiting](../tasks-events-and-waiting.md)
- [Errors and troubleshooting](../errors-and-troubleshooting.md)
- [Alias methods](aliases.md)

## `home`

Path to your home waypoint

### When to use this
- This command is an alias for: waypoints goto home

### Method signature
- `Client.home(*args: CommandArg) -> CommandDispatchResult`

### Baritone syntax
- `> waypoints goto home`

### Domain and aliases
- Domain: `waypoints`
- Aliases: none

### Example
```python
import asyncio
from pyritone import Client

async def main() -> None:
    async with Client() as client:
        dispatch = await client.home()
        print(dispatch)

asyncio.run(main())
```

### Return shape
```text
CommandDispatchResult
- command_text: exact command string sent through `baritone.execute`.
- raw: raw bridge response object.
- task_id (optional): task identifier if the bridge returns one.
- accepted (optional): acceptance flag if provided by the bridge.
```

### Wait pattern
If `task_id` exists, wait for a terminal event:

- `terminal = await client.wait_for_task(dispatch["task_id"])`

### Common mistakes
- Passing separate string tokens when one argument contains spaces. Use one Python string.
- Treating dispatch as completion. Dispatch is immediate; wait on `task_id` when needed.
- `home()` is an alias wrapper for `waypoints goto home`.

### Source provenance
- Baritone version: `v1.15.0`
- Source file: `DefaultCommands.java (CommandAlias)`

### Related methods
- [`sethome`](#sethome)
- [`waypoints`](#waypoints)
- [Alias mappings](aliases.md) for shortcut methods

## `sethome`

Sets your home waypoint

### When to use this
- This command is an alias for: waypoints save home

### Method signature
- `Client.sethome(*args: CommandArg) -> CommandDispatchResult`

### Baritone syntax
- `> waypoints save home`

### Domain and aliases
- Domain: `waypoints`
- Aliases: none

### Example
```python
import asyncio
from pyritone import Client

async def main() -> None:
    async with Client() as client:
        dispatch = await client.sethome()
        print(dispatch)

asyncio.run(main())
```

### Return shape
```text
CommandDispatchResult
- command_text: exact command string sent through `baritone.execute`.
- raw: raw bridge response object.
- task_id (optional): task identifier if the bridge returns one.
- accepted (optional): acceptance flag if provided by the bridge.
```

### Wait pattern
If `task_id` exists, wait for a terminal event:

- `terminal = await client.wait_for_task(dispatch["task_id"])`

### Common mistakes
- Passing separate string tokens when one argument contains spaces. Use one Python string.
- Treating dispatch as completion. Dispatch is immediate; wait on `task_id` when needed.
- `sethome()` is an alias wrapper for `waypoints save home`.

### Source provenance
- Baritone version: `v1.15.0`
- Source file: `DefaultCommands.java (CommandAlias)`

### Related methods
- [`home`](#home)
- [`waypoints`](#waypoints)
- [Alias mappings](aliases.md) for shortcut methods

## `waypoints`

Manage waypoints

### When to use this
- The waypoint command allows you to manage Baritone's waypoints.

### Method signature
- `Client.waypoints(*args: CommandArg) -> CommandDispatchResult`

### Baritone syntax
- `> wp [l/list] - List all waypoints.`
- `> wp <l/list> <tag> - List all waypoints by tag.`
- `> wp <s/save> - Save an unnamed USER waypoint at your current position`
- `> wp <s/save> [tag] [name] [pos] - Save a waypoint with the specified tag, name and position.`
- `> wp <i/info/show> <tag/name> - Show info on a waypoint by tag or name.`
- `> wp <d/delete> <tag/name> - Delete a waypoint by tag or name.`
- `> wp <restore> <n> - Restore the last n deleted waypoints.`
- `> wp <c/clear> <tag> - Delete all waypoints with the specified tag.`
- `> wp <g/goal> <tag/name> - Set a goal to a waypoint by tag or name.`
- `> wp <goto> <tag/name> - Set a goal to a waypoint by tag or name and start pathing.`

### Domain and aliases
- Domain: `waypoints`
- Aliases: waypoint, wp

### Example
```python
import asyncio
from pyritone import Client

async def main() -> None:
    async with Client() as client:
        dispatch = await client.waypoints("list")
        print(dispatch)

asyncio.run(main())
```

### Return shape
```text
CommandDispatchResult
- command_text: exact command string sent through `baritone.execute`.
- raw: raw bridge response object.
- task_id (optional): task identifier if the bridge returns one.
- accepted (optional): acceptance flag if provided by the bridge.
```

### Wait pattern
If `task_id` exists, wait for a terminal event:

- `terminal = await client.wait_for_task(dispatch["task_id"])`

### Common mistakes
- Passing separate string tokens when one argument contains spaces. Use one Python string.
- Treating dispatch as completion. Dispatch is immediate; wait on `task_id` when needed.

### Source provenance
- Baritone version: `v1.15.0`
- Source file: `WaypointsCommand.java`

### Related methods
- [`home`](#home)
- [`sethome`](#sethome)
- [Alias mappings](aliases.md) for shortcut methods
