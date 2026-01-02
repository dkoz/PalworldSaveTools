import os 
import sys 
import json 
import traceback 
from PySide6 .QtWidgets import (
QWidget ,QVBoxLayout ,QHBoxLayout ,QLabel ,QPushButton ,
QFrame ,QScrollArea ,QMessageBox ,QSizePolicy ,QSpacerItem ,QGridLayout 
)
from PySide6 .QtCore import Qt ,QSize ,Signal 
from PySide6 .QtGui import QPixmap ,QIcon ,QFont ,QCursor 
from i18n import t 
try :
    from palworld_aio import constants 
except ImportError :
    from ..import constants 
def get_assets_path ():

    return os .path .dirname (os .path .dirname (os .path .dirname (os .path .abspath (__file__ ))))
def load_tool_icons ():

    icon_file =os .path .join (get_assets_path (),"toolicon.json")
    if not os .path .exists (icon_file ):
        return {}
    try :
        with open (icon_file ,'r',encoding ='utf-8')as f :
            data =json .load (f )
        return data if isinstance (data ,dict )else {}
    except Exception :
        return {}
CONVERTING_TOOL_KEYS =[
"tool.convert.level.to_json",
"tool.convert.level.to_sav",
"tool.convert.players.to_json",
"tool.convert.players.to_sav",
"tool.convert.gamepass.steam",
"tool.convert.steamid",
]
MANAGEMENT_TOOL_KEYS =[
"tool.slot_injector",
"tool.modify_save",
"tool.character_transfer",
"tool.fix_host_save",
"tool.restore_map",
]
class ToolButton (QWidget ):

    clicked =Signal ()
    def __init__ (self ,label_text ,tooltip_text ,icon_path =None ,parent =None ):
        super ().__init__ (parent )
        self .setProperty ("class","toolRow")
        self .setCursor (QCursor (Qt .PointingHandCursor ))
        layout =QHBoxLayout (self )
        layout .setContentsMargins (8 ,6 ,8 ,6 )
        layout .setSpacing (12 )
        self .icon_label =QLabel ()
        self .icon_label .setFixedSize (32 ,32 )
        if icon_path and os .path .exists (icon_path ):
            pix =QPixmap (icon_path ).scaled (32 ,32 ,Qt .KeepAspectRatio ,Qt .SmoothTransformation )
            self .icon_label .setPixmap (pix )
        else :
            default_icon =os .path .join (get_assets_path (),'resources','pal.ico')
            if os .path .exists (default_icon ):
                pix =QPixmap (default_icon ).scaled (32 ,32 ,Qt .KeepAspectRatio ,Qt .SmoothTransformation )
                self .icon_label .setPixmap (pix )
        layout .addWidget (self .icon_label )
        self .text_label =QLabel (label_text )
        self .text_label .setToolTip (tooltip_text )
        self .text_label .setFont (QFont ("Segoe UI",11 ))
        layout .addWidget (self .text_label ,1 )
    def mousePressEvent (self ,event ):
        if event .button ()==Qt .LeftButton :
            self .clicked .emit ()
        super ().mousePressEvent (event )
class ToolsTab (QWidget ):

    def __init__ (self ,parent =None ):
        super ().__init__ (parent )
        self .parent_window =parent 
        self .tool_icons =load_tool_icons ()
        self ._setup_ui ()
    def _setup_ui (self ):

        main_layout =QVBoxLayout (self )
        main_layout .setContentsMargins (10 ,10 ,10 ,10 )
        main_layout .setSpacing (15 )
        scroll =QScrollArea ()
        scroll .setWidgetResizable (True )
        scroll .setFrameShape (QFrame .NoFrame )
        content =QWidget ()
        content_layout =QHBoxLayout (content )
        content_layout .setSpacing (20 )
        left_frame =QFrame ()
        left_frame .setObjectName ("glass")
        left_layout =QVBoxLayout (left_frame )
        left_layout .setContentsMargins (15 ,15 ,15 ,15 )
        left_layout .setSpacing (10 )
        left_title =QLabel (t ('cat.converting')if t else 'Converting Tools')
        left_title .setProperty ("class","categoryTitle")
        left_title .setFont (QFont ("Segoe UI",14 ,QFont .Bold ))
        left_layout .addWidget (left_title )
        for idx ,key in enumerate (CONVERTING_TOOL_KEYS ):
            icon_path =self ._get_tool_icon_path (key )
            btn =ToolButton (t (key )if t else key ,t (key )if t else key ,icon_path )
            btn .clicked .connect (lambda i =idx :self ._run_converting_tool (i ))
            left_layout .addWidget (btn )
        left_layout .addStretch (1 )
        right_frame =QFrame ()
        right_frame .setObjectName ("glass")
        right_layout =QVBoxLayout (right_frame )
        right_layout .setContentsMargins (15 ,15 ,15 ,15 )
        right_layout .setSpacing (10 )
        right_title =QLabel (t ('cat.management')if t else 'Management Tools')
        right_title .setProperty ("class","categoryTitle")
        right_title .setFont (QFont ("Segoe UI",14 ,QFont .Bold ))
        right_layout .addWidget (right_title )
        for idx ,key in enumerate (MANAGEMENT_TOOL_KEYS ):
            icon_path =self ._get_tool_icon_path (key )
            btn =ToolButton (t (key )if t else key ,t (key )if t else key ,icon_path )
            btn .clicked .connect (lambda i =idx :self ._run_management_tool (i ))
            right_layout .addWidget (btn )
        right_layout .addStretch (1 )
        content_layout .addWidget (left_frame ,1 )
        content_layout .addWidget (right_frame ,1 )
        scroll .setWidget (content )
        main_layout .addWidget (scroll ,1 )
        note =QLabel (t ('notice.backup')if t else 'WARNING: ALWAYS BACKUP YOUR SAVES BEFORE USING THIS TOOL!')
        note .setAlignment (Qt .AlignCenter )
        note .setStyleSheet ("color: #FFD24D; padding: 10px;")
        main_layout .addWidget (note )
    def _get_tool_icon_path (self ,tool_key ):

        if tool_key in self .tool_icons :
            icon_name =self .tool_icons [tool_key ]
            icon_path =os .path .join (get_assets_path (),"data","icon",f"{icon_name }.ico")
            if os .path .exists (icon_path ):
                return icon_path 
        return None 
    def _import_and_call (self ,module_name ,function_name ,*args ):

        try :
            assets_path =get_assets_path ()
            if assets_path not in sys .path :
                sys .path .insert (0 ,assets_path )
            import importlib 
            module =importlib .import_module (module_name )
            func =getattr (module ,function_name )
            return func (*args )if args else func ()
        except Exception as e :
            print (f"Error importing/calling {module_name }.{function_name }: {e }")
            traceback .print_exc ()
            QMessageBox .critical (
            self ,
            t ('Error')if t else 'Error',
            f"Failed to run tool: {e }"
            )
            raise 
    def _run_converting_tool (self ,index ):

        try :
            dialog =None 
            if index ==0 :
                self ._import_and_call ("convert_level_location_finder","convert_level_location_finder","json")
            elif index ==1 :
                self ._import_and_call ("convert_level_location_finder","convert_level_location_finder","sav")
            elif index ==2 :
                self ._import_and_call ("convert_players_location_finder","convert_players_location_finder","json")
            elif index ==3 :
                self ._import_and_call ("convert_players_location_finder","convert_players_location_finder","sav")
            elif index ==4 :
                dialog =self ._import_and_call ("game_pass_save_fix","game_pass_save_fix")
            elif index ==5 :
                dialog =self ._import_and_call ("convertids","convert_steam_id")
            if dialog is not None :
                dialog .show ()
                if not hasattr (self ,'_active_dialogs'):
                    self ._active_dialogs =[]
                self ._active_dialogs .append (dialog )
        except Exception as e :
            print (f"Error running converting tool {index }: {e }")
    def _run_management_tool (self ,index ):

        try :
            dialog =None 
            if index ==0 :
                dialog =self ._import_and_call ("slot_injector","slot_injector")
            elif index ==1 :
                dialog =self ._import_and_call ("modify_save","modify_save")
            elif index ==2 :
                dialog =self ._import_and_call ("character_transfer","character_transfer")
            elif index ==3 :
                dialog =self ._import_and_call ("fix_host_save","fix_host_save")
            elif index ==4 :
                dialog =self ._import_and_call ("restore_map","restore_map")
            if dialog is not None :
                dialog .show ()
                if not hasattr (self ,'_active_dialogs'):
                    self ._active_dialogs =[]
                self ._active_dialogs .append (dialog )
        except Exception as e :
            print (f"Error running management tool {index }: {e }")
    def refresh (self ):

        pass 
