"""One version number: the program and the Arch package must agree."""

from __future__ import annotations

import re
import subprocess
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKGBUILD = HERE.parent / "packaging" / "arch" / "PKGBUILD"
sys.path.insert(0, str(HERE / "vela"))

import importlib.util

# Load vela/__main__.py under another name; "__main__" is the test runner.
spec = importlib.util.spec_from_file_location("vela_main", HERE / "vela" / "__main__.py")
vela_main = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vela_main)


class VersionTest(unittest.TestCase):
    def test_version_flag(self):
        for flag in ("--version", "-V"):
            result = subprocess.run(
                [sys.executable, str(HERE / "vela" / "__main__.py"), flag],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), f"vela {vela_main.VERSION}")

    @unittest.skipUnless(PKGBUILD.exists(), "no PKGBUILD in this tree")
    def test_pkgbuild_matches(self):
        pkgver = re.search(r"^pkgver=(\S+)$", PKGBUILD.read_text(), re.M).group(1)
        self.assertEqual(pkgver, vela_main.VERSION)


if __name__ == "__main__":
    unittest.main()
