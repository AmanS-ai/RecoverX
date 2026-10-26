#!/usr/bin/env python3
"""RecoverX command-line interface."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from recoverx.extractor import extract_path
from recoverx.scanner import iter_path_signatures
from recoverx.utils import iter_input_files, validate_input_path


def _scan(input_path: Path) -> int:
    total_jpeg = 0
    total_png = 0
    errors = 0
    try:
        for source in iter_input_files(input_path):
            jpeg_count = 0
            png_count = 0
            try:
                for image_format, offset in iter_path_signatures(source):
                    print(f"{source}: {image_format} signature at byte offset {offset}")
                    if image_format == "JPEG":
                        jpeg_count += 1
                    else:
                        png_count += 1
            except OSError as error:
                errors += 1
                print(f"Error: could not read {source}: {error}", file=sys.stderr)
                continue
            total_jpeg += jpeg_count
            total_png += png_count
            print(f"{source}: {jpeg_count} JPEG, {png_count} PNG signature(s)")
    except OSError as error:
        print(f"Error: could not scan input: {error}", file=sys.stderr)
        return 1

    print(
        f"Scan summary: {total_jpeg + total_png} signature(s) "
        f"({total_jpeg} JPEG, {total_png} PNG)"
    )
    return 1 if errors else 0


def _extract(input_path: Path, output_path: Path) -> int:
    try:
        summary = extract_path(
            input_path,
            output_path,
            progress_callback=lambda source: print(f"Processing {source}...", flush=True),
        )
    except (OSError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    print(f"Processed {summary.files_scanned} file(s).")
    print(
        f"Saved {summary.jpeg_candidates} JPEG candidate(s) and "
        f"{summary.png_candidates} PNG candidate(s) to {output_path}."
    )
    if summary.partial_candidates:
        print(f"{summary.partial_candidates} candidate(s) were saved without a detected end marker.")
    print(
        "Candidates are best-effort and may be partial, duplicated, blurred, or invalid; "
        "signatures are not proof of recoverable photos."
    )
    for warning in summary.warnings:
        print(f"Warning: {warning}", file=sys.stderr)
    return 1 if summary.warnings else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="recoverx",
        description=(
            "Scan Android Gallery cache files and carve JPEG/PNG image candidates."
        ),
    )
    commands = parser.add_subparsers(dest="command", required=True)

    scan_parser = commands.add_parser("scan", help="find JPEG and PNG signatures")
    scan_parser.add_argument("input", help="cache file or directory to scan")

    extract_parser = commands.add_parser(
        "extract", help="carve best-effort image candidates"
    )
    extract_parser.add_argument("input", help="cache file or directory to process")
    extract_parser.add_argument(
        "--output",
        default="GalleryRecovery",
        help="output directory (default: GalleryRecovery)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        input_path = validate_input_path(args.input)
    except (OSError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    if args.command == "scan":
        return _scan(input_path)
    return _extract(input_path, Path(args.output))


if __name__ == "__main__":
    raise SystemExit(main())
