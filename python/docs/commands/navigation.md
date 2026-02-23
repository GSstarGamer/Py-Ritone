# Navigation Commands

Usage-first command guide for `Navigation` methods in `pyritone`.

### When to use this
- Movement, path goals, and travel flow control.
- Generated from Baritone `v1.15.0` command metadata.

### Commands in this page
- [`axis`](#axis)
- [`blacklist`](#blacklist)
- [`come`](#come)
- [`elytra`](#elytra)
- [`explore`](#explore)
- [`explorefilter`](#explorefilter)
- [`goal`](#goal)
- [`goto`](#goto)
- [`invert`](#invert)
- [`path`](#path)
- [`surface`](#surface)
- [`thisway`](#thisway)
- [`tunnel`](#tunnel)

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

## `axis`

Set a goal to the axes

### When to use this
- The axis command sets a goal that tells Baritone to head towards the nearest axis. That is, X=0 or Z=0.

### Method signature
- `Client.axis(*args: CommandArg) -> CommandDispatchResult`

### Baritone syntax
- `> axis`

### Domain and aliases
- Domain: `navigation`
- Aliases: highway

### Example
```python
import asyncio
from pyritone import Client

async def main() -> None:
    async with Client() as client:
        dispatch = await client.axis()
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
- Source file: `AxisCommand.java`

### Related methods
- [`blacklist`](#blacklist)
- [`come`](#come)
- [`elytra`](#elytra)
- [`explore`](#explore)
- [Alias mappings](aliases.md) for shortcut methods

## `blacklist`

Blacklist closest block

### When to use this
- While going to a block this command blacklists the closest block so that Baritone won't attempt to get to it.

### Method signature
- `Client.blacklist(*args: CommandArg) -> CommandDispatchResult`

### Baritone syntax
- `> blacklist`

### Domain and aliases
- Domain: `navigation`
- Aliases: none

### Example
```python
import asyncio
from pyritone import Client

async def main() -> None:
    async with Client() as client:
        dispatch = await client.blacklist()
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
- Source file: `BlacklistCommand.java`

### Related methods
- [`axis`](#axis)
- [`come`](#come)
- [`elytra`](#elytra)
- [`explore`](#explore)
- [Alias mappings](aliases.md) for shortcut methods

## `come`

Start heading towards your camera

### When to use this
- The come command tells Baritone to head towards your camera.

### Method signature
- `Client.come(*args: CommandArg) -> CommandDispatchResult`

### Baritone syntax
- `> come`

### Domain and aliases
- Domain: `navigation`
- Aliases: none

### Example
```python
import asyncio
from pyritone import Client

async def main() -> None:
    async with Client() as client:
        dispatch = await client.come()
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
- Source file: `ComeCommand.java`

### Related methods
- [`axis`](#axis)
- [`blacklist`](#blacklist)
- [`elytra`](#elytra)
- [`explore`](#explore)
- [Alias mappings](aliases.md) for shortcut methods

## `elytra`

elytra time

### When to use this
- The elytra command tells baritone to, in the nether, automatically fly to the current goal.

### Method signature
- `Client.elytra(*args: CommandArg) -> CommandDispatchResult`

### Baritone syntax
- `> elytra - fly to the current goal`
- `> elytra reset - Resets the state of the process, but will try to keep flying to the same goal.`
- `> elytra repack - Queues all of the chunks in render distance to be given to the native library.`
- `> elytra supported - Tells you if baritone ships a native library that is compatible with your PC.`

### Domain and aliases
- Domain: `navigation`
- Aliases: none

### Example
```python
import asyncio
from pyritone import Client

async def main() -> None:
    async with Client() as client:
        dispatch = await client.elytra()
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
- Source file: `ElytraCommand.java`

### Related methods
- [`axis`](#axis)
- [`blacklist`](#blacklist)
- [`come`](#come)
- [`explore`](#explore)
- [Alias mappings](aliases.md) for shortcut methods

## `explore`

Explore things

### When to use this
- Tell Baritone to explore randomly. If you used explorefilter before this, it will be applied.

### Method signature
- `Client.explore(*args: CommandArg) -> CommandDispatchResult`

### Baritone syntax
- `> explore - Explore from your current position.`
- `> explore <x> <z> - Explore from the specified X and Z position.`

### Domain and aliases
- Domain: `navigation`
- Aliases: none

### Example
```python
import asyncio
from pyritone import Client

async def main() -> None:
    async with Client() as client:
        dispatch = await client.explore()
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
- Source file: `ExploreCommand.java`

### Related methods
- [`axis`](#axis)
- [`blacklist`](#blacklist)
- [`come`](#come)
- [`elytra`](#elytra)
- [Alias mappings](aliases.md) for shortcut methods

## `explorefilter`

Explore chunks from a json

### When to use this
- Apply an explore filter before using explore, which tells the explore process which chunks have been explored/not explored.

### Method signature
- `Client.explorefilter(*args: CommandArg) -> CommandDispatchResult`

### Baritone syntax
- `> explorefilter <path> [invert] - Load the JSON file referenced by the specified path. If invert is specified, it must be the literal word 'invert'.`

### Domain and aliases
- Domain: `navigation`
- Aliases: none

### Example
```python
import asyncio
from pyritone import Client

async def main() -> None:
    async with Client() as client:
        dispatch = await client.explorefilter("explore-filter.json")
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
- Use a valid JSON file path for the filter input.

### Source provenance
- Baritone version: `v1.15.0`
- Source file: `ExploreFilterCommand.java`

### Related methods
- [`axis`](#axis)
- [`blacklist`](#blacklist)
- [`come`](#come)
- [`elytra`](#elytra)
- [Alias mappings](aliases.md) for shortcut methods

## `goal`

Set or clear the goal

### When to use this
- The goal command allows you to set or clear Baritone's goal.

### Method signature
- `Client.goal(*args: CommandArg) -> CommandDispatchResult`

### Baritone syntax
- `> goal - Set the goal to your current position`
- `> goal <reset/clear/none> - Erase the goal`
- `> goal <y> - Set the goal to a Y level`
- `> goal <x> <z> - Set the goal to an X,Z position`
- `> goal <x> <y> <z> - Set the goal to an X,Y,Z position`

### Domain and aliases
- Domain: `navigation`
- Aliases: none

### Example
```python
import asyncio
from pyritone import Client

async def main() -> None:
    async with Client() as client:
        dispatch = await client.goal(100, 70, 100)
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
- Source file: `GoalCommand.java`

### Related methods
- [`axis`](#axis)
- [`blacklist`](#blacklist)
- [`come`](#come)
- [`elytra`](#elytra)
- [Alias mappings](aliases.md) for shortcut methods

## `goto`

Go to a coordinate or block

### When to use this
- The goto command tells Baritone to head towards a given goal or block.

### Method signature
- `Client.goto(x: int, y: int, z: int, *extra_args: CommandArg) -> CommandDispatchResult`

### Baritone syntax
- `> goto <block> - Go to a block, wherever it is in the world`
- `> goto <y> - Go to a Y level`
- `> goto <x> <z> - Go to an X,Z position`
- `> goto <x> <y> <z> - Go to an X,Y,Z position`

### Domain and aliases
- Domain: `navigation`
- Aliases: none

### Example
```python
import asyncio
from pyritone import Client

async def main() -> None:
    async with Client() as client:
        dispatch = await client.goto(100, 70, 100)
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
- Use `wait_for_task` (or `goto_wait`) if you need terminal completion state.

### Source provenance
- Baritone version: `v1.15.0`
- Source file: `GotoCommand.java`

### Related methods
- [`axis`](#axis)
- [`blacklist`](#blacklist)
- [`come`](#come)
- [`elytra`](#elytra)
- [Alias mappings](aliases.md) for shortcut methods

## `invert`

Run away from the current goal

### When to use this
- The invert command tells Baritone to head away from the current goal rather than towards it.

### Method signature
- `Client.invert(*args: CommandArg) -> CommandDispatchResult`

### Baritone syntax
- `> invert - Invert the current goal.`

### Domain and aliases
- Domain: `navigation`
- Aliases: none

### Example
```python
import asyncio
from pyritone import Client

async def main() -> None:
    async with Client() as client:
        dispatch = await client.invert()
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
- Source file: `InvertCommand.java`

### Related methods
- [`axis`](#axis)
- [`blacklist`](#blacklist)
- [`come`](#come)
- [`elytra`](#elytra)
- [Alias mappings](aliases.md) for shortcut methods

## `path`

Start heading towards the goal

### When to use this
- The path command tells Baritone to head towards the current goal.

### Method signature
- `Client.path(*args: CommandArg) -> CommandDispatchResult`

### Baritone syntax
- `> path - Start the pathing.`

### Domain and aliases
- Domain: `navigation`
- Aliases: none

### Example
```python
import asyncio
from pyritone import Client

async def main() -> None:
    async with Client() as client:
        dispatch = await client.path()
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
- Source file: `PathCommand.java`

### Related methods
- [`axis`](#axis)
- [`blacklist`](#blacklist)
- [`come`](#come)
- [`elytra`](#elytra)
- [Alias mappings](aliases.md) for shortcut methods

## `surface`

Used to get out of caves, mines, ...

### When to use this
- The surface/top command tells Baritone to head towards the closest surface-like area.

### Method signature
- `Client.surface(*args: CommandArg) -> CommandDispatchResult`

### Baritone syntax
- `> surface - Used to get out of caves, mines, ...`
- `> top - Used to get out of caves, mines, ...`

### Domain and aliases
- Domain: `navigation`
- Aliases: top

### Example
```python
import asyncio
from pyritone import Client

async def main() -> None:
    async with Client() as client:
        dispatch = await client.surface()
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
- Source file: `SurfaceCommand.java`

### Related methods
- [`axis`](#axis)
- [`blacklist`](#blacklist)
- [`come`](#come)
- [`elytra`](#elytra)
- [Alias mappings](aliases.md) for shortcut methods

## `thisway`

Travel in your current direction

### When to use this
- Creates a GoalXZ some amount of blocks in the direction you're currently looking

### Method signature
- `Client.thisway(*args: CommandArg) -> CommandDispatchResult`

### Baritone syntax
- `> thisway <distance> - makes a GoalXZ distance blocks in front of you`

### Domain and aliases
- Domain: `navigation`
- Aliases: forward

### Example
```python
import asyncio
from pyritone import Client

async def main() -> None:
    async with Client() as client:
        dispatch = await client.thisway(200)
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
- Source file: `ThisWayCommand.java`

### Related methods
- [`axis`](#axis)
- [`blacklist`](#blacklist)
- [`come`](#come)
- [`elytra`](#elytra)
- [Alias mappings](aliases.md) for shortcut methods

## `tunnel`

Set a goal to tunnel in your current direction

### When to use this
- The tunnel command sets a goal that tells Baritone to mine completely straight in the direction that you're facing.

### Method signature
- `Client.tunnel(*args: CommandArg) -> CommandDispatchResult`

### Baritone syntax
- `> tunnel - No arguments, mines in a 1x2 radius.`
- `> tunnel <height> <width> <depth> - Tunnels in a user defined height, width and depth.`

### Domain and aliases
- Domain: `navigation`
- Aliases: none

### Example
```python
import asyncio
from pyritone import Client

async def main() -> None:
    async with Client() as client:
        dispatch = await client.tunnel(2, 1, 64)
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
- Source file: `TunnelCommand.java`

### Related methods
- [`axis`](#axis)
- [`blacklist`](#blacklist)
- [`come`](#come)
- [`elytra`](#elytra)
- [Alias mappings](aliases.md) for shortcut methods
