import tempfile
import unittest
from pathlib import Path

from recoverx.scanner import iter_path_signatures
from recoverx.utils import JPEG_SIGNATURE, PNG_SIGNATURE


class ScannerTests(unittest.TestCase):
    def test_detects_jpeg_and_png_offsets_across_chunk_boundaries(self):
        content = b"x" * 7 + JPEG_SIGNATURE + b"y" * 5 + PNG_SIGNATURE
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "cache.bin"
            source.write_bytes(content)

            self.assertEqual(
                list(iter_path_signatures(source, chunk_size=8)),
                [("JPEG", 7), ("PNG", 15)],
            )

    def test_empty_and_invalid_files_have_no_signatures(self):
        with tempfile.TemporaryDirectory() as directory:
            empty = Path(directory) / "empty"
            invalid = Path(directory) / "invalid"
            empty.write_bytes(b"")
            invalid.write_bytes(b"not an image")

            self.assertEqual(list(iter_path_signatures(empty)), [])
            self.assertEqual(list(iter_path_signatures(invalid)), [])

    def test_signatures_in_overlap_are_not_reported_twice(self):
        content = b"x" + JPEG_SIGNATURE + b"y" * 9 + JPEG_SIGNATURE
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "cache.bin"
            source.write_bytes(content)

            self.assertEqual(
                list(iter_path_signatures(source, chunk_size=8)),
                [("JPEG", 1), ("JPEG", 13)],
            )

    def test_missing_file_is_reported(self):
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "missing"
            with self.assertRaises(FileNotFoundError):
                list(iter_path_signatures(missing))

    def test_invalid_chunk_size_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "cache.bin"
            source.write_bytes(PNG_SIGNATURE)
            with self.assertRaises(ValueError):
                list(iter_path_signatures(source, chunk_size=0))


if __name__ == "__main__":
    unittest.main()
