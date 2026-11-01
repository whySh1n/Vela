"""Window close must not segfault, and refreshing the list must not leak rows."""

from __future__ import annotations

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
        for i in range(8)
    ]
    radio.search = lambda *args, **kwargs: list(STATIONS)

    from PySide6.QtCore import Qt, QTimer
    from PySide6.QtGui import QKeyEvent
    from PySide6.QtWidgets import QApplication, QWidget
    import shiboken6
    import gui

    released = threading.Event()
    resume = threading.Event()
    device_thread = [None]
    play_started = threading.Event()
    play_thread = [None]
    thread_errors = []
    original_thread_excepthook = threading.excepthook

    def record_thread_error(args):
        thread_errors.append(str(args.exc_value))
        original_thread_excepthook(args)

    threading.excepthook = record_thread_error

    original_exec = QApplication.exec

    def hooked(*_args, **_kwargs):
        def work():
            windows = [item for item in QApplication.topLevelWidgets() if type(item).__name__ == "Window"]
            if not windows:
                QTimer.singleShot(30, work)
                return
            window = windows[0]
            window.stations = list(STATIONS)
            window.scope = "dial"

            def kids():
                return len([child for child in window.list.viewport().children() if isinstance(child, QWidget)])

            window.fill()
            first = kids()
            for _ in range(4):
                window.fill()
            print("KIDS %s %s ROWS %s" % (first, kids(), window.list.count()), flush=True)
            sentinel = QWidget(window.list.viewport())
            window.fill()
            print("SENTINEL %s" % int(shiboken6.isValid(sentinel)), flush=True)
            window.stations = list(STATIONS[:2])
            window.selected = 7
            window.fill()
            selected = window.list.itemWidget(window.list.item(1))
            print("SELECTION %s %s %s %s" % (
                window.list.count(), window.selected, window.list.currentRow(),
                int("#161616" in selected.styleSheet())), flush=True)

            if os.environ.get("VELA_QUIT") == "device":
                class GateLock:
                    def __init__(self):
                        self.lock = threading.Lock()

                    def __enter__(self):
                        self.lock.acquire()

                    def __exit__(self, *_args):
                        self.lock.release()
                        if threading.current_thread() is device_thread[0]:
                            released.set()
                            resume.wait(10)

                window.lock = GateLock()
                window.player.url = "https://example.com/s.mp3"
                window.player.set_device = lambda _device: device_thread.__setitem__(0, threading.current_thread())
                window.device_box.addItem("Test device", "test-device")
                window.device_box.setCurrentIndex(window.device_box.count() - 1)

                def close_when_ready():
                    if released.is_set():
                        window.close()
                        print("AFTER_CLOSE %s %s" % (window.list.count(), kids()), flush=True)
                    else:
                        QTimer.singleShot(1, close_when_ready)

                QTimer.singleShot(1, close_when_ready)
                return
            if os.environ.get("VELA_QUIT") == "play":
                def playing(_url, allow_private=False):
                    play_thread[0] = threading.current_thread()
                    play_started.set()
                    time.sleep(0.25)
                    return None

                window.player.play = playing
                window.play_index(0)

                def close_while_playing():
                    if play_started.is_set():
                        window.close()
                        print("AFTER_CLOSE %s %s" % (window.list.count(), kids()), flush=True)
                    else:
                        QTimer.singleShot(1, close_while_playing)

                QTimer.singleShot(1, close_while_playing)
                return
            if os.environ.get("VELA_QUIT") == "key":
                window.list.setFocus()
                window.keyPressEvent(QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key_Q, Qt.ControlModifier))
            else:
                window.close()
            print("AFTER_CLOSE %s %s" % (window.list.count(), kids()), flush=True)

        QTimer.singleShot(40, work)
        return original_exec()

    QApplication.exec = hooked
    code = gui.main(["vela"])
    if os.environ.get("VELA_QUIT") == "device":
        resume.set()
        if device_thread[0] is not None:
            device_thread[0].join(5)
        print("DEVICE_THREAD %s ERRORS %s" % (
            int(device_thread[0] is not None and not device_thread[0].is_alive()),
            len(thread_errors)), flush=True)
    if os.environ.get("VELA_QUIT") == "play":
        if play_thread[0] is not None:
            play_thread[0].join(5)
        print("PLAY_THREAD %s ERRORS %s" % (
            int(play_thread[0] is not None and not play_thread[0].is_alive()),
            len(thread_errors)), flush=True)
    print("THREAD_ERRORS %s" % len(thread_errors), flush=True)
    print("CLOSED %s" % code, flush=True)
    raise SystemExit(code or 0)
    """
)


class ShutdownTest(unittest.TestCase):
    def run_child(self, quit_mode):
        with tempfile.TemporaryDirectory() as config:
            env = os.environ.copy()
            env["VELA_DIR"] = str(VELA)
            env["XDG_CONFIG_HOME"] = config
            env["QT_QPA_PLATFORM"] = "offscreen"
            env["QT_QPA_PLATFORMTHEME"] = "none"
            env["VELA_QUIT"] = quit_mode
            return subprocess.run(
                [sys.executable, "-c", CHILD],
                env=env,
                text=True,
                capture_output=True,
                timeout=30,
                check=False,
            )

    def assert_clean(self, quit_mode):
        result = self.run_child(quit_mode)
        self.assertEqual(
            result.returncode,
            0,
            "stdout:\n%s\nstderr:\n%s" % (result.stdout, result.stderr),
        )
        line = next(line for line in result.stdout.splitlines() if line.startswith("KIDS "))
        _label, first, again, _rows_label, rows = line.split()
        self.assertEqual(first, again)
        self.assertEqual(first, rows)
        self.assertNotEqual(first, "0")
        self.assertIn("SENTINEL 1", result.stdout)
        self.assertIn("SELECTION 2 1 1 1", result.stdout)
        self.assertIn("AFTER_CLOSE 0 1", result.stdout)
        if quit_mode == "device":
            self.assertIn("DEVICE_THREAD 1 ERRORS 0", result.stdout)
        if quit_mode == "play":
            self.assertIn("PLAY_THREAD 1 ERRORS 0", result.stdout)
        self.assertIn("THREAD_ERRORS 0", result.stdout)
        self.assertIn("CLOSED 0", result.stdout)

    def test_close_releases_rows_and_exits(self):
        self.assert_clean("close")

    def test_ctrl_q_exits(self):
        self.assert_clean("key")

    def test_device_change_does_not_emit_after_close(self):
        self.assert_clean("device")

    def test_close_waits_for_inflight_play(self):
        self.assert_clean("play")


if __name__ == "__main__":
    unittest.main()
