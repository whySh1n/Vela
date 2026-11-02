"""Vela's window. Qt on the machine you are using. No browser."""

from __future__ import annotations

import contextlib
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
QMainWindow, QWidget#app { background: #0c0c0c; color: #f4f1ea; }
QWidget#stage { background: #101010; }
QLabel, QListWidget { background: transparent; color: #f4f1ea; }
QLabel#word { font-size: 16px; font-weight: 650; }
QLabel#status { color: #8d877f; font-size: 13px; }
QLabel#status[live="true"] { color: #e8a04a; }
QFrame#line { background: #242424; max-height: 1px; min-height: 1px; border: none; }
QLineEdit {
  background: transparent; color: #f4f1ea; border: none; padding: 0 14px;
  selection-background-color: #2c2c2c; selection-color: #f4f1ea;
}
QWidget#finder {
  background: #141414; border: 1px solid #242424; border-radius: 12px; min-height: 42px;
}
QFrame#finderRule { background: #2a2a2a; border: none; max-width: 1px; min-width: 1px; }
QListWidget { border: none; outline: none; }
QListWidget::item { border: none; background: transparent; }
QListWidget::item:selected { background: transparent; }
QPushButton {
  background: transparent; color: #8d877f; border: none;
  border-radius: 9px; padding: 6px 12px;
}
QPushButton:hover { color: #f4f1ea; background: #1a1a1a; }
QPushButton#add { color: #f4f1ea; padding: 6px 14px; }
QPushButton#add:hover { background: #1a1a1a; }
QWidget#segments { background: #171717; border-radius: 12px; }
QPushButton#ghost {
  padding: 6px 14px; border-radius: 8px; color: #8d877f; background: transparent;
}
QPushButton#ghost:hover { color: #f4f1ea; background: transparent; }
QPushButton#ghost:checked { color: #141414; background: #f4f1ea; }
QPushButton#ghost:checked:hover { color: #141414; background: #ffffff; }
QPushButton#transport { color: #cfc8be; padding: 6px 10px; border-radius: 8px; }
QPushButton#transport:hover { color: #f4f1ea; background: #1c1c1c; }
QPushButton#play {
  background: #f4f1ea; color: #141414; border: none; border-radius: 22px;
  min-width: 44px; max-width: 44px; min-height: 44px; max-height: 44px;
  font-size: 13px; padding: 0;
}
QPushButton#play:hover { background: #ffffff; color: #141414; }
QPushButton#chip {
  background: transparent; color: #8d877f; border: none; border-radius: 8px; padding: 4px 10px;
}
QPushButton#chip:hover { color: #f4f1ea; background: #1a1a1a; }
QPushButton#chip:checked { color: #141414; background: #f4f1ea; }
QPushButton#chip:checked:hover { color: #141414; background: #ffffff; }
QComboBox {
  background: #171717; border: none; border-radius: 8px;
  padding: 5px 10px; min-height: 18px; color: #f4f1ea;
}
QComboBox::drop-down { border: none; width: 18px; }
QComboBox QAbstractItemView {
  background: #171717; color: #f4f1ea; border: none;
  selection-background-color: #242424; outline: none;
}
QSlider::groove:horizontal { height: 2px; background: #2a2a2a; border: none; }
QSlider::sub-page:horizontal { background: #f4f1ea; }
QSlider::handle:horizontal {
  background: #f4f1ea; border: none; width: 12px; height: 12px; margin: -5px 0; border-radius: 6px;
}
QLabel#eyebrow { color: #8d877f; font-size: 11px; letter-spacing: 1.2px; }
QLabel#eyebrow[live="true"] { color: #e8a04a; }
QLabel#muted, QLabel#meta { color: #8d877f; font-size: 12px; }
QLabel#count { color: #6a655f; font-size: 10px; letter-spacing: 1.6px; }
QLabel#err { color: #e8a04a; font-size: 12px; }
QLabel#mark {
  background: #1a1a1a; color: #f4f1ea; border: none; border-radius: 16px;
  font-size: 16px; font-weight: 650;
}
QLabel#mark[live="true"] { background: #f4f1ea; color: #141414; }
QScrollBar:vertical { background: transparent; width: 8px; margin: 4px 0; }
QScrollBar::handle:vertical { background: #2a2a2a; border-radius: 4px; min-height: 24px; }
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
        from PySide6.QtCore import QEvent, Qt, QTimer, QObject, Signal, QSize
        from PySide6.QtGui import QColor, QFont, QFontMetrics, QKeyEvent, QPainter, QPalette
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
            QSizePolicy,
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

    import shiboken6

    class Bridge(QObject):
        results = Signal(int, object, str)
        played = Signal(int, str)
        devices = Signal(object)

    # Keys the window owns even while the station list has focus. Without this
    # the list's type-to-find swallows the letters, and Enter double-fires.
    LIST_KEYS = {
        Qt.Key_Space,
        Qt.Key_J,
        Qt.Key_K,
        Qt.Key_F,
        Qt.Key_N,
        Qt.Key_P,
        Qt.Key_M,
        Qt.Key_S,
        Qt.Key_A,
        Qt.Key_Slash,
        Qt.Key_Return,
        Qt.Key_Enter,
    }

    def quiet(button):
        # Buttons are for the mouse. Every one has a key, and a focused button
        # would take Space for itself instead of play and pause.
        button.setFocusPolicy(Qt.NoFocus)
        return button

    class ElideLabel(QLabel):
        def __init__(self, text, color, size=15, weight=QFont.Weight.Medium):
            super().__init__(text)
            self._color = QColor(color)
            font = QFont(self.font())
            font.setPixelSize(size)
            font.setWeight(weight)
            self.setFont(font)
            self.setMinimumWidth(0)
            self.setMinimumHeight(size + 6)
            self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)

        def paintEvent(self, _event):
            painter = QPainter(self)
            painter.setPen(self._color)
            painter.setFont(self.font())
            text = QFontMetrics(self.font()).elidedText(self.text(), Qt.ElideRight, max(0, self.width()))
            painter.drawText(self.rect(), int(Qt.AlignVCenter | Qt.AlignLeft), text)

    class Window(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("Vela")
            self.resize(1200, 760)
            self.setMinimumSize(980, 620)
            self.lib = library.load()
            self.player = player.Player(self.lib.get("volume", 82), self.lib.get("route"))
            self.lock = threading.Lock()
            self._closing = False
            self.bridge = Bridge(self)
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
            self.track_artist = ""
            self.track_title = ""
            self.outputs = [{"id": "auto", "label": "System default"}]
            # Sliders fire on every step; write the library once they settle.
            self.save_timer = QTimer(self)
            self.save_timer.setSingleShot(True)
            self.save_timer.setInterval(400)
            self.save_timer.timeout.connect(self._save_now)
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
            self.list.setFocus()

        @contextlib.contextmanager
        def _try_lock(self):
            # A worker holds the lock while mpv tunes or restarts. The UI must
            # never wait on that; callers fall back to updating state only.
            got = self.lock.acquire(blocking=False)
            try:
                yield got
            finally:
                if got:
                    self.lock.release()

        def eventFilter(self, watched, event):
            if (
                watched is self.list
                and event.type() == QEvent.KeyPress
                and event.key() in LIST_KEYS
                and not event.modifiers() & Qt.ControlModifier
            ):
                self.keyPressEvent(event)
                return True
            return super().eventFilter(watched, event)

        def _build(self):
            root = QWidget()
            root.setObjectName("app")
            self.setCentralWidget(root)
            outer = QVBoxLayout(root)
            outer.setContentsMargins(0, 0, 0, 0)
            outer.setSpacing(0)

            header = QWidget()
            bar = QHBoxLayout(header)
            bar.setContentsMargins(22, 14, 18, 12)
            bar.setSpacing(16)
            brand = QWidget()
            brand_row = QHBoxLayout(brand)
            brand_row.setContentsMargins(0, 0, 0, 0)
            brand_row.setSpacing(10)
            name = QLabel("Vela")
            name.setObjectName("word")
            self.header_status = QLabel("Quiet")
            self.header_status.setObjectName("status")
            brand_row.addWidget(name)
            brand_row.addWidget(self.header_status)
            brand_row.addStretch(1)
            actions = QWidget()
            action_row = QHBoxLayout(actions)
            action_row.setContentsMargins(0, 0, 0, 0)
            action_row.addStretch(1)
            add = quiet(QPushButton("Add"))
            add.setObjectName("add")
            add.setCursor(Qt.PointingHandCursor)
            add.clicked.connect(self.add_dialog)
            action_row.addWidget(add)
            segments = QWidget()
            segments.setObjectName("segments")
            seg = QHBoxLayout(segments)
            seg.setContentsMargins(4, 4, 4, 4)
            seg.setSpacing(2)
            self.scope_group = QButtonGroup(self)
            self.scope_group.setExclusive(True)
            self.scope_buttons = {}
            for key, label in (("dial", "Dial"), ("saved", "Saved"), ("mine", "Mine")):
                button = quiet(QPushButton(label))
                button.setObjectName("ghost")
                button.setFlat(True)
                button.setCursor(Qt.PointingHandCursor)
                button.setCheckable(True)
                button.setChecked(key == "dial")
                button.clicked.connect(lambda _=False, k=key: self.on_scope(k))
                self.scope_group.addButton(button)
                self.scope_buttons[key] = button
                seg.addWidget(button)
            bar.addWidget(brand, 1)
            bar.addWidget(segments, 0, Qt.AlignCenter)
            bar.addWidget(actions, 1)
            outer.addWidget(header)

            filters = QWidget()
            filters_box = QVBoxLayout(filters)
            filters_box.setContentsMargins(20, 4, 20, 6)
            filters_box.setSpacing(8)
            finder = QWidget()
            finder.setObjectName("finder")
            finder.setFixedHeight(42)
            finder_row = QHBoxLayout(finder)
            finder_row.setContentsMargins(0, 0, 0, 0)
            finder_row.setSpacing(0)
            self.search_box = QLineEdit()
            self.search_box.setObjectName("finderField")
            self.search_box.setPlaceholderText("Search stations")
            self.search_box.textChanged.connect(self.on_query)
            rule_host = QWidget()
            rule_host.setFixedWidth(1)
            rule_box = QVBoxLayout(rule_host)
            rule_box.setContentsMargins(0, 10, 0, 10)
            rule_box.setSpacing(0)
            rule = QFrame()
            rule.setObjectName("finderRule")
            rule_box.addWidget(rule)
            self.country_box = QLineEdit()
            self.country_box.setObjectName("finderField")
            self.country_box.setPlaceholderText("Country")
            self.country_box.setFixedWidth(180)
            self.country_box.textChanged.connect(self.on_country)
            finder_row.addWidget(self.search_box, 1)
            finder_row.addWidget(rule_host)
            finder_row.addWidget(self.country_box)
            filters_box.addWidget(finder)

            genre_row = QHBoxLayout()
            genre_row.setContentsMargins(0, 0, 0, 0)
            genre_row.setSpacing(2)
            self.genre_group = QButtonGroup(self)
            self.genre_group.setExclusive(True)
            for genre_id, label in GENRES:
                button = quiet(QPushButton(label))
                button.setObjectName("chip")
                button.setFlat(True)
                button.setCursor(Qt.PointingHandCursor)
                button.setCheckable(True)
                button.setChecked(genre_id == "")
                button.clicked.connect(lambda _=False, gid=genre_id: self.on_tag(gid))
                self.genre_group.addButton(button)
                genre_row.addWidget(button)
            genre_row.addStretch(1)
            filters_box.addLayout(genre_row)
            self.count = QLabel("DIRECTORY")
            self.count.setObjectName("count")
            filters_box.addWidget(self.count)
            outer.addWidget(filters)

            list_host = QWidget()
            list_box = QHBoxLayout(list_host)
            list_box.setContentsMargins(12, 0, 6, 8)
            list_box.setSpacing(0)
            self.list = QListWidget()
            self.list.setSpacing(4)
            self.list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.list.setFrameShape(QFrame.NoFrame)
            self.list.itemClicked.connect(self.on_click)
            self.list.currentRowChanged.connect(self.on_row)
            self.list.installEventFilter(self)
            list_box.addWidget(self.list)
            outer.addWidget(list_host, 1)
            self._list_fade = QWidget(list_host)
            self._list_fade.setAttribute(Qt.WA_TransparentForMouseEvents, True)
            self._list_fade.setStyleSheet(
                "background: qlineargradient(x1:0, y1:0, x2:0, y2:1,"
                " stop:0 rgba(12,12,12,0), stop:0.25 rgba(12,12,12,0), stop:0.72 #0c0c0c, stop:1 #0c0c0c);"
            )

            outer.addWidget(self._rule())
            outer.addWidget(self._deck())

        def resizeEvent(self, event):
            super().resizeEvent(event)
            if getattr(self, "_list_fade", None) is not None:
                self._place_list_fade()

        def _place_list_fade(self):
            host = self._list_fade.parentWidget()
            if host is None:
                return
            height = 36
            self._list_fade.setGeometry(0, max(0, host.height() - height), host.width(), height)
            self._list_fade.raise_()

        def _deck(self):
            stage = QWidget()
            stage.setObjectName("stage")
            side = QVBoxLayout(stage)
            side.setContentsMargins(20, 14, 20, 16)
            side.setSpacing(12)

            top = QHBoxLayout()
            top.setSpacing(16)
            self.mark = QLabel("·")
            self.mark.setObjectName("mark")
            self.mark.setAlignment(Qt.AlignCenter)
            self.mark.setFixedSize(56, 56)
            identity = QVBoxLayout()
            identity.setContentsMargins(0, 0, 0, 0)
            identity.setSpacing(1)
            self.eyebrow = QLabel("Quiet")
            self.eyebrow.setObjectName("eyebrow")
            self.title = ElideLabel("No station", "#f4f1ea", 20, QFont.Weight.DemiBold)
            self.title.setObjectName("title")
            self.song = ElideLabel("", "#f4f1ea", 15, QFont.Weight.Medium)
            self.song.setObjectName("song")
            self.song.hide()
            self.who = ElideLabel("", "#e8a04a", 13, QFont.Weight.Normal)
            self.who.setObjectName("who")
            self.who.hide()
            self.meta = ElideLabel("Pick a station from the directory.", "#8d877f", 13, QFont.Weight.Normal)
            self.meta.setObjectName("meta")
            self.err = QLabel("")
            self.err.setObjectName("err")
            self.err.setWordWrap(True)
            self.err.hide()
            identity.addStretch(1)
            identity.addWidget(self.eyebrow)
            identity.addWidget(self.title)
            identity.addWidget(self.song)
            identity.addWidget(self.who)
            identity.addWidget(self.meta)
            identity.addWidget(self.err)
            identity.addStretch(1)

            transport = QHBoxLayout()
            transport.setSpacing(4)
            prev = quiet(QPushButton("Prev"))
            prev.setObjectName("transport")
            prev.clicked.connect(lambda: self.step(-1))
            self.play_btn = quiet(QPushButton("▶"))
            self.play_btn.setObjectName("play")
            self.play_btn.clicked.connect(self.toggle)
            nxt = quiet(QPushButton("Next"))
            nxt.setObjectName("transport")
            nxt.clicked.connect(lambda: self.step(1))
            transport.addWidget(prev)
            transport.addWidget(self.play_btn)
            transport.addWidget(nxt)
            self.elapsed = QLabel("")
            self.elapsed.setObjectName("muted")
            self.elapsed.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.elapsed.setMinimumWidth(44)

            vol = QHBoxLayout()
            vol.setSpacing(8)
            vol_name = QLabel("Volume")
            vol_name.setObjectName("muted")
            self.vol = QSlider(Qt.Horizontal)
            self.vol.setRange(0, 100)
            self.vol.setValue(self.player.volume)
            self.vol.setFixedWidth(132)
            self.vol.valueChanged.connect(self.on_volume)
            self.vol_label = QLabel(str(self.player.volume))
            self.vol_label.setObjectName("muted")
            self.vol_label.setFixedWidth(28)
            self.vol_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.mute_btn = quiet(QPushButton("Mute"))
            self.mute_btn.setObjectName("transport")
            self.mute_btn.clicked.connect(self.toggle_mute)
            vol.addWidget(vol_name)
            vol.addWidget(self.vol)
            vol.addWidget(self.vol_label)
            vol.addWidget(self.mute_btn)

            top.addWidget(self.mark, 0, Qt.AlignVCenter)
            top.addLayout(identity, 1)
            top.addLayout(transport)
            top.addWidget(self.elapsed)
            top.addLayout(vol)

            sound = QHBoxLayout()
            sound.setSpacing(8)
            output_name = QLabel("Output")
            output_name.setObjectName("muted")
            self.device_box = QComboBox()
            self.device_box.setMinimumWidth(180)
            self.device_box.addItem("System default", "auto")
            self.device_box.currentIndexChanged.connect(self.on_device)
            self.balance_label = QLabel(self._balance_text())
            self.balance_label.setObjectName("muted")
            self.balance = QSlider(Qt.Horizontal)
            self.balance.setRange(-10, 10)
            self.balance.setValue(int(round(self.player.balance * 10)))
            self.balance.setFixedWidth(128)
            self.balance.valueChanged.connect(self.on_balance)
            tone_name = QLabel("Tone")
            tone_name.setObjectName("muted")
            self.eq_box = QComboBox()
            self.eq_box.setMinimumWidth(108)
            for key, label in EQS:
                self.eq_box.addItem(label, key)
            index = self.eq_box.findData(self.player.eq)
            if index >= 0:
                self.eq_box.setCurrentIndex(index)
            self.eq_box.currentIndexChanged.connect(self.on_eq)
            self.sleep_btn = quiet(QPushButton("Sleep"))
            self.sleep_btn.setObjectName("transport")
            self.sleep_btn.clicked.connect(self.cycle_sleep)
            sound.addWidget(output_name)
            sound.addWidget(self.device_box, 1)
            sound.addWidget(self.balance_label)
            sound.addWidget(self.balance)
            sound.addWidget(tone_name)
            sound.addWidget(self.eq_box)
            sound.addWidget(self.sleep_btn)
            self.route = QLabel("Output · system")
            self.route.setObjectName("muted")
            self.route.hide()

            side.addLayout(top)
            side.addLayout(sound)
            self._sync_route_label()
            return stage

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

        def _discard_rows(self):
            # QListWidget.clear() drops the items and leaves their widgets
            # parented to the viewport. Those leftovers stay Python-owned, and
            # PySide destroys them again while the application is shutting down.
            widgets = [self.list.itemWidget(self.list.item(index)) for index in range(self.list.count())]
            self.list.clear()
            for widget in widgets:
                if widget is not None and shiboken6.isValid(widget):
                    widget.setParent(None)
                    shiboken6.delete(widget)

        def _save_later(self):
            self.save_timer.start()

        def _save_now(self):
            self.save_timer.stop()
            library.save(self.lib)

        def shutdown(self):
            if self._closing:
                return
            if self.save_timer.isActive():
                self._save_now()
            self.search_timer.stop()
            self.clock.stop()
            # A dead station can tune for seconds; don't make closing wait for it.
            self.player.cancel()
            with self.lock:
                self._closing = True
                self.token += 1
                self.play_token += 1
                self.bridge.blockSignals(True)
                self.player.stop()
            self._discard_rows()

        def fill(self):
            if self._closing:
                return
            rows = self.visible()
            self.list.blockSignals(True)
            self._discard_rows()
            saved = self.saved_ids()
            if rows:
                self.selected = max(0, min(self.selected, len(rows) - 1))
            for index, station in enumerate(rows):
                item = QListWidgetItem()
                item.setData(Qt.UserRole, station["id"])
                item.setSizeHint(QSize(0, 68))
                self.list.addItem(item)
                self.list.setItemWidget(item, self._row(station, index, station["id"] in saved))
            if rows:
                self.list.setCurrentRow(self.selected)
            self.list.blockSignals(False)
            self._shown_playing = None
            self._paint_badges()
            self.scope_buttons["saved"].setText(f"Saved  {len(self.lib['favorites']) or ''}".strip())
            self.scope_buttons["mine"].setText(f"Mine  {len(self.lib['custom']) or ''}".strip())
            label = {"dial": "DIRECTORY", "saved": "SAVED", "mine": "YOUR STREAMS"}[self.scope]
            if self.scope == "dial" and self.status == "connecting" and not rows:
                self.count.setText("SEARCHING")
            else:
                self.count.setText(f"{label}    {len(rows)}")

        @staticmethod
        def _row_style(selected):
            return "background:#161616;border-radius:10px;" if selected else "background:transparent;"

        @staticmethod
        def _badge_style(live):
            if live:
                return "background:#f4f1ea;color:#141414;border-radius:10px;font-size:11px;font-weight:650;"
            return "background:#1a1a1a;color:#cfc8be;border-radius:10px;font-size:11px;font-weight:650;"

        def _paint_badges(self):
            playing_id = None
            if self.current and self.status in ("playing", "connecting"):
                playing_id = self.current["id"]
            if playing_id == getattr(self, "_shown_playing", None):
                return
            self._shown_playing = playing_id
            for row in range(self.list.count()):
                item = self.list.item(row)
                widget = self.list.itemWidget(item) if item is not None else None
                if widget is None or not shiboken6.isValid(widget):
                    continue
                badge = widget.findChild(QLabel, "badge")
                if badge is None or not shiboken6.isValid(badge):
                    continue
                badge.setStyleSheet(self._badge_style(item.data(Qt.UserRole) == playing_id))

        def _style_row(self, row, selected):
            item = self.list.item(row) if row >= 0 else None
            widget = self.list.itemWidget(item) if item is not None else None
            if widget is not None and shiboken6.isValid(widget):
                widget.setStyleSheet(self._row_style(selected))

        def _row(self, station, index, saved):
            wrap = QWidget()
            wrap.setStyleSheet(self._row_style(index == self.selected))
            box = QHBoxLayout(wrap)
            box.setContentsMargins(12, 8, 8, 8)
            box.setSpacing(12)
            badge = QLabel(monogram(station["name"]))
            badge.setObjectName("badge")
            badge.setAlignment(Qt.AlignCenter)
            badge.setFixedSize(36, 36)
            live = self.current is not None and station["id"] == self.current.get("id") and self.status in ("playing", "connecting")
            badge.setStyleSheet(self._badge_style(live))
            text = QVBoxLayout()
            text.setSpacing(0)
            text.setContentsMargins(0, 0, 0, 0)
            title = ElideLabel(station["name"], "#f4f1ea", 15, QFont.Weight.Medium)
            sub = ElideLabel(place_line(station), "#8d877f", 12, QFont.Weight.Normal)
            text.addWidget(title)
            text.addWidget(sub)
            box.addWidget(badge)
            box.addLayout(text, 1)
            rate = station.get("bitrate")
            if rate:
                meta = QLabel(str(rate))
                meta.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                meta.setStyleSheet("color:#6a655f;font-size:11px;background:transparent;")
                box.addWidget(meta)
            star = quiet(QPushButton("★" if saved else "☆"))
            star.setFlat(True)
            star.setFixedWidth(32)
            star.setStyleSheet(
                "color:#f4f1ea;font-size:14px;background:transparent;" if saved else "color:#6a655f;background:transparent;"
            )
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
                if row != self.selected:
                    self._style_row(self.selected, False)
                self.selected = row
                self._style_row(row, True)

        def on_click(self, item):
            row = self.list.row(item)
            rows = self.visible()
            if row < 0 or row >= len(rows):
                return
            if (
                self.current
                and rows[row]["id"] == self.current["id"]
                and self.status in ("playing", "connecting")
            ):
                return
            self.play_index(row)

        def search(self):
            if self._closing:
                return
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
                with self.lock:
                    if self._closing or token != self.token:
                        return
                    self.bridge.results.emit(token, rows, err)

            threading.Thread(target=work, daemon=True).start()

        def on_results(self, token, rows, err):
            if self._closing or token != self.token or self.scope != "dial":
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
            self.track_artist = ""
            self.track_title = ""
            self.refresh_stage()
            self.play_token += 1
            token = self.play_token
            url = station["streamUrl"]
            # Let go of a station that is still tuning instead of queueing behind it.
            self.player.cancel()

            def work():
                with self.lock:
                    if self._closing or token != self.play_token:
                        return
                    message = self.player.play(url, allow_private=bool(station.get("custom")))
                    if self._closing or token != self.play_token:
                        return
                    self.bridge.played.emit(token, message or "")

            threading.Thread(target=work, daemon=True).start()

        def on_played(self, token, message):
            if self._closing or token != self.play_token:
                return
            if message:
                self.status = "error"
                self.error = message
                self.started = None
            else:
                with self.lock:
                    # Volume, mute, balance or tone may have moved while tuning.
                    self.player.sync()
                self.status = "playing"
                self.error = ""
                self.started = time.time()
            self.refresh_stage()

        def toggle(self):
            with self._try_lock() as got:
                if not got:
                    return  # still tuning
                alive = self.player.alive()
                if alive:
                    self.player.toggle()
                    paused = self.player.paused
            if alive:
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
            with self._try_lock() as got:
                self.player.toggle_mute(send=got)
                muted = self.player.muted
                volume = self.player.volume
            self.mute_btn.setText("Muted" if muted else "Mute")
            self.vol.blockSignals(True)
            self.vol.setValue(0 if muted else volume)
            self.vol.blockSignals(False)
            self.vol_label.setText("0" if muted else str(volume))

        def on_volume(self, value):
            with self._try_lock() as got:
                self.player.set_volume(value, send=got)
            self.vol_label.setText(str(value))
            self.mute_btn.setText("Mute")
            self.lib["volume"] = value
            self._save_later()

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
                    if self._closing or token != self.play_token:
                        return
                    self.player.set_device(device)
                    if self._closing or token != self.play_token:
                        return
                    self.bridge.played.emit(token, "")

            self.player.device = device
            self._remember_route()
            if self.player.url:
                threading.Thread(target=work, daemon=True).start()
            else:
                self._sync_route_label()

        def on_balance(self, value):
            with self._try_lock() as got:
                self.player.set_balance(value / 10, send=got)
            self.balance_label.setText(self._balance_text())
            self._remember_route()

        def on_eq(self, _index):
            eq = self.eq_box.currentData()
            with self._try_lock() as got:
                self.player.set_eq(eq, send=got)
            self._remember_route()

        def _remember_route(self):
            self.lib["route"] = {
                "device": self.player.device,
                "balance": self.player.balance,
                "eq": self.player.eq,
            }
            self._save_later()
            self._sync_route_label()

        def _load_devices(self):
            if self._closing:
                return
            # Probing runs `mpv --audio-device=help`; it shares no state, so it
            # must not hold the lock the UI needs.
            found = self.player.devices()
            if not found:
                found = [{"id": "auto", "label": "System default"}]
            elif not any(item["id"] == "auto" for item in found):
                found = [{"id": "auto", "label": "System default"}, *found]
            with self.lock:
                if self._closing:
                    return
                self.bridge.devices.emit(found)

        def on_devices(self, found):
            if self._closing:
                return
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
                    "id": library.new_custom_id(),
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
                "idle": "Quiet",
                "connecting": "Tuning",
                "playing": "On air",
                "paused": "Paused",
                "error": "Off air",
            }
            self.eyebrow.setText(labels.get(self.status, "QUIET"))
            self.header_status.setText(labels.get(self.status, "QUIET"))
            self.mark.setText(monogram(station["name"]) if station else "·")
            live = "true" if self.status == "playing" else "false"
            for widget in (self.mark, self.eyebrow, self.header_status):
                widget.setProperty("live", live)
                widget.style().unpolish(widget)
                widget.style().polish(widget)
            self.title.setText(station["name"] if station else "No station")
            self._show_track()
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
            self._paint_badges()

        def _show_track(self):
            if self.track_title:
                self.song.setText(self.track_title)
                self.song.show()
            else:
                self.song.hide()
            if self.track_artist:
                self.who.setText(self.track_artist)
                self.who.show()
            else:
                self.who.hide()

        def tick(self):
            if self._closing:
                return
            if self.sleep_at and time.time() >= self.sleep_at:
                with self._try_lock() as got:
                    if got and self.player.alive() and not self.player.paused:
                        self.player.toggle()
                if got:  # otherwise mpv is busy tuning; try again next tick
                    self.sleep_at = None
                    self.sleep_btn.setText("Sleep")
                    self.status = "paused"
                    self.refresh_stage()
            if self.status == "playing":
                track = None
                with self._try_lock() as got:
                    if got:
                        alive = self.player.alive()
                        if alive and self.current:
                            track = self.player.track(self.current.get("name") or "")
                    else:
                        alive = True
                if not alive:
                    self.status = "error"
                    self.error = "The stream ended."
                    self.started = None
                    self.track_artist = ""
                    self.track_title = ""
                elif track is not None and (track[0] or track[1]) and track != (self.track_artist, self.track_title):
                    self.track_artist, self.track_title = track
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
            self.shutdown()
            event.accept()

    def retire(window, app):
        # Destroy the window while QApplication is still alive. Otherwise
        # PySide walks every leftover wrapper from interpreter shutdown and
        # faults in QObject's destructor.
        if window is not None and shiboken6.isValid(window):
            window.shutdown()
            window.hide()
            app.processEvents()
            shiboken6.delete(window)

    app = QApplication(argv)
    app.setApplicationName("Vela")
    app.setStyle("Fusion")
    app.setFont(QFont("Adwaita Sans", 11))
    ink = QPalette()
    ink.setColor(QPalette.Window, QColor("#0c0c0c"))
    ink.setColor(QPalette.WindowText, QColor("#f4f1ea"))
    ink.setColor(QPalette.Base, QColor("#141414"))
    ink.setColor(QPalette.AlternateBase, QColor("#101010"))
    ink.setColor(QPalette.Text, QColor("#f4f1ea"))
    ink.setColor(QPalette.Button, QColor("#171717"))
    ink.setColor(QPalette.ButtonText, QColor("#f4f1ea"))
    ink.setColor(QPalette.Highlight, QColor("#242424"))
    ink.setColor(QPalette.HighlightedText, QColor("#f4f1ea"))
    ink.setColor(QPalette.PlaceholderText, QColor("#6a655f"))
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
        retire(window, app)
        return 0
    code = app.exec()
    retire(window, app)
    return code


if __name__ == "__main__":
    sys.exit(main() or 0)
