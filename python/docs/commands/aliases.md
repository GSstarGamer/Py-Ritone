# Alias Methods

Direct alias-to-canonical mapping for all generated alias methods.

### When to use this
- Use aliases when you prefer short command names (`wp`, `p`, `r`, `c`, etc.).
- Alias methods call canonical methods and return the same result shape.

### Mapping table
| Alias command | Canonical command | Alias Python method | Canonical Python method | Domain |
| --- | --- | --- | --- | --- |
| `?` | `help` | `qmark` | `help` | `info` |
| `baritone` | `modified` | `baritone` | `modified` | `control` |
| `c` | `cancel` | `c` | `cancel` | `control` |
| `forward` | `thisway` | `forward` | `thisway` | `navigation` |
| `highway` | `axis` | `highway` | `axis` | `navigation` |
| `mod` | `modified` | `mod` | `modified` | `control` |
| `modifiedsettings` | `modified` | `modifiedsettings` | `modified` | `control` |
| `p` | `pause` | `p` | `pause` | `control` |
| `paws` | `pause` | `paws` | `pause` | `control` |
| `r` | `resume` | `r` | `resume` | `control` |
| `rescan` | `repack` | `rescan` | `repack` | `info` |
| `s` | `sel` | `s` | `sel` | `build` |
| `selection` | `sel` | `selection` | `sel` | `build` |
| `setting` | `set` | `setting` | `set` | `control` |
| `settings` | `set` | `settings` | `set` | `control` |
| `stop` | `cancel` | `stop` | `cancel` | `control` |
| `top` | `surface` | `top` | `surface` | `navigation` |
| `unpause` | `resume` | `unpause` | `resume` | `control` |
| `unpaws` | `resume` | `unpaws` | `resume` | `control` |
| `waypoint` | `waypoints` | `waypoint` | `waypoints` | `waypoints` |
| `wp` | `waypoints` | `wp` | `waypoints` | `waypoints` |

### Example
```python
import asyncio
from pyritone import Client

async def main() -> None:
    async with Client() as client:
        dispatch = await client.wp("list")
        print(dispatch)

asyncio.run(main())
```

### Return shape
```text
Aliases return the same shape as their canonical method.
```

### Common mistakes
- Mixing alias names and canonical names in the same style guide. Pick one style per codebase.
- Assuming aliases have different behavior; they are wrappers only.

### Related methods
- [Control commands](control.md)
- [Navigation commands](navigation.md)
- [Waypoints commands](waypoints.md)

## Alias cards

### `?` -> `help`

Alias method `qmark` delegates to `help`.

#### Example
```python
import asyncio
from pyritone import Client

async def main() -> None:
    async with Client() as client:
        dispatch = await client.qmark("goto")
        print(dispatch)

asyncio.run(main())
```

#### Related canonical command
- Domain: `info`
- Canonical method: [`help`](./info.md#help)

### `baritone` -> `modified`

Alias method `baritone` delegates to `modified`.

#### Example
```python
import asyncio
from pyritone import Client

async def main() -> None:
    async with Client() as client:
        dispatch = await client.baritone()
        print(dispatch)

asyncio.run(main())
```

#### Related canonical command
- Domain: `control`
- Canonical method: [`modified`](./control.md#modified)

### `c` -> `cancel`

Alias method `c` delegates to `cancel`.

#### Example
```python
import asyncio
from pyritone import Client

async def main() -> None:
    async with Client() as client:
        result = await client.c()
        print(result)

asyncio.run(main())
```

#### Related canonical command
- Domain: `control`
- Canonical method: [`cancel`](./control.md#cancel)

### `forward` -> `thisway`

Alias method `forward` delegates to `thisway`.

#### Example
```python
import asyncio
from pyritone import Client

async def main() -> None:
    async with Client() as client:
        dispatch = await client.forward(200)
        print(dispatch)

asyncio.run(main())
```

#### Related canonical command
- Domain: `navigation`
- Canonical method: [`thisway`](./navigation.md#thisway)

### `highway` -> `axis`

Alias method `highway` delegates to `axis`.

#### Example
```python
import asyncio
from pyritone import Client

async def main() -> None:
    async with Client() as client:
        dispatch = await client.highway()
        print(dispatch)

asyncio.run(main())
```

#### Related canonical command
- Domain: `navigation`
- Canonical method: [`axis`](./navigation.md#axis)

### `mod` -> `modified`

Alias method `mod` delegates to `modified`.

#### Example
```python
import asyncio
from pyritone import Client

async def main() -> None:
    async with Client() as client:
        dispatch = await client.mod()
        print(dispatch)

asyncio.run(main())
```

#### Related canonical command
- Domain: `control`
- Canonical method: [`modified`](./control.md#modified)

### `modifiedsettings` -> `modified`

Alias method `modifiedsettings` delegates to `modified`.

#### Example
```python
import asyncio
from pyritone import Client

async def main() -> None:
    async with Client() as client:
        dispatch = await client.modifiedsettings()
        print(dispatch)

asyncio.run(main())
```

#### Related canonical command
- Domain: `control`
- Canonical method: [`modified`](./control.md#modified)

### `p` -> `pause`

Alias method `p` delegates to `pause`.

#### Example
```python
import asyncio
from pyritone import Client

async def main() -> None:
    async with Client() as client:
        dispatch = await client.p()
        print(dispatch)

asyncio.run(main())
```

#### Related canonical command
- Domain: `control`
- Canonical method: [`pause`](./control.md#pause)

### `paws` -> `pause`

Alias method `paws` delegates to `pause`.

#### Example
```python
import asyncio
from pyritone import Client

async def main() -> None:
    async with Client() as client:
        dispatch = await client.paws()
        print(dispatch)

asyncio.run(main())
```

#### Related canonical command
- Domain: `control`
- Canonical method: [`pause`](./control.md#pause)

### `r` -> `resume`

Alias method `r` delegates to `resume`.

#### Example
```python
import asyncio
from pyritone import Client

async def main() -> None:
    async with Client() as client:
        dispatch = await client.r()
        print(dispatch)

asyncio.run(main())
```

#### Related canonical command
- Domain: `control`
- Canonical method: [`resume`](./control.md#resume)

### `rescan` -> `repack`

Alias method `rescan` delegates to `repack`.

#### Example
```python
import asyncio
from pyritone import Client

async def main() -> None:
    async with Client() as client:
        dispatch = await client.rescan()
        print(dispatch)

asyncio.run(main())
```

#### Related canonical command
- Domain: `info`
- Canonical method: [`repack`](./info.md#repack)

### `s` -> `sel`

Alias method `s` delegates to `sel`.

#### Example
```python
import asyncio
from pyritone import Client

async def main() -> None:
    async with Client() as client:
        dispatch = await client.s("pos1")
        print(dispatch)

asyncio.run(main())
```

#### Related canonical command
- Domain: `build`
- Canonical method: [`sel`](./build.md#sel)

### `selection` -> `sel`

Alias method `selection` delegates to `sel`.

#### Example
```python
import asyncio
from pyritone import Client

async def main() -> None:
    async with Client() as client:
        dispatch = await client.selection("pos1")
        print(dispatch)

asyncio.run(main())
```

#### Related canonical command
- Domain: `build`
- Canonical method: [`sel`](./build.md#sel)

### `setting` -> `set`

Alias method `setting` delegates to `set`.

#### Example
```python
import asyncio
from pyritone import Client

async def main() -> None:
    async with Client() as client:
        dispatch = await client.setting("allowPlace", True)
        print(dispatch)

asyncio.run(main())
```

#### Related canonical command
- Domain: `control`
- Canonical method: [`set`](./control.md#set)

### `settings` -> `set`

Alias method `settings` delegates to `set`.

#### Example
```python
import asyncio
from pyritone import Client

async def main() -> None:
    async with Client() as client:
        dispatch = await client.settings("allowPlace", True)
        print(dispatch)

asyncio.run(main())
```

#### Related canonical command
- Domain: `control`
- Canonical method: [`set`](./control.md#set)

### `stop` -> `cancel`

Alias method `stop` delegates to `cancel`.

#### Example
```python
import asyncio
from pyritone import Client

async def main() -> None:
    async with Client() as client:
        result = await client.stop()
        print(result)

asyncio.run(main())
```

#### Related canonical command
- Domain: `control`
- Canonical method: [`cancel`](./control.md#cancel)

### `top` -> `surface`

Alias method `top` delegates to `surface`.

#### Example
```python
import asyncio
from pyritone import Client

async def main() -> None:
    async with Client() as client:
        dispatch = await client.top()
        print(dispatch)

asyncio.run(main())
```

#### Related canonical command
- Domain: `navigation`
- Canonical method: [`surface`](./navigation.md#surface)

### `unpause` -> `resume`

Alias method `unpause` delegates to `resume`.

#### Example
```python
import asyncio
from pyritone import Client

async def main() -> None:
    async with Client() as client:
        dispatch = await client.unpause()
        print(dispatch)

asyncio.run(main())
```

#### Related canonical command
- Domain: `control`
- Canonical method: [`resume`](./control.md#resume)

### `unpaws` -> `resume`

Alias method `unpaws` delegates to `resume`.

#### Example
```python
import asyncio
from pyritone import Client

async def main() -> None:
    async with Client() as client:
        dispatch = await client.unpaws()
        print(dispatch)

asyncio.run(main())
```

#### Related canonical command
- Domain: `control`
- Canonical method: [`resume`](./control.md#resume)

### `waypoint` -> `waypoints`

Alias method `waypoint` delegates to `waypoints`.

#### Example
```python
import asyncio
from pyritone import Client

async def main() -> None:
    async with Client() as client:
        dispatch = await client.waypoint("list")
        print(dispatch)

asyncio.run(main())
```

#### Related canonical command
- Domain: `waypoints`
- Canonical method: [`waypoints`](./waypoints.md#waypoints)

### `wp` -> `waypoints`

Alias method `wp` delegates to `waypoints`.

#### Example
```python
import asyncio
from pyritone import Client

async def main() -> None:
    async with Client() as client:
        dispatch = await client.wp("list")
        print(dispatch)

asyncio.run(main())
```

#### Related canonical command
- Domain: `waypoints`
- Canonical method: [`waypoints`](./waypoints.md#waypoints)
