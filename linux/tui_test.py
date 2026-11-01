"""Terminal state handling that does not need a real terminal."""

from __future__ import annotations

import os
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent / "vela"))

import library
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


class TuiCase(unittest.TestCase):
    def setUp(self):
        self.config = tempfile.TemporaryDirectory()
        self.env = patch.dict(os.environ, {"XDG_CONFIG_HOME": self.config.name})
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.config.cleanup()


def collect_until(app, done, seconds=5):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        app.collect()
        if done():
            return True
        time.sleep(0.01)
    return False


class SearchTest(TuiCase):
    def test_search_returns_at_once_and_results_arrive_later(self):
        gate = threading.Event()

        def slow(name, tag, country):
            gate.wait(5)
            return [station(1), station(2)]

        app = tui.App()
        with patch.object(tui.radio, "search", slow):
            started = time.monotonic()
            app.search()
            self.assertLess(time.monotonic() - started, 0.5)
            self.assertTrue(app.searching)
            self.assertEqual(app.note, "tuning the directory…")
            gate.set()
            self.assertTrue(collect_until(app, lambda: not app.searching))
        self.assertEqual([row["id"] for row in app.stations], ["s1", "s2"])
        self.assertEqual(app.note, "2 stations")

    def test_an_older_answer_does_not_replace_a_newer_one(self):
        gate = threading.Event()

        def search(name, tag, country):
            if name == "old":
                gate.wait(5)
                return [station(1)]
            return [station(2)]

        app = tui.App()
        with patch.object(tui.radio, "search", search):
            app.query = "old"
            app.search()
            app.query = "new"
            app.search()
            self.assertTrue(collect_until(app, lambda: not app.searching))
            gate.set()
            time.sleep(0.2)
            app.collect()
        self.assertEqual([row["id"] for row in app.stations], ["s2"])

    def test_a_failed_search_shows_the_error(self):
        def broken(*_args):
            raise RuntimeError("The directory did not answer.")

        app = tui.App()
        with patch.object(tui.radio, "search", broken):
            app.search()
            self.assertTrue(collect_until(app, lambda: not app.searching))
        self.assertEqual(app.stations, [])
        self.assertEqual(app.error, "The directory did not answer.")


class CustomStreamTest(TuiCase):
    def test_two_streams_added_in_the_same_second_both_stay(self):
        app = tui.App()
        app.player.play = lambda *_args, **_kwargs: None
        with patch.object(time, "time", return_value=1_700_000_000.0):
            app.add_custom("One", "https://one.example.com/live")
            app.add_custom("Two", "https://two.example.com/live")
        names = sorted(item["name"] for item in library.load()["custom"])
        self.assertEqual(names, ["One", "Two"])

    def test_custom_ids_are_unique(self):
        ids = {library.new_custom_id() for _ in range(500)}
        self.assertEqual(len(ids), 500)
        self.assertTrue(all(item.startswith("custom:") for item in ids))


if __name__ == "__main__":
    unittest.main()
