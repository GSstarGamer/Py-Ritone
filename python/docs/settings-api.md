# Settings API

Use the settings namespace to get/set/toggle/reset Baritone settings cleanly.

### When to use this

- You want typed-looking access like `client.settings.allowPlace`.
- You need to modify settings before pathing commands.

### Example

```python
from pyritone import Client

client = Client()
await client.connect()
try:
    print(await client.settings.allowPlace.set(True))
    print(await client.settings.allowPlace.get())
    print(await client.settings.allowPlace.toggle())
    print(await client.settings.allowPlace.reset())
finally:
    await client.close()
```

### Return shape

```text
All settings operations return CommandDispatchResult.
The command text uses the `set` command internally:
- set <name> <value>
- set <name>
- set toggle <name>
- set reset <name>
```

### Common mistakes

- Expecting direct Python booleans back from `get()`; you get dispatch payload.
- Forgetting that setting names are Baritone setting identifiers.

### Related methods

- `commands/control.md`
- `tasks-events-and-waiting.md`
- `errors-and-troubleshooting.md`
