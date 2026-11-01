"""The download in public/ must match the code in linux/."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import make_zip


class DownloadTest(unittest.TestCase):
    def test_public_zip_is_current(self):
        with tempfile.TemporaryDirectory() as folder:
            fresh = make_zip.build(Path(folder) / "vela-linux.zip").read_bytes()
        self.assertEqual(
            fresh,
            make_zip.TARGET.read_bytes(),
            "public/vela-linux.zip is out of date. Run: python3 linux/make_zip.py",
        )


if __name__ == "__main__":
    unittest.main()
