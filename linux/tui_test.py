"""Terminal state handling that does not need a real terminal."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent / "vela"))

import tui


def station(index):
    return {"id": f"s{index}", "name": f"Station {index}", "streamUrl": "https://example.com/s.mp3", "custom": False}


class SavedScopeTest(unittest.TestCase):
    def setUp(self):
        self.config = tempfile.TemporaryDirectory()
        self.env = patch.dict(os.environ, {"XDG_CONFIG_HOME": self.config.name})
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.config.cleanup()

    def test_unsaving_the_last_row_twice_does_not_crash(self):
        app = tui.App()
        app.lib["favorites"] = [station(1), station(2)]
        app.scope = "saved"
        app.selected = 1
        app.toggle_saved()
        self.assertEqual(len(app.visible()), 1)
        self.assertEqual(app.selected, 0)
        app.toggle_saved()
        self.assertEqual(app.visible(), [])
        self.assertEqual(app.selected, 0)
        app.toggle_saved()  # empty list: nothing to do

    def test_stale_selection_is_clamped_before_use(self):
        app = tui.App()
        app.lib["favorites"] = [station(1)]
        app.scope = "saved"
        app.selected = 5
        app.toggle_saved()
        self.assertEqual(app.lib["favorites"], [])


if __name__ == "__main__":
    unittest.main()
