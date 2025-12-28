import sys, os, time, random, subprocess, threading, json, traceback
import tkinter as tk
from import_libs import *
_active_loader_proc = None
_worker_ref = None
_result_data = {"status": "idle", "data": None}
def get_base_directory():
    if getattr(sys, 'frozen', False): return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))
def get_assets_directory():
    base_dir = get_base_directory()
    if getattr(sys, 'frozen', False): return os.path.join(base_dir, "Assets")
    return base_dir
def get_resources_directory():
    return os.path.join(get_assets_directory(), "resources")
def get_path(filename):
    return os.path.normpath(os.path.join(get_resources_directory(), filename))
def _spawn_process(args):
    try:
        exe = sys.executable
        cmd = [exe] + args if getattr(sys, 'frozen', False) else [exe, os.path.abspath(__file__)] + args
        return subprocess.Popen(cmd, creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.PIPE)
    except: return None
if "--spawn-loader" in sys.argv:
    from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton, QTextEdit, QGraphicsOpacityEffect
    from PySide6.QtCore import Qt, QTimer, QThread, Signal, QPropertyAnimation, QEasingCurve
    from PySide6.QtGui import QPixmap, QColor, QPainter, QConicalGradient, QPen
    class STDINListener(QThread):
        message_received = Signal(dict)
        def run(self):
            while True:
                line = sys.stdin.readline()
                if not line: break
                try:
                    data = json.loads(line)
                    self.message_received.emit(data)
                except: pass
    class OverlayController(QWidget):
        def __init__(self, start_time, phrases):
            super().__init__()
            self.phrases = phrases
            self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
            self.setAttribute(Qt.WA_TranslucentBackground)
            self.setMinimumSize(850, 500)
            self.is_dark = self._load_theme_pref()
            self.main_layout = QVBoxLayout(self)
            self.container = QFrame()
            self.container.setObjectName("mainContainer")
            self.main_layout.addWidget(self.container)
            self.inner = QVBoxLayout(self.container)
            self.inner.setContentsMargins(30, 10, 30, 30)
            self.setup_loader_ui(start_time)
            self.listener = STDINListener()
            self.listener.message_received.connect(self.handle_message)
            self.listener.start()
        def _load_theme_pref(self):
            try:
                cfg = os.path.join(get_assets_directory(), "data", "configs", "user.cfg")
                if os.path.exists(cfg):
                    with open(cfg, 'r') as f: return json.load(f).get("theme") == "dark"
            except: pass
            return True
        def clear_layout(self):
            while self.inner.count():
                child = self.inner.takeAt(0)
                if child.widget(): child.widget().deleteLater()
                elif child.layout(): self._clear_sub_layout(child.layout())
        def _clear_sub_layout(self, layout):
            while layout.count():
                child = layout.takeAt(0)
                if child.widget(): child.widget().deleteLater()
                elif child.layout(): self._clear_sub_layout(child.layout())
        def setup_loader_ui(self, start_time):
            self.start_ts = start_time
            self._angle = 0
            bg = "rgba(5, 7, 12, 252)" if self.is_dark else "rgba(245, 245, 245, 252)"
            txt = "white" if self.is_dark else "#1a1a1a"
            self.container.setStyleSheet(f"#mainContainer {{ background-color: {bg}; border-radius: 40px; border: none; }}")
            top_bar = QHBoxLayout(); top_bar.addStretch()
            self.close_btn = QPushButton("✕")
            self.close_btn.setFixedSize(40, 40)
            self.close_btn.clicked.connect(self.safe_exit)
            self.close_btn.setStyleSheet(f"background: transparent; color: {txt}; font-size: 20px; font-weight: bold; border: none; margin-top: 10px; margin-right: 10px;")
            top_bar.addWidget(self.close_btn); self.inner.addLayout(top_bar); self.inner.addStretch()
            self.label = QLabel(random.choice(self.phrases))
            self.label.setAlignment(Qt.AlignCenter); self.label.setWordWrap(True)
            self.label.setStyleSheet(f"color: {txt}; font-family: 'Segoe UI'; font-size: 15px; font-weight: 700; background: transparent; border: none;")
            self.opacity_effect = QGraphicsOpacityEffect(self.label); self.label.setGraphicsEffect(self.opacity_effect)
            self.inner.addWidget(self.label)
            self.icon_label = QLabel(); self.icon_label.setAlignment(Qt.AlignCenter)
            p = get_path("Xenolord.webp")
            if os.path.exists(p):
                pix = QPixmap(p); self.icon_label.setPixmap(pix.scaled(140, 140, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            self.inner.addWidget(self.icon_label)
            self.timer_label = QLabel("00:00.00")
            self.timer_label.setAlignment(Qt.AlignCenter)
            self.timer_label.setStyleSheet(f"color: #00f2ff; font-family: 'Consolas'; font-size: 24px; font-weight: bold; background: transparent; border: none;")
            self.inner.addWidget(self.timer_label); self.inner.addStretch()
            self.tick_timer = QTimer(self); self.tick_timer.timeout.connect(self.update_loader); self.tick_timer.start(10)
            self.phrase_timer = QTimer(self); self.phrase_timer.timeout.connect(self.cycle_phrase); self.phrase_timer.start(3000)
        def cycle_phrase(self):
            self.anim = QPropertyAnimation(self.opacity_effect, b"opacity")
            self.anim.setDuration(400); self.anim.setStartValue(1.0); self.anim.setEndValue(0.0)
            self.anim.finished.connect(self._change_and_fade_in); self.anim.start()
        def _change_and_fade_in(self):
            self.label.setText(random.choice(self.phrases))
            self.anim = QPropertyAnimation(self.opacity_effect, b"opacity")
            self.anim.setDuration(400); self.anim.setStartValue(0.0); self.anim.setEndValue(1.0); self.anim.start()
        def update_loader(self):
            elapsed = time.time() - self.start_ts
            self._angle = (elapsed * 300) % 360
            self.timer_label.setText(f"{int(elapsed//60):02d}:{int(elapsed%60):02d}.{int((elapsed*100)%100):02d}")
            self.update()
        def handle_message(self, data):
            cmd = data.get("cmd")
            if cmd == "error": self.switch_to_error(data)
            elif cmd == "exit": self.safe_exit()
        def safe_exit(self):
            QApplication.quit()
            os._exit(0)
        def copy_to_clipboard(self, text, btn):
            try:
                subprocess.run(['clip.exe'], input=text.encode('utf-16'), check=True)
                old_txt = btn.text(); btn.setText("COPIED!")
                QTimer.singleShot(2000, lambda: btn.setText(old_txt))
            except:
                try:
                    root = tk.Tk(); root.withdraw()
                    root.clipboard_clear(); root.clipboard_append(text)
                    root.update(); root.destroy()
                except: pass
        def switch_to_error(self, data):
            if hasattr(self, "tick_timer"): self.tick_timer.stop()
            if hasattr(self, "phrase_timer"): self.phrase_timer.stop()
            self.clear_layout(); self.repaint()
            bg = "#0f0f0f" if self.is_dark else "#ffffff"
            brd = "#ff3333"
            txt = "#ffffff" if self.is_dark else "#000000"
            btn_bg = "#1e1e1e" if self.is_dark else "#e0e0e0"
            btn_txt = "#ffffff" if self.is_dark else "#000000"
            self.container.setStyleSheet(f"#mainContainer {{ background-color: {bg}; border-radius: 20px; border: 3px solid {brd}; }}")
            head = QHBoxLayout()
            img_p = get_path("lamball_error.webp")
            def mk_ico():
                l = QLabel(); l.setStyleSheet("border:none;background:transparent;")
                if os.path.exists(img_p):
                    pix = QPixmap(img_p); l.setPixmap(pix.scaled(70, 70, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                return l
            t_lbl = QLabel(data.get("title", "ERROR"))
            t_lbl.setStyleSheet(f"color:{brd};font-weight:900;font-size:26px;border:none;background:transparent;")
            head.addStretch(); head.addWidget(mk_ico()); head.addSpacing(15); head.addWidget(t_lbl); head.addSpacing(15); head.addWidget(mk_ico()); head.addStretch()
            self.inner.addLayout(head)
            txt_edit = QTextEdit(); txt_edit.setReadOnly(True); txt_edit.setPlainText(data.get("text", ""))
            txt_edit.setStyleSheet(f"background: {'#050505' if self.is_dark else '#f9f9f9'}; color: {txt}; font-family: 'Consolas'; font-size: 13px; padding: 15px; border: 1px solid #444;")
            self.inner.addWidget(txt_edit)
            btns = QHBoxLayout()
            btn_style = f"QPushButton {{ background-color: {btn_bg}; color: {btn_txt}; border: 2px solid {brd}; border-radius: 10px; padding: 12px; font-weight: bold; min-width: 150px; font-size: 14px; }} QPushButton:hover {{ background-color: {brd}; color: white; }}"
            c_btn = QPushButton(data.get("copy", "COPY")); c_btn.setStyleSheet(btn_style)
            c_btn.clicked.connect(lambda: self.copy_to_clipboard(data.get("text", ""), c_btn))
            cl_btn = QPushButton(data.get("close", "CLOSE")); cl_btn.setStyleSheet(btn_style)
            cl_btn.clicked.connect(self.safe_exit)
            btns.addStretch(); btns.addWidget(c_btn); btns.addSpacing(30); btns.addWidget(cl_btn); btns.addStretch()
            self.inner.addLayout(btns)
        def paintEvent(self, e):
            if not hasattr(self, "tick_timer") or not self.tick_timer.isActive(): return
            p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
            rect = self.container.geometry(); g = QConicalGradient(rect.center(), -self._angle)
            stops = [(0.0, QColor(255, 0, 0)), (0.17, QColor(255, 255, 0)), (0.33, QColor(0, 255, 0)), (0.5, QColor(0, 255, 255)), (0.67, QColor(0, 0, 255)), (0.83, QColor(255, 0, 255)), (1.0, QColor(255, 0, 0))]
            for s, c in stops: g.setColorAt(s, c)
            p.setPen(QPen(g, 10)); p.drawRoundedRect(rect.adjusted(2, 2, -2, -2), 40, 40)
    app = QApplication(sys.argv)
    idx = sys.argv.index("--spawn-loader")
    win = OverlayController(float(sys.argv[idx+1]), json.loads(sys.argv[idx+2]))
    win.show(); sys.exit(app.exec())
def run_with_loading(callback, func, *args, **kwargs):
    global _worker_ref, _result_data
    if _result_data.get("status") == "running": return
    _result_data.update({"status": "running", "data": None})
    start_ts = time.time()
    try: phrases = [t(f"loading.phrase.{i}") for i in range(1, 21)]
    except: phrases = ["LOADING..."]
    loader_proc = _spawn_process(["--spawn-loader", str(start_ts), json.dumps(phrases)])
    def cleanup_loader():
        if loader_proc and loader_proc.poll() is None:
            try:
                loader_proc.stdin.write(b'{"cmd":"exit"}\n'); loader_proc.stdin.flush()
                loader_proc.wait(timeout=1)
            except:
                try: loader_proc.kill()
                except: pass
    def task():
        try: _result_data["data"] = func(*args, **kwargs)
        except: _result_data["data"] = traceback.format_exc()
        _result_data["status"] = "finished"
    _worker_ref = threading.Thread(target=task, daemon=True); _worker_ref.start()
    def monitor():
        if _result_data["status"] != "finished":
            QTimer.singleShot(100, monitor); return
        res = _result_data["data"]; _result_data["status"] = "idle"
        if isinstance(res, str) and "Traceback" in res:
            try: trans = {"title": t("error.overlay.title"), "close": t("error.overlay.close"), "copy": t("error.overlay.copy")}
            except: trans = {"title": "AN ERROR OCCURRED", "close": "CLOSE", "copy": "COPY"}
            if loader_proc and loader_proc.poll() is None:
                try:
                    loader_proc.stdin.write((json.dumps({"cmd":"error", "text":res, **trans}) + "\n").encode())
                    loader_proc.stdin.flush()
                except: cleanup_loader()
            else:
                QMessageBox.critical(None, trans["title"], res)
        else:
            cleanup_loader()
            if callback: callback(res)
    QTimer.singleShot(100, monitor)