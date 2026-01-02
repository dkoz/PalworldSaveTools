import sys 
import os 
os .environ ['QT_LOGGING_RULES']='*=false'
os .environ ['QT_DEBUG_PLUGINS']='0'
base_dir =os .path .dirname (os .path .dirname (os .path .abspath (__file__ )))
assets_dir =base_dir if os .path .basename (base_dir )=="Assets"else os .path .join (base_dir ,"Assets")
if assets_dir not in sys .path :
    sys .path .insert (0 ,assets_dir )
for sub in ['palworld_coord','palworld_save_tools','palworld_xgp_import','resources','palworld_aio']:
    p =os .path .join (assets_dir ,sub )
    if os .path .isdir (p )and p not in sys .path :
        sys .path .insert (0 ,p )
import io 
from contextlib import redirect_stderr 
stderr_capture =io .StringIO ()
try :
    with redirect_stderr (stderr_capture ):
        from PySide6 .QtWidgets import QApplication 
        from PySide6 .QtGui import QIcon 
        from PySide6 .QtCore import Qt ,qInstallMessageHandler ,QtMsgType 
        from i18n import init_language 
        from import_libs import center_window 
        from palworld_aio import constants 
        from palworld_aio .ui import MainWindow 
        from palworld_aio .save_manager import save_manager 
        from palworld_aio .func_manager import (
        remove_invalid_items_from_save ,
        remove_invalid_pals_from_save ,
        delete_invalid_structure_map_objects ,
        delete_unreferenced_data ,
        delete_non_base_map_objects 
        )
except Exception :
    from PySide6 .QtWidgets import QApplication 
    from PySide6 .QtGui import QIcon 
    from PySide6 .QtCore import Qt ,qInstallMessageHandler ,QtMsgType 
    from i18n import init_language 
    from import_libs import center_window 
    from palworld_aio import constants 
    from palworld_aio .ui import MainWindow 
    from palworld_aio .save_manager import save_manager 
    from palworld_aio .func_manager import (
    remove_invalid_items_from_save ,
    remove_invalid_pals_from_save ,
    delete_invalid_structure_map_objects ,
    delete_unreferenced_data ,
    delete_non_base_map_objects 
    )
def qt_message_handler (mode ,context ,message ):
    if "QThreadStorage"in str (message )and "destroyed before end of thread"in str (message ):
        return 
qInstallMessageHandler (qt_message_handler )
def run_aio ():
    try :
        with redirect_stderr (stderr_capture ):
            init_language ('en_US')
    except Exception :
        init_language ('en_US')

    # Check for test loading popup argument
    if '--test-loading-popup' in sys.argv:
        from palworld_aio.widgets import LoadingPopup

        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

        # Create and show the loading popup for testing
        popup = LoadingPopup()
        popup.show_with_fade()

        # Keep it visible for 5 seconds, then fade out
        def hide_popup():
            popup.hide_with_fade(lambda: app.quit())

        from PySide6.QtCore import QTimer
        QTimer.singleShot(5000, hide_popup)

        sys.exit(app.exec())

    if len (sys .argv )>1 and not sys.argv[1].startswith('--'):
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
