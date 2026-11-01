"""mpv-backed playback with a small JSON IPC socket."""

from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import tempfile
import time


class Player:
    def __init__(self, volume=82):
        self.volume = max(0, min(100, int(volume)))
        self.muted = False
        self.paused = False
        self.sock = os.path.join(tempfile.gettempdir(), f"vela-{os.getuid()}.sock")
        self.proc = None
        self.url = ""
        self._request = 0

    def available(self):
        return shutil.which("mpv") is not None

    def play(self, url):
        if not self.available():
            return "mpv is not installed. The installer adds it on Arch and Debian."
        urls = [url]
        if url.startswith("http://"):
            urls = ["https://" + url[len("http://") :], url]
        last = "This station did not answer."
        for candidate in urls:
            self._start(candidate)
            time.sleep(0.8)
            if self.proc and self.proc.poll() is None:
                self.url = candidate
                self.paused = False
                return None
            last = "This station did not answer."
        self.url = ""
        return last

    def _start(self, url):
        self.stop()
        if os.path.exists(self.sock):
            try:
                os.remove(self.sock)
            except OSError:
                pass
        self.proc = subprocess.Popen(
            [
                "mpv",
                "--no-video",
                "--no-terminal",
                "--really-quiet",
                "--idle=no",
                f"--volume={0 if self.muted else self.volume}",
                f"--input-ipc-server={self.sock}",
                "--",
                url,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def stop(self):
        proc = self.proc
        self.proc = None
        if proc and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=1)
            except subprocess.TimeoutExpired:
                proc.kill()

    def alive(self):
        return self.proc is not None and self.proc.poll() is None

    def toggle(self):
        if not self.alive():
            return
        self.paused = not self.paused
        self.ipc(["set_property", "pause", self.paused])

    def set_volume(self, volume):
        self.volume = max(0, min(100, int(volume)))
        if self.volume > 0:
            self.muted = False
        self.ipc(["set_property", "volume", 0 if self.muted else self.volume])

    def toggle_mute(self):
        self.muted = not self.muted
        self.ipc(["set_property", "volume", 0 if self.muted else self.volume])

    def ipc(self, command):
        if not os.path.exists(self.sock):
            return None
        self._request += 1
        payload = {"command": command, "request_id": self._request}
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client.settimeout(0.4)
        try:
            client.connect(self.sock)
            client.sendall((json.dumps(payload) + "\n").encode("utf-8"))
            data = b""
            while b"\n" not in data:
                chunk = client.recv(4096)
                if not chunk:
                    break
                data += chunk
        except OSError:
            return None
        finally:
            client.close()
        return data
