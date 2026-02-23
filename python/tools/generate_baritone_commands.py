from __future__ import annotations

import argparse
import ast
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from urllib.request import urlopen

BARITONE_VERSION = "v1.15.0"
BARITONE_BASE_RAW_URL = f"https://raw.githubusercontent.com/cabaletta/baritone/{BARITONE_VERSION}/src/main/java/baritone/command/defaults"

DEFAULT_COMMANDS_URL = f"{BARITONE_BASE_RAW_URL}/DefaultCommands.java"
EXECUTION_CONTROL_URL = f"{BARITONE_BASE_RAW_URL}/ExecutionControlCommands.java"

ROOT = Path(__file__).resolve().parents[1]
COMMANDS_DIR = ROOT / "src" / "pyritone" / "commands"
DOCS_RAW_REFERENCE_PATH = ROOT / "docs" / "baritone-commands.md"
DOCS_COMMANDS_DIR = ROOT / "docs" / "commands"
DOCS_ALIASES_PATH = DOCS_COMMANDS_DIR / "aliases.md"

DOMAIN_BY_COMMAND = {
    "axis": "navigation",
    "blacklist": "navigation",
    "build": "build",
    "cancel": "control",
    "click": "world",
    "come": "navigation",
    "elytra": "navigation",
    "eta": "info",
    "explore": "navigation",
    "explorefilter": "navigation",
    "farm": "world",
    "find": "world",
    "follow": "world",
    "forcecancel": "control",
    "gc": "info",
    "goal": "navigation",
    "goto": "navigation",
    "help": "info",
    "home": "waypoints",
    "invert": "navigation",
    "litematica": "build",
    "mine": "world",
    "modified": "control",
    "path": "navigation",
    "pause": "control",
    "paused": "control",
    "pickup": "world",
    "proc": "info",
    "reloadall": "info",
    "render": "info",
    "repack": "info",
    "reset": "control",
    "resume": "control",
    "saveall": "info",
    "sel": "build",
    "set": "control",
    "sethome": "waypoints",
    "surface": "navigation",
    "thisway": "navigation",
    "tunnel": "navigation",
    "version": "info",
    "waypoints": "waypoints",
}

PYTHON_NAME_OVERRIDES = {
    "?": "qmark",
}

SPECIAL_CANONICAL_CALLS = {
    "modified": ("set", ["modified"]),
    "reset": ("set", ["reset"]),
    "sethome": ("waypoints", ["save", "home"]),
    "home": ("waypoints", ["goto", "home"]),
}

DOMAIN_MODULES = [
    "navigation",
    "world",
    "build",
    "control",
    "info",
    "waypoints",
]

DOMAIN_TITLES = {
    "navigation": "Navigation",
    "world": "World",
    "build": "Build",
    "control": "Control",
    "info": "Info",
    "waypoints": "Waypoints",
}

DOMAIN_DESCRIPTIONS = {
    "navigation": "Movement, path goals, and travel flow control.",
    "world": "Block/entity interaction commands such as mine, follow, and pickup.",
    "build": "Schematic and selection operations.",
    "control": "Execution-state and settings-related commands.",
    "info": "Read-only status and cache/diagnostic commands.",
    "waypoints": "Waypoint save/list/goto helpers and aliases.",
}

TASK_LIKELY_DOMAINS = {"navigation", "world", "build", "waypoints"}


@dataclass(frozen=True, slots=True)
class ParsedCommand:
    name: str
    aliases: tuple[str, ...]
    short_desc: str
    long_desc_lines: tuple[str, ...]
    usage_lines: tuple[str, ...]
    source_file: str
    domain: str
    target: str | None = None


@dataclass(frozen=True, slots=True)
class CommandExampleSpec:
    sync_call: str
    async_call: str
    notes: tuple[str, ...] = ()


COMMAND_EXAMPLES: dict[str, CommandExampleSpec] = {
    "axis": CommandExampleSpec("dispatch = client.axis()", "dispatch = await client.axis()"),
    "blacklist": CommandExampleSpec("dispatch = client.blacklist()", "dispatch = await client.blacklist()"),
    "build": CommandExampleSpec(
        "dispatch = client.build(\"starter_house\")",
        "dispatch = await client.build(\"starter_house\")",
        (
            "For local Python-file-relative schematic paths, use `build_file(...)`.",
            "Use `build_file_wait(...)` when you want dispatch + wait in one call.",
        ),
    ),
    "cancel": CommandExampleSpec(
        "result = client.cancel()",
        "result = await client.cancel()",
        (
            "This method uses the bridge `task.cancel` endpoint, not `baritone.execute \"cancel\"`.",
            "Pass `task_id` if you want to cancel a specific known task.",
        ),
    ),
    "click": CommandExampleSpec("dispatch = client.click()", "dispatch = await client.click()"),
    "come": CommandExampleSpec("dispatch = client.come()", "dispatch = await client.come()"),
    "elytra": CommandExampleSpec("dispatch = client.elytra()", "dispatch = await client.elytra()"),
    "eta": CommandExampleSpec("dispatch = client.eta()", "dispatch = await client.eta()"),
    "explore": CommandExampleSpec("dispatch = client.explore()", "dispatch = await client.explore()"),
    "explorefilter": CommandExampleSpec(
        "dispatch = client.explorefilter(\"explore-filter.json\")",
        "dispatch = await client.explorefilter(\"explore-filter.json\")",
        ("Use a valid JSON file path for the filter input.",),
    ),
    "farm": CommandExampleSpec("dispatch = client.farm(64)", "dispatch = await client.farm(64)"),
    "find": CommandExampleSpec("dispatch = client.find(\"diamond_ore\")", "dispatch = await client.find(\"diamond_ore\")"),
    "follow": CommandExampleSpec("dispatch = client.follow(\"players\")", "dispatch = await client.follow(\"players\")"),
    "forcecancel": CommandExampleSpec("dispatch = client.forcecancel()", "dispatch = await client.forcecancel()"),
    "gc": CommandExampleSpec("dispatch = client.gc()", "dispatch = await client.gc()"),
    "goal": CommandExampleSpec("dispatch = client.goal(100, 70, 100)", "dispatch = await client.goal(100, 70, 100)"),
    "goto": CommandExampleSpec(
        "dispatch = client.goto(100, 70, 100)",
        "dispatch = await client.goto(100, 70, 100)",
        ("Use `wait_for_task` (or `goto_wait`) if you need terminal completion state.",),
    ),
    "help": CommandExampleSpec("dispatch = client.help(\"goto\")", "dispatch = await client.help(\"goto\")"),
    "home": CommandExampleSpec(
        "dispatch = client.home()",
        "dispatch = await client.home()",
        ("`home()` is an alias wrapper for `waypoints goto home`.",),
    ),
    "invert": CommandExampleSpec("dispatch = client.invert()", "dispatch = await client.invert()"),
    "litematica": CommandExampleSpec("dispatch = client.litematica()", "dispatch = await client.litematica()"),
    "mine": CommandExampleSpec("dispatch = client.mine(\"diamond_ore\")", "dispatch = await client.mine(\"diamond_ore\")"),
    "modified": CommandExampleSpec(
        "dispatch = client.modified()",
        "dispatch = await client.modified()",
        ("`modified()` routes to `set modified` internally.",),
    ),
    "path": CommandExampleSpec("dispatch = client.path()", "dispatch = await client.path()"),
    "pause": CommandExampleSpec("dispatch = client.pause()", "dispatch = await client.pause()"),
    "paused": CommandExampleSpec("dispatch = client.paused()", "dispatch = await client.paused()"),
    "pickup": CommandExampleSpec("dispatch = client.pickup(\"diamond\")", "dispatch = await client.pickup(\"diamond\")"),
    "proc": CommandExampleSpec("dispatch = client.proc()", "dispatch = await client.proc()"),
    "reloadall": CommandExampleSpec("dispatch = client.reloadall()", "dispatch = await client.reloadall()"),
    "render": CommandExampleSpec("dispatch = client.render()", "dispatch = await client.render()"),
    "repack": CommandExampleSpec("dispatch = client.repack()", "dispatch = await client.repack()"),
    "reset": CommandExampleSpec(
        "dispatch = client.reset(\"allowPlace\")",
        "dispatch = await client.reset(\"allowPlace\")",
        ("`reset()` routes to `set reset ...` internally.",),
    ),
    "resume": CommandExampleSpec("dispatch = client.resume()", "dispatch = await client.resume()"),
    "saveall": CommandExampleSpec("dispatch = client.saveall()", "dispatch = await client.saveall()"),
    "sel": CommandExampleSpec("dispatch = client.sel(\"pos1\")", "dispatch = await client.sel(\"pos1\")"),
    "set": CommandExampleSpec(
        "dispatch = client.set(\"allowPlace\", True)",
        "dispatch = await client.set(\"allowPlace\", True)",
        (
            "For setting ergonomics, prefer `client.settings.<name>` when possible.",
            "Boolean values serialize as lowercase `true`/`false` in command text.",
        ),
    ),
    "sethome": CommandExampleSpec(
        "dispatch = client.sethome()",
        "dispatch = await client.sethome()",
        ("`sethome()` is an alias wrapper for `waypoints save home`.",),
    ),
    "surface": CommandExampleSpec("dispatch = client.surface()", "dispatch = await client.surface()"),
    "thisway": CommandExampleSpec("dispatch = client.thisway(200)", "dispatch = await client.thisway(200)"),
    "tunnel": CommandExampleSpec("dispatch = client.tunnel(2, 1, 64)", "dispatch = await client.tunnel(2, 1, 64)"),
    "version": CommandExampleSpec("dispatch = client.version()", "dispatch = await client.version()"),
    "waypoints": CommandExampleSpec("dispatch = client.waypoints(\"list\")", "dispatch = await client.waypoints(\"list\")"),
}


def fetch_text(url: str) -> str:
    with urlopen(url) as response:
        return response.read().decode("utf-8")


def parse_java_string_literal(literal: str) -> str:
    return ast.literal_eval(literal)


def extract_string_literals(text: str) -> list[str]:
    literals = re.findall(r'"(?:\\.|[^"\\])*"', text)
    return [parse_java_string_literal(literal) for literal in literals]


def split_top_level_args(text: str) -> list[str]:
    parts: list[str] = []
    current: list[str] = []
    depth = 0
    in_string = False
    escape = False

    for character in text:
        if in_string:
            current.append(character)
            if escape:
                escape = False
            elif character == "\\":
                escape = True
            elif character == '"':
                in_string = False
            continue

        if character == '"':
            in_string = True
            current.append(character)
            continue

        if character == "(":
            depth += 1
            current.append(character)
            continue

        if character == ")":
            depth -= 1
            current.append(character)
            continue

        if character == "," and depth == 0:
            parts.append("".join(current).strip())
            current = []
            continue

        current.append(character)

    tail = "".join(current).strip()
    if tail:
        parts.append(tail)
    return parts


def parse_short_desc(source: str) -> str:
    match = re.search(r'getShortDesc\(\)\s*\{\s*return\s+"((?:\\.|[^"\\])*)";\s*\}', source, re.S)
    if not match:
        return ""
    return parse_java_string_literal(f'"{match.group(1)}"')


def parse_long_desc_lines(source: str) -> tuple[str, ...]:
    match = re.search(r'getLongDesc\(\)\s*\{\s*return\s+Arrays\.asList\((.*?)\);\s*\}', source, re.S)
    if not match:
        return tuple()
    return tuple(extract_string_literals(match.group(1)))


def parse_usage_lines(long_desc_lines: Iterable[str]) -> tuple[str, ...]:
    return tuple(line for line in long_desc_lines if line.lstrip().startswith(">"))


def parse_command_names_from_super(source: str) -> tuple[str, ...]:
    match = re.search(r"super\(\s*baritone\s*,\s*(.*?)\);", source, re.S)
    if not match:
        raise ValueError("Could not parse command names from super(...) call")
    names = tuple(extract_string_literals(match.group(1)))
    if not names:
        raise ValueError("No command names found in super(...) call")
    return names


def parse_default_command_classes(default_source: str) -> list[str]:
    classes: list[str] = []
    for line in default_source.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("//"):
            continue
        match = re.search(r"new\s+([A-Za-z0-9_]+Command)\(baritone\)", stripped)
        if match:
            classes.append(match.group(1))
    return classes


def parse_command_alias_entries(default_source: str) -> list[ParsedCommand]:
    parsed: list[ParsedCommand] = []

    for line in default_source.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("//"):
            continue
        if "new CommandAlias(" not in stripped:
            continue

        match = re.search(r"new\s+CommandAlias\(baritone,\s*(.*)\)\s*,?$", stripped)
        if not match:
            continue

        parts = split_top_level_args(match.group(1))
        if len(parts) != 3:
            raise ValueError(f"Unexpected CommandAlias argument structure: {parts}")

        names_expression = parts[0]
        short_desc = parse_java_string_literal(parts[1])
        target = parse_java_string_literal(parts[2])

        if names_expression.startswith("Arrays.asList"):
            names = tuple(extract_string_literals(names_expression))
        else:
            names = tuple(extract_string_literals(names_expression))

        if not names:
            raise ValueError("CommandAlias did not define names")

        canonical = names[0]
        long_desc_lines = (f"This command is an alias for: {target}",)
        parsed.append(
            ParsedCommand(
                name=canonical,
                aliases=names[1:],
                short_desc=short_desc,
                long_desc_lines=long_desc_lines,
                usage_lines=tuple(),
                source_file="DefaultCommands.java (CommandAlias)",
                domain=DOMAIN_BY_COMMAND[canonical],
                target=target,
            )
        )

    return parsed


def parse_default_commands(default_source: str) -> list[ParsedCommand]:
    parsed: list[ParsedCommand] = []

    class_names = parse_default_command_classes(default_source)
    for class_name in class_names:
        source_url = f"{BARITONE_BASE_RAW_URL}/{class_name}.java"
        source = fetch_text(source_url)

        names = parse_command_names_from_super(source)
        canonical = names[0]
        if canonical == "schematica":
            continue

        if canonical not in DOMAIN_BY_COMMAND:
            raise ValueError(f"Missing domain mapping for command: {canonical}")

        long_desc_lines = parse_long_desc_lines(source)

        parsed.append(
            ParsedCommand(
                name=canonical,
                aliases=names[1:],
                short_desc=parse_short_desc(source),
                long_desc_lines=long_desc_lines,
                usage_lines=parse_usage_lines(long_desc_lines),
                source_file=f"{class_name}.java",
                domain=DOMAIN_BY_COMMAND[canonical],
                target=None,
            )
        )

    parsed.extend(parse_command_alias_entries(default_source))
    return parsed


def parse_execution_control_commands(execution_source: str) -> list[ParsedCommand]:
    parsed: list[ParsedCommand] = []
    pattern = re.compile(
        r"new\s+Command\(baritone,\s*(?P<names>.*?)\)\s*\{(?P<body>.*?)^\s*\};",
        re.S | re.M,
    )

    for match in pattern.finditer(execution_source):
        names = tuple(extract_string_literals(match.group("names")))
        if not names:
            continue

        canonical = names[0]
        if canonical not in DOMAIN_BY_COMMAND:
            raise ValueError(f"Missing domain mapping for command: {canonical}")

        body = match.group("body")
        long_desc_lines = parse_long_desc_lines(body)
        parsed.append(
            ParsedCommand(
                name=canonical,
                aliases=names[1:],
                short_desc=parse_short_desc(body),
                long_desc_lines=long_desc_lines,
                usage_lines=parse_usage_lines(long_desc_lines),
                source_file="ExecutionControlCommands.java",
                domain=DOMAIN_BY_COMMAND[canonical],
                target=None,
            )
        )

    return parsed


def python_name(name: str) -> str:
    if name in PYTHON_NAME_OVERRIDES:
        return PYTHON_NAME_OVERRIDES[name]
    safe = name.replace("-", "_")
    if safe.isidentifier():
        return safe
    raise ValueError(f"Cannot convert command name to valid Python identifier: {name}")


def build_alias_to_canonical(commands: Iterable[ParsedCommand]) -> dict[str, str]:
    alias_to_canonical: dict[str, str] = {}
    for command in commands:
        for alias in command.aliases:
            alias_to_canonical[alias] = command.name
    return dict(sorted(alias_to_canonical.items()))


def command_docstring(command: ParsedCommand) -> str:
    alias_text = ", ".join(command.aliases) if command.aliases else "none"
    lines = [
        command.short_desc or f"Baritone command: {command.name}",
        "",
        f"Canonical command: `{command.name}`",
        f"Aliases: {alias_text}",
    ]

    if command.usage_lines:
        lines.append("Usage:")
        for usage in command.usage_lines:
            lines.append(f"- `{usage}`")

    lines.append(f"Source: `{command.source_file}`")
    return "\n".join(lines)


def render_async_method(command: ParsedCommand) -> str:
    name = python_name(command.name)
    doc = command_docstring(command)

    if command.name == "cancel":
        return ""

    if command.name == "goto":
        return (
            f"    async def {name}(self, x: int, y: int, z: int, *extra_args: CommandArg) -> CommandDispatchResult:\n"
            f"        \"\"\"{doc}\"\"\"\n"
            f"        return await dispatch_async(self, {command.name!r}, x, y, z, *extra_args)\n\n"
            f"    async def goto_wait(self, x: int, y: int, z: int, *extra_args: CommandArg) -> dict[str, Any]:\n"
            "        \"\"\"Dispatch `goto` and wait for its terminal task event.\"\"\"\n"
            "        return await dispatch_and_wait_async(self, 'goto', x, y, z, *extra_args)\n"
        )

    if command.name in SPECIAL_CANONICAL_CALLS:
        target_method, target_args = SPECIAL_CANONICAL_CALLS[command.name]
        literal_args = ", ".join(repr(value) for value in target_args)
        call_prefix = f"{literal_args}, *args" if literal_args else "*args"
        return (
            f"    async def {name}(self, *args: CommandArg) -> CommandDispatchResult:\n"
            f"        \"\"\"{doc}\"\"\"\n"
            f"        return await self.{python_name(target_method)}({call_prefix})\n"
        )

    return (
        f"    async def {name}(self, *args: CommandArg) -> CommandDispatchResult:\n"
        f"        \"\"\"{doc}\"\"\"\n"
        f"        return await dispatch_async(self, {command.name!r}, *args)\n"
    )


def render_sync_method(command: ParsedCommand) -> str:
    name = python_name(command.name)
    doc = command_docstring(command)

    if command.name == "cancel":
        return ""

    if command.name == "goto":
        return (
            f"    def {name}(self, x: int, y: int, z: int, *extra_args: CommandArg) -> CommandDispatchResult:\n"
            f"        \"\"\"{doc}\"\"\"\n"
            f"        return dispatch_sync(self, {command.name!r}, x, y, z, *extra_args)\n\n"
            f"    def goto_wait(self, x: int, y: int, z: int, *extra_args: CommandArg) -> dict[str, Any]:\n"
            "        \"\"\"Dispatch `goto` and wait for its terminal task event.\"\"\"\n"
            "        return dispatch_and_wait_sync(self, 'goto', x, y, z, *extra_args)\n"
        )

    if command.name in SPECIAL_CANONICAL_CALLS:
        target_method, target_args = SPECIAL_CANONICAL_CALLS[command.name]
        literal_args = ", ".join(repr(value) for value in target_args)
        call_prefix = f"{literal_args}, *args" if literal_args else "*args"
        return (
            f"    def {name}(self, *args: CommandArg) -> CommandDispatchResult:\n"
            f"        \"\"\"{doc}\"\"\"\n"
            f"        return self.{python_name(target_method)}({call_prefix})\n"
        )

    return (
        f"    def {name}(self, *args: CommandArg) -> CommandDispatchResult:\n"
        f"        \"\"\"{doc}\"\"\"\n"
        f"        return dispatch_sync(self, {command.name!r}, *args)\n"
    )


def render_async_alias(alias: str, canonical: str) -> str:
    alias_method = python_name(alias)
    canonical_method = python_name(canonical)

    if canonical == "cancel":
        return (
            f"    async def {alias_method}(self, task_id: str | None = None) -> dict[str, Any]:\n"
            f"        \"\"\"Alias for `{canonical_method}`.\"\"\"\n"
            "        return await self.cancel(task_id=task_id)\n"
        )

    return (
        f"    async def {alias_method}(self, *args: CommandArg) -> CommandDispatchResult:\n"
        f"        \"\"\"Alias for `{canonical_method}`.\"\"\"\n"
        f"        return await self.{canonical_method}(*args)\n"
    )


def render_sync_alias(alias: str, canonical: str) -> str:
    alias_method = python_name(alias)
    canonical_method = python_name(canonical)

    if canonical == "cancel":
        return (
            f"    def {alias_method}(self, task_id: str | None = None) -> dict[str, Any]:\n"
            f"        \"\"\"Alias for `{canonical_method}`.\"\"\"\n"
            "        return self.cancel(task_id=task_id)\n"
        )

    return (
        f"    def {alias_method}(self, *args: CommandArg) -> CommandDispatchResult:\n"
        f"        \"\"\"Alias for `{canonical_method}`.\"\"\"\n"
        f"        return self.{canonical_method}(*args)\n"
    )


def generate_domain_module(commands: list[ParsedCommand], alias_map: dict[str, str], domain: str, *, async_mode: bool) -> str:
    selected_commands = sorted((command for command in commands if command.domain == domain), key=lambda item: item.name)
    selected_aliases = sorted((alias, canonical) for alias, canonical in alias_map.items() if DOMAIN_BY_COMMAND[canonical] == domain)

    class_prefix = "Async" if async_mode else "Sync"
    class_name = f"{class_prefix}{domain.capitalize()}Commands"

    needs_wait_helper = any(command.name == "goto" for command in selected_commands)

    if async_mode:
        core_import = "from ._core import dispatch_async\n"
        if needs_wait_helper:
            core_import = "from ._core import dispatch_and_wait_async, dispatch_async\n"

        header = (
            "from __future__ import annotations\n\n"
            "from typing import Any\n\n"
            + core_import
            + "from ._types import CommandArg, CommandDispatchResult\n\n\n"
        )
        method_renderer = render_async_method
        alias_renderer = render_async_alias
    else:
        core_import = "from ._core import dispatch_sync\n"
        if needs_wait_helper:
            core_import = "from ._core import dispatch_and_wait_sync, dispatch_sync\n"

        header = (
            "from __future__ import annotations\n\n"
            "from typing import Any\n\n"
            + core_import
            + "from ._types import CommandArg, CommandDispatchResult\n\n\n"
        )
        method_renderer = render_sync_method
        alias_renderer = render_sync_alias

    body = [f"class {class_name}:\n"]

    for command in selected_commands:
        rendered = method_renderer(command)
        if rendered:
            body.append(rendered + "\n")

    for alias, canonical in selected_aliases:
        body.append(alias_renderer(alias, canonical) + "\n")

    return header + "".join(body).rstrip() + "\n"


def generate_catalog_module(commands: list[ParsedCommand], alias_map: dict[str, str]) -> str:
    command_method_names = {command.name: python_name(command.name) for command in commands}
    alias_method_names = {alias: python_name(alias) for alias in alias_map}

    lines = [
        "from __future__ import annotations",
        "",
        "from ._types import CommandSpec",
        "",
        f"BARITONE_VERSION = {BARITONE_VERSION!r}",
        "",
        "COMMAND_SPECS: tuple[CommandSpec, ...] = (",
    ]

    for command in sorted(commands, key=lambda item: item.name):
        lines.extend(
            [
                "    CommandSpec(",
                f"        name={command.name!r},",
                f"        aliases={command.aliases!r},",
                f"        short_desc={command.short_desc!r},",
                f"        long_desc_lines={command.long_desc_lines!r},",
                f"        usage_lines={command.usage_lines!r},",
                f"        source_file={command.source_file!r},",
                f"        domain={command.domain!r},",
                f"        target={command.target!r},",
                "    ),",
            ]
        )

    lines.extend(
        [
            ")",
            "",
            "ALIAS_TO_CANONICAL: dict[str, str] = {",
        ]
    )
    for alias, canonical in sorted(alias_map.items()):
        lines.append(f"    {alias!r}: {canonical!r},")

    lines.extend(
        [
            "}",
            "",
            "COMMAND_NAME_SET: frozenset[str] = frozenset(spec.name for spec in COMMAND_SPECS)",
            "",
            "COMMAND_METHOD_NAMES: dict[str, str] = {",
        ]
    )
    for command_name, method_name in sorted(command_method_names.items()):
        lines.append(f"    {command_name!r}: {method_name!r},")

    lines.extend(
        [
            "}",
            "",
            "ALIAS_METHOD_NAMES: dict[str, str] = {",
        ]
    )
    for alias_name, method_name in sorted(alias_method_names.items()):
        lines.append(f"    {alias_name!r}: {method_name!r},")

    lines.extend(["}", ""])
    return "\n".join(lines)


def clean_usage_line(line: str) -> str:
    stripped = line.strip()
    if stripped.startswith(">"):
        return stripped
    return f"> {stripped}"


def first_meaningful_long_desc_line(command: ParsedCommand) -> str | None:
    for line in command.long_desc_lines:
        stripped = line.strip()
        if not stripped or stripped.startswith(">") or stripped.lower().startswith("usage"):
            continue
        return stripped
    return None


def command_method_signature(command: ParsedCommand) -> str:
    method_name = python_name(command.name)
    if command.name == "goto":
        return f"{method_name}(x: int, y: int, z: int, *extra_args: CommandArg) -> CommandDispatchResult"
    if command.name == "cancel":
        return f"{method_name}(task_id: str | None = None) -> dict[str, Any]"
    return f"{method_name}(*args: CommandArg) -> CommandDispatchResult"


def command_usage_lines(command: ParsedCommand) -> tuple[str, ...]:
    if command.usage_lines:
        return tuple(clean_usage_line(line) for line in command.usage_lines)
    if command.target:
        return (f"> {command.target}",)
    return (f"> {command.name}",)


def extract_assignment_target(statement: str) -> str | None:
    if "=" not in statement:
        return None
    target = statement.split("=", 1)[0].strip()
    if target.isidentifier():
        return target
    return None


def render_async_snippet(example: CommandExampleSpec) -> str:
    lines = [
        "import asyncio",
        "from pyritone import Client",
        "",
        "async def main() -> None:",
        "    async with Client() as client:",
        f"        {example.async_call}",
    ]
    target = extract_assignment_target(example.async_call)
    if target is not None:
        lines.append(f"        print({target})")
    lines.extend(["", "asyncio.run(main())"])
    return "\n".join(lines)


def command_return_shape_lines(command: ParsedCommand) -> tuple[str, ...]:
    if command.name == "cancel":
        return (
            "dict[str, Any]",
            "- Raw bridge payload from `task.cancel`.",
            "- May include cancellation result for active or requested task.",
        )

    return (
        "CommandDispatchResult",
        "- command_text: exact command string sent through `baritone.execute`.",
        "- raw: raw bridge response object.",
        "- task_id (optional): task identifier if the bridge returns one.",
        "- accepted (optional): acceptance flag if provided by the bridge.",
    )


def is_task_likely_command(command: ParsedCommand) -> bool:
    return command.domain in TASK_LIKELY_DOMAINS and command.name != "cancel"


def related_commands(command: ParsedCommand, domain_commands: list[ParsedCommand], *, limit: int = 4) -> tuple[ParsedCommand, ...]:
    related = [candidate for candidate in domain_commands if candidate.name != command.name]
    return tuple(sorted(related, key=lambda item: item.name)[:limit])


def render_wait_pattern_block(command: ParsedCommand) -> list[str]:
    if not is_task_likely_command(command):
        return []
    return [
        "### Wait pattern",
        "If `task_id` exists, wait for a terminal event:",
        "",
        "- `terminal = await client.wait_for_task(dispatch[\"task_id\"])`",
    ]


def render_common_mistakes(command: ParsedCommand, example: CommandExampleSpec) -> list[str]:
    lines = [
        "### Common mistakes",
        "- Passing separate string tokens when one argument contains spaces. Use one Python string.",
    ]
    if command.name != "cancel":
        lines.append("- Treating dispatch as completion. Dispatch is immediate; wait on `task_id` when needed.")
    else:
        lines.append("- Expecting `cancel()` to return `CommandDispatchResult`; it returns raw cancel payload.")

    for note in example.notes:
        lines.append(f"- {note}")
    return lines


def render_related_methods(command: ParsedCommand, domain_commands: list[ParsedCommand]) -> list[str]:
    related = related_commands(command, domain_commands)
    lines = ["### Related methods"]
    if not related:
        lines.append("- None")
        return lines
    for other in related:
        lines.append(f"- [`{python_name(other.name)}`](#{other.name})")
    lines.append("- [Alias mappings](aliases.md) for shortcut methods")
    return lines


def generate_command_card(command: ParsedCommand, domain_commands: list[ParsedCommand]) -> str:
    example = COMMAND_EXAMPLES[command.name]
    aliases_text = ", ".join(command.aliases) if command.aliases else "none"

    summary = command.short_desc.strip() or f"Run Baritone `{command.name}`."
    when_to_use = first_meaningful_long_desc_line(command) or summary

    lines = [
        f"## `{command.name}`",
        "",
        summary,
        "",
        "### When to use this",
        f"- {when_to_use}",
        "",
        "### Method signature",
        f"- `Client.{command_method_signature(command)}`",
        "",
        "### Baritone syntax",
    ]
    for usage in command_usage_lines(command):
        lines.append(f"- `{usage}`")

    lines.extend(
        [
            "",
            "### Domain and aliases",
            f"- Domain: `{command.domain}`",
            f"- Aliases: {aliases_text}",
            "",
            "### Example",
            "```python",
            render_async_snippet(example),
            "```",
            "",
            "### Return shape",
            "```text",
            *command_return_shape_lines(command),
            "```",
            "",
        ]
    )

    wait_lines = render_wait_pattern_block(command)
    if wait_lines:
        lines.extend(wait_lines)
        lines.append("")

    lines.extend(render_common_mistakes(command, example))
    lines.extend(
        [
            "",
            "### Source provenance",
            f"- Baritone version: `{BARITONE_VERSION}`",
            f"- Source file: `{command.source_file}`",
            "",
        ]
    )
    lines.extend(render_related_methods(command, domain_commands))
    lines.append("")
    return "\n".join(lines)


def generate_domain_commands_markdown(commands: list[ParsedCommand], domain: str) -> str:
    domain_commands = sorted((command for command in commands if command.domain == domain), key=lambda item: item.name)
    command_links = "\n".join(f"- [`{command.name}`](#{command.name})" for command in domain_commands)

    lines = [
        f"# {DOMAIN_TITLES[domain]} Commands",
        "",
        f"Usage-first command guide for `{DOMAIN_TITLES[domain]}` methods in `pyritone`.",
        "",
        "### When to use this",
        f"- {DOMAIN_DESCRIPTIONS[domain]}",
        f"- Generated from Baritone `{BARITONE_VERSION}` command metadata.",
        "",
        "### Commands in this page",
        command_links,
        "",
        "### Return shape",
        "```text",
        "CommandDispatchResult",
        "- command_text",
        "- raw",
        "- task_id (optional)",
        "- accepted (optional)",
        "```",
        "",
        "### Common mistakes",
        "- Assuming command dispatch means task completion. Use `wait_for_task` when `task_id` exists.",
        "- Forgetting to connect the client before calling methods.",
        "",
        "### Related methods",
        "- [Tasks, events, and waiting](../tasks-events-and-waiting.md)",
        "- [Errors and troubleshooting](../errors-and-troubleshooting.md)",
        "- [Alias methods](aliases.md)",
        "",
    ]

    if domain == "build":
        lines.extend(
            [
                "## Pyritone Build Helpers",
                "",
                "Extra helpers for local schematic files relative to your Python script.",
                "",
                "### Example",
                "```python",
                "import asyncio",
                "from pyritone import Client",
                "",
                "async def main() -> None:",
                "    async with Client() as client:",
                "        dispatch = await client.build_file(\"schematics/base\", 100, 70, 100)",
                "        print(dispatch)",
                "        terminal = await client.build_file_wait(\"schematics/base\", 100, 70, 100)",
                "        print(terminal)",
                "",
                "asyncio.run(main())",
                "```",
                "",
                "### Notes",
                "- Relative paths are resolved from the calling Python file directory by default.",
                "- Pass `base_dir` to override path base.",
                "- No extension uses probing order: `.schem`, `.schematic`, `.litematic`.",
                "- If no file matches, extension-less path is sent so Baritone fallback extension still applies.",
                "",
            ]
        )

    for command in domain_commands:
        lines.append(generate_command_card(command, domain_commands))

    return "\n".join(lines).rstrip() + "\n"


def call_with_method(statement: str, source_method: str, target_method: str) -> str:
    return statement.replace(f"client.{source_method}(", f"client.{target_method}(", 1)


def build_alias_examples(alias: str, canonical: str) -> CommandExampleSpec:
    alias_method = python_name(alias)
    canonical_method = python_name(canonical)
    base = COMMAND_EXAMPLES[canonical]
    return CommandExampleSpec(
        sync_call=call_with_method(base.sync_call, canonical_method, alias_method),
        async_call=call_with_method(base.async_call, canonical_method, alias_method),
    )


def generate_alias_markdown(commands: list[ParsedCommand], alias_map: dict[str, str]) -> str:
    command_by_name = {command.name: command for command in commands}

    lines = [
        "# Alias Methods",
        "",
        "Direct alias-to-canonical mapping for all generated alias methods.",
        "",
        "### When to use this",
        "- Use aliases when you prefer short command names (`wp`, `p`, `r`, `c`, etc.).",
        "- Alias methods call canonical methods and return the same result shape.",
        "",
        "### Mapping table",
        "| Alias command | Canonical command | Alias Python method | Canonical Python method | Domain |",
        "| --- | --- | --- | --- | --- |",
    ]

    for alias, canonical in sorted(alias_map.items()):
        lines.append(
            f"| `{alias}` | `{canonical}` | `{python_name(alias)}` | `{python_name(canonical)}` | `{command_by_name[canonical].domain}` |"
        )

    lines.extend(
        [
            "",
            "### Example",
            "```python",
            "import asyncio",
            "from pyritone import Client",
            "",
            "async def main() -> None:",
            "    async with Client() as client:",
            "        dispatch = await client.wp(\"list\")",
            "        print(dispatch)",
            "",
            "asyncio.run(main())",
            "```",
            "",
            "### Return shape",
            "```text",
            "Aliases return the same shape as their canonical method.",
            "```",
            "",
            "### Common mistakes",
            "- Mixing alias names and canonical names in the same style guide. Pick one style per codebase.",
            "- Assuming aliases have different behavior; they are wrappers only.",
            "",
            "### Related methods",
            "- [Control commands](control.md)",
            "- [Navigation commands](navigation.md)",
            "- [Waypoints commands](waypoints.md)",
            "",
            "## Alias cards",
            "",
        ]
    )

    for alias, canonical in sorted(alias_map.items()):
        alias_method = python_name(alias)
        canonical_method = python_name(canonical)
        canonical_command = command_by_name[canonical]
        example = build_alias_examples(alias, canonical)

        lines.extend(
            [
                f"### `{alias}` -> `{canonical}`",
                "",
                f"Alias method `{alias_method}` delegates to `{canonical_method}`.",
                "",
                "#### Example",
                "```python",
                render_async_snippet(example),
                "```",
                "",
                "#### Related canonical command",
                f"- Domain: `{canonical_command.domain}`",
                f"- Canonical method: [`{canonical_method}`](./{canonical_command.domain}.md#{canonical})",
                "",
            ]
        )

    return "\n".join(lines).rstrip() + "\n"


def generate_markdown(commands: list[ParsedCommand], alias_map: dict[str, str]) -> str:

    lines = [
        "# Pyritone Baritone Command Reference",
        "",
        f"Generated from Baritone `{BARITONE_VERSION}` source files.",
        "",
        "## Canonical Commands",
        "",
    ]

    for command in sorted(commands, key=lambda item: item.name):
        method_name = python_name(command.name)
        aliases = ", ".join(command.aliases) if command.aliases else "none"
        target_note = f"Target: `{command.target}`" if command.target else None

        lines.extend(
            [
                f"### `{command.name}`",
                "",
                f"- Python method: `{method_name}`",
                f"- Aliases: {aliases}",
                f"- Domain: `{command.domain}`",
                f"- Source: `{command.source_file}`",
            ]
        )

        if target_note:
            lines.append(f"- {target_note}")

        lines.append(f"- Summary: {command.short_desc}")
        lines.append("")

        if command.usage_lines:
            lines.append("Usage:")
            for usage_line in command.usage_lines:
                lines.append(f"- `{usage_line}`")
            lines.append("")

        if command.long_desc_lines:
            lines.append("Notes:")
            for note_line in command.long_desc_lines:
                if note_line:
                    lines.append(f"- {note_line}")
            lines.append("")

    lines.extend(["## Alias Methods", ""])
    for alias, canonical in sorted(alias_map.items()):
        lines.append(f"- `{python_name(alias)}` -> `{python_name(canonical)}` (`{alias}` -> `{canonical}`)")

    lines.append("")
    return "\n".join(lines)


def generate_commands_package_init() -> str:
    return "\n".join(
        [
            "from ._catalog import ALIAS_METHOD_NAMES, ALIAS_TO_CANONICAL, BARITONE_VERSION, COMMAND_METHOD_NAMES, COMMAND_NAME_SET, COMMAND_SPECS",
            "from ._types import CommandArg, CommandDispatchResult, CommandSpec",
            "",
            "__all__ = [",
            "    \"ALIAS_METHOD_NAMES\",",
            "    \"ALIAS_TO_CANONICAL\",",
            "    \"BARITONE_VERSION\",",
            "    \"COMMAND_METHOD_NAMES\",",
            "    \"COMMAND_NAME_SET\",",
            "    \"COMMAND_SPECS\",",
            "    \"CommandArg\",",
            "    \"CommandDispatchResult\",",
            "    \"CommandSpec\",",
            "]",
            "",
        ]
    )


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Pyritone command wrappers from Baritone source")
    parser.add_argument("--check", action="store_true", help="Validate generated outputs without writing")
    args = parser.parse_args()

    default_source = fetch_text(DEFAULT_COMMANDS_URL)
    execution_source = fetch_text(EXECUTION_CONTROL_URL)

    commands = parse_default_commands(default_source)
    commands.extend(parse_execution_control_commands(execution_source))

    by_name: dict[str, ParsedCommand] = {}
    for command in commands:
        if command.name in by_name:
            raise ValueError(f"Duplicate command name parsed: {command.name}")
        by_name[command.name] = command

    commands = sorted(by_name.values(), key=lambda item: item.name)
    alias_map = build_alias_to_canonical(commands)

    if len(commands) != 42:
        raise ValueError(f"Expected 42 canonical commands, found {len(commands)}")
    if len(alias_map) != 21:
        raise ValueError(f"Expected 21 aliases, found {len(alias_map)}")
    if "schematica" in by_name:
        raise ValueError("schematica should not be included in generated commands")
    if set(COMMAND_EXAMPLES) != set(by_name):
        missing = sorted(set(by_name) - set(COMMAND_EXAMPLES))
        extra = sorted(set(COMMAND_EXAMPLES) - set(by_name))
        raise ValueError(f"COMMAND_EXAMPLES mismatch. Missing={missing} Extra={extra}")

    outputs = {
        COMMANDS_DIR / "_catalog.py": generate_catalog_module(commands, alias_map),
        COMMANDS_DIR / "__init__.py": generate_commands_package_init(),
        COMMANDS_DIR / "async_navigation.py": generate_domain_module(commands, alias_map, "navigation", async_mode=True),
        COMMANDS_DIR / "async_world.py": generate_domain_module(commands, alias_map, "world", async_mode=True),
        COMMANDS_DIR / "async_build.py": generate_domain_module(commands, alias_map, "build", async_mode=True),
        COMMANDS_DIR / "async_control.py": generate_domain_module(commands, alias_map, "control", async_mode=True),
        COMMANDS_DIR / "async_info.py": generate_domain_module(commands, alias_map, "info", async_mode=True),
        COMMANDS_DIR / "async_waypoints.py": generate_domain_module(commands, alias_map, "waypoints", async_mode=True),
        COMMANDS_DIR / "sync_navigation.py": generate_domain_module(commands, alias_map, "navigation", async_mode=False),
        COMMANDS_DIR / "sync_world.py": generate_domain_module(commands, alias_map, "world", async_mode=False),
        COMMANDS_DIR / "sync_build.py": generate_domain_module(commands, alias_map, "build", async_mode=False),
        COMMANDS_DIR / "sync_control.py": generate_domain_module(commands, alias_map, "control", async_mode=False),
        COMMANDS_DIR / "sync_info.py": generate_domain_module(commands, alias_map, "info", async_mode=False),
        COMMANDS_DIR / "sync_waypoints.py": generate_domain_module(commands, alias_map, "waypoints", async_mode=False),
        DOCS_RAW_REFERENCE_PATH: generate_markdown(commands, alias_map),
        DOCS_ALIASES_PATH: generate_alias_markdown(commands, alias_map),
    }

    for domain in DOMAIN_MODULES:
        outputs[DOCS_COMMANDS_DIR / f"{domain}.md"] = generate_domain_commands_markdown(commands, domain)

    if args.check:
        for path, content in outputs.items():
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                raise SystemExit(f"Out of date: {path}")
        return

    for path, content in outputs.items():
        write_text(path, content)

    print(f"Generated {len(outputs)} files")


if __name__ == "__main__":
    main()

