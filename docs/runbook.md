# Runbook

## Release Prep

- Async-only release checklist: `docs/release-checklist.md`
- Parity/fallback debt snapshot: `python/docs/release-parity-fallback-report.md`

## Bridge Not Starting

- Check Minecraft client logs for `pyritone_bridge` startup errors.
- Ensure no process is already using `127.0.0.1:27841`.

## Python Client Cannot Connect

- Confirm Minecraft has started with both mods installed.
- Confirm bridge file exists:
  - `%APPDATA%\.minecraft\config\pyritone_bridge\bridge-info.json`
- Use explicit options for troubleshooting:

```bash
pyritone --host 127.0.0.1 --port 27841 --token <token> ping
```

## Unauthorized Errors

- Token mismatch between Python side and bridge info file.
- Restart Minecraft client to regenerate/update bridge metadata.

## Baritone Unavailable

- Baritone mod is missing or wrong version.
- Install `baritone-api-fabric-1.15.0.jar`.

## Not In World

- Connect to any singleplayer or multiplayer world before running `baritone.execute`.
