import tempfile
import unittest
from pathlib import Path

from recoverx.extractor import extract_path
from recoverx.utils import JPEG_SIGNATURE, PNG_SIGNATURE


def png_candidate():
    return (
        PNG_SIGNATURE
        + b"\x00\x00\x00\x00IHDR"
        + b"\x00\x00\x00\x00"
        + b"\x00\x00\x00\x00"
        + b"\x00\x00\x00\x00"
        + b"\x00\x00\x00\x00"
        + b"\x00\x00\x00\x00IEND\xaeB`\x82"
    )


class ExtractorTests(unittest.TestCase):
    def test_extracts_jpeg_and_png_into_separate_folders(self):
        jpeg = JPEG_SIGNATURE + b"synthetic jpeg payload" + b"\xff\xd9"
        png = png_candidate()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "cache.bin"
            output = root / "recovered"
            source.write_bytes(b"junk" + jpeg + b"gap" + png)

            result = extract_path(source, output)

            self.assertEqual(result.jpeg_candidates, 1)
            self.assertEqual(result.png_candidates, 1)
            self.assertEqual(result.partial_candidates, 0)
            self.assertEqual((output / "jpeg" / "candidate_000001_001.jpg").read_bytes(), jpeg)
            self.assertEqual((output / "png" / "candidate_000002_001.png").read_bytes(), png)

    def test_empty_and_invalid_files_produce_no_candidates(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "cache.bin"
            output = root / "recovered"
            source.write_bytes(b"")
            result = extract_path(source, output)
            self.assertEqual(result.jpeg_candidates + result.png_candidates, 0)

            source.write_bytes(b"not image data")
            result = extract_path(source, output)
            self.assertEqual(result.jpeg_candidates + result.png_candidates, 0)

    def test_truncated_candidates_are_saved_and_counted_as_partial(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "cache.bin"
            output = root / "recovered"
            source.write_bytes(JPEG_SIGNATURE + b"partial jpeg" + PNG_SIGNATURE + b"partial png")

            result = extract_path(source, output)

            self.assertEqual(result.jpeg_candidates, 1)
            self.assertEqual(result.png_candidates, 1)
            self.assertEqual(result.partial_candidates, 2)
            self.assertEqual(
                (output / "jpeg" / "candidate_000001_001.jpg").read_bytes(),
                JPEG_SIGNATURE + b"partial jpeg",
            )

    def test_existing_candidates_are_not_overwritten(self):
        jpeg = JPEG_SIGNATURE + b"payload" + b"\xff\xd9"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "cache.bin"
            output = root / "recovered"
            target = output / "jpeg" / "candidate_000001_001.jpg"
            target.parent.mkdir(parents=True)
            target.write_bytes(b"keep existing")
            source.write_bytes(jpeg)

            extract_path(source, output)

            self.assertEqual(target.read_bytes(), b"keep existing")
            self.assertEqual(
                (output / "jpeg" / "candidate_000001_002.jpg").read_bytes(), jpeg
            )

    def test_missing_input_is_reported(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(FileNotFoundError):
                extract_path(Path(directory) / "missing", Path(directory) / "out")


if __name__ == "__main__":
    unittest.main()
