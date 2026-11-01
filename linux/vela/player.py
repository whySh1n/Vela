"""mpv-backed playback with a small JSON IPC socket."""

from __future__ import annotations

import ipaddress
import json
import os
import re
import shutil
import socket
import subprocess
import time
from urllib.parse import urlsplit

EQS = ("flat", "voice", "night", "bass")
_DEVICE = re.compile(r"^[A-Za-z0-9_.:/=+-]+$")
_HELP = re.compile(r"^\s*'([^']+)'\s+\((.*)\)\s*$")


def safe_url(url, allow_private=False):
    """Accept only a plain http(s) stream. No files, credentials, or local services."""
    if not isinstance(url, str):
        return ""
    url = url.strip()
    if not url or len(url) > 500:
        return ""
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in url):
        return ""
    try:
        parts = urlsplit(url)
    except ValueError:
        return ""
    if parts.scheme not in ("http", "https") or parts.username or parts.password:
        return ""
    host = parts.hostname
    if not host or host.isdigit() or host.lower() in ("localhost", "metadata.google.internal"):
        return ""
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        address = None
    if address is not None:
        if (
            address.is_loopback
            or address.is_link_local
            or address.is_multicast
            or address.is_reserved
            or address.is_unspecified
            or (address.is_private and not allow_private)
        ):
            return ""
    return url


def parse_devices(text):
    devices = []
    seen = set()
    for line in text.splitlines():
        match = _HELP.match(line)
        if not match:
            continue
        device_id = match.group(1).strip()
        if not device_id or device_id in seen or _safe_device(device_id) != device_id:
            continue
        seen.add(device_id)
        devices.append({"id": device_id, "label": match.group(2).strip() or device_id})
    return devices


def _safe_device(device):
    if not device or device == "auto":
        return "auto"
    if len(device) > 180 or not _DEVICE.match(device):
        return "auto"
    return device


def _filter(balance, eq):
    parts = []
    if abs(balance) >= 0.05:
        parts.append(f"stereotools=balance_out={balance:.2f}")
    if eq == "voice":
        parts.append("highpass=f=140")
        parts.append("treble=g=3")
    elif eq == "night":
        parts.append("bass=g=-3")
        parts.append("treble=g=-4")
    elif eq == "bass":
        parts.append("bass=g=7")
        parts.append("treble=g=-1")
    if not parts:
        return ""
    return "lavfi=[" + ",".join(parts) + "]"


def _runtime_socket():
    runtime = os.environ.get("XDG_RUNTIME_DIR") or ""
    if runtime and os.path.isdir(runtime):
        mode = os.stat(runtime).st_mode
        if mode & 0o077 == 0:
            return os.path.join(runtime, f"vela-{os.getpid()}.sock")
    folder = os.path.join(os.path.expanduser("~"), ".local", "share", "vela")
    os.makedirs(folder, mode=0o700, exist_ok=True)
    os.chmod(folder, 0o700)
    return os.path.join(folder, f"vela-{os.getpid()}.sock")


class Player:
    def __init__(self, volume=82, route=None):
        self.volume = max(0, min(100, int(volume)))
        self.muted = False
        self.paused = False
        self.allow_private = False
        route = route or {}
        self.device = _safe_device(route.get("device"))
        try:
            self.balance = max(-1.0, min(1.0, float(route.get("balance") or 0)))
        except (TypeError, ValueError):
            self.balance = 0.0
        self.eq = route.get("eq") if route.get("eq") in EQS else "flat"
        self.sock = _runtime_socket()
        self.proc = None
        self.url = ""
        self._request = 0

    def available(self):
        return shutil.which("mpv") is not None

    def devices(self):
        if not self.available():
            return []
        try:
            result = subprocess.run(
                ["mpv", "--audio-device=help"],
                capture_output=True,
                text=True,
                timeout=4,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            return []
        return parse_devices((result.stdout or "") + "\n" + (result.stderr or ""))

    def play(self, url, allow_private=None):
        if allow_private is None:
            allow_private = self.allow_private
        checked = safe_url(url, allow_private=allow_private)
        if not checked:
            self.url = ""
            return "That address is not a plain http or https stream."
        if not self.available():
            return "mpv is not installed. The installer adds it on Arch and Debian."
        self.allow_private = bool(allow_private)
        urls = [checked]
        if checked.startswith("http://"):
            upgraded = safe_url("https://" + checked[len("http://") :], allow_private=allow_private)
            if upgraded:
                urls = [upgraded, checked]
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
        command = [
            "mpv",
            "--no-config",
            "--no-video",
            "--no-terminal",
            "--really-quiet",
            "--idle=no",
            "--load-scripts=no",
            "--ytdl=no",
            "--load-unsafe-playlists=no",
            "--network-timeout=12",
            "--demuxer-lavf-o=protocol_whitelist=http,https,tcp,tls,crypto,hls",
            f"--volume={0 if self.muted else self.volume}",
            f"--input-ipc-server={self.sock}",
        ]
        if self.device != "auto":
            command.append(f"--audio-device={self.device}")
        filt = _filter(self.balance, self.eq)
        if filt:
            command.append(f"--af={filt}")
        command.extend(["--", url])
        self.proc = subprocess.Popen(
            command,
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
        if self.sock and os.path.exists(self.sock):
            try:
                os.remove(self.sock)
            except OSError:
                pass

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

    def set_device(self, device):
        self.device = _safe_device(device)
        if self.alive() and self.url:
            paused = self.paused
            self.play(self.url)
            if paused and self.alive():
                self.toggle()
        return self.device

    def set_balance(self, balance):
        try:
            self.balance = max(-1.0, min(1.0, round(float(balance), 2)))
        except (TypeError, ValueError):
            self.balance = 0.0
        self._apply_filters()
        return self.balance

    def set_eq(self, eq):
        self.eq = eq if eq in EQS else "flat"
        self._apply_filters()
        return self.eq

    def _apply_filters(self):
        if not self.alive():
            return
        filt = _filter(self.balance, self.eq)
        if filt:
            self.ipc(["af", "set", filt])
        else:
            self.ipc(["af", "clr", ""])

    def route_label(self):
        bits = []
        if self.device != "auto":
            bits.append("output")
        if self.eq != "flat":
            bits.append(self.eq)
        if abs(self.balance) >= 0.05:
            side = "L" if self.balance < 0 else "R"
            bits.append(f"{side}{int(round(abs(self.balance) * 100))}")
        return " · ".join(bits)

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
