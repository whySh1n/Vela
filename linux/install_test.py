"""Run the real installer against a throwaway home folder."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path

INSTALL = Path(__file__).resolve().parent / "install.sh"
LINE = 'export PATH="{home}/.local/bin:$PATH"'


def has_window():
    result = subprocess.run(
        ["python3", "-c", "from PySide6.QtWidgets import QApplication"],
        capture_output=True,
        check=False,
    )
    return result.returncode == 0


@unittest.skipUnless(shutil.which("mpv") and has_window(), "needs mpv and PySide6 already installed")
class InstallTest(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.home = Path(self.folder.name) / "home"
        self.home.mkdir()

    def tearDown(self):
        self.folder.cleanup()

    def install(self, extra_path=None):
        env = {key: value for key, value in os.environ.items() if key not in ("PREFIX",)}
        env["HOME"] = str(self.home)
        if extra_path:
            env["PATH"] = f"{extra_path}{os.pathsep}{env['PATH']}"
        return subprocess.run(
            ["sh", str(INSTALL)],
            env=env,
            text=True,
            capture_output=True,
            timeout=60,
            check=False,
        )

    def line(self):
        return LINE.format(home=self.home)

    def test_installs_into_the_home_folder(self):
        result = self.install()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        launcher = self.home / ".local/bin/vela"
        self.assertTrue(os.access(launcher, os.X_OK))
        self.assertTrue((self.home / ".local/opt/vela/gui.py").is_file())
        desktop = (self.home / ".local/share/applications/vela.desktop").read_text()
        self.assertNotIn("__PREFIX__", desktop)

    def test_without_shell_files_only_a_profile_is_written(self):
        result = self.install()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse((self.home / ".bashrc").exists())
        self.assertFalse((self.home / ".zshrc").exists())
        self.assertIn(self.line(), (self.home / ".profile").read_text())

    def test_existing_shell_files_get_the_path_once(self):
        (self.home / ".bashrc").write_text("# mine\n")
        (self.home / ".zshrc").write_text("# mine\n")
        for _ in range(2):
            result = self.install()
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for name in (".bashrc", ".zshrc"):
            text = (self.home / name).read_text()
            self.assertTrue(text.startswith("# mine\n"))
            self.assertEqual(text.count(self.line()), 1, name)
        self.assertFalse((self.home / ".profile").exists())

    def test_pip_refusal_explains_what_to_do(self):
        stubs = Path(self.folder.name) / "stubs"
        stubs.mkdir()
        real_python = shutil.which("python3")
        scripts = {
            # No PySide6, and pip refuses like on Arch.
            "python3": f"""
                if [ "$1" = "-c" ]; then exit 1; fi
                if [ "$1" = "-m" ] && [ "$2" = "pip" ]; then
                  echo "error: externally-managed-environment" >&2
                  exit 1
                fi
                exec {real_python} "$@"
            """,
            # The package manager step fails too (say the password was refused).
            "sudo": "exit 1",
        }
        for name, body in scripts.items():
            path = stubs / name
            path.write_text("#!/bin/sh\n" + textwrap.dedent(body))
            path.chmod(0o755)
        result = self.install(extra_path=stubs)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("could not add PySide6 with pip", result.stdout)
        self.assertIn("sudo pacman -S pyside6", result.stdout)
        self.assertFalse((self.home / ".local/bin/vela").exists())


if __name__ == "__main__":
    unittest.main()
