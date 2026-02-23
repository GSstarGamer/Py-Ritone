# Developer Setup

## Requirements

- Java 21+ (build targets Java 21 bytecode)
- Python 3.10+
- Git

## Build Fabric Mod

```powershell
cd mod
.\gradlew.bat build
```

Output jar:

- `mod/build/libs/pyritone_bridge-<version>.jar`

## Run Python Tests

```powershell
cd python
python -m pytest
```

## Build Python Package

```powershell
cd python
python -m build
python -m twine check dist/*
```

## Local End-to-End Smoke

1. Install Baritone `v1.15.0` and Py-Ritone mod jar in your Fabric client `mods` folder.
2. Start Minecraft client and join a world.
3. From Python:

```python
import asyncio
from pyritone import Client


async def main() -> None:
    async with Client() as client:
        print(await client.ping())
        print(await client.status_get())


asyncio.run(main())
```
