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
from pyritone import PyritoneClient

with PyritoneClient() as client:
    print(client.ping())
    print(client.status_get())
```
