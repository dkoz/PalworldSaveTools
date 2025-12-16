import os,sys,subprocess,tempfile,time,urllib.request,re,json
import importlib,importlib.util,traceback,nerdfont as nf
from pathlib import Path;from typing import List
try:
    import PySide6.QtWidgets as _qtwidgets
    if not hasattr(_qtwidgets, "QAction"):
        try:
            import PySide6.QtGui as _qtgui
            if hasattr(_qtgui, "QAction"):
                setattr(_qtwidgets, "QAction", _qtgui.QAction)
        except Exception:
            pass
except Exception:
    pass
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QFrame, QScrollArea, QMessageBox, QToolButton, QStyle, QStatusBar,
    QSpacerItem, QSizePolicy
)
from PySide6.QtGui import QPixmap, QIcon, QFont, QFontDatabase, QCursor
from PySide6.QtCore import Qt, QTimer, QSize
try:
    from PIL import Image
except Exception:
    Image = None
try:
    import tkinter as tk
    from tkinter import ttk, messagebox
except Exception:
    tk = None
    ttk = None
    messagebox = None
try:
    import customtkinter as ctk
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")
except Exception:
    ctk = None
def unlock_self_folder():
    print(f"Attempting to unlock the folder...")
    folder=os.path.dirname(os.path.abspath(sys.argv[0]))
    script=(
        f"$target=\"{folder}\"\n"
        "$p=Get-Process\n"
        "foreach($x in $p){try{if($x.Id -ne $PID -and $x.Path -and $x.Path.StartsWith($target)){Stop-Process -Id $x.Id -Force -ErrorAction SilentlyContinue}}catch{}}\n"
        "foreach($x in $p){try{$m=$x.Modules|Where-Object{$_.FileName -and $_.FileName.StartsWith($target)};if($m.Count -gt 0 -and $x.Id -ne $PID){Stop-Process -Id $x.Id -Force -ErrorAction SilentlyContinue}}catch{}}\n"
        "exit\n"
    )
    tmp=tempfile.NamedTemporaryFile(delete=False,suffix=".ps1")
    tmp.write(script.encode())
    tmp.close()
    si=subprocess.STARTUPINFO()
    si.dwFlags=subprocess.STARTF_USESHOWWINDOW
    subprocess.Popen(["powershell","-WindowStyle","Hidden","-ExecutionPolicy","Bypass","-File",tmp.name],startupinfo=si,creationflags=subprocess.CREATE_NO_WINDOW)
    print("Operation completed.")
def is_frozen() -> bool:
    return getattr(sys, 'frozen', False)
def get_assets_path() -> str:
    env = os.environ.get("ASSETS_PATH")
    if env:
        return os.path.abspath(env)
    if is_frozen():
        exe_dir = os.path.dirname(sys.executable)
        assets = os.path.join(exe_dir, "Assets")
        if os.path.isdir(assets):
            return assets
    try:
        base = os.path.dirname(__file__)
    except NameError:
        base = os.path.dirname(os.path.abspath(sys.argv[0]))
    assets = os.path.join(base, "Assets")
    if os.path.isdir(assets):
        return assets
    return os.path.abspath(os.path.join(base, "Assets"))
def setup_import_paths():
    assets = get_assets_path()
    if assets not in sys.path:
        sys.path.insert(0, assets)
    for sub in ['palworld_coord', 'palworld_save_tools', 'palworld_xgp_import', 'resources']:
        p = os.path.join(assets, sub)
        if os.path.isdir(p) and p not in sys.path:
            sys.path.insert(0, p)
setup_import_paths()
def clear_console():
    try:
        os.system('cls' if os.name == 'nt' else 'clear')
    except Exception:
        pass
def set_console_title(title: str):
    if sys.platform == "win32":
        os.system(f"title {title}")
    else:
        print(f'\033]0;{title}\a', end='', flush=True)
try:
    from i18n import init_language, t, set_language, get_language, load_resources, get_config_value
except Exception:
    def t(key, **fmt):
        return key.format(**fmt) if fmt else key
    def init_language(default_lang: str = "zh_CN"):
        pass
    def set_language(lang: str):
        pass
    def get_language():
        return "zh_CN"
    def load_resources(lang: str | None = None):
        pass
class LazyImporter:
    def __init__(self, debug: bool = False):
        self._modules = {}
        self._common_funcs = None
        self.debug = debug
        self._assets_path = get_assets_path()
    def _log(self, *args):
        if self.debug:
            print("[LazyImporter]", *args)
    def _module_variants(self, module_name: str):
        yield module_name
        yield f"Assets.{module_name}"
        if "-" in module_name:
            yield module_name.replace("-", "_")
            yield f"Assets.{module_name.replace('-', '_')}"
        yield f"{module_name}.__init__"
        yield f"Assets.{module_name}.__init__"
    def _file_candidates_in_assets(self, module_name: str) -> List[str]:
        candidates = []
        assets = self._assets_path
        if not os.path.isdir(assets):
            return candidates
        top = os.path.join(assets, f"{module_name}.py")
        if os.path.isfile(top):
            candidates.append(top)
        for root, dirs, files in os.walk(assets):
            if f"{module_name}.py" in files:
                candidates.append(os.path.join(root, f"{module_name}.py"))
            pkg_dir = os.path.join(root, module_name)
            if os.path.isdir(pkg_dir) and os.path.isfile(os.path.join(pkg_dir, "__init__.py")):
                candidates.append(os.path.join(pkg_dir, "__init__.py"))
        return candidates
    def _try_import(self, module_name: str):
        tried = []
        for variant in self._module_variants(module_name):
            try:
                if variant in sys.modules:
                    importlib.reload(sys.modules[variant])
                    self._modules[module_name] = sys.modules[variant]
                    self._log("reloaded variant", variant)
                    return self._modules[module_name]
                module = importlib.import_module(variant)
                self._modules[module_name] = module
                self._log("imported variant", variant)
                return module
            except Exception as e:
                tried.append(f"import {variant}: {e.__class__.__name__}: {e}")
        file_candidates = self._file_candidates_in_assets(module_name)
        for fp in file_candidates:
            tried.append(f"file {fp}")
            try:
                spec = importlib.util.spec_from_file_location(module_name, fp)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    self._modules[module_name] = module
                    self._log("loaded from file", fp)
                    return module
            except Exception as e:
                tried.append(f"spec load {fp}: {e.__class__.__name__}: {e}")
        diag = "\n".join(tried)
        raise ImportError(t("error.module") + f" {module_name}\nTried:\n{diag}")
    def get_module(self, module_name: str):
        return self._try_import(module_name)
    def get_function(self, module_name: str, function_name: str):
        module = self.get_module(module_name)
        if not hasattr(module, function_name):
            available = ", ".join([n for n in dir(module) if not n.startswith("_")])
            raise AttributeError(f"Module '{module_name}' loaded but missing '{function_name}'. Available: {available}")
        return getattr(module, function_name)
    def get_common_functions(self):
        if self._common_funcs is not None:
            return self._common_funcs
        try:
            common_module = self._try_import('common')
            self._common_funcs = {
                'ICON_PATH': getattr(common_module, 'ICON_PATH', os.path.join(get_assets_path(), 'resources', 'pal.ico')),
                'get_versions': getattr(common_module, 'get_versions', lambda: ("Unknown", "Unknown")),
                'open_file_with_default_app': getattr(common_module, 'open_file_with_default_app', lambda x: None)
            }
        except Exception:
            self._common_funcs = {
                'ICON_PATH': os.path.join(get_assets_path(), 'resources', 'pal.ico'),
                'get_versions': lambda: ("Unknown", "Unknown"),
                'open_file_with_default_app': lambda x: None
            }
        return self._common_funcs
lazy_importer = LazyImporter(debug=bool(os.environ.get("PST_DEBUG", False)))
common_funcs = lazy_importer.get_common_functions()
ICON_PATH = common_funcs['ICON_PATH']
get_versions = common_funcs['get_versions']
open_file_with_default_app = common_funcs['open_file_with_default_app']
def list_assets_modules() -> List[str]:
    assets = get_assets_path()
    results = []
    if not os.path.isdir(assets):
        return results
    for root, dirs, files in os.walk(assets):
        for f in files:
            if f.endswith('.py'):
                rel = os.path.relpath(os.path.join(root, f), assets)
                results.append(rel.replace('\\', '/'))
        for d in dirs:
            if os.path.isfile(os.path.join(root, d, '__init__.py')):
                rel = os.path.relpath(os.path.join(root, d), assets)
                results.append(rel.replace('\\', '/') + '/')
    return sorted(results)
GITHUB_RAW_URL = "https://raw.githubusercontent.com/deafdudecomputers/PalworldSaveTools/main/Assets/common.py"
GITHUB_LATEST_ZIP = "https://github.com/deafdudecomputers/PalworldSaveTools/releases/latest"
UPDATE_CACHE = None
def check_github_update(auto_download=False, download_folder="PST_update", force_test=False):
    try:
        r = urllib.request.urlopen(GITHUB_RAW_URL, timeout=5)
        content = r.read().decode("utf-8")
        match = re.search(r'APP_VERSION\s*=\s*"([^"]+)"', content)
        latest = match.group(1) if match else None
        local, _ = get_versions()
        if force_test:
            local = "0.0.1"
        if latest:
            try:
                local_tuple = tuple(int(x) for x in local.split("."))
                latest_tuple = tuple(int(x) for x in latest.split("."))
            except Exception:
                local_tuple = (0,)
                latest_tuple = (0,)
            if local_tuple >= latest_tuple:
                return True, latest
            return False, latest
        return True, None
    except Exception:
        return True, None
def get_cached_update_info():
    global UPDATE_CACHE
    if UPDATE_CACHE is None:
        UPDATE_CACHE = check_github_update(force_test=False)
    return UPDATE_CACHE
def run_tool(choice):
    def import_and_call(module_name, function_name, *args):
        try:
            func = lazy_importer.get_function(module_name, function_name)
            return func(*args) if args else func()
        except Exception as e:
            print(f"Error importing/calling {module_name}.{function_name}: {e}")
            traceback.print_exc()
            raise
    tool_lists = [
        [
            lambda: import_and_call("convert_level_location_finder", "convert_level_location_finder", "json"),
            lambda: import_and_call("convert_level_location_finder", "convert_level_location_finder", "sav"),
            lambda: import_and_call("convert_players_location_finder", "convert_players_location_finder", "json"),
            lambda: import_and_call("convert_players_location_finder", "convert_players_location_finder", "sav"),
            lambda: import_and_call("game_pass_save_fix", "game_pass_save_fix"),
            lambda: import_and_call("convertids", "convert_steam_id"),
        ],
        [
            lambda: import_and_call("all_in_one_tools", "all_in_one_tools"),
            lambda: import_and_call("slot_injector", "slot_injector"),
            lambda: import_and_call("modify_save", "modify_save"),
            lambda: import_and_call("character_transfer", "character_transfer"),
            lambda: import_and_call("fix_host_save", "fix_host_save"),
            lambda: import_and_call("restore_map", "restore_map"),
        ]
    ]
    try:
        category_index, tool_index = choice
        return tool_lists[category_index][tool_index]()
    except Exception as e:
        print("Invalid choice or error running tool:", e)
        traceback.print_exc()
converting_tool_keys = [
    "tool.convert.level.to_json",
    "tool.convert.level.to_sav",
    "tool.convert.players.to_json",
    "tool.convert.players.to_sav",
    "tool.convert.gamepass.steam",
    "tool.convert.steamid",
]
management_tool_keys = [
    "tool.deletion",
    "tool.slot_injector",
    "tool.modify_save",
    "tool.character_transfer",
    "tool.fix_host_save",
    "tool.restore_map",
]
def load_tool_icons():
    icon_file = os.path.join(get_assets_path(), "toolicon.json")
    if not os.path.exists(icon_file):
        return {}
    try:
        with open(icon_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}
DARK_STYLE = r"""
/* Background gradient */
QWidget#central {
    background: qlineargradient(spread:pad, x1:0.0, y1:0.0, x2:1.0, y2:1.0,
                stop:0 #07080a, stop:0.5 #08101a, stop:1 #05060a);
    color: #dfeefc;
    font-family: "Segoe UI", Roboto, Arial;
}

/* Card */
QFrame#glass {
    background: rgba(18,20,24,0.65);
    border-radius: 10px;
    border: 1px solid rgba(255,255,255,0.04);
    padding: 10px;
}

/* Title area */
QLabel#title {
    font-size: 20px;
    font-weight: 800;
    color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #7DD3FC, stop:1 #A78BFA);
    letter-spacing: 1px;
}

/* Small version chip */
QLabel#versionChip {
    background: rgba(125,211,252,0.08);
    border: 1px solid rgba(125,211,252,0.12);
    padding: 6px 10px;
    border-radius: 10px;
    font-size: 17px;
    color: #7DD3FC;
}

/* PULSE STYLE: Applied when the pulse="true" dynamic property is set */
QLabel#versionChip[pulse="true"] {
    background: #FFD24D; /* Bright Gold/Amber for pulsing */
    border: 1px solid #FFD24D;
    color: #000000; /* Contrast text color */
}

/* Game version chip */
QLabel#gameVersionChip {
    background: rgba(34,197,94,0.08);
    border: 1px solid rgba(34,197,94,0.12);
    padding: 6px 10px;
    border-radius: 10px;
    font-size: 17px;
    color: #22C55E;
}

/* Tool widget (composite row) */
QWidget.toolRow {
    background: transparent;
    border: 2px solid rgba(255,255,255,0.04);
    border-radius: 8px;
    padding: 4px;
    margin: 4px 0px;
}
QWidget.toolRow:hover {
    border: 2px solid rgba(125,211,252,0.65);
    background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0,
                stop:0 rgba(10,20,28,0.45), stop:1 rgba(20,12,30,0.28));
}

/* Tool button tightened */
QPushButton.toolCard {
    background: transparent;
    border: none;
    text-align: left;
    padding: 4px 6px;
    font-weight: 600;
    min-height: 40px;
    color: #E6EDF3;
}
QPushButton.toolCard:hover {
    color: #AEE9FF;
}

/* Icon label */
QLabel.toolIcon {
    background: rgba(255,255,255,0.02);
    border-radius: 6px;
    padding: 4px;
    min-width: 30px;
    min-height: 30px;
    max-width: 30px;
    max-height: 30px;
}

/* Category title */
QLabel.categoryTitle {
    font-size: 15px;
    font-weight: 700;
    color: rgba(255,255,255,0.9);
}

/* Header buttons */
QToolButton#hdrBtn {
    border: none;
    background: transparent;
    padding: 6px;
    margin-left: 6px;
}
QToolButton#hdrBtn:hover {
    background: rgba(255,255,255,0.02);
    border-radius: 6px;
}

/* Footer */
QStatusBar {
    background: transparent;
    color: rgba(255,255,255,0.6);
    border-top: 1px solid rgba(255,255,255,0.02);
}
"""
class MenuGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.running = True
        tv, _ = get_versions()
        self.setWindowTitle(t("app.title", version=tv))
        self._default_width = 950
        self.setStyleSheet(DARK_STYLE)
        font_path = os.path.join(get_assets_path(), "resources", "HackNerdFont-Regular.ttf")
        if os.path.exists(font_path):
            families = QFontDatabase.families()
            if "Hack Nerd Font" not in families:
                font_id = QFontDatabase.addApplicationFont(font_path)
                if font_id == -1:
                    print("Warning: Failed to load HackNerdFont-Regular.ttf")
        try:
            if ICON_PATH and os.path.exists(ICON_PATH):
                self.setWindowIcon(QIcon(ICON_PATH))
        except Exception:
            pass
        self.version_labels = []
        self.category_frames = []
        self.tool_widgets = []
        self.lang_combo = None
        self.debug_mode = bool(os.environ.get("PST_DEBUG", False))
        self.tool_icons = load_tool_icons()
        self.setup_ui()
        self._fit_window_to_listing()
    def center_window(self):
        screen = QApplication.primaryScreen().availableGeometry()
        size = self.size()
        self.move((screen.width() - size.width()) // 2, (screen.height() - size.height()) // 2)
    def setup_ui(self):
        tools_version, game_version = get_versions()
        central = QWidget()
        central.setObjectName("central")
        self.setCentralWidget(central)
        main_v = QVBoxLayout(central)
        main_v.setContentsMargins(14, 14, 14, 14)
        main_v.setSpacing(12)
        top_h = QHBoxLayout()
        top_h.setSpacing(8)
        logo_container = QHBoxLayout()
        title_label = QLabel()
        title_label.setObjectName("title")
        logo_path = os.path.join(get_assets_path(), "resources", "PalworldSaveTools_Blue.png")
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaledToHeight(44, Qt.SmoothTransformation)
                title_label.setPixmap(scaled_pixmap)
                title_label.setFixedSize(scaled_pixmap.size())
        else:
            title_label.setText("PALWORLD SAVE TOOLS")
            title_label.setFont(QFont("", 16, QFont.Bold))
        logo_container.addWidget(title_label)
        logo_container.addSpacing(8)
        self.app_version_label = QLabel(f"{nf.icons['nf-cod-github']} {tools_version}")
        self.app_version_label.setObjectName("versionChip")
        self.app_version_label.setCursor(QCursor(Qt.PointingHandCursor))
        self.app_version_label.setFont(QFont("Consolas", 11))
        self.app_version_label.mousePressEvent = self._open_github
        self.game_version_label = QLabel(f"{nf.icons['nf-fa-save']} {game_version}")
        self.game_version_label.setObjectName("gameVersionChip")
        self.game_version_label.setFont(QFont("Consolas", 11))
        logo_container.addWidget(self.app_version_label, alignment=Qt.AlignVCenter)
        logo_container.addWidget(self.game_version_label, alignment=Qt.AlignVCenter)
        top_h.addLayout(logo_container)
        top_h.addItem(QSpacerItem(20, 10, QSizePolicy.Expanding, QSizePolicy.Minimum))
        self.warn_btn = QToolButton()
        self.warn_btn.setObjectName("hdrBtn")
        self.warn_btn.setToolTip(t("PalworldSaveTools") if callable(t) else "Warnings")
        self.warn_btn.setIcon(self.style().standardIcon(QStyle.SP_MessageBoxWarning))
        self.warn_btn.setStyleSheet("color: #FFD24D;")
        self.warn_btn.clicked.connect(self._show_warnings)
        self.warn_btn.setIconSize(QSize(26, 26))
        top_h.addWidget(self.warn_btn)
        self.lang_combo = QComboBox()
        values = [t(f'lang.{code}') for code in ["zh_CN","en_US","ru_RU","fr_FR","es_ES","de_DE","ja_JP","ko_KR"]]
        self.lang_combo.addItems(values)
        self.lang_combo.setFixedWidth(93)
        self.lang_combo.currentTextChanged.connect(self.on_language_change_cmd)
        top_h.addWidget(self.lang_combo)
        main_v.addLayout(top_h)
        content_h = QHBoxLayout()
        content_h.setSpacing(12)
        left_frame = QFrame()
        left_frame.setObjectName("glass")
        left_v = QVBoxLayout(left_frame)
        left_v.setContentsMargins(12, 12, 12, 12)
        left_v.setSpacing(6)
        left_title = QLabel(t("cat.converting"))
        left_title.setProperty("class", "categoryTitle")
        left_v.addWidget(left_title)
        self.category_frames.append((left_title, "cat.converting"))
        self.left_tools_container = QWidget()
        self.left_tools_layout = QVBoxLayout(self.left_tools_container)
        self.left_tools_layout.setSpacing(6)
        self.left_tools_layout.setContentsMargins(0, 0, 0, 0)
        left_v.addWidget(self.left_tools_container)
        left_v.addStretch(1)
        right_frame = QFrame()
        right_frame.setObjectName("glass")
        right_v = QVBoxLayout(right_frame)
        right_v.setContentsMargins(12, 12, 12, 12)
        right_v.setSpacing(6)
        right_title = QLabel(t("cat.management"))
        right_title.setProperty("class", "categoryTitle")
        right_v.addWidget(right_title)
        self.category_frames.append((right_title, "cat.management"))
        self.right_tools_container = QWidget()
        self.right_tools_layout = QVBoxLayout(self.right_tools_container)
        self.right_tools_layout.setSpacing(6)
        self.right_tools_layout.setContentsMargins(0, 0, 0, 0)
        right_v.addWidget(self.right_tools_container)
        right_v.addStretch(1)
        content_h.addWidget(left_frame, 1)
        content_h.addWidget(right_frame, 1)
        scroll = QScrollArea()
        content_widget = QWidget()
        content_widget.setLayout(content_h)
        scroll.setWidgetResizable(True)
        scroll.setWidget(content_widget)
        main_v.addWidget(scroll, 1)
        status = QStatusBar()
        status.showMessage("Ready")
        self.status = status
        main_v.addWidget(status)
        self._populate_tool_buttons()
        self.refresh_texts()
    def _make_tool_row(self, label_text: str, tooltip_text: str, icon_path: str = None, icon_qicon: QIcon = None, icon_size: QSize = QSize(24,24)):
        show_icons = get_config_value("showiconinlist", True)
        container = QWidget()
        container.setProperty("class", "toolRow")
        layout = QHBoxLayout(container)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(10)
        icon_label = QLabel()
        icon_label.setObjectName("toolIcon")
        icon_label.setProperty("class", "toolIcon")
        if show_icons:
            icon_label.setFixedSize(icon_size)
            pix = None
            if icon_path and os.path.exists(icon_path):
                pix = QPixmap(icon_path).scaled(icon_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            elif icon_qicon:
                pix = icon_qicon.pixmap(icon_size)
            elif ICON_PATH and os.path.exists(ICON_PATH):
                pix = QPixmap(ICON_PATH).scaled(icon_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            else:
                try:
                    std_icon = self.style().standardIcon(QStyle.SP_FileIcon)
                    pix = std_icon.pixmap(icon_size)
                except Exception:
                    pix = None
            if pix and not pix.isNull():
                icon_label.setPixmap(pix)
            else:
                icon_label.setText("")
        else:
            icon_label.hide()
        text_btn = QPushButton(label_text)
        text_btn.setObjectName("toolCard")
        text_btn.setProperty("class", "toolCard")
        text_btn.setToolTip(tooltip_text)
        text_btn.setCursor(QCursor(Qt.PointingHandCursor))
        text_btn.setFlat(True)
        text_btn.setMinimumHeight(26)
        layout.addWidget(icon_label, 0, Qt.AlignVCenter)
        layout.addWidget(text_btn, 1, Qt.AlignVCenter)
        return container, text_btn, icon_label
    def _get_tool_icon(self, tool_key: str) -> QIcon:
        if tool_key in self.tool_icons:
            icon_name = self.tool_icons[tool_key]
            icon_path = os.path.join(get_assets_path(), "resources", "i18n", "icon", f"{icon_name}.ico")
            if os.path.exists(icon_path):
                return QIcon(icon_path)
        if ICON_PATH and os.path.exists(ICON_PATH):
            return QIcon(ICON_PATH)
        return None
    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
    def _populate_tool_buttons(self):
        self._clear_layout(self.left_tools_layout)
        self._clear_layout(self.right_tools_layout)
        self.tool_widgets.clear()
        for idx, key in enumerate(converting_tool_keys):
            label = t(key)
            tooltip = t(key)
            icon_q = self._get_tool_icon(key)
            row_widget, btn, icon_lbl = self._make_tool_row(label, tooltip, icon_qicon=icon_q)
            choice = (0, idx)
            btn.clicked.connect(lambda checked, choice=choice: self._on_tool_clicked(choice))
            icon_lbl.mousePressEvent = (lambda ev, choice=choice: self._on_tool_clicked(choice))
            self.left_tools_layout.addWidget(row_widget)
            self.tool_widgets.append((row_widget, btn, key, 0, idx))
        for idx, key in enumerate(management_tool_keys):
            label = t(key)
            tooltip = t(key)
            icon_q = self._get_tool_icon(key)
            row_widget, btn, icon_lbl = self._make_tool_row(label, tooltip, icon_qicon=icon_q)
            choice = (1, idx)
            btn.clicked.connect(lambda checked, choice=choice: self._on_tool_clicked(choice))
            icon_lbl.mousePressEvent = (lambda ev, choice=choice: self._on_tool_clicked(choice))
            self.right_tools_layout.addWidget(row_widget)
            self.tool_widgets.append((row_widget, btn, key, 1, idx))
        self.left_tools_layout.addStretch(1)
        self.right_tools_layout.addStretch(1)
    def _on_tool_clicked(self, choice):
        name = self.get_tool_name(choice)
        self.status.showMessage(f"Opening {name}...")
        self._run_tool(choice, name)
    def _run_tool(self, choice, name):
        self.hide()
        try:
            tool_window = run_tool(choice)
            if tool_window:
                if hasattr(tool_window, 'exec'):
                    tool_window.exec()
                elif hasattr(tool_window, 'show'):
                    tool_window.setAttribute(Qt.WA_DeleteOnClose, True)
                    tool_window.show()
                    from PySide6.QtCore import QEventLoop
                    loop = QEventLoop()
                    tool_window.destroyed.connect(loop.quit)
                    loop.exec()
                elif hasattr(tool_window, 'mainloop'):
                    root = getattr(tool_window, 'master', None)
                    if root and hasattr(root, 'withdraw'):
                        root.withdraw()
                        root.lower()
                        root.tk.eval('proc bgerror {args} {}')
                        def tk_exit_handler():
                            root.quit()
                            root.destroy()
                        tool_window.protocol("WM_DELETE_WINDOW", tk_exit_handler)
                    tool_window.mainloop()
                else:
                    # Check if it's a tkinter toplevel window
                    if hasattr(tool_window, 'winfo_exists'):
                        loop = QEventLoop()
                        def check_closed():
                            if not tool_window.winfo_exists():
                                loop.quit()
                        timer = QTimer()
                        timer.timeout.connect(check_closed)
                        timer.start(100)
                        loop.exec()
                        timer.stop()
            self.refresh_texts()
            self.status.showMessage(t('status.close', name=name))
            self.show()
        except Exception as e:
            QMessageBox.critical(self, t("error.title"), t("error.runtime", error=str(e)))
            traceback.print_exc()
            self.refresh_texts()
            self.status.showMessage("Error occurred")
            self.show()
    def get_tool_name(self, choice):
        try:
            category_index, tool_index = choice
            if category_index == 0:
                key = converting_tool_keys[tool_index]
            elif category_index == 1:
                key = management_tool_keys[tool_index]
            else:
                key = str(choice)
            return t(key)
        except Exception:
            return str(choice)
    def refresh_texts(self):
        tools_version, game_version = get_versions()
        self.setWindowTitle(t("app.title", version=tools_version))
        for label, key in self.category_frames:
            label.setText(t(key))
        for container, btn, key, cat, idx in self.tool_widgets:
            btn.setText(t(key))
            btn.setToolTip(t(key))
        try:
            self.lang_combo.currentTextChanged.disconnect(self.on_language_change_cmd)
        except Exception:
            pass
        current_lang = get_language()
        values = [t(f'lang.{code}') for code in ["zh_CN","en_US","ru_RU","fr_FR","es_ES","de_DE","ja_JP","ko_KR"]]
        self.lang_combo.clear()
        self.lang_combo.addItems(values)
        try:
            self.lang_combo.setCurrentText(t(f'lang.{current_lang}'))
        except Exception:
            pass
        self.lang_combo.currentTextChanged.connect(self.on_language_change_cmd)
    def on_language_change_cmd(self, choice):
        sel = choice
        lang_map = {t(f'lang.{code}'): code for code in ["zh_CN","en_US","ru_RU","fr_FR","es_ES","de_DE","ja_JP","ko_KR"]}
        lang = lang_map.get(sel, "zh_CN")
        set_language(lang)
        load_resources(lang)
        self.refresh_texts()
    def _show_warnings(self):
        warnings = [
            (t("notice.backup"), {}),
            (t("notice.patch", game_version=get_versions()[1]), {}),
            (t("notice.errors"), {})
        ]
        combined = "\n\n".join(w for w, _ in warnings if w)
        if not combined:
            combined = t("notice.none") if callable(t) else "No warnings."
        QMessageBox.warning(self, t("PalworldSaveTools") if callable(t) else "Warnings", combined)
    def _automatic_check_updates(self):
        try:
            ok, latest = check_github_update(force_test=False)
            if not ok:
                self.app_version_label.setProperty("pulse", True)
                self.app_version_label.style().polish(self.app_version_label)
                tools_version, _ = get_versions()
                self.app_version_label.setText(f"{nf.icons['nf-cod-github']} {tools_version}")
            global UPDATE_CACHE
            UPDATE_CACHE = (ok, latest)
            self.refresh_texts()
        except Exception:
            pass
    def _open_github(self, event):
        url = GITHUB_LATEST_ZIP
        import webbrowser
        webbrowser.open(url)
        self.status.showMessage(f"Opening GitHub release page: {url}")
    def _fit_window_to_listing(self):
        per_row = 55
        header_h = 80
        footer_h = 40
        margins = 90
        left_count = len(converting_tool_keys)
        right_count = len(management_tool_keys)
        max_rows = max(left_count, right_count)
        desired_height = header_h + (max_rows * per_row) + footer_h + margins + 50
        desired_width = self._default_width
        screen = QApplication.primaryScreen().availableGeometry()
        max_h = screen.height() - 100
        max_w = screen.width() - 100
        final_h = min(desired_height, max_h)
        final_w = min(desired_width, max_w)
        self.resize(final_w, int(final_h))
        self.center_window()
    def closeEvent(self, event):
        QApplication.quit()
        event.accept()
def on_exit():
    unlock_self_folder()
    os._exit(0)
    pass
if __name__ == "__main__":
    if "--list-assets" in sys.argv:
        print("Assets path:", get_assets_path())
        for p in list_assets_modules():
            print(" -", p)
        sys.exit(0)
    try:
        init_language("zh_CN")
    except Exception:
        pass
    tv, gv = get_versions()
    set_console_title(f"PalworldSaveTools v{tv}")
    clear_console()
    os.environ['QT_LOGGING_RULES'] = 'qt.qpa.fonts=false'
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    gui = MenuGUI()
    gui.show()
    gui._automatic_check_updates()
    try:
        sys.exit(app.exec())
    except KeyboardInterrupt:
        app.quit()
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}")
        traceback.print_exc()
        app.quit()
        sys.exit(1)
