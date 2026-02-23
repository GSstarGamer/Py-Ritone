# Pyritone Demos

## Current Demo

1. `01_nearest_entity_walk.py`
   - Source: copied from `python/test.py`.
   - Purpose: continuously find nearby mobs and walk nearest-first using `entities.list` + `goto_entity`.
   - Run from repo root:

```bash
python python/demos/01_nearest_entity_walk.py
```

## Notes

1. Requires Minecraft client with `pyritone_bridge` + Baritone loaded.
2. Requires being in-world for entity listing/pathing.
3. Use `#pyritone end` (or `/pyritone end`) in-game to terminate active Python websocket sessions.
