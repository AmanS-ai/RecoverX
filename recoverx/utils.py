"""Shared file handling helpers for RecoverX."""

from __future__ import annotations

import os
from pathlib import Path
from typing import BinaryIO, Iterator

JPEG_SIGNATURE = b"\xff\xd8\xff"
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
SIGNATURES = (("JPEG", JPEG_SIGNATURE), ("PNG", PNG_SIGNATURE))
DEFAULT_CHUNK_SIZE = 1024 * 1024


def validate_input_path(path: str | os.PathLike[str]) -> Path:
    """Return an existing file or directory path, raising a useful error otherwise."""
    input_path = Path(path)
    if not input_path.exists():
        raise FileNotFoundError(f"Input path does not exist: {input_path}")
    if not input_path.is_file() and not input_path.is_dir():
        raise ValueError(f"Input path is not a file or directory: {input_path}")
    return input_path


def iter_input_files(
    path: str | os.PathLike[str],
    excluded_directories: tuple[Path, ...] = (),
) -> Iterator[Path]:
    """Yield files from a file or recursively from a directory."""
    input_path = validate_input_path(path)
    if input_path.is_file():
        yield input_path
        return

    excluded = tuple(item.resolve() for item in excluded_directories)

    def on_walk_error(error: OSError) -> None:
        raise error

    for root, directories, filenames in os.walk(input_path, onerror=on_walk_error):
        current = Path(root)
        kept_directories = []
        for name in directories:
            candidate = (current / name).resolve()
            if not any(candidate == item or item in candidate.parents for item in excluded):
                kept_directories.append(name)
        directories[:] = kept_directories
        for name in filenames:
            yield current / name


def write_candidate_name(
    folder: Path, index: int, extension: str
) -> tuple[Path, BinaryIO]:
    """Create a uniquely named, empty candidate without overwriting existing data."""
    folder.mkdir(parents=True, exist_ok=True)
    suffix = 1
    while True:
        candidate = folder / f"candidate_{index:06d}_{suffix:03d}.{extension}"
        try:
            return candidate, candidate.open("xb")
        except FileExistsError:
            suffix += 1
