"""Saved stations in ~/.config/vela/library.json."""

from __future__ import annotations

import json
import os
import tempfile

MAX_STATIONS = 200
EQS = ("flat", "voice", "night", "bass")


def path():
    root = os.environ.get("XDG_CONFIG_HOME") or os.path.join(os.path.expanduser("~"), ".config")
    folder = os.path.join(root, "vela")
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, "library.json")


def _station(value):
    if not isinstance(value, dict):
        return None
    name = str(value.get("name") or "").strip()[:120]
    stream = str(value.get("streamUrl") or "").strip()[:500]
    station_id = str(value.get("id") or "").strip()[:80]
    if not name or not stream.startswith(("http://", "https://")) or not station_id:
        return None
    try:
        bitrate = max(0, int(value.get("bitrate") or 0))
    except (TypeError, ValueError):
        bitrate = 0
    return {
        "id": station_id,
        "name": name,
        "streamUrl": stream,
        "homepage": str(value.get("homepage") or "")[:200],
        "tags": str(value.get("tags") or "")[:180],
        "country": str(value.get("country") or "")[:60],
        "countryCode": str(value.get("countryCode") or "")[:8],
        "language": str(value.get("language") or "")[:40],
        "codec": str(value.get("codec") or "")[:16],
        "bitrate": bitrate,
        "custom": bool(value.get("custom")),
    }


def _route(value):
    raw = value if isinstance(value, dict) else {}
    device = str(raw.get("device") or "auto").strip()[:180] or "auto"
    try:
        balance = float(raw.get("balance") or 0)
    except (TypeError, ValueError):
        balance = 0.0
    eq = str(raw.get("eq") or "flat")
    if eq not in EQS:
        eq = "flat"
    return {"device": device, "balance": round(max(-1.0, min(1.0, balance)), 2), "eq": eq}


def empty():
    return {"favorites": [], "custom": [], "volume": 82, "route": _route(None)}


def load():
    try:
        with open(path(), encoding="utf-8") as handle:
            raw = json.load(handle)
    except (OSError, ValueError):
        return empty()
    if not isinstance(raw, dict):
        return empty()
    favorites = []
    custom = []
    for item in raw.get("favorites") or []:
        station = _station(item)
        if station:
            favorites.append(station)
    for item in raw.get("custom") or []:
        station = _station(item)
        if station:
            station["custom"] = True
            custom.append(station)
    try:
        volume = int(raw.get("volume", 82))
    except (TypeError, ValueError):
        volume = 82
    return {
        "favorites": favorites[:MAX_STATIONS],
        "custom": custom[:MAX_STATIONS],
        "volume": max(0, min(100, volume)),
        "route": _route(raw.get("route")),
    }


def save(library):
    favorites = []
    for item in library.get("favorites") or []:
        station = _station(item)
        if station:
            favorites.append(station)
    custom = []
    for item in library.get("custom") or []:
        station = _station(item)
        if station:
            station["custom"] = True
            custom.append(station)
    try:
        volume = int(library.get("volume", 82))
    except (TypeError, ValueError):
        volume = 82
    current = load()
    route = _route(library["route"]) if isinstance(library, dict) and "route" in library else current["route"]
    payload = {
        "favorites": favorites[:MAX_STATIONS],
        "custom": custom[:MAX_STATIONS],
        "volume": max(0, min(100, volume)),
        "route": route,
    }
    target = path()
    folder = os.path.dirname(target)
    fd, temporary = tempfile.mkstemp(prefix="library.", dir=folder)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
            handle.write("\n")
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            try:
                os.remove(temporary)
            except OSError:
                pass
    return payload
