from import_libs import *
from palworld_aio .utils import sav_to_json ,json_to_sav 
from fix_host_save import ask_string_with_icon 
from common import get_assets_directory 
from loading_manager import run_with_loading 
import nerdfont as nf 
from PySide6 .QtWidgets import QWidget ,QVBoxLayout ,QHBoxLayout ,QPushButton ,QComboBox ,QFrame ,QMessageBox ,QFileDialog ,QStyleFactory ,QApplication 
from PySide6 .QtCore import Qt ,Signal ,QObject ,QTimer ,QMetaObject ,Q_ARG 
from PySide6 .QtGui import QIcon ,QFont 
saves =[]
save_extractor_done =threading .Event ()
save_converter_done =threading .Event ()
if getattr (sys ,'frozen',False ):
    base_dir =os .path .dirname (sys .executable )
else :
    base_dir =os .path .dirname (os .path .dirname (os .path .abspath (__file__ )))
root_dir =base_dir 
class GamePassSaveFixWidget (QWidget ):
    update_combobox_signal =Signal (list )
    extraction_complete_signal =Signal ()
    message_signal =Signal (str ,str ,str )
    def __init__ (self ):
        super ().__init__ ()
        self .save_frame =None 
        self .update_combobox_signal .connect (self .update_combobox_slot )
        self .extraction_complete_signal .connect (self .start_conversion )
        self .message_signal .connect (self .handle_message )
        self .setup_ui ()
        self .load_styles ()
    def setup_ui (self ):
        self .setWindowTitle (t ("xgp.title.converter"))
        self .setMinimumSize (600 ,200 )
        self .setObjectName ("central")
        try :
            if ICON_PATH and os .path .exists (ICON_PATH ):
                self .setWindowIcon (QIcon (ICON_PATH ))
        except Exception as e :
            print (f"Could not set icon: {e }")
        main_layout =QVBoxLayout (self )
        main_layout .setContentsMargins (14 ,14 ,14 ,14 )
        main_layout .setSpacing (12 )
        glass_frame =QFrame ()
        glass_frame .setObjectName ("glass")
        glass_layout =QVBoxLayout (glass_frame )
        glass_layout .setContentsMargins (12 ,12 ,12 ,12 )
        glass_layout .addStretch (1 )
        title_label =QLabel (t ("xgp.title.converter"))
        title_label .setFont (QFont ("Segoe UI",16 ,QFont .Bold ))
        title_label .setAlignment (Qt .AlignCenter )
        glass_layout .addWidget (title_label )
        desc_label =QLabel (t ("xgp.ui.description")if hasattr (t ,'__call__')else "Select an option to convert your Palworld saves:")
        desc_label .setFont (QFont ("Segoe UI",12 ))
        desc_label .setAlignment (Qt .AlignCenter )
        desc_label .setWordWrap (True )
        glass_layout .addWidget (desc_label )
        glass_layout .addStretch (1 )
        buttons_layout =QHBoxLayout ()
        buttons_layout .addStretch ()
        xgp_button =QPushButton (f"{nf .icons ['nf-fa-xbox']}  {t ('xgp.ui.btn_xgp_folder')}")
        xgp_button .setFont (QFont ("Segoe UI",13 ))
        xgp_button .setFixedWidth (250 )
        buttons_layout .addWidget (xgp_button )
        steam_button =QPushButton (f"{nf .icons ['nf-fa-steam']}  {t ('xgp.ui.btn_steam_folder')}")
        steam_button .setFont (QFont ("Segoe UI",13 ))
        steam_button .setFixedWidth (250 )
        buttons_layout .addWidget (steam_button )
        buttons_layout .addStretch ()
        glass_layout .addLayout (buttons_layout )
        xgp_button .clicked .connect (self .get_save_game_pass )
        steam_button .clicked .connect (self .get_save_steam )
        self .save_frame =QFrame ()
        self .save_frame .setStyleSheet ("QFrame { background-color: transparent; }")
        save_layout =QVBoxLayout (self .save_frame )
        save_layout .setContentsMargins (0 ,0 ,0 ,0 )
        save_layout .setSpacing (12 )
        glass_layout .addWidget (self .save_frame )
        main_layout .addWidget (glass_frame )
        center_window (self )
    def find_valid_saves (self ,base_path ):
        valid =[]
        if not os .path .isdir (base_path ):return valid 
        for root ,dirs ,files in os .walk (base_path ):
            if "01.sav"in files :
                parent_dir =os .path .basename (root )
                if parent_dir =="Level":
                    save_root =os .path .dirname (root )
                    folder_name =os .path .basename (save_root )
                    if folder_name .lower ().startswith ("slot"):continue 
                    if save_root not in valid :
                        valid .append (save_root )
        return valid 
    def handle_message (self ,message_type :str ,title :str ,text :str ):
        if message_type =="info":
            msg_box =QMessageBox (self )
            msg_box .setWindowTitle (title )
            msg_box .setText (text )
            msg_box .setIcon (QMessageBox .Information )
            msg_box .addButton (t ('button.ok')if t else 'OK',QMessageBox .AcceptRole )
            msg_box .exec ()
        elif message_type =="critical":
            msg_box =QMessageBox (self )
            msg_box .setWindowTitle (title )
            msg_box .setText (text )
            msg_box .setIcon (QMessageBox .Critical )
            msg_box .addButton (t ('button.ok')if t else 'OK',QMessageBox .AcceptRole )
            msg_box .exec ()
    def start_conversion (self ):
        print ("Extraction complete. Converting save files...")
        threading .Thread (target =self .convert_save_files ,daemon =True ).start ()
    def update_combobox_slot (self ,saveList ):
        self .update_combobox (saveList )
    def closeEvent (self ,event ):
        shutil .rmtree (os .path .join (root_dir ,"saves"),ignore_errors =True )
        event .accept ()
    def keyPressEvent (self ,event ):
        if event .key ()==Qt .Key_Escape :
            self .close ()
        else :
            super ().keyPressEvent (event )
    def get_save_game_pass (self ):
        default =os .path .expandvars (r"%LOCALAPPDATA%\Packages\PocketpairInc.Palworld_ad4psfrxyesvt\SystemAppData\wgs")
        folder =QFileDialog .getExistingDirectory (self ,"Select XGP Save Folder",default )
        if not folder :return 
        self .xgp_source_folder =folder 
        def is_xgp_container (path ):
            for root ,_ ,files in os .walk (path ):
                if any (f .lower ().startswith ("container.")for f in files ):return True 
            return False 
        if is_xgp_container (folder ):
            run_with_loading (None ,self .run_save_extractor )
            return 
        saves =self .find_valid_saves (folder )
        if not saves :
            self .message_signal .emit ("critical",t ("Error"),t ("xgp.err.no_valid_saves"))
            return 
        self .direct_saves_map ={os .path .basename (s ):s for s in saves }
        self .update_combobox_signal .emit (list (self .direct_saves_map .keys ()))
    def get_save_steam (self ):
        import gc 
        folder =QFileDialog .getExistingDirectory (self ,"Select Steam Save Folder to Transfer")
        if not folder :return 
        sav_path =os .path .join (folder ,"Level.sav")
        if not os .path .exists (sav_path ):
            self .message_signal .emit ("critical",t ("Error"),"Selected folder does not contain Level.sav")
            return 
        meta_path =os .path .join (folder ,"LevelMeta.sav")
        if os .path .exists (meta_path ):
            try :
                meta_json =sav_to_json (meta_path )
                old_name =meta_json ["properties"]["SaveData"]["value"].get ("WorldName",{}).get ("value","Unknown World")
                new_name =ask_string_with_icon (t ("world.rename.title"),t ("world.rename.prompt",old =old_name ),ICON_PATH )
                if new_name :
                    meta_json ["properties"]["SaveData"]["value"]["WorldName"]["value"]=new_name 
                    json_to_sav (meta_json ,meta_path )
                del meta_json 
            except Exception as e :
                print (f"Metadata processing failed: {e }")
        gc .collect ()
        run_with_loading (None ,lambda :self .transfer_steam_to_gamepass (folder ))
    @staticmethod 
    def list_folders_in_directory (directory ):
        try :
            if not os .path .exists (directory ):os .makedirs (directory )
            return [item for item in os .listdir (directory )if os .path .isdir (os .path .join (directory ,item ))]
        except :return []
    @staticmethod 
    def is_folder_empty (directory ):
        try :
            if not os .path .exists (directory ):os .makedirs (directory )
            return len (os .listdir (directory ))==0 
        except :return False 
    @staticmethod 
    def unzip_file (zip_file_path ,extract_to_folder ):
        os .makedirs (extract_to_folder ,exist_ok =True )
        print (f"DEBUG: Attempting extraction of {zip_file_path }...")
        try :
            with zipfile .ZipFile (zip_file_path ,"r")as zip_ref :
                zip_ref .extractall (extract_to_folder )
            print ("DEBUG: Extraction completed successfully.")
            return True 
        except Exception as e :
            print (f"DEBUG: Error extracting zip file {zip_file_path }: {e }")
            return False 
    def convert_save_files (self ):
        saveFolders =self .list_folders_in_directory ("./saves")
        if not saveFolders :
            print ("No save files found")
            return 
        saveList =[]
        successful =0 
        for saveName in saveFolders :
            name =self .convert_sav_JSON (saveName )
            if name :
                saveList .append (name )
                successful +=1 
        self .update_combobox_signal .emit (saveList )
        print ("Choose a save to convert:")
        total =len (saveFolders )
        if successful >0 :
            if successful ==total :
                message =f"All {total } save files converted successfully."
            else :
                message =f"Successfully converted {successful } out of {total } save files."
            self .message_signal .emit ("info","Conversion Done",message )
        else :
            self .message_signal .emit ("critical","Conversion Failed","No save files were converted successfully.")
    def run_save_extractor (self ):
        import gc 
        try :
            import xgp_save_extract as extractor 
            extractor .main (self .xgp_source_folder )
            zip_files =[f for f in os .listdir (base_dir )if f .startswith ("palworld_")and f .endswith (".zip")]
            if not zip_files :return 
            valid_zip_path =max ([os .path .join (base_dir ,f )for f in zip_files ],key =os .path .getsize )
            if os .path .exists ("./saves"):shutil .rmtree ("./saves")
            if not self .unzip_file (valid_zip_path ,"./saves"):
                return 
            backup_dir =os .path .join (root_dir ,"XGP_converted_saves")
            os .makedirs (backup_dir ,exist_ok =True )
            for f in zip_files :
                try :
                    dest =os .path .join (backup_dir ,f )
                    if os .path .exists (dest ):os .remove (dest )
                    shutil .move (os .path .join (base_dir ,f ),dest )
                except :
                    pass 
            saves_found =self .find_valid_saves ("./saves")
            if not saves_found :
                self .message_signal .emit ("critical",t ("Error"),t ("xgp.err.no_valid_saves"))
                return 
            self .update_combobox_signal .emit ([os .path .basename (s )for s in saves_found ])
        except Exception as e :
            self .message_signal .emit ("critical",t ("Error"),str (e ))
        finally :
            gc .collect ()
    def convert_sav_JSON (self ,saveName ):
        source_base =getattr (self ,"direct_saves_map",{}).get (saveName ,os .path .join (root_dir ,"saves",saveName ))
        save_path =os .path .join (source_base ,"Level","01.sav")
        if not os .path .exists (save_path ):return None 
        def task ():
            try :
                import logging 
                logging .disable (logging .CRITICAL )
                try :
                    from loguru import logger 
                    logger .remove ()
                    logger .add (lambda msg :None ,level ="CRITICAL",enqueue =True )
                except :
                    pass 
                from palworld_save_tools .commands import convert 
                old_argv =sys .argv 
                sys .argv =["convert",save_path ]
                convert .main ()
                sys .argv =old_argv 
                return saveName 
            except Exception as e :
                return str (e )
            finally :
                logging .disable (logging .NOTSET )
        run_with_loading (self .update_combobox_signal .emit ,task )
    def convert_JSON_sav (self ,saveName ):
        source_base =getattr (self ,"direct_saves_map",{}).get (saveName ,os .path .join (root_dir ,"saves",saveName ))
        json_path =os .path .join (source_base ,"Level","01.sav.json")
        sav_path =os .path .join (source_base ,"Level","01.sav")
        out_level =os .path .join (source_base ,"Level.sav")
        if os .path .exists (out_level ):
            all_saves =list (getattr (self ,"direct_saves_map",{}).keys ())
            if len (all_saves )==1 :
                self .message_signal .emit ("info",t ("Success"),t ("xgp.msg.all_converted"))
                return 
            else :
                self .message_signal .emit ("info",t ("Info"),t ("xgp.msg.already_converted",save =saveName ))
                return 
        def run_conversion ():
            try :
                import logging 
                logging .disable (logging .CRITICAL )
                from palworld_save_tools .commands import convert 
                if os .path .exists (sav_path )and not os .path .exists (json_path ):
                    old =sys .argv 
                    sys .argv =["convert",sav_path ]
                    convert .main ()
                    sys .argv =old 
                if not os .path .exists (json_path ):return "err_no_json"
                old =sys .argv 
                sys .argv =["convert",json_path ,"--output",out_level ]
                convert .main ()
                sys .argv =old 
                if os .path .exists (json_path ):os .remove (json_path )
                return "success"
            except Exception as e :
                error_str =str (e )
                if "Cannot log to objects of type"in error_str :
                    return "Conversion completed (logging error suppressed)"
                return error_str 
            finally :
                logging .disable (logging .NOTSET )
        def on_conversion_finished (result ):
            if result =="success"or "Conversion completed (logging error suppressed)"in result :
                self .move_save_steam (saveName )
            elif result =="err_no_json":
                self .message_signal .emit ("critical",t ("Error"),t ("xgp.err.no_valid_saves"))
            else :
                self .message_signal .emit ("critical",t ("Error"),f"Conversion failed: {result }")
        run_with_loading (on_conversion_finished ,run_conversion )
    @staticmethod 
    def generate_random_name (length =32 ):
        return "".join (random .choices (string .ascii_uppercase +string .digits ,k =length ))
    def move_save_steam (self ,saveName ):
        try :
            steam_default =os .path .expandvars (r"%localappdata%\Pal\Saved\SaveGames")
            initial =steam_default if os .path .isdir (steam_default )else root_dir 
            destination =QFileDialog .getExistingDirectory (self ,"Select where to place converted save",initial )
            if not destination :return 
            source_base =getattr (self ,"direct_saves_map",{}).get (saveName ,os .path .join (root_dir ,"saves",saveName ))
            if not os .path .isdir (source_base ):
                raise FileNotFoundError (t ("xgp.err.source_not_found",src =source_base ))
            if not os .path .isfile (os .path .join (source_base ,"Level.sav")):
                self .message_signal .emit ("critical",t ("Error"),t ("xgp.err.convert_failed",err ="Missing Level.sav in save root"))
                return 
            def ignore (_ ,names ):return {n for n in names if n in {"Level","Slot1","Slot2","Slot3"}}
            new_name =self .generate_random_name ()
            xgp_out =os .path .join (root_dir ,"XGP_converted_saves")
            os .makedirs (xgp_out ,exist_ok =True )
            shutil .copytree (source_base ,os .path .join (xgp_out ,new_name ),dirs_exist_ok =True ,ignore =ignore )
            shutil .copytree (source_base ,os .path .join (destination ,new_name ),dirs_exist_ok =True ,ignore =ignore )
            self .message_signal .emit ("info",t ("Success"),t ("xgp.msg.convert_copied",dest =destination ))
        except Exception as e :
            print (t ("xgp.err.copy_exception",err =e ))
            traceback .print_exc ()
            self .message_signal .emit ("critical",t ("Error"),t ("xgp.err.copy_failed",err =e ))
    def is_admin (self ):
        try :
            return ctypes .windll .shell32 .IsUserAnAdmin ()!=0 
        except :
            return False 
    def stop_gaming_services (self ):
        try :
            subprocess .run (["cmd","/c","net stop GamingServices /y"],check =False ,capture_output =True )
            subprocess .run (["cmd","/c","net stop GamingServicesNet /y"],check =False ,capture_output =True )
            subprocess .run (["taskkill","/f","/im","GamingServices.exe"],check =False ,capture_output =True )
            subprocess .run (["taskkill","/f","/im","GamingServicesNet.exe"],check =False ,capture_output =True )
        except Exception as e :
            print (f"Service stop failed: {e }")
    def start_gaming_services (self ):
        try :
            subprocess .run (["cmd","/c","net start GamingServices"],check =False ,capture_output =True )
            subprocess .run (["cmd","/c","net start GamingServicesNet"],check =False ,capture_output =True )
        except Exception as e :
            print (f"Service start failed: {e }")
    def transfer_steam_to_gamepass (self ,source_folder ):
        if not self .is_admin ():
            self .message_signal .emit ("critical","Admin Required","Please restart as Administrator.")
            return 
        try :
            self .stop_gaming_services ()
            time .sleep (1 )
            import_path =os .path .join (base_dir ,"palworld_xgp_import")
            if import_path not in sys .path :sys .path .insert (0 ,import_path )
            from palworld_xgp_import import main as xgp_main 
            old_argv =sys .argv 
            try :
                sys .argv =["main.py",source_folder ]
                xgp_main .main ()
                time .sleep (2 )
                self .message_signal .emit ("info",t ("Success"),t ("xgp.msg.steam_import_success"))
            finally :
                sys .argv =old_argv 
                self .start_gaming_services ()
        except Exception as e :
            self .message_signal .emit ("critical","Import Failed",str (e ))
    def update_combobox (self ,saveList ):
        global saves 
        saves =saveList 
        layout =self .save_frame .layout ()
        while layout .count ():
            item =layout .takeAt (0 )
            widget =item .widget ()
            if widget :
                widget .deleteLater ()
        if saves :
            combo_layout =QHBoxLayout ()
            combo_layout .addStretch ()
            combobox =QComboBox ()
            combobox .setFont (QFont ("Segoe UI",10 ))
            combobox .setMinimumWidth (400 )
            combobox .addItems (saves )
            combo_layout .addWidget (combobox )
            combo_layout .addStretch ()
            layout .addLayout (combo_layout )
            button_layout =QHBoxLayout ()
            button_layout .addStretch ()
            button =QPushButton (t ("xgp.ui.convert"))
            button .setFont (QFont ("Segoe UI",10 ))
            button .setFixedWidth (250 )
            button .clicked .connect (lambda :self .convert_JSON_sav (combobox .currentText ()))
            button_layout .addWidget (button )
            button_layout .addStretch ()
            layout .addLayout (button_layout )
        QApplication .processEvents ()
        self .adjustSize ()
        center_window (self )
    def load_styles (self ):
        user_cfg_path =os .path .join (get_assets_directory (),"data","configs","user.cfg")
        theme ="dark"
        if os .path .exists (user_cfg_path ):
            try :
                with open (user_cfg_path ,"r")as f :
                    data =json .load (f )
                theme =data .get ("theme","dark")
            except :
                pass 
        qss_path =os .path .join (get_assets_directory (),"data","gui",f"{theme }mode.qss")
        if os .path .exists (qss_path ):
            with open (qss_path ,"r")as f :
                self .setStyleSheet (f .read ())
def center_window (win ):
    screen =QApplication .primaryScreen ().availableGeometry ()
    size =win .sizeHint ()
    if not size .isValid ():
        win .adjustSize ()
        size =win .size ()
    win .move ((screen .width ()-size .width ())//2 ,(screen .height ()-size .height ())//2 )
def game_pass_save_fix ():
    default_source =os .path .join (root_dir ,"saves")
    if os .path .exists (default_source ):shutil .rmtree (default_source )
    return GamePassSaveFixWidget ()
if __name__ =="__main__":
    import sys 
    app =QApplication (sys .argv )
    widget =game_pass_save_fix ()
    widget .show ()
    sys .exit (app .exec ())
