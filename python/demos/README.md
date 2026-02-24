# Pyritone Demos

## Available Demos

1. `01_nearest_entity_walk.py`
   - Source: copied from `python/test.py`.
   - Purpose: continuously find nearby mobs and walk nearest-first using `entities.list` + `goto_entity`.
   - Run from repo root:

```bash
python python/demos/01_nearest_entity_walk.py
```

2. `02_on_events_chat.py`
   - Purpose: Discord-style event API (`@client.event`) with blocking `client.connect()`.
   - Includes handlers for:
     - `on_ready` / `on_disconnect`
     - `on_chat_message` / `on_system_message`
     - `on_player_join` / `on_player_leave` / `on_player_death` / `on_player_respawn`
   - Run from repo root:

```bash
python python/demos/02_on_events_chat.py
```

## Notes

1. Requires Minecraft client with `pyritone_bridge` + Baritone loaded.
2. Requires being in-world for entity listing/pathing.
3. Use `#pyritone end` (or `/pyritone end`) in-game to terminate active Python websocket sessions.
