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
    import gui

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
            if os.environ.get("VELA_QUIT") == "key":
                window.list.setFocus()
                window.keyPressEvent(QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key_Q, Qt.ControlModifier))
            else:
                window.close()

        QTimer.singleShot(40, work)
        return original_exec()

    QApplication.exec = hooked
    code = gui.main(["vela"])
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
        self.assertIn("CLOSED 0", result.stdout)

    def test_close_releases_rows_and_exits(self):
        self.assert_clean("close")

    def test_ctrl_q_exits(self):
        self.assert_clean("key")


if __name__ == "__main__":
    unittest.main()
