# Baritone Typed Parity Matrix (v1.15.0)

Wave 7 inventory and coverage matrix for typed wrappers in:

- `baritone.api.cache`
- `baritone.api.selection`
- `baritone.api.schematic`
- `baritone.api.command`
- `baritone.api.utils`
- `baritone.api.event`

## Inventory Source

- Artifact: `mod/.gradle/dev-mods/baritone-api-fabric-1.15.0.jar`
- Inventory command:

```powershell
tar -tf mod/.gradle/dev-mods/baritone-api-fabric-1.15.0.jar `
| ? { $_ -match '^baritone/api/(cache|selection|schematic|command|utils|event)/.*\.class$' -and $_ -notmatch '\$' }
```

Package-tree class counts (non-inner classes):

- `cache`: 9
- `selection`: 2
- `schematic`: 23
- `command`: 43
- `utils`: 25
- `event`: 20

## Coverage Matrix

### cache

| Java API class | Python surface | Status |
| --- | --- | --- |
| `baritone.api.cache.IWorldProvider` | `WorldProviderRef`, `BaritoneNamespace.world_provider()` | Wrapped |
| `baritone.api.cache.IWorldData` | `WorldDataRef` | Wrapped |
| `baritone.api.cache.ICachedWorld` | `CachedWorldRef` | Wrapped |
| `baritone.api.cache.IWaypointCollection` | `WaypointCollectionRef` | Wrapped |
| `baritone.api.cache.IWaypoint` | `WaypointRef` | Wrapped |
| `baritone.api.cache.IWorldScanner` | `WorldScannerRef`, `BaritoneNamespace.world_scanner()` | Wrapped |
| `baritone.api.cache.Waypoint` | `BaritoneNamespace.waypoint()` constructor helper | Wrapped |
| `baritone.api.cache.IBlockTypeAccess` | N/A | Deferred |
| `baritone.api.cache.ICachedRegion` | N/A | Deferred |

### selection

| Java API class | Python surface | Status |
| --- | --- | --- |
| `baritone.api.selection.ISelectionManager` | `SelectionManagerRef`, `BaritoneNamespace.selection_manager()` | Wrapped |
| `baritone.api.selection.ISelection` | `SelectionRef` | Wrapped |

### schematic

| Java API class | Python surface | Status |
| --- | --- | --- |
| `baritone.api.schematic.ISchematicSystem` | `SchematicSystemRef`, `BaritoneNamespace.schematic_system()` | Wrapped |
| `baritone.api.schematic.format.ISchematicFormat` | `SchematicFormatRef` | Wrapped |
| `baritone.api.schematic.ISchematic` | `SchematicRef` | Wrapped |
| `baritone.api.schematic.IStaticSchematic` | `StaticSchematicRef` | Wrapped |
| `baritone.api.schematic.FillSchematic` | `FillSchematicRef`, `BaritoneNamespace.fill_schematic()` | Wrapped |
| `baritone.api.schematic.CompositeSchematic` | `CompositeSchematicRef`, `BaritoneNamespace.composite_schematic()` | Wrapped |
| `baritone.api.schematic.mask.Mask` | `MaskRef` | Wrapped |
| `baritone.api.schematic.mask.StaticMask` | `StaticMaskRef` | Wrapped |
| `baritone.api.schematic.mask.shape.SphereMask` | `BaritoneNamespace.sphere_mask()` | Wrapped |
| `baritone.api.schematic.mask.shape.CylinderMask` | `BaritoneNamespace.cylinder_mask()` | Wrapped |
| `baritone.api.schematic.MaskSchematic` | `BaritoneNamespace.mask_schematic()` | Wrapped |
| Other schematic classes (`AbstractSchematic`, `MirroredSchematic`, `ReplaceSchematic`, etc.) | N/A | Deferred |

### command

| Java API class | Python surface | Status |
| --- | --- | --- |
| `baritone.api.command.manager.ICommandManager` | `CommandManagerRef`, `BaritoneNamespace.command_manager()` | Wrapped |
| `baritone.api.command.ICommand` | `CommandRef` | Wrapped |
| `baritone.api.command.ICommandSystem` | `CommandSystemRef`, `BaritoneNamespace.command_system()` | Wrapped |
| `baritone.api.command.argparser.IArgParserManager` | `ArgParserManagerRef` | Wrapped |
| `baritone.api.command.registry.Registry` | `RegistryRef` | Wrapped |
| Other command classes (datatypes/exception/helpers/concrete command types) | N/A | Deferred |

### utils

| Java API class | Python surface | Status |
| --- | --- | --- |
| `baritone.api.utils.IPlayerContext` | `PlayerContextRef`, `BaritoneNamespace.player_context()` | Wrapped |
| `baritone.api.utils.IInputOverrideHandler` | `InputOverrideHandlerRef`, `BaritoneNamespace.input_override_handler()` | Wrapped |
| `baritone.api.utils.BetterBlockPos` | `BaritoneNamespace.better_block_pos()`, selection helpers | Wrapped |
| `baritone.api.utils.BlockOptionalMetaLookup` | `BaritoneNamespace.block_optional_meta_lookup()` | Wrapped |
| `baritone.api.utils.input.Input` | `BaritoneNamespace.input_key()` | Wrapped |
| Other utility classes (`Rotation`, `TypeUtils`, `VecUtils`, etc.) | N/A | Deferred |

### event

| Java API class | Python surface | Status |
| --- | --- | --- |
| `baritone.api.event.listener.IEventBus` | `EventBusRef`, `BaritoneNamespace.game_event_handler()` | Wrapped |
| `baritone.api.event.listener.IGameEventListener` | `GameEventListenerRef` | Wrapped (subset callbacks) |
| Event payload classes in `baritone.api.event.events.*` | N/A | Deferred |
| `baritone.api.event.listener.AbstractGameEventListener` | N/A | Deferred |

## Notes

- `BaritoneNamespace.provider()` wraps `baritone.api.BaritoneAPI.getProvider()` and unlocks provider-level `world_scanner`, `command_system`, and `schematic_system`.
- Deferred classes are tracked intentionally for later parity burn-down waves; Wave 7 focuses on typed access to the package interfaces most relevant to command/control workflows.
