import sys
import os
import pathlib
import gi

# GStreamer
gi.require_version("Gst", "1.0")
from gi.repository import Gst

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QSlider,
    QLabel,
    QListWidget,
    QFileDialog,
    QGroupBox,
    QMessageBox,
)
from PyQt6.QtGui import QAction , QIcon
from PyQt6.QtCore import Qt, QTimer, QSettings

AUDIO_EXT = [".mp3", ".wav", ".ogg", ".flac", ".m4a", ".mp4"]


def format_time(seconds):
    m, s = divmod(int(seconds), 60)
    return f"{m:02d}:{s:02d}"


class PlayerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Central Player Pro v2.5 - Qt Edition")
        self.resize(1100, 650)
        self.setWindowIcon(QIcon("icon.png"))

        self.settings = QSettings("ShayDev", "CentralPlayerPro")

        # --- מנוע GStreamer ---
        Gst.init(None)
        self.player = Gst.ElementFactory.make("playbin")
        self.equalizer = Gst.ElementFactory.make("equalizer-10bands")

        self.fakesink = Gst.ElementFactory.make("fakesink")
        self.player.set_property("video-sink", self.fakesink)

        self.player.set_property("audio-filter", self.equalizer)
        self.player.set_property("volume", 0.5)

        self.playlist = []
        self.current_idx = -1

        # --- בניית הממשק והתפריטים ---
        self.create_menus()
        self.init_ui()

        self.load_playlist()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_player)
        self.timer.start(100)

    def create_menus(self):
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("File")
        action_add = QAction("Add Files...", self)
        action_add.setShortcut("Ctrl+O")
        action_add.triggered.connect(self.add_files)
        file_menu.addAction(action_add)

        action_scan = QAction("Scan Folder...", self)
        action_scan.setShortcut("Ctrl+Shift+O")
        action_scan.triggered.connect(self.scan_folder)
        file_menu.addAction(action_scan)

        file_menu.addSeparator()

        action_exit = QAction("Exit", self)
        action_exit.setShortcut("Ctrl+Q")
        action_exit.triggered.connect(self.close)
        file_menu.addAction(action_exit)

        playback_menu = menu_bar.addMenu("Playback")
        action_play = QAction("Play / Pause", self)
        action_play.setShortcut("Space")
        action_play.triggered.connect(self.play_current)
        playback_menu.addAction(action_play)

        action_next = QAction("Next Track", self)
        action_next.setShortcut("Right")
        action_next.triggered.connect(self.play_next)
        playback_menu.addAction(action_next)

        action_prev = QAction("Previous Track", self)
        action_prev.setShortcut("Left")
        action_prev.triggered.connect(self.play_prev)
        playback_menu.addAction(action_prev)

        theme_menu = menu_bar.addMenu("Theme")
        for color in ["Blue", "Red", "Green", "Purple"]:
            action = QAction(color, self)
            action.triggered.connect(lambda checked, c=color: self.apply_theme(c))
            theme_menu.addAction(action)

        help_menu = menu_bar.addMenu("Help")
        action_about = QAction("About", self)
        action_about.triggered.connect(self.show_about)
        help_menu.addAction(action_about)

    def apply_theme(self, theme_name):
        themes = {
            "Blue": {
                "accent": "#58a6ff",
                "select": "#1f6feb",
                "bg": "#0d1117",
                "item_bg": "#010409",
            },
            "Red": {
                "accent": "#ff5555",
                "select": "#d73a49",
                "bg": "#140a0a",
                "item_bg": "#0a0505",
            },
            "Green": {
                "accent": "#3fb950",
                "select": "#2ea043",
                "bg": "#0a140d",
                "item_bg": "#050a06",
            },
            "Purple": {
                "accent": "#d2a8ff",
                "select": "#8957e5",
                "bg": "#120a17",
                "item_bg": "#09050b",
            },
        }
        t = themes[theme_name]

        # הוספתי פה QPushButton:checked כדי שהכפתורים יזהרו כשהם דלוקים!
        qss = f"""
            QMainWindow {{ background-color: {t['bg']}; }}
            QMenuBar {{ background-color: {t['bg']}; color: #c9d1d9; font-weight: bold; }}
            QMenuBar::item:selected {{ background-color: {t['select']}; color: white; border-radius: 4px; }}
            QMenu {{ background-color: {t['item_bg']}; color: #c9d1d9; border: 1px solid #30363d; }}
            QMenu::item:selected {{ background-color: {t['select']}; color: white; }}
            QLabel {{ color: #c9d1d9; font-weight: bold; }}
            QListWidget {{ 
                background-color: {t['item_bg']}; color: #c9d1d9; 
                border: 1px solid #30363d; border-radius: 5px; padding: 5px; font-size: 14px;
            }}
            QListWidget::item:selected {{ background-color: {t['select']}; color: white; }}
            QGroupBox {{ 
                color: #8b949e; border: 1px solid #30363d; 
                border-radius: 5px; margin-top: 15px; font-weight: bold;
            }}
            QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 3px 0 3px; }}
            QPushButton {{ 
                background-color: #21262d; color: #c9d1d9; 
                border: 1px solid #363b42; border-radius: 5px; padding: 8px 15px; font-weight: bold;
            }}
            QLabel#statusPlay {{ color: #00ff00; font-style: italic; font-size: 15px; font-weight: 900; }}
            QLabel#statusMode {{ color: #ff00ff; font-style: italic; font-size: 15px; font-weight: 900; }}
            QLabel#statusFreq {{ color: #00ffff; font-style: italic; font-size: 15px; font-weight: 900; }}
            QLabel#statusEngine {{ color: #00ff00; font-style: italic; font-size: 15px; font-weight: 900; }}
            QLabel#statusVer {{ color: #ffaa00; font-style: italic; font-size: 15px; font-weight: 900; }}
            
            
        """
        self.setStyleSheet(qss)

        self.lbl_playing.setStyleSheet(
            f"font-size: 18px; color: {t['accent']}; margin-top: 5px; margin-bottom: 5px;"
        )
        for lbl in self.findChildren(QLabel):
            if lbl.text() in [
                "29",
                "59",
                "119",
                "237",
                "474",
                "947",
                "1.8k",
                "3.7k",
                "7.5k",
                "15k",
            ]:
                lbl.setStyleSheet(f"font-size: 10px; color: {t['accent']};")

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

        top_bar = QHBoxLayout()
        btn_add = QPushButton("🎵 Add Files")
        btn_add.clicked.connect(self.add_files)
        btn_scan = QPushButton("📂 Scan Folder")
        btn_scan.clicked.connect(self.scan_folder)
        top_bar.addWidget(btn_add)
        top_bar.addWidget(btn_scan)
        top_bar.addStretch()
        main_layout.addLayout(top_bar)

        self.lbl_playing = QLabel("Ready to play...")
        main_layout.addWidget(self.lbl_playing)

        seek_layout = QHBoxLayout()
        self.lbl_time = QLabel("00:00")
        self.seek_slider = QSlider(Qt.Orientation.Horizontal)
        self.seek_slider.setRange(0, 100)
        self.seek_slider.sliderMoved.connect(self.on_seek)
        self.lbl_total = QLabel("00:00")
        seek_layout.addWidget(self.lbl_time)
        seek_layout.addWidget(self.seek_slider)
        seek_layout.addWidget(self.lbl_total)
        main_layout.addLayout(seek_layout)

        controls_layout = QHBoxLayout()
        btn_prev = QPushButton("⏮ Prev")
        btn_prev.clicked.connect(self.play_prev)
        btn_play = QPushButton("▶ Play / Pause")
        btn_play.clicked.connect(self.play_current)
        btn_next = QPushButton("⏭ Next")
        btn_next.clicked.connect(self.play_next)
        controls_layout.addStretch()
        controls_layout.addWidget(btn_prev)
        controls_layout.addWidget(btn_play)
        controls_layout.addWidget(btn_next)
        controls_layout.addStretch()
        main_layout.addLayout(controls_layout)

        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(self.play_selected_from_list)
        main_layout.addWidget(self.list_widget, stretch=1)

        # --- אזור האקולייזר המעודכן עם כפתורי האפקטים ---
        eq_group = QGroupBox(" EQ & MASTER ")
        eq_group.setMaximumHeight(260)  # הגדלנו קצת שיהיה מקום לכפתורים
        eq_main_layout = QVBoxLayout()

        # כפתורי האפקטים
        effects_layout = QHBoxLayout()

        self.btn_dsp = QPushButton("🎛️ DSP Mode")
        self.btn_dsp.setCheckable(True)  # מאפשר לכפתור להישאר לחוץ
        self.btn_dsp.clicked.connect(self.toggle_dsp)

        self.btn_bass = QPushButton("🔊 BASS BOOST")
        self.btn_bass.setCheckable(True)
        self.btn_bass.clicked.connect(self.toggle_bass)

        self.btn_flat = QPushButton("🔄 Flat")
        self.btn_flat.clicked.connect(self.reset_eq)

        effects_layout.addWidget(self.btn_dsp)
        effects_layout.addWidget(self.btn_bass)
        effects_layout.addWidget(self.btn_flat)
        effects_layout.addStretch()

        eq_main_layout.addLayout(effects_layout)

        # הסליידרים
        eq_layout = QHBoxLayout()
        self.sliders = []
        freqs = ["29", "59", "119", "237", "474", "947", "1.8k", "3.7k", "7.5k", "15k"]

        for i, freq in enumerate(freqs):
            band_layout = QVBoxLayout()
            slider = QSlider(Qt.Orientation.Vertical)
            slider.setRange(-24, 12)
            slider.setValue(0)
            slider.valueChanged.connect(lambda val, idx=i: self.set_eq(idx, val))

            lbl_freq = QLabel(freq)
            lbl_freq.setAlignment(Qt.AlignmentFlag.AlignCenter)

            band_layout.addWidget(slider, alignment=Qt.AlignmentFlag.AlignHCenter)
            band_layout.addWidget(lbl_freq, alignment=Qt.AlignmentFlag.AlignHCenter)
            eq_layout.addLayout(band_layout)
            self.sliders.append(slider)

        vol_layout = QVBoxLayout()
        self.vol_slider = QSlider(Qt.Orientation.Vertical)
        self.vol_slider.setRange(0, 100)
        self.vol_slider.setValue(50)
        self.vol_slider.valueChanged.connect(self.on_volume)

        lbl_vol = QLabel("VOL")
        lbl_vol.setStyleSheet("font-size: 11px; color: #8b949e;")
        lbl_vol.setAlignment(Qt.AlignmentFlag.AlignCenter)

        vol_layout.addWidget(self.vol_slider, alignment=Qt.AlignmentFlag.AlignHCenter)
        vol_layout.addWidget(lbl_vol, alignment=Qt.AlignmentFlag.AlignHCenter)

        eq_layout.addSpacing(30)
        eq_layout.addLayout(vol_layout)

        eq_main_layout.addLayout(eq_layout)
        eq_group.setLayout(eq_main_layout)
        main_layout.addWidget(eq_group)

        # --- שורת סטטוס בתחתית (Status Bar) ---
        status_layout = QHBoxLayout()
        status_layout.setContentsMargins(0, 10, 0, 0)

        self.lbl_status_play = QLabel("🔊 PLAYING")
        self.lbl_status_play.setObjectName("statusPlay")

        lbl_sep1 = QLabel(" | ")
        lbl_sep1.setStyleSheet("color: #8b949e; font-weight: bold;")

        self.lbl_status_mode = QLabel("UHD/4K Mode")
        self.lbl_status_mode.setObjectName("statusMode")

        lbl_sep2 = QLabel(" | ")
        lbl_sep2.setStyleSheet("color: #8b949e; font-weight: bold;")

        self.lbl_status_freq = QLabel("325.1kHz")
        self.lbl_status_freq.setObjectName("statusFreq")

        self.lbl_status_engine = QLabel(" GstremerBASS")
        self.lbl_status_engine.setObjectName("statusEngine")

        lbl_sep3 = QLabel(" | ")
        lbl_sep3.setStyleSheet("color: #8b949e; font-weight: bold;")

        self.lbl_status_ver = QLabel("v2.5 Stable")
        self.lbl_status_ver.setObjectName("statusVer")

        status_layout.addWidget(self.lbl_status_play)
        status_layout.addWidget(lbl_sep1)
        status_layout.addWidget(self.lbl_status_mode)
        status_layout.addWidget(lbl_sep2)
        status_layout.addWidget(self.lbl_status_freq)
        status_layout.addWidget(self.lbl_status_engine)
        status_layout.addStretch()  # דוחף את הגרסה ימינה עד הסוף
        status_layout.addWidget(lbl_sep3)
        status_layout.addWidget(self.lbl_status_ver)

        main_layout.addLayout(status_layout)

        self.apply_theme("Blue")

    # --- פונקציות האפקטים החדשות ---
    def toggle_bass(self, checked):
        if checked:
            self.btn_dsp.setChecked(False)  # מכבה את ה-DSP אם הוא דלק
            # נותן בוסט מטורף לנמוכים (29, 59, 119) ומוריד טיפה את השאר
            bass_preset = [10, 8, 5, 2, 0, 0, 0, 0, 0, 0]
            self.apply_eq_preset(bass_preset)
        else:
            self.reset_eq()

    def toggle_dsp(self, checked):
        if checked:
            self.btn_bass.setChecked(False)  # מכבה את הבס אם הוא דלק
            # צורת V קלאסית של DSP - בוסט לבסים וטרבלים, מנקה את האמצע
            dsp_preset = [6, 4, 1, -2, -3, -2, 1, 4, 6, 8]
            self.apply_eq_preset(dsp_preset)
        else:
            self.reset_eq()

    def reset_eq(self):
        self.btn_bass.setChecked(False)
        self.btn_dsp.setChecked(False)
        self.apply_eq_preset([0] * 10)

    def apply_eq_preset(self, values):
        """פונקציה שמעדכנת גם את הסליידרים במסך וגם את הסאונד בלייב"""
        for i, val in enumerate(values):
            self.sliders[i].setValue(val)
            self.set_eq(i, val)

    # --- שמירה וטעינה של הפלייליסט ---
    def load_playlist(self):
        saved_playlist = self.settings.value("playlist", [])
        if saved_playlist:
            for path in saved_playlist:
                if os.path.exists(path):
                    self.add_to_playlist(path)

    def closeEvent(self, event):
        self.player.set_state(Gst.State.NULL)
        self.settings.setValue("playlist", self.playlist)
        event.accept()

    # --- פונקציות לוגיקה כלליות ---
    def show_about(self):
        QMessageBox.about(
            self,
            "About Central Player Pro",
            "<h2>Central Player Pro</h2>"
            "<p><b>Version:</b> 2.5 Stable</p>"
            "<p>The fastest Qt/GStreamer player on Fedora KDE.</p>",
        )

    def set_eq(self, band_idx, val):
        self.equalizer.set_property(f"band{band_idx}", float(val))

    def add_to_playlist(self, path):
        if path not in self.playlist:
            self.playlist.append(path)
            self.list_widget.addItem(pathlib.Path(path).stem)

    def add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Songs", "", "Audio Files (*.mp3 *.wav *.flac *.m4a *.ogg)"
        )
        for f in files:
            self.add_to_playlist(f)

    def scan_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            for root, _, files in os.walk(folder):
                for file in files:
                    if pathlib.Path(file).suffix.lower() in AUDIO_EXT:
                        self.add_to_playlist(os.path.join(root, file))

    def play_selected_from_list(self, item):
        self.current_idx = self.list_widget.row(item)
        self.play_file(self.playlist[self.current_idx])

    def play_current(self):
        if self.current_idx >= 0:
            state = self.player.get_state(0).state
            if state == Gst.State.PLAYING:
                self.player.set_state(Gst.State.PAUSED)
                # הופך לאדום כשיש פאוזה
                self.lbl_status_play.setText("⏸ PAUSED")
                self.lbl_status_play.setStyleSheet(
                    "color: #ff5555; font-style: italic; font-size: 15px; font-weight: 900;"
                )
            else:
                self.player.set_state(Gst.State.PLAYING)
                # חוזר לירוק כשמנגן
                self.lbl_status_play.setText("🔊 PLAYING")
                self.lbl_status_play.setStyleSheet(
                    "color: #00ff00; font-style: italic; font-size: 15px; font-weight: 900;"
                )
        elif self.playlist:
            self.current_idx = 0
            self.play_file(self.playlist[0])
            self.lbl_status_play.setText("🔊 PLAYING")
            self.lbl_status_play.setStyleSheet(
                "color: #00ff00; font-style: italic; font-size: 15px; font-weight: 900;"
            )

    def play_next(self):
        if self.playlist and self.current_idx < len(self.playlist) - 1:
            self.current_idx += 1
            self.list_widget.setCurrentRow(self.current_idx)
            self.play_file(self.playlist[self.current_idx])

    def play_prev(self):
        if self.playlist and self.current_idx > 0:
            self.current_idx -= 1
            self.list_widget.setCurrentRow(self.current_idx)
            self.play_file(self.playlist[self.current_idx])

    def play_file(self, path):
        uri = pathlib.Path(path).absolute().as_uri()
        self.player.set_state(Gst.State.NULL)
        self.player.set_property("uri", uri)
        self.player.set_state(Gst.State.PLAYING)
        self.lbl_playing.setText(f"Now Playing: {pathlib.Path(path).stem}")

    def on_volume(self, val):
        self.player.set_property("volume", val / 100.0)

    def on_seek(self, val):
        self.player.seek_simple(
            Gst.Format.TIME,
            Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT,
            val * Gst.SECOND,
        )

    def update_player(self):
        bus = self.player.get_bus()
        msg = bus.pop()
        if msg and msg.type == Gst.MessageType.EOS:
            self.play_next()

        if not self.seek_slider.isSliderDown():
            ok, pos = self.player.query_position(Gst.Format.TIME)
            ok2, dur = self.player.query_duration(Gst.Format.TIME)
            if ok and ok2 and dur > 0:
                sec_pos = pos / Gst.SECOND
                sec_dur = dur / Gst.SECOND
                self.seek_slider.setMaximum(int(sec_dur))
                self.seek_slider.setValue(int(sec_pos))
                self.lbl_time.setText(format_time(sec_pos))
                self.lbl_total.setText(format_time(sec_dur))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = PlayerWindow()
    window.show()
    sys.exit(app.exec())
