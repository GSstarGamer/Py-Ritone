from __future__ import annotations

from typing import Any

from ._core import dispatch_and_wait_async, dispatch_async
from ._types import CommandArg, CommandDispatchResult


class AsyncNavigationCommands:
    async def axis(self, *args: CommandArg) -> CommandDispatchResult:
        """Set a goal to the axes

Canonical command: `axis`
Aliases: highway
Usage:
- `> axis`
Source: `AxisCommand.java`"""
        return await dispatch_async(self, 'axis', *args)

    async def blacklist(self, *args: CommandArg) -> CommandDispatchResult:
        """Blacklist closest block

Canonical command: `blacklist`
Aliases: none
Usage:
- `> blacklist`
Source: `BlacklistCommand.java`"""
        return await dispatch_async(self, 'blacklist', *args)

    async def come(self, *args: CommandArg) -> CommandDispatchResult:
        """Start heading towards your camera

Canonical command: `come`
Aliases: none
Usage:
- `> come`
Source: `ComeCommand.java`"""
        return await dispatch_async(self, 'come', *args)

    async def elytra(self, *args: CommandArg) -> CommandDispatchResult:
        """elytra time

Canonical command: `elytra`
Aliases: none
Usage:
- `> elytra - fly to the current goal`
- `> elytra reset - Resets the state of the process, but will try to keep flying to the same goal.`
- `> elytra repack - Queues all of the chunks in render distance to be given to the native library.`
- `> elytra supported - Tells you if baritone ships a native library that is compatible with your PC.`
Source: `ElytraCommand.java`"""
        return await dispatch_async(self, 'elytra', *args)

    async def explore(self, *args: CommandArg) -> CommandDispatchResult:
        """Explore things

Canonical command: `explore`
Aliases: none
Usage:
- `> explore - Explore from your current position.`
- `> explore <x> <z> - Explore from the specified X and Z position.`
Source: `ExploreCommand.java`"""
        return await dispatch_async(self, 'explore', *args)

    async def explorefilter(self, *args: CommandArg) -> CommandDispatchResult:
        """Explore chunks from a json

Canonical command: `explorefilter`
Aliases: none
Usage:
- `> explorefilter <path> [invert] - Load the JSON file referenced by the specified path. If invert is specified, it must be the literal word 'invert'.`
Source: `ExploreFilterCommand.java`"""
        return await dispatch_async(self, 'explorefilter', *args)

    async def goal(self, *args: CommandArg) -> CommandDispatchResult:
        """Set or clear the goal

Canonical command: `goal`
Aliases: none
Usage:
- `> goal - Set the goal to your current position`
- `> goal <reset/clear/none> - Erase the goal`
- `> goal <y> - Set the goal to a Y level`
- `> goal <x> <z> - Set the goal to an X,Z position`
- `> goal <x> <y> <z> - Set the goal to an X,Y,Z position`
Source: `GoalCommand.java`"""
        return await dispatch_async(self, 'goal', *args)

    async def goto(self, x: int, y: int, z: int, *extra_args: CommandArg) -> CommandDispatchResult:
        """Go to a coordinate or block

Canonical command: `goto`
Aliases: none
Usage:
- `> goto <block> - Go to a block, wherever it is in the world`
- `> goto <y> - Go to a Y level`
- `> goto <x> <z> - Go to an X,Z position`
- `> goto <x> <y> <z> - Go to an X,Y,Z position`
Source: `GotoCommand.java`"""
        return await dispatch_async(self, 'goto', x, y, z, *extra_args)

    async def goto_wait(self, x: int, y: int, z: int, *extra_args: CommandArg) -> dict[str, Any]:
        """Dispatch `goto` and wait for its terminal task event."""
        return await dispatch_and_wait_async(self, 'goto', x, y, z, *extra_args)

    async def invert(self, *args: CommandArg) -> CommandDispatchResult:
        """Run away from the current goal

Canonical command: `invert`
Aliases: none
Usage:
- `> invert - Invert the current goal.`
Source: `InvertCommand.java`"""
        return await dispatch_async(self, 'invert', *args)

    async def path(self, *args: CommandArg) -> CommandDispatchResult:
        """Start heading towards the goal

Canonical command: `path`
Aliases: none
Usage:
- `> path - Start the pathing.`
Source: `PathCommand.java`"""
        return await dispatch_async(self, 'path', *args)

    async def surface(self, *args: CommandArg) -> CommandDispatchResult:
        """Used to get out of caves, mines, ...

Canonical command: `surface`
Aliases: top
Usage:
- `> surface - Used to get out of caves, mines, ...`
- `> top - Used to get out of caves, mines, ...`
Source: `SurfaceCommand.java`"""
        return await dispatch_async(self, 'surface', *args)

    async def thisway(self, *args: CommandArg) -> CommandDispatchResult:
        """Travel in your current direction

Canonical command: `thisway`
Aliases: forward
Usage:
- `> thisway <distance> - makes a GoalXZ distance blocks in front of you`
Source: `ThisWayCommand.java`"""
        return await dispatch_async(self, 'thisway', *args)

    async def tunnel(self, *args: CommandArg) -> CommandDispatchResult:
        """Set a goal to tunnel in your current direction

Canonical command: `tunnel`
Aliases: none
Usage:
- `> tunnel - No arguments, mines in a 1x2 radius.`
- `> tunnel <height> <width> <depth> - Tunnels in a user defined height, width and depth.`
Source: `TunnelCommand.java`"""
        return await dispatch_async(self, 'tunnel', *args)

    async def forward(self, *args: CommandArg) -> CommandDispatchResult:
        """Alias for `thisway`."""
        return await self.thisway(*args)

    async def highway(self, *args: CommandArg) -> CommandDispatchResult:
        """Alias for `axis`."""
        return await self.axis(*args)

    async def top(self, *args: CommandArg) -> CommandDispatchResult:
        """Alias for `surface`."""
        return await self.surface(*args)
