from __future__ import annotations

from typing import Any

from ._core import dispatch_async
from ._types import CommandArg, CommandDispatchResult


class AsyncInfoCommands:
    async def eta(self, *args: CommandArg) -> CommandDispatchResult:
        """View the current ETA

Canonical command: `eta`
Aliases: none
Usage:
- `> eta - View ETA, if present`
Source: `ETACommand.java`"""
        return await dispatch_async(self, 'eta', *args)

    async def gc(self, *args: CommandArg) -> CommandDispatchResult:
        """Call System.gc()

Canonical command: `gc`
Aliases: none
Usage:
- `> gc`
Source: `GcCommand.java`"""
        return await dispatch_async(self, 'gc', *args)

    async def help(self, *args: CommandArg) -> CommandDispatchResult:
        """View all commands or help on specific ones

Canonical command: `help`
Aliases: ?
Usage:
- `> help - Lists all commands and their short descriptions.`
- `> help <command> - Displays help information on a specific command.`
Source: `HelpCommand.java`"""
        return await dispatch_async(self, 'help', *args)

    async def proc(self, *args: CommandArg) -> CommandDispatchResult:
        """View process state information

Canonical command: `proc`
Aliases: none
Usage:
- `> proc - View process information, if present`
Source: `ProcCommand.java`"""
        return await dispatch_async(self, 'proc', *args)

    async def reloadall(self, *args: CommandArg) -> CommandDispatchResult:
        """Reloads Baritone's cache for this world

Canonical command: `reloadall`
Aliases: none
Usage:
- `> reloadall`
Source: `ReloadAllCommand.java`"""
        return await dispatch_async(self, 'reloadall', *args)

    async def render(self, *args: CommandArg) -> CommandDispatchResult:
        """Fix glitched chunks

Canonical command: `render`
Aliases: none
Usage:
- `> render`
Source: `RenderCommand.java`"""
        return await dispatch_async(self, 'render', *args)

    async def repack(self, *args: CommandArg) -> CommandDispatchResult:
        """Re-cache chunks

Canonical command: `repack`
Aliases: rescan
Usage:
- `> repack - Repack chunks.`
Source: `RepackCommand.java`"""
        return await dispatch_async(self, 'repack', *args)

    async def saveall(self, *args: CommandArg) -> CommandDispatchResult:
        """Saves Baritone's cache for this world

Canonical command: `saveall`
Aliases: none
Usage:
- `> saveall`
Source: `SaveAllCommand.java`"""
        return await dispatch_async(self, 'saveall', *args)

    async def version(self, *args: CommandArg) -> CommandDispatchResult:
        """View the Baritone version

Canonical command: `version`
Aliases: none
Usage:
- `> version - View version information, if present`
Source: `VersionCommand.java`"""
        return await dispatch_async(self, 'version', *args)

    async def qmark(self, *args: CommandArg) -> CommandDispatchResult:
        """Alias for `help`."""
        return await self.help(*args)

    async def rescan(self, *args: CommandArg) -> CommandDispatchResult:
        """Alias for `repack`."""
        return await self.repack(*args)
