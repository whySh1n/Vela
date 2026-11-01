"""Radio Browser directory client. Stdlib only."""

from __future__ import annotations

import json
import urllib.parse
import urllib.request

from player import safe_url

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
        checked = safe_url(candidate, allow_private=False)
        if checked.startswith("https://"):
            return checked
    for candidate in (resolved, url):
        checked = safe_url(candidate, allow_private=False)
        if checked.startswith("http://"):
            return checked
    return ""


def slim(row):
    if not isinstance(row, dict):
        return None
    station_id = _text(row.get("stationuuid"), 80)
    name = _text(row.get("name"), 120)
    stream = best_url(row)
    if not station_id or not name or not stream:
        return None
    homepage = safe_url(_text(row.get("homepage"), 200), allow_private=False)
    if not homepage.startswith("https://"):
        homepage = ""
    try:
        bitrate = max(0, int(row.get("bitrate") or 0))
    except (TypeError, ValueError):
        bitrate = 0
    return {
        "id": station_id,
        "name": name,
        "streamUrl": stream,
        "homepage": homepage,
        "tags": _text(row.get("tags"), 180),
        "country": _text(row.get("country"), 60),
        "countryCode": _text(row.get("countrycode"), 8).upper(),
        "language": _text(row.get("language"), 40),
        "codec": _text(row.get("codec"), 16).upper(),
        "bitrate": bitrate,
        "custom": False,
    }


def search(name="", tag="", country="", limit=40):
    name = str(name or "")[:80]
    tag = str(tag or "")[:40]
    country = str(country or "")[:60]
    try:
        limit = int(limit)
    except (TypeError, ValueError):
        limit = 40
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
                raw = response.read(2_000_001)
            if len(raw) > 2_000_000:
                continue
            payload = json.loads(raw.decode("utf-8"))
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
