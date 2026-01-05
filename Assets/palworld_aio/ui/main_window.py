import os
import json
import webbrowser
import urllib .request
import re
import io
import sys
from functools import partial
from loguru import logger
from PySide6 .QtWidgets import (
QMainWindow ,QWidget ,QVBoxLayout ,QHBoxLayout ,QLabel ,
QPushButton ,QFrame ,QMenuBar ,QMenu ,QStatusBar ,
QSplitter ,QMessageBox ,QFileDialog ,QInputDialog ,QDialog ,QCheckBox ,QComboBox ,QApplication ,
QStackedWidget ,QTextEdit
)
from PySide6 .QtCore import Qt ,QTimer ,Signal ,QObject ,QPoint ,QPropertyAnimation ,QEasingCurve
from PySide6 .QtGui import QIcon ,QFont ,QAction ,QPixmap ,QCloseEvent ,QTextCursor
from i18n import t ,set_language ,load_resources
from common import get_versions
from import_libs import run_with_loading
from .tools_tab import center_on_parent
GITHUB_RAW_URL ="https://raw.githubusercontent.com/deafdudecomputers/PalworldSaveTools/main/Assets/common.py"
GITHUB_LATEST_ZIP ="https://github.com/deafdudecomputers/PalworldSaveTools/releases/latest"
try :
    from palworld_aio import constants 
    from palworld_aio .utils import check_for_update ,as_uuid 
    from palworld_aio .save_manager import save_manager 
    from palworld_aio .data_manager import get_guilds ,get_guild_members ,get_bases ,delete_guild ,delete_player ,load_exclusions ,save_exclusions ,delete_base_camp 
    from palworld_aio .func_manager import (
    delete_empty_guilds ,delete_inactive_players ,delete_inactive_bases ,
    delete_duplicated_players ,delete_unreferenced_data ,delete_non_base_map_objects ,
    delete_invalid_structure_map_objects ,delete_all_skins ,unlock_all_private_chests ,
    remove_invalid_items_from_save ,remove_invalid_pals_from_save ,fix_missions ,
    reset_anti_air_turrets ,reset_dungeons ,unlock_viewing_cage_for_player ,
    fix_all_negative_timestamps ,reset_selected_player_timestamp 
    )
    from palworld_aio .guild_manager import move_player_to_guild ,rebuild_all_guilds ,make_member_leader ,rename_guild ,max_guild_level 
    from palworld_aio .base_manager import export_base_json ,import_base_json ,clone_base_complete 
    from palworld_aio .player_manager import rename_player 
    from palworld_aio .map_generator import generate_world_map 
    from palworld_aio .dialogs import InputDialog ,DaysInputDialog ,PalDefenderDialog 
    from palworld_aio .widgets import SearchPanel ,StatsPanel 
except ImportError :
    from ..import constants 
    from ..utils import check_for_update ,as_uuid 
    from ..save_manager import save_manager 
    from ..data_manager import get_guilds ,get_guild_members ,get_bases ,delete_guild ,delete_player ,load_exclusions ,save_exclusions ,delete_base_camp 
    from ..func_manager import (
    delete_empty_guilds ,delete_inactive_players ,delete_inactive_bases ,
    delete_duplicated_players ,delete_unreferenced_data ,delete_non_base_map_objects ,
    delete_invalid_structure_map_objects ,delete_all_skins ,unlock_all_private_chests ,
    remove_invalid_items_from_save ,remove_invalid_pals_from_save ,fix_missions ,
    reset_anti_air_turrets ,reset_dungeons ,unlock_viewing_cage_for_player ,
    fix_all_negative_timestamps ,reset_selected_player_timestamp 
    )
    from ..guild_manager import move_player_to_guild ,rebuild_all_guilds ,make_member_leader ,rename_guild ,max_guild_level 
    from ..base_manager import export_base_json ,import_base_json ,clone_base_complete 
    from ..player_manager import rename_player 
    from ..map_generator import generate_world_map 
    from ..dialogs import InputDialog ,DaysInputDialog ,PalDefenderDialog 
from ..widgets import SearchPanel ,StatsPanel
class DetachedStatusWindow (QWidget ):
    def __init__ (self ,parent =None ):
        super ().__init__ ()
        self .parent =parent 
        self .setWindowFlags (Qt .Window |Qt .FramelessWindowHint |Qt .WindowStaysOnTopHint |Qt .Tool )
        self .setAttribute (Qt .WA_TranslucentBackground )
        self .setMinimumSize (600 ,400 )
        self ._drag_pos =QPoint ()
        self .is_dark =parent .is_dark_mode if parent else True 
        self ._load_theme ()
        self .main_layout =QVBoxLayout (self )
        self .container =QFrame ()
        self .container .setObjectName ("mainContainer")
        self .main_layout .addWidget (self .container )
        self .inner =QVBoxLayout (self .container )
        self .inner .setContentsMargins (10 ,5 ,10 ,10 )
        self .setup_status_ui ()
        self .setWindowOpacity (0.0 )
        self .show ()
        self .fade_animation =QPropertyAnimation (self ,b"windowOpacity")
        self .fade_animation .setDuration (400 )
        self .fade_animation .setStartValue (0.0 )
        self .fade_animation .setEndValue (1.0 )
        self .fade_animation .setEasingCurve (QEasingCurve .OutCubic )
        self .fade_animation .start ()
    def mousePressEvent (self ,event ):
        if event .button ()==Qt .LeftButton :
            self ._drag_pos =event .globalPosition ().toPoint ()-self .frameGeometry ().topLeft ()
            event .accept ()
    def mouseMoveEvent (self ,event ):
        if event .buttons ()==Qt .LeftButton :
            self .move (event .globalPosition ().toPoint ()-self ._drag_pos )
            event .accept ()
    def _load_theme (self ):
        base_path =constants .get_assets_path ()
        theme_file ='darkmode.qss'if self .is_dark else 'lightmode.qss'
        theme_path =os .path .join (base_path ,'data','gui',theme_file )
        if os .path .exists (theme_path ):
            try :
                with open (theme_path ,'r',encoding ='utf-8')as f :
                    qss_content =f .read ()
                    self .setStyleSheet (qss_content )
            except Exception as e :
                print (f"Failed to load theme {theme_file }: {e }")
                self ._apply_fallback_styles ()
        else :
            self ._apply_fallback_styles ()
    def _apply_fallback_styles (self ):
        if self .is_dark :
            bg_gradient ="qlineargradient(spread:pad, x1:0.0, y1:0.0, x2:1.0, y2:1.0, stop:0 #07080a, stop:0.5 #08101a, stop:1 #05060a)"
            glass_bg ="rgba(18,20,24,0.95)"
            glass_border ="rgba(255,255,255,0.08)"
            txt_color ="#dfeefc"
            accent_color ="#7DD3FC"
        else :
            bg_gradient ="qlineargradient(spread:pad, x1:0.0, y1:0.0, x2:1.0, y2:1.0, stop:0 #e6ecef, stop:0.5 #bdd5df, stop:1 #a7c9da)"
            glass_bg ="rgba(240,245,255,1.0)"
            glass_border ="rgba(180,200,220,0.5)"
            txt_color ="#000000"
            accent_color ="#1e3a8a"
        self .setStyleSheet (f"QWidget {{ background: {bg_gradient }; color: {txt_color }; font-family: 'Segoe UI', Roboto, Arial; }}")
        self .container .setStyleSheet (f"#mainContainer {{ background: {glass_bg }; border-radius: 10px; border: 1px solid {glass_border }; }}")
    def setup_status_ui (self ):
        head =QHBoxLayout ()
        txt_color ="#dfeefc"if self .is_dark else "#000000"
        title_label =QLabel ("Console")
        title_label .setStyleSheet (f"font-weight: bold; font-size: 14px; color: {txt_color};")
        head .addWidget (title_label )
        head .addStretch ()
        self .close_btn =QPushButton ("✕")
        self .close_btn .setFixedSize (40 ,40 )
        self .close_btn .clicked .connect (self .close )
        self .close_btn .setObjectName ("consoleCloseBtn")
        head .addWidget (self .close_btn )
        self .inner .addLayout (head )
        self .text_edit =QTextEdit ()
        self .text_edit .setReadOnly (True )
        self .text_edit .setObjectName ("consoleTextEdit")
        self .inner .addWidget (self .text_edit )
    def append_message (self ,text ):
        self .text_edit .append (text )
        document =self .text_edit .document ()
        if document .blockCount ()>500 :
            cursor =self .text_edit .textCursor ()
            cursor .movePosition (QTextCursor .Start )
            cursor .movePosition (QTextCursor .Down ,QTextCursor .KeepAnchor ,document .blockCount ()-500 )
            cursor .removeSelectedText ()
        cursor =self .text_edit .textCursor ()
        cursor .movePosition (QTextCursor .End )
        self .text_edit .setTextCursor (cursor )
    def closeEvent (self ,event ):
        if self .parent and hasattr (self .parent ,'status_stream'):
            self .parent .status_stream .detach_window =None
            self .parent .status_stream .detached =False
            self .parent .status_stream .detach_state_changed .emit (False )
        event .accept ()
class StatusBarStream (QObject ):
    text_written =Signal (str )
    detach_state_changed =Signal (bool )
    def __init__ (self ,status_bar ,parent =None ):
        QObject .__init__ (self )
        self .status_bar =status_bar
        self .parent =parent 
        self .stringio =io .StringIO ()
        self .detached =False 
        self .detach_window =None 
        self .text_written .connect (self ._handle_text )
    def _handle_text (self ,text ):
        if self .detached and self .detach_window :
            self .detach_window .append_message (text )
        else :
            self .status_bar .showMessage (text )
    def write (self ,text ):
        self .stringio .write (text )
        if text .strip ():
            self .text_written .emit (text .strip ())
    def flush (self ):
        pass
    def detach (self ):
        if not self .detached :
            self .detached =True 
            self .detach_window =DetachedStatusWindow (self .parent )
            self .detach_window .setWindowOpacity (0.0 )
            self .detach_window .show ()
            # Add fade-in animation
            self .detach_window .fade_animation =QPropertyAnimation (self .detach_window ,b"windowOpacity")
            self .detach_window .fade_animation .setDuration (300 )
            self .detach_window .fade_animation .setStartValue (0.0 )
            self .detach_window .fade_animation .setEndValue (1.0 )
            self .detach_window .fade_animation .setEasingCurve (QEasingCurve .InOutQuad )
            self .detach_window .fade_animation .start ()
            self .detach_state_changed .emit (True )
    def attach (self ):
        if self .detached :
            self .detached =False
            self .detach_state_changed .emit (False )
            if self .detach_window :
                self .detach_window .close ()
                self .detach_window =None
    def __getattr__ (self ,name ):
        return getattr (self .stringio ,name )
class MainWindow (QMainWindow ):
    def __init__ (self ):
        super ().__init__ ()
        self .is_dark_mode =True 
        self .user_settings ={}
        self .lang_map ={
        "English":"en_US",
        "中文":"zh_CN",
        "Русский":"ru_RU",
        "Français":"fr_FR",
        "Español":"es_ES",
        "Deutsch":"de_DE",
        "日本語":"ja_JP",
        "한국어":"ko_KR"
        }
        load_exclusions ()
        self ._load_user_settings ()
        self ._setup_ui ()
        self ._load_theme ()
        self ._setup_menus ()
        self ._setup_connections ()
        self ._check_update ()
        # Start zombie process monitor at app launch
        try :
            from common import unlock_self_folder
            unlock_self_folder ()
        except Exception :
            pass
        # Redirect print statements to status bar
        self .status_stream =StatusBarStream (self .status_bar ,self )
        self .status_stream .detach_state_changed .connect (self ._on_detach_state_changed )
        sys .stdout =self .status_stream
        sys .stderr =self .status_stream
        # Redirect loguru logging to status bar
        logger .add (self .status_stream ,level ="INFO",format ="{message}")
    def _setup_ui (self ):
        self .setWindowTitle (t ('deletion.title')if t else 'All-in-One Tools')
        self .setMinimumSize (1400 ,800 )
        self .resize (1400 ,800 )
        self .setWindowFlags (Qt .FramelessWindowHint )
        if os .path .exists (constants .ICON_PATH ):
            self .setWindowIcon (QIcon (constants .ICON_PATH ))
        central_widget =QWidget ()
        central_widget .setObjectName ("central")
        self .setCentralWidget (central_widget )
        main_layout =QVBoxLayout (central_widget )
        main_layout .setContentsMargins (0 ,0 ,0 ,0 )
        main_layout .setSpacing (0 )
        from .header_widget import HeaderWidget 
        self .header_widget =HeaderWidget ()
        self .header_widget .set_theme (self .is_dark_mode )
        self .header_widget .minimize_clicked .connect (self .showMinimized )
        self .header_widget .maximize_clicked .connect (self ._toggle_maximize )
        self .header_widget .close_clicked .connect (self .close )
        self .header_widget .theme_toggle_clicked .connect (self ._toggle_theme )
        self .header_widget .about_clicked .connect (self ._show_about )
        self .header_widget .warn_btn .clicked .connect (self ._show_warnings )
        self .header_widget .show_warning (True )
        main_layout .addWidget (self .header_widget )
        self ._dashboard_collapsed =False 
        self ._dashboard_sizes =[1000 ,400 ]
        from .custom_tab_bar import TabBarContainer 
        self .tab_bar_container =TabBarContainer ()
        self .tab_bar =self .tab_bar_container .tab_bar 
        self .tab_bar .currentChanged .connect (self ._on_tab_changed )
        self .tab_bar_container .sidebar_toggle_clicked .connect (self ._toggle_dashboard )
        main_layout .addWidget (self .tab_bar_container )
        self .splitter =QSplitter (Qt .Horizontal )
        self .splitter .setChildrenCollapsible (False )
        self .stacked_widget =QStackedWidget ()
        self ._setup_tools_tab ()
        self ._setup_players_tab ()
        self ._setup_guilds_tab ()
        self ._setup_bases_tab ()
        self ._setup_map_tab ()
        self ._setup_exclusions_tab ()
        self .splitter .addWidget (self .stacked_widget )
        from .results_widget import ResultsWidget 
        self .results_widget =ResultsWidget ()
        self .splitter .addWidget (self .results_widget )
        total_width =self .width ()
        tab_width =int (total_width *0.75 )
        results_width =int (total_width *0.25 )
        self .splitter .setSizes ([tab_width ,results_width ])
        self .splitter .setStretchFactor (0 ,1 )
        self .splitter .setStretchFactor (1 ,1 )
        main_layout .addWidget (self .splitter ,stretch =1 )
        self .status_bar =QStatusBar ()
        self .status_bar .setMinimumHeight (35 )
        self .setStatusBar (self .status_bar )
        self .status_bar .showMessage (t ('status.ready')if t else 'Ready')
        detach_btn =QPushButton ("Detach")
        detach_btn .setObjectName ("detachButton")
        detach_btn .setFixedSize (60 ,20 )
        detach_btn .setStyleSheet ("font-size: 10px;")
        detach_btn .clicked .connect (self ._detach_status )
        self .status_bar .addPermanentWidget (detach_btn )
    def _setup_players_tab (self ):
        players_tab =QWidget ()
        layout =QVBoxLayout (players_tab )
        layout .setContentsMargins (10 ,10 ,10 ,10 )
        self .players_panel =SearchPanel (
        'deletion.search_players',
        ['deletion.col.player_name','deletion.col.last_seen','deletion.col.level',
        'deletion.col.pals','deletion.col.uid','deletion.col.guild_name','deletion.col.guild_id','deletion.col.guild_level'],
        [140 ,120 ,60 ,60 ,150 ,180 ,180 ,60 ]
        )
        self .players_panel .item_selected .connect (self ._on_player_selected )
        self .players_panel .tree .customContextMenuRequested .connect (self ._show_player_context_menu )
        layout .addWidget (self .players_panel )
        self .tab_bar .addTab (t ('deletion.search_players')if t else 'Players')
        self .stacked_widget .addWidget (players_tab )
    def _setup_guilds_tab (self ):
        guilds_tab =QWidget ()
        layout =QVBoxLayout (guilds_tab )
        layout .setContentsMargins (10 ,10 ,10 ,10 )
        splitter =QSplitter (Qt .Vertical )
        self .guilds_panel =SearchPanel (
        'deletion.search_guilds',
        ['deletion.col.guild_name','deletion.col.guild_id','deletion.col.guild_level'],
        [200 ,300 ,60 ]
        )
        self .guilds_panel .item_selected .connect (self ._on_guild_selected )
        self .guilds_panel .tree .customContextMenuRequested .connect (self ._show_guild_context_menu )
        splitter .addWidget (self .guilds_panel )
        self .guild_members_panel =SearchPanel (
        'deletion.guild_members',
        ['deletion.col.member','deletion.col.last_seen','deletion.col.level',
        'deletion.col.pals','deletion.col.uid'],
        [200 ,120 ,60 ,100 ,300 ]
        )
        self .guild_members_panel .item_selected .connect (self ._on_guild_member_selected )
        self .guild_members_panel .tree .customContextMenuRequested .connect (self ._show_guild_member_context_menu )
        splitter .addWidget (self .guild_members_panel )
        layout .addWidget (splitter )
        self .tab_bar .addTab (t ('deletion.search_guilds')if t else 'Guilds')
        self .stacked_widget .addWidget (guilds_tab )
    def _setup_bases_tab (self ):
        bases_tab =QWidget ()
        layout =QVBoxLayout (bases_tab )
        layout .setContentsMargins (10 ,10 ,10 ,10 )
        self .bases_panel =SearchPanel (
        'deletion.search_bases',
        ['deletion.col.base_id','deletion.col.guild_id','deletion.col.guild_name','deletion.col.guild_level'],
        [200 ,200 ,200 ,100 ]
        )
        self .bases_panel .item_selected .connect (self ._on_base_selected )
        self .bases_panel .tree .customContextMenuRequested .connect (self ._show_base_context_menu )
        layout .addWidget (self .bases_panel )
        self .tab_bar .addTab (t ('deletion.search_bases')if t else 'Bases')
        self .stacked_widget .addWidget (bases_tab )
    def _setup_map_tab (self ):
        from .map_tab import MapTab 
        self .map_tab =MapTab (self )
        self .tab_bar .addTab (t ('map.viewer')if t else 'Map')
        self .stacked_widget .addWidget (self .map_tab )
    def _setup_tools_tab (self ):
        from .tools_tab import ToolsTab 
        self .tools_tab =ToolsTab (self )
        self .tab_bar .addTab (t ('tools_tab')if t else 'Tools')
        self .stacked_widget .addWidget (self .tools_tab )
    def _setup_exclusions_tab (self ):
        exclusions_tab =QWidget ()
        layout =QHBoxLayout (exclusions_tab )
        layout .setContentsMargins (10 ,10 ,10 ,10 )
        layout .setSpacing (10 )
        self .excl_players_panel =SearchPanel (
        'deletion.exclusions.player_label',
        ['deletion.excluded_player_uid'],
        [300 ]
        )
        self .excl_players_panel .tree .customContextMenuRequested .connect (
        lambda pos :self ._show_exclusion_context_menu (pos ,'players'))
        layout .addWidget (self .excl_players_panel )
        self .excl_guilds_panel =SearchPanel (
        'deletion.exclusions.guild_label',
        ['deletion.excluded_guild_id'],
        [300 ]
        )
        self .excl_guilds_panel .tree .customContextMenuRequested .connect (
        lambda pos :self ._show_exclusion_context_menu (pos ,'guilds'))
        layout .addWidget (self .excl_guilds_panel )
        self .excl_bases_panel =SearchPanel (
        'deletion.exclusions.base_label',
        ['deletion.excluded_bases'],
        [300 ]
        )
        self .excl_bases_panel .tree .customContextMenuRequested .connect (
        lambda pos :self ._show_exclusion_context_menu (pos ,'bases'))
        layout .addWidget (self .excl_bases_panel )
        self .tab_bar .addTab (t ('deletion.menu.exclusions')if t else 'Exclusions')
        self .stacked_widget .addWidget (exclusions_tab )
    def _setup_menus (self ):
        menu_actions ={
        'file':[
        (t ('menu.file.load_save')if t else 'Load Save',self ._load_save ),
        (t ('menu.file.save_changes')if t else 'Save Changes',self ._save_changes ),
        (t ('menu.file.rename_world')if t else 'Rename World',self ._rename_world ),
        ],
        'functions':[
        (t ('deletion.menu.delete_empty_guilds')if t else 'Delete Empty Guilds',self ._delete_empty_guilds ),
        (t ('deletion.menu.delete_inactive_bases')if t else 'Delete Inactive Bases',self ._delete_inactive_bases ),
        (t ('deletion.menu.delete_duplicate_players')if t else 'Delete Duplicate Players',self ._delete_duplicate_players ),
        (t ('deletion.menu.delete_inactive_players')if t else 'Delete Inactive Players',self ._delete_inactive_players ),
        (t ('deletion.menu.delete_unreferenced')if t else 'Delete Unreferenced Data',self ._delete_unreferenced ),
        (t ('deletion.menu.delete_non_base_map_objs')if t else 'Delete Non-Base Map Objects',self ._delete_non_base_map_objs ),
        (t ('deletion.menu.delete_all_skins')if t else 'Delete All Skins',self ._delete_all_skins ),
        (t ('deletion.menu.unlock_private_chests')if t else 'Unlock Private Chests',self ._unlock_private_chests ),
        (t ('deletion.menu.remove_invalid_items')if t else 'Remove Invalid Items',self ._remove_invalid_items ),
        (t ('deletion.menu.remove_invalid_structures')if t else 'Remove Invalid Structures',self ._remove_invalid_structures ),
        (t ('deletion.menu.remove_invalid_pals')if t else 'Remove Invalid Pals',self ._remove_invalid_pals ),
        (t ('deletion.menu.reset_missions')if t else 'Reset Missions',self ._reset_missions ),
        (t ('deletion.menu.reset_anti_air')if t else 'Reset Anti-Air Turrets',self ._reset_anti_air ),
        (t ('deletion.menu.reset_dungeons')if t else 'Reset Dungeons',self ._reset_dungeons ),
        (t ('deletion.menu.paldefender')if t else 'PalDefender Commands',self ._open_paldefender ,'separator_after'),
        (t ('deletion.menu.fix_timestamps')if t else 'Fix All Negative Timestamps',self ._fix_all_timestamps ,'separator_after'),
        (t ('base.export_all')if t else 'Export All Bases',self ._export_all_bases ),
        (t ('guild.menu.rebuild_all_guilds')if t else 'Rebuild All Guilds',self ._rebuild_all_guilds ),
        (t ('guild.menu.move_selected_player_to_selected_guild')if t else 'Move Player to Guild',self ._move_player_to_guild ),
        ],
        'maps':[
        (t ('deletion.menu.show_map')if t else 'Show Map',self ._show_map ),
        (t ('deletion.menu.generate_map')if t else 'Generate Map',self ._generate_map ),
        ],
        'exclusions':[
        (t ('deletion.menu.save_exclusions')if t else 'Save Exclusions',self ._save_exclusions ),
        ],
        'languages':[
        (t (f'lang.{code }')if t else code ,partial (self ._change_language ,code ),{
        'en_US':'🇺🇸',
        'zh_CN':'🇨🇳',
        'ru_RU':'🇷🇺',
        'fr_FR':'🇫🇷',
        'es_ES':'🇪🇸',
        'de_DE':'🇩🇪',
        'ja_JP':'🇯🇵',
        'ko_KR':'🇰🇷'
        }[code ])
        for code in ['en_US','zh_CN','ru_RU','fr_FR','es_ES','de_DE','ja_JP','ko_KR']
        ],
        }
        self .header_widget .set_menu_actions (menu_actions )
    def _create_action (self ,text ,callback ):
        action =QAction (text ,self )
        action .triggered .connect (callback )
        return action 
    def _setup_connections (self ):
        save_manager .load_finished .connect (self ._on_load_finished )
        save_manager .save_finished .connect (self ._on_save_finished )
    def _on_tab_changed (self ,index ):
        self .stacked_widget .setCurrentIndex (index )
    def _load_user_settings (self ):
        base_path =constants .get_assets_path ()
        user_cfg_path =os .path .join (base_path ,'data','configs','user.cfg')
        default_settings ={
        "theme":"dark",
        "language":"en_US",
        "show_icons":True ,
        "boot_preference":"menu"
        }
        if os .path .exists (user_cfg_path ):
            try :
                with open (user_cfg_path ,'r')as f :
                    self .user_settings =json .load (f )
                    for key ,value in default_settings .items ():
                        if key not in self .user_settings :
                            self .user_settings [key ]=value 
                    self .is_dark_mode =self .user_settings .get ('theme','dark')=='dark'
            except Exception as e :
                print (f"Failed to load user settings: {e }")
                self .user_settings =default_settings .copy ()
                self .is_dark_mode =True 
        else :
            self .user_settings =default_settings .copy ()
            self .is_dark_mode =True 
            os .makedirs (os .path .dirname (user_cfg_path ),exist_ok =True )
            self ._save_user_settings ()
    def _save_user_settings (self ):
        base_path =constants .get_assets_path ()
        user_cfg_path =os .path .join (base_path ,'data','configs','user.cfg')
        try :
            os .makedirs (os .path .dirname (user_cfg_path ),exist_ok =True )
            with open (user_cfg_path ,'w')as f :
                json .dump (self .user_settings ,f ,indent =2 )
        except Exception as e :
            print (f"Failed to save user settings: {e }")
    def _load_theme (self ):
        base_path =constants .get_assets_path ()
        theme_file ='darkmode.qss'if self .is_dark_mode else 'lightmode.qss'
        theme_path =os .path .join (base_path ,'data','gui',theme_file )
        if os .path .exists (theme_path ):
            try :
                with open (theme_path ,'r',encoding ='utf-8')as f :
                    qss_content =f .read ()
                    self .setStyleSheet (qss_content )
            except Exception as e :
                print (f"Failed to load theme {theme_file }: {e }")
                self ._apply_fallback_styles ()
        else :
            print (f"Theme file not found: {theme_path }")
            self ._apply_fallback_styles ()
    def _apply_fallback_styles (self ):
        border_color = "rgba(70,70,70,1.0)" if self.is_dark_mode else "rgba(70,70,70,1.0)"
        self .setStyleSheet (f"""
            QMainWindow {{
                background-color: {constants .BG };
            }}
            QWidget {{
                color: {constants .TEXT };
            }}
            QTabWidget::pane {{
                background-color: {constants .GLASS };
                border: 1px solid {border_color };
                border-radius: 4px;
            }}
            QTabBar::tab {{
                background-color: {constants .GLASS };
                color: {constants .TEXT };
                padding: 8px 16px;
                border: 1px solid {border_color };
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }}
            QTabBar::tab:selected {{
                background-color: {constants .ACCENT };
            }}
            QTabBar::tab:hover {{
                background-color: {constants .BUTTON_HOVER };
            }}
            QPushButton {{
                background-color: {constants .GLASS };
                color: {constants .TEXT };
                border: 1px solid {border_color };
                border-radius: 4px;
                padding: 6px 12px;
            }}
            QPushButton:hover {{
                background-color: {constants .BUTTON_HOVER };
            }}
            QMenuBar {{
                background-color: {constants .GLASS };
                color: {constants .TEXT };
            }}
            QMenuBar::item:selected {{
                background-color: {constants .ACCENT };
            }}
            QMenu {{
                background-color: {constants .GLASS };
                color: {constants .TEXT };
                border: 1px solid {border_color };
            }}
            QMenu::item:selected {{
                background-color: {constants .ACCENT };
            }}
        """)
    def _toggle_theme (self ):
        self .is_dark_mode =not self .is_dark_mode 
        self .user_settings ['theme']='dark'if self .is_dark_mode else 'light'
        self ._save_user_settings ()
        self ._load_theme ()
        if hasattr (self ,'header_widget'):
            self .header_widget .set_theme (self .is_dark_mode )
        if hasattr (self ,'tab_bar_container'):
            self .tab_bar_container .set_theme (self .is_dark_mode )
    def _toggle_dashboard (self ):
        if self ._dashboard_collapsed :
            self .results_widget .show ()
            self .splitter .setSizes (self ._dashboard_sizes )
            self ._dashboard_collapsed =False 
        else :
            self ._dashboard_sizes =self .splitter .sizes ()
            self .results_widget .hide ()
            self ._dashboard_collapsed =True 
        self .tab_bar_container .set_sidebar_collapsed (self ._dashboard_collapsed )
    def _toggle_maximize (self ):
        if self .isMaximized ():
            self .showNormal ()
        else :
            self .showMaximized ()
    def _detach_status (self ):
        if self .status_stream :
            if self .status_stream .detached :
                self .status_stream .attach ()
            else :
                self .status_stream .detach ()
    def _on_detach_state_changed (self ,detached ):
        detach_btn =self .status_bar .findChild (QPushButton )
        if detach_btn :
            detach_btn .setText ("Reattach"if detached else "Detach")
    def check_github_update (self ,force_test =False ):
        try :
            r =urllib .request .urlopen (GITHUB_RAW_URL ,timeout =5 )
            content =r .read ().decode ("utf-8")
            match =re .search (r'APP_VERSION\s*=\s*"([^"]+)"',content )
            latest =match .group (1 )if match else None 
            local ,_ =get_versions ()
            if force_test :
                local ="0.0.1"
            if latest :
                try :
                    local_tuple =tuple (int (x )for x in local .split ("."))
                    latest_tuple =tuple (int (x )for x in latest .split ("."))
                except Exception :
                    local_tuple =(0 ,)
                    latest_tuple =(0 ,)
                if local_tuple >=latest_tuple :
                    return True ,latest 
                return False ,latest 
            return True ,None 
        except Exception :
            return True ,None 
    def _check_update (self ):
        try :
            ok ,latest =self .check_github_update (force_test =False )
            if not ok and latest :
                tools_version ,_ =get_versions ()
                self .header_widget .start_pulse_animation (latest )
                self .header_widget .update_version_text (tools_version ,latest )
                self .status_bar .showMessage (
                f"{t ('update.current')if t else 'Current'}: {tools_version } | {t ('update.latest')if t else 'Latest'}: {latest } - Click version chip to update",
                0 
                )
        except Exception :
            pass 
    def _on_load_finished (self ,success ):
        if success :
            self .refresh_all ()
            self .results_widget .refresh_stats_before ()
            self .status_bar .showMessage (t ('status.loaded')if t else 'Save loaded successfully',5000 )
            msg_box =QMessageBox (self )
            msg_box .setWindowTitle (t ('success.title'))
            msg_box .setText (t ('save.loaded'))
            msg_box .setIcon (QMessageBox .Information )
            msg_box .addButton (t ('button.ok'),QMessageBox .AcceptRole )
            msg_box .exec ()
        else :
            self .status_bar .showMessage (t ('status.load_failed')if t else 'Failed to load save',5000 )
            msg_box =QMessageBox (self )
            msg_box .setWindowTitle (t ('error.title'))
            msg_box .setText (t ('save.load_failed'))
            msg_box .setIcon (QMessageBox .Critical )
            msg_box .addButton (t ('button.ok'),QMessageBox .AcceptRole )
            msg_box .exec ()
    def _on_save_finished (self ,duration ):
        self .status_bar .showMessage (f"{t ('status.saved')if t else 'Save completed'} ({duration :.2f}s)",5000 )
        msg_box =QMessageBox (self )
        msg_box .setWindowTitle (t ('success.title'))
        msg_box .setText (t ('save.complete'))
        msg_box .setIcon (QMessageBox .Information )
        msg_box .addButton (t ('button.ok'),QMessageBox .AcceptRole )
        msg_box .exec ()
    def refresh_all (self ):
        self ._refresh_players ()
        self ._refresh_guilds ()
        self ._refresh_bases ()
        self ._refresh_map ()
        self ._refresh_exclusions ()
        self .results_widget .refresh_stats_after ()
    def _refresh_stats (self ):
        stats =save_manager .get_current_stats ()
        self .results_widget .update_stats (stats )
    def _refresh_players (self ):
        self .players_panel .clear ()
        players =save_manager .get_players ()
        for uid ,name ,gid ,lastseen ,level in players :
            pals =constants .PLAYER_PAL_COUNTS .get (uid .replace ('-','').lower (),0 )
            gname =save_manager .get_guild_name_by_id (gid )
            glevel =save_manager .get_guild_level_by_id (gid )
            is_leader =save_manager .is_player_guild_leader (gid ,uid )
            display_name =f'[L] {name }'if is_leader else name 
            self .players_panel .add_item ([display_name ,lastseen ,level ,pals ,uid ,gname ,gid ,glevel ])
    def _refresh_guilds (self ):
        self .guilds_panel .clear ()
        self .guild_members_panel .clear ()
        guilds =get_guilds ()
        for g in guilds :
            self .guilds_panel .add_item ([g ['name'],g ['id'],g ['level']])
    def _refresh_bases (self ):
        self .bases_panel .clear ()
        bases =get_bases ()
        for b in bases :
            glevel =save_manager .get_guild_level_by_id (b ['guild_id'])
            self .bases_panel .add_item ([b ['id'],b ['guild_id'],b ['guild_name'],glevel ])
    def _refresh_map (self ):
        if hasattr (self ,'map_tab'):
            self .map_tab .refresh ()
    def _refresh_exclusions (self ):
        self .excl_players_panel .clear ()
        for uid in constants .exclusions .get ('players',[]):
            self .excl_players_panel .add_item ([uid ])
        self .excl_guilds_panel .clear ()
        for gid in constants .exclusions .get ('guilds',[]):
            self .excl_guilds_panel .add_item ([gid ])
        self .excl_bases_panel .clear ()
        for bid in constants .exclusions .get ('bases',[]):
            self .excl_bases_panel .add_item ([bid ])
    def mousePressEvent (self ,event ):
        if event .button ()==Qt .LeftButton :
            if hasattr (self ,'header_widget')and self .header_widget .underMouse ():
                self .drag_position =event .globalPosition ().toPoint ()-self .frameGeometry ().topLeft ()
                event .accept ()
            else :
                super ().mousePressEvent (event )
        else :
            super ().mousePressEvent (event )
    def mouseMoveEvent (self ,event ):
        if event .buttons ()==Qt .LeftButton and hasattr (self ,'drag_position'):
            self .move (event .globalPosition ().toPoint ()-self .drag_position )
            event .accept ()
        else :
            super ().mouseMoveEvent (event )
    def mouseReleaseEvent (self ,event ):
        if hasattr (self ,'drag_position'):
            delattr (self ,'drag_position')
        super ().mouseReleaseEvent (event )
    def _show_warnings (self ):
        warnings =[
        (t ("notice.backup")if t else "WARNING: ALWAYS BACKUP YOUR SAVES BEFORE USING THESE TOOLS!",{}),
        (t ("notice.patch",game_version =get_versions ()[1 ])if t else "MAKE SURE TO UPDATE YOUR SAVES AFTER EVERY GAME PATCH!",{}),
        (t ("notice.errors")if t else "IF YOU DO NOT UPDATE YOUR SAVES AFTER A PATCH, YOU MAY ENCOUNTER ERRORS!",{})
        ]
        combined ="\n\n".join (w for w ,_ in warnings if w )
        if not combined :
            combined =t ("notice.none")if t else "No warnings."
        QMessageBox .warning (
        self ,
        t ("PalworldSaveTools")if t else "Palworld Save Tools",
        combined 
        )
    def _show_about (self ):
        tools_version ,game_version =get_versions ()
        h2_color ="#4a90e2"if self .is_dark_mode else "#1a5fb4"
        text_color ="#e0e0e0"if self .is_dark_mode else "#333"
        sub_color ="#888"if self .is_dark_mode else "#666"
        about_text =f"""<h2 style="color: {h2_color };">{t ('about.title')if t else 'Palworld Save Tools'} v{tools_version }</h2>
    <p style="color: {text_color };">{t ('about.description')if t else 'A comprehensive toolkit for managing Palworld save files.'}</p>
    <p style="color: {text_color };"><b>{t ('about.features.label')if t else 'Features'}:</b></p>
    <ul>
    <li style="color: {text_color };">{t ('about.features.1')if t else 'Transfer saves between servers and co-op worlds'}</li>
    <li style="color: {text_color };">{t ('about.features.2')if t else 'Fix host saves and manage player/guild data'}</li>
    <li style="color: {text_color };">{t ('about.features.3')if t else 'Edit bases and manage save files'}</li>
    <li style="color: {text_color };">{t ('about.features.4')if t else 'Convert between Steam and GamePass formats'}</li>
    <li style="color: {text_color };">{t ('about.features.5')if t else 'Visualize and manage world maps'}</li>
    </ul>
    <p style="color: {text_color };"><b>{t ('about.game_version')if t else 'Game Version'}:</b> {game_version }</p>
    <p style="color: {text_color };"><b>{t ('about.developer')if t else 'Developer'}:</b> Palworld Save Tools Team</p>
    <p style="color: {text_color };"><b>GitHub:</b> <a href="{GITHUB_LATEST_ZIP }" style="color: {h2_color };">{t ('about.github')if t else 'View on GitHub'}</a></p>
    <p style="color: {sub_color };">© 2025 Palworld Save Tools</p>"""
        msg_box =QMessageBox (self )
        msg_box .setWindowTitle (t ("About PST")if t else "About PST")
        msg_box .setTextFormat (Qt .RichText )
        msg_box .setText (about_text )
        msg_box .setStandardButtons (QMessageBox .Ok )
        msg_box .setIcon (QMessageBox .Information )
        center_on_parent (msg_box )
        msg_box .exec ()
    def _on_player_selected (self ,data ):
        if data :
            self .results_widget .set_player (data [0 ])
            self .results_widget .set_guild (data [5 ])
    def _on_guild_selected (self ,data ):
        if data :
            self .results_widget .set_guild (data [0 ])
            self .guild_members_panel .clear ()
            members =get_guild_members (data [1 ])
            for m in members :
                prefix ='[L] 'if m ['is_leader']else ''
                self .guild_members_panel .add_item ([
                prefix +m ['name'],m ['lastseen'],m ['level'],m ['pals'],m ['uid']
                ])
    def _on_guild_member_selected (self ,data ):
        if data :
            name =data [0 ].replace ('[L] ','')
            self .results_widget .set_player (name )
    def _on_base_selected (self ,data ):
        if data :
            self .results_widget .set_base (data [0 ])
            self .results_widget .set_guild (data [2 ])
    def closeEvent (self ,event :QCloseEvent ):
        boot_preference =self .user_settings .get ("boot_preference","menu")
        if boot_preference =="palworld_aio":
            QApplication .quit ()
            event .accept ()
        else :
            event .accept ()
    def _show_player_context_menu (self ,pos ):
        item =self .players_panel .tree .itemAt (pos )
        if not item :
            return 
        menu =QMenu (self )
        menu .addAction (self ._create_action (t ('deletion.ctx.add_exclusion'),lambda :self ._add_exclusion ('players',item .text (4 ))))
        menu .addAction (self ._create_action (t ('deletion.ctx.remove_exclusion'),lambda :self ._remove_exclusion ('players',item .text (4 ))))
        menu .addAction (self ._create_action (t ('deletion.ctx.delete_player'),lambda :self ._delete_player (item .text (4 ))))
        menu .addAction (self ._create_action (t ('player.rename.menu'),lambda :self ._rename_player (item .text (4 ),item .text (0 ))))
        menu .addAction (self ._create_action (t ('player.viewing_cage.menu'),lambda :self ._unlock_viewing_cage (item .text (4 ))))
        menu .addAction (self ._create_action (t ('player.reset_timestamp.menu')if t else 'Reset Timestamp',lambda :self ._reset_player_timestamp (item .text (4 ))))
        menu .addSeparator ()
        menu .addAction (self ._create_action (t ('guild.ctx.make_leader'),lambda :self ._make_leader (item .text (6 ),item .text (4 ))))
        menu .addAction (self ._create_action (t ('deletion.ctx.delete_guild'),lambda :self ._delete_guild (item .text (6 ))))
        menu .addAction (self ._create_action (t ('guild.rename.menu'),lambda :self ._rename_guild_action (item .text (6 ),item .text (5 ))))
        menu .addAction (self ._create_action (t ('guild.menu.max_level'),lambda :self ._max_guild_level (item .text (6 ))))
        menu .addAction (self ._create_action (t ('button.import'),lambda :self ._import_base_to_guild (item .text (6 ))))
        menu .exec (self .players_panel .tree .viewport ().mapToGlobal (pos ))
    def _show_guild_context_menu (self ,pos ):
        item =self .guilds_panel .tree .itemAt (pos )
        if not item :
            return 
        menu =QMenu (self )
        menu .addAction (self ._create_action (t ('deletion.ctx.add_exclusion'),lambda :self ._add_exclusion ('guilds',item .text (1 ))))
        menu .addAction (self ._create_action (t ('deletion.ctx.remove_exclusion'),lambda :self ._remove_exclusion ('guilds',item .text (1 ))))
        menu .addAction (self ._create_action (t ('deletion.ctx.delete_guild'),lambda :self ._delete_guild (item .text (1 ))))
        menu .addAction (self ._create_action (t ('guild.rename.menu'),lambda :self ._rename_guild_action (item .text (1 ),item .text (0 ))))
        menu .addAction (self ._create_action (t ('guild.menu.max_level'),lambda :self ._max_guild_level (item .text (1 ))))
        menu .addSeparator ()
        menu .addAction (self ._create_action (t ('base.export_guild'),lambda :self ._export_bases_for_guild (item .text (1 ))))
        menu .addAction (self ._create_action (t ('base.import_multi'),lambda :self ._import_base_to_guild (item .text (1 ))))
        menu .addAction (self ._create_action (t ('guild.menu.move_selected_player_to_selected_guild'),self ._move_player_to_guild ))
        menu .exec (self .guilds_panel .tree .viewport ().mapToGlobal (pos ))
    def _show_guild_member_context_menu (self ,pos ):
        item =self .guild_members_panel .tree .itemAt (pos )
        if not item :
            return 
        guild_data =self .guilds_panel .get_selected_data ()
        if not guild_data :
            return 
        menu =QMenu (self )
        menu .addAction (self ._create_action (t ('guild.ctx.make_leader'),lambda :self ._make_leader (guild_data [1 ],item .text (4 ))))
        menu .addAction (self ._create_action (t ('deletion.ctx.add_exclusion'),lambda :self ._add_exclusion ('players',item .text (4 ))))
        menu .addAction (self ._create_action (t ('deletion.ctx.remove_exclusion'),lambda :self ._remove_exclusion ('players',item .text (4 ))))
        menu .addAction (self ._create_action (t ('deletion.ctx.delete_player'),lambda :self ._delete_player (item .text (4 ))))
        menu .addAction (self ._create_action (t ('player.rename.menu'),lambda :self ._rename_player (item .text (4 ),item .text (0 ).replace ('[L] ',''))))
        menu .addAction (self ._create_action (t ('player.reset_timestamp.menu')if t else 'Reset Timestamp',lambda :self ._reset_player_timestamp (item .text (4 ))))
        menu .exec (self .guild_members_panel .tree .viewport ().mapToGlobal (pos ))
    def _show_base_context_menu (self ,pos ):
        item =self .bases_panel .tree .itemAt (pos )
        if not item :
            return 
        menu =QMenu (self )
        menu .addAction (self ._create_action (t ('deletion.ctx.add_exclusion'),lambda :self ._add_exclusion ('bases',item .text (0 ))))
        menu .addAction (self ._create_action (t ('deletion.ctx.remove_exclusion'),lambda :self ._remove_exclusion ('bases',item .text (0 ))))
        menu .addAction (self ._create_action (t ('deletion.ctx.delete_base'),lambda :self ._delete_base (item .text (0 ),item .text (1 ))))
        menu .addAction (self ._create_action (t ('guild.rename.menu'),lambda :self ._rename_guild_action (item .text (1 ),item .text (2 ))))
        menu .addAction (self ._create_action (t ('guild.menu.max_level'),lambda :self ._max_guild_level (item .text (1 ))))
        menu .addAction (self ._create_action (t ('export.base'),lambda :self ._export_base (item .text (0 ))))
        menu .addAction (self ._create_action (t ('import.base'),lambda :self ._import_base (item .text (1 ))))
        menu .addAction (self ._create_action (t ('clone.base'),lambda :self ._clone_base (item .text (0 ),item .text (1 ))))
        menu .exec (self .bases_panel .tree .viewport ().mapToGlobal (pos ))
    def _show_exclusion_context_menu (self ,pos ,excl_type ):
        panel =getattr (self ,f'excl_{excl_type }_panel')
        item =panel .tree .itemAt (pos )
        if not item :
            return 
        menu =QMenu (self )
        menu .addAction (self ._create_action (t ('deletion.ctx.remove_exclusion'),lambda :self ._remove_exclusion (excl_type ,item .text (0 ))))
        menu .exec (panel .tree .viewport ().mapToGlobal (pos ))
    def _load_save (self ):
        if constants .loaded_level_json is not None :
            constants .loaded_level_json =None 
            constants .current_save_path =None 
            constants .backup_save_path =None 
            constants .srcGuildMapping =None 
            constants .base_guild_lookup ={}
            constants .files_to_delete =set ()
            constants .PLAYER_PAL_COUNTS ={}
            constants .player_levels ={}
            constants .PLAYER_DETAILS_CACHE ={}
            constants .PLAYER_REMAPS ={}
            constants .exclusions ={}
            constants .selected_source_player =None 
            constants .dps_executor =None 
            constants .dps_futures =[]
            constants .dps_tasks =[]
            constants .original_loaded_level_json =None 
            try :
                from palobject import MappingCacheObject 
                MappingCacheObject ._MappingCacheInstances .clear ()
            except ImportError :
                from ..palobject import MappingCacheObject 
                MappingCacheObject ._MappingCacheInstances .clear ()
        save_manager .load_save (parent =self )
    def _restart_program (self ):
        import sys 
        python =sys .executable 
        os .execl (python ,python ,*sys .argv )
    def _save_changes (self ):
        if not constants .loaded_level_json :
            QMessageBox .warning (self ,t ('error.title'),t ('guild.rebuild.no_save'))
            return 
        save_manager .save_changes (parent =self )
    def _rename_world (self ):
        from ..utils import sav_to_json ,json_to_sav 
        if not constants .current_save_path :
            return 
        meta_path =os .path .join (constants .current_save_path ,'LevelMeta.sav')
        if not os .path .exists (meta_path ):
            return 
        meta_json =sav_to_json (meta_path )
        old =meta_json ['properties']['SaveData']['value'].get ('WorldName',{}).get ('value','Unknown World')
        new_name =InputDialog .get_text (t ('world.rename.title'),t ('world.rename.prompt',old =old ),self )
        if new_name :
            meta_json ['properties']['SaveData']['value']['WorldName']['value']=new_name 
            json_to_sav (meta_json ,meta_path )
            QMessageBox .information (self ,t ('success.title'),t ('world.rename.done'))
    def _delete_empty_guilds (self ):
        if not constants .loaded_level_json :
            msg_box =QMessageBox (self )
            msg_box .setWindowTitle (t ('error.title')if t else 'Error')
            msg_box .setText (t ('error.no_save_loaded')if t else 'No save file loaded.')
            msg_box .setIcon (QMessageBox .Warning )
            msg_box .addButton (t ('button.ok')if t else 'OK',QMessageBox .AcceptRole )
            msg_box .exec ()
            return 
        def task ():
            return delete_empty_guilds (self )
        def on_finished (removed ):
            self .refresh_all ()
            msg_box =QMessageBox (self )
            msg_box .setWindowTitle (t ('Done'))
            msg_box .setText (t ('deletion.empty_guilds_removed',count =removed ))
            msg_box .setIcon (QMessageBox .Information )
            msg_box .addButton (t ('button.ok'),QMessageBox .AcceptRole )
            msg_box .exec ()
        run_with_loading (on_finished ,task )
    def _delete_inactive_bases (self ):
        if not constants .loaded_level_json :
            msg_box =QMessageBox (self )
            msg_box .setWindowTitle (t ('error.title')if t else 'Error')
            msg_box .setText (t ('error.no_save_loaded')if t else 'No save file loaded.')
            msg_box .setIcon (QMessageBox .Warning )
            msg_box .addButton (t ('button.ok')if t else 'OK',QMessageBox .AcceptRole )
            msg_box .exec ()
            return 
        days =DaysInputDialog .get_days (
        t ('deletion.inactive_bases.title')if t else 'Delete Inactive Bases',
        t ('deletion.inactive_bases.prompt')if t else 'Delete bases where ALL players inactive for how many days?',
        self 
        )
        if not days :
            return 
        def task ():
            cnt =delete_inactive_bases (days ,self )
            self ._delete_orphaned_bases ()
            return cnt 
        def on_finished (cnt ):
            self .refresh_all ()
            msg_box =QMessageBox (self )
            msg_box .setWindowTitle (t ('Done')if t else 'Done')
            msg_box .setText (t ('bases.deleted_count',count =cnt )if t else f'Deleted {cnt } bases')
            msg_box .setIcon (QMessageBox .Information )
            msg_box .addButton (t ('button.ok')if t else 'OK',QMessageBox .AcceptRole )
            msg_box .exec ()
        run_with_loading (on_finished ,task )
    def _delete_orphaned_bases (self ):
        if not constants .loaded_level_json :
            return 
        wsd =constants .loaded_level_json ['properties']['worldSaveData']['value']
        valid_guild_ids ={
        as_uuid (g ['key'])
        for g in wsd .get ('GroupSaveDataMap',{}).get ('value',[])
        if g ['value']['GroupType']['value']['value']=='EPalGroupType::Guild'
        }
        base_list =wsd .get ('BaseCampSaveData',{}).get ('value',[])[:]
        cnt =0 
        for b in base_list :
            raw =b ['value']['RawData']['value']
            gid_raw =raw .get ('group_id_belong_to')
            gid =as_uuid (gid_raw )if gid_raw else None 
            if not gid or gid not in valid_guild_ids :
                if delete_base_camp (b ,gid ):
                    cnt +=1 
        if cnt >0 :
            QMessageBox .information (self ,t ('Done'),t ('orphaned_bases_deleted',count =cnt ))
    def _delete_duplicate_players (self ):
        if not constants .loaded_level_json :
            QMessageBox .warning (self ,t ('Error'),t ('error.no_save_loaded'))
            return
        def task ():
            return delete_duplicated_players (self )
        def on_finished (removed ):
            self .refresh_all ()
            QMessageBox .information (self ,t ('Done'),t ('deletion.duplicates_removed',count =removed ))
        run_with_loading (on_finished ,task )
    def _delete_inactive_players (self ):
        if not constants .loaded_level_json :
            QMessageBox .warning (self ,t ('Error'),t ('error.no_save_loaded'))
            return
        days =DaysInputDialog .get_days (t ('deletion.inactive_days_title'),t ('deletion.inactive_days_prompt'),self )
        if days :
            def task ():
                return delete_inactive_players (days ,self )
            def on_finished (removed ):
                self .refresh_all ()
                QMessageBox .information (self ,t ('Done'),t ('deletion.inactive_players_removed',count =removed ))
            run_with_loading (on_finished ,task )
    def _delete_unreferenced (self ):
        if not constants .loaded_level_json :
            QMessageBox .warning (self ,t ('Error'),t ('error.no_save_loaded'))
            return
        def task ():
            return delete_unreferenced_data (self )
        def on_finished (result ):
            self .refresh_all ()
            msg =f"Removed {result .get ('characters',0 )} players, {result .get ('pals',0 )} pals, {result .get ('guilds',0 )} guilds\n"
            msg +=f"Removed {result .get ('broken_objects',0 )} broken objects, {result .get ('dropped_items',0 )} dropped items"
            QMessageBox .information (self ,t ('Done'),msg )
        run_with_loading (on_finished ,task )
    def _delete_non_base_map_objs (self ):
        if not constants .loaded_level_json :
            QMessageBox .warning (self ,t ('Error'),t ('error.no_save_loaded'))
            return
        def task ():
            return delete_non_base_map_objects (self )
        def on_finished (removed ):
            self .refresh_all ()
            QMessageBox .information (self ,t ('Done'),t ('deletion.non_base_objs_removed',count =removed ))
        run_with_loading (on_finished ,task )
    def _delete_all_skins (self ):
        if not constants .loaded_level_json :
            QMessageBox .warning (self ,t ('Error'),t ('error.no_save_loaded'))
            return
        def task ():
            return delete_all_skins (self )
        def on_finished (removed ):
            self .refresh_all ()
            QMessageBox .information (self ,t ('Done'),t ('deletion.skins_removed',count =removed ))
        run_with_loading (on_finished ,task )
    def _unlock_private_chests (self ):
        if not constants .loaded_level_json :
            QMessageBox .warning (self ,t ('Error'),t ('error.no_save_loaded'))
            return
        def task ():
            return unlock_all_private_chests (self )
        def on_finished (unlocked ):
            self .refresh_all ()
            QMessageBox .information (self ,t ('Done'),t ('deletion.chests_unlocked',count =unlocked ))
        run_with_loading (on_finished ,task )
    def _remove_invalid_items (self ):
        if not constants .loaded_level_json :
            QMessageBox .warning (self ,t ('Error'),t ('error.no_save_loaded'))
            return
        def task ():
            return remove_invalid_items_from_save (self )
        def on_finished (fixed ):
            self .refresh_all ()
            QMessageBox .information (self ,t ('done'),t ('fixed_files',fixed =fixed ))
        run_with_loading (on_finished ,task )
    def _remove_invalid_structures (self ):
        if not constants .loaded_level_json :
            QMessageBox .warning (self ,t ('Error'),t ('error.no_save_loaded'))
            return
        def task ():
            return delete_invalid_structure_map_objects (self )
        def on_finished (removed ):
            self .refresh_all ()
            QMessageBox .information (self ,t ('Done'),t ('invalid_structures_removed',removed =removed ))
        run_with_loading (on_finished ,task )
    def _remove_invalid_pals (self ):
        if not constants .loaded_level_json :
            QMessageBox .warning (self ,t ('Error'),t ('error.no_save_loaded'))
            return
        def task ():
            return remove_invalid_pals_from_save (self )
        def on_finished (removed ):
            self .refresh_all ()
            QMessageBox .information (self ,t ('Done'),t ('palclean.summary',removed =removed ))
        run_with_loading (on_finished ,task )
    def _reset_missions (self ):
        if not constants .loaded_level_json :
            QMessageBox .warning (self ,t ('Error'),t ('error.no_save_loaded'))
            return
        def task ():
            return fix_missions (self )
        def on_finished (result ):
            self .refresh_all ()
            QMessageBox .information (self ,t ('missions.reset_title'),t ('missions.summary',**result ))
        run_with_loading (on_finished ,task )
    def _reset_anti_air (self ):
        if not constants .loaded_level_json :
            QMessageBox .warning (self ,t ('Error'),t ('error.no_save_loaded'))
            return
        count =reset_anti_air_turrets (self )
        self .refresh_all ()
        QMessageBox .information (self ,t ('Done'),t ('anti_air_reset_count',count =count ))
    def _reset_dungeons (self ):
        if not constants .loaded_level_json :
            QMessageBox .warning (self ,t ('Error'),t ('error.no_save_loaded'))
            return
        count =reset_dungeons (self )
        self .refresh_all ()
        QMessageBox .information (self ,t ('Done'),t ('dungeons_reset_count',count =count ))
    def _fix_all_timestamps (self ):
        if not constants .loaded_level_json :
            QMessageBox .warning (self ,t ('Error')if t else 'Error',t ('guild.rebuild.no_save')if t else 'No save loaded!')
            return 
        fixed =fix_all_negative_timestamps (self )
        self .refresh_all ()
        QMessageBox .information (self ,t ('Done')if t else 'Done',t ('timestamps.fixed_count',count =fixed )if t else f'Fixed {fixed } player timestamps')
    def _reset_player_timestamp (self ,uid ):
        if reset_selected_player_timestamp (uid ,self ):
            self .refresh_all ()
            QMessageBox .information (self ,t ('Done')if t else 'Done',t ('timestamps.player_reset')if t else 'Player timestamp reset to current time')
        else :
            QMessageBox .warning (self ,t ('Error')if t else 'Error',t ('timestamps.reset_failed')if t else 'Failed to reset player timestamp')
    def _open_paldefender (self ):
        dialog =PalDefenderDialog (self )
        dialog .exec ()
    def _rebuild_all_guilds (self ):
        if not constants .loaded_level_json :
            QMessageBox .warning (self ,t ('Error'),t ('error.no_save_loaded'))
            return
        def task ():
            return rebuild_all_guilds ()
        def on_finished (success ):
            if success :
                self .refresh_all ()
                QMessageBox .information (self ,t ('Done'),t ('guild.rebuild.done'))
            else :
                QMessageBox .warning (self ,t ('error.title'),t ('guild.rebuild.failed'))
        run_with_loading (on_finished ,task )
    def _move_player_to_guild (self ):
        if not constants .loaded_level_json :
            QMessageBox .warning (self ,t ('Error'),t ('error.no_save_loaded'))
            return 
        player_data =self .players_panel .get_selected_data ()
        guild_data =self .guilds_panel .get_selected_data ()
        if not player_data :
            QMessageBox .warning (self ,t ('Error'),t ('guild.move.no_player'))
            return 
        if not guild_data :
            QMessageBox .warning (self ,t ('Error'),t ('guild.common.select_guild_first'))
            return 
        if move_player_to_guild (player_data [4 ],guild_data [1 ]):
            self .refresh_all ()
            QMessageBox .information (self ,t ('Done'),t ('guild.move.moved',player =player_data [0 ],guild =guild_data [0 ]))
        else :
            QMessageBox .warning (self ,t ('Error'),t ('guild.move.failed'))
    def _show_map (self ):
        if not constants .loaded_level_json :
            QMessageBox .warning (self ,t ('Error')if t else 'Error',
            t ('error.no_save_loaded')if t else 'No save file loaded.')
            return 
        for i in range (self .stacked_widget .count ()):
            if self .stacked_widget .widget (i )==self .map_tab :
                self .tab_bar .setCurrentIndex (i )
                return 
    def _generate_map (self ):
        if not constants .loaded_level_json :
            QMessageBox .warning (self ,t ('Error')if t else 'Error',
            t ('error.no_save_loaded')if t else 'No save file loaded.')
            return
        def task ():
            return generate_world_map ()
        def on_finished (path ):
            if path :
                from common import open_file_with_default_app
                open_file_with_default_app (path )
                msg_box =QMessageBox (self )
                msg_box .setWindowTitle (t ('Done')if t else 'Done')
                msg_box .setText (t ('map_saved',path =path )if t else f"Map saved to {path }")
                msg_box .setIcon (QMessageBox .Information )
                msg_box .addButton (t ('button.ok')if t else 'OK',QMessageBox .AcceptRole )
                msg_box .exec ()
            else :
                QMessageBox .warning (self ,t ('Error')if t else 'Error',
                t ('mapgen.failed')if t else 'Map generation failed.')
        run_with_loading (on_finished ,task )
    def _save_exclusions (self ):
        save_exclusions ()
        QMessageBox .information (self ,t ('Saved'),t ('deletion.saved_exclusions'))
    def _change_language (self ,code ):
        old_lang =self .user_settings .get ("language")
        if old_lang !=code :
            self .user_settings ["language"]=code 
            self ._save_user_settings ()
            load_resources (code )
            set_language (code )
            self .setWindowTitle (t ('deletion.title')if t else 'All-in-One Tools')
            self ._update_tab_texts ()
            self ._setup_menus ()
            self ._refresh_texts ()
            self .tools_tab .refresh_labels ()
            self .results_widget .refresh_labels ()
            self .header_widget .refresh_labels ()
            self .tab_bar_container .refresh_labels ()
            if hasattr (self .header_widget ,'_menu_popup')and self .header_widget ._menu_popup :
                self .header_widget ._menu_popup .refresh_labels ()
            if hasattr (self ,'map_tab')and self .map_tab :
                self .map_tab .refresh_labels ()
    def _update_tab_texts (self ):
        self .tab_bar .setTabText (0 ,t ('tools_tab')if t else 'Tools')
        self .tab_bar .setTabText (1 ,t ('deletion.search_players')if t else 'Players')
        self .tab_bar .setTabText (2 ,t ('deletion.search_guilds')if t else 'Guilds')
        self .tab_bar .setTabText (3 ,t ('deletion.search_bases')if t else 'Bases')
        self .tab_bar .setTabText (4 ,t ('map.viewer')if t else 'Map')
        self .tab_bar .setTabText (5 ,t ('deletion.menu.exclusions')if t else 'Exclusions')
    def _refresh_texts (self ):
        tools_version ,_ =get_versions ()
        self .setWindowTitle (t ('app.title',version =tools_version )+' - '+t ('tool.deletion'))
        if hasattr (self ,'results_widget')and self .results_widget :
            if hasattr (self .results_widget ,'stats_panel'):
                self .results_widget .stats_panel .refresh_labels ()
        if hasattr (self ,'players_panel'):
            self .players_panel .refresh_labels ()
        if hasattr (self ,'guilds_panel'):
            self .guilds_panel .refresh_labels ()
        if hasattr (self ,'guild_members_panel'):
            self .guild_members_panel .refresh_labels ()
        if hasattr (self ,'bases_panel'):
            self .bases_panel .refresh_labels ()
        if hasattr (self ,'excl_players_panel'):
            self .excl_players_panel .refresh_labels ()
        if hasattr (self ,'excl_guilds_panel'):
            self .excl_guilds_panel .refresh_labels ()
        if hasattr (self ,'excl_bases_panel'):
            self .excl_bases_panel .refresh_labels ()
        if hasattr (self ,'menu_bar'):
            self ._setup_menus ()
    def _add_exclusion (self ,excl_type ,value ):
        if value not in constants .exclusions [excl_type ]:
            constants .exclusions [excl_type ].append (value )
            self ._refresh_exclusions ()
        else :
            QMessageBox .information (self ,t ('Info'),t ('deletion.info.already_in_exclusions',kind =excl_type [:-1 ].capitalize ()))
    def _remove_exclusion (self ,excl_type ,value ):
        if value in constants .exclusions [excl_type ]:
            constants .exclusions [excl_type ].remove (value )
            self ._refresh_exclusions ()
    def _delete_player (self ,uid ):
        if uid in constants .exclusions .get ('players',[]):
            QMessageBox .warning (self ,t ('warning.title')if t else 'Warning',t ('deletion.warning.protected_player')if t else f'Player {uid } is in exclusion list and cannot be deleted.')
            return 
        delete_player (uid )
        self .refresh_all ()
        QMessageBox .information (self ,t ('Done'),t ('deletion.player_deleted'))
    def _delete_guild (self ,gid ):
        if gid in constants .exclusions .get ('guilds',[]):
            QMessageBox .warning (self ,t ('warning.title')if t else 'Warning',t ('deletion.warning.protected_guild')if t else f'Guild {gid } is in exclusion list and cannot be deleted.')
            return 
        delete_guild (gid )
        self .refresh_all ()
        QMessageBox .information (self ,t ('Done'),t ('deletion.guild_deleted'))
    def _delete_base (self ,bid ,gid ):
        if bid in constants .exclusions .get ('bases',[]):
            QMessageBox .warning (self ,t ('warning.title')if t else 'Warning',t ('deletion.warning.protected_base')if t else f'Base {bid } is in exclusion list and cannot be deleted.')
            return 
        from ..data_manager import delete_base_camp 
        wsd =constants .loaded_level_json ['properties']['worldSaveData']['value']
        base_list =wsd .get ('BaseCampSaveData',{}).get ('value',[])
        for b in base_list :
            if str (b ['key']).replace ('-','').lower ()==bid .replace ('-','').lower ():
                delete_base_camp (b ,gid )
                break 
        self .refresh_all ()
        QMessageBox .information (self ,t ('Done'),t ('deletion.base_deleted'))
    def _rename_player (self ,uid ,old_name ):
        new_name =InputDialog .get_text (t ('player.rename.title'),t ('player.rename.prompt'),self )
        if new_name :
            rename_player (uid ,new_name )
            self .refresh_all ()
            QMessageBox .information (self ,t ('player.rename.done_title'),t ('player.rename.done_msg',old =old_name ,new =new_name ))
    def _unlock_viewing_cage (self ,uid ):
        if unlock_viewing_cage_for_player (uid ,self ):
            QMessageBox .information (self ,t ('Done'),t ('player.viewing_cage.unlocked'))
        else :
            QMessageBox .warning (self ,t ('Error'),t ('player.viewing_cage.failed'))
    def _rename_guild_action (self ,gid ,old_name ):
        new_name =InputDialog .get_text (t ('guild.rename.title'),t ('guild.rename.prompt'),self )
        if new_name :
            rename_guild (gid ,new_name )
            self .refresh_all ()
            QMessageBox .information (self ,t ('guild.rename.done_title'),t ('guild.rename.done_msg',old =old_name ,new =new_name ))
    def _max_guild_level (self ,gid ):
        max_guild_level (gid )
        self .refresh_all ()
        QMessageBox .information (self ,t ('success.title'),t ('guild.level.maxed'))
    def _make_leader (self ,gid ,uid ):
        make_member_leader (gid ,uid )
        self .refresh_all ()
        QMessageBox .information (self ,t ('Done'),t ('guild.leader_changed'))
    def _import_base_to_guild (self ,gid ):
        file_paths ,_ =QFileDialog .getOpenFileNames (self ,'Select Base JSON Files','','JSON Files (*.json)')
        if not file_paths :
            return 
        successful_imports =0 
        failed_imports =0 
        failed_files =[]
        for file_path in file_paths :
            try :
                with open (file_path ,'r',encoding ='utf-8')as f :
                    exported_data =json .load (f )
                if import_base_json (constants .loaded_level_json ,exported_data ,gid ):
                    successful_imports +=1 
                else :
                    failed_imports +=1 
                    failed_files .append (os .path .basename (file_path )+' (import failed)')
            except Exception as e :
                failed_imports +=1 
                failed_files .append (os .path .basename (file_path )+f' (error: {str (e )})')
        self .refresh_all ()
        if successful_imports >0 :
            msg =f'Successfully imported {successful_imports } base(s).'
            if failed_imports >0 :
                msg +=f'\nFailed to import {failed_imports } file(s):\n'+'\n'.join (failed_files )
            QMessageBox .information (self ,t ('success.title'),msg )
        else :
            QMessageBox .warning (self ,t ('error.title'),f'Failed to import any bases.\n'+'\n'.join (failed_files ))
    def _export_all_bases (self ):
        if not constants .loaded_level_json :
            QMessageBox .warning (self ,t ('Error')if t else 'Error',t ('error.no_save_loaded')if t else 'No save file loaded.')
            return
        bases =get_bases ()
        if not bases :
            QMessageBox .information (self ,t ('Info')if t else 'Info','No bases found in the save.')
            return
        export_dir =QFileDialog .getExistingDirectory (self ,'Select Export Directory')
        if not export_dir :
            return
        def task ():
            successful_exports =0
            failed_exports =0
            failed_bases =[]
            class CustomEncoder (json .JSONEncoder ):
                def default (self ,obj ):
                    if hasattr (obj ,'bytes')or obj .__class__ .__name__ =='UUID':
                        return str (obj )
                    return super ().default (obj )
            for base in bases :
                bid =base ['id']
                gid =base ['guild_id']
                gname =base ['guild_name']
                try :
                    data =export_base_json (constants .loaded_level_json ,bid )
                    if not data :
                        failed_exports +=1
                        failed_bases .append (f'Base {bid } (no data)')
                        continue
                    safe_gname =''.join (c for c in gname if c .isalnum ()or c in (' ','-','_')).rstrip ()
                    filename =f'base_{bid }_{safe_gname }.json'
                    file_path =os .path .join (export_dir ,filename )
                    with open (file_path ,'w',encoding ='utf-8')as f :
                        json .dump (data ,f ,cls =CustomEncoder ,indent =2 )
                    successful_exports +=1
                except Exception as e :
                    failed_exports +=1
                    failed_bases .append (f'Base {bid } (error: {str (e )})')
            return successful_exports ,failed_exports ,failed_bases ,export_dir
        def on_finished (result ):
            successful_exports ,failed_exports ,failed_bases ,export_dir =result
            if successful_exports >0 :
                msg =f'Successfully exported {successful_exports } base(s) to {export_dir }.'
                if failed_exports >0 :
                    msg +=f'\nFailed to export {failed_exports } base(s):\n'+'\n'.join (failed_bases )
                QMessageBox .information (self ,t ('success.title'),msg )
            else :
                QMessageBox .warning (self ,t ('error.title'),f'Failed to export any bases.\n'+'\n'.join (failed_bases ))
        run_with_loading (on_finished ,task )
    def _export_bases_for_guild (self ,gid ):
        if not constants .loaded_level_json :
            QMessageBox .warning (self ,t ('Error')if t else 'Error',t ('error.no_save_loaded')if t else 'No save file loaded.')
            return 
        guild_name =save_manager .get_guild_name_by_id (gid )
        if not guild_name :
            QMessageBox .warning (self ,t ('error.title'),f'Guild not found: {gid }')
            return 
        bases =get_bases ()
        guild_bases =[b for b in bases if str (b ['guild_id'])==str (gid )]
        if not guild_bases :
            QMessageBox .information (self ,t ('Info')if t else 'Info',f'No bases found for guild "{guild_name }".')
            return 
        export_dir =QFileDialog .getExistingDirectory (self ,f'Select Export Directory for "{guild_name }"')
        if not export_dir :
            return 
        successful_exports =0 
        failed_exports =0 
        failed_bases =[]
        class CustomEncoder (json .JSONEncoder ):
            def default (self ,obj ):
                if hasattr (obj ,'bytes')or obj .__class__ .__name__ =='UUID':
                    return str (obj )
                return super ().default (obj )
        for base in guild_bases :
            bid =base ['id']
            gname =base ['guild_name']
            try :
                data =export_base_json (constants .loaded_level_json ,bid )
                if not data :
                    failed_exports +=1 
                    failed_bases .append (f'Base {bid } (no data)')
                    continue 
                safe_gname =''.join (c for c in gname if c .isalnum ()or c in (' ','-','_')).rstrip ()
                filename =f'base_{bid }_{safe_gname }.json'
                file_path =os .path .join (export_dir ,filename )
                with open (file_path ,'w',encoding ='utf-8')as f :
                    json .dump (data ,f ,cls =CustomEncoder ,indent =2 )
                successful_exports +=1 
            except Exception as e :
                failed_exports +=1 
                failed_bases .append (f'Base {bid } (error: {str (e )})')
        if successful_exports >0 :
            msg =f'Successfully exported {successful_exports } base(s) for guild "{guild_name }" to {export_dir }.'
            if failed_exports >0 :
                msg +=f'\nFailed to export {failed_exports } base(s):\n'+'\n'.join (failed_bases )
            QMessageBox .information (self ,t ('success.title'),msg )
        else :
            QMessageBox .warning (self ,t ('error.title'),f'Failed to export any bases for guild "{guild_name }".\n'+'\n'.join (failed_bases ))
    def _export_base (self ,bid ):
        if not constants .loaded_level_json :
            QMessageBox .warning (self ,t ('Error')if t else 'Error',t ('error.no_save_loaded')if t else 'No save file loaded.')
            return 
        data =export_base_json (constants .loaded_level_json ,bid )
        if not data :
            QMessageBox .warning (
            self ,
            t ('error.title')if t else 'Error',
            t ('base.export.not_found')if t else f'Could not find base data for ID: {bid }'
            )
            return 
        default_filename =f'base_{bid }.json'
        file_path ,_ =QFileDialog .getSaveFileName (
        self ,
        t ('base.export.title')if t else 'Export Base',
        default_filename ,
        'JSON Files (*.json)'
        )
        if not file_path :
            return 
        try :
            class CustomEncoder (json .JSONEncoder ):
                def default (self ,obj ):
                    if hasattr (obj ,'bytes')or obj .__class__ .__name__ =='UUID':
                        return str (obj )
                    return super ().default (obj )
            with open (file_path ,'w',encoding ='utf-8')as f :
                json .dump (data ,f ,cls =CustomEncoder ,indent =2 )
            QMessageBox .information (
            self ,
            t ('success.title')if t else 'Success',
            t ('base.export.success')if t else 'Base exported successfully'
            )
        except Exception as e :
            QMessageBox .critical (
            self ,
            t ('error.title')if t else 'Error',
            t ('base.export.failed')if t else f'Failed to export base: {str (e )}'
            )
    def _import_base (self ,gid ):
        self ._import_base_to_guild (gid )
    def _clone_base (self ,bid ,gid ):
        if clone_base_complete (constants .loaded_level_json ,bid ,gid ):
            self .refresh_all ()
            QMessageBox .information (self ,t ('success.title'),t ('clone_base.msg'))
        else :
            QMessageBox .warning (self ,t ('error.title'),'Failed to clone base')
    def keyPressEvent (self ,event ):
        if event .key ()==Qt .Key_F5 :
            if constants .current_save_path :
                self .refresh_all ()
        super ().keyPressEvent (event )
