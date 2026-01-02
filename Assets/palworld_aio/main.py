import sys 
import os 
base_dir =os .path .dirname (os .path .dirname (os .path .abspath (__file__ )))
assets_dir =base_dir if os .path .basename (base_dir )=="Assets"else os .path .join (base_dir ,"Assets")
if assets_dir not in sys .path :
    sys .path .insert (0 ,assets_dir )
for sub in ['palworld_coord','palworld_save_tools','palworld_xgp_import','resources','palworld_aio']:
    p =os .path .join (assets_dir ,sub )
    if os .path .isdir (p )and p not in sys .path :
        sys .path .insert (0 ,p )
from PySide6 .QtWidgets import QApplication 
from PySide6 .QtGui import QIcon 
from PySide6 .QtCore import Qt 
from i18n import init_language 
from import_libs import center_window 
from .import constants 
from .ui import MainWindow 
from .save_manager import save_manager 
from .func_manager import (
remove_invalid_items_from_save ,
remove_invalid_pals_from_save ,
delete_invalid_structure_map_objects ,
delete_unreferenced_data ,
delete_non_base_map_objects 
)
def run_aio ():
    init_language ('en_US')
    if len (sys .argv )>1 :
        path_arg =' '.join (sys .argv [1 :]).strip ().strip ('"')
        app =QApplication .instance ()
        if app is None :
            app =QApplication (sys .argv )
        save_manager .load_save (path_arg )
        remove_invalid_items_from_save ()
        remove_invalid_pals_from_save ()
        delete_invalid_structure_map_objects ()
        delete_unreferenced_data ()
        delete_non_base_map_objects ()
        save_manager .save_changes ()
    else :
        app =QApplication .instance ()
        if app is None :
            app =QApplication (sys .argv )
        app .setStyle ('Fusion')
        if os .path .exists (constants .ICON_PATH ):
            app .setWindowIcon (QIcon (constants .ICON_PATH ))
        window =MainWindow ()
        center_window (window )
        window .show ()
        sys .exit (app .exec ())
if __name__ =='__main__':
    run_aio ()
