import sys
import os
import pathlib
import gi

# GStreamer
gi.require_version('Gst', '1.0')
from gi.repository import Gst

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QSlider, QLabel, 
                             QListWidget, QFileDialog, QGroupBox)
from PyQt6.QtCore import Qt, QTimer

AUDIO_EXT = [".mp3", ".wav", ".ogg", ".flac", ".m4a", ".mp4"]

def format_time(seconds):
    m, s = divmod(int(seconds), 60)
    return f"{m:02d}:{s:02d}"

class PlayerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Central Player Pro v2.5 - Qt Edition")
        self.resize(1100, 650)

        # --- מנוע GStreamer ---
        Gst.init(None)
        self.player = Gst.ElementFactory.make("playbin")
        self.equalizer = Gst.ElementFactory.make("equalizer-10bands")
        
        # הטריק מהראסט - זורקים את הווידאו לפח כדי ש-Wayland לא יקרוס
        self.fakesink = Gst.ElementFactory.make("fakesink")
        self.player.set_property("video-sink", self.fakesink)
        
        self.player.set_property("audio-filter", self.equalizer)
        self.player.set_property("volume", 0.5)

        self.playlist = []
        self.current_idx = -1

        # --- בניית הממשק ---
        self.init_ui()

        # טיימר למשיכת נתונים (פרוגרס והודעות מ-GStreamer)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_player)
        self.timer.start(100) # מתעדכן כל עשירית שנייה

    def init_ui(self):
        # --- עיצוב Dark Mode בהשראת הראסט ---
        self.setStyleSheet("""
            QMainWindow { background-color: #0d1117; }
            QLabel { color: #c9d1d9; font-weight: bold; }
            QListWidget { 
                background-color: #010409; 
                color: #c9d1d9; 
                border: 1px solid #30363d;
                border-radius: 5px;
                padding: 5px;
                font-size: 14px;
            }
            QListWidget::item:selected { background-color: #1f6feb; color: white; }
            QGroupBox { 
                color: #8b949e; 
                border: 1px solid #30363d; 
                border-radius: 5px; 
                margin-top: 15px; 
                font-weight: bold;
            }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 3px 0 3px; }
            QPushButton { 
                background-color: #21262d; 
                color: #c9d1d9; 
                border: 1px solid #363b42; 
                border-radius: 5px; 
                padding: 8px 15px; 
                font-weight: bold;
            }
            QPushButton:hover { background-color: #30363d; border-color: #8b949e; }
        """)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

        # --- שורה עליונה (כפתורים, נגן ופרוגרס) ---
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
        self.lbl_playing.setStyleSheet("font-size: 18px; color: #58a6ff; margin-top: 5px; margin-bottom: 5px;")
        main_layout.addWidget(self.lbl_playing)

        # סליידר זמן מתחת לשם השיר
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

        # --- אמצע: הפלייליסט (מקבל את רוב המקום) ---
        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(self.play_selected_from_list)
        main_layout.addWidget(self.list_widget, stretch=1) 

        # --- למטה: אקולייזר (קומפקטי ומוגבל בגובה עם תדרים) ---
        eq_group = QGroupBox(" EQ & MASTER ")
        eq_group.setMaximumHeight(200) # גובה קבוע שלא ישתלט על המסך
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
            lbl_freq.setStyleSheet("font-size: 10px; color: #58a6ff;")
            lbl_freq.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            band_layout.addWidget(slider, alignment=Qt.AlignmentFlag.AlignHCenter)
            band_layout.addWidget(lbl_freq, alignment=Qt.AlignmentFlag.AlignHCenter)
            eq_layout.addLayout(band_layout)
            self.sliders.append(slider)
        
        # הווליום ליד האקולייזר בצד ימין
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
        
        eq_layout.addSpacing(30) # רווח בין האקולייזר לווליום
        eq_layout.addLayout(vol_layout)
        
        eq_group.setLayout(eq_layout)
        main_layout.addWidget(eq_group)

    # --- פונקציות לוגיקה ---
    def set_eq(self, band_idx, val):
        self.equalizer.set_property(f"band{band_idx}", float(val))

    def add_to_playlist(self, path):
        if path not in self.playlist:
            self.playlist.append(path)
            self.list_widget.addItem(pathlib.Path(path).stem)

    def add_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select Songs", "", "Audio Files (*.mp3 *.wav *.flac *.m4a *.ogg)")
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
            # אם הוא כבר מתנגן נעשה Pause, אם לא ננגן
            state = self.player.get_state(0).state
            if state == Gst.State.PLAYING:
                self.player.set_state(Gst.State.PAUSED)
            else:
                self.player.set_state(Gst.State.PLAYING)
        elif self.playlist:
            self.current_idx = 0
            self.play_file(self.playlist[0])

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
        self.player.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT, val * Gst.SECOND)

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

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle("Fusion") 
    window = PlayerWindow()
    window.show()
    sys.exit(app.exec())