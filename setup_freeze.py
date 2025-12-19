import sys,os
sys.path.insert(0,os.path.abspath("Assets"))
from cx_Freeze import setup,Executable
def find_customtkinter_assets():
    try:
        import customtkinter
        customtkinter_path=os.path.dirname(customtkinter.__file__)
        assets_path=os.path.join(customtkinter_path,"assets")
        if os.path.exists(assets_path): return(assets_path,"lib/customtkinter/assets")
    except ImportError: pass
    return None
def find_ooz_library():
    try:
        import ooz
        ooz_path=os.path.dirname(ooz.__file__)
        return(ooz_path,"Assets/palworld_save_tools/lib/windows")
    except ImportError: pass
    return None
def find_pyside6_assets():
    try:
        import PySide6
        pyside6_path=os.path.dirname(PySide6.__file__)
        plugins_path=os.path.join(pyside6_path,"plugins")
        if os.path.exists(plugins_path): return(plugins_path,"lib/PySide6/plugins")
    except ImportError: pass
    return None
build_exe_options={
    "packages":[
        "pygame","loguru","os","sys","subprocess","pathlib","shutil","matplotlib","pandas","customtkinter",
        "cityhash","tkinter","json","uuid","time","datetime","struct","enum","collections","itertools","math",
        "zlib","gzip","zipfile","threading","multiprocessing","io","base64","binascii","hashlib","hmac",
        "secrets","ssl","socket","urllib","http","email","mimetypes","tempfile","glob","fnmatch","argparse",
        "configparser","logging","traceback","warnings","weakref","string","random","re","copy","ctypes",
        "functools","gc","importlib","importlib.metadata","importlib.util","PIL","PIL.Image","PIL.ImageDraw",
        "PIL.ImageOps","PIL.ImageFont","numpy","ooz","pickle","tarfile","csv","pprint","code","platform",
        "matplotlib.patches","matplotlib.font_manager","matplotlib.patheffects","tkinter.font",
        "tkinter.simpledialog","urllib.request","multiprocessing.shared_memory","fontTools","PySide6.QtCore","PySide6.QtGui","PySide6.QtWidgets","nerdfont"
    ],
    "excludes":[
        "test","unittest","pdb","tkinter.test","lib2to3","distutils","setuptools","pip","wheel","venv",
        "ensurepip","msgpack"
    ],
    "include_files":[
        ("Assets/","Assets/"),("readme.md","readme.md"),("license","license")
    ],
    "includes":[
        "all_in_one_tools","character_transfer","modify_save","slot_injector","fix_host_save",
        "restore_map","convertids","convert_players_location_finder","convert_level_location_finder",
        "game_pass_save_fix"
    ],
    "zip_include_packages":[],
    "zip_exclude_packages":["customtkinter"],
    "build_exe":"PST_standalone",
    "bin_includes":["python311.dll","vcruntime140.dll"] if sys.platform=="win32" else []
}
customtkinter_assets=find_customtkinter_assets()
if customtkinter_assets: build_exe_options["include_files"].append(customtkinter_assets)
ooz_library=find_ooz_library()
if ooz_library: build_exe_options["include_files"].append(ooz_library)
pyside6_assets=find_pyside6_assets()
if pyside6_assets: build_exe_options["include_files"].append(pyside6_assets)
base=None
if sys.platform=="win32": base="Console"
setup(
    name="PalworldSaveTools",
    version="1.1.35",
    description="All-in-one tool for fixing/trans ferring/editing Palworld saves",
    options={"build_exe":build_exe_options},
    executables=[
        Executable("menu.py",base=base,target_name="PalworldSaveTools.exe",icon="Assets/resources/pal.ico")
    ]
)