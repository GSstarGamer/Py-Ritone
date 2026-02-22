# Info Commands

Usage-first command guide for `Info` methods in `pyritone`.

### When to use this
- Read-only status and cache/diagnostic commands.
- Generated from Baritone `v1.15.0` command metadata.

### Commands in this page
- [`eta`](#eta)
- [`gc`](#gc)
- [`help`](#help)
- [`proc`](#proc)
- [`reloadall`](#reloadall)
- [`render`](#render)
- [`repack`](#repack)
- [`saveall`](#saveall)
- [`version`](#version)

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

## `eta`

View the current ETA

### When to use this
- The ETA command provides information about the estimated time until the next segment.

### Method signatures
- Sync: `PyritoneClient.eta(*args: CommandArg) -> CommandDispatchResult`
- Async: `AsyncPyritoneClient.eta(*args: CommandArg) -> CommandDispatchResult`

### Baritone syntax
- `> eta - View ETA, if present`

### Domain and aliases
- Domain: `info`
- Aliases: none

### Sync example
```python
from pyritone import PyritoneClient

with PyritoneClient() as client:
    dispatch = client.eta()
    print(dispatch)
```

### Async example
```python
import asyncio
from pyritone import AsyncPyritoneClient

async def main() -> None:
    client = AsyncPyritoneClient()
    await client.connect()
    try:
        dispatch = await client.eta()
        print(dispatch)
    finally:
        await client.close()

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
- Source file: `ETACommand.java`

### Related methods
- [`gc`](#gc)
- [`help`](#help)
- [`proc`](#proc)
- [`reloadall`](#reloadall)
- [Alias mappings](aliases.md) for shortcut methods

## `gc`

Call System.gc()

### When to use this
- Calls System.gc().

### Method signatures
- Sync: `PyritoneClient.gc(*args: CommandArg) -> CommandDispatchResult`
- Async: `AsyncPyritoneClient.gc(*args: CommandArg) -> CommandDispatchResult`

### Baritone syntax
- `> gc`

### Domain and aliases
- Domain: `info`
- Aliases: none

### Sync example
```python
from pyritone import PyritoneClient

with PyritoneClient() as client:
    dispatch = client.gc()
    print(dispatch)
```

### Async example
```python
import asyncio
from pyritone import AsyncPyritoneClient

async def main() -> None:
    client = AsyncPyritoneClient()
    await client.connect()
    try:
        dispatch = await client.gc()
        print(dispatch)
    finally:
        await client.close()

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
- Source file: `GcCommand.java`

### Related methods
- [`eta`](#eta)
- [`help`](#help)
- [`proc`](#proc)
- [`reloadall`](#reloadall)
- [Alias mappings](aliases.md) for shortcut methods

## `help`

View all commands or help on specific ones

### When to use this
- Using this command, you can view detailed help information on how to use certain commands of Baritone.

### Method signatures
- Sync: `PyritoneClient.help(*args: CommandArg) -> CommandDispatchResult`
- Async: `AsyncPyritoneClient.help(*args: CommandArg) -> CommandDispatchResult`

### Baritone syntax
- `> help - Lists all commands and their short descriptions.`
- `> help <command> - Displays help information on a specific command.`

### Domain and aliases
- Domain: `info`
- Aliases: ?

### Sync example
```python
from pyritone import PyritoneClient

with PyritoneClient() as client:
    dispatch = client.help("goto")
    print(dispatch)
```

### Async example
```python
import asyncio
from pyritone import AsyncPyritoneClient

async def main() -> None:
    client = AsyncPyritoneClient()
    await client.connect()
    try:
        dispatch = await client.help("goto")
        print(dispatch)
    finally:
        await client.close()

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
- Source file: `HelpCommand.java`

### Related methods
- [`eta`](#eta)
- [`gc`](#gc)
- [`proc`](#proc)
- [`reloadall`](#reloadall)
- [Alias mappings](aliases.md) for shortcut methods

## `proc`

View process state information

### When to use this
- The proc command provides miscellaneous information about the process currently controlling Baritone.

### Method signatures
- Sync: `PyritoneClient.proc(*args: CommandArg) -> CommandDispatchResult`
- Async: `AsyncPyritoneClient.proc(*args: CommandArg) -> CommandDispatchResult`

### Baritone syntax
- `> proc - View process information, if present`

### Domain and aliases
- Domain: `info`
- Aliases: none

### Sync example
```python
from pyritone import PyritoneClient

with PyritoneClient() as client:
    dispatch = client.proc()
    print(dispatch)
```

### Async example
```python
import asyncio
from pyritone import AsyncPyritoneClient

async def main() -> None:
    client = AsyncPyritoneClient()
    await client.connect()
    try:
        dispatch = await client.proc()
        print(dispatch)
    finally:
        await client.close()

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
- Source file: `ProcCommand.java`

### Related methods
- [`eta`](#eta)
- [`gc`](#gc)
- [`help`](#help)
- [`reloadall`](#reloadall)
- [Alias mappings](aliases.md) for shortcut methods

## `reloadall`

Reloads Baritone's cache for this world

### When to use this
- The reloadall command reloads Baritone's world cache.

### Method signatures
- Sync: `PyritoneClient.reloadall(*args: CommandArg) -> CommandDispatchResult`
- Async: `AsyncPyritoneClient.reloadall(*args: CommandArg) -> CommandDispatchResult`

### Baritone syntax
- `> reloadall`

### Domain and aliases
- Domain: `info`
- Aliases: none

### Sync example
```python
from pyritone import PyritoneClient

with PyritoneClient() as client:
    dispatch = client.reloadall()
    print(dispatch)
```

### Async example
```python
import asyncio
from pyritone import AsyncPyritoneClient

async def main() -> None:
    client = AsyncPyritoneClient()
    await client.connect()
    try:
        dispatch = await client.reloadall()
        print(dispatch)
    finally:
        await client.close()

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
- Source file: `ReloadAllCommand.java`

### Related methods
- [`eta`](#eta)
- [`gc`](#gc)
- [`help`](#help)
- [`proc`](#proc)
- [Alias mappings](aliases.md) for shortcut methods

## `render`

Fix glitched chunks

### When to use this
- The render command fixes glitched chunk rendering without having to reload all of them.

### Method signatures
- Sync: `PyritoneClient.render(*args: CommandArg) -> CommandDispatchResult`
- Async: `AsyncPyritoneClient.render(*args: CommandArg) -> CommandDispatchResult`

### Baritone syntax
- `> render`

### Domain and aliases
- Domain: `info`
- Aliases: none

### Sync example
```python
from pyritone import PyritoneClient

with PyritoneClient() as client:
    dispatch = client.render()
    print(dispatch)
```

### Async example
```python
import asyncio
from pyritone import AsyncPyritoneClient

async def main() -> None:
    client = AsyncPyritoneClient()
    await client.connect()
    try:
        dispatch = await client.render()
        print(dispatch)
    finally:
        await client.close()

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
- Source file: `RenderCommand.java`

### Related methods
- [`eta`](#eta)
- [`gc`](#gc)
- [`help`](#help)
- [`proc`](#proc)
- [Alias mappings](aliases.md) for shortcut methods

## `repack`

Re-cache chunks

### When to use this
- Repack chunks around you. This basically re-caches them.

### Method signatures
- Sync: `PyritoneClient.repack(*args: CommandArg) -> CommandDispatchResult`
- Async: `AsyncPyritoneClient.repack(*args: CommandArg) -> CommandDispatchResult`

### Baritone syntax
- `> repack - Repack chunks.`

### Domain and aliases
- Domain: `info`
- Aliases: rescan

### Sync example
```python
from pyritone import PyritoneClient

with PyritoneClient() as client:
    dispatch = client.repack()
    print(dispatch)
```

### Async example
```python
import asyncio
from pyritone import AsyncPyritoneClient

async def main() -> None:
    client = AsyncPyritoneClient()
    await client.connect()
    try:
        dispatch = await client.repack()
        print(dispatch)
    finally:
        await client.close()

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
- Source file: `RepackCommand.java`

### Related methods
- [`eta`](#eta)
- [`gc`](#gc)
- [`help`](#help)
- [`proc`](#proc)
- [Alias mappings](aliases.md) for shortcut methods

## `saveall`

Saves Baritone's cache for this world

### When to use this
- The saveall command saves Baritone's world cache.

### Method signatures
- Sync: `PyritoneClient.saveall(*args: CommandArg) -> CommandDispatchResult`
- Async: `AsyncPyritoneClient.saveall(*args: CommandArg) -> CommandDispatchResult`

### Baritone syntax
- `> saveall`

### Domain and aliases
- Domain: `info`
- Aliases: none

### Sync example
```python
from pyritone import PyritoneClient

with PyritoneClient() as client:
    dispatch = client.saveall()
    print(dispatch)
```

### Async example
```python
import asyncio
from pyritone import AsyncPyritoneClient

async def main() -> None:
    client = AsyncPyritoneClient()
    await client.connect()
    try:
        dispatch = await client.saveall()
        print(dispatch)
    finally:
        await client.close()

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
- Source file: `SaveAllCommand.java`

### Related methods
- [`eta`](#eta)
- [`gc`](#gc)
- [`help`](#help)
- [`proc`](#proc)
- [Alias mappings](aliases.md) for shortcut methods

## `version`

View the Baritone version

### When to use this
- The version command prints the version of Baritone you're currently running.

### Method signatures
- Sync: `PyritoneClient.version(*args: CommandArg) -> CommandDispatchResult`
- Async: `AsyncPyritoneClient.version(*args: CommandArg) -> CommandDispatchResult`

### Baritone syntax
- `> version - View version information, if present`

### Domain and aliases
- Domain: `info`
- Aliases: none

### Sync example
```python
from pyritone import PyritoneClient

with PyritoneClient() as client:
    dispatch = client.version()
    print(dispatch)
```

### Async example
```python
import asyncio
from pyritone import AsyncPyritoneClient

async def main() -> None:
    client = AsyncPyritoneClient()
    await client.connect()
    try:
        dispatch = await client.version()
        print(dispatch)
    finally:
        await client.close()

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
- Source file: `VersionCommand.java`

### Related methods
- [`eta`](#eta)
- [`gc`](#gc)
- [`help`](#help)
- [`proc`](#proc)
- [Alias mappings](aliases.md) for shortcut methods
