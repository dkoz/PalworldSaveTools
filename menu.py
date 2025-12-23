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
    QSpacerItem, QSizePolicy, QGraphicsOpacityEffect, QGraphicsDropShadowEffect, QDialog, QCheckBox, QMenu
)
from PySide6.QtGui import QPixmap, QIcon, QFont, QFontDatabase, QCursor, QColor, QPalette
from PySide6.QtCore import Qt, QTimer, QSize, QPropertyAnimation, QEasingCurve, QPoint
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
    if getattr(sys, 'frozen', False):
        folder = os.path.dirname(os.path.abspath(sys.executable))
    else:
        folder = os.path.dirname(os.path.abspath(sys.argv[0]))
    folder_escaped = folder.replace("\\", "\\\\")
    parent_pid = os.getpid()
    ps_command = (
        "Set-Location C:\\; "
        f"$target = '{folder_escaped}'; "
        f"$pPid = {parent_pid}; "
        "function Global-Nuke { "
        "  $procs = Get-WmiObject Win32_Process | Where-Object { ($_.ExecutablePath -like \"$target*\") -and ($_.ProcessId -ne $PID) }; "
        "  foreach($p in $procs){ "
        "    try { "
        "      taskkill /F /T /ID $p.ProcessId /NoWindow; "
        "      $process = Get-Process -Id $p.ProcessId -ErrorAction SilentlyContinue; "
        "      if($process){ $process.Kill() } "
        "    } catch {} "
        "  } "
        "}; "
        "while($true){ "
        "  Start-Sleep -Seconds 1; "
        "  $parentAlive = Get-Process -Id $pPid -ErrorAction SilentlyContinue; "
        "  if(!$parentAlive){ "
        "    Global-Nuke; "
        "    break; "
        "  } "
        "  $active = Get-WmiObject Win32_Process | Where-Object { ($_.ExecutablePath -like \"$target*\") -and ($_.ProcessId -ne $PID) -and ($_.ProcessId -ne $pPid) }; "
        "  if(!$active){ "
        "    break; "
        "  } "
        "}; "
        "Stop-Process -Id $PID -Force"
    )
    si = subprocess.STARTUPINFO()
    si.dwFlags = subprocess.STARTF_USESHOWWINDOW
    subprocess.Popen(
        ["powershell", "-WindowStyle", "Hidden", "-ExecutionPolicy", "Bypass", "-Command", ps_command],
        startupinfo=si,
        creationflags=subprocess.CREATE_NO_WINDOW,
        cwd="C:\\"
    )
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

class MenuGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.running = True
        tv, _ = get_versions()
        self.setWindowTitle(t("app.title", version=tv))
        self._default_width = 1050
        self.is_dark_mode = True
        self._drag_pos = None
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
        self.lang_map = {
            "English": "en_US",
            "Chinese": "zh_CN",
            "Russian": "ru_RU",
            "French": "fr_FR",
            "Spanish": "es_ES",
            "German": "de_DE",
            "Japanese": "ja_JP",
            "Korean": "ko_KR"
        }
        self.load_user_settings()
        self.setup_ui()
        self.update_logo()
        self._fit_window_to_listing()
        self.effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.effect)
        self.effect.setOpacity(0)
        self.animation = QPropertyAnimation(self.effect, b"opacity")
        self.animation.setDuration(1000)
        self.animation.setStartValue(0)
        self.animation.setEndValue(1)
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)
    def load_user_settings(self):
        user_cfg_path = os.path.join(get_assets_path(), "data", "configs", "user.cfg")
        default_settings = {"theme": "dark", "show_icons": True, "language": "en_US"}
        if os.path.exists(user_cfg_path):
            try:
                with open(user_cfg_path, "r") as f:
                    self.user_settings = json.load(f)
            except:
                self.user_settings = default_settings.copy()
                with open(user_cfg_path, "w") as f:
                    json.dump(self.user_settings, f)
        else:
            self.user_settings = default_settings.copy()
            with open(user_cfg_path, "w") as f:
                json.dump(self.user_settings, f)
        self.is_dark_mode = self.user_settings.get("theme", "dark") == "dark"
        set_language(self.user_settings["language"])
        load_resources(self.user_settings["language"])
        self.load_styles()
    def start_fade_in(self):
        self.animation.start()
    def center_window(self):
        screen = QApplication.primaryScreen().availableGeometry()
        size = self.size()
        self.move((screen.width() - size.width()) // 2, (screen.height() - size.height()) // 2)
    def setup_ui(self):
        tools_version, game_version = get_versions()
        central = QWidget()
        central.setObjectName("central")
        glow_effect = QGraphicsDropShadowEffect()
        glow_effect.setColor(QColor(125, 211, 252, 80))
        glow_effect.setBlurRadius(15)
        glow_effect.setOffset(0, 0)
        central.setGraphicsEffect(glow_effect)
        self.setCentralWidget(central)
        main_v = QVBoxLayout(central)
        main_v.setContentsMargins(14, 14, 14, 14)
        main_v.setSpacing(12)
        top_h = QHBoxLayout()
        top_h.setSpacing(8)
        logo_container = QHBoxLayout()
        self.title_label = QLabel()
        self.title_label.setObjectName("title")
        logo_container.addWidget(self.title_label)
        self.update_logo()
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
        dropdown_btn = QPushButton(nf.icons['nf-md-menu'])
        dropdown_btn.setObjectName("controlChip")
        dropdown_btn.setFlat(True)
        dropdown_btn.setToolTip(t("Menu"))
        menu = QMenu()
        action_toggle = menu.addAction(nf.icons['nf-md-theme_light_dark'] + " " + t("Toggle Theme"))
        menu.addSeparator()
        action_settings = menu.addAction(nf.icons['nf-md-cog'] + " " + t("Settings"))
        action_toggle.triggered.connect(self.toggle_theme)
        action_settings.triggered.connect(self.show_settings)
        dropdown_btn.clicked.connect(lambda: menu.exec(dropdown_btn.mapToGlobal(QPoint(0, dropdown_btn.height()))))
        self.dropdown_btn = dropdown_btn
        self.menu = menu
        self.action_toggle = action_toggle
        self.action_settings = action_settings
        top_h.addWidget(dropdown_btn)
        minimize_btn = QPushButton(nf.icons['nf-md-circle_medium'])
        minimize_btn.setObjectName("controlChip")
        minimize_btn.setFlat(True)
        minimize_btn.clicked.connect(self.showMinimized)
        top_h.addWidget(minimize_btn)
        close_btn = QPushButton(nf.icons['nf-fa-close'])
        close_btn.setObjectName("controlChip")
        close_btn.setFlat(True)
        close_btn.clicked.connect(self.close)
        top_h.addWidget(close_btn)
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
        scroll.setObjectName("mainScrollArea")
        content_widget = QWidget()
        content_widget.setObjectName("contentWidget")
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
        show_icons = self.user_settings.get("show_icons", True)
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
            icon_path = os.path.join(get_assets_path(), "data", "icon", f"{icon_name}.ico")
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
        self.action_toggle.setText(nf.icons['nf-md-theme_light_dark'] + " " + t("Toggle Theme"))
        self.action_settings.setText(nf.icons['nf-md-cog'] + " " + t("Settings"))
        self.dropdown_btn.setToolTip(t("Menu"))
        self.warn_btn.setToolTip(t("PalworldSaveTools"))

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
                self.app_version_label.setProperty("pulse", "true")
                self.app_version_label.style().polish(self.app_version_label)
                self._start_pulse_animation()
                tools_version, _ = get_versions()
                self.app_version_label.setText(f"{nf.icons['nf-cod-github']} {tools_version}")
            global UPDATE_CACHE
            UPDATE_CACHE = (ok, latest)
            self.refresh_texts()
        except Exception:
            pass
    def _start_pulse_animation(self):
        if hasattr(self, "_pulse_timer"):
            return
        self._pulse_timer = QTimer()
        self._pulse_timer.timeout.connect(self._toggle_pulse)
        self._pulse_timer.start(500)  # toggle every 500ms

    def _toggle_pulse(self):
        current = self.app_version_label.property("pulse")
        new_val = "false" if current == "true" else "true"
        self.app_version_label.setProperty("pulse", new_val)
        self.app_version_label.style().polish(self.app_version_label)
    def _open_github(self, event):
        url = GITHUB_LATEST_ZIP
        import webbrowser
        webbrowser.open(url)
        self.status.showMessage(f"Opening GitHub release page: {url}")
    def load_styles(self):
        assets_path = os.path.join(get_assets_path(), "data", "gui")
        mode_file = "darkmode.qss" if self.is_dark_mode else "lightmode.qss"
        with open(os.path.join(assets_path, mode_file), "r") as f:
            mode_qss = f.read()
        self.setStyleSheet(mode_qss)
    def toggle_theme(self):
        self.is_dark_mode = not self.is_dark_mode
        self.user_settings["theme"] = "dark" if self.is_dark_mode else "light"
        user_cfg_path = os.path.join(get_assets_path(), "data", "configs", "user.cfg")
        with open(user_cfg_path, "w") as f:
            json.dump(self.user_settings, f)
        self.load_styles()
        self.update_logo()
    def update_theme_toggle_icon(self):
        self.theme_toggle.setToolTip("Switch to light mode" if self.is_dark_mode else "Switch to dark mode")
    def update_logo(self):
        logo_name = "PalworldSaveTools_Black.png" if not self.is_dark_mode else "PalworldSaveTools_Blue.png"
        logo_path = os.path.join(get_assets_path(), "resources", logo_name)
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaledToHeight(44, Qt.SmoothTransformation)
                self.title_label.setPixmap(scaled_pixmap)
                self.title_label.setFixedSize(scaled_pixmap.size())
        else:
            self.title_label.setText("PALWORLD SAVE TOOLS")
            self.title_label.setFont(QFont("", 16, QFont.Bold))
    def set_theme(self, mode):
        self.is_dark_mode = mode == "dark"
        self.user_settings["theme"] = mode
        user_cfg_path = os.path.join(get_assets_path(), "data", "configs", "user.cfg")
        with open(user_cfg_path, "w") as f:
            json.dump(self.user_settings, f)
        self.load_styles()
        self.update_logo()
    def show_settings(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Settings")
        layout = QVBoxLayout(dialog)
        user_cfg_path = os.path.join(get_assets_path(), "data", "configs", "user.cfg")
        settings = self.user_settings.copy()
        theme_layout = QHBoxLayout()
        theme_label = QLabel("Theme:")
        theme_combo = QComboBox()
        theme_combo.addItems(["dark", "light"])
        theme_combo.setCurrentText(settings.get("theme", "dark"))
        theme_combo.currentTextChanged.connect(lambda: self._auto_save_settings(dialog, theme_combo, show_icons_cb, lang_combo))
        theme_layout.addWidget(theme_label)
        theme_layout.addWidget(theme_combo)
        layout.addLayout(theme_layout)
        show_icons_cb = QCheckBox("Show icons in tool list")
        show_icons_cb.setChecked(settings.get("show_icons", True))
        show_icons_cb.stateChanged.connect(lambda: self._auto_save_settings(dialog, theme_combo, show_icons_cb, lang_combo))
        layout.addWidget(show_icons_cb)
        lang_layout = QHBoxLayout()
        lang_label = QLabel("Language:")
        lang_combo = QComboBox()
        lang_combo.addItems(self.lang_map.keys())
        current_lang_code = settings.get("language", "en_US")
        current_lang_name = next((name for name, code in self.lang_map.items() if code == current_lang_code), "English")
        lang_combo.setCurrentText(current_lang_name)
        lang_combo.currentTextChanged.connect(lambda: self._auto_save_settings(dialog, theme_combo, show_icons_cb, lang_combo))
        lang_layout.addWidget(lang_label)
        lang_layout.addWidget(lang_combo)
        layout.addLayout(lang_layout)
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.close)
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)
        dialog.show()
    def _preview_show_icons(self, show):
        self.user_settings["show_icons"] = show
        self._populate_tool_buttons()
    def _auto_save_settings(self, dialog, theme_combo, show_icons_cb, lang_combo):
        old_lang = self.user_settings.get("language")
        settings = {
            "theme": theme_combo.currentText(),
            "show_icons": show_icons_cb.isChecked(),
            "language": self.lang_map.get(lang_combo.currentText(), "en_US")
        }
        self.user_settings = settings
        user_cfg_path = os.path.join(get_assets_path(), "data", "configs", "user.cfg")
        with open(user_cfg_path, "w") as f:
            json.dump(settings, f)
        old_dark = self.is_dark_mode
        self.is_dark_mode = settings["theme"] == "dark"
        if self.is_dark_mode != old_dark:
            self.load_styles()
            dialog.setStyleSheet(self.styleSheet())
            self.update_logo()
        if old_lang != settings["language"]:
            set_language(settings["language"])
            load_resources(settings["language"])
            self.refresh_texts()
            self.repaint()
        self._populate_tool_buttons()
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
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
    def mouseMoveEvent(self, event):
        if self._drag_pos is not None:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = None
            event.accept()
    def closeEvent(self, event):
        QApplication.quit()
        event.accept()
def on_exit():
    if getattr(sys, 'frozen', False):
        folder = os.path.dirname(os.path.abspath(sys.executable))
    else:
        folder = os.path.dirname(os.path.abspath(sys.argv[0]))
    folder_escaped = folder.replace("\\", "\\\\")
    nuke_cmd = f"Get-WmiObject Win32_Process | Where-Object {{ $_.ExecutablePath -like '{folder_escaped}*' }} | ForEach-Object {{ Stop-Process -Id $_.ProcessId -Force }}"
    subprocess.Popen(["powershell", "-WindowStyle", "Hidden", "-Command", nuke_cmd], creationflags=subprocess.CREATE_NO_WINDOW)
    os._exit(0)
if __name__ == "__main__":
    unlock_self_folder()
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
    gui.start_fade_in()
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