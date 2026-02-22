# CLI

Use `pyritone` directly from terminal for quick checks and scripts.

### When to use this

- You want quick diagnostics without writing Python code.
- You need shell scripts for simple bridge automation.

### Sync example

```bash
pyritone ping
pyritone status
pyritone exec "goto 100 70 100"
pyritone cancel
```

### Async example

```text
The CLI is internally async, but you use it as normal shell commands.
```

### Return shape

```text
CLI commands print JSON payloads from the bridge:
- ping/status/exec/cancel: pretty JSON
- events: streaming JSON lines
```

### Common mistakes

- Not quoting command strings with spaces in `pyritone exec`.
- Forgetting `--task-id` when canceling a specific task.
- Running CLI without bridge metadata/token available.

### Related methods

- Python equivalent APIs: `sync-client.md`, `async-client.md`
- Troubleshooting: `errors-and-troubleshooting.md`

## Commands

- `pyritone ping`
- `pyritone status`
- `pyritone exec "<baritone command>"`
- `pyritone cancel [--task-id <id>]`
- `pyritone events`

## Connection Overrides

- `--host`
- `--port`
- `--token`
- `--bridge-info`
- `--timeout`

