from __future__ import annotations

from typing import Any

from ._core import dispatch_sync
from ._types import CommandArg, CommandDispatchResult


class SyncInfoCommands:
    def eta(self, *args: CommandArg) -> CommandDispatchResult:
        """View the current ETA

Canonical command: `eta`
Aliases: none
Usage:
- `> eta - View ETA, if present`
Source: `ETACommand.java`"""
        return dispatch_sync(self, 'eta', *args)

    def gc(self, *args: CommandArg) -> CommandDispatchResult:
        """Call System.gc()

Canonical command: `gc`
Aliases: none
Usage:
- `> gc`
Source: `GcCommand.java`"""
        return dispatch_sync(self, 'gc', *args)

    def help(self, *args: CommandArg) -> CommandDispatchResult:
        """View all commands or help on specific ones

Canonical command: `help`
Aliases: ?
Usage:
- `> help - Lists all commands and their short descriptions.`
- `> help <command> - Displays help information on a specific command.`
Source: `HelpCommand.java`"""
        return dispatch_sync(self, 'help', *args)

    def proc(self, *args: CommandArg) -> CommandDispatchResult:
        """View process state information

Canonical command: `proc`
Aliases: none
Usage:
- `> proc - View process information, if present`
Source: `ProcCommand.java`"""
        return dispatch_sync(self, 'proc', *args)

    def reloadall(self, *args: CommandArg) -> CommandDispatchResult:
        """Reloads Baritone's cache for this world

Canonical command: `reloadall`
Aliases: none
Usage:
- `> reloadall`
Source: `ReloadAllCommand.java`"""
        return dispatch_sync(self, 'reloadall', *args)

    def render(self, *args: CommandArg) -> CommandDispatchResult:
        """Fix glitched chunks

Canonical command: `render`
Aliases: none
Usage:
- `> render`
Source: `RenderCommand.java`"""
        return dispatch_sync(self, 'render', *args)

    def repack(self, *args: CommandArg) -> CommandDispatchResult:
        """Re-cache chunks

Canonical command: `repack`
Aliases: rescan
Usage:
- `> repack - Repack chunks.`
Source: `RepackCommand.java`"""
        return dispatch_sync(self, 'repack', *args)

    def saveall(self, *args: CommandArg) -> CommandDispatchResult:
        """Saves Baritone's cache for this world

Canonical command: `saveall`
Aliases: none
Usage:
- `> saveall`
Source: `SaveAllCommand.java`"""
        return dispatch_sync(self, 'saveall', *args)

    def version(self, *args: CommandArg) -> CommandDispatchResult:
        """View the Baritone version

Canonical command: `version`
Aliases: none
Usage:
- `> version - View version information, if present`
Source: `VersionCommand.java`"""
        return dispatch_sync(self, 'version', *args)

    def qmark(self, *args: CommandArg) -> CommandDispatchResult:
        """Alias for `help`."""
        return self.help(*args)

    def rescan(self, *args: CommandArg) -> CommandDispatchResult:
        """Alias for `repack`."""
        return self.repack(*args)
