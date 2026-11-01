"""Radio Browser directory client. Stdlib only."""

from __future__ import annotations

import json
import urllib.parse
import urllib.request

SERVERS = (
    "https://de1.api.radio-browser.info",
    "https://de2.api.radio-browser.info",
    "https://fi1.api.radio-browser.info",
)
UA = "Vela/1.0 (linux; quiet radio)"


def _text(value, limit=160):
    if not isinstance(value, str):
        return ""
    return value.strip()[:limit]


def best_url(row):
    url = _text(row.get("url"), 500)
    resolved = _text(row.get("url_resolved"), 500)
    for candidate in (url, resolved):
        if candidate.startswith("https://"):
            return candidate
    for candidate in (resolved, url):
        if candidate.startswith("http://"):
            return candidate
    return ""


def slim(row):
    if not isinstance(row, dict):
        return None
    station_id = _text(row.get("stationuuid"), 80)
    name = _text(row.get("name"), 120)
    stream = best_url(row)
    if not station_id or not name or not stream:
        return None
    homepage = _text(row.get("homepage"), 200)
    try:
        bitrate = max(0, int(row.get("bitrate") or 0))
    except (TypeError, ValueError):
        bitrate = 0
    return {
        "id": station_id,
        "name": name,
        "streamUrl": stream,
        "homepage": homepage if homepage.startswith("https://") else "",
        "tags": _text(row.get("tags"), 180),
        "country": _text(row.get("country"), 60),
        "countryCode": _text(row.get("countrycode"), 8).upper(),
        "language": _text(row.get("language"), 40),
        "codec": _text(row.get("codec"), 16).upper(),
        "bitrate": bitrate,
        "custom": False,
    }


def search(name="", tag="", country="", limit=40):
    params = {
        "hidebroken": "true",
        "limit": str(max(1, min(int(limit), 50))),
        "order": "votes",
        "reverse": "true",
    }
    if name:
        params["name"] = name
    if tag:
        params["tag"] = tag
    if country:
        params["country"] = country
    query = urllib.parse.urlencode(params)
    last = "The directory did not answer."
    for base in SERVERS:
        request = urllib.request.Request(
            f"{base}/json/stations/search?{query}",
            headers={"User-Agent": UA, "Accept": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=12) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (OSError, ValueError):
            continue
        if not isinstance(payload, list):
            continue
        seen = set()
        stations = []
        for row in payload:
            station = slim(row)
            if not station or station["id"] in seen:
                continue
            seen.add(station["id"])
            stations.append(station)
        return stations
    raise RuntimeError(last)
