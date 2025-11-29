import os, sys, shutil
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pygame.pkgdata")
from pathlib import Path
import importlib.util
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from PIL import Image, ImageTk
import os, sys, urllib.request, zipfile, subprocess, re
GITHUB_RAW_URL = "https://raw.githubusercontent.com/deafdudecomputers/PalworldSaveTools/main/Assets/common.py"
GITHUB_LATEST_ZIP = "https://github.com/deafdudecomputers/PalworldSaveTools/releases/latest/download/PST_standalone.zip"
def check_github_update(auto_download=False, download_folder="PST_update", force_test=False):
    try:
        r=urllib.request.urlopen(GITHUB_RAW_URL,timeout=5)
        content=r.read().decode("utf-8")
        match=re.search(r'APP_VERSION\s*=\s*"([^"]+)"',content)
        latest=match.group(1) if match else None
        local,_=get_versions()
        if force_test: local="0.0.1"
        if latest:
            local_tuple=tuple(int(x) for x in local.split("."))
            latest_tuple=tuple(int(x) for x in latest.split("."))
            if local_tuple>=latest_tuple:
                print(f"{GREEN_FONT}You are on the latest version: {local}{RESET_FONT}")
                return True,latest
            print(f"{YELLOW_FONT}Update available! Local: {local}, Latest: {latest}{RESET_FONT}")
            new_folder=f"PST_v{latest}"
            if auto_download:
                if os.path.exists(new_folder):
                    new_exe=None
                    for root,dirs,files in os.walk(new_folder):
                        if "PalworldSaveTools.exe" in files:
                            new_exe=os.path.join(root,"PalworldSaveTools.exe")
                            break
                    if new_exe:
                        print(f"{YELLOW_FONT}Launching existing downloaded update...{RESET_FONT}")
                        subprocess.Popen([new_exe])
                        sys.exit(0)
                os.makedirs(new_folder,exist_ok=True)
                zip_path=os.path.join(new_folder,"update.zip")
                try:
                    print("Downloading latest release...")
                    urllib.request.urlretrieve(GITHUB_LATEST_ZIP,zip_path)
                    print(f"{GREEN_FONT}Downloaded latest ZIP to {zip_path}{RESET_FONT}")
                    print("Extracting...")
                    with zipfile.ZipFile(zip_path,'r') as zf: zf.extractall(new_folder)
                    os.remove(zip_path)
                    print(f"{GREEN_FONT}Extraction complete.{RESET_FONT}")
                    new_exe=None
                    for root,dirs,files in os.walk(new_folder):
                        if "PalworldSaveTools.exe" in files:
                            new_exe=os.path.join(root,"PalworldSaveTools.exe")
                            break
                    if new_exe:
                        print(f"{YELLOW_FONT}Launching new PST...{RESET_FONT}")
                        subprocess.Popen([new_exe])
                        sys.exit(0)
                    print(f"{RED_FONT}New executable not found in {new_folder}{RESET_FONT}")
                except Exception as e:
                    print(f"{RED_FONT}Failed to download or extract latest ZIP: {e}{RESET_FONT}")
            return False,latest
        print(f"{RED_FONT}Could not parse APP_VERSION from GitHub.{RESET_FONT}")
        return True,None
    except Exception as e:
        print(f"{RED_FONT}Failed to check GitHub version: {e}{RESET_FONT}")
        return True,None
def is_frozen():
    return getattr(sys, 'frozen', False)
def get_assets_path():
    if is_frozen():
        return os.path.join(os.path.dirname(sys.executable), "Assets")
    else:
        return os.path.join(os.path.dirname(__file__), "Assets")
def setup_import_paths():
    assets_path = get_assets_path()
    if assets_path not in sys.path:
        sys.path.insert(0, assets_path)
    subdirs = ['palworld_coord', 'palworld_save_tools', 'palworld_xgp_import', 'resources']
    for subdir in subdirs:
        subdir_path = os.path.join(assets_path, subdir)
        if os.path.exists(subdir_path) and subdir_path not in sys.path:
            sys.path.insert(0, subdir_path)
setup_import_paths()
try:
    from i18n import init_language, t, set_language, get_language, load_resources
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
    def __init__(self):
        self._modules = {}
        self._common_funcs = None    
    def _try_import(self, module_name):
        import importlib
        if module_name in sys.modules:
            importlib.reload(sys.modules[module_name])
            self._modules[module_name] = sys.modules[module_name]
            return self._modules[module_name]
        try:
            module = importlib.import_module(module_name)
            self._modules[module_name] = module
            return module
        except ImportError:
            pass
        try:
            full_module_name = f"Assets.{module_name}"
            if full_module_name in sys.modules:
                importlib.reload(sys.modules[full_module_name])
                self._modules[module_name] = sys.modules[full_module_name]
                return self._modules[module_name]
            module = importlib.import_module(full_module_name)
            self._modules[module_name] = module
            return module
        except ImportError:
            pass
        try:
            assets_path = get_assets_path()
            module_file = os.path.join(assets_path, f"{module_name}.py")
            if os.path.exists(module_file):
                spec = importlib.util.spec_from_file_location(module_name, module_file)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    self._modules[module_name] = module
                    return module
        except Exception:
            pass
        raise ImportError(f"Could not import module: {module_name}")
    def get_module(self, module_name):
        return self._try_import(module_name)    
    def get_function(self, module_name, function_name):
        module = self.get_module(module_name)
        return getattr(module, function_name)    
    def get_common_functions(self):
        if self._common_funcs is not None:
            return self._common_funcs        
        try:
            common_module = self._try_import('common')
            self._common_funcs = {
                'ICON_PATH': getattr(common_module, 'ICON_PATH', 'Assets/resources/pal.ico'),
                'get_versions': getattr(common_module, 'get_versions', lambda: ("Unknown", "Unknown")),
                'open_file_with_default_app': getattr(common_module, 'open_file_with_default_app', lambda x: None)
            }
        except ImportError:
            self._common_funcs = {
                'ICON_PATH': 'Assets/resources/pal.ico',
                'get_versions': lambda: ("Unknown", "Unknown"),
                'open_file_with_default_app': lambda x: None
            }        
        return self._common_funcs
lazy_importer = LazyImporter()
common_funcs = lazy_importer.get_common_functions()
ICON_PATH = common_funcs['ICON_PATH']
get_versions = common_funcs['get_versions']
open_file_with_default_app = common_funcs['open_file_with_default_app']
def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')
def is_frozen():
    return getattr(sys, 'frozen', False)
def get_python_executable():
    if is_frozen():
        return sys.executable
    else:
        return sys.executable
RED_FONT = "\033[91m"
BLUE_FONT = "\033[94m"
GREEN_FONT = "\033[92m"
YELLOW_FONT= "\033[93m"
PURPLE_FONT = "\033[95m"
RESET_FONT = "\033[0m"
original_executable = sys.executable
def set_console_title(title): os.system(f'title {title}') if sys.platform == "win32" else print(f'\033]0;{title}\a', end='', flush=True)
def setup_environment():
    if sys.platform != "win32":
        try:
            import resource
            resource.setrlimit(resource.RLIMIT_NOFILE, (65535, 65535))
        except ImportError:
            pass
    os.system('cls' if os.name == 'nt' else 'clear')
    os.makedirs("PalworldSave/Players", exist_ok=True)
try:
    columns = os.get_terminal_size().columns
except OSError:
    columns = 80
def center_text(text):
    return "\n".join(line.center(columns) for line in text.splitlines())
def run_tool(choice):
    def import_and_call(module_name, function_name, *args):
        if module_name in sys.modules:
            importlib.reload(sys.modules[module_name])
        func = lazy_importer.get_function(module_name, function_name)
        return func(*args) if args else func()
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
            lambda: import_and_call("all_in_one_deletion", "all_in_one_deletion"),
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
        print(f"Invalid choice or error running tool: {e}")
        raise
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
class MenuGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        try:
            if os.name == 'nt' and os.path.exists(ICON_PATH):
                self.iconbitmap(ICON_PATH)
        except Exception as e:
            print(f"Could not set icon: {e}")
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure("TFrame", background="#2f2f2f")
        style.configure("TLabel", background="#2f2f2f", foreground="white")
        style.configure("TEntry", fieldbackground="#444444", foreground="white")
        style.configure("Treeview.Heading", font=("Arial", 12, "bold"), background="#444444", foreground="white")
        style.configure("Treeview", background="#333333", foreground="white", rowheight=25, fieldbackground="#333333", borderwidth=0)
        style.configure("Dark.TButton", background="#555555", foreground="white", padding=6)
        style.map("Dark.TButton", background=[("active", "#666666"), ("!disabled", "#555555")], foreground=[("disabled", "#888888"), ("!disabled", "white")])
        tools_version, _ = get_versions()
        self.title(t("app.title", version=tools_version))
        self.configure(bg="#2f2f2f")
        self.geometry("800x550")
        self.resizable(False, True)
        self.info_labels = [] 
        self.category_frames = [] 
        self.tool_buttons = []  
        self.lang_combo = None
        self.setup_ui()
        center_window(self)
    def setup_ui(self):
        root_frame = ttk.Frame(self, style="TFrame")
        root_frame.pack(fill="both", expand=True, padx=10, pady=10)
        canvas = tk.Canvas(root_frame, bg="#2f2f2f", highlightthickness=0)
        vbar = ttk.Scrollbar(root_frame, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        vbar.pack(side="right", fill="y")
        container = ttk.Frame(canvas, style="TFrame")
        win = canvas.create_window((0, 0), window=container, anchor="nw")
        def _on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        def _on_canvas_configure(event):
            canvas.itemconfigure(win, width=event.width)
        container.bind("<Configure>", _on_frame_configure)
        canvas.bind("<Configure>", _on_canvas_configure)
        def _on_mousewheel(event):
            delta = -1 * int(event.delta / 120) if event.delta else 0
            canvas.yview_scroll(delta, "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        topbar = ttk.Frame(container, style="TFrame")
        topbar.pack(fill="x", pady=(0, 6))
        self.lang_combo = ttk.Combobox(topbar, state="readonly", values=[])
        self.lang_combo.pack(side="right", padx=(0,6))
        self.lang_combo.bind("<<ComboboxSelected>>", lambda e: self.on_language_change())
        logo_path = os.path.join("Assets", "resources", "PalworldSaveTools.png")
        if os.path.exists(logo_path):
            img = Image.open(logo_path)
            img = img.resize((400, 100), Image.LANCZOS)
            self.logo_img = ImageTk.PhotoImage(img)
            ttk.Label(container, image=self.logo_img, style="TLabel").pack(anchor="center", pady=(0,10))
        else:
            ascii_font = ("Consolas", 12)
            logo_text = r"""
          ___      _                _    _ ___              _____         _    
         | _ \__ _| |_ __ _____ _ _| |__| / __| __ ___ ____|_   _|__  ___| |___
         |  _/ _` | \ V  V / _ \ '_| / _` \__ \/ _` \ V / -_)| |/ _ \/ _ \ (_-<
         |_| \__,_|_|\_/\_/\___/_| |_\__,_|___/\__,_|\_/\___||_|\___/\___/_/__/
                """
            for line in logo_text.strip('\n').split('\n'):
                ttk.Label(container, text=line, font=ascii_font, style="TLabel").pack(anchor="center")
        tools_version, game_version = get_versions()
        info_items = [
            ("app.subtitle", {"game_version": game_version}, "#6f9", ("Consolas", 10)),
            ("notice.backup", {}, "#f44", ("Consolas", 9, "bold")),
            ("notice.patch", {"game_version": game_version}, "#f44", ("Consolas", 9, "bold")),
            ("notice.errors", {}, "#f44", ("Consolas", 9, "bold")),
        ]
        for key, fmt, color, font in info_items:
            label = ttk.Label(container, text=t(key, **fmt), style="TLabel")
            label.configure(foreground=color, font=font)
            label.pack(pady=(0,2))
            self.info_labels.append((label, key, fmt))
        ttk.Label(container, text="="*85, font=("Consolas", 12), style="TLabel").pack(pady=(5,10))
        tools_frame = ttk.Frame(container, style="TFrame")
        tools_frame.pack(fill="both", expand=True)
        tools_frame.columnconfigure(0, weight=1)
        tools_frame.columnconfigure(1, weight=1)
        tools_frame.columnconfigure(0, weight=1, uniform="cols")
        tools_frame.columnconfigure(1, weight=1, uniform="cols")
        left_frame = ttk.Frame(tools_frame, style="TFrame")
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0,5))
        left_frame.columnconfigure(0, weight=1)
        right_frame = ttk.Frame(tools_frame, style="TFrame")
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(5,0))
        right_frame.columnconfigure(0, weight=1)
        left_categories = [
            ("cat.converting", converting_tool_keys, "#2196F3"),
        ]
        right_categories = [
            ("cat.management", management_tool_keys, "#4CAF50")
        ]
        for idx, (title, tools, color) in enumerate(left_categories):
            frame = self.create_labeled_frame(left_frame, title, color)
            frame.columnconfigure(0, weight=1)
            self.populate_tools(frame, tools, idx)
        for idx, (title, tools, color) in enumerate(right_categories, start=len(left_categories)):
            frame = self.create_labeled_frame(right_frame, title, color)
            frame.columnconfigure(0, weight=1)
            self.populate_tools(frame, tools, idx)
        self.refresh_texts()
    def create_labeled_frame(self, parent, title_key, color):
        style_name = f"{title_key.replace('.', '_')}.TLabelframe"
        ttk.Style().configure(style_name, background="#2a2a2a", foreground=color, font=("Consolas", 12, "bold"), labelanchor="n")
        ttk.Style().configure(f"{style_name}.Label", background="#2a2a2a", foreground=color, font=("Consolas", 12, "bold"))
        frame = ttk.LabelFrame(parent, text=t(title_key), style=style_name, labelanchor="n")
        frame.pack(fill="x", pady=5)
        self.category_frames.append((frame, title_key))
        return frame
    def populate_tools(self, parent, tool_keys, category_offset):
        parent.columnconfigure(0, weight=1)
        for i, tool_key in enumerate(tool_keys):
            idx = (category_offset, i)
            btn = ttk.Button(parent, text=t(tool_key), style="Dark.TButton", command=lambda idx=idx: self.run_tool(idx))
            btn.grid(row=i, column=0, sticky="ew", pady=3, padx=5)
            self.tool_buttons.append((btn, tool_key))
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
    def run_tool(self, choice):
        tool_name = self.get_tool_name(choice)
        print(t('status.open', name=tool_name))
        self.withdraw()
        try:
            tool_window = run_tool(choice)
            if tool_window: tool_window.wait_window()
        except Exception:
            pass
        print(t('status.close', name=tool_name))
        self.deiconify()
    def on_language_change(self):
        sel = self.lang_combo.get()
        lang_map = {t(f'lang.{code}'): code for code in ["zh_CN","en_US","ru_RU","fr_FR","es_ES","de_DE","ja_JP","ko_KR"]}
        lang = lang_map.get(sel, "zh_CN")
        set_language(lang)
        load_resources(lang)
        self.refresh_texts()
    def refresh_texts(self):
        tools_version, game_version = get_versions()
        self.title(t("app.title", version=tools_version))
        for label, key, fmt in self.info_labels:
            label.configure(text=t(key, **fmt))
        for frame, key in self.category_frames:
            frame.configure(text=t(key))
        for btn, key in self.tool_buttons:
            btn.configure(text=t(key))
        values = [t(f'lang.{code}') for code in ["zh_CN","en_US","ru_RU","fr_FR","es_ES","de_DE","ja_JP","ko_KR"]]
        self.lang_combo.configure(values=values)
        cur = get_language()
        self.lang_combo.set(t(f'lang.{cur}'))
def center_window(win):
    win.update_idletasks()
    w, h = win.winfo_width(), win.winfo_height()
    ws, hs = win.winfo_screenwidth(), win.winfo_screenheight()
    x, y = (ws - w) // 2, (hs - h) // 2
    win.geometry(f'{w}x{h}+{x}+{y}')
def on_exit():
    app.destroy()
    sys.exit(0)
if __name__=="__main__":
    try:
        init_language("zh_CN")
    except Exception:
        pass
    tv,gv=get_versions()
    set_console_title(f"PalworldSaveTools v{tv}")
    clear_console()
    check_github_update(auto_download=True,download_folder="PST_update",force_test=False)
    import tkinter as tk
    tk._default_root=None
    from Assets.all_in_one_deletion import all_in_one_deletion
    window=all_in_one_deletion()
    window.mainloop()
