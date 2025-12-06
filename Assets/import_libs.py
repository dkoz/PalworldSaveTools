import os, warnings
os.environ['PYGAME_HIDE_SUPPORT_PROMPT']='1'
warnings.filterwarnings("ignore", category=UserWarning, module="pygame.pkgdata")
import sys,argparse,code,collections,copy,ctypes,datetime,functools,gc,importlib.metadata,json,shutil,glob
import logging,multiprocessing,platform,pprint,re,subprocess,tarfile,threading,pickle,zipfile,customtkinter,string,palworld_coord
import time,traceback,uuid,io,pathlib,tkinter as tk,tkinter.font,csv,urllib.request,tempfile,random,pandas as pd
import matplotlib.pyplot as plt,matplotlib.patches as patches,matplotlib.font_manager as font_manager,matplotlib.patheffects as path_effects
from multiprocessing import shared_memory
from tkinter import ttk, filedialog, messagebox, PhotoImage, simpledialog
from PIL import Image,ImageDraw,ImageOps,ImageFont,ImageTk
sys.path.insert(0,os.path.abspath(os.path.join(os.path.dirname(__file__),"palworld_save_tools","commands")))
from palworld_save_tools.archive import *
from palworld_save_tools.palsav import *
from palworld_save_tools.paltypes import *
import palworld_save_tools.rawdata.group as palworld_save_group
from palobject import *
from palworld_save_tools.gvas import *
from palworld_save_tools.rawdata import *
from palworld_save_tools.json_tools import *
from generate_map import *
from palworld_coord import sav_to_map
from common import ICON_PATH
from collections import defaultdict
import pygame
from common import *
def backup_whole_directory(source_folder, backup_folder):
    import os, sys, shutil, datetime as dt
    def get_timestamp(): return dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    source_folder = os.path.abspath(source_folder)
    if not os.path.isabs(backup_folder):
        base_path = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        backup_folder = os.path.abspath(os.path.join(base_path, backup_folder))
    else: backup_folder = os.path.abspath(backup_folder)
    if not os.path.exists(backup_folder): os.makedirs(backup_folder)
    print("Now backing up Level.sav, LevelMeta.sav and Players folder...")
    timestamp = get_timestamp()
    backup_path = os.path.join(backup_folder, f"PalworldSave_backup_{timestamp}")
    os.makedirs(backup_path, exist_ok=True)
    level_src = os.path.join(source_folder, "Level.sav")
    levelmeta_src = os.path.join(source_folder, "LevelMeta.sav")
    players_src = os.path.join(source_folder, "Players")
    if os.path.exists(level_src): shutil.copy2(level_src, os.path.join(backup_path, "Level.sav"))
    if os.path.exists(levelmeta_src): shutil.copy2(levelmeta_src, os.path.join(backup_path, "LevelMeta.sav"))
    if os.path.exists(players_src): shutil.copytree(players_src, os.path.join(backup_path, "Players"))
    print(f"Backup created at: {backup_path}")
def center_window(win):
    win.update_idletasks()
    w, h = win.winfo_width(), win.winfo_height()
    ws, hs = win.winfo_screenwidth(), win.winfo_screenheight()
    x, y = (ws - w) // 2, (hs - h) // 2
    win.geometry(f'{w}x{h}+{x}+{y}')
try:
    from i18n import t
except Exception:
    def t(key, **fmt):
        return key.format(**fmt) if fmt else key