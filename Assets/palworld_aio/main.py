import sys
import os
os .environ ['QT_LOGGING_RULES']='*=false'
os .environ ['QT_DEBUG_PLUGINS']='0'
if getattr (sys ,'frozen',False ):
    base_dir =os .path .dirname (sys .executable )
    assets_dir =os .path .join (base_dir ,"Assets")
else :
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

    # Check for CLI mode first
    if len (sys .argv )>1 and not sys.argv[1].startswith('--'):
        # Pure CLI mode - no GUI components
        path_arg =' '.join (sys .argv [1 :]).strip ().strip ('"')
        print (f"Processing save file: {path_arg }")

        # CLI-specific load_save without GUI components
        if constants .loaded_level_json is not None :
            from palworld_aio .utils import restart_program
            restart_program ()
        p =path_arg
        if not p :
            print ("Error: No path provided")
            sys .exit (1 )
        if not p .endswith ('Level.sav'):
            print ("Error: File must be Level.sav")
            sys .exit (1 )
        d =os .path .dirname (p )
        playerdir =os .path .join (d ,'Players')
        if not os .path .isdir (playerdir ):
            print ("Error: Players folder not found")
            sys .exit (1 )
        print ("Loading save...")
        constants .current_save_path =d
        constants .backup_save_path =constants .current_save_path
        import time
        from palworld_aio .utils import sav_to_json
        from palobject import MappingCacheObject ,toUUID

        t0 =time .perf_counter ()
        constants .loaded_level_json =sav_to_json (p )
        t1 =time .perf_counter ()
        print (f"Save loaded and converted to JSON in {t1 -t0 :.2f} seconds")
        save_manager ._build_player_levels ()
        if not constants .loaded_level_json :
            print ("Error: Failed to load save")
            sys .exit (1 )
        data_source =constants .loaded_level_json ['properties']['worldSaveData']['value']
        try :
            if hasattr (MappingCacheObject ,'clear_cache'):
                MappingCacheObject .clear_cache ()
            constants .srcGuildMapping =MappingCacheObject .get (data_source ,use_mp =True )
            if constants .srcGuildMapping ._worldSaveData .get ('GroupSaveDataMap')is None :
                constants .srcGuildMapping .GroupSaveDataMap ={}
        except Exception as e :
            print (f"Error: {e }")
            constants .srcGuildMapping =None
        constants .base_guild_lookup ={}
        guild_name_map ={}
        if constants .srcGuildMapping :
            for gid_uuid ,gdata in constants .srcGuildMapping .GroupSaveDataMap .items ():
                gid =str (gid_uuid )
                guild_name =gdata ['value']['RawData']['value'].get ('guild_name','Unnamed Guild')
                guild_name_map [gid .lower ()]=guild_name
                for base_id_uuid in gdata ['value']['RawData']['value'].get ('base_ids',[]):
                    constants .base_guild_lookup [str (base_id_uuid )]={'GuildName':guild_name ,'GuildID':gid }
        print ("Loading done")
        base_path =constants .get_base_path ()
        log_folder =os .path .join (base_path ,'Scan Save Logger')
        import shutil
        if os .path .exists (log_folder ):
            try :
                shutil .rmtree (log_folder )
            except :
                pass
        os .makedirs (log_folder ,exist_ok =True )
        player_pals_count ={}
        save_manager ._count_pals_found (data_source ,player_pals_count ,log_folder ,constants .current_save_path ,guild_name_map )
        constants .PLAYER_PAL_COUNTS =player_pals_count
        save_manager ._process_scan_log (data_source ,playerdir ,log_folder ,guild_name_map )

        print ("Running cleanup operations...")
        remove_invalid_items_from_save ()
        remove_invalid_pals_from_save ()
        delete_invalid_structure_map_objects ()
        delete_unreferenced_data ()
        delete_non_base_map_objects ()
        print ("Saving changes...")
        # Direct synchronous save for CLI mode
        if constants .current_save_path and constants .loaded_level_json :
            from import_libs import backup_whole_directory
            from palworld_aio.utils import json_to_sav

            backup_whole_directory (constants .backup_save_path ,'Backups/AllinOneTools')
            level_sav_path =os .path .join (constants .current_save_path ,'Level.sav')
            t0 =time .perf_counter ()
            json_to_sav (constants .loaded_level_json ,level_sav_path )
            t1 =time .perf_counter ()
            # Handle player file deletions
            players_folder =os .path .join (constants .current_save_path ,'Players')
            for uid in constants .files_to_delete :
                f =os .path .join (players_folder ,uid +'.sav')
                f_dps =os .path .join (players_folder ,f'{uid }_dps.sav')
                try :
                    os .remove (f )
                except FileNotFoundError :
                    pass
                try :
                    os .remove (f_dps )
                except FileNotFoundError :
                    pass
            constants .files_to_delete .clear ()
            duration =t1 -t0
            print (f'Changes saved successfully in {duration :.2f} seconds')
        else:
            print ("Error: No save file loaded")
        sys .exit (0 )

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

    # GUI mode - no CLI arguments provided
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    app.setStyle('Fusion')
    if os.path.exists(constants.ICON_PATH):
        app.setWindowIcon(QIcon(constants.ICON_PATH))
    window = MainWindow()
    center_window(window)
    window.show()
    sys.exit(app.exec())
if __name__ =='__main__':
    run_aio ()
