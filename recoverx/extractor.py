"""Best-effort JPEG and PNG candidate carving."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import BinaryIO, Callable

from .scanner import iter_file_signatures
from .utils import (
    DEFAULT_CHUNK_SIZE,
    JPEG_SIGNATURE,
    PNG_SIGNATURE,
    iter_input_files,
    write_candidate_name,
)

JPEG_END = b"\xff\xd9"


@dataclass
class FileExtraction:
    """Extraction counts and warnings for one input file."""

    path: Path
    jpeg_candidates: int = 0
    png_candidates: int = 0
    partial_candidates: int = 0
    warnings: list[str] = field(default_factory=list)


@dataclass
class ExtractionSummary:
    """Totals for an extraction operation."""

    files_scanned: int = 0
    jpeg_candidates: int = 0
    png_candidates: int = 0
    partial_candidates: int = 0
    warnings: list[str] = field(default_factory=list)


def _find_jpeg_end(file_obj: BinaryIO, start: int, file_size: int) -> tuple[int, bool]:
    file_obj.seek(start + len(JPEG_SIGNATURE))
    position = start + len(JPEG_SIGNATURE)
    carry = b""
    while True:
        chunk = file_obj.read(DEFAULT_CHUNK_SIZE)
        if not chunk:
            return file_size, False
        searchable = carry + chunk
        searchable_base = position - len(carry)
        marker = searchable.find(JPEG_END)
        next_signature_offsets = [
            searchable.find(signature)
            for signature in (JPEG_SIGNATURE, PNG_SIGNATURE)
            if searchable.find(signature) != -1
        ]
        next_signature_offset = min(next_signature_offsets, default=-1)
        if searchable_base + next_signature_offset <= start:
            next_signature_offset = -1
        if marker != -1:
            end_offset = searchable_base + marker + len(JPEG_END)
            if next_signature_offset == -1 or end_offset <= searchable_base + next_signature_offset:
                return end_offset, True
        if next_signature_offset != -1:
            return searchable_base + next_signature_offset, False
        position += len(chunk)
        carry = searchable[-(len(PNG_SIGNATURE) - 1):]


def _next_signature_offset(file_obj: BinaryIO, start: int, file_size: int) -> int:
    next_match = next(iter_file_signatures(file_obj, start_offset=start), None)
    return next_match[1] if next_match is not None else file_size


def _find_png_end(file_obj: BinaryIO, start: int, file_size: int) -> tuple[int, bool]:
    file_obj.seek(start + len(PNG_SIGNATURE))
    while file_obj.tell() + 8 <= file_size:
        header = file_obj.read(8)
        if len(header) != 8:
            break
        length = int.from_bytes(header[:4], "big")
        chunk_type = header[4:]
        chunk_end = file_obj.tell() + length + 4
        if chunk_end > file_size:
            break
        file_obj.seek(length + 4, 1)
        if chunk_type == b"IEND" and length == 0:
            return file_obj.tell(), True
    return _next_signature_offset(file_obj, start + len(PNG_SIGNATURE), file_size), False


def _copy_range(file_obj: BinaryIO, start: int, end: int, destination: BinaryIO) -> None:
    file_obj.seek(start)
    remaining = end - start
    while remaining:
        chunk = file_obj.read(min(DEFAULT_CHUNK_SIZE, remaining))
        if not chunk:
            raise OSError("Input file changed or ended while extracting a candidate")
        destination.write(chunk)
        remaining -= len(chunk)


def extract_file(
    path: str | Path,
    output_directory: str | Path,
) -> FileExtraction:
    """Carve image candidates from one file into format-specific subdirectories."""
    source = Path(path)
    output = Path(output_directory)
    result = FileExtraction(path=source)

    with source.open("rb") as file_obj:
        file_size = source.stat().st_size
        cursor = 0
        candidate_index = 0
        while cursor < file_size:
            match = next(iter_file_signatures(file_obj, start_offset=cursor), None)
            if match is None:
                break
            image_format, start = match
            if image_format == "JPEG":
                end, complete = _find_jpeg_end(file_obj, start, file_size)
                extension = "jpg"
                folder = output / "jpeg"
            else:
                end, complete = _find_png_end(file_obj, start, file_size)
                extension = "png"
                folder = output / "png"

            candidate_index += 1
            candidate_path, destination = write_candidate_name(
                folder, candidate_index, extension
            )
            try:
                with destination:
                    _copy_range(file_obj, start, end, destination)
            except OSError:
                candidate_path.unlink(missing_ok=True)
                raise

            if image_format == "JPEG":
                result.jpeg_candidates += 1
            else:
                result.png_candidates += 1
            if not complete:
                result.partial_candidates += 1
                result.warnings.append(
                    f"Partial {image_format} candidate saved: {candidate_path}"
                )
            cursor = max(end, start + (len(JPEG_SIGNATURE) if image_format == "JPEG" else len(PNG_SIGNATURE)))
            if not complete and end >= file_size:
                break

    return result


def extract_path(
    input_path: str | Path,
    output_directory: str | Path,
    progress_callback: Callable[[Path], None] | None = None,
) -> ExtractionSummary:
    """Extract candidates from a file or recursively from a directory."""
    output = Path(output_directory)
    excluded_directories = (output / "jpeg", output / "png")
    summary = ExtractionSummary()
    for source in iter_input_files(input_path, excluded_directories):
        if progress_callback is not None:
            progress_callback(source)
        try:
            result = extract_file(source, output)
        except OSError as error:
            summary.warnings.append(f"Could not process {source}: {error}")
            continue
        summary.files_scanned += 1
        summary.jpeg_candidates += result.jpeg_candidates
        summary.png_candidates += result.png_candidates
        summary.partial_candidates += result.partial_candidates
        summary.warnings.extend(result.warnings)
    return summary
