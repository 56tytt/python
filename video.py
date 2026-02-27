#!/usr/bin/env python3
import sys
import os
import gi
gi.require_version("Gst", "1.0")
from gi.repository import Gst, GObject

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFileDialog, QSlider, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt, QTimer, QUrl
from PyQt6.QtGui import QAction, QKeySequence, QDragEnterEvent, QDropEvent


Gst.init(None)
GObject.threads_init()


class PyGStreamPro(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyGStream PRO – Video Player")
        self.resize(1200, 700)

        self.playlist = []
        self.current_index = -1
        self.duration_ns = 0
        self.is_fullscreen = False

        self._build_ui()
        self._build_gst()
        self._build_timer()

        # Drag & Drop
        self.setAcceptDrops(True)

    # ───────────────── UI ─────────────────

    def _build_ui(self):
        # Video area
        self.video_widget = QWidget()
        self.video_widget.setStyleSheet("background-color: black;")

        # Position slider
        self.position_slider = QSlider(Qt.Orientation.Horizontal)
        self.position_slider.setRange(0, 1000)
        self.position_slider.sliderMoved.connect(self.on_seek)

        # Volume slider
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(80)
        self.volume_slider.sliderMoved.connect(self.on_volume_change)

        # Buttons
        open_btn = QPushButton("Open")
        prev_btn = QPushButton("Prev")
        play_btn = QPushButton("Play")
        pause_btn = QPushButton("Pause")
        next_btn = QPushButton("Next")
        sub_btn = QPushButton("Subtitles")

        open_btn.clicked.connect(self.open_files)
        prev_btn.clicked.connect(self.prev_track)
        play_btn.clicked.connect(self.play)
        pause_btn.clicked.connect(self.pause)
        next_btn.clicked.connect(self.next_track)
        sub_btn.clicked.connect(self.load_subtitles)

        controls = QHBoxLayout()
        controls.addWidget(open_btn)
        controls.addWidget(prev_btn)
        controls.addWidget(play_btn)
        controls.addWidget(pause_btn)
        controls.addWidget(next_btn)
        controls.addWidget(sub_btn)
        controls.addWidget(self.position_slider)
        controls.addWidget(self.volume_slider)

        # Playlist
        self.playlist_widget = QListWidget()
        self.playlist_widget.itemDoubleClicked.connect(self.on_playlist_double_click)
        self.playlist_widget.setMaximumWidth(260)

        # Layout
        main_layout = QHBoxLayout()
        video_layout = QVBoxLayout()
        video_layout.addWidget(self.video_widget)
        video_layout.addLayout(controls)

        video_container = QWidget()
        video_container.setLayout(video_layout)

        main_layout.addWidget(video_container)
        #main_layout.addWidget(self.playlist_widget)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # Menu + shortcuts
        self._build_menu_shortcuts()

    def _build_menu_shortcuts(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")

        open_act = QAction("Open", self)
        open_act.setShortcut(QKeySequence("Ctrl+O"))
        open_act.triggered.connect(self.open_files)
        file_menu.addAction(open_act)

        sub_act = QAction("Load Subtitles", self)
        sub_act.triggered.connect(self.load_subtitles)
        file_menu.addAction(sub_act)

        # Keyboard shortcuts
        self.shortcut_play_pause = QAction(self)
        self.shortcut_play_pause.setShortcut(QKeySequence(Qt.Key.Key_Space))
        self.shortcut_play_pause.triggered.connect(self.toggle_play_pause)
        self.addAction(self.shortcut_play_pause)

        self.shortcut_fullscreen = QAction(self)
        self.shortcut_fullscreen.setShortcut(QKeySequence("F"))
        self.shortcut_fullscreen.triggered.connect(self.toggle_fullscreen)
        self.addAction(self.shortcut_fullscreen)

        self.shortcut_seek_forward = QAction(self)
        self.shortcut_seek_forward.setShortcut(QKeySequence(Qt.Key.Key_Right))
        self.shortcut_seek_forward.triggered.connect(lambda: self.seek_relative(5))
        self.addAction(self.shortcut_seek_forward)

        self.shortcut_seek_back = QAction(self)
        self.shortcut_seek_back.setShortcut(QKeySequence(Qt.Key.Key_Left))
        self.shortcut_seek_back.triggered.connect(lambda: self.seek_relative(-5))
        self.addAction(self.shortcut_seek_back)

        self.shortcut_vol_up = QAction(self)
        self.shortcut_vol_up.setShortcut(QKeySequence(Qt.Key.Key_Up))
        self.shortcut_vol_up.triggered.connect(lambda: self.change_volume(+5))
        self.addAction(self.shortcut_vol_up)

        self.shortcut_vol_down = QAction(self)
        self.shortcut_vol_down.setShortcut(QKeySequence(Qt.Key.Key_Down))
        self.shortcut_vol_down.triggered.connect(lambda: self.change_volume(-5))
        self.addAction(self.shortcut_vol_down)

    # ───────────────── GStreamer ─────────────────

    def _build_gst(self):
        self.pipeline = Gst.ElementFactory.make("playbin", "player")
        if not self.pipeline:
            raise RuntimeError("Failed to create playbin")

        # Video sink with VAAPI / GL (HDR/VAAPI friendly)
        videosink = (Gst.ElementFactory.make("vaapisink", "videosink")
                     or Gst.ElementFactory.make("glimagesink", "videosink")
                     or Gst.ElementFactory.make("ximagesink", "videosink"))
        self.pipeline.set_property("video-sink", videosink)

        # Attach video widget window
        self.video_widget.winId()
        if hasattr(videosink, "set_window_handle"):
            videosink.set_window_handle(int(self.video_widget.winId()))

        # Bus
        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self.on_bus_message)

        # Volume
        self.pipeline.set_property("volume", 0.8)

    def _build_timer(self):
        self.timer = QTimer(self)
        self.timer.setInterval(200)
        self.timer.timeout.connect(self.update_position)
        self.timer.start()

    # ───────────────── Playlist ─────────────────

    def open_files(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Open videos", "", "Video Files (*.mp4 *.mkv *.avi *.mov);;All Files (*)"
        )
        if not paths:
            return
        for p in paths:
            self.add_to_playlist(p)
        if self.current_index == -1 and self.playlist:
            self.play_index(0)

    def add_to_playlist(self, path):
        self.playlist.append(path)
        item = QListWidgetItem(os.path.basename(path))
        item.setToolTip(path)
        self.playlist_widget.addItem(item)

    def on_playlist_double_click(self, item):
        row = self.playlist_widget.row(item)
        self.play_index(row)

    def play_index(self, idx):
        if idx < 0 or idx >= len(self.playlist):
            return
        self.current_index = idx
        path = self.playlist[idx]
        uri = QUrl.fromLocalFile(path).toString()
        self.pipeline.set_state(Gst.State.NULL)
        self.pipeline.set_property("uri", uri)
        self.pipeline.set_state(Gst.State.PLAYING)
        self.highlight_playlist_row(idx)

    def highlight_playlist_row(self, idx):
        for i in range(self.playlist_widget.count()):
            it = self.playlist_widget.item(i)
            it.setSelected(i == idx)

    def next_track(self):
        if self.current_index + 1 < len(self.playlist):
            self.play_index(self.current_index + 1)

    def prev_track(self):
        if self.current_index - 1 >= 0:
            self.play_index(self.current_index - 1)

    # ───────────────── Playback ─────────────────

    def play(self):
        self.pipeline.set_state(Gst.State.PLAYING)

    def pause(self):
        self.pipeline.set_state(Gst.State.PAUSED)

    def toggle_play_pause(self):
        state = self.pipeline.get_state(0).state
        if state == Gst.State.PLAYING:
            self.pause()
        else:
            self.play()

    # ───────────────── Position / Seek ─────────────────

    def update_position(self):
        state = self.pipeline.get_state(0).state
        if state < Gst.State.PAUSED:
            return
        ok, pos = self.pipeline.query_position(Gst.Format.TIME)
        ok2, dur = self.pipeline.query_duration(Gst.Format.TIME)
        if not ok or not ok2 or dur <= 0:
            return
        self.duration_ns = dur
        frac = pos / dur
        self.position_slider.blockSignals(True)
        self.position_slider.setValue(int(frac * 1000))
        self.position_slider.blockSignals(False)

    def on_seek(self, value):
        if self.duration_ns <= 0:
            return
        frac = value / 1000.0
        seek_ns = int(self.duration_ns * frac)
        self.pipeline.seek_simple(
            Gst.Format.TIME,
            Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT,
            seek_ns
        )

    def seek_relative(self, seconds):
        ok, pos = self.pipeline.query_position(Gst.Format.TIME)
        ok2, dur = self.pipeline.query_duration(Gst.Format.TIME)
        if not ok or not ok2 or dur <= 0:
            return
        new_pos = pos + seconds * Gst.SECOND
        new_pos = max(0, min(new_pos, dur))
        self.pipeline.seek_simple(
            Gst.Format.TIME,
            Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT,
            new_pos
        )

    # ───────────────── Volume ─────────────────

    def on_volume_change(self, value):
        self.pipeline.set_property("volume", value / 100.0)

    def change_volume(self, delta):
        v = self.volume_slider.value() + delta
        v = max(0, min(100, v))
        self.volume_slider.setValue(v)
        self.on_volume_change(v)

    # ───────────────── Subtitles ─────────────────

    def load_subtitles(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Load subtitles", "", "Subtitle Files (*.srt *.sub *.ass);;All Files (*)"
        )
        if not path:
            return
        uri = QUrl.fromLocalFile(path).toString()
        # playbin property for external subs
        self.pipeline.set_property("suburi", uri)

    # ───────────────── Fullscreen ─────────────────

    def toggle_fullscreen(self):
        if self.is_fullscreen:
            self.showNormal()
            self.is_fullscreen = False
        else:
            self.showFullScreen()
            self.is_fullscreen = True

    # ───────────────── Drag & Drop ─────────────────

    def dragEnterEvent(self, e: QDragEnterEvent):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    def dropEvent(self, e: QDropEvent):
        urls = e.mimeData().urls()
        paths = [u.toLocalFile() for u in urls if u.isLocalFile()]
        for p in paths:
            if os.path.isfile(p):
                self.add_to_playlist(p)
        if self.current_index == -1 and self.playlist:
            self.play_index(0)

    # ───────────────── Bus ─────────────────

    def on_bus_message(self, bus, msg):
        t = msg.type
        if t == Gst.MessageType.EOS:
            self.next_track()
        elif t == Gst.MessageType.ERROR:
            err, debug = msg.parse_error()
            print("GStreamer error:", err, debug)
            self.pipeline.set_state(Gst.State.NULL)

    # ───────────────── Close ─────────────────

    def closeEvent(self, e):
        self.pipeline.set_state(Gst.State.NULL)
        super().closeEvent(e)


def main():
    app = QApplication(sys.argv)
    win = PyGStreamPro()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
