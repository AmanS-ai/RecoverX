"""Streaming detection of JPEG and PNG signatures in cache files."""

from __future__ import annotations

from heapq import merge
from pathlib import Path
from typing import BinaryIO, Iterator

from .utils import DEFAULT_CHUNK_SIZE, SIGNATURES


def iter_file_signatures(
    file_obj: BinaryIO,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    start_offset: int = 0,
) -> Iterator[tuple[str, int]]:
    """Yield (format, byte offset) for each signature using bounded memory."""
    if chunk_size < 1:
        raise ValueError("chunk_size must be greater than zero")

    file_obj.seek(start_offset)
    position = start_offset
    overlap_size = max(len(signature) for _, signature in SIGNATURES) - 1
    overlap = b""

    while True:
        chunk = file_obj.read(chunk_size)
        if not chunk:
            return

        searchable = overlap + chunk
        searchable_base = position - len(overlap)

        def matches(image_format: str, signature: bytes) -> Iterator[tuple[str, int]]:
            earliest_new_offset = max(start_offset, position - len(signature) + 1)
            search_from = 0
            while True:
                match = searchable.find(signature, search_from)
                if match == -1:
                    return
                offset = searchable_base + match
                if offset >= earliest_new_offset:
                    yield image_format, offset
                search_from = match + 1

        yield from merge(
            *(matches(image_format, signature) for image_format, signature in SIGNATURES),
            key=lambda item: item[1],
        )
        position += len(chunk)
        overlap = searchable[-overlap_size:] if overlap_size else b""


def iter_path_signatures(
    path: str | Path,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
) -> Iterator[tuple[str, int]]:
    """Yield signatures and offsets from one file."""
    with Path(path).open("rb") as file_obj:
        yield from iter_file_signatures(file_obj, chunk_size=chunk_size)
