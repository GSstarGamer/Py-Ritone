# Control Commands

Usage-first command guide for `Control` methods in `pyritone`.

### When to use this
- Execution-state and settings-related commands.
- Generated from Baritone `v1.15.0` command metadata.

### Commands in this page
- [`cancel`](#cancel)
- [`forcecancel`](#forcecancel)
- [`modified`](#modified)
- [`pause`](#pause)
- [`paused`](#paused)
- [`reset`](#reset)
- [`resume`](#resume)
- [`set`](#set)

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

## `cancel`

Cancel what Baritone is currently doing

### When to use this
- The cancel command tells Baritone to stop whatever it's currently doing.

### Method signature
- `Client.cancel(task_id: str | None = None) -> dict[str, Any]`

### Baritone syntax
- `> cancel`

### Domain and aliases
- Domain: `control`
- Aliases: c, stop

### Example
```python
import asyncio
from pyritone import Client

async def main() -> None:
    async with Client() as client:
        result = await client.cancel()
        print(result)

asyncio.run(main())
```

### Return shape
```text
dict[str, Any]
- Raw bridge payload from `task.cancel`.
- May include cancellation result for active or requested task.
```

### Common mistakes
- Passing separate string tokens when one argument contains spaces. Use one Python string.
- Expecting `cancel()` to return `CommandDispatchResult`; it returns raw cancel payload.
- This method uses the bridge `task.cancel` endpoint, not `baritone.execute "cancel"`.
- Pass `task_id` if you want to cancel a specific known task.

### Source provenance
- Baritone version: `v1.15.0`
- Source file: `ExecutionControlCommands.java`

### Related methods
- [`forcecancel`](#forcecancel)
- [`modified`](#modified)
- [`pause`](#pause)
- [`paused`](#paused)
- [Alias mappings](aliases.md) for shortcut methods

## `forcecancel`

Force cancel

### When to use this
- Like cancel, but more forceful.

### Method signature
- `Client.forcecancel(*args: CommandArg) -> CommandDispatchResult`

### Baritone syntax
- `> forcecancel`

### Domain and aliases
- Domain: `control`
- Aliases: none

### Example
```python
import asyncio
from pyritone import Client

async def main() -> None:
    async with Client() as client:
        dispatch = await client.forcecancel()
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

### Common mistakes
- Passing separate string tokens when one argument contains spaces. Use one Python string.
- Treating dispatch as completion. Dispatch is immediate; wait on `task_id` when needed.

### Source provenance
- Baritone version: `v1.15.0`
- Source file: `ForceCancelCommand.java`

### Related methods
- [`cancel`](#cancel)
- [`modified`](#modified)
- [`pause`](#pause)
- [`paused`](#paused)
- [Alias mappings](aliases.md) for shortcut methods

## `modified`

List modified settings

### When to use this
- This command is an alias for: set modified

### Method signature
- `Client.modified(*args: CommandArg) -> CommandDispatchResult`

### Baritone syntax
- `> set modified`

### Domain and aliases
- Domain: `control`
- Aliases: mod, baritone, modifiedsettings

### Example
```python
import asyncio
from pyritone import Client

async def main() -> None:
    async with Client() as client:
        dispatch = await client.modified()
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

### Common mistakes
- Passing separate string tokens when one argument contains spaces. Use one Python string.
- Treating dispatch as completion. Dispatch is immediate; wait on `task_id` when needed.
- `modified()` routes to `set modified` internally.

### Source provenance
- Baritone version: `v1.15.0`
- Source file: `DefaultCommands.java (CommandAlias)`

### Related methods
- [`cancel`](#cancel)
- [`forcecancel`](#forcecancel)
- [`pause`](#pause)
- [`paused`](#paused)
- [Alias mappings](aliases.md) for shortcut methods

## `pause`

Pauses Baritone until you use resume

### When to use this
- The pause command tells Baritone to temporarily stop whatever it's doing.

### Method signature
- `Client.pause(*args: CommandArg) -> CommandDispatchResult`

### Baritone syntax
- `> pause`

### Domain and aliases
- Domain: `control`
- Aliases: p, paws

### Example
```python
import asyncio
from pyritone import Client

async def main() -> None:
    async with Client() as client:
        dispatch = await client.pause()
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

### Common mistakes
- Passing separate string tokens when one argument contains spaces. Use one Python string.
- Treating dispatch as completion. Dispatch is immediate; wait on `task_id` when needed.

### Source provenance
- Baritone version: `v1.15.0`
- Source file: `ExecutionControlCommands.java`

### Related methods
- [`cancel`](#cancel)
- [`forcecancel`](#forcecancel)
- [`modified`](#modified)
- [`paused`](#paused)
- [Alias mappings](aliases.md) for shortcut methods

## `paused`

Tells you if Baritone is paused

### When to use this
- The paused command tells you if Baritone is currently paused by use of the pause command.

### Method signature
- `Client.paused(*args: CommandArg) -> CommandDispatchResult`

### Baritone syntax
- `> paused`

### Domain and aliases
- Domain: `control`
- Aliases: none

### Example
```python
import asyncio
from pyritone import Client

async def main() -> None:
    async with Client() as client:
        dispatch = await client.paused()
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

### Common mistakes
- Passing separate string tokens when one argument contains spaces. Use one Python string.
- Treating dispatch as completion. Dispatch is immediate; wait on `task_id` when needed.

### Source provenance
- Baritone version: `v1.15.0`
- Source file: `ExecutionControlCommands.java`

### Related methods
- [`cancel`](#cancel)
- [`forcecancel`](#forcecancel)
- [`modified`](#modified)
- [`pause`](#pause)
- [Alias mappings](aliases.md) for shortcut methods

## `reset`

Reset all settings or just one

### When to use this
- This command is an alias for: set reset

### Method signature
- `Client.reset(*args: CommandArg) -> CommandDispatchResult`

### Baritone syntax
- `> set reset`

### Domain and aliases
- Domain: `control`
- Aliases: none

### Example
```python
import asyncio
from pyritone import Client

async def main() -> None:
    async with Client() as client:
        dispatch = await client.reset("allowPlace")
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

### Common mistakes
- Passing separate string tokens when one argument contains spaces. Use one Python string.
- Treating dispatch as completion. Dispatch is immediate; wait on `task_id` when needed.
- `reset()` routes to `set reset ...` internally.

### Source provenance
- Baritone version: `v1.15.0`
- Source file: `DefaultCommands.java (CommandAlias)`

### Related methods
- [`cancel`](#cancel)
- [`forcecancel`](#forcecancel)
- [`modified`](#modified)
- [`pause`](#pause)
- [Alias mappings](aliases.md) for shortcut methods

## `resume`

Resumes Baritone after a pause

### When to use this
- The resume command tells Baritone to resume whatever it was doing when you last used pause.

### Method signature
- `Client.resume(*args: CommandArg) -> CommandDispatchResult`

### Baritone syntax
- `> resume`

### Domain and aliases
- Domain: `control`
- Aliases: r, unpause, unpaws

### Example
```python
import asyncio
from pyritone import Client

async def main() -> None:
    async with Client() as client:
        dispatch = await client.resume()
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

### Common mistakes
- Passing separate string tokens when one argument contains spaces. Use one Python string.
- Treating dispatch as completion. Dispatch is immediate; wait on `task_id` when needed.

### Source provenance
- Baritone version: `v1.15.0`
- Source file: `ExecutionControlCommands.java`

### Related methods
- [`cancel`](#cancel)
- [`forcecancel`](#forcecancel)
- [`modified`](#modified)
- [`pause`](#pause)
- [Alias mappings](aliases.md) for shortcut methods

## `set`

View or change settings

### When to use this
- Using the set command, you can manage all of Baritone's settings. Almost every aspect is controlled by these settings - go wild!

### Method signature
- `Client.set(*args: CommandArg) -> CommandDispatchResult`

### Baritone syntax
- `> set - Same as `set list``
- `> set list [page] - View all settings`
- `> set modified [page] - View modified settings`
- `> set <setting> - View the current value of a setting`
- `> set <setting> <value> - Set the value of a setting`
- `> set reset all - Reset ALL SETTINGS to their defaults`
- `> set reset <setting> - Reset a setting to its default`
- `> set toggle <setting> - Toggle a boolean setting`
- `> set save - Save all settings (this is automatic tho)`
- `> set load - Load settings from settings.txt`
- `> set load [filename] - Load settings from another file in your minecraft/baritone`

### Domain and aliases
- Domain: `control`
- Aliases: setting, settings

### Example
```python
import asyncio
from pyritone import Client

async def main() -> None:
    async with Client() as client:
        dispatch = await client.set("allowPlace", True)
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

### Common mistakes
- Passing separate string tokens when one argument contains spaces. Use one Python string.
- Treating dispatch as completion. Dispatch is immediate; wait on `task_id` when needed.
- For setting ergonomics, prefer `client.settings.<name>` when possible.
- Boolean values serialize as lowercase `true`/`false` in command text.

### Source provenance
- Baritone version: `v1.15.0`
- Source file: `SetCommand.java`

### Related methods
- [`cancel`](#cancel)
- [`forcecancel`](#forcecancel)
- [`modified`](#modified)
- [`pause`](#pause)
- [Alias mappings](aliases.md) for shortcut methods
