from __future__ import annotations

import inspect
from pathlib import Path

DEFAULT_SCHEMATIC_EXTENSIONS = (".schem", ".schematic", ".litematic")
_PACKAGE_ROOT = Path(__file__).resolve().parent


def _infer_caller_base_dir() -> Path:
    stack = inspect.stack()
    try:
        for frame_info in stack[2:]:
            filename = frame_info.filename
            if not filename or filename.startswith("<"):
                continue

            frame_path = Path(filename)
            resolved = frame_path.resolve()

            # Skip internal library frames so we resolve against user code.
            if resolved == _PACKAGE_ROOT or _PACKAGE_ROOT in resolved.parents:
                continue

            if resolved.exists() and resolved.is_dir():
                return resolved
            return resolved.parent
    finally:
        del stack

    return Path.cwd()


def normalize_schematic_path(path: str | Path, *, base_dir: str | Path | None = None) -> str:
    input_path = Path(path).expanduser()

    if base_dir is not None:
        base_path = Path(base_dir).expanduser().resolve()
    else:
        base_path = _infer_caller_base_dir()

    if input_path.is_absolute():
        candidate = input_path
    else:
        candidate = base_path / input_path

    if candidate.suffix:
        resolved = candidate.resolve()
        return resolved.as_posix()

    # No extension provided: prefer local existing files by extension.
    for extension in DEFAULT_SCHEMATIC_EXTENSIONS:
        with_extension = candidate.with_suffix(extension)
        if with_extension.exists():
            return with_extension.resolve().as_posix()

    # Fall back to extension-less path so Baritone fallback extension can apply.
    return candidate.resolve().as_posix()


def normalize_build_coords(coords: tuple[int, ...]) -> tuple[int, ...]:
    if len(coords) not in (0, 3):
        raise ValueError("build_file expects either 0 or 3 coordinates")

    for value in coords:
        if not isinstance(value, int) or isinstance(value, bool):
            raise ValueError("build_file coordinates must be integers")

    return coords
