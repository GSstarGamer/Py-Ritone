# World Commands

Usage-first command guide for `World` methods in `pyritone`.

### When to use this
- Block/entity interaction commands such as mine, follow, and pickup.
- Generated from Baritone `v1.15.0` command metadata.

### Commands in this page
- [`click`](#click)
- [`farm`](#farm)
- [`find`](#find)
- [`follow`](#follow)
- [`mine`](#mine)
- [`pickup`](#pickup)

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

## `click`

Open click

### When to use this
- Opens click dude

### Method signature
- `Client.click(*args: CommandArg) -> CommandDispatchResult`

### Baritone syntax
- `> click`

### Domain and aliases
- Domain: `world`
- Aliases: none

### Example
```python
import asyncio
from pyritone import Client

async def main() -> None:
    async with Client() as client:
        dispatch = await client.click()
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
- Source file: `ClickCommand.java`

### Related methods
- [`farm`](#farm)
- [`find`](#find)
- [`follow`](#follow)
- [`mine`](#mine)
- [Alias mappings](aliases.md) for shortcut methods

## `farm`

Farm nearby crops

### When to use this
- The farm command starts farming nearby plants. It harvests mature crops and plants new ones.

### Method signature
- `Client.farm(*args: CommandArg) -> CommandDispatchResult`

### Baritone syntax
- `> farm - farms every crop it can find.`
- `> farm <range> - farm crops within range from the starting position.`
- `> farm <range> <waypoint> - farm crops within range from waypoint.`

### Domain and aliases
- Domain: `world`
- Aliases: none

### Example
```python
import asyncio
from pyritone import Client

async def main() -> None:
    async with Client() as client:
        dispatch = await client.farm(64)
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
- Source file: `FarmCommand.java`

### Related methods
- [`click`](#click)
- [`find`](#find)
- [`follow`](#follow)
- [`mine`](#mine)
- [Alias mappings](aliases.md) for shortcut methods

## `find`

Find positions of a certain block

### When to use this
- The find command searches through Baritone's cache and attempts to find the location of the block.

### Method signature
- `Client.find(*args: CommandArg) -> CommandDispatchResult`

### Baritone syntax
- `> find <block> [...] - Try finding the listed blocks`

### Domain and aliases
- Domain: `world`
- Aliases: none

### Example
```python
import asyncio
from pyritone import Client

async def main() -> None:
    async with Client() as client:
        dispatch = await client.find("diamond_ore")
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
- Source file: `FindCommand.java`

### Related methods
- [`click`](#click)
- [`farm`](#farm)
- [`follow`](#follow)
- [`mine`](#mine)
- [Alias mappings](aliases.md) for shortcut methods

## `follow`

Follow entity things

### When to use this
- The follow command tells Baritone to follow certain kinds of entities.

### Method signature
- `Client.follow(*args: CommandArg) -> CommandDispatchResult`

### Baritone syntax
- `> follow entities - Follows all entities.`
- `> follow entity <entity1> <entity2> <...> - Follow certain entities (for example 'skeleton', 'horse' etc.)`
- `> follow players - Follow players`
- `> follow player <username1> <username2> <...> - Follow certain players`

### Domain and aliases
- Domain: `world`
- Aliases: none

### Example
```python
import asyncio
from pyritone import Client

async def main() -> None:
    async with Client() as client:
        dispatch = await client.follow("players")
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
- Source file: `FollowCommand.java`

### Related methods
- [`click`](#click)
- [`farm`](#farm)
- [`find`](#find)
- [`mine`](#mine)
- [Alias mappings](aliases.md) for shortcut methods

## `mine`

Mine some blocks

### When to use this
- The mine command allows you to tell Baritone to search for and mine individual blocks.

### Method signature
- `Client.mine(*args: CommandArg) -> CommandDispatchResult`

### Baritone syntax
- `> mine diamond_ore - Mines all diamonds it can find.`

### Domain and aliases
- Domain: `world`
- Aliases: none

### Example
```python
import asyncio
from pyritone import Client

async def main() -> None:
    async with Client() as client:
        dispatch = await client.mine("diamond_ore")
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
- Source file: `MineCommand.java`

### Related methods
- [`click`](#click)
- [`farm`](#farm)
- [`find`](#find)
- [`follow`](#follow)
- [Alias mappings](aliases.md) for shortcut methods

## `pickup`

Pickup items

### When to use this
- Pickup items

### Method signature
- `Client.pickup(*args: CommandArg) -> CommandDispatchResult`

### Baritone syntax
- `> pickup - Pickup anything`
- `> pickup <item1> <item2> <...> - Pickup certain items`

### Domain and aliases
- Domain: `world`
- Aliases: none

### Example
```python
import asyncio
from pyritone import Client

async def main() -> None:
    async with Client() as client:
        dispatch = await client.pickup("diamond")
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
- Source file: `PickupCommand.java`

### Related methods
- [`click`](#click)
- [`farm`](#farm)
- [`find`](#find)
- [`follow`](#follow)
- [Alias mappings](aliases.md) for shortcut methods
