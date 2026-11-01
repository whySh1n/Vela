"""Vela's window. Qt on the machine you are using. No browser."""

from __future__ import annotations

import sys
import threading
import time

import library
import player
import radio

GENRES = (
    ("", "Top"),
    ("jazz", "Jazz"),
    ("classical", "Classical"),
    ("ambient", "Ambient"),
    ("electronic", "Electronic"),
    ("rock", "Rock"),
    ("soul", "Soul"),
    ("folk", "Folk"),
    ("news", "News"),
    ("talk", "Talk"),
    ("world", "World"),
)
EQS = (("flat", "Flat"), ("voice", "Voice"), ("night", "Night"), ("bass", "Bass"))
SLEEP = (0, 15, 30, 45, 60, 90)

QSS = """
QMainWindow, QWidget#app { background: #141311; color: #efe8dc; }
QWidget#stage { background: #191816; }
QLabel, QListWidget { background: transparent; color: #efe8dc; }
QFrame#line { background: #2c2924; max-height: 1px; min-height: 1px; border: none; }
QLineEdit {
  background: #1e1c19; color: #efe8dc; border: none; border-radius: 10px;
  padding: 10px 14px; min-height: 20px;
  selection-background-color: #3a342c; selection-color: #efe8dc;
}
QLineEdit:focus { background: #24211d; }
QWidget#finder { background: #1e1c19; border-radius: 10px; }
QLineEdit#finderField, QLineEdit#finderField:focus {
  background: transparent; border: none; border-radius: 0; padding: 10px 14px;
}
QFrame#finderRule { background: #2c2924; border: none; max-width: 1px; min-width: 1px; }
QListWidget { border: none; outline: none; }
QListWidget::item { border: none; }
QListWidget::item:selected { background: #221f1b; }
QPushButton {
  background: transparent; color: #9a9082; border: none;
  border-radius: 8px; padding: 8px 12px; min-height: 20px;
}
QPushButton:hover { color: #efe8dc; background: #221f1b; }
QPushButton:checked { color: #efe8dc; background: transparent; }
QPushButton#ghost { padding: 8px 10px; }
QPushButton#ghost:checked { color: #e6b15a; background: transparent; }
QPushButton#play {
  background: #e6b15a; color: #2a2114; border: none; border-radius: 26px;
  min-width: 52px; max-width: 52px; min-height: 52px; max-height: 52px;
  font-size: 16px; padding: 0;
}
QPushButton#play:hover { background: #efc27a; color: #2a2114; }
QPushButton#chip {
  background: transparent; color: #9a9082; border: none; border-radius: 8px;
  padding: 6px 10px;
}
QPushButton#chip:hover { color: #efe8dc; background: #221f1b; }
QPushButton#chip:checked { color: #e6b15a; background: #221f1b; }
QComboBox {
  background: #1e1c19; border: none; border-radius: 8px;
  padding: 8px 12px; min-height: 20px; color: #efe8dc;
}
QComboBox::drop-down { border: none; width: 22px; }
QComboBox QAbstractItemView {
  background: #1e1c19; color: #efe8dc; border: none;
  selection-background-color: #2a261f; outline: none;
}
QSlider::groove:horizontal { height: 2px; background: #2c2924; border: none; }
QSlider::sub-page:horizontal { background: #e6b15a; }
QSlider::handle:horizontal {
  background: #efe8dc; border: none; width: 12px; height: 12px; margin: -5px 0; border-radius: 6px;
}
QLabel#eyebrow { color: #e6b15a; font-size: 11px; letter-spacing: 2px; }
QLabel#title { font-size: 26px; font-weight: 500; }
QLabel#muted, QLabel#meta { color: #9a9082; }
QLabel#mark {
  background: #141311; color: #e6b15a; border: none; border-radius: 18px; font-size: 26px;
}
QScrollBar:vertical { background: transparent; width: 8px; margin: 0; }
QScrollBar::handle:vertical { background: #2c2924; border-radius: 4px; min-height: 24px; }
QScrollBar:horizontal { background: transparent; height: 8px; margin: 0; }
QScrollBar::handle:horizontal { background: #2c2924; border-radius: 4px; min-width: 24px; }
QScrollBar::add-line, QScrollBar::sub-line, QScrollBar::add-page, QScrollBar::sub-page, QScrollBar::corner {
  background: transparent; border: none; width: 0; height: 0;
}
"""


def monogram(name):
    parts = []
    token = []
    for ch in name:
        if ch.isalnum() or ch == " ":
            token.append(ch)
        else:
            token.append(" ")
    for part in "".join(token).split():
        parts.append(part)
    if not parts:
        return "·"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[1][0]).upper()


def short_country(country):
    text = country[4:] if country.startswith("The ") else country
    text = text.replace(" Of America", "").replace(" Of Great Britain And Northern Ireland", "")
    return text


def place_line(station):
    tags = [part.strip() for part in station.get("tags", "").split(",") if part.strip() and len(part.strip()) < 18]
    bits = [short_country(station.get("country") or ""), *tags[:2]]
    return " · ".join(bit for bit in bits if bit) or ("Custom stream" if station.get("custom") else "Live")


def tech_line(station):
    bits = []
    if station.get("codec"):
        bits.append(station["codec"])
    if station.get("bitrate"):
        bits.append(f"{station['bitrate']} kbps")
    if station.get("country"):
        bits.append(short_country(station["country"]))
    return " · ".join(bits) or "Custom stream"


def main(argv=None):
    argv = list(sys.argv if argv is None else argv)
    try:
        from PySide6.QtCore import Qt, QTimer, QObject, Signal, QSize
        from PySide6.QtGui import QColor, QFont, QKeyEvent, QPalette
        from PySide6.QtWidgets import (
            QApplication,
            QButtonGroup,
            QComboBox,
            QDialog,
            QFrame,
            QHBoxLayout,
            QLabel,
            QLineEdit,
            QListWidget,
            QListWidgetItem,
            QMainWindow,
            QPushButton,
            QSlider,
            QVBoxLayout,
            QWidget,
        )
    except ImportError:
        print("Vela's window needs PySide6.")
        print("Arch:    sudo pacman -S pyside6")
        print("Debian:  sudo apt install python3-pyside6.qtwidgets python3-pyside6.qtgui python3-pyside6.qtcore")
        print("Or:      python3 -m pip install --user PySide6-Essentials")
        print("You can still listen with:  vela --term")
        return 1

    class Bridge(QObject):
        results = Signal(int, object, str)
        played = Signal(int, str)
        devices = Signal(object)

    class Window(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("Vela")
            self.resize(1120, 720)
            self.setMinimumSize(860, 560)
            self.lib = library.load()
            self.player = player.Player(self.lib.get("volume", 82), self.lib.get("route"))
            self.lock = threading.Lock()
            self.bridge = Bridge()
            self.bridge.results.connect(self.on_results)
            self.bridge.played.connect(self.on_played)
            self.bridge.devices.connect(self.on_devices)
            self.scope = "dial"
            self.tag = ""
            self.query = ""
            self.country = ""
            self.stations = []
            self.selected = 0
            self.current = None
            self.status = "idle"
            self.error = ""
            self.token = 0
            self.play_token = 0
            self.started = None
            self.sleep_at = None
            self.outputs = [{"id": "auto", "label": "System default"}]
            self._build()
            self.fill()
            self.refresh_stage()
            self.search_timer = QTimer(self)
            self.search_timer.setSingleShot(True)
            self.search_timer.timeout.connect(self.search)
            self.clock = QTimer(self)
            self.clock.timeout.connect(self.tick)
            self.clock.start(1000)
            threading.Thread(target=self._load_devices, daemon=True).start()
            self.search()

        def _build(self):
            root = QWidget()
            root.setObjectName("app")
            self.setCentralWidget(root)
            outer = QVBoxLayout(root)
            outer.setContentsMargins(0, 0, 0, 0)
            outer.setSpacing(0)

            header = QWidget()
            bar = QHBoxLayout(header)
            bar.setContentsMargins(16, 10, 12, 10)
            mark = QLabel("V")
            mark.setFixedSize(28, 28)
            mark.setAlignment(Qt.AlignCenter)
            mark.setStyleSheet("background:#e8a04a;color:#2a1c0a;border-radius:4px;font-weight:600;")
            titles = QVBoxLayout()
            titles.setSpacing(0)
            name = QLabel("Vela")
            name.setStyleSheet("font-size:15px;font-weight:600;")
            self.header_status = QLabel("QUIET")
            self.header_status.setObjectName("muted")
            self.header_status.setStyleSheet("color:#a39882;font-size:10px;letter-spacing:1px;")
            titles.addWidget(name)
            titles.addWidget(self.header_status)
            bar.addWidget(mark)
            bar.addSpacing(8)
            bar.addLayout(titles)
            bar.addStretch(1)
            self.sleep_btn = QPushButton("Sleep")
            self.sleep_btn.clicked.connect(self.cycle_sleep)
            self.mute_btn = QPushButton("Mute")
            self.mute_btn.clicked.connect(self.toggle_mute)
            bar.addWidget(self.sleep_btn)
            bar.addWidget(self.mute_btn)
            outer.addWidget(header)
            outer.addWidget(self._rule())

            body = QHBoxLayout()
            body.setContentsMargins(0, 0, 0, 0)
            body.setSpacing(0)
            outer.addLayout(body, 1)

            left = QWidget()
            left_box = QVBoxLayout(left)
            left_box.setContentsMargins(16, 12, 16, 8)
            left_box.setSpacing(8)
            finder = QWidget()
            finder.setObjectName("finder")
            filters = QHBoxLayout(finder)
            filters.setContentsMargins(0, 0, 0, 0)
            filters.setSpacing(0)
            self.search_box = QLineEdit()
            self.search_box.setObjectName("finderField")
            self.search_box.setPlaceholderText("Search stations")
            self.search_box.textChanged.connect(self.on_query)
            rule_host = QWidget()
            rule_host.setFixedWidth(1)
            rule_box = QVBoxLayout(rule_host)
            rule_box.setContentsMargins(0, 12, 0, 12)
            rule_box.setSpacing(0)
            rule = QFrame()
            rule.setObjectName("finderRule")
            rule_box.addWidget(rule)
            self.country_box = QLineEdit()
            self.country_box.setObjectName("finderField")
            self.country_box.setPlaceholderText("Country")
            self.country_box.setFixedWidth(168)
            self.country_box.textChanged.connect(self.on_country)
            filters.addWidget(self.search_box, 1)
            filters.addWidget(rule_host)
            filters.addWidget(self.country_box)
            left_box.addWidget(finder)

            self.genre_group = QButtonGroup(self)
            self.genre_group.setExclusive(True)
            for chunk in (GENRES[:6], GENRES[6:]):
                genre_row = QHBoxLayout()
                genre_row.setContentsMargins(0, 0, 0, 0)
                genre_row.setSpacing(2)
                for genre_id, label in chunk:
                    button = QPushButton(label)
                    button.setObjectName("chip")
                    button.setFlat(True)
                    button.setCursor(Qt.PointingHandCursor)
                    button.setCheckable(True)
                    button.setChecked(genre_id == "")
                    button.clicked.connect(lambda _=False, gid=genre_id: self.on_tag(gid))
                    self.genre_group.addButton(button)
                    genre_row.addWidget(button)
                genre_row.addStretch(1)
                left_box.addLayout(genre_row)

            scopes = QHBoxLayout()
            self.scope_group = QButtonGroup(self)
            self.scope_group.setExclusive(True)
            self.scope_buttons = {}
            for key, label in (("dial", "Dial"), ("saved", "Saved"), ("mine", "Mine")):
                button = QPushButton(label)
                button.setObjectName("ghost")
                button.setFlat(True)
                button.setCursor(Qt.PointingHandCursor)
                button.setCheckable(True)
                button.setChecked(key == "dial")
                button.clicked.connect(lambda _=False, k=key: self.on_scope(k))
                self.scope_group.addButton(button)
                self.scope_buttons[key] = button
                scopes.addWidget(button)
            scopes.addStretch(1)
            add = QPushButton("Add")
            add.clicked.connect(self.add_dialog)
            scopes.addWidget(add)
            left_box.addLayout(scopes)

            self.count = QLabel("DIRECTORY")
            self.count.setObjectName("muted")
            self.count.setStyleSheet("color:#a39882;font-size:10px;letter-spacing:1px;")
            left_box.addWidget(self.count)
            self.list = QListWidget()
            self.list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.list.itemActivated.connect(self.on_activate)
            self.list.currentRowChanged.connect(self.on_row)
            left_box.addWidget(self.list, 1)
            body.addWidget(left, 1)

            stage = QWidget()
            stage.setObjectName("stage")
            stage.setFixedWidth(340)
            side = QVBoxLayout(stage)
            side.setContentsMargins(22, 22, 22, 16)
            side.setSpacing(8)
            self.eyebrow = QLabel("QUIET")
            self.eyebrow.setObjectName("eyebrow")
            self.mark = QLabel("·")
            self.mark.setObjectName("mark")
            self.mark.setAlignment(Qt.AlignCenter)
            self.mark.setFixedSize(88, 88)
            self.title = QLabel("No station")
            self.title.setObjectName("title")
            self.title.setWordWrap(True)
            self.meta = QLabel("Pick a station from the directory.")
            self.meta.setObjectName("meta")
            self.meta.setWordWrap(True)
            self.err = QLabel("")
            self.err.setWordWrap(True)
            self.err.hide()
            transport = QHBoxLayout()
            prev = QPushButton("Prev")
            prev.clicked.connect(lambda: self.step(-1))
            self.play_btn = QPushButton("▶")
            self.play_btn.setObjectName("play")
            self.play_btn.clicked.connect(self.toggle)
            nxt = QPushButton("Next")
            nxt.clicked.connect(lambda: self.step(1))
            transport.addWidget(prev)
            transport.addWidget(self.play_btn)
            transport.addWidget(nxt)
            transport.addStretch(1)
            self.elapsed = QLabel("")
            self.elapsed.setObjectName("muted")
            transport.addWidget(self.elapsed)
            vol = QHBoxLayout()
            self.vol_label = QLabel(str(self.player.volume))
            self.vol_label.setFixedWidth(28)
            self.vol = QSlider(Qt.Horizontal)
            self.vol.setRange(0, 100)
            self.vol.setValue(self.player.volume)
            self.vol.valueChanged.connect(self.on_volume)
            vol.addWidget(self.vol_label)
            vol.addWidget(self.vol, 1)
            self.route = QLabel("Output · system")
            self.route.setObjectName("muted")
            self.route.setWordWrap(True)
            self.device_box = QComboBox()
            self.device_box.addItem("System default", "auto")
            self.device_box.currentIndexChanged.connect(self.on_device)
            self.balance = QSlider(Qt.Horizontal)
            self.balance.setRange(-10, 10)
            self.balance.setValue(int(round(self.player.balance * 10)))
            self.balance.valueChanged.connect(self.on_balance)
            self.balance_label = QLabel(self._balance_text())
            self.balance_label.setObjectName("muted")
            self.eq_box = QComboBox()
            for key, label in EQS:
                self.eq_box.addItem(label, key)
            index = self.eq_box.findData(self.player.eq)
            if index >= 0:
                self.eq_box.setCurrentIndex(index)
            self.eq_box.currentIndexChanged.connect(self.on_eq)
            side.addWidget(self.eyebrow)
            side.addWidget(self.mark)
            side.addWidget(self.title)
            side.addWidget(self.meta)
            side.addWidget(self.err)
            side.addStretch(1)
            side.addLayout(transport)
            side.addLayout(vol)
            side.addWidget(self._rule())
            side.addWidget(QLabel("Output"))
            side.addWidget(self.device_box)
            side.addWidget(self.balance_label)
            side.addWidget(self.balance)
            side.addWidget(QLabel("Tone"))
            side.addWidget(self.eq_box)
            side.addWidget(self.route)
            body.addWidget(stage)
            self._sync_route_label()

        def _rule(self):
            rule = QFrame()
            rule.setObjectName("line")
            rule.setFrameShape(QFrame.NoFrame)
            return rule

        def _balance_text(self):
            value = self.player.balance
            if abs(value) < 0.05:
                return "Balance · center"
            side = "left" if value < 0 else "right"
            return f"Balance · {side} {int(round(abs(value) * 100))}"

        def _sync_route_label(self):
            label = "system"
            for item in self.outputs:
                if item["id"] == self.player.device:
                    label = item["label"]
                    break
            tone = self.player.eq
            self.route.setText(f"{label} · {tone}")

        def visible(self):
            if self.scope == "saved":
                rows = list(self.lib["favorites"])
            elif self.scope == "mine":
                rows = list(self.lib["custom"])
            else:
                rows = list(self.stations)
            if self.scope != "dial" and self.query.strip():
                needle = self.query.strip().lower()
                rows = [row for row in rows if needle in f"{row['name']} {row.get('country','')} {row.get('tags','')}".lower()]
            return rows

        def saved_ids(self):
            return {item["id"] for item in self.lib["favorites"]}

        def fill(self):
            rows = self.visible()
            self.list.blockSignals(True)
            self.list.clear()
            saved = self.saved_ids()
            for index, station in enumerate(rows):
                item = QListWidgetItem()
                item.setData(Qt.UserRole, station["id"])
                item.setSizeHint(QSize(0, 58))
                self.list.addItem(item)
                self.list.setItemWidget(item, self._row(station, index, station["id"] in saved))
            if rows:
                self.selected = max(0, min(self.selected, len(rows) - 1))
                self.list.setCurrentRow(self.selected)
            self.list.blockSignals(False)
            self.scope_buttons["saved"].setText(f"Saved  {len(self.lib['favorites']) or ''}".strip())
            self.scope_buttons["mine"].setText(f"Mine  {len(self.lib['custom']) or ''}".strip())
            label = {"dial": "DIRECTORY", "saved": "SAVED", "mine": "YOUR STREAMS"}[self.scope]
            if self.scope == "dial" and self.status == "connecting" and not rows:
                self.count.setText("SEARCHING")
            else:
                self.count.setText(f"{label}    {len(rows)}")

        def _row(self, station, index, saved):
            wrap = QWidget()
            wrap.setStyleSheet("background:transparent;")
            box = QHBoxLayout(wrap)
            box.setContentsMargins(8, 4, 4, 4)
            text = QVBoxLayout()
            text.setSpacing(0)
            title = QLabel(station["name"])
            title.setStyleSheet("font-size:14px;background:transparent;")
            sub = QLabel(place_line(station))
            sub.setStyleSheet("color:#a39882;font-size:12px;background:transparent;")
            text.addWidget(title)
            text.addWidget(sub)
            box.addLayout(text, 1)
            rate = station.get("bitrate")
            if rate:
                meta = QLabel(f"{rate}k")
                meta.setStyleSheet("color:#a39882;font-size:12px;background:transparent;")
                box.addWidget(meta)
            star = QPushButton("★" if saved else "☆")
            star.setFixedWidth(36)
            star.setStyleSheet("color:#e8a04a;font-size:16px;background:transparent;" if saved else "background:transparent;")
            star.clicked.connect(lambda _=False, i=index: self.toggle_saved(i))
            box.addWidget(star)
            return wrap

        def on_query(self, text):
            self.query = text
            self.search_timer.start(280)

        def on_country(self, text):
            self.country = text
            self.scope = "dial"
            self.scope_buttons["dial"].setChecked(True)
            self.search_timer.start(280)

        def on_tag(self, genre_id):
            self.tag = genre_id
            self.scope = "dial"
            self.scope_buttons["dial"].setChecked(True)
            self.selected = 0
            self.search()

        def on_scope(self, key):
            self.scope = key
            self.selected = 0
            if key == "dial":
                self.search()
            else:
                self.fill()

        def on_row(self, row):
            if row >= 0:
                self.selected = row

        def on_activate(self, _item):
            self.play_index(self.list.currentRow())

        def search(self):
            self.token += 1
            token = self.token
            if self.scope != "dial":
                self.fill()
                return
            name, tag, country = self.query.strip(), self.tag, self.country.strip()
            self.count.setText("SEARCHING")

            def work():
                try:
                    rows = radio.search(name, tag, country)
                    err = ""
                except RuntimeError as exc:
                    rows, err = [], str(exc)
                self.bridge.results.emit(token, rows, err)

            threading.Thread(target=work, daemon=True).start()

        def on_results(self, token, rows, err):
            if token != self.token or self.scope != "dial":
                return
            self.stations = list(rows)
            self.error = err
            self.selected = 0
            self.fill()
            if err and not rows:
                self.err.setText(err)
                self.err.show()

        def play_index(self, index):
            rows = self.visible()
            if not rows:
                return
            index = max(0, min(index, len(rows) - 1))
            self.selected = index
            self.list.setCurrentRow(index)
            station = rows[index]
            self.current = station
            self.status = "connecting"
            self.error = ""
            self.started = None
            self.refresh_stage()
            self.play_token += 1
            token = self.play_token
            url = station["streamUrl"]

            def work():
                with self.lock:
                    if token != self.play_token:
                        return
                    message = self.player.play(url)
                self.bridge.played.emit(token, message or "")

            threading.Thread(target=work, daemon=True).start()

        def on_played(self, token, message):
            if token != self.play_token:
                return
            if message:
                self.status = "error"
                self.error = message
                self.started = None
            else:
                self.status = "playing"
                self.error = ""
                self.started = time.time()
            self.refresh_stage()

        def toggle(self):
            with self.lock:
                alive = self.player.alive()
                paused = self.player.paused
            if alive:
                with self.lock:
                    self.player.toggle()
                    paused = self.player.paused
                self.status = "paused" if paused else "playing"
                self.refresh_stage()
                return
            if self.current:
                self.play_index(self.selected if self.visible() and self.visible()[self.selected]["id"] == self.current["id"] else 0)
            else:
                self.play_index(self.selected)

        def step(self, delta):
            rows = self.visible()
            if not rows:
                return
            start = self.selected
            if self.current:
                for index, station in enumerate(rows):
                    if station["id"] == self.current["id"]:
                        start = index
                        break
            self.play_index(max(0, min(len(rows) - 1, start + delta)))

        def toggle_saved(self, index):
            rows = self.visible()
            if index < 0 or index >= len(rows):
                return
            station = rows[index]
            favorites = self.lib["favorites"]
            if any(item["id"] == station["id"] for item in favorites):
                self.lib["favorites"] = [item for item in favorites if item["id"] != station["id"]]
            else:
                self.lib["favorites"] = [station, *[item for item in favorites if item["id"] != station["id"]]][:200]
            library.save(self.lib)
            self.fill()

        def toggle_mute(self):
            with self.lock:
                self.player.toggle_mute()
                muted = self.player.muted
                volume = self.player.volume
            self.mute_btn.setText("Muted" if muted else "Mute")
            self.vol.blockSignals(True)
            self.vol.setValue(0 if muted else volume)
            self.vol.blockSignals(False)
            self.vol_label.setText("0" if muted else str(volume))

        def on_volume(self, value):
            with self.lock:
                self.player.set_volume(value)
            self.vol_label.setText(str(value))
            self.mute_btn.setText("Mute")
            self.lib["volume"] = value
            library.save(self.lib)

        def cycle_sleep(self):
            current = 0
            if self.sleep_at:
                left = max(0, int(self.sleep_at - time.time()))
                current = min(SLEEP, key=lambda step: abs(step * 60 - left) if step else 10**9)
            index = SLEEP.index(current) if current in SLEEP else 0
            nxt = SLEEP[(index + 1) % len(SLEEP)]
            self.sleep_at = None if nxt == 0 else time.time() + nxt * 60
            self.sleep_btn.setText("Sleep" if nxt == 0 else f"{nxt}m")

        def on_device(self, index):
            if index < 0:
                return
            device = self.device_box.currentData()
            if not device or device == self.player.device:
                return
            self.play_token += 1
            token = self.play_token

            def work():
                with self.lock:
                    self.player.set_device(device)
                self.bridge.played.emit(token, "")

            self.player.device = device
            self._remember_route()
            if self.player.url:
                threading.Thread(target=work, daemon=True).start()
            else:
                with self.lock:
                    self.player.device = device
                self._sync_route_label()

        def on_balance(self, value):
            with self.lock:
                self.player.set_balance(value / 10)
            self.balance_label.setText(self._balance_text())
            self._remember_route()

        def on_eq(self, _index):
            eq = self.eq_box.currentData()
            with self.lock:
                self.player.set_eq(eq)
            self._remember_route()

        def _remember_route(self):
            self.lib["route"] = {
                "device": self.player.device,
                "balance": self.player.balance,
                "eq": self.player.eq,
            }
            library.save(self.lib)
            self._sync_route_label()

        def _load_devices(self):
            with self.lock:
                found = self.player.devices()
            if not found:
                found = [{"id": "auto", "label": "System default"}]
            elif not any(item["id"] == "auto" for item in found):
                found = [{"id": "auto", "label": "System default"}, *found]
            self.bridge.devices.emit(found)

        def on_devices(self, found):
            self.outputs = list(found)
            self.device_box.blockSignals(True)
            self.device_box.clear()
            for item in self.outputs:
                self.device_box.addItem(item["label"], item["id"])
            index = self.device_box.findData(self.player.device)
            self.device_box.setCurrentIndex(index if index >= 0 else 0)
            self.device_box.blockSignals(False)
            self._sync_route_label()

        def add_dialog(self):
            dialog = QDialog(self)
            dialog.setWindowTitle("Add a stream")
            dialog.setModal(True)
            dialog.setMinimumWidth(380)
            box = QVBoxLayout(dialog)
            name = QLineEdit()
            name.setPlaceholderText("Name")
            url = QLineEdit()
            url.setPlaceholderText("https://")
            place = QLineEdit()
            place.setPlaceholderText("Place, optional")
            error = QLabel("")
            error.setStyleSheet("color:#e8a04a;")
            error.hide()
            buttons = QHBoxLayout()
            cancel = QPushButton("Cancel")
            cancel.clicked.connect(dialog.reject)
            ok = QPushButton("Put it on the dial")
            ok.setStyleSheet("background:#e8a04a;color:#2a1c0a;")
            buttons.addWidget(cancel)
            buttons.addWidget(ok)
            box.addWidget(name)
            box.addWidget(url)
            box.addWidget(place)
            box.addWidget(error)
            box.addLayout(buttons)

            def submit():
                stream = url.text().strip()
                if not name.text().strip():
                    error.setText("Give it a name.")
                    error.show()
                    return
                if not stream.startswith(("http://", "https://")):
                    error.setText("The stream needs an http or https address.")
                    error.show()
                    return
                station = {
                    "id": f"custom:{int(time.time())}",
                    "name": name.text().strip()[:120],
                    "streamUrl": stream[:500],
                    "homepage": "",
                    "tags": "",
                    "country": place.text().strip()[:60],
                    "countryCode": "",
                    "language": "",
                    "codec": "",
                    "bitrate": 0,
                    "custom": True,
                }
                self.lib["custom"] = [station, *[item for item in self.lib["custom"] if item["id"] != station["id"]]][:200]
                self.lib["favorites"] = [station, *[item for item in self.lib["favorites"] if item["id"] != station["id"]]][:200]
                library.save(self.lib)
                dialog.accept()
                self.scope = "mine"
                self.scope_buttons["mine"].setChecked(True)
                self.selected = 0
                self.fill()
                self.play_index(0)

            ok.clicked.connect(submit)
            dialog.exec()

        def refresh_stage(self):
            station = self.current
            labels = {
                "idle": "QUIET",
                "connecting": "TUNING",
                "playing": "ON AIR",
                "paused": "PAUSED",
                "error": "OFF AIR",
            }
            self.eyebrow.setText(labels.get(self.status, "QUIET"))
            self.header_status.setText(labels.get(self.status, "QUIET"))
            self.mark.setText(monogram(station["name"]) if station else "·")
            self.mark.setProperty("live", "true" if self.status == "playing" else "false")
            self.mark.style().unpolish(self.mark)
            self.mark.style().polish(self.mark)
            self.title.setText(station["name"] if station else "No station")
            self.meta.setText(tech_line(station) if station else "Pick a station from the directory.")
            if self.error:
                self.err.setText(self.error)
                self.err.show()
            else:
                self.err.hide()
            self.play_btn.setText("❚❚" if self.status == "playing" else "▶")
            if self.started and self.status == "playing":
                seconds = int(time.time() - self.started)
                self.elapsed.setText(f"{seconds // 60}:{seconds % 60:02d}")
            else:
                self.elapsed.setText("")

        def tick(self):
            if self.sleep_at and time.time() >= self.sleep_at:
                with self.lock:
                    if self.player.alive() and not self.player.paused:
                        self.player.toggle()
                self.sleep_at = None
                self.sleep_btn.setText("Sleep")
                self.status = "paused"
                self.refresh_stage()
            if self.status == "playing":
                with self.lock:
                    alive = self.player.alive()
                if not alive:
                    self.status = "error"
                    self.error = "The stream ended."
                    self.started = None
                self.refresh_stage()

        def keyPressEvent(self, event: QKeyEvent):
            focused = QApplication.focusWidget()
            typing = isinstance(focused, QLineEdit)
            key = event.key()
            if key == Qt.Key_Escape and typing:
                self.list.setFocus()
                return
            if typing:
                super().keyPressEvent(event)
                return
            if key == Qt.Key_Space:
                self.toggle()
                return
            if key in (Qt.Key_J, Qt.Key_Down):
                self.list.setCurrentRow(min(self.list.count() - 1, self.list.currentRow() + 1))
                return
            if key in (Qt.Key_K, Qt.Key_Up):
                self.list.setCurrentRow(max(0, self.list.currentRow() - 1))
                return
            if key in (Qt.Key_Return, Qt.Key_Enter):
                self.play_index(self.list.currentRow())
                return
            if key == Qt.Key_F:
                self.toggle_saved(self.list.currentRow())
                return
            if key == Qt.Key_N:
                self.step(1)
                return
            if key == Qt.Key_P:
                self.step(-1)
                return
            if key == Qt.Key_M:
                self.toggle_mute()
                return
            if key == Qt.Key_S:
                self.cycle_sleep()
                return
            if key == Qt.Key_A:
                self.add_dialog()
                return
            if key == Qt.Key_Slash:
                self.search_box.setFocus()
                self.search_box.selectAll()
                return
            if key == Qt.Key_Q and event.modifiers() & Qt.ControlModifier:
                self.close()
                return
            super().keyPressEvent(event)

        def closeEvent(self, event):
            with self.lock:
                self.player.stop()
            event.accept()

    app = QApplication(argv)
    app.setApplicationName("Vela")
    app.setStyle("Fusion")
    app.setFont(QFont("Sans Serif", 11))
    ink = QPalette()
    ink.setColor(QPalette.Window, QColor("#141311"))
    ink.setColor(QPalette.WindowText, QColor("#efe8dc"))
    ink.setColor(QPalette.Base, QColor("#1e1c19"))
    ink.setColor(QPalette.AlternateBase, QColor("#191816"))
    ink.setColor(QPalette.Text, QColor("#efe8dc"))
    ink.setColor(QPalette.Button, QColor("#1e1c19"))
    ink.setColor(QPalette.ButtonText, QColor("#efe8dc"))
    ink.setColor(QPalette.Highlight, QColor("#2a261f"))
    ink.setColor(QPalette.HighlightedText, QColor("#efe8dc"))
    ink.setColor(QPalette.PlaceholderText, QColor("#7c7468"))
    app.setPalette(ink)
    app.setStyleSheet(QSS)
    window = Window()
    window.show()
    if "--shot" in argv:
        window.search_box.setText("")
        window.search()
        deadline = time.time() + 8
        while time.time() < deadline and not window.stations and not window.error:
            app.processEvents()
            time.sleep(0.05)
        app.processEvents()
        path = "/tmp/vela-window.png"
        if argv[-1].endswith(".png"):
            path = argv[-1]
        window.grab().save(path)
        print(path)
        return 0
    return app.exec()


if __name__ == "__main__":
    sys.exit(main() or 0)
