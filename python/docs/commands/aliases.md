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

### Sync example
```python
from pyritone import PyritoneClient

with PyritoneClient() as client:
    dispatch = client.wp("list")
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
        dispatch = await client.wp("list")
        print(dispatch)
    finally:
        await client.close()

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

#### Sync example
```python
from pyritone import PyritoneClient

with PyritoneClient() as client:
    dispatch = client.qmark("goto")
    print(dispatch)
```

#### Async example
```python
import asyncio
from pyritone import AsyncPyritoneClient

async def main() -> None:
    client = AsyncPyritoneClient()
    await client.connect()
    try:
        dispatch = await client.qmark("goto")
        print(dispatch)
    finally:
        await client.close()

asyncio.run(main())
```

#### Related canonical command
- Domain: `info`
- Canonical method: [`help`](./info.md#help)

### `baritone` -> `modified`

Alias method `baritone` delegates to `modified`.

#### Sync example
```python
from pyritone import PyritoneClient

with PyritoneClient() as client:
    dispatch = client.baritone()
    print(dispatch)
```

#### Async example
```python
import asyncio
from pyritone import AsyncPyritoneClient

async def main() -> None:
    client = AsyncPyritoneClient()
    await client.connect()
    try:
        dispatch = await client.baritone()
        print(dispatch)
    finally:
        await client.close()

asyncio.run(main())
```

#### Related canonical command
- Domain: `control`
- Canonical method: [`modified`](./control.md#modified)

### `c` -> `cancel`

Alias method `c` delegates to `cancel`.

#### Sync example
```python
from pyritone import PyritoneClient

with PyritoneClient() as client:
    result = client.c()
    print(result)
```

#### Async example
```python
import asyncio
from pyritone import AsyncPyritoneClient

async def main() -> None:
    client = AsyncPyritoneClient()
    await client.connect()
    try:
        result = await client.c()
        print(result)
    finally:
        await client.close()

asyncio.run(main())
```

#### Related canonical command
- Domain: `control`
- Canonical method: [`cancel`](./control.md#cancel)

### `forward` -> `thisway`

Alias method `forward` delegates to `thisway`.

#### Sync example
```python
from pyritone import PyritoneClient

with PyritoneClient() as client:
    dispatch = client.forward(200)
    print(dispatch)
```

#### Async example
```python
import asyncio
from pyritone import AsyncPyritoneClient

async def main() -> None:
    client = AsyncPyritoneClient()
    await client.connect()
    try:
        dispatch = await client.forward(200)
        print(dispatch)
    finally:
        await client.close()

asyncio.run(main())
```

#### Related canonical command
- Domain: `navigation`
- Canonical method: [`thisway`](./navigation.md#thisway)

### `highway` -> `axis`

Alias method `highway` delegates to `axis`.

#### Sync example
```python
from pyritone import PyritoneClient

with PyritoneClient() as client:
    dispatch = client.highway()
    print(dispatch)
```

#### Async example
```python
import asyncio
from pyritone import AsyncPyritoneClient

async def main() -> None:
    client = AsyncPyritoneClient()
    await client.connect()
    try:
        dispatch = await client.highway()
        print(dispatch)
    finally:
        await client.close()

asyncio.run(main())
```

#### Related canonical command
- Domain: `navigation`
- Canonical method: [`axis`](./navigation.md#axis)

### `mod` -> `modified`

Alias method `mod` delegates to `modified`.

#### Sync example
```python
from pyritone import PyritoneClient

with PyritoneClient() as client:
    dispatch = client.mod()
    print(dispatch)
```

#### Async example
```python
import asyncio
from pyritone import AsyncPyritoneClient

async def main() -> None:
    client = AsyncPyritoneClient()
    await client.connect()
    try:
        dispatch = await client.mod()
        print(dispatch)
    finally:
        await client.close()

asyncio.run(main())
```

#### Related canonical command
- Domain: `control`
- Canonical method: [`modified`](./control.md#modified)

### `modifiedsettings` -> `modified`

Alias method `modifiedsettings` delegates to `modified`.

#### Sync example
```python
from pyritone import PyritoneClient

with PyritoneClient() as client:
    dispatch = client.modifiedsettings()
    print(dispatch)
```

#### Async example
```python
import asyncio
from pyritone import AsyncPyritoneClient

async def main() -> None:
    client = AsyncPyritoneClient()
    await client.connect()
    try:
        dispatch = await client.modifiedsettings()
        print(dispatch)
    finally:
        await client.close()

asyncio.run(main())
```

#### Related canonical command
- Domain: `control`
- Canonical method: [`modified`](./control.md#modified)

### `p` -> `pause`

Alias method `p` delegates to `pause`.

#### Sync example
```python
from pyritone import PyritoneClient

with PyritoneClient() as client:
    dispatch = client.p()
    print(dispatch)
```

#### Async example
```python
import asyncio
from pyritone import AsyncPyritoneClient

async def main() -> None:
    client = AsyncPyritoneClient()
    await client.connect()
    try:
        dispatch = await client.p()
        print(dispatch)
    finally:
        await client.close()

asyncio.run(main())
```

#### Related canonical command
- Domain: `control`
- Canonical method: [`pause`](./control.md#pause)

### `paws` -> `pause`

Alias method `paws` delegates to `pause`.

#### Sync example
```python
from pyritone import PyritoneClient

with PyritoneClient() as client:
    dispatch = client.paws()
    print(dispatch)
```

#### Async example
```python
import asyncio
from pyritone import AsyncPyritoneClient

async def main() -> None:
    client = AsyncPyritoneClient()
    await client.connect()
    try:
        dispatch = await client.paws()
        print(dispatch)
    finally:
        await client.close()

asyncio.run(main())
```

#### Related canonical command
- Domain: `control`
- Canonical method: [`pause`](./control.md#pause)

### `r` -> `resume`

Alias method `r` delegates to `resume`.

#### Sync example
```python
from pyritone import PyritoneClient

with PyritoneClient() as client:
    dispatch = client.r()
    print(dispatch)
```

#### Async example
```python
import asyncio
from pyritone import AsyncPyritoneClient

async def main() -> None:
    client = AsyncPyritoneClient()
    await client.connect()
    try:
        dispatch = await client.r()
        print(dispatch)
    finally:
        await client.close()

asyncio.run(main())
```

#### Related canonical command
- Domain: `control`
- Canonical method: [`resume`](./control.md#resume)

### `rescan` -> `repack`

Alias method `rescan` delegates to `repack`.

#### Sync example
```python
from pyritone import PyritoneClient

with PyritoneClient() as client:
    dispatch = client.rescan()
    print(dispatch)
```

#### Async example
```python
import asyncio
from pyritone import AsyncPyritoneClient

async def main() -> None:
    client = AsyncPyritoneClient()
    await client.connect()
    try:
        dispatch = await client.rescan()
        print(dispatch)
    finally:
        await client.close()

asyncio.run(main())
```

#### Related canonical command
- Domain: `info`
- Canonical method: [`repack`](./info.md#repack)

### `s` -> `sel`

Alias method `s` delegates to `sel`.

#### Sync example
```python
from pyritone import PyritoneClient

with PyritoneClient() as client:
    dispatch = client.s("pos1")
    print(dispatch)
```

#### Async example
```python
import asyncio
from pyritone import AsyncPyritoneClient

async def main() -> None:
    client = AsyncPyritoneClient()
    await client.connect()
    try:
        dispatch = await client.s("pos1")
        print(dispatch)
    finally:
        await client.close()

asyncio.run(main())
```

#### Related canonical command
- Domain: `build`
- Canonical method: [`sel`](./build.md#sel)

### `selection` -> `sel`

Alias method `selection` delegates to `sel`.

#### Sync example
```python
from pyritone import PyritoneClient

with PyritoneClient() as client:
    dispatch = client.selection("pos1")
    print(dispatch)
```

#### Async example
```python
import asyncio
from pyritone import AsyncPyritoneClient

async def main() -> None:
    client = AsyncPyritoneClient()
    await client.connect()
    try:
        dispatch = await client.selection("pos1")
        print(dispatch)
    finally:
        await client.close()

asyncio.run(main())
```

#### Related canonical command
- Domain: `build`
- Canonical method: [`sel`](./build.md#sel)

### `setting` -> `set`

Alias method `setting` delegates to `set`.

#### Sync example
```python
from pyritone import PyritoneClient

with PyritoneClient() as client:
    dispatch = client.setting("allowPlace", True)
    print(dispatch)
```

#### Async example
```python
import asyncio
from pyritone import AsyncPyritoneClient

async def main() -> None:
    client = AsyncPyritoneClient()
    await client.connect()
    try:
        dispatch = await client.setting("allowPlace", True)
        print(dispatch)
    finally:
        await client.close()

asyncio.run(main())
```

#### Related canonical command
- Domain: `control`
- Canonical method: [`set`](./control.md#set)

### `settings` -> `set`

Alias method `settings` delegates to `set`.

#### Sync example
```python
from pyritone import PyritoneClient

with PyritoneClient() as client:
    dispatch = client.settings("allowPlace", True)
    print(dispatch)
```

#### Async example
```python
import asyncio
from pyritone import AsyncPyritoneClient

async def main() -> None:
    client = AsyncPyritoneClient()
    await client.connect()
    try:
        dispatch = await client.settings("allowPlace", True)
        print(dispatch)
    finally:
        await client.close()

asyncio.run(main())
```

#### Related canonical command
- Domain: `control`
- Canonical method: [`set`](./control.md#set)

### `stop` -> `cancel`

Alias method `stop` delegates to `cancel`.

#### Sync example
```python
from pyritone import PyritoneClient

with PyritoneClient() as client:
    result = client.stop()
    print(result)
```

#### Async example
```python
import asyncio
from pyritone import AsyncPyritoneClient

async def main() -> None:
    client = AsyncPyritoneClient()
    await client.connect()
    try:
        result = await client.stop()
        print(result)
    finally:
        await client.close()

asyncio.run(main())
```

#### Related canonical command
- Domain: `control`
- Canonical method: [`cancel`](./control.md#cancel)

### `top` -> `surface`

Alias method `top` delegates to `surface`.

#### Sync example
```python
from pyritone import PyritoneClient

with PyritoneClient() as client:
    dispatch = client.top()
    print(dispatch)
```

#### Async example
```python
import asyncio
from pyritone import AsyncPyritoneClient

async def main() -> None:
    client = AsyncPyritoneClient()
    await client.connect()
    try:
        dispatch = await client.top()
        print(dispatch)
    finally:
        await client.close()

asyncio.run(main())
```

#### Related canonical command
- Domain: `navigation`
- Canonical method: [`surface`](./navigation.md#surface)

### `unpause` -> `resume`

Alias method `unpause` delegates to `resume`.

#### Sync example
```python
from pyritone import PyritoneClient

with PyritoneClient() as client:
    dispatch = client.unpause()
    print(dispatch)
```

#### Async example
```python
import asyncio
from pyritone import AsyncPyritoneClient

async def main() -> None:
    client = AsyncPyritoneClient()
    await client.connect()
    try:
        dispatch = await client.unpause()
        print(dispatch)
    finally:
        await client.close()

asyncio.run(main())
```

#### Related canonical command
- Domain: `control`
- Canonical method: [`resume`](./control.md#resume)

### `unpaws` -> `resume`

Alias method `unpaws` delegates to `resume`.

#### Sync example
```python
from pyritone import PyritoneClient

with PyritoneClient() as client:
    dispatch = client.unpaws()
    print(dispatch)
```

#### Async example
```python
import asyncio
from pyritone import AsyncPyritoneClient

async def main() -> None:
    client = AsyncPyritoneClient()
    await client.connect()
    try:
        dispatch = await client.unpaws()
        print(dispatch)
    finally:
        await client.close()

asyncio.run(main())
```

#### Related canonical command
- Domain: `control`
- Canonical method: [`resume`](./control.md#resume)

### `waypoint` -> `waypoints`

Alias method `waypoint` delegates to `waypoints`.

#### Sync example
```python
from pyritone import PyritoneClient

with PyritoneClient() as client:
    dispatch = client.waypoint("list")
    print(dispatch)
```

#### Async example
```python
import asyncio
from pyritone import AsyncPyritoneClient

async def main() -> None:
    client = AsyncPyritoneClient()
    await client.connect()
    try:
        dispatch = await client.waypoint("list")
        print(dispatch)
    finally:
        await client.close()

asyncio.run(main())
```

#### Related canonical command
- Domain: `waypoints`
- Canonical method: [`waypoints`](./waypoints.md#waypoints)

### `wp` -> `waypoints`

Alias method `wp` delegates to `waypoints`.

#### Sync example
```python
from pyritone import PyritoneClient

with PyritoneClient() as client:
    dispatch = client.wp("list")
    print(dispatch)
```

#### Async example
```python
import asyncio
from pyritone import AsyncPyritoneClient

async def main() -> None:
    client = AsyncPyritoneClient()
    await client.connect()
    try:
        dispatch = await client.wp("list")
        print(dispatch)
    finally:
        await client.close()

asyncio.run(main())
```

#### Related canonical command
- Domain: `waypoints`
- Canonical method: [`waypoints`](./waypoints.md#waypoints)
