# Pyritone Baritone Command Reference

Generated from Baritone `v1.15.0` source files.

## Canonical Commands

### `axis`

- Python method: `axis`
- Aliases: highway
- Domain: `navigation`
- Source: `AxisCommand.java`
- Summary: Set a goal to the axes

Usage:
- `> axis`

Notes:
- The axis command sets a goal that tells Baritone to head towards the nearest axis. That is, X=0 or Z=0.
- Usage:
- > axis

### `blacklist`

- Python method: `blacklist`
- Aliases: none
- Domain: `navigation`
- Source: `BlacklistCommand.java`
- Summary: Blacklist closest block

Usage:
- `> blacklist`

Notes:
- While going to a block this command blacklists the closest block so that Baritone won't attempt to get to it.
- Usage:
- > blacklist

### `build`

- Python method: `build`
- Aliases: none
- Domain: `build`
- Source: `BuildCommand.java`
- Summary: Build a schematic

Usage:
- `> build <filename> - Loads and builds '<filename>.schematic'`
- `> build <filename> <x> <y> <z> - Custom position`

Notes:
- Build a schematic from a file.
- Usage:
- > build <filename> - Loads and builds '<filename>.schematic'
- > build <filename> <x> <y> <z> - Custom position

### `cancel`

- Python method: `cancel`
- Aliases: c, stop
- Domain: `control`
- Source: `ExecutionControlCommands.java`
- Summary: Cancel what Baritone is currently doing

Usage:
- `> cancel`

Notes:
- The cancel command tells Baritone to stop whatever it's currently doing.
- Usage:
- > cancel

### `click`

- Python method: `click`
- Aliases: none
- Domain: `world`
- Source: `ClickCommand.java`
- Summary: Open click

Usage:
- `> click`

Notes:
- Opens click dude
- Usage:
- > click

### `come`

- Python method: `come`
- Aliases: none
- Domain: `navigation`
- Source: `ComeCommand.java`
- Summary: Start heading towards your camera

Usage:
- `> come`

Notes:
- The come command tells Baritone to head towards your camera.
- This can be useful in hacked clients where freecam doesn't move your player position.
- Usage:
- > come

### `elytra`

- Python method: `elytra`
- Aliases: none
- Domain: `navigation`
- Source: `ElytraCommand.java`
- Summary: elytra time

Usage:
- `> elytra - fly to the current goal`
- `> elytra reset - Resets the state of the process, but will try to keep flying to the same goal.`
- `> elytra repack - Queues all of the chunks in render distance to be given to the native library.`
- `> elytra supported - Tells you if baritone ships a native library that is compatible with your PC.`

Notes:
- The elytra command tells baritone to, in the nether, automatically fly to the current goal.
- Usage:
- > elytra - fly to the current goal
- > elytra reset - Resets the state of the process, but will try to keep flying to the same goal.
- > elytra repack - Queues all of the chunks in render distance to be given to the native library.
- > elytra supported - Tells you if baritone ships a native library that is compatible with your PC.

### `eta`

- Python method: `eta`
- Aliases: none
- Domain: `info`
- Source: `ETACommand.java`
- Summary: View the current ETA

Usage:
- `> eta - View ETA, if present`

Notes:
- The ETA command provides information about the estimated time until the next segment.
- and the goal
- Be aware that the ETA to your goal is really unprecise
- Usage:
- > eta - View ETA, if present

### `explore`

- Python method: `explore`
- Aliases: none
- Domain: `navigation`
- Source: `ExploreCommand.java`
- Summary: Explore things

Usage:
- `> explore - Explore from your current position.`
- `> explore <x> <z> - Explore from the specified X and Z position.`

Notes:
- Tell Baritone to explore randomly. If you used explorefilter before this, it will be applied.
- Usage:
- > explore - Explore from your current position.
- > explore <x> <z> - Explore from the specified X and Z position.

### `explorefilter`

- Python method: `explorefilter`
- Aliases: none
- Domain: `navigation`
- Source: `ExploreFilterCommand.java`
- Summary: Explore chunks from a json

Usage:
- `> explorefilter <path> [invert] - Load the JSON file referenced by the specified path. If invert is specified, it must be the literal word 'invert'.`

Notes:
- Apply an explore filter before using explore, which tells the explore process which chunks have been explored/not explored.
- The JSON file will follow this format: [{"x":0,"z":0},...]
- If 'invert' is specified, the chunks listed will be considered NOT explored, rather than explored.
- Usage:
- > explorefilter <path> [invert] - Load the JSON file referenced by the specified path. If invert is specified, it must be the literal word 'invert'.

### `farm`

- Python method: `farm`
- Aliases: none
- Domain: `world`
- Source: `FarmCommand.java`
- Summary: Farm nearby crops

Usage:
- `> farm - farms every crop it can find.`
- `> farm <range> - farm crops within range from the starting position.`
- `> farm <range> <waypoint> - farm crops within range from waypoint.`

Notes:
- The farm command starts farming nearby plants. It harvests mature crops and plants new ones.
- Usage:
- > farm - farms every crop it can find.
- > farm <range> - farm crops within range from the starting position.
- > farm <range> <waypoint> - farm crops within range from waypoint.

### `find`

- Python method: `find`
- Aliases: none
- Domain: `world`
- Source: `FindCommand.java`
- Summary: Find positions of a certain block

Usage:
- `> find <block> [...] - Try finding the listed blocks`

Notes:
- The find command searches through Baritone's cache and attempts to find the location of the block.
- Tab completion will suggest only cached blocks and uncached blocks can not be found.
- Usage:
- > find <block> [...] - Try finding the listed blocks

### `follow`

- Python method: `follow`
- Aliases: none
- Domain: `world`
- Source: `FollowCommand.java`
- Summary: Follow entity things

Usage:
- `> follow entities - Follows all entities.`
- `> follow entity <entity1> <entity2> <...> - Follow certain entities (for example 'skeleton', 'horse' etc.)`
- `> follow players - Follow players`
- `> follow player <username1> <username2> <...> - Follow certain players`

Notes:
- The follow command tells Baritone to follow certain kinds of entities.
- Usage:
- > follow entities - Follows all entities.
- > follow entity <entity1> <entity2> <...> - Follow certain entities (for example 'skeleton', 'horse' etc.)
- > follow players - Follow players
- > follow player <username1> <username2> <...> - Follow certain players

### `forcecancel`

- Python method: `forcecancel`
- Aliases: none
- Domain: `control`
- Source: `ForceCancelCommand.java`
- Summary: Force cancel

Usage:
- `> forcecancel`

Notes:
- Like cancel, but more forceful.
- Usage:
- > forcecancel

### `gc`

- Python method: `gc`
- Aliases: none
- Domain: `info`
- Source: `GcCommand.java`
- Summary: Call System.gc()

Usage:
- `> gc`

Notes:
- Calls System.gc().
- Usage:
- > gc

### `goal`

- Python method: `goal`
- Aliases: none
- Domain: `navigation`
- Source: `GoalCommand.java`
- Summary: Set or clear the goal

Usage:
- `> goal - Set the goal to your current position`
- `> goal <reset/clear/none> - Erase the goal`
- `> goal <y> - Set the goal to a Y level`
- `> goal <x> <z> - Set the goal to an X,Z position`
- `> goal <x> <y> <z> - Set the goal to an X,Y,Z position`

Notes:
- The goal command allows you to set or clear Baritone's goal.
- Wherever a coordinate is expected, you can use ~ just like in regular Minecraft commands. Or, you can just use regular numbers.
- Usage:
- > goal - Set the goal to your current position
- > goal <reset/clear/none> - Erase the goal
- > goal <y> - Set the goal to a Y level
- > goal <x> <z> - Set the goal to an X,Z position
- > goal <x> <y> <z> - Set the goal to an X,Y,Z position

### `goto`

- Python method: `goto`
- Aliases: none
- Domain: `navigation`
- Source: `GotoCommand.java`
- Summary: Go to a coordinate or block

Usage:
- `> goto <block> - Go to a block, wherever it is in the world`
- `> goto <y> - Go to a Y level`
- `> goto <x> <z> - Go to an X,Z position`
- `> goto <x> <y> <z> - Go to an X,Y,Z position`

Notes:
- The goto command tells Baritone to head towards a given goal or block.
- Wherever a coordinate is expected, you can use ~ just like in regular Minecraft commands. Or, you can just use regular numbers.
- Usage:
- > goto <block> - Go to a block, wherever it is in the world
- > goto <y> - Go to a Y level
- > goto <x> <z> - Go to an X,Z position
- > goto <x> <y> <z> - Go to an X,Y,Z position

### `help`

- Python method: `help`
- Aliases: ?
- Domain: `info`
- Source: `HelpCommand.java`
- Summary: View all commands or help on specific ones

Usage:
- `> help - Lists all commands and their short descriptions.`
- `> help <command> - Displays help information on a specific command.`

Notes:
- Using this command, you can view detailed help information on how to use certain commands of Baritone.
- Usage:
- > help - Lists all commands and their short descriptions.
- > help <command> - Displays help information on a specific command.

### `home`

- Python method: `home`
- Aliases: none
- Domain: `waypoints`
- Source: `DefaultCommands.java (CommandAlias)`
- Target: `waypoints goto home`
- Summary: Path to your home waypoint

Notes:
- This command is an alias for: waypoints goto home

### `invert`

- Python method: `invert`
- Aliases: none
- Domain: `navigation`
- Source: `InvertCommand.java`
- Summary: Run away from the current goal

Usage:
- `> invert - Invert the current goal.`

Notes:
- The invert command tells Baritone to head away from the current goal rather than towards it.
- Usage:
- > invert - Invert the current goal.

### `litematica`

- Python method: `litematica`
- Aliases: none
- Domain: `build`
- Source: `LitematicaCommand.java`
- Summary: Builds the loaded schematic

Usage:
- `> litematica`
- `> litematica <#>`

Notes:
- Build a schematic currently open in Litematica.
- Usage:
- > litematica
- > litematica <#>

### `mine`

- Python method: `mine`
- Aliases: none
- Domain: `world`
- Source: `MineCommand.java`
- Summary: Mine some blocks

Usage:
- `> mine diamond_ore - Mines all diamonds it can find.`

Notes:
- The mine command allows you to tell Baritone to search for and mine individual blocks.
- The specified blocks can be ores, or any other block.
- Also see the legitMine settings (see #set l legitMine).
- Usage:
- > mine diamond_ore - Mines all diamonds it can find.

### `modified`

- Python method: `modified`
- Aliases: mod, baritone, modifiedsettings
- Domain: `control`
- Source: `DefaultCommands.java (CommandAlias)`
- Target: `set modified`
- Summary: List modified settings

Notes:
- This command is an alias for: set modified

### `path`

- Python method: `path`
- Aliases: none
- Domain: `navigation`
- Source: `PathCommand.java`
- Summary: Start heading towards the goal

Usage:
- `> path - Start the pathing.`

Notes:
- The path command tells Baritone to head towards the current goal.
- Usage:
- > path - Start the pathing.

### `pause`

- Python method: `pause`
- Aliases: p, paws
- Domain: `control`
- Source: `ExecutionControlCommands.java`
- Summary: Pauses Baritone until you use resume

Usage:
- `> pause`

Notes:
- The pause command tells Baritone to temporarily stop whatever it's doing.
- This can be used to pause pathing, building, following, whatever. A single use of the resume command will start it right back up again!
- Usage:
- > pause

### `paused`

- Python method: `paused`
- Aliases: none
- Domain: `control`
- Source: `ExecutionControlCommands.java`
- Summary: Tells you if Baritone is paused

Usage:
- `> paused`

Notes:
- The paused command tells you if Baritone is currently paused by use of the pause command.
- Usage:
- > paused

### `pickup`

- Python method: `pickup`
- Aliases: none
- Domain: `world`
- Source: `PickupCommand.java`
- Summary: Pickup items

Usage:
- `> pickup - Pickup anything`
- `> pickup <item1> <item2> <...> - Pickup certain items`

Notes:
- Usage:
- > pickup - Pickup anything
- > pickup <item1> <item2> <...> - Pickup certain items

### `proc`

- Python method: `proc`
- Aliases: none
- Domain: `info`
- Source: `ProcCommand.java`
- Summary: View process state information

Usage:
- `> proc - View process information, if present`

Notes:
- The proc command provides miscellaneous information about the process currently controlling Baritone.
- You are not expected to understand this if you aren't familiar with how Baritone works.
- Usage:
- > proc - View process information, if present

### `reloadall`

- Python method: `reloadall`
- Aliases: none
- Domain: `info`
- Source: `ReloadAllCommand.java`
- Summary: Reloads Baritone's cache for this world

Usage:
- `> reloadall`

Notes:
- The reloadall command reloads Baritone's world cache.
- Usage:
- > reloadall

### `render`

- Python method: `render`
- Aliases: none
- Domain: `info`
- Source: `RenderCommand.java`
- Summary: Fix glitched chunks

Usage:
- `> render`

Notes:
- The render command fixes glitched chunk rendering without having to reload all of them.
- Usage:
- > render

### `repack`

- Python method: `repack`
- Aliases: rescan
- Domain: `info`
- Source: `RepackCommand.java`
- Summary: Re-cache chunks

Usage:
- `> repack - Repack chunks.`

Notes:
- Repack chunks around you. This basically re-caches them.
- Usage:
- > repack - Repack chunks.

### `reset`

- Python method: `reset`
- Aliases: none
- Domain: `control`
- Source: `DefaultCommands.java (CommandAlias)`
- Target: `set reset`
- Summary: Reset all settings or just one

Notes:
- This command is an alias for: set reset

### `resume`

- Python method: `resume`
- Aliases: r, unpause, unpaws
- Domain: `control`
- Source: `ExecutionControlCommands.java`
- Summary: Resumes Baritone after a pause

Usage:
- `> resume`

Notes:
- The resume command tells Baritone to resume whatever it was doing when you last used pause.
- Usage:
- > resume

### `saveall`

- Python method: `saveall`
- Aliases: none
- Domain: `info`
- Source: `SaveAllCommand.java`
- Summary: Saves Baritone's cache for this world

Usage:
- `> saveall`

Notes:
- The saveall command saves Baritone's world cache.
- Usage:
- > saveall

### `sel`

- Python method: `sel`
- Aliases: selection, s
- Domain: `build`
- Source: `SelCommand.java`
- Summary: WorldEdit-like commands

Usage:
- `> sel pos1/p1/1 - Set position 1 to your current position.`
- `> sel pos1/p1/1 <x> <y> <z> - Set position 1 to a relative position.`
- `> sel pos2/p2/2 - Set position 2 to your current position.`
- `> sel pos2/p2/2 <x> <y> <z> - Set position 2 to a relative position.`
- `> sel clear/c - Clear the selection.`
- `> sel undo/u - Undo the last action (setting positions, creating selections, etc.)`
- `> sel set/fill/s/f [block] - Completely fill all selections with a block.`
- `> sel walls/w [block] - Fill in the walls of the selection with a specified block.`
- `> sel shell/shl [block] - The same as walls, but fills in a ceiling and floor too.`
- `> sel sphere/sph [block] - Fills the selection with a sphere bounded by the sides.`
- `> sel hsphere/hsph [block] - The same as sphere, but hollow.`
- `> sel cylinder/cyl [block] <axis> - Fills the selection with a cylinder bounded by the sides, oriented about the given axis. (default=y)`
- `> sel hcylinder/hcyl [block] <axis> - The same as cylinder, but hollow.`
- `> sel cleararea/ca - Basically 'set air'.`
- `> sel replace/r <blocks...> <with> - Replaces blocks with another block.`
- `> sel copy/cp <x> <y> <z> - Copy the selected area relative to the specified or your position.`
- `> sel paste/p <x> <y> <z> - Build the copied area relative to the specified or your position.`
- `> sel expand <target> <direction> <blocks> - Expand the targets.`
- `> sel contract <target> <direction> <blocks> - Contract the targets.`
- `> sel shift <target> <direction> <blocks> - Shift the targets (does not resize).`

Notes:
- The sel command allows you to manipulate Baritone's selections, similarly to WorldEdit.
- Using these selections, you can clear areas, fill them with blocks, or something else.
- The expand/contract/shift commands use a kind of selector to choose which selections to target. Supported ones are a/all, n/newest, and o/oldest.
- Usage:
- > sel pos1/p1/1 - Set position 1 to your current position.
- > sel pos1/p1/1 <x> <y> <z> - Set position 1 to a relative position.
- > sel pos2/p2/2 - Set position 2 to your current position.
- > sel pos2/p2/2 <x> <y> <z> - Set position 2 to a relative position.
- > sel clear/c - Clear the selection.
- > sel undo/u - Undo the last action (setting positions, creating selections, etc.)
- > sel set/fill/s/f [block] - Completely fill all selections with a block.
- > sel walls/w [block] - Fill in the walls of the selection with a specified block.
- > sel shell/shl [block] - The same as walls, but fills in a ceiling and floor too.
- > sel sphere/sph [block] - Fills the selection with a sphere bounded by the sides.
- > sel hsphere/hsph [block] - The same as sphere, but hollow.
- > sel cylinder/cyl [block] <axis> - Fills the selection with a cylinder bounded by the sides, oriented about the given axis. (default=y)
- > sel hcylinder/hcyl [block] <axis> - The same as cylinder, but hollow.
- > sel cleararea/ca - Basically 'set air'.
- > sel replace/r <blocks...> <with> - Replaces blocks with another block.
- > sel copy/cp <x> <y> <z> - Copy the selected area relative to the specified or your position.
- > sel paste/p <x> <y> <z> - Build the copied area relative to the specified or your position.
- > sel expand <target> <direction> <blocks> - Expand the targets.
- > sel contract <target> <direction> <blocks> - Contract the targets.
- > sel shift <target> <direction> <blocks> - Shift the targets (does not resize).

### `set`

- Python method: `set`
- Aliases: setting, settings
- Domain: `control`
- Source: `SetCommand.java`
- Summary: View or change settings

Usage:
- `> set - Same as `set list``
- `> set list [page] - View all settings`
- `> set modified [page] - View modified settings`
- `> set <setting> - View the current value of a setting`
- `> set <setting> <value> - Set the value of a setting`
- `> set reset all - Reset ALL SETTINGS to their defaults`
- `> set reset <setting> - Reset a setting to its default`
- `> set toggle <setting> - Toggle a boolean setting`
- `> set save - Save all settings (this is automatic tho)`
- `> set load - Load settings from settings.txt`
- `> set load [filename] - Load settings from another file in your minecraft/baritone`

Notes:
- Using the set command, you can manage all of Baritone's settings. Almost every aspect is controlled by these settings - go wild!
- Usage:
- > set - Same as `set list`
- > set list [page] - View all settings
- > set modified [page] - View modified settings
- > set <setting> - View the current value of a setting
- > set <setting> <value> - Set the value of a setting
- > set reset all - Reset ALL SETTINGS to their defaults
- > set reset <setting> - Reset a setting to its default
- > set toggle <setting> - Toggle a boolean setting
- > set save - Save all settings (this is automatic tho)
- > set load - Load settings from settings.txt
- > set load [filename] - Load settings from another file in your minecraft/baritone

### `sethome`

- Python method: `sethome`
- Aliases: none
- Domain: `waypoints`
- Source: `DefaultCommands.java (CommandAlias)`
- Target: `waypoints save home`
- Summary: Sets your home waypoint

Notes:
- This command is an alias for: waypoints save home

### `surface`

- Python method: `surface`
- Aliases: top
- Domain: `navigation`
- Source: `SurfaceCommand.java`
- Summary: Used to get out of caves, mines, ...

Usage:
- `> surface - Used to get out of caves, mines, ...`
- `> top - Used to get out of caves, mines, ...`

Notes:
- The surface/top command tells Baritone to head towards the closest surface-like area.
- This can be the surface or the highest available air space, depending on circumstances.
- Usage:
- > surface - Used to get out of caves, mines, ...
- > top - Used to get out of caves, mines, ...

### `thisway`

- Python method: `thisway`
- Aliases: forward
- Domain: `navigation`
- Source: `ThisWayCommand.java`
- Summary: Travel in your current direction

Usage:
- `> thisway <distance> - makes a GoalXZ distance blocks in front of you`

Notes:
- Creates a GoalXZ some amount of blocks in the direction you're currently looking
- Usage:
- > thisway <distance> - makes a GoalXZ distance blocks in front of you

### `tunnel`

- Python method: `tunnel`
- Aliases: none
- Domain: `navigation`
- Source: `TunnelCommand.java`
- Summary: Set a goal to tunnel in your current direction

Usage:
- `> tunnel - No arguments, mines in a 1x2 radius.`
- `> tunnel <height> <width> <depth> - Tunnels in a user defined height, width and depth.`

Notes:
- The tunnel command sets a goal that tells Baritone to mine completely straight in the direction that you're facing.
- Usage:
- > tunnel - No arguments, mines in a 1x2 radius.
- > tunnel <height> <width> <depth> - Tunnels in a user defined height, width and depth.

### `version`

- Python method: `version`
- Aliases: none
- Domain: `info`
- Source: `VersionCommand.java`
- Summary: View the Baritone version

Usage:
- `> version - View version information, if present`

Notes:
- The version command prints the version of Baritone you're currently running.
- Usage:
- > version - View version information, if present

### `waypoints`

- Python method: `waypoints`
- Aliases: waypoint, wp
- Domain: `waypoints`
- Source: `WaypointsCommand.java`
- Summary: Manage waypoints

Usage:
- `> wp [l/list] - List all waypoints.`
- `> wp <l/list> <tag> - List all waypoints by tag.`
- `> wp <s/save> - Save an unnamed USER waypoint at your current position`
- `> wp <s/save> [tag] [name] [pos] - Save a waypoint with the specified tag, name and position.`
- `> wp <i/info/show> <tag/name> - Show info on a waypoint by tag or name.`
- `> wp <d/delete> <tag/name> - Delete a waypoint by tag or name.`
- `> wp <restore> <n> - Restore the last n deleted waypoints.`
- `> wp <c/clear> <tag> - Delete all waypoints with the specified tag.`
- `> wp <g/goal> <tag/name> - Set a goal to a waypoint by tag or name.`
- `> wp <goto> <tag/name> - Set a goal to a waypoint by tag or name and start pathing.`

Notes:
- The waypoint command allows you to manage Baritone's waypoints.
- Waypoints can be used to mark positions for later. Waypoints are each given a tag and an optional name.
- Note that the info, delete, and goal commands let you specify a waypoint by tag. If there is more than one waypoint with a certain tag, then they will let you select which waypoint you mean.
- Missing arguments for the save command use the USER tag, creating an unnamed waypoint and your current position as defaults.
- Usage:
- > wp [l/list] - List all waypoints.
- > wp <l/list> <tag> - List all waypoints by tag.
- > wp <s/save> - Save an unnamed USER waypoint at your current position
- > wp <s/save> [tag] [name] [pos] - Save a waypoint with the specified tag, name and position.
- > wp <i/info/show> <tag/name> - Show info on a waypoint by tag or name.
- > wp <d/delete> <tag/name> - Delete a waypoint by tag or name.
- > wp <restore> <n> - Restore the last n deleted waypoints.
- > wp <c/clear> <tag> - Delete all waypoints with the specified tag.
- > wp <g/goal> <tag/name> - Set a goal to a waypoint by tag or name.
- > wp <goto> <tag/name> - Set a goal to a waypoint by tag or name and start pathing.

## Alias Methods

- `qmark` -> `help` (`?` -> `help`)
- `baritone` -> `modified` (`baritone` -> `modified`)
- `c` -> `cancel` (`c` -> `cancel`)
- `forward` -> `thisway` (`forward` -> `thisway`)
- `highway` -> `axis` (`highway` -> `axis`)
- `mod` -> `modified` (`mod` -> `modified`)
- `modifiedsettings` -> `modified` (`modifiedsettings` -> `modified`)
- `p` -> `pause` (`p` -> `pause`)
- `paws` -> `pause` (`paws` -> `pause`)
- `r` -> `resume` (`r` -> `resume`)
- `rescan` -> `repack` (`rescan` -> `repack`)
- `s` -> `sel` (`s` -> `sel`)
- `selection` -> `sel` (`selection` -> `sel`)
- `setting` -> `set` (`setting` -> `set`)
- `settings` -> `set` (`settings` -> `set`)
- `stop` -> `cancel` (`stop` -> `cancel`)
- `top` -> `surface` (`top` -> `surface`)
- `unpause` -> `resume` (`unpause` -> `resume`)
- `unpaws` -> `resume` (`unpaws` -> `resume`)
- `waypoint` -> `waypoints` (`waypoint` -> `waypoints`)
- `wp` -> `waypoints` (`wp` -> `waypoints`)
