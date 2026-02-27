"""
PyDown - Professional Download Manager
כלי הורדה מקצועי עם ממשק PyQt6

התקנה:
    pip install PyQt6 requests

הרצה:
    python pydown.py
"""

import sys
import os
import math
import time
import threading
import requests
from urllib.parse import urlparse, unquote
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QLabel, QFileDialog, QTableWidget,
    QTableWidgetItem, QHeaderView, QProgressBar, QDialog,
    QMessageBox, QFrame, QSizePolicy, QAbstractItemView, QStatusBar,
    QToolBar
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize
from PyQt6.QtGui import (
    QColor, QPalette, QFont, QAction
)


# ─── Color Palette ────────────────────────────────────────────────────────────

COLORS = {
    "bg_dark":      "#0D1117",
    "bg_card":      "#161B22",
    "bg_hover":     "#1C2129",
    "border":       "#30363D",
    "accent":       "#00D4FF",
    "accent_dim":   "#0099BB",
    "success":      "#39D353",
    "warning":      "#F0A500",
    "danger":       "#F85149",
    "text_primary": "#E6EDF3",
    "text_muted":   "#7D8590",
    "text_dim":     "#484F58",
    "progress_bg":  "#21262D",
}

STYLESHEET = f"""
QMainWindow, QWidget {{
    background-color: {COLORS["bg_dark"]};
    color: {COLORS["text_primary"]};
    font-family: 'Segoe UI', 'SF Pro Display', 'Helvetica Neue', sans-serif;
    font-size: 13px;
}}
QToolBar {{
    background-color: {COLORS["bg_card"]};
    border-bottom: 1px solid {COLORS["border"]};
    padding: 6px 12px;
    spacing: 8px;
}}
QPushButton {{
    background-color: {COLORS["bg_card"]};
    color: {COLORS["text_primary"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 8px;
    padding: 8px 16px;
    font-size: 13px;
    font-weight: 500;
}}
QPushButton:hover {{
    background-color: {COLORS["bg_hover"]};
    border-color: {COLORS["accent"]};
    color: {COLORS["accent"]};
}}
QPushButton:pressed {{
    background-color: {COLORS["accent_dim"]};
    color: white;
}}
QPushButton#accentBtn {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 {COLORS["accent"]}, stop:1 {COLORS["accent_dim"]});
    color: {COLORS["bg_dark"]};
    border: none;
    font-weight: 700;
}}
QPushButton#accentBtn:hover {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #33DDFF, stop:1 {COLORS["accent"]});
    color: {COLORS["bg_dark"]};
}}
QPushButton#dangerBtn {{
    background-color: transparent;
    color: {COLORS["danger"]};
    border: 1px solid {COLORS["danger"]};
}}
QPushButton#dangerBtn:hover {{
    background-color: {COLORS["danger"]};
    color: white;
}}
QLineEdit {{
    background-color: {COLORS["bg_card"]};
    color: {COLORS["text_primary"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 8px;
    padding: 10px 14px;
    font-size: 13px;
}}
QLineEdit:focus {{
    border-color: {COLORS["accent"]};
    background-color: {COLORS["bg_hover"]};
}}
QTableWidget {{
    background-color: transparent;
    border: none;
    gridline-color: {COLORS["border"]};
    selection-background-color: {COLORS["bg_hover"]};
    alternate-background-color: rgba(255,255,255,0.02);
    outline: none;
}}
QTableWidget::item {{
    padding: 10px 12px;
    border-bottom: 1px solid {COLORS["border"]};
    color: {COLORS["text_primary"]};
}}
QTableWidget::item:selected {{
    background-color: {COLORS["bg_hover"]};
    color: {COLORS["accent"]};
}}
QHeaderView::section {{
    background-color: {COLORS["bg_card"]};
    color: {COLORS["text_muted"]};
    border: none;
    border-bottom: 2px solid {COLORS["border"]};
    padding: 10px 12px;
    font-size: 11px;
    font-weight: 600;
}}
QScrollBar:vertical {{
    background: {COLORS["bg_dark"]};
    width: 6px;
    border-radius: 3px;
}}
QScrollBar::handle:vertical {{
    background: {COLORS["border"]};
    border-radius: 3px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background: {COLORS["accent_dim"]};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QStatusBar {{
    background-color: {COLORS["bg_card"]};
    color: {COLORS["text_muted"]};
    border-top: 1px solid {COLORS["border"]};
    font-size: 12px;
    padding: 0 12px;
}}
QDialog {{
    background-color: {COLORS["bg_dark"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 12px;
}}
QFrame#card {{
    background-color: {COLORS["bg_card"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 12px;
}}
QProgressBar {{
    background-color: {COLORS["progress_bg"]};
    border-radius: 3px;
    border: none;
    height: 6px;
    text-align: center;
}}
QProgressBar::chunk {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 {COLORS["accent"]}, stop:1 {COLORS["accent_dim"]});
    border-radius: 3px;
}}
"""


# ─── Utilities ────────────────────────────────────────────────────────────────

def format_size(b):
    if b <= 0: return "0 B"
    units = ["B","KB","MB","GB","TB"]
    i = min(int(math.floor(math.log(b, 1024))), 4)
    return f"{round(b / math.pow(1024, i), 2)} {units[i]}"

def format_speed(bps):
    return f"{format_size(bps)}/s" if bps > 0 else "—"

def format_eta(sec):
    if sec <= 0 or sec == float('inf'): return "—"
    m, s = divmod(int(sec), 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"

def get_filename(url, headers=None):
    if headers:
        cd = headers.get('content-disposition', '')
        if 'filename=' in cd:
            return cd.split('filename=')[-1].strip().strip('"\'')
    name = unquote(os.path.basename(urlparse(url).path))
    return name or f"download_{int(time.time())}"


# ─── Download Worker ──────────────────────────────────────────────────────────

class DownloadWorker(QThread):
    progress       = pyqtSignal(int, int, int, float, float)  # row, dl, total, speed, eta
    finished       = pyqtSignal(int, bool, str)
    status_changed = pyqtSignal(int, str)

    def __init__(self, row, url, save_path, threads=8):
        super().__init__()
        self.row = row
        self.url = url
        self.save_path = save_path
        self.num_threads = threads
        self._pause = False
        self._cancel = False
        self._lock = threading.Lock()
        self._downloaded = 0

    def pause(self):  self._pause = True
    def resume(self): self._pause = False
    def cancel(self): self._cancel = True; self._pause = False

    def run(self):
        try:
            self._download()
        except Exception as e:
            self.finished.emit(self.row, False, str(e))

    def _download(self):
        try:
            head = requests.head(self.url, allow_redirects=True, timeout=15)
            total = int(head.headers.get('content-length', 0))
            supports_range = 'bytes' in head.headers.get('accept-ranges', '')
        except Exception:
            total, supports_range = 0, False

        self.status_changed.emit(self.row, "מוריד")

        if supports_range and total > 0 and self.num_threads > 1:
            self._multi(total)
        else:
            self._single(total)

    def _single(self, total):
        try:
            resp = requests.get(self.url, stream=True, timeout=30)
            resp.raise_for_status()
            if not total:
                total = int(resp.headers.get('content-length', 0))
            downloaded, last_bytes, last_t = 0, 0, time.time()
            with open(self.save_path, 'wb') as f:
                for chunk in resp.iter_content(65536):
                    if self._cancel:
                        self.finished.emit(self.row, False, "בוטל"); return
                    while self._pause: time.sleep(0.1)
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        now = time.time()
                        if now - last_t >= 0.5:
                            speed = (downloaded - last_bytes) / (now - last_t)
                            eta = (total - downloaded) / speed if speed > 0 and total else 0
                            self.progress.emit(self.row, downloaded, total, speed, eta)
                            last_t, last_bytes = now, downloaded
            self.finished.emit(self.row, True, "הושלם")
        except Exception as e:
            self.finished.emit(self.row, False, str(e))

    def _multi(self, total):
        chunk = math.ceil(total / self.num_threads)
        ranges = [(i * chunk, min((i+1)*chunk - 1, total-1)) for i in range(self.num_threads)]
        temps = [f"{self.save_path}.part{i}" for i in range(len(ranges))]
        errors = []
        self._downloaded = 0

        def dl_chunk(s, e, path):
            try:
                r = requests.get(self.url, headers={'Range': f'bytes={s}-{e}'}, stream=True, timeout=60)
                r.raise_for_status()
                with open(path, 'wb') as f:
                    for ch in r.iter_content(65536):
                        if self._cancel: return
                        while self._pause: time.sleep(0.1)
                        if ch:
                            f.write(ch)
                            with self._lock: self._downloaded += len(ch)
            except Exception as ex:
                errors.append(str(ex))

        threads = [threading.Thread(target=dl_chunk, args=(s, e, t), daemon=True)
                   for (s, e), t in zip(ranges, temps)]
        for t in threads: t.start()

        last_bytes, last_t = 0, time.time()
        while any(t.is_alive() for t in threads):
            if self._cancel:
                for t in threads: t.join(0.1)
                self.finished.emit(self.row, False, "בוטל"); return
            now = time.time()
            if now - last_t >= 0.5:
                curr = self._downloaded
                speed = (curr - last_bytes) / (now - last_t)
                eta = (total - curr) / speed if speed > 0 else 0
                self.progress.emit(self.row, curr, total, speed, eta)
                last_t, last_bytes = now, curr
            time.sleep(0.2)

        if errors:
            self.finished.emit(self.row, False, errors[0]); return

        try:
            with open(self.save_path, 'wb') as out:
                for p in temps:
                    with open(p, 'rb') as f: out.write(f.read())
                    os.remove(p)
            self.finished.emit(self.row, True, "הושלם")
        except Exception as e:
            self.finished.emit(self.row, False, f"שגיאת מיזוג: {e}")


# ─── Add Download Dialog ──────────────────────────────────────────────────────

class AddDownloadDialog(QDialog):
    def __init__(self, parent=None, default_dir=""):
        super().__init__(parent)
        self.setWindowTitle("הוסף הורדה חדשה")
        self.setMinimumWidth(540)
        self.save_dir = default_dir or str(Path.home() / "Downloads")
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(14)

        title = QLabel("⬇  הורדה חדשה")
        title.setStyleSheet(f"font-size:20px; font-weight:700; color:{COLORS['accent']};")
        layout.addWidget(title)

        layout.addWidget(self._section("כתובת URL"))
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://example.com/file.zip")
        self.url_input.setMinimumHeight(42)
        layout.addWidget(self.url_input)

        layout.addWidget(self._section("תיקיית שמירה"))
        row = QHBoxLayout()
        self.path_input = QLineEdit(self.save_dir)
        self.path_input.setMinimumHeight(42)
        browse = QPushButton("📁 עיין")
        browse.setFixedWidth(90)
        browse.setMinimumHeight(42)
        browse.clicked.connect(self._browse)
        row.addWidget(self.path_input)
        row.addWidget(browse)
        layout.addLayout(row)

        layout.addWidget(self._section("מספר חוטים (1-16)"))
        self.thread_input = QLineEdit("8")
        self.thread_input.setMinimumHeight(42)
        layout.addWidget(self.thread_input)

        layout.addSpacing(8)
        btns = QHBoxLayout()
        cancel = QPushButton("ביטול")
        cancel.setObjectName("dangerBtn")
        cancel.clicked.connect(self.reject)
        ok = QPushButton("⬇  התחל הורדה")
        ok.setObjectName("accentBtn")
        ok.setMinimumHeight(44)
        ok.clicked.connect(self._ok)
        btns.addWidget(cancel)
        btns.addStretch()
        btns.addWidget(ok)
        layout.addLayout(btns)

    def _section(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet(f"font-size:11px; font-weight:600; color:{COLORS['text_muted']}; text-transform:uppercase; letter-spacing:1px;")
        return lbl

    def _browse(self):
        f = QFileDialog.getExistingDirectory(self, "בחר תיקייה", self.save_dir)
        if f: self.path_input.setText(f)

    def _ok(self):
        if not self.url_input.text().strip():
            QMessageBox.warning(self, "שגיאה", "נא להזין כתובת URL"); return
        self.accept()

    def get_data(self):
        try: t = max(1, min(16, int(self.thread_input.text())))
        except: t = 8
        return {"url": self.url_input.text().strip(),
                "save_dir": self.path_input.text().strip(),
                "threads": t}


# ─── Main Window ──────────────────────────────────────────────────────────────

class PyDownWindow(QMainWindow):
    STATUS_ICONS  = {"ממתין":"⏳","מוריד":"⬇","מושהה":"⏸","הושלם":"✅","שגיאה":"❌","בוטל":"🚫"}
    STATUS_COLORS = {"מוריד":COLORS["accent"],"הושלם":COLORS["success"],
                     "שגיאה":COLORS["danger"],"בוטל":COLORS["danger"],
                     "מושהה":COLORS["warning"],"ממתין":COLORS["text_muted"]}

    C_NAME, C_SIZE, C_PROG, C_SPEED, C_ETA, C_STATUS, C_THREADS = range(7)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyDown — מנהל הורדות מקצועי")
        self.resize(1060, 660)
        self.setMinimumSize(800, 500)
        self.downloads = []
        self.workers   = {}
        self.save_dir  = str(Path.home() / "Downloads")
        self._build()
        self._timer = QTimer()
        self._timer.timeout.connect(self._refresh_stats)
        self._timer.start(1000)

    def _build(self):
        self.setStyleSheet(STYLESHEET)

        # ── Toolbar
        tb = QToolBar()
        tb.setMovable(False)
        tb.setIconSize(QSize(16, 16))
        self.addToolBar(tb)

        for label, shortcut, slot in [
            ("⬇  הורדה חדשה", "Ctrl+N", self._add_download),
            (None, None, None),
            ("▶  המשך",   None, self._resume_selected),
            ("⏸  השהה",   None, self._pause_selected),
            (None, None, None),
            ("🗑  מחק",    "Del", self._delete_selected),
            (None, None, None),
            ("📁  תיקייה", None, self._change_folder),
        ]:
            if label is None:
                tb.addSeparator(); continue
            act = QAction(label, self)
            if shortcut: act.setShortcut(shortcut)
            act.triggered.connect(slot)
            tb.addAction(act)

        # ── Central
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(16, 16, 16, 8)
        layout.setSpacing(12)
        self.setCentralWidget(central)

        # Header card
        hcard = QFrame(); hcard.setObjectName("card")
        hl = QHBoxLayout(hcard)
        hl.setContentsMargins(20, 14, 20, 14)
        logo = QLabel("⬇ PyDown")
        logo.setStyleSheet(f"font-size:22px; font-weight:800; color:{COLORS['accent']}; letter-spacing:-1px;")
        sub = QLabel("מנהל הורדות מקצועי  •  Multi-Threaded  •  Fast")
        sub.setStyleSheet(f"color:{COLORS['text_muted']}; font-size:12px;")
        self.speed_lbl = QLabel("")
        self.speed_lbl.setStyleSheet(f"color:{COLORS['accent']}; font-size:14px; font-weight:700;")
        hl.addWidget(logo); hl.addWidget(sub); hl.addStretch(); hl.addWidget(self.speed_lbl)
        layout.addWidget(hcard)

        # Table
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(["שם קובץ", "גודל", "התקדמות", "מהירות", "ETA", "סטטוס", "חוטים"])
        h = self.table.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for col, w in [(1,100),(2,200),(3,110),(4,80),(5,100),(6,65)]:
            h.setSectionResizeMode(col, QHeaderView.ResizeMode.Fixed)
            self.table.setColumnWidth(col, w)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        layout.addWidget(self.table)

        # Status bar
        self.sb = QStatusBar()
        self.setStatusBar(self.sb)
        self.sb.showMessage(f"מוכן  |  תיקיית שמירה: {self.save_dir}")

    # ── Add ───────────────────────────────────────────────────────────────────

    def _add_download(self):
        dlg = AddDownloadDialog(self, self.save_dir)
        if dlg.exec() != QDialog.DialogCode.Accepted: return
        d = dlg.get_data()
        self._start(d["url"], d["save_dir"], d["threads"])

    def _start(self, url, save_dir, threads=8):
        os.makedirs(save_dir, exist_ok=True)
        try:
            head = requests.head(url, allow_redirects=True, timeout=10)
            fname = get_filename(url, head.headers)
        except Exception:
            fname = get_filename(url)

        save_path = os.path.join(save_dir, fname)
        base, ext = os.path.splitext(save_path)
        c = 1
        while os.path.exists(save_path):
            save_path = f"{base}_{c}{ext}"; c += 1

        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setRowHeight(row, 52)

        self.downloads.append({
            "url": url, "filename": os.path.basename(save_path),
            "save_path": save_path, "total": 0, "downloaded": 0,
            "speed": 0, "eta": 0, "status": "ממתין", "threads": threads
        })

        for col, val in [(self.C_NAME, os.path.basename(save_path)),
                         (self.C_SIZE, "—"), (self.C_SPEED, "—"),
                         (self.C_ETA, "—"), (self.C_THREADS, str(threads))]:
            item = QTableWidgetItem(val)
            if col == self.C_NAME: item.setToolTip(url)
            self.table.setItem(row, col, item)
        self._set_status(row, "ממתין")

        pb = QProgressBar()
        pb.setRange(0, 100); pb.setValue(0)
        pb.setTextVisible(False); pb.setFixedHeight(6)
        self.table.setCellWidget(row, self.C_PROG, pb)

        w = DownloadWorker(row, url, save_path, threads)
        w.progress.connect(self._on_progress)
        w.finished.connect(self._on_finished)
        w.status_changed.connect(self._on_status_changed)
        self.workers[row] = w
        w.start()
        self.sb.showMessage(f"הורדה החלה: {os.path.basename(save_path)}")

    # ── Signals ───────────────────────────────────────────────────────────────

    def _on_progress(self, row, dl, total, speed, eta):
        if row >= len(self.downloads): return
        m = self.downloads[row]
        m["downloaded"], m["total"], m["speed"], m["eta"] = dl, total, speed, eta
        pct = int(dl / total * 100) if total else 0
        pb = self.table.cellWidget(row, self.C_PROG)
        if pb: pb.setValue(pct)
        size_str = f"{format_size(dl)} / {format_size(total)}" if total else format_size(dl)
        self.table.setItem(row, self.C_SIZE,  QTableWidgetItem(size_str))
        self.table.setItem(row, self.C_SPEED, QTableWidgetItem(format_speed(speed)))
        self.table.setItem(row, self.C_ETA,   QTableWidgetItem(format_eta(eta)))

    def _on_finished(self, row, ok, msg):
        if row >= len(self.downloads): return
        status = "הושלם" if ok else ("בוטל" if msg == "בוטל" else "שגיאה")
        self.downloads[row]["status"] = status
        self._set_status(row, status)
        pb = self.table.cellWidget(row, self.C_PROG)
        if pb and ok: pb.setValue(100)
        self.table.setItem(row, self.C_SPEED, QTableWidgetItem("—"))
        self.table.setItem(row, self.C_ETA,   QTableWidgetItem("—"))
        fname = self.downloads[row]["filename"]
        self.sb.showMessage(f"{'✅ הושלם' if ok else '❌ שגיאה'}: {fname}" + ("" if ok else f" — {msg}"))

    def _on_status_changed(self, row, status):
        if row < len(self.downloads): self.downloads[row]["status"] = status
        self._set_status(row, status)

    def _set_status(self, row, status):
        icon  = self.STATUS_ICONS.get(status, "")
        color = self.STATUS_COLORS.get(status, COLORS["text_primary"])
        item = QTableWidgetItem(f"{icon}  {status}")
        item.setForeground(QColor(color))
        bold = status in ("מוריד", "הושלם")
        item.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold if bold else QFont.Weight.Normal))
        self.table.setItem(row, self.C_STATUS, item)

    # ── Toolbar Actions ───────────────────────────────────────────────────────

    def _selected_rows(self):
        return list({i.row() for i in self.table.selectedIndexes()})

    def _pause_selected(self):
        for row in self._selected_rows():
            w = self.workers.get(row)
            if w and w.isRunning():
                w.pause(); self._on_status_changed(row, "מושהה")

    def _resume_selected(self):
        for row in self._selected_rows():
            meta = self.downloads[row]
            w = self.workers.get(row)
            if w and w.isRunning():
                w.resume(); self._on_status_changed(row, "מוריד")
            elif meta["status"] in ("שגיאה", "בוטל", "מושהה"):
                if w: w.cancel()
                nw = DownloadWorker(row, meta["url"], meta["save_path"], meta["threads"])
                nw.progress.connect(self._on_progress)
                nw.finished.connect(self._on_finished)
                nw.status_changed.connect(self._on_status_changed)
                self.workers[row] = nw
                nw.start()
                pb = self.table.cellWidget(row, self.C_PROG)
                if pb: pb.setValue(0)

    def _delete_selected(self):
        rows = sorted(self._selected_rows(), reverse=True)
        if not rows: return
        if QMessageBox.question(self, "מחיקה", f"למחוק {len(rows)} הורדה/ות?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes:
            return
        for row in rows:
            w = self.workers.pop(row, None)
            if w: w.cancel(); w.wait(300)
            self.table.removeRow(row)
            if row < len(self.downloads): self.downloads.pop(row)
            nw = {}
            for r, wk in self.workers.items():
                nr = r if r < row else r - 1
                wk.row = nr; nw[nr] = wk
            self.workers = nw

    def _change_folder(self):
        f = QFileDialog.getExistingDirectory(self, "בחר תיקייה", self.save_dir)
        if f:
            self.save_dir = f
            self.sb.showMessage(f"תיקיית שמירה: {self.save_dir}")

    # ── Stats ─────────────────────────────────────────────────────────────────

    def _refresh_stats(self):
        active = [d for d in self.downloads if d["status"] == "מוריד"]
        total_speed = sum(d["speed"] for d in active)
        done = sum(1 for d in self.downloads if d["status"] == "הושלם")
        if total_speed > 0:
            self.speed_lbl.setText(f"⬇ {format_speed(total_speed)}")
        else:
            self.speed_lbl.setText(f"{len(active)} פעיל  •  {done} הושלמו")

    # ── Close ─────────────────────────────────────────────────────────────────

    def closeEvent(self, e):
        active = [r for r, w in self.workers.items() if w.isRunning()]
        if active:
            if QMessageBox.question(self, "יציאה", f"יש {len(active)} הורדות פעילות. לצאת?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes:
                e.ignore(); return
        for w in self.workers.values(): w.cancel()
        e.accept()


# ─── Entry Point ──────────────────────────────────────────────────────────────

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("PyDown")
    app.setStyle("Fusion")

    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window,          QColor(COLORS["bg_dark"]))
    palette.setColor(QPalette.ColorRole.WindowText,      QColor(COLORS["text_primary"]))
    palette.setColor(QPalette.ColorRole.Base,            QColor(COLORS["bg_card"]))
    palette.setColor(QPalette.ColorRole.AlternateBase,   QColor(COLORS["bg_hover"]))
    palette.setColor(QPalette.ColorRole.Text,            QColor(COLORS["text_primary"]))
    palette.setColor(QPalette.ColorRole.Button,          QColor(COLORS["bg_card"]))
    palette.setColor(QPalette.ColorRole.ButtonText,      QColor(COLORS["text_primary"]))
    palette.setColor(QPalette.ColorRole.Highlight,       QColor(COLORS["accent"]))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(COLORS["bg_dark"]))
    app.setPalette(palette)

    win = PyDownWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
