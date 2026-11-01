"""Check that mpv accepts Vela's options, and how play() picks https or http."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import time
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


# Stands in for mpv. https behaviour comes from FAKE_MPV_HTTPS: "hang" keeps
# connecting forever with no IPC, "serve" decodes. http always decodes. The
# IPC socket sends an event before each reply, as mpv does.
FAKE_MPV = textwrap.dedent(
    """
    import json, os, socket, sys, threading, time
    args = sys.argv[1:]
    url = args[args.index("--") + 1]
    sock = next(a.split("=", 1)[1] for a in args if a.startswith("--input-ipc-server="))
    with open(os.environ["FAKE_MPV_LOG"], "a") as log:
        log.write(url + "\\n")
    if url.startswith("https://") and os.environ.get("FAKE_MPV_HTTPS") == "hang":
        time.sleep(60)
        sys.exit(1)
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(sock)
    server.listen(4)
    def answer(conn):
        with conn:
            line = conn.makefile().readline()
            request = json.loads(line)
            conn.sendall(b'{"event":"audio-reconfig"}\\n')
            reply = {"request_id": request["request_id"], "error": "success", "data": "mp3"}
            conn.sendall((json.dumps(reply) + "\\n").encode())
    while True:
        conn, _ = server.accept()
        threading.Thread(target=answer, args=(conn,), daemon=True).start()
    """
)


class PlayFallbackTest(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        root = Path(self.folder.name)
        script = root / "mpv"
        script.write_text(f"#!{sys.executable}\n" + FAKE_MPV)
        script.chmod(0o755)
        self.log = root / "calls.log"
        self.env = patch.dict(os.environ, {"PATH": f"{root}{os.pathsep}{os.environ.get('PATH', '')}", "FAKE_MPV_LOG": str(self.log)})
        self.env.start()
        self.sock = patch.object(player, "_runtime_socket", return_value=str(root / "player.sock"))
        self.sock.start()
        self.player = player.Player()
        self.player.UPGRADE_WAIT = 1.0

    def tearDown(self):
        self.player.stop()
        self.sock.stop()
        self.env.stop()
        self.folder.cleanup()

    def calls(self):
        return self.log.read_text().split()

    def test_https_upgrade_that_never_decodes_falls_back_to_http(self):
        os.environ["FAKE_MPV_HTTPS"] = "hang"
        started = time.monotonic()
        message = self.player.play("http://radio.example.com/live")
        self.assertIsNone(message)
        self.assertEqual(self.player.url, "http://radio.example.com/live")
        self.assertEqual(self.calls(), ["https://radio.example.com/live", "http://radio.example.com/live"])
        self.assertLess(time.monotonic() - started, 4)

    def test_working_https_upgrade_is_kept(self):
        os.environ["FAKE_MPV_HTTPS"] = "serve"
        message = self.player.play("http://radio.example.com/live")
        self.assertIsNone(message)
        self.assertEqual(self.player.url, "https://radio.example.com/live")
        self.assertEqual(self.calls(), ["https://radio.example.com/live"])

    def test_ipc_skips_events_to_find_its_reply(self):
        os.environ["FAKE_MPV_HTTPS"] = "serve"
        self.player.play("https://radio.example.com/live")
        reply = self.player._reply(["get_property", "audio-codec-name"])
        self.assertEqual(reply["data"], "mp3")
        self.assertEqual(reply["request_id"], self.player._request)


if __name__ == "__main__":
    unittest.main()
