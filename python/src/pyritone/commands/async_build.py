from __future__ import annotations

from typing import Any

from ._core import dispatch_async
from ._types import CommandArg, CommandDispatchResult


class AsyncBuildCommands:
    async def build(self, *args: CommandArg) -> CommandDispatchResult:
        """Build a schematic

Canonical command: `build`
Aliases: none
Usage:
- `> build <filename> - Loads and builds '<filename>.schematic'`
- `> build <filename> <x> <y> <z> - Custom position`
Source: `BuildCommand.java`"""
        return await dispatch_async(self, 'build', *args)

    async def litematica(self, *args: CommandArg) -> CommandDispatchResult:
        """Builds the loaded schematic

Canonical command: `litematica`
Aliases: none
Usage:
- `> litematica`
- `> litematica <#>`
Source: `LitematicaCommand.java`"""
        return await dispatch_async(self, 'litematica', *args)

    async def sel(self, *args: CommandArg) -> CommandDispatchResult:
        """WorldEdit-like commands

Canonical command: `sel`
Aliases: selection, s
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
Source: `SelCommand.java`"""
        return await dispatch_async(self, 'sel', *args)

    async def s(self, *args: CommandArg) -> CommandDispatchResult:
        """Alias for `sel`."""
        return await self.sel(*args)

    async def selection(self, *args: CommandArg) -> CommandDispatchResult:
        """Alias for `sel`."""
        return await self.sel(*args)
