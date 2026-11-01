"""Keyboard, selection, click, and locking behaviour of the Qt window."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

VELA = Path(__file__).resolve().parent / "vela"

CHILD = textwrap.dedent(
    r"""
    import json
    import os
    import sys
    import threading
    import time

    sys.path.insert(0, os.environ["VELA_DIR"])
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

    import radio

    STATIONS = [
        {
            "id": "s%s" % i,
            "name": "Station %s" % i,
            "streamUrl": "https://example.com/s.mp3",
            "homepage": "",
            "tags": "jazz",
            "country": "Nowhere",
            "countryCode": "XX",
            "language": "en",
            "codec": "MP3",
            "bitrate": 128,
            "custom": False,
        }
        for i in range(6)
    ]
    radio.search = lambda *args, **kwargs: list(STATIONS)
    import library

    from PySide6.QtCore import Qt, QTimer
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication, QPushButton
    import gui

    results = {}
    original_exec = QApplication.exec

    def settle(app, seconds=0.2):
        end = time.time() + seconds
        while time.time() < end:
            app.processEvents()
            time.sleep(0.01)

    def hooked(*_args, **_kwargs):
        app = QApplication.instance()

        def work():
            windows = [item for item in QApplication.topLevelWidgets() if type(item).__name__ == "Window"]
            if not windows or windows[0].list.count() == 0:
                QTimer.singleShot(30, work)
                return
            window = windows[0]
            window.activateWindow()
            settle(app)
            # Keep tests away from a real mpv.
            plays = []
            window.player.play = lambda url, allow_private=False: plays.append(url) or None
            window.player.devices = lambda: []

            # Bug 1: Space at launch plays instead of pressing a focused button.
            focus = QApplication.focusWidget()
            results["initial_focus_button"] = isinstance(focus, QPushButton)
            results["initial_focus_list"] = focus is window.list
            toggles = []
            original_toggle = window.toggle
            window.toggle = lambda: toggles.append(1)
            QTest.keyClick(focus or window, Qt.Key_Space)
            settle(app, 0.05)
            results["space_toggles"] = len(toggles)
            results["sleep_after_space"] = window.sleep_btn.text()
            window.toggle = original_toggle

            # Bug 2: shortcuts work while the list has focus.
            window.list.setFocus()
            window.list.setCurrentRow(0)
            settle(app, 0.05)
            QTest.keyClick(window.list, Qt.Key_F)
            results["favorites_after_f"] = len(window.lib["favorites"])
            QTest.keyClick(window.list, Qt.Key_S)
            results["sleep_after_s"] = window.sleep_btn.text()
            window.sleep_at = None
            window.sleep_btn.setText("Sleep")
            QTest.keyClick(window.list, Qt.Key_J)
            results["row_after_j"] = window.list.currentRow()

            # Bug 3: the highlight follows the selection.
            QTest.keyClick(window.list, Qt.Key_Down)
            def lit(row):
                return "#161616" in window.list.itemWidget(window.list.item(row)).styleSheet()
            results["row_after_down"] = window.list.currentRow()
            results["lit"] = [lit(row) for row in range(4)]

            # Bug 5: a single click plays, once; clicking the live station again does not restart it.
            cancels = []
            window.player.cancel = lambda: cancels.append(1)
            plays.clear()
            row_widget = window.list.itemWidget(window.list.item(3))
            point = row_widget.rect().center()
            point.setX(40)
            QTest.mouseClick(row_widget, Qt.LeftButton, Qt.NoModifier, point)
            settle(app, 0.3)
            results["plays_after_click"] = len(plays)
            results["status_after_click"] = window.status
            QTest.mouseClick(row_widget, Qt.LeftButton, Qt.NoModifier, point)
            settle(app, 0.3)
            results["plays_after_second_click"] = len(plays)
            results["cancels_after_click"] = len(cancels)

            # Bug 4: the UI does not wait for a worker that holds the lock,
            # and what changed meanwhile reaches mpv once tuning ends.
            synced = []
            window.player.sync = lambda: synced.append(window.player.volume)
            holding = threading.Event()
            def hold():
                with window.lock:
                    holding.set()
                    time.sleep(1.5)
            holder = threading.Thread(target=hold)
            holder.start()
            holding.wait(5)
            start = time.time()
            window.vol.setValue(37)
            window.toggle_mute()
            window.toggle_mute()
            window.balance.setValue(3)
            window.toggle()
            window.tick()
            results["blocked_seconds"] = round(time.time() - start, 2)
            holder.join()
            results["volume_field"] = window.player.volume
            window.play_token += 1
            window.on_played(window.play_token, "")
            results["synced"] = synced

            # Sliders write the library once they settle, and closing flushes.
            settle(app, 0.6)
            saves = []
            original_save = library.save
            library.save = lambda lib: saves.append(lib.get("volume")) or original_save(lib)
            for value in range(50, 70):
                window.vol.setValue(value)
            for value in range(-5, 6):
                window.balance.setValue(value)
            results["saves_while_dragging"] = len(saves)
            settle(app, 0.7)
            results["saves_after_settle"] = list(saves)
            window.vol.setValue(12)

            print("RESULTS " + json.dumps(results), flush=True)

            # Closing while a dead station tunes must not wait for it.
            gate = threading.Event()
            def slow(url, allow_private=False):
                gate.wait(10)
                return "Tuning stopped."
            window.player.play = slow
            window.player.cancel = gate.set
            window.play_index(0)
            settle(app, 0.1)
            start = time.time()
            window.close()
            print("CLOSE_SECONDS %.2f" % (time.time() - start), flush=True)

        QTimer.singleShot(40, work)
        return original_exec()

    QApplication.exec = hooked
    code = gui.main(["vela"])
    print("SAVED_VOLUME %s" % library.load()["volume"], flush=True)
    raise SystemExit(code or 0)
    """
)


class WindowTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with tempfile.TemporaryDirectory() as config:
            env = os.environ.copy()
            env["VELA_DIR"] = str(VELA)
            env["XDG_CONFIG_HOME"] = config
            env["QT_QPA_PLATFORM"] = "offscreen"
            env["QT_QPA_PLATFORMTHEME"] = "none"
            result = subprocess.run(
                [sys.executable, "-c", CHILD],
                env=env,
                text=True,
                capture_output=True,
                timeout=60,
                check=False,
            )
        line = next((item for item in result.stdout.splitlines() if item.startswith("RESULTS ")), None)
        if result.returncode != 0 or line is None:
            raise AssertionError("stdout:\n%s\nstderr:\n%s" % (result.stdout, result.stderr))
        cls.results = json.loads(line[len("RESULTS ") :])
        cls.stdout = result.stdout

    def test_space_at_launch_plays_instead_of_pressing_a_button(self):
        self.assertFalse(self.results["initial_focus_button"])
        self.assertTrue(self.results["initial_focus_list"])
        self.assertEqual(self.results["space_toggles"], 1)
        self.assertEqual(self.results["sleep_after_space"], "Sleep")

    def test_letter_shortcuts_work_while_the_list_has_focus(self):
        self.assertEqual(self.results["favorites_after_f"], 1)
        self.assertEqual(self.results["sleep_after_s"], "15m")
        self.assertEqual(self.results["row_after_j"], 1)

    def test_highlight_follows_the_selection(self):
        self.assertEqual(self.results["row_after_down"], 2)
        self.assertEqual(self.results["lit"], [False, False, True, False])

    def test_single_click_plays_once(self):
        self.assertEqual(self.results["plays_after_click"], 1)
        self.assertEqual(self.results["status_after_click"], "playing")
        self.assertEqual(self.results["plays_after_second_click"], 1)

    def test_controls_do_not_wait_for_a_tuning_worker(self):
        self.assertLess(self.results["blocked_seconds"], 0.3)
        self.assertEqual(self.results["volume_field"], 37)
        self.assertEqual(self.results["synced"], [37])

    def test_sliders_write_the_library_once_they_settle(self):
        self.assertEqual(self.results["saves_while_dragging"], 0)
        self.assertEqual(self.results["saves_after_settle"], [69])

    def test_starting_a_station_cancels_one_still_tuning(self):
        self.assertEqual(self.results["cancels_after_click"], 1)

    def test_closing_does_not_wait_for_a_dead_station(self):
        line = next(item for item in self.stdout.splitlines() if item.startswith("CLOSE_SECONDS "))
        self.assertLess(float(line.split()[1]), 1.0)

    def test_closing_flushes_a_pending_save(self):
        self.assertIn("SAVED_VOLUME 12", self.stdout)


if __name__ == "__main__":
    unittest.main()
