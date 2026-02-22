# Build Commands

Usage-first command guide for `Build` methods in `pyritone`.

### When to use this
- Schematic and selection operations.
- Generated from Baritone `v1.15.0` command metadata.

### Commands in this page
- [`build`](#build)
- [`litematica`](#litematica)
- [`sel`](#sel)

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

## Pyritone Build Helpers

Extra helpers for local schematic files relative to your Python script.

### Sync example
```python
from pyritone import PyritoneClient

with PyritoneClient() as client:
    dispatch = client.build_file("schematics/base", 100, 70, 100)
    print(dispatch)
    terminal = client.build_file_wait("schematics/base", 100, 70, 100)
    print(terminal)
```

### Async example
```python
import asyncio
from pyritone import AsyncPyritoneClient

async def main() -> None:
    client = AsyncPyritoneClient()
    await client.connect()
    try:
        dispatch = await client.build_file("schematics/base", 100, 70, 100)
        print(dispatch)
        terminal = await client.build_file_wait("schematics/base", 100, 70, 100)
        print(terminal)
    finally:
        await client.close()

asyncio.run(main())
```

### Notes
- Relative paths are resolved from the calling Python file directory by default.
- Pass `base_dir` to override path base.
- No extension uses probing order: `.schem`, `.schematic`, `.litematic`.
- If no file matches, extension-less path is sent so Baritone fallback extension still applies.

## `build`

Build a schematic

### When to use this
- Build a schematic from a file.

### Method signatures
- Sync: `PyritoneClient.build(*args: CommandArg) -> CommandDispatchResult`
- Async: `AsyncPyritoneClient.build(*args: CommandArg) -> CommandDispatchResult`

### Baritone syntax
- `> build <filename> - Loads and builds '<filename>.schematic'`
- `> build <filename> <x> <y> <z> - Custom position`

### Domain and aliases
- Domain: `build`
- Aliases: none

### Sync example
```python
from pyritone import PyritoneClient

with PyritoneClient() as client:
    dispatch = client.build("starter_house")
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
        dispatch = await client.build("starter_house")
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

### Wait pattern
If `task_id` exists, wait for a terminal event:

- Sync: `terminal = client.wait_for_task(dispatch["task_id"])`
- Async: `terminal = await client.wait_for_task(dispatch["task_id"])`

### Common mistakes
- Passing separate string tokens when one argument contains spaces. Use one Python string.
- Treating dispatch as completion. Dispatch is immediate; wait on `task_id` when needed.
- For local Python-file-relative schematic paths, use `build_file(...)`.
- Use `build_file_wait(...)` when you want dispatch + wait in one call.

### Source provenance
- Baritone version: `v1.15.0`
- Source file: `BuildCommand.java`

### Related methods
- [`litematica`](#litematica)
- [`sel`](#sel)
- [Alias mappings](aliases.md) for shortcut methods

## `litematica`

Builds the loaded schematic

### When to use this
- Build a schematic currently open in Litematica.

### Method signatures
- Sync: `PyritoneClient.litematica(*args: CommandArg) -> CommandDispatchResult`
- Async: `AsyncPyritoneClient.litematica(*args: CommandArg) -> CommandDispatchResult`

### Baritone syntax
- `> litematica`
- `> litematica <#>`

### Domain and aliases
- Domain: `build`
- Aliases: none

### Sync example
```python
from pyritone import PyritoneClient

with PyritoneClient() as client:
    dispatch = client.litematica()
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
        dispatch = await client.litematica()
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

### Wait pattern
If `task_id` exists, wait for a terminal event:

- Sync: `terminal = client.wait_for_task(dispatch["task_id"])`
- Async: `terminal = await client.wait_for_task(dispatch["task_id"])`

### Common mistakes
- Passing separate string tokens when one argument contains spaces. Use one Python string.
- Treating dispatch as completion. Dispatch is immediate; wait on `task_id` when needed.

### Source provenance
- Baritone version: `v1.15.0`
- Source file: `LitematicaCommand.java`

### Related methods
- [`build`](#build)
- [`sel`](#sel)
- [Alias mappings](aliases.md) for shortcut methods

## `sel`

WorldEdit-like commands

### When to use this
- The sel command allows you to manipulate Baritone's selections, similarly to WorldEdit.

### Method signatures
- Sync: `PyritoneClient.sel(*args: CommandArg) -> CommandDispatchResult`
- Async: `AsyncPyritoneClient.sel(*args: CommandArg) -> CommandDispatchResult`

### Baritone syntax
- `> sel pos1/p1/1 - Set position 1 to your current position.`
- `> sel pos1/p1/1 <x> <y> <z> - Set position 1 to a relative position.`
- `> sel pos2/p2/2 - Set position 2 to your current position.`
- `> sel pos2/p2/2 <x> <y> <z> - Set position 2 to a relative position.`
- `> sel clear/c - Clear the selection.`
- `> sel undo/u - Undo the last action (setting positions, creating selections, etc.)`
- `> sel set/fill/s/f [block] - Completely fill all selections with a block.`
- `> sel walls/w [block] - Fill in the walls of the selection with a specified block.`
- `> sel shell/shl [block] - The same as walls, but fills in a ceiling and floor too.`
- `> sel sphere/sph [block] - Fills the selection with a sphere bounded by the sides.`
- `> sel hsphere/hsph [block] - The same as sphere, but hollow.`
- `> sel cylinder/cyl [block] <axis> - Fills the selection with a cylinder bounded by the sides, oriented about the given axis. (default=y)`
- `> sel hcylinder/hcyl [block] <axis> - The same as cylinder, but hollow.`
- `> sel cleararea/ca - Basically 'set air'.`
- `> sel replace/r <blocks...> <with> - Replaces blocks with another block.`
- `> sel copy/cp <x> <y> <z> - Copy the selected area relative to the specified or your position.`
- `> sel paste/p <x> <y> <z> - Build the copied area relative to the specified or your position.`
- `> sel expand <target> <direction> <blocks> - Expand the targets.`
- `> sel contract <target> <direction> <blocks> - Contract the targets.`
- `> sel shift <target> <direction> <blocks> - Shift the targets (does not resize).`

### Domain and aliases
- Domain: `build`
- Aliases: selection, s

### Sync example
```python
from pyritone import PyritoneClient

with PyritoneClient() as client:
    dispatch = client.sel("pos1")
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
        dispatch = await client.sel("pos1")
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

### Wait pattern
If `task_id` exists, wait for a terminal event:

- Sync: `terminal = client.wait_for_task(dispatch["task_id"])`
- Async: `terminal = await client.wait_for_task(dispatch["task_id"])`

### Common mistakes
- Passing separate string tokens when one argument contains spaces. Use one Python string.
- Treating dispatch as completion. Dispatch is immediate; wait on `task_id` when needed.

### Source provenance
- Baritone version: `v1.15.0`
- Source file: `SelCommand.java`

### Related methods
- [`build`](#build)
- [`litematica`](#litematica)
- [Alias mappings](aliases.md) for shortcut methods
