import sys ,os 
sys .path .insert (0 ,os .path .abspath ("Assets"))
from cx_Freeze import setup ,Executable 
def find_customtkinter_assets ():
    try :
        import customtkinter 
        p =os .path .dirname (customtkinter .__file__ )
        a =os .path .join (p ,"assets")
        if os .path .exists (a ):return (a ,"lib/customtkinter/assets")
    except :pass 
    return None 
def find_ooz_library ():
    try :
        import ooz 
        return (os .path .dirname (ooz .__file__ ),"Assets/palworld_save_tools/lib/windows")
    except :pass 
    return None 
def find_pyside6_assets ():
    try :
        import PySide6 
        p =os .path .dirname (PySide6 .__file__ )
        a =os .path .join (p ,"plugins")
        if os .path .exists (a ):return (a ,"lib/PySide6/plugins")
    except :pass 
    return None 
build_exe_options ={
"packages":[
"pygame","loguru","subprocess","pathlib","shutil","matplotlib","pandas",
"customtkinter","cityhash","tkinter","json","uuid","time","datetime",
"struct","enum","collections","itertools","math","zlib","gzip","zipfile",
"threading","multiprocessing","io","base64","binascii","hashlib","hmac",
"secrets","ssl","socket","urllib","http","email","mimetypes","tempfile",
"glob","fnmatch","argparse","configparser","logging","traceback",
"warnings","weakref","string","random","re","copy","ctypes","functools",
"gc","importlib","PIL","numpy","ooz","pickle","tarfile","csv","pprint",
"code","platform","fontTools","PySide6.QtCore","PySide6.QtGui",
"PySide6.QtWidgets","nerdfont","unittest","unittest.mock"
],
"excludes":[
"test","pdb","tkinter.test","lib2to3","distutils",
"setuptools","pip","wheel","venv","ensurepip","msgpack"
],
"include_files":[
("Assets/","Assets/"),
("readme.md","readme.md"),
("license","license")
],
"zip_include_packages":[],
"zip_exclude_packages":["*"],
"build_exe":"PST_standalone",
"optimize":0 
}
ctk_a =find_customtkinter_assets ()
if ctk_a :build_exe_options ["include_files"].append (ctk_a )
ooz_l =find_ooz_library ()
if ooz_l :build_exe_options ["include_files"].append (ooz_l )
ps6_a =find_pyside6_assets ()
if ps6_a :build_exe_options ["include_files"].append (ps6_a )
setup (
name ="PalworldSaveTools",
version="1.1.42",
options ={"build_exe":build_exe_options },
executables =[
Executable (
"menu.py",
base ="Console"if sys .platform =="win32"else None ,
target_name ="PalworldSaveTools.exe",
icon ="Assets/resources/pal.ico"
)
]
)
