"""Check that mpv accepts the playback options Vela actually builds."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent / "vela"))

import player


class PlayerOptionsTest(unittest.TestCase):
    @unittest.skipUnless(shutil.which("mpv"), "mpv is not installed")
    def test_mpv_accepts_playback_options(self):
        with tempfile.TemporaryDirectory() as folder:
            socket_path = str(Path(folder) / "player.sock")
            with patch.object(player, "_runtime_socket", return_value=socket_path):
                with patch.object(player.subprocess, "Popen") as popen:
                    player.Player()._start("https://example.invalid/stream")
                    command = popen.call_args.args[0]

        self.assertEqual(command[-2:], ["--", "https://example.invalid/stream"])
        result = subprocess.run(
            [*command[:-2], "--list-options"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
