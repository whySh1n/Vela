"""Keyboard-first Vela. Run with `vela --term`."""

from __future__ import annotations

import curses
import time

import library
import player
import radio

SCOPES = ("dial", "saved", "mine")
GENRES = (
    "",
    "jazz",
    "classical",
    "ambient",
    "electronic",
    "rock",
    "soul",
    "folk",
    "news",
    "talk",
    "world",
)
SLEEP_STEPS = (0, 15, 30, 45, 60, 90)


def clip(text, width):
    text = str(text).replace("\n", " ")
    if width <= 0:
        return ""
    if len(text) <= width:
        return text
    if width == 1:
        return "…"
    return text[: width - 1] + "…"


def put(win, y, x, text, attr=0):
    height, width = win.getmaxyx()
    if y < 0 or y >= height or x >= width:
        return
    shown = clip(text, width - x - 1)
    try:
        win.addstr(y, x, shown, attr)
    except curses.error:
        pass


def place_line(station):
    tags = [part.strip() for part in station.get("tags", "").split(",") if part.strip()]
    bits = [station.get("country") or "", *tags[:2]]
    return " · ".join(bit for bit in bits if bit) or "your stream"


class App:
    def __init__(self):
        self.lib = library.load()
        self.player = player.Player(self.lib["volume"], self.lib.get("route"))
        self.outputs = []
        self.scope = "dial"
        self.tag = ""
        self.country = ""
        self.query = ""
        self.stations = []
        self.selected = 0
        self.current = None
        self.note = "tuning the dial…"
        self.error = ""
        self.help = False
        self.started = None
        self.sleep_at = None
        self.row_origin = 4

    def visible(self):
        if self.scope == "saved":
            rows = list(self.lib["favorites"])
        elif self.scope == "mine":
            rows = list(self.lib["custom"])
        else:
            rows = list(self.stations)
        if self.scope != "dial" and self.query:
            needle = self.query.lower()
            rows = [row for row in rows if needle in row["name"].lower()]
        return rows

    def search(self):
        self.note = "tuning the directory…"
        self.error = ""
        try:
            self.stations = radio.search(self.query, self.tag, self.country)
            self.note = f"{len(self.stations)} stations"
        except RuntimeError as exc:
            self.stations = []
            self.error = str(exc)
            self.note = ""
        self.selected = 0

    def play_index(self, index):
        rows = self.visible()
        if not rows:
            return
        index = max(0, min(index, len(rows) - 1))
        self.selected = index
        station = rows[index]
        self.current = station
        self.error = ""
        self.note = f"tuning {station['name']}…"
        message = self.player.play(station["streamUrl"], allow_private=bool(station.get("custom")))
        if message:
            self.error = message
            self.note = ""
            self.started = None
        else:
            self.started = time.time()
            self.note = "on air"
            self.remember_volume()

    def clamp(self):
        rows = self.visible()
        self.selected = max(0, min(self.selected, len(rows) - 1)) if rows else 0
        return rows

    def toggle_saved(self):
        rows = self.clamp()
        if not rows:
            return
        station = rows[self.selected]
        favorites = self.lib["favorites"]
        if any(item["id"] == station["id"] for item in favorites):
            self.lib["favorites"] = [item for item in favorites if item["id"] != station["id"]]
            self.note = "removed"
        else:
            self.lib["favorites"] = [station, *[item for item in favorites if item["id"] != station["id"]]][:200]
            self.note = "saved"
        library.save(self.lib)
        self.clamp()

    def add_custom(self, name, url):
        station = {
            "id": f"custom:{int(time.time())}",
            "name": name[:120] or "My stream",
            "streamUrl": url,
            "homepage": "",
            "tags": "",
            "country": "",
            "countryCode": "",
            "language": "",
            "codec": "",
            "bitrate": 0,
            "custom": True,
        }
        self.lib["custom"] = [station, *[item for item in self.lib["custom"] if item["id"] != station["id"]]][:200]
        self.lib["favorites"] = [station, *[item for item in self.lib["favorites"] if item["id"] != station["id"]]][:200]
        library.save(self.lib)
        self.scope = "mine"
        self.current = station
        self.note = f"added {station['name']}"
        message = self.player.play(url, allow_private=True)
        if message:
            self.error = message
        else:
            self.started = time.time()

    def remember_volume(self):
        self.lib["volume"] = self.player.volume
        library.save(self.lib)

    def remember_route(self):
        self.lib["route"] = {
            "device": self.player.device,
            "balance": self.player.balance,
            "eq": self.player.eq,
        }
        library.save(self.lib)

    def cycle_sleep(self):
        current = 0
        if self.sleep_at:
            remaining = max(0, int(self.sleep_at - time.time()))
            current = min(SLEEP_STEPS, key=lambda step: abs(step * 60 - remaining) if step else 10**9)
        index = SLEEP_STEPS.index(current) if current in SLEEP_STEPS else 0
        nxt = SLEEP_STEPS[(index + 1) % len(SLEEP_STEPS)]
        self.sleep_at = None if nxt == 0 else time.time() + nxt * 60
        self.note = "sleep off" if nxt == 0 else f"sleep {nxt}m"

    def tick(self):
        if self.sleep_at and time.time() >= self.sleep_at:
            self.player.toggle() if self.player.alive() and not self.player.paused else self.player.stop()
            self.sleep_at = None
            self.note = "the dial rested"
        if self.current and self.started and not self.player.alive() and not self.player.paused and not self.error:
            self.error = "The stream ended."
            self.started = None


def init_colors():
    if not curses.has_colors():
        return
    curses.start_color()
    curses.use_default_colors()
    if curses.COLORS >= 256:
        curses.init_pair(1, 214, -1)
        curses.init_pair(2, 245, -1)
        curses.init_pair(3, 16, 214)
    else:
        curses.init_pair(1, curses.COLOR_YELLOW, -1)
        curses.init_pair(2, curses.COLOR_WHITE, -1)
        curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_YELLOW)


def prompt(stdscr, label):
    curses.curs_set(1)
    curses.echo()
    height, width = stdscr.getmaxyx()
    try:
        stdscr.addstr(height - 1, 0, " " * max(0, width - 1))
    except curses.error:
        pass
    put(stdscr, height - 1, 0, label)
    stdscr.refresh()
    try:
        raw = stdscr.getstr(height - 1, min(len(label), width - 2), max(1, width - len(label) - 2))
    except curses.error:
        raw = b""
    curses.noecho()
    curses.curs_set(0)
    return raw.decode("utf-8", "replace").strip()


def draw(stdscr, app: App):
    stdscr.erase()
    height, width = stdscr.getmaxyx()
    if height < 12 or width < 48:
        put(stdscr, 0, 0, "Make the terminal a little larger.")
        stdscr.refresh()
        return
    amber = curses.color_pair(1) if curses.has_colors() else curses.A_BOLD
    muted = curses.color_pair(2) if curses.has_colors() else curses.A_DIM
    hot = curses.color_pair(3) if curses.has_colors() else curses.A_REVERSE

    put(stdscr, 0, 0, "vela", amber | curses.A_BOLD)
    put(stdscr, 0, 6, "terminal", muted)
    header = f"{app.scope}"
    if app.tag:
        header += f"  {app.tag}"
    if app.country:
        header += f"  {app.country}"
    if app.query:
        header += f"  /{app.query}"
    put(stdscr, 0, max(16, width - len(header) - 1), header, muted)

    genres = "  ".join(genre or "top" for genre in GENRES)
    put(stdscr, 1, 0, genres, muted)
    put(stdscr, 2, 0, "dial   saved   mine    a add    ? keys", muted)

    rows = app.visible()
    list_top = 4
    list_bottom = height - 6
    app.row_origin = list_top
    if app.help:
        lines = [
            "space  play or pause",
            "j k    move",
            "enter  play",
            "f      save",
            "n p    next or previous",
            "m      mute",
            "o      next output",
            "[ ]    balance",
            "e      tone: flat, voice, night, bass",
            "s      sleep",
            "/      search",
            "a      add a stream",
            ":place and :tag from the search prompt",
            "q      quit",
            "any key closes this card",
        ]
        top = max(3, (height - len(lines)) // 2)
        for index, line in enumerate(lines):
            put(stdscr, top + index, 4, line, amber if index == 0 else 0)
        stdscr.refresh()
        return

    if not rows:
        message = app.error or app.note or "Nothing on this dial."
        put(stdscr, list_top, 2, message, muted)
    else:
        window = max(1, list_bottom - list_top)
        start = 0
        if app.selected >= window:
            start = app.selected - window + 1
        for offset in range(window):
            index = start + offset
            if index >= len(rows):
                break
            station = rows[index]
            y = list_top + offset
            saved = any(item["id"] == station["id"] for item in app.lib["favorites"])
            mark = ">" if index == app.selected else " "
            star = "*" if saved else " "
            rate = str(station["bitrate"]) if station.get("bitrate") else station.get("countryCode") or ""
            name_width = max(8, width - 16)
            line = f"{mark} {star} {clip(station['name'], name_width)}"
            attr = hot if index == app.selected else 0
            put(stdscr, y, 0, line, attr)
            put(stdscr, y, max(0, width - 8), rate, muted)

    now_y = height - 5
    name = app.current["name"] if app.current else "nothing on the air"
    detail = place_line(app.current) if app.current else "pick a station"
    vol = 0 if app.player.muted else app.player.volume
    listened = ""
    if app.started and app.player.alive():
        seconds = int(time.time() - app.started)
        listened = f"  {seconds // 60}:{seconds % 60:02d}"
    sleep = ""
    if app.sleep_at:
        left = max(0, int(app.sleep_at - time.time()))
        sleep = f"  sleep {left // 60}:{left % 60:02d}"
    state = "paused" if app.player.paused else "playing" if app.player.alive() else "idle"
    put(stdscr, now_y, 0, "now", muted)
    put(stdscr, now_y + 1, 0, name, amber if app.player.alive() else 0)
    route = app.player.route_label()
    if route:
        detail = f"{detail}  ·  {route}"
    put(stdscr, now_y + 2, 0, f"{detail}  ·  {state}  ·  vol {vol}{sleep}{listened}", muted)
    footer_note = app.error or app.note
    put(stdscr, height - 2, 0, footer_note, amber if app.error else muted)
    put(stdscr, height - 1, 0, "j k move   enter play   f save   space pause   / search   q quit", muted)
    stdscr.refresh()


def handle(stdscr, app: App, key):
    if app.help:
        app.help = False
        return
    rows = app.visible()
    if key in (ord("q"), ord("Q")):
        app.player.stop()
        raise SystemExit
    if key == ord("?"):
        app.help = True
        return
    if key in (curses.KEY_DOWN, ord("j")):
        if rows:
            app.selected = min(len(rows) - 1, app.selected + 1)
        return
    if key in (curses.KEY_UP, ord("k")):
        app.selected = max(0, app.selected - 1)
        return
    if key in (curses.KEY_ENTER, 10, 13):
        app.play_index(app.selected)
        return
    if key == ord(" "):
        if app.player.alive():
            app.player.toggle()
            app.note = "paused" if app.player.paused else "on air"
        else:
            app.play_index(app.selected)
        return
    if key == ord("f"):
        app.toggle_saved()
        return
    if key == ord("n"):
        app.play_index(app.selected + 1)
        return
    if key == ord("p"):
        app.play_index(max(0, app.selected - 1))
        return
    if key == ord("m"):
        app.player.toggle_mute()
        app.remember_volume()
        app.note = "muted" if app.player.muted else "sound on"
        return
    if key == ord("o"):
        if not app.outputs:
            app.note = "reading outputs…"
            app.outputs = app.player.devices() or [{"id": "auto", "label": "System default"}]
        ids = [item["id"] for item in app.outputs]
        index = ids.index(app.player.device) if app.player.device in ids else -1
        nxt = app.outputs[(index + 1) % len(app.outputs)]
        app.player.set_device(nxt["id"])
        app.remember_route()
        app.note = nxt["label"]
        return
    if key == ord("["):
        app.player.set_balance(app.player.balance - 0.2)
        app.remember_route()
        app.note = "balance center" if abs(app.player.balance) < 0.05 else f"balance {'left' if app.player.balance < 0 else 'right'}"
        return
    if key == ord("]"):
        app.player.set_balance(app.player.balance + 0.2)
        app.remember_route()
        app.note = "balance center" if abs(app.player.balance) < 0.05 else f"balance {'left' if app.player.balance < 0 else 'right'}"
        return
    if key == ord("e"):
        order = ("flat", "voice", "night", "bass")
        index = order.index(app.player.eq) if app.player.eq in order else 0
        app.player.set_eq(order[(index + 1) % len(order)])
        app.remember_route()
        app.note = f"tone {app.player.eq}"
        return
    if key == ord("s"):
        app.cycle_sleep()
        return
    if key in (ord("+"), ord("=")):
        app.player.set_volume(app.player.volume + 5)
        app.remember_volume()
        return
    if key in (ord("-"), ord("_")):
        app.player.set_volume(app.player.volume - 5)
        app.remember_volume()
        return
    if key == ord("a"):
        name = prompt(stdscr, "name  ")
        if not name:
            return
        url = prompt(stdscr, "url   ")
        if not url.startswith(("http://", "https://")):
            app.error = "The stream needs an http or https address."
            return
        app.add_custom(name, url)
        return
    if key == ord("/"):
        text = prompt(stdscr, "/ ")
        if text.startswith(":place"):
            app.country = text[6:].strip()
            app.scope = "dial"
        elif text.startswith(":tag"):
            app.tag = text[4:].strip().lower()
            app.scope = "dial"
        elif text.startswith(":add"):
            rest = text[4:].strip()
            if "|" in rest:
                name, url = [part.strip() for part in rest.split("|", 1)]
            else:
                bits = rest.rsplit(" ", 1)
                if len(bits) == 2 and bits[1].startswith("http"):
                    name, url = bits[0], bits[1]
                else:
                    app.error = "use :add Name | https://stream"
                    return
            if url.startswith(("http://", "https://")):
                app.add_custom(name, url)
            else:
                app.error = "The stream needs an http or https address."
            return
        else:
            app.query = text[1:].strip() if text.startswith("/") else text
            app.scope = "dial"
        app.search()
        return
    if key == ord("1"):
        app.scope = SCOPES[(SCOPES.index(app.scope) + 1) % len(SCOPES)]
        app.selected = 0
        return
    if key == curses.KEY_MOUSE:
        try:
            _, _x, y, _, _state = curses.getmouse()
        except curses.error:
            return
        rows = app.visible()
        index = y - app.row_origin
        # Mouse index is only right when the list is not scrolled. Close enough
        # for a click near the top of a short list; keyboard stays exact.
        if 0 <= index < len(rows) and app.selected < (curses.LINES - 10):
            app.play_index(index)


def run(stdscr):
    curses.curs_set(0)
    stdscr.keypad(True)
    stdscr.timeout(250)
    try:
        curses.mousemask(curses.BUTTON1_CLICKED)
    except curses.error:
        pass
    init_colors()
    app = App()
    draw(stdscr, app)
    app.search()
    while True:
        app.tick()
        draw(stdscr, app)
        key = stdscr.getch()
        if key == -1:
            continue
        handle(stdscr, app, key)


def main():
    try:
        curses.wrapper(run)
    except SystemExit:
        pass
    except KeyboardInterrupt:
        pass
