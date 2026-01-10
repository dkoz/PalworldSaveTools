import os 
import json 
import uuid 
from PySide6 .QtWidgets import (
QDialog ,QVBoxLayout ,QHBoxLayout ,QLabel ,QPushButton ,
QLineEdit ,QSpinBox ,QComboBox ,QTextEdit ,QFileDialog ,
QMessageBox ,QGroupBox ,QFormLayout ,QCheckBox ,QFrame ,QTabWidget ,QScrollArea ,QWidget ,QGridLayout ,QListWidget ,QInputDialog ,QTableWidget ,QApplication 
)
from PySide6 .QtCore import Qt ,QTimer ,Signal ,QPoint ,QEvent 
from PySide6 .QtGui import QIcon ,QFont ,QPixmap ,QRegion ,QCursor 
from i18n import t 
from palworld_aio import constants 
from palworld_aio .utils import sav_to_json ,extract_value ,format_character_key ,json_to_sav 
class FramelessDialog (QDialog ):
    def __init__ (self ,title_key ="edit_pals.title",parent =None ):
        super ().__init__ (parent )
        self .setWindowFlags (Qt .FramelessWindowHint |Qt .Dialog )
        self .setAttribute (Qt .WA_TranslucentBackground )
        self ._drag_position =QPoint ()
        self ._maximized =False 
        self ._normal_geometry =None 
        self .container =QWidget (self )
        self .container .setObjectName ("editPalsContainer")
        main_layout =QVBoxLayout (self )
        main_layout .setContentsMargins (10 ,10 ,10 ,10 )
        main_layout .addWidget (self .container )
        container_layout =QVBoxLayout (self .container )
        container_layout .setContentsMargins (0 ,0 ,0 ,0 )
        container_layout .setSpacing (0 )
        self .title_bar =QWidget (self .container )
        self .title_bar .setObjectName ("editPalsTitleBar")
        self .title_bar .setFixedHeight (48 )
        title_layout =QHBoxLayout (self .title_bar )
        title_layout .setContentsMargins (16 ,0 ,8 ,0 )
        self .icon_label =QLabel ("🐾")
        self .icon_label .setObjectName ("titleBarIcon")
        title_layout .addWidget (self .icon_label )
        self .title_label =QLabel (t (title_key ))
        self .title_label .setObjectName ("titleBarTitle")
        title_layout .addWidget (self .title_label )
        title_layout .addStretch ()
        self .minimize_btn =QPushButton ("−")
        self .minimize_btn .setObjectName ("titleBarMinimize")
        self .minimize_btn .setFixedSize (36 ,28 )
        self .minimize_btn .clicked .connect (self .showMinimized )
        title_layout .addWidget (self .minimize_btn )
        self .maximize_btn =QPushButton ("□")
        self .maximize_btn .setObjectName ("titleBarMaximize")
        self .maximize_btn .setFixedSize (36 ,28 )
        self .maximize_btn .clicked .connect (self ._toggle_maximize )
        title_layout .addWidget (self .maximize_btn )
        self .close_btn =QPushButton ("×")
        self .close_btn .setObjectName ("titleBarClose")
        self .close_btn .setFixedSize (36 ,28 )
        self .close_btn .clicked .connect (self .close )
        title_layout .addWidget (self .close_btn )
        container_layout .addWidget (self .title_bar )
        self .content_widget =QWidget (self .container )
        self .content_widget .setObjectName ("editPalsContent")
        self .content_layout =QVBoxLayout (self .content_widget )
        self .content_layout .setContentsMargins (16 ,12 ,16 ,16 )
        container_layout .addWidget (self .content_widget )
        self ._apply_styles ()
        self .title_bar .installEventFilter (self )
    def _apply_styles (self ):
        self .setStyleSheet ("""
            QWidget#editPalsContainer {
                background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1,
                            stop:0 rgba(12,14,18,0.98), stop:0.5 rgba(10,16,22,0.98), stop:1 rgba(8,12,18,0.98));
                border: 1px solid rgba(125,211,252,0.2);
                border-radius: 12px;
            }

            QWidget#editPalsTitleBar {
                background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0,
                            stop:0 rgba(125,211,252,0.08), stop:1 rgba(167,139,250,0.08));
                border: none;
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
            }

            QLabel#titleBarIcon {
                font-size: 20px;
                padding: 0px 4px;
            }

            QLabel#titleBarTitle {
                font-size: 14px;
                font-weight: 700;
                color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0,
                            stop:0 #7DD3FC, stop:1 #A78BFA);
                padding: 0px 8px;
            }

            QPushButton#titleBarMinimize, QPushButton#titleBarMaximize {
                background: transparent;
                border: none;
                color: #A6B8C8;
                font-size: 16px;
                font-weight: bold;
                border-radius: 4px;
            }

            QPushButton#titleBarMinimize:hover, QPushButton#titleBarMaximize:hover {
                background: rgba(255,255,255,0.1);
                color: #FFFFFF;
            }

            QPushButton#titleBarClose {
                background: transparent;
                border: none;
                color: #FB7185;
                font-size: 20px;
                font-weight: bold;
                border-radius: 4px;
            }

            QPushButton#titleBarClose:hover {
                background: rgba(251,113,133,0.2);
                color: #FFFFFF;
            }

            QWidget#editPalsContent {
                background: transparent;
            }

            /* Section headers in edit pals */
            QLabel#editPalsSection {
                background: rgba(125,211,252,0.08);
                border: 1px solid rgba(125,211,252,0.15);
                border-radius: 8px;
                padding: 8px 16px;
                color: #7DD3FC;
                font-weight: 700;
                font-size: 12px;
            }

            /* Pal card widgets */
            QFrame#palCard {
                background: rgba(255,255,255,0.03);
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 8px;
                padding: 8px;
            }

            QFrame#palCard:hover {
                background: rgba(125,211,252,0.08);
                border-color: rgba(125,211,252,0.2);
            }

            QFrame#palCard[selected="true"] {
                background: rgba(125,211,252,0.15);
                border-color: rgba(125,211,252,0.4);
            }

            /* Skill badges */
            QLabel#skillBadge {
                background: rgba(34,197,94,0.15);
                border: 1px solid rgba(34,197,94,0.25);
                border-radius: 4px;
                padding: 3px 8px;
                color: #22C55E;
                font-size: 10px;
            }

            QLabel#skillBadge:hover {
                background: rgba(34,197,94,0.25);
            }

            /* Stats display */
            QLabel#statsValue {
                color: #FFFFFF;
                font-weight: 700;
            }

            QLabel#statsLabel {
                color: #A6B8C8;
                font-size: 11px;
            }

            /* Input fields */
            QLineEdit#editPalsInput {
                background: rgba(255,255,255,0.06);
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 6px;
                padding: 6px 10px;
                color: #dfeefc;
                font-size: 11px;
            }

            QLineEdit#editPalsInput:focus {
                background: rgba(255,255,255,0.08);
                border-color: rgba(125,211,252,0.3);
            }

            /* Spin boxes */
            QSpinBox#editPalsSpin {
                background: rgba(255,255,255,0.06);
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 6px;
                padding: 4px;
                color: #dfeefc;
            }

            QSpinBox#editPalsSpin:focus {
                border-color: rgba(125,211,252,0.3);
            }

            /* Combo boxes */
            QComboBox#editPalsCombo {
                background: rgba(255,255,255,0.06);
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 6px;
                padding: 4px 8px;
                color: #dfeefc;
            }

            QComboBox#editPalsCombo:hover {
                border-color: rgba(125,211,252,0.2);
            }

            QComboBox#editPalsCombo::drop-down {
                border: none;
                padding-right: 20px;
            }

            /* Action buttons */
            QPushButton#editPalsActionButton {
                background: rgba(125,211,252,0.12);
                border: 1px solid rgba(125,211,252,0.2);
                border-radius: 6px;
                padding: 8px 16px;
                color: #7DD3FC;
                font-weight: 600;
                font-size: 11px;
            }

            QPushButton#editPalsActionButton:hover {
                background: rgba(125,211,252,0.2);
                border-color: rgba(125,211,252,0.4);
                color: #FFFFFF;
            }

            QPushButton#editPalsActionButton:pressed {
                background: rgba(125,211,252,0.3);
            }

            /* Danger button */
            QPushButton#editPalsDangerButton {
                background: rgba(251,113,133,0.12);
                border: 1px solid rgba(251,113,133,0.2);
                border-radius: 6px;
                padding: 8px 16px;
                color: #FB7185;
                font-weight: 600;
                font-size: 11px;
            }

            QPushButton#editPalsDangerButton:hover {
                background: rgba(251,113,133,0.2);
                border-color: rgba(251,113,133,0.4);
                color: #FFFFFF;
            }

            /* Success button */
            QPushButton#editPalsSuccessButton {
                background: rgba(34,197,94,0.12);
                border: 1px solid rgba(34,197,94,0.2);
                border-radius: 6px;
                padding: 8px 16px;
                color: #22C55E;
                font-weight: 600;
                font-size: 11px;
            }

            QPushButton#editPalsSuccessButton:hover {
                background: rgba(34,197,94,0.2);
                border-color: rgba(34,197,94,0.4);
                color: #FFFFFF;
            }

            /* Group boxes */
            QGroupBox#editPalsGroup {
                background: rgba(255,255,255,0.02);
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 8px;
                margin-top: 8px;
                padding: 12px;
                font-size: 11px;
                color: #A6B8C8;
            }

            QGroupBox#editPalsGroup::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 2px 8px;
                color: #7DD3FC;
                font-weight: 600;
            }

            /* Scroll areas */
            QScrollArea#editPalsScroll {
                background: transparent;
                border: none;
            }

            QScrollArea#editPalsScroll > QWidget > QWidget {
                background: transparent;
            }

            /* Pal selector widget */
            QFrame#palSelectorWidget {
                background: rgba(255,255,255,0.03);
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 8px;
            }

            QFrame#palSelectorWidget:hover {
                border-color: rgba(125,211,252,0.2);
            }

            QFrame#palSelectorWidget[selected="true"] {
                background: rgba(125,211,252,0.12);
                border-color: rgba(125,211,252,0.4);
            }

            /* Context menu for edit pals */
            QMenu#editPalsContextMenu {
                background: rgba(12,14,18,0.98);
                border: 1px solid rgba(125,211,252,0.2);
                border-radius: 8px;
                padding: 4px;
            }

            QMenu#editPalsContextMenu::item {
                padding: 8px 20px;
                border-radius: 4px;
                color: #E6EEF6;
            }

            QMenu#editPalsContextMenu::item:selected {
                background: rgba(125,211,252,0.15);
                color: #FFFFFF;
            }

            QMenu#editPalsContextMenu::separator {
                height: 1px;
                background: rgba(255,255,255,0.1);
                margin: 4px 10px;
            }
        """)
    def _toggle_maximize (self ):
        if self ._maximized :
            self .showNormal ()
            self ._maximized =False 
            self .maximize_btn .setText ("□")
        else :
            self ._normal_geometry =self .geometry ()
            self .showMaximized ()
            self ._maximized =True 
            self .maximize_btn .setText ("❐")
    def eventFilter (self ,obj ,event ):
        if obj ==self .title_bar :
            if event .type ()==QEvent .Type .MouseButtonPress :
                if event .button ()==Qt .LeftButton :
                    self ._drag_position =event .globalPosition ().toPoint ()-self .frameGeometry ().topLeft ()
                    event .accept ()
            elif event .type ()==QEvent .Type .MouseMove :
                if event .buttons ()==Qt .LeftButton and self ._drag_position :
                    self .move (event .globalPosition ().toPoint ()-self ._drag_position )
                    event .accept ()
            elif event .type ()==QEvent .Type .MouseButtonDblClick :
                self ._toggle_maximize ()
                event .accept ()
                return True 
        return super ().eventFilter (obj ,event )
    def set_title (self ,title_key ):
        self .title_label .setText (t (title_key ))
    def set_title_text (self ,text ):
        self .title_label .setText (text )
class StarButton (QPushButton ):
    def mouseReleaseEvent (self ,event ):
        if event .button ()==Qt .LeftButton :
            super ().mouseReleaseEvent (event )
        else :
            event .ignore ()
_ICON_CACHE ={}
_PIXMAP_CACHE ={}
class PalIcon (QFrame ):
    clicked =Signal ()
    rightClicked =Signal (int ,str ,str )
    def __init__ (self ,pal_data =None ,tab =None ,slot_index =0 ,tab_name ="",parent =None ):
        super ().__init__ (parent )
        self .pal_data =pal_data 
        self .slot_index =slot_index 
        self .tab_name =tab_name 
        self .selected =False 
        self .setFrameStyle (QFrame .Box )
        self .setFixedSize (80 ,80 )
        self .setObjectName ("palIcon")
        self .setStyleSheet ("""
            QFrame#palIcon {
                border: 2px solid #666;
                border-radius: 40px;
                background-color: #333;
            }
            QFrame#palIcon:hover {
                border: 2px solid #7DD3FC;
                background-color: #444;
            }
        """)
        self ._setup_ui ()
    def _setup_ui (self ):
        self ._clear_ui ()
        if not self .pal_data :
            return 
        try :
            if 'data'in self .pal_data :
                raw =self .pal_data ['data']
            elif 'value'in self .pal_data :
                raw =self .pal_data ['value']['RawData']['value']['object']['SaveParameter']['value']
            else :
                raw =self .pal_data 
            if not isinstance (raw ,dict ):
                print (f"Warning: Pal data raw is not a dict (type: {type (raw )}), skipping widget setup")
                layout =QVBoxLayout (self )
                layout .setContentsMargins (0 ,0 ,0 ,0 )
                empty_label =QLabel ("Invalid Data")
                empty_label .setAlignment (Qt .AlignCenter )
                empty_label .setStyleSheet ("color: red; font-size: 8px;")
                layout .addWidget (empty_label ,alignment =Qt .AlignCenter )
                return 
            cid =extract_value (raw ,'CharacterID','')
            nick =extract_value (raw ,'NickName','')
            level =extract_value (raw ,'Level',1 )
            gender_data =extract_value (raw ,'Gender',{})
            if isinstance (gender_data ,dict )and 'value'in gender_data :
                gender =gender_data ['value']
            elif isinstance (gender_data ,str ):
                gender =gender_data 
            else :
                gender ='EPalGenderType::Female'
            is_boss =cid .upper ().startswith ('BOSS_')or extract_value (raw ,'IsRarePal',False )
            is_predator =extract_value (raw ,'IsRarePal',False )
            is_lucky =extract_value (raw ,'IsRarePal',False )
            image_label =QLabel (self )
            image_label .setAlignment (Qt .AlignCenter )
            image_label .setFixedSize (64 ,64 )
            image_label .setStyleSheet ("border: none; background: transparent;")
            image_label .setAttribute (Qt .WA_TransparentForMouseEvents )
            base_dir =os .path .dirname (os .path .dirname (os .path .abspath (__file__ )))
            icon_path =os .path .join (base_dir ,'resources','game_data','icons','pals',f"{cid }.webp")
            if cid not in _ICON_CACHE :
                if not os .path .exists (icon_path ):
                    icon_path =os .path .join (base_dir ,'resources','game_data','icons','pals',f"{cid .lower ()}.webp")
                if not os .path .exists (icon_path ):
                    cid_no_boss =cid .lower ().replace ("boss_","").replace ("b_o_s_s_","")
                    icon_path =os .path .join (base_dir ,'resources','game_data','icons','pals',f"{cid_no_boss }.webp")
                if not os .path .exists (icon_path ):
                    icon_path =os .path .join (base_dir ,'resources','game_data','icons','pals','unknown.webp')
                if not os .path .exists (icon_path ):
                    icon_path =os .path .join (base_dir ,'resources','baseicon.webp')
                _ICON_CACHE [cid ]=icon_path 
            else :
                icon_path =_ICON_CACHE [cid ]
            if icon_path and os .path .exists (icon_path ):
                pixmap_key =f"{icon_path }_64x64"
                if pixmap_key not in _PIXMAP_CACHE :
                    pixmap =QPixmap (icon_path )
                    if not pixmap .isNull ():
                        scaled_pixmap =pixmap .scaled (64 ,64 ,Qt .KeepAspectRatio ,Qt .SmoothTransformation )
                        if not scaled_pixmap .isNull ():
                            _PIXMAP_CACHE [pixmap_key ]=scaled_pixmap 
                if pixmap_key in _PIXMAP_CACHE :
                    image_label .setPixmap (_PIXMAP_CACHE [pixmap_key ])
                    try :
                        mask =QRegion (0 ,0 ,64 ,64 ,QRegion .Ellipse )
                        image_label .setMask (mask )
                    except Exception as e :
                        pass 
                    self .update ()
            pal_name =PalFrame ._NAMEMAP .get (cid .lower (),cid )
            if nick :
                pal_name =f"{pal_name } ({nick })"
            self ._add_overlays (level ,gender ,is_boss ,is_predator ,is_lucky ,image_label ,pal_name )
            image_label .move ((self .width ()-image_label .width ())//2 ,(self .height ()-image_label .height ())//2 )
        except Exception as e :
            print (f"Error setting up PalIcon: {e }")
            self ._clear_ui ()
    def _clear_ui (self ):
        for child in self .findChildren (QLabel ):
            child .deleteLater ()
        self .update ()
    def _add_overlays (self ,level ,gender ,is_boss ,is_predator ,is_lucky ,image_label ,pal_name ):
        level_label =QLabel (f"{level }")
        level_label .setStyleSheet ("""
            color: white;
            font-size: 10px;
            font-weight: bold;
            background-color: rgba(0,0,0,0.7);
            border-radius: 2px;
            padding: 1px 2px;
        """)
        level_label .setFixedSize (25 ,15 )
        level_label .move (2 ,self .height ()-17 )
        level_label .setAttribute (Qt .WA_TransparentForMouseEvents )
        gender_icon ="♂"if t ("edit_pals.male")in gender else "♀"
        gender_color ="#7DD3FC"if t ("edit_pals.male")in gender else "#FB7185"
        gender_label =QLabel (gender_icon )
        gender_label .setStyleSheet (f"""
            color: {gender_color };
            font-size: 14px;
            font-weight: bold;
            background-color: rgba(0,0,0,0.7);
            border-radius: 7px;
        """)
        gender_label .setFixedSize (16 ,16 )
        gender_label .move (self .width ()-18 ,2 )
        gender_label .setAttribute (Qt .WA_TransparentForMouseEvents )
        self .gender_label =gender_label 
        badge_x =2 
        if is_boss :
            boss_label =QLabel ("α")
            boss_label .setStyleSheet ("""
                color: #F59E0B;
                font-size: 12px;
                font-weight: bold;
                background-color: rgba(0,0,0,0.7);
                border-radius: 6px;
            """)
            boss_label .setFixedSize (14 ,14 )
            boss_label .move (badge_x ,2 )
            boss_label .setAttribute (Qt .WA_TransparentForMouseEvents )
            badge_x +=16 
        if is_predator :
            predator_label =QLabel ("🦹")
            predator_label .setStyleSheet ("""
                color: #EF4444;
                font-size: 10px;
                background-color: rgba(0,0,0,0.7);
                border-radius: 6px;
            """)
            predator_label .setFixedSize (14 ,14 )
            predator_label .move (badge_x ,2 )
            predator_label .setAttribute (Qt .WA_TransparentForMouseEvents )
            badge_x +=16 
        if is_lucky :
            lucky_label =QLabel ("✨")
            lucky_label .setStyleSheet ("""
                color: #F59E0B;
                font-size: 10px;
                background-color: rgba(0,0,0,0.7);
                border-radius: 6px;
            """)
            lucky_label .setFixedSize (14 ,14 )
            lucky_label .move (badge_x ,2 )
            lucky_label .setAttribute (Qt .WA_TransparentForMouseEvents )
    def mousePressEvent (self ,event ):
        if event .button ()==Qt .LeftButton :
            self .clicked .emit ()
        super ().mousePressEvent (event )
    def contextMenuEvent (self ,event ):
        from PySide6 .QtWidgets import QMenu 
        menu =QMenu (self )
        if self .pal_data :
            delete_action =menu .addAction ("Delete")
            clone_action =menu .addAction ("Clone")
            menu .addSeparator ()
            rename_action =menu .addAction (t ("edit_pals.rename_pal"))
            swap_gender_action =menu .addAction ("Swap Gender")
            increase_rank_action =menu .addAction (t ("edit_pals.increase_rank"))
            menu .addSeparator ()
            max_stats_action =menu .addAction (t ("edit_pals.max_all"))
            max_ivs_action =menu .addAction (t ("edit_pals.max_ivs"))
            max_souls_action =menu .addAction (t ("edit_pals.max_souls"))
            action =menu .exec (event .globalPos ())
            if action ==delete_action :
                self .rightClicked .emit (self .slot_index ,self .tab_name ,"delete")
            elif action ==clone_action :
                pass 
            elif action ==rename_action :
                self .rightClicked .emit (self .slot_index ,self .tab_name ,"rename")
            elif action ==swap_gender_action :
                self .rightClicked .emit (self .slot_index ,self .tab_name ,"swap_gender")
            elif action ==increase_rank_action :
                self .rightClicked .emit (self .slot_index ,self .tab_name ,"increase_rank")
            elif action ==max_stats_action :
                self .rightClicked .emit (self .slot_index ,self .tab_name ,"max_stats")
            elif action ==max_ivs_action :
                self .rightClicked .emit (self .slot_index ,self .tab_name ,"max_ivs")
            elif action ==max_souls_action :
                self .rightClicked .emit (self .slot_index ,self .tab_name ,"max_souls")
        else :
            add_action =menu .addAction ("Add New Pal")
            action =menu .exec (event .globalPos ())
            if action ==add_action :
                self .rightClicked .emit (self .slot_index ,self .tab_name ,"add_new")
    def set_selected (self ,selected ):
        self .selected =selected 
        if selected :
            self .setStyleSheet ("""
                QFrame#palIcon {
                    border: 4px solid #7DD3FC;
                    border-radius: 40px;
                    background-color: #444;
                }
            """)
        else :
            self .setStyleSheet ("""
                QFrame#palIcon {
                    border: 2px solid #666;
                    border-radius: 40px;
                    background-color: #333;
                }
                QFrame#palIcon:hover {
                    border: 2px solid #7DD3FC;
                    background-color: #444;
                }
            """)
class PalCardWidget (QFrame ):
    clicked =Signal ()
    def __init__ (self ,pal_data =None ,parent =None ):
        super ().__init__ (parent )
        self .pal_data =pal_data 
        self .selected =False 
        self .setFrameStyle (QFrame .Box )
        self .setFixedSize (350 ,80 )
        self .setObjectName ("palCard")
        self .setStyleSheet ("""
            QFrame#palCard {
                border: 2px solid #666;
                background-color: #333;
            }
            QFrame#palCard:hover {
                border: 2px solid #7DD3FC;
                background-color: #444;
            }
        """)
        self .setCursor (Qt .PointingHandCursor )
        self ._setup_ui ()
    def mousePressEvent (self ,event ):
        if event .button ()==Qt .LeftButton :
            self .clicked .emit ()
        super ().mousePressEvent (event )
    def _setup_ui (self ):
        if not self .pal_data :
            return 
        try :
            if 'data'in self .pal_data :
                raw =self .pal_data ['data']
            elif 'value'in self .pal_data :
                raw =self .pal_data ['value']['RawData']['value']['object']['SaveParameter']['value']
            else :
                raw =self .pal_data 
            if not isinstance (raw ,dict ):
                print (f"Warning: Pal data raw is not a dict (type: {type (raw )}), skipping widget setup")
                layout =QHBoxLayout (self )
                layout .setContentsMargins (10 ,5 ,10 ,5 )
                layout .setSpacing (10 )
                left_widget =QWidget ()
                left_layout =QVBoxLayout (left_widget )
                left_layout .setContentsMargins (0 ,0 ,0 ,0 )
                error_label =QLabel ("Invalid Data")
                error_label .setStyleSheet ("font-weight: bold; font-size: 12px; color: red;")
                left_layout .addWidget (error_label )
                layout .addWidget (left_widget )
                empty_label =QLabel ()
                empty_label .setFixedSize (48 ,48 )
                layout .addWidget (empty_label ,alignment =Qt .AlignCenter )
                return 
            cid =extract_value (raw ,'CharacterID','')
            nick =extract_value (raw ,'NickName','')
            level =extract_value (raw ,'Level',1 )
            gender_data =extract_value (raw ,'Gender',{})
            if isinstance (gender_data ,dict )and 'value'in gender_data :
                gender =gender_data ['value']
            elif isinstance (gender_data ,str ):
                gender =gender_data 
            else :
                gender ='EPalGenderType::Female'
            hp =extract_value (raw ,'Hp',0 )
            max_hp =extract_value (raw ,'MaxHp',hp )
            stomach =extract_value (raw ,'FullStomach',0 )
            pal_name =PalFrame ._NAMEMAP .get (cid .lower (),cid )
            if nick :
                pal_name =f"{pal_name } ({nick })"
            layout =QHBoxLayout (self )
            layout .setContentsMargins (10 ,5 ,10 ,5 )
            layout .setSpacing (10 )
            left_widget =QWidget ()
            left_layout =QVBoxLayout (left_widget )
            left_layout .setContentsMargins (0 ,0 ,0 ,0 )
            left_layout .setSpacing (2 )
            name_layout =QHBoxLayout ()
            name_layout .setSpacing (5 )
            name_label =QLabel (pal_name )
            name_label .setStyleSheet ("font-weight: bold; font-size: 12px; color: white;")
            name_layout .addWidget (name_label )
            level_gender_layout =QHBoxLayout ()
            level_gender_layout .setSpacing (5 )
            level_label =QLabel (f"LV {level }")
            level_label .setStyleSheet ("font-size: 10px; color: #7DD3FC;")
            level_gender_layout .addWidget (level_label )
            gender_icon ="♂"if t ("edit_pals.male")in gender else "♀"
            gender_color ="#7DD3FC"if t ("edit_pals.male")in gender else "#FB7185"
            gender_label =QLabel (gender_icon )
            gender_label .setStyleSheet (f"font-size: 12px; color: {gender_color };")
            level_gender_layout .addWidget (gender_label )
            self .gender_label =gender_label 
            level_gender_layout .addStretch ()
            name_layout .addLayout (level_gender_layout )
            left_layout .addLayout (name_layout )
            health_layout =QVBoxLayout ()
            health_layout .setSpacing (1 )
            health_label =QLabel (t ("edit_pals.hp"))
            health_label .setStyleSheet ("font-size: 8px; color: #9CA3AF;")
            health_layout .addWidget (health_label )
            health_bar =QFrame ()
            health_bar .setFixedHeight (6 )
            health_ratio =hp /max_hp if max_hp >0 else 0 
            health_bar .setStyleSheet (f"""
                QFrame {{
                    background-color: #374151;
                    border-radius: 3px;
                }}
                QFrame::after {{
                    content: '';
                    display: block;
                    width: {health_ratio *100 }%;
                    height: 100%;
                    background-color: #10B981;
                    border-radius: 3px;
                }}
            """)
            health_layout .addWidget (health_bar )
            left_layout .addLayout (health_layout )
            stomach_layout =QVBoxLayout ()
            stomach_layout .setSpacing (1 )
            stomach_label =QLabel ("Stomach")
            stomach_label .setStyleSheet ("font-size: 8px; color: #9CA3AF;")
            stomach_layout .addWidget (stomach_label )
            stomach_bar =QFrame ()
            stomach_bar .setFixedHeight (6 )
            stomach_ratio =stomach /150.0 
            stomach_bar .setStyleSheet (f"""
                QFrame {{
                    background-color: #374151;
                    border-radius: 3px;
                }}
                QFrame::after {{
                    content: '';
                    display: block;
                    width: {stomach_ratio *100 }%;
                    height: 100%;
                    background-color: #F59E0B;
                    border-radius: 3px;
                }}
            """)
            stomach_layout .addWidget (stomach_bar )
            left_layout .addLayout (stomach_layout )
            layout .addWidget (left_widget )
            image_label =QLabel ()
            image_label .setAlignment (Qt .AlignCenter )
            image_label .setFixedSize (48 ,48 )
            image_label .setStyleSheet ("border: none; background: transparent;")
            base_dir =os .path .dirname (os .path .dirname (os .path .abspath (__file__ )))
            icon_path =os .path .join (base_dir ,'resources','game_data','icons','pals',f"{cid }.webp")
            if not os .path .exists (icon_path ):
                icon_path =os .path .join (base_dir ,'resources','game_data','icons','pals',f"{cid .lower ()}.webp")
            if not os .path .exists (icon_path ):
                cid_no_boss =cid .lower ().replace ("boss_","").replace ("b_o_s_s_","")
                icon_path =os .path .join (base_dir ,'resources','game_data','icons','pals',f"{cid_no_boss }.webp")
            if not os .path .exists (icon_path ):
                icon_path =os .path .join (base_dir ,'resources','game_data','icons','pals','unknown.webp')
            if not os .path .exists (icon_path ):
                icon_path =os .path .join (base_dir ,'resources','baseicon.webp')
            if os .path .exists (icon_path ):
                pixmap =QPixmap (icon_path )
                if not pixmap .isNull ():
                    image_label .setPixmap (pixmap .scaled (image_label .size (),Qt .KeepAspectRatio ,Qt .SmoothTransformation ))
                    self .update ()
            layout .addWidget (image_label ,alignment =Qt .AlignCenter )
        except Exception as e :
            print (f"Error setting up PalCardWidget: {e }")
            layout =QHBoxLayout (self )
            layout .setContentsMargins (10 ,5 ,10 ,5 )
            layout .setSpacing (10 )
            left_widget =QWidget ()
            left_layout =QVBoxLayout (left_widget )
            left_layout .setContentsMargins (0 ,0 ,0 ,0 )
            error_label =QLabel ("Error")
            error_label .setStyleSheet ("font-weight: bold; font-size: 12px; color: red;")
            left_layout .addWidget (error_label )
            layout .addWidget (left_widget )
            empty_label =QLabel ()
            empty_label .setFixedSize (48 ,48 )
            layout .addWidget (empty_label ,alignment =Qt .AlignCenter )
    def set_selected (self ,selected ):
        self .selected =selected 
        if selected :
            self .setStyleSheet ("""
                QFrame#palCard {
                    border: 4px solid #7DD3FC;
                    background-color: #444;
                }
            """)
        else :
            self .setStyleSheet ("""
                QFrame#palCard {
                    border: 2px solid #666;
                    background-color: #333;
                }
                QFrame#palCard:hover {
                    border: 2px solid #7DD3FC;
                    background-color: #444;
                }
            """)
class EditPalsDialog (FramelessDialog ):
    def __init__ (self ,player_uid ,player_name ,parent =None ):
        super ().__init__ ("edit_pals.title",parent )
        self .player_uid =player_uid 
        self .player_name =player_name 
        self .set_title_text (f"{t ('edit_pals.title')} - {player_name }")
        self .setModal (True )
        self .setMinimumSize (1200 ,800 )
        if os .path .exists (constants .ICON_PATH ):
            self .setWindowIcon (QIcon (constants .ICON_PATH ))
        self ._get_container_ids ()
        PalFrame ._load_maps ()
        self .tabs =QTabWidget ()
        self .tabs .setObjectName ("editPalsTab")
        self .party_tab =self ._create_tab (t ("edit_pals.party"))
        self .palbox_tab =self ._create_tab (t ("edit_pals.palbox"))
        self .tabs .addTab (self .party_tab ,t ("edit_pals.party"))
        self .tabs .addTab (self .palbox_tab ,t ("edit_pals.palbox"))
        save_tab =QWidget ()
        cancel_tab =QWidget ()
        self .tabs .addTab (save_tab ,t ("edit_pals.save"))
        self .tabs .addTab (cancel_tab ,t ("edit_pals.cancel"))
        self .tabs .currentChanged .connect (self ._on_tab_changed )
        self .skill_filter_timer =QTimer (self )
        self .skill_filter_timer .setSingleShot (True )
        self .skill_filter_timer .timeout .connect (self ._do_filter_skills )
        self .current_filter_combo =None 
        self .current_filter_skill_type =None 
        self ._setup_ui ()
        self ._load_pals ()
    def _on_tab_changed (self ,index ):
        tab_text =self .tabs .tabText (index )
        if tab_text ==t ("edit_pals.save"):
            self .accept ()
        elif tab_text ==t ("edit_pals.cancel"):
            self .reject ()
    def _get_container_ids (self ):
        self .party_container =None 
        self .palbox_container =None 
        self .player_sav_path =None 
        players_dir =os .path .join (constants .current_save_path ,'Players')
        target_uid =self .player_uid .replace ('-','').lower ()
        if os .path .exists (players_dir ):
            for filename in os .listdir (players_dir ):
                if filename .endswith ('.sav')and '_dps'not in filename :
                    p_uid_raw =filename .replace ('.sav','').lower ()
                    if p_uid_raw ==target_uid :
                        self .player_sav_path =os .path .join (players_dir ,filename )
                        try :
                            p_json =sav_to_json (self .player_sav_path )
                            p_prop =p_json .get ('properties',{}).get ('SaveData',{}).get ('value',{})
                            self .party_container =p_prop .get ('OtomoCharacterContainerId',{}).get ('value',{}).get ('ID',{}).get ('value')
                            self .palbox_container =p_prop .get ('PalStorageContainerId',{}).get ('value',{}).get ('ID',{}).get ('value')
                        except :
                            pass 
    def _create_tab (self ,tab_name ):
        tab =QWidget ()
        tab .layout =QVBoxLayout (tab )
        tab .layout .setContentsMargins (10 ,10 ,10 ,10 )
        tab .layout .setSpacing (10 )
        tab .pal_scroll =QScrollArea ()
        tab .pal_scroll .setObjectName ("editPalsScroll")
        tab .pal_scroll .setWidgetResizable (True )
        tab .pal_scroll .setHorizontalScrollBarPolicy (Qt .ScrollBarAsNeeded )
        tab .pal_scroll .setVerticalScrollBarPolicy (Qt .ScrollBarAsNeeded )
        tab .pal_scroll .setMinimumHeight (150 )
        tab .pal_scroll .setMaximumHeight (250 )
        tab .pal_container =QWidget ()
        tab .pal_container .setObjectName ("palContainer")
        tab .pal_layout =QGridLayout (tab .pal_container )
        tab .pal_layout .setSpacing (5 )
        tab .pal_scroll .setWidget (tab .pal_container )
        tab .layout .addWidget (tab .pal_scroll )
        tab .selected_pal_index =-1 
        max_slots =5 if tab_name ==t ("edit_pals.party")else (960 if tab_name ==t ("edit_pals.palbox")else 9600 )
        tab .max_slots =max_slots 
        main_layout =QHBoxLayout ()
        main_layout .setSpacing (15 )
        left_panel =self ._create_tab_left_panel (tab ,tab_name )
        main_layout .addWidget (left_panel ,1 )
        center_panel =self ._create_tab_center_panel (tab ,tab_name )
        main_layout .addWidget (center_panel ,1 )
        right_panel =self ._create_tab_right_panel (tab ,tab_name )
        main_layout .addWidget (right_panel ,3 )
        tab .layout .addLayout (main_layout )
        tab .slot_label =QLabel (t ("edit_pals.slot_count",current =0 ,max =max_slots ))
        tab .slot_label .setObjectName ("slotCountLabel")
        tab .layout .addWidget (tab .slot_label )
        tab .pal_data =[]
        return tab 
    def _setup_ui (self ):
        self .content_layout .setContentsMargins (8 ,8 ,8 ,8 )
        self .content_layout .setSpacing (8 )
        self .content_layout .addWidget (self .tabs )
    def _create_left_panel (self ):
        panel =QWidget ()
        panel .setMinimumWidth (300 )
        layout =QVBoxLayout (panel )
        layout .setContentsMargins (10 ,10 ,10 ,10 )
        layout .setSpacing (10 )
        active_skills_label =QLabel (t ("edit_pals.active_skills"))
        active_skills_label .setStyleSheet ("font-weight: bold; font-size: 14px;")
        layout .addWidget (active_skills_label )
        self .active_skills_list =QVBoxLayout ()
        self .active_skills_list .setSpacing (5 )
        layout .addLayout (self .active_skills_list )
        passive_skills_label =QLabel (t ("edit_pals.passive_skills"))
        passive_skills_label .setStyleSheet ("font-weight: bold; font-size: 14px;")
        layout .addWidget (passive_skills_label )
        self .passive_skills_list =QVBoxLayout ()
        self .passive_skills_list .setSpacing (5 )
        layout .addLayout (self .passive_skills_list )
        layout .addStretch ()
        return panel 
    def _create_center_panel (self ):
        panel =QWidget ()
        layout =QVBoxLayout (panel )
        layout .setContentsMargins (10 ,10 ,10 ,10 )
        self .pal_image_label =QLabel ("No Image")
        self .pal_image_label .setAlignment (Qt .AlignCenter )
        self .pal_image_label .setMinimumSize (200 ,200 )
        self .pal_image_label .setStyleSheet ("""
            QLabel {
                border: 2px solid #ccc;
                background-color: #f0f0f0;
                border-radius: 10px;
            }
        """)
        layout .addWidget (self .pal_image_label )
        layout .addStretch ()
        return panel 
    def _create_right_panel (self ):
        panel =QWidget ()
        panel .setMinimumWidth (250 )
        layout =QVBoxLayout (panel )
        layout .setContentsMargins (10 ,10 ,10 ,10 )
        layout .setSpacing (10 )
        stats_label =QLabel ("Stats")
        stats_label .setStyleSheet ("font-weight: bold; font-size: 14px;")
        layout .addWidget (stats_label )
        ivs_hbox =QHBoxLayout ()
        ivs_label =QLabel ("Talents(IVs):")
        ivs_label .setStyleSheet ("font-weight: bold; font-size: 14px;")
        ivs_hbox .addWidget (ivs_label )
        max_ivs_btn =QPushButton (t ("edit_pals.max_ivs"))
        max_ivs_btn .clicked .connect (self ._max_ivs )
        ivs_hbox .addWidget (max_ivs_btn )
        ivs_hbox .addStretch ()
        layout .addLayout (ivs_hbox )
        ivs_layout =QHBoxLayout ()
        self .ivs_hp_spin =QSpinBox ()
        self .ivs_hp_spin .setRange (0 ,100 )
        self .ivs_hp_spin .setValue (50 )
        ivs_layout .addWidget (QLabel (t ("edit_pals.hp")))
        ivs_layout .addWidget (self .ivs_hp_spin )
        layout .addLayout (ivs_layout )
        souls_label =QLabel (t ("edit_pals.souls"))
        souls_label .setStyleSheet ("font-weight: bold; font-size: 14px;")
        layout .addWidget (souls_label )
        souls_layout =QVBoxLayout ()
        souls_layout .setSpacing (5 )
        max_souls_btn =QPushButton (t ("edit_pals.max_souls"))
        max_souls_btn .clicked .connect (self ._max_souls )
        souls_layout .addWidget (max_souls_btn )
        layout .addLayout (souls_layout )
        layout .addStretch ()
        return panel 
    def _create_tab_left_panel (self ,tab ,tab_name ):
        panel =QWidget ()
        panel .setMinimumWidth (350 )
        layout =QVBoxLayout (panel )
        layout .setContentsMargins (10 ,10 ,10 ,10 )
        layout .setSpacing (10 )
        active_skills_label =QLabel (t ("edit_pals.active_skills")+" (3 max)")
        active_skills_label .setObjectName ("sectionLabel")
        layout .addWidget (active_skills_label )
        tab .active_skills_area =QScrollArea ()
        tab .active_skills_area .setObjectName ("skillsScrollArea")
        tab .active_skills_area .setWidgetResizable (True )
        tab .active_skills_area .setMaximumHeight (200 )
        tab .active_skills_area .setHorizontalScrollBarPolicy (Qt .ScrollBarAlwaysOff )
        tab .active_skills_area .setVerticalScrollBarPolicy (Qt .ScrollBarAlwaysOff )
        tab .active_skills_widget =QWidget ()
        tab .active_skills_grid =QGridLayout (tab .active_skills_widget )
        tab .active_skills_grid .setSpacing (5 )
        tab .active_skills_area .setWidget (tab .active_skills_widget )
        layout .addWidget (tab .active_skills_area )
        tab .active_skill_search =QComboBox ()
        tab .active_skill_search .setObjectName ("editPalsCombo")
        tab .active_skill_search .setEditable (True )
        tab .active_skill_search .setMinimumWidth (200 )
        tab .active_skill_search .setStyleSheet ("QComboBox { combobox-popup: 0; } QComboBox QAbstractItemView { min-height: 200px; max-height: 200px; }")
        tab .active_skill_all_items =sorted (PalFrame ._SKILLMAP .values ())
        for skill_name in tab .active_skill_all_items :
            tab .active_skill_search .addItem (skill_name )
        tab .active_skill_search .currentTextChanged .connect (lambda text ,t =tab :self ._filter_active_skills (text ,t ))
        passive_skills_label =QLabel (t ("edit_pals.passive_skills")+" (4 max)")
        passive_skills_label .setObjectName ("sectionLabel")
        layout .addWidget (passive_skills_label )
        tab .passive_skills_area =QScrollArea ()
        tab .passive_skills_area .setObjectName ("skillsScrollArea")
        tab .passive_skills_area .setWidgetResizable (True )
        tab .passive_skills_area .setMaximumHeight (200 )
        tab .passive_skills_area .setHorizontalScrollBarPolicy (Qt .ScrollBarAlwaysOff )
        tab .passive_skills_area .setVerticalScrollBarPolicy (Qt .ScrollBarAlwaysOff )
        tab .passive_skills_widget =QWidget ()
        tab .passive_skills_grid =QGridLayout (tab .passive_skills_widget )
        tab .passive_skills_grid .setSpacing (5 )
        tab .passive_skills_area .setWidget (tab .passive_skills_widget )
        layout .addWidget (tab .passive_skills_area )
        tab .passive_skill_search =QComboBox ()
        tab .passive_skill_search .setObjectName ("editPalsCombo")
        tab .passive_skill_search .setEditable (True )
        tab .passive_skill_search .setMinimumWidth (200 )
        tab .passive_skill_search .setStyleSheet ("QComboBox { combobox-popup: 0; } QComboBox QAbstractItemView { min-height: 200px; max-height: 200px; }")
        tab .passive_skill_all_items =sorted (PalFrame ._PASSMAP .values ())
        for passive_name in tab .passive_skill_all_items :
            tab .passive_skill_search .addItem (passive_name )
        tab .passive_skill_search .currentTextChanged .connect (lambda text ,t =tab :self ._filter_passive_skills (text ,t ))
        return panel 
    def _create_tab_center_panel (self ,tab ,tab_name ):
        panel =QWidget ()
        layout =QVBoxLayout (panel )
        layout .setContentsMargins (10 ,10 ,10 ,10 )
        layout .addStretch ()
        return panel 
    def _create_tab_right_panel (self ,tab ,tab_name ):
        panel =QWidget ()
        panel .setMinimumWidth (375 )
        scroll_area =QScrollArea ()
        scroll_area .setWidgetResizable (True )
        scroll_area .setHorizontalScrollBarPolicy (Qt .ScrollBarAsNeeded )
        scroll_area .setVerticalScrollBarPolicy (Qt .ScrollBarAsNeeded )
        scroll_widget =QWidget ()
        layout =QVBoxLayout (scroll_widget )
        layout .setContentsMargins (10 ,10 ,10 ,10 )
        layout .setSpacing (10 )
        name_layout =QHBoxLayout ()
        name_layout .addWidget (QLabel (t ("edit_pals.name")))
        tab .pal_name_label =QLabel (t ("edit_pals.no_pal_selected"))
        tab .pal_name_label .setObjectName ("palNameLabel")
        name_layout .addWidget (tab .pal_name_label )
        rename_btn =QPushButton (t ("edit_pals.rename_pal"))
        rename_btn .setObjectName ("editPalsActionButton")
        rename_btn .clicked .connect (self ._rename_pal )
        name_layout .addWidget (rename_btn )
        name_layout .addStretch ()
        layout .addLayout (name_layout )
        main_stats_layout =QHBoxLayout ()
        stats_layout =QHBoxLayout ()
        stats_layout .addWidget (QLabel (t ("edit_pals.stats")))
        max_stats_btn =QPushButton (t ("edit_pals.max_all"))
        max_stats_btn .setObjectName ("editPalsActionButton")
        max_stats_btn .clicked .connect (self ._max_stats )
        stats_layout .addWidget (max_stats_btn )
        main_stats_layout .addLayout (stats_layout )
        gender_layout =QHBoxLayout ()
        gender_layout .addWidget (QLabel (t ("edit_pals.gender")))
        gender_icon_label =QLabel ("♀")
        gender_icon_label .setObjectName ("genderIconLabel")
        gender_icon_label .setStyleSheet ("font-size: 16px; color: #FB7185;")
        tab .gender_icon_label =gender_icon_label 
        gender_layout .addWidget (gender_icon_label )
        swap_gender_btn =QPushButton (t ("edit_pals.gender"))
        swap_gender_btn .setObjectName ("editPalsActionButton")
        swap_gender_btn .clicked .connect (lambda :self ._swap_gender_icon (tab ,gender_icon_label ))
        gender_layout .addWidget (swap_gender_btn )
        main_stats_layout .addLayout (gender_layout )
        rank_layout =QHBoxLayout ()
        rank_layout .addWidget (QLabel (t ("edit_pals.rank")))
        tab .rank_star_buttons =[]
        for i in range (4 ):
            btn =StarButton ("☆")
            btn .setObjectName ("starButton")
            btn .setStyleSheet ("""
                QPushButton {
                    font-size: 14px;
                    color: #FFD700;
                    border: none;
                    background: transparent;
                    padding: 0px;
                    min-width: 20px;
                    max-width: 20px;
                }
                QPushButton:hover {
                    color: #FFA500;
                }
            """)
            btn .clicked .connect (lambda checked ,rank =i +2 ,t =tab :self ._set_rank_from_star (t ,rank ))
            btn .setContextMenuPolicy (Qt .CustomContextMenu )
            btn .customContextMenuRequested .connect (lambda pos ,t =tab :self ._reset_rank_to_zero (t ))
            rank_layout .addWidget (btn )
            tab .rank_star_buttons .append (btn )
        main_stats_layout .addLayout (rank_layout )
        main_stats_layout .addStretch ()
        layout .addLayout (main_stats_layout )
        level_layout =QHBoxLayout ()
        level_layout .addWidget (QLabel (t ("edit_pals.level")))
        tab .level_spin =QSpinBox ()
        tab .level_spin .setObjectName ("editPalsSpin")
        tab .level_spin .setRange (1 ,65 )
        tab .level_spin .setValue (1 )
        level_layout .addWidget (tab .level_spin )
        level_layout .addStretch ()
        layout .addLayout (level_layout )
        talents_group =QGroupBox (t ("edit_pals.talents"))
        talents_group .setObjectName ("editPalsGroup")
        talents_layout_outer =QVBoxLayout (talents_group )
        talents_layout_outer .setContentsMargins (10 ,10 ,10 ,10 )
        talents_layout_outer .setSpacing (5 )
        ivs_hbox =QHBoxLayout ()
        max_ivs_btn =QPushButton (t ("edit_pals.max_ivs"))
        max_ivs_btn .setObjectName ("editPalsActionButton")
        max_ivs_btn .clicked .connect (self ._max_ivs )
        ivs_hbox .addWidget (max_ivs_btn )
        ivs_hbox .addStretch ()
        talents_layout_outer .addLayout (ivs_hbox )
        talents_layout =QVBoxLayout ()
        talents_layout .setSpacing (5 )
        hp_layout =QHBoxLayout ()
        hp_layout .addWidget (QLabel (t ("edit_pals.hp")))
        tab .talent_hp_spin =QSpinBox ()
        tab .talent_hp_spin .setObjectName ("editPalsSpin")
        tab .talent_hp_spin .setRange (0 ,100 )
        tab .talent_hp_spin .setValue (50 )
        hp_layout .addWidget (tab .talent_hp_spin )
        talents_layout .addLayout (hp_layout )
        shot_layout =QHBoxLayout ()
        shot_layout .addWidget (QLabel (t ("edit_pals.attack")))
        tab .talent_shot_spin =QSpinBox ()
        tab .talent_shot_spin .setObjectName ("editPalsSpin")
        tab .talent_shot_spin .setRange (0 ,100 )
        tab .talent_shot_spin .setValue (50 )
        shot_layout .addWidget (tab .talent_shot_spin )
        talents_layout .addLayout (shot_layout )
        defense_layout =QHBoxLayout ()
        defense_layout .addWidget (QLabel (t ("edit_pals.defense")))
        tab .talent_defense_spin =QSpinBox ()
        tab .talent_defense_spin .setObjectName ("editPalsSpin")
        tab .talent_defense_spin .setRange (0 ,100 )
        tab .talent_defense_spin .setValue (50 )
        defense_layout .addWidget (tab .talent_defense_spin )
        talents_layout .addLayout (defense_layout )
        talents_layout_outer .addLayout (talents_layout )
        layout .addWidget (talents_group )
        souls_group =QGroupBox (t ("edit_pals.souls"))
        souls_group .setObjectName ("editPalsGroup")
        souls_layout_outer =QVBoxLayout (souls_group )
        souls_layout_outer .setContentsMargins (10 ,10 ,10 ,10 )
        souls_layout_outer .setSpacing (5 )
        souls_hbox =QHBoxLayout ()
        max_souls_btn =QPushButton (t ("edit_pals.max_souls"))
        max_souls_btn .setObjectName ("editPalsActionButton")
        max_souls_btn .clicked .connect (self ._max_souls )
        souls_hbox .addWidget (max_souls_btn )
        souls_hbox .addStretch ()
        souls_layout_outer .addLayout (souls_hbox )
        souls_layout =QVBoxLayout ()
        souls_layout .setSpacing (5 )
        hp_soul_layout =QHBoxLayout ()
        hp_soul_layout .addWidget (QLabel (t ("edit_pals.hp")))
        tab .rank_hp_spin =QSpinBox ()
        tab .rank_hp_spin .setObjectName ("editPalsSpin")
        tab .rank_hp_spin .setRange (0 ,20 )
        tab .rank_hp_spin .setValue (0 )
        hp_soul_layout .addWidget (tab .rank_hp_spin )
        souls_layout .addLayout (hp_soul_layout )
        attack_soul_layout =QHBoxLayout ()
        attack_soul_layout .addWidget (QLabel (t ("edit_pals.attack")))
        tab .rank_attack_spin =QSpinBox ()
        tab .rank_attack_spin .setObjectName ("editPalsSpin")
        tab .rank_attack_spin .setRange (0 ,20 )
        tab .rank_attack_spin .setValue (0 )
        attack_soul_layout .addWidget (tab .rank_attack_spin )
        souls_layout .addLayout (attack_soul_layout )
        defense_soul_layout =QHBoxLayout ()
        defense_soul_layout .addWidget (QLabel (t ("edit_pals.defense")))
        tab .rank_defense_spin =QSpinBox ()
        tab .rank_defense_spin .setObjectName ("editPalsSpin")
        tab .rank_defense_spin .setRange (0 ,20 )
        tab .rank_defense_spin .setValue (0 )
        defense_soul_layout .addWidget (tab .rank_defense_spin )
        souls_layout .addLayout (defense_soul_layout )
        work_soul_layout =QHBoxLayout ()
        work_soul_layout .addWidget (QLabel (t ("edit_pals.craft_speed")+":"))
        tab .rank_craftspeed_spin =QSpinBox ()
        tab .rank_craftspeed_spin .setObjectName ("editPalsSpin")
        tab .rank_craftspeed_spin .setRange (0 ,20 )
        tab .rank_craftspeed_spin .setValue (0 )
        work_soul_layout .addWidget (tab .rank_craftspeed_spin )
        souls_layout .addLayout (work_soul_layout )
        souls_layout_outer .addLayout (souls_layout )
        layout .addWidget (souls_group )
        layout .addStretch ()
        scroll_area .setWidget (scroll_widget )
        panel_layout =QVBoxLayout (panel )
        panel_layout .addWidget (scroll_area )
        tab .level_spin .valueChanged .connect (lambda v :self ._update_level (tab ,v ))
        tab .talent_hp_spin .valueChanged .connect (lambda v :self ._update_talent (tab ,'hp',v ))
        tab .talent_shot_spin .valueChanged .connect (lambda v :self ._update_talent (tab ,'shot',v ))
        tab .talent_defense_spin .valueChanged .connect (lambda v :self ._update_talent (tab ,'defense',v ))
        tab .rank_hp_spin .valueChanged .connect (lambda v :self ._update_soul (tab ,'hp',v ))
        tab .rank_attack_spin .valueChanged .connect (lambda v :self ._update_soul (tab ,'attack',v ))
        tab .rank_defense_spin .valueChanged .connect (lambda v :self ._update_soul (tab ,'defense',v ))
        tab .rank_craftspeed_spin .valueChanged .connect (lambda v :self ._update_soul (tab ,'craftspeed',v ))
        return panel 
    def _load_pals (self ):
        if not constants .loaded_level_json :
            return 
        PalFrame ._load_maps ()
        cmap =constants .loaded_level_json ['properties']['worldSaveData']['value']['CharacterSaveParameterMap']['value']
        party_pals =[]
        palbox_pals =[]
        for item in cmap :
            rawf =item .get ('value',{}).get ('RawData',{}).get ('value',{})
            raw =rawf .get ('object',{}).get ('SaveParameter',{}).get ('value',{})
            if 'IsPlayer'in raw :
                continue 
            owner_uid =raw .get ('OwnerPlayerUId',{}).get ('value')
            if not owner_uid or str (owner_uid ).replace ('-','').lower ()!=self .player_uid .replace ('-','').lower ():
                continue 
            slot_id =raw .get ('SlotId',{}).get ('value',{}).get ('ContainerId',{}).get ('value',{}).get ('ID',{}).get ('value')
            if slot_id and str (slot_id ).lower ()==str (self .party_container ).lower ():
                party_pals .append (item )
            elif slot_id and str (slot_id ).lower ()==str (self .palbox_container ).lower ():
                palbox_pals .append (item )
        self ._populate_tab (self .party_tab ,party_pals ,t ("edit_pals.party"))
        self ._populate_tab (self .palbox_tab ,palbox_pals ,t ("edit_pals.palbox"))
        total_slots =len (party_pals )+len (palbox_pals )
        if total_slots >=960 :
            self .party_tab .slot_label .setStyleSheet ("color: red; font-weight: bold;")
            self .palbox_tab .slot_label .setStyleSheet ("color: red; font-weight: bold;")
    def _populate_tab (self ,tab ,pals ,tab_name ):
        tab .pal_data =pals 
        max_slots =tab .max_slots 
        if tab_name =="DPS"and hasattr (tab ,'widget_list'):
            pal_dict ={}
            for pal_item in pals :
                try :
                    slot_index =pal_item ['index']
                    pal_dict [slot_index ]=pal_item 
                except :
                    pass 
            for i in range (max_slots ):
                pal_item =pal_dict .get (i ,None )
                widget =tab .widget_list [i ]
                widget .pal_data =pal_item 
                widget ._setup_ui ()
        else :
            if hasattr (tab .pal_layout ,'count'):
                for i in reversed (range (tab .pal_layout .count ())):
                    widget =tab .pal_layout .itemAt (i ).widget ()
                    if widget :
                        widget .setParent (None )
            pal_dict ={}
            for pal_item in pals :
                try :
                    raw =pal_item ['value']['RawData']['value']['object']['SaveParameter']['value']
                    slot_index =raw .get ('SlotId',{}).get ('value',{}).get ('SlotIndex',{}).get ('value',0 )
                    pal_dict [slot_index ]=pal_item 
                except :
                    pass 
            for i in range (max_slots ):
                pal_item =pal_dict .get (i ,None )
                pal_widget =PalIcon (pal_item ,tab =tab ,slot_index =i ,tab_name =tab_name )
                slot_idx =i 
                pal_widget .clicked .connect (lambda idx =slot_idx ,t =tab ,tn =tab_name :self ._on_pal_widget_selected (idx ,t ,tn ))
                pal_widget .rightClicked .connect (self ._on_pal_right_click )
                row =i //6 
                col =i %6 
                tab .pal_layout .addWidget (pal_widget ,row ,col )
        self ._update_tab_pal_display (tab ,-1 )
        tab .slot_label .setText (t ("edit_pals.slot_count",current =len (pals ),max =max_slots ))
    def _on_party_table_selection (self ,tab ):
        selected_items =tab .pal_layout .selectedItems ()
        if selected_items :
            pal_index =selected_items [0 ].row ()
            tab .selected_pal_index =pal_index 
            if 0 <=pal_index <len (tab .pal_data ):
                self ._update_tab_pal_display (tab ,pal_index )
    def _on_pal_widget_selected (self ,slot_index ,tab ,tab_name ):
        widget =None 
        for i in range (tab .pal_layout .count ()):
            w =tab .pal_layout .itemAt (i ).widget ()
            if w and hasattr (w ,'slot_index')and w .slot_index ==slot_index :
                widget =w 
                break 
        if widget and widget .pal_data :
            try :
                tab .selected_pal_index =tab .pal_data .index (widget .pal_data )
                pal_item =widget .pal_data 
            except ValueError :
                tab .selected_pal_index =-1 
                pal_item =None 
        else :
            tab .selected_pal_index =-1 
            pal_item =None 
        for i in range (tab .pal_layout .count ()):
            widget =tab .pal_layout .itemAt (i ).widget ()
            if hasattr (widget ,'set_selected'):
                widget .set_selected (i ==slot_index )
        self ._update_tab_pal_display (tab ,tab .selected_pal_index )
        if pal_item :
            if 'data'in pal_item :
                raw =pal_item ['data']
            else :
                raw =pal_item ['value']['RawData']['value']['object']['SaveParameter']['value']
            cid =extract_value (raw ,'CharacterID','')
            nick =extract_value (raw ,'NickName','')
            pal_name =PalFrame ._NAMEMAP .get (cid .lower (),cid )
            if nick :
                pal_name =f"{pal_name } ({nick })"
            tab .pal_name_label .setText (pal_name )
        else :
            tab .pal_name_label .setText (t ("edit_pals.no_pal_selected"))
    def _on_pal_right_click (self ,slot_index ,tab_name ,action ):
        if tab_name ==t ("edit_pals.party"):
            tab =self .party_tab 
        elif tab_name ==t ("edit_pals.palbox"):
            tab =self .palbox_tab 
        elif tab_name =="DPS":
            tab =self .dps_tab 
        else :
            return 
        pal_dict ={}
        for pal_item in tab .pal_data :
            try :
                if tab_name =="DPS":
                    slot_idx =pal_item ['index']
                else :
                    raw =pal_item ['value']['RawData']['value']['object']['SaveParameter']['value']
                    slot_idx =raw .get ('SlotId',{}).get ('value',{}).get ('SlotIndex',{}).get ('value',0 )
                pal_dict [slot_idx ]=pal_item 
            except :
                pass 
        has_pal =slot_index in pal_dict 
        if has_pal :
            pal_item =pal_dict [slot_index ]
            index =tab .pal_data .index (pal_item )
            if 'data'in pal_item :
                raw =pal_item ['data']
            else :
                raw =pal_item ['value']['RawData']['value']['object']['SaveParameter']['value']
            if action =="delete":
                if tab_name =="DPS":
                    self ._delete_dps_pal (tab ,slot_index )
                else :
                    if not hasattr (self ,'_pending_deletions'):
                        self ._pending_deletions =[]
                    self ._pending_deletions .append ({
                    'pal_item':pal_item ,
                    'tab':tab ,
                    'tab_name':tab_name ,
                    'slot_index':slot_index 
                    })
                    tab .pal_data .remove (pal_item )
                    self ._populate_tab (tab ,tab .pal_data ,tab_name )
                    tab .selected_pal_index =-1 
                    self ._update_tab_pal_display (tab ,-1 )
                    tab .pal_name_label .setText (t ("edit_pals.no_pal_selected"))
            elif action =="rename":
                current_nick =extract_value (raw ,'NickName','')
                new_nick ,ok =QInputDialog .getText (self ,t ("edit_pals.rename_pal"),"Enter new nickname:",text =current_nick )
                if ok and new_nick !=current_nick :
                    raw ['NickName']={'id':None ,'type':'StrProperty','value':new_nick }
                    self ._update_tab_pal_display (tab ,index )
            elif action =="swap_gender":
                gender_data =extract_value (raw ,'Gender',{})
                if isinstance (gender_data ,dict )and 'value'in gender_data :
                    current_gender =gender_data ['value']
                    if current_gender =='EPalGenderType::Male':
                        new_gender ='EPalGenderType::Female'
                    else :
                        new_gender ='EPalGenderType::Male'
                    raw ['Gender']={
                    'id':None ,
                    'type':'EnumProperty',
                    'value':{
                    'type':'EPalGenderType',
                    'value':new_gender 
                    }
                    }
                    self ._update_tab_pal_display (tab ,index )
            elif action =="increase_rank":
                current_rank =extract_value (raw ,'Rank',1 )
                new_rank =min (current_rank +1 ,5 )
                raw ['Rank']={'id':None ,'type':'ByteProperty','value':{'type':'None','value':new_rank }}
                self ._update_tab_pal_display (tab ,index )
            elif action =="max_stats":
                raw ['Level']={'id':None ,'type':'ByteProperty','value':{'type':'None','value':65 }}
                raw ['Rank']={'id':None ,'type':'ByteProperty','value':{'type':'None','value':5 }}
                raw ['Talent_HP']={'id':None ,'type':'ByteProperty','value':{'type':'None','value':100 }}
                raw ['Talent_Shot']={'id':None ,'type':'ByteProperty','value':{'type':'None','value':100 }}
                raw ['Talent_Defense']={'id':None ,'type':'ByteProperty','value':{'type':'None','value':100 }}
                raw ['Rank_HP']={'id':None ,'type':'ByteProperty','value':{'type':'None','value':20 }}
                raw ['Rank_Attack']={'id':None ,'type':'ByteProperty','value':{'type':'None','value':20 }}
                raw ['Rank_Defence']={'id':None ,'type':'ByteProperty','value':{'type':'None','value':20 }}
                raw ['Rank_CraftSpeed']={'id':None ,'type':'ByteProperty','value':{'type':'None','value':20 }}
                self ._update_tab_pal_display (tab ,index )
            elif action =="max_ivs":
                raw ['Talent_HP']={'id':None ,'type':'ByteProperty','value':{'type':'None','value':100 }}
                raw ['Talent_Shot']={'id':None ,'type':'ByteProperty','value':{'type':'None','value':100 }}
                raw ['Talent_Defense']={'id':None ,'type':'ByteProperty','value':{'type':'None','value':100 }}
                self ._update_tab_pal_display (tab ,index )
            elif action =="max_souls":
                raw ['Rank_HP']={'id':None ,'type':'ByteProperty','value':{'type':'None','value':20 }}
                raw ['Rank_Attack']={'id':None ,'type':'ByteProperty','value':{'type':'None','value':20 }}
                raw ['Rank_Defence']={'id':None ,'type':'ByteProperty','value':{'type':'None','value':20 }}
                raw ['Rank_CraftSpeed']={'id':None ,'type':'ByteProperty','value':{'type':'None','value':20 }}
                self ._update_tab_pal_display (tab ,index )
        else :
            if action =="add_new":
                pal_data =self ._show_create_pal_dialog (slot_index ,tab_name )
                if pal_data :
                    if not hasattr (self ,'_pending_additions'):
                        self ._pending_additions =[]
                    self ._pending_additions .append (pal_data )
                    cmap =constants .loaded_level_json ['properties']['worldSaveData']['value']['CharacterSaveParameterMap']['value']
                    cmap .append (pal_data ['pal_item'])
                    if tab_name =="DPS":
                        self ._add_dps_pal (tab ,slot_index ,pal_data ['character_id'],pal_data ['nickname'])
                    else :
                        tab .pal_data .append (pal_data ['pal_item'])
                        self ._populate_tab (tab ,tab .pal_data ,tab_name )
                        new_index =len (tab .pal_data )-1 
                        tab .selected_pal_index =new_index 
                        for i in range (tab .pal_layout .count ()):
                            widget =tab .pal_layout .itemAt (i ).widget ()
                            if widget and hasattr (widget ,'slot_index')and widget .slot_index ==slot_index :
                                widget .set_selected (True )
                                break 
                        self ._update_tab_pal_display (tab ,new_index )
    def _on_tab_pal_selected (self ,index ,tab_name ):
        if tab_name ==t ("edit_pals.party"):
            tab =self .party_tab 
        elif tab_name ==t ("edit_pals.palbox"):
            tab =self .palbox_tab 
        elif tab_name =="DPS":
            tab =self .dps_tab 
        else :
            return 
        if 0 <=index <len (tab .pal_data ):
            self ._update_tab_pal_display (tab ,index )
    def _update_tab_pal_display (self ,tab ,index ):
        if index <0 or index >=len (tab .pal_data ):
            if hasattr (tab ,'level_spin'):
                tab .level_spin .setValue (0 )
                tab .talent_hp_spin .setValue (0 )
                tab .talent_shot_spin .setValue (0 )
                tab .talent_defense_spin .setValue (0 )
                tab .rank_hp_spin .setValue (0 )
                tab .rank_attack_spin .setValue (0 )
                tab .rank_defense_spin .setValue (0 )
                tab .rank_craftspeed_spin .setValue (0 )
            tab .pal_name_label .setText (t ("edit_pals.no_pal_selected"))
            if hasattr (tab ,'rank_star_buttons'):
                for btn in tab .rank_star_buttons :
                    btn .setText ("☆")
            if hasattr (tab ,'gender_icon_label'):
                tab .gender_icon_label .setText ("♀")
                tab .gender_icon_label .setStyleSheet ("font-size: 16px; color: #FB7185;")
            tab .current_active_skills =[]
            tab .current_passive_skills =[]
            self ._update_tab_skills_display (tab ,[],[])
            tab .update ()
            return 
        pal_item =tab .pal_data [index ]
        try :
            if 'data'in pal_item :
                raw =pal_item ['data']
            else :
                raw =pal_item ['value']['RawData']['value']['object']['SaveParameter']['value']
            level =extract_value (raw ,'Level',1 )
            cid =extract_value (raw ,'CharacterID','')
            character_key =format_character_key (cid )
            talent_hp =extract_value (raw ,'Talent_HP',0 )
            talent_shot =extract_value (raw ,'Talent_Shot',0 )
            talent_defense =extract_value (raw ,'Talent_Defense',0 )
            rank_hp =extract_value (raw ,'Rank_HP',0 )
            rank_attack =extract_value (raw ,'Rank_Attack',0 )
            rank_defense =extract_value (raw ,'Rank_Defence',0 )
            is_boss =cid .upper ().startswith ('BOSS_')or extract_value (raw ,'IsRarePal',False )
            is_lucky =extract_value (raw ,'IsRarePal',False )
            passive_skill_data =raw .get ('PassiveSkillList',{})
            if isinstance (passive_skill_data ,dict ):
                p_list =passive_skill_data .get ('value',{}).get ('values',[])
            elif isinstance (passive_skill_data ,list ):
                p_list =passive_skill_data 
            else :
                p_list =[]
            equip_waza_data =raw .get ('EquipWaza',{})
            if isinstance (equip_waza_data ,dict ):
                e_list =equip_waza_data .get ('value',{}).get ('values',[])
            elif isinstance (equip_waza_data ,list ):
                e_list =equip_waza_data 
            else :
                e_list =[]
            hp =extract_value (raw ,'Hp',0 )
            atk =extract_value (raw ,'Attack',0 )
            defense_val =extract_value (raw ,'Defense',0 )
            gender_data =extract_value (raw ,'Gender',{})
            if isinstance (gender_data ,dict )and 'value'in gender_data :
                gender =gender_data ['value']
            elif isinstance (gender_data ,str ):
                gender =gender_data 
            else :
                gender ='EPalGenderType::Female'
            rank =extract_value (raw ,'Rank',1 )
            if hasattr (tab ,'level_spin'):
                tab .level_spin .setValue (level )
            if hasattr (tab ,'talent_hp_spin'):
                tab .talent_hp_spin .setValue (talent_hp )
                tab .talent_shot_spin .setValue (talent_shot )
                tab .talent_defense_spin .setValue (talent_defense )
                tab .rank_hp_spin .setValue (rank_hp )
                tab .rank_attack_spin .setValue (rank_attack )
                tab .rank_defense_spin .setValue (rank_defense )
                tab .rank_craftspeed_spin .setValue (extract_value (raw ,'Rank_CraftSpeed',0 ))
            if hasattr (tab ,'rank_star_buttons'):
                for i in range (4 ):
                    if i <rank -1 :
                        tab .rank_star_buttons [i ].setText ("★")
                    else :
                        tab .rank_star_buttons [i ].setText ("☆")
            if hasattr (tab ,'gender_combo'):
                if gender =='EPalGenderType::Male':
                    tab .gender_combo .setCurrentIndex (0 )
                else :
                    tab .gender_combo .setCurrentIndex (1 )
            if hasattr (tab ,'gender_icon_label'):
                if gender =='EPalGenderType::Male':
                    tab .gender_icon_label .setText ("♂")
                    tab .gender_icon_label .setStyleSheet ("font-size: 16px; color: #7DD3FC;")
                else :
                    tab .gender_icon_label .setText ("♀")
                    tab .gender_icon_label .setStyleSheet ("font-size: 16px; color: #FB7185;")
            moves =[None ]*3 
            for i in range (min (3 ,len (e_list ))):
                if e_list [i ]:
                    w_clean =e_list [i ].split ('::')[-1 ].lower ()
                    move_name =PalFrame ._SKILLMAP .get (w_clean ,"Unknown Skill")
                    moves [i ]=move_name 
            passives =[None ]*4 
            for i in range (min (4 ,len (p_list ))):
                if p_list [i ]:
                    p_clean =p_list [i ].lower ()
                    passive_name =PalFrame ._PASSMAP .get (p_clean ,"Unknown Passive")
                    passives [i ]=passive_name 
            tab .current_active_skills =moves .copy ()
            tab .current_passive_skills =passives .copy ()
            self ._update_tab_skills_display (tab ,moves ,passives )
        except Exception as e :
            print (f"Error updating display: {e }")
    def _update_tab_skills_display (self ,tab ,moves ,passives ):
        for i in reversed (range (tab .active_skills_grid .count ())):
            item =tab .active_skills_grid .itemAt (i )
            if item .widget ():
                item .widget ().setParent (None )
        for i in reversed (range (tab .passive_skills_grid .count ())):
            item =tab .passive_skills_grid .itemAt (i )
            if item .widget ():
                item .widget ().setParent (None )
        for i in range (3 ):
            if i ==0 :
                row ,col =0 ,0 
            elif i ==1 :
                row ,col =0 ,1 
            elif i ==2 :
                row ,col =1 ,0 
            skill_button =QPushButton ()
            skill_button .setObjectName ("skillButton")
            skill_button .setMinimumWidth (150 )
            skill_button .setStyleSheet ("""
                QPushButton {
                    text-align: left;
                    padding: 5px;
                    border: 1px solid #666;
                    border-radius: 3px;
                    background-color: #333;
                    color: #fff;
                    font-weight: normal;
                }
                QPushButton:hover {
                    background-color: #555;
                    border: 1px solid #888;
                }
                QPushButton:pressed {
                    background-color: #222;
                }
            """)
            if i <len (moves )and moves [i ]is not None :
                skill_button .setText (moves [i ])
            else :
                skill_button .setText (t ("edit_pals.clear_skill"))
            skill_button .clicked .connect (lambda checked ,t =tab ,idx =i ,typ ="active":self ._open_skill_select_dialog (t ,idx ,typ ))
            tab .active_skills_grid .addWidget (skill_button ,row ,col )
        for i in range (4 ):
            if i ==0 :
                row ,col =0 ,0 
            elif i ==1 :
                row ,col =0 ,1 
            elif i ==2 :
                row ,col =1 ,0 
            elif i ==3 :
                row ,col =1 ,1 
            skill_button =QPushButton ()
            skill_button .setObjectName ("skillButton")
            skill_button .setMinimumWidth (150 )
            skill_button .setStyleSheet ("""
                QPushButton {
                    text-align: left;
                    padding: 5px;
                    border: 1px solid #666;
                    border-radius: 3px;
                    background-color: #333;
                    color: #fff;
                    font-weight: normal;
                }
                QPushButton:hover {
                    background-color: #555;
                    border: 1px solid #888;
                }
                QPushButton:pressed {
                    background-color: #222;
                }
            """)
            if i <len (passives )and passives [i ]is not None :
                skill_button .setText (passives [i ])
            else :
                skill_button .setText (t ("edit_pals.clear_skill"))
            skill_button .clicked .connect (lambda checked ,t =tab ,idx =i ,typ ="passive":self ._open_skill_select_dialog (t ,idx ,typ ))
            tab .passive_skills_grid .addWidget (skill_button ,row ,col )
    def _add_active_skill (self ,tab ,tab_name ):
        skill_name =tab .active_skill_combo .currentText ()
        if skill_name =="Select Skill to Add"or not skill_name :
            return 
        pal_index =getattr (tab ,'selected_pal_index',-1 )
        if pal_index <0 or pal_index >=len (tab .pal_data ):
            return 
        pal_item =tab .pal_data [pal_index ]
        try :
            if 'data'in pal_item :
                raw =pal_item ['data']
            else :
                raw =pal_item ['value']['RawData']['value']['object']['SaveParameter']['value']
            e_list =raw .get ('EquipWaza',{}).get ('value',{}).get ('values',[])
            print (f"DEBUG: Current EquipWaza list: {e_list }")
            if sum (1 for w in e_list if w )>=3 :
                QMessageBox .warning (self ,"Limit Reached","Maximum 3 active skills allowed.")
                return 
        except :
            pass 
        skill_asset =None 
        for asset ,name in PalFrame ._SKILLMAP .items ():
            if name ==skill_name :
                skill_asset =asset 
                break 
        if not skill_asset :
            return 
        pal_index =getattr (tab ,'selected_pal_index',-1 )
        if pal_index <0 or pal_index >=len (tab .pal_data ):
            return 
        pal_item =tab .pal_data [pal_index ]
        try :
            if 'data'in pal_item :
                raw =pal_item ['data']
            else :
                raw =pal_item ['value']['RawData']['value']['object']['SaveParameter']['value']
            e_list =raw .get ('EquipWaza',{}).get ('value',{}).get ('values',[])
            skill_full =f"EPalWazaID::{skill_asset }"
            print (f"DEBUG: Adding skill_full: {skill_full }")
            if skill_full not in e_list :
                e_list .append (skill_full )
                raw ['EquipWaza']['value']['values']=e_list 
                print (f"DEBUG: Updated EquipWaza list: {e_list }")
            self ._update_tab_pal_display (tab ,pal_index )
        except Exception as e :
            print (f"Error adding active skill: {e }")
    def _add_passive_skill (self ,tab ,tab_name ):
        skill_name =tab .passive_skill_combo .currentText ()
        if skill_name =="Select Passive to Add"or not skill_name :
            return 
        pal_index =getattr (tab ,'selected_pal_index',-1 )
        if pal_index <0 or pal_index >=len (tab .pal_data ):
            return 
        pal_item =tab .pal_data [pal_index ]
        try :
            if 'data'in pal_item :
                raw =pal_item ['data']
            else :
                raw =pal_item ['value']['RawData']['value']['object']['SaveParameter']['value']
            p_list =raw .get ('PassiveSkillList',{}).get ('value',{}).get ('values',[])
            if sum (1 for p in p_list if p )>=4 :
                QMessageBox .warning (self ,"Limit Reached","Maximum 4 passive skills allowed.")
                return 
        except :
            pass 
        skill_asset =None 
        for asset ,name in PalFrame ._PASSMAP .items ():
            if name ==skill_name :
                skill_asset =asset 
                break 
        if not skill_asset :
            return 
        pal_index =getattr (tab ,'selected_pal_index',-1 )
        if pal_index <0 or pal_index >=len (tab .pal_data ):
            return 
        pal_item =tab .pal_data [pal_index ]
        try :
            if 'data'in pal_item :
                raw =pal_item ['data']
            else :
                raw =pal_item ['value']['RawData']['value']['object']['SaveParameter']['value']
            p_list =raw .get ('PassiveSkillList',{}).get ('value',{}).get ('values',[])
            if skill_asset not in p_list :
                p_list .append (skill_asset )
                raw ['PassiveSkillList']['value']['values']=p_list 
            self ._update_tab_pal_display (tab ,pal_index )
        except Exception as e :
            print (f"Error adding passive skill: {e }")
    def _remove_skill (self ,skill_index ,tab ,skill_type ):
        pal_index =getattr (tab ,'selected_pal_index',-1 )
        if pal_index <0 or pal_index >=len (tab .pal_data ):
            return 
        pal_item =tab .pal_data [pal_index ]
        try :
            if 'data'in pal_item :
                raw =pal_item ['data']
            else :
                raw =pal_item ['value']['RawData']['value']['object']['SaveParameter']['value']
            if skill_type =="active":
                e_list =raw .get ('EquipWaza',{}).get ('value',{}).get ('values',[])
                if hasattr (tab ,'active_valid_indices')and 0 <=skill_index <len (tab .active_valid_indices ):
                    idx =tab .active_valid_indices [skill_index ]
                    e_list [idx ]=""
                    raw ['EquipWaza']['value']['values']=e_list 
            elif skill_type =="passive":
                p_list =raw .get ('PassiveSkillList',{}).get ('value',{}).get ('values',[])
                if hasattr (tab ,'passive_valid_indices')and 0 <=skill_index <len (tab .passive_valid_indices ):
                    idx =tab .passive_valid_indices [skill_index ]
                    p_list [idx ]=""
                    raw ['PassiveSkillList']['value']['values']=p_list 
            self ._update_tab_pal_display (tab ,pal_index )
        except Exception as e :
            print (f"Error removing skill: {e }")
    def _filter_skills (self ,text ,tab ,skill_type ):
        if skill_type =="active":
            combo =tab .active_skill_combo 
            all_items =tab .active_skill_all_items 
        elif skill_type =="passive":
            combo =tab .passive_skill_combo 
            all_items =tab .passive_skill_all_items 
        else :
            return 
        combo .clear ()
        if not text :
            for item in all_items :
                combo .addItem (item )
        else :
            combo .addItem (all_items [0 ])
            for item in all_items [1 :]:
                if text .lower ()in item .lower ():
                    combo .addItem (item )
    def _filter_active_skills (self ,text ,tab ):
        combo =tab .active_skill_combo 
        all_items =tab .active_skill_all_items 
        combo .clear ()
        if not text :
            combo .addItem ("Select Skill to Add")
            for item in all_items :
                combo .addItem (item )
        else :
            combo .addItem ("Select Skill to Add")
            for item in all_items :
                if text .lower ()in item .lower ():
                    combo .addItem (item )
    def _filter_passive_skills (self ,text ,tab ):
        combo =tab .passive_skill_combo 
        all_items =tab .passive_skill_all_items 
        combo .clear ()
        if not text :
            for item in all_items :
                combo .addItem (item )
        else :
            for item in all_items :
                if text .lower ()in item .lower ():
                    combo .addItem (item )
    def _update_skill_slot_from_combo (self ,tab ,combo ,slot_index ,skill_type ):
        skill_name =combo .currentText ()
        if skill_name ==t ("edit_pals.clear_skill"):
            skill_name =""
        elif skill_type =="active"and skill_name not in PalFrame ._SKILLMAP .values ():
            return 
        elif skill_type =="passive"and skill_name not in PalFrame ._PASSMAP .values ():
            return 
        pal_index =getattr (tab ,'selected_pal_index',-1 )
        if pal_index <0 or pal_index >=len (tab .pal_data ):
            return 
        pal_item =tab .pal_data [pal_index ]
        try :
            if 'data'in pal_item :
                raw =pal_item ['data']
            else :
                raw =pal_item ['value']['RawData']['value']['object']['SaveParameter']['value']
            if skill_type =="active":
                e_list =raw .get ('EquipWaza',{}).get ('value',{}).get ('values',[])
                skill_asset =None 
                if skill_name :
                    for asset ,name in PalFrame ._SKILLMAP .items ():
                        if name ==skill_name :
                            skill_asset =asset 
                            break 
                if skill_asset :
                    skill_full =f"EPalWazaID::{skill_asset }"
                else :
                    skill_full =""
                while len (e_list )<=slot_index :
                    e_list .append ("")
                e_list [slot_index ]=skill_full 
                raw ['EquipWaza']['value']['values']=e_list 
            elif skill_type =="passive":
                p_list =raw .get ('PassiveSkillList',{}).get ('value',{}).get ('values',[])
                passive_asset =None 
                if skill_name :
                    for asset ,name in PalFrame ._PASSMAP .items ():
                        if name ==skill_name :
                            passive_asset =asset 
                            break 
                while len (p_list )<=slot_index :
                    p_list .append ("")
                p_list [slot_index ]=passive_asset if passive_asset else ""
                raw ['PassiveSkillList']['value']['values']=p_list 
            self ._update_tab_pal_display (tab ,pal_index )
        except Exception as e :
            print (f"Error updating skill slot: {e }")
    def _start_skill_filter (self ,combo ,skill_type ):
        self .current_filter_combo =combo 
        self .current_filter_skill_type =skill_type 
        self .skill_filter_timer .start (300 )
    def _open_skill_select_dialog (self ,tab ,slot_index ,skill_type ):
        dialog =QDialog (self )
        dialog .setWindowTitle (t ("edit_pals.select_skill"))
        dialog .setModal (True )
        dialog .setMinimumSize (400 ,500 )
        layout =QVBoxLayout (dialog )
        layout .setContentsMargins (10 ,10 ,10 ,10 )
        layout .setSpacing (10 )
        search_label =QLabel ("Search:")
        layout .addWidget (search_label )
        search_edit =QLineEdit ()
        search_edit .setPlaceholderText ("Type to filter skills...")
        layout .addWidget (search_edit )
        list_label =QLabel (t ("edit_pals.available_skills"))
        layout .addWidget (list_label )
        skill_list =QListWidget ()
        skill_list .setMinimumHeight (400 )
        layout .addWidget (skill_list )
        button_layout =QHBoxLayout ()
        button_layout .addStretch ()
        ok_btn =QPushButton ("OK")
        ok_btn .clicked .connect (lambda :select_skill ())
        button_layout .addWidget (ok_btn )
        cancel_btn =QPushButton (t ("edit_pals.cancel"))
        cancel_btn .clicked .connect (dialog .reject )
        button_layout .addWidget (cancel_btn )
        layout .addLayout (button_layout )
        all_skills =[t ("edit_pals.clear_skill")]
        if skill_type =="active":
            all_skills .extend (sorted (PalFrame ._SKILLMAP .values ()))
        elif skill_type =="passive":
            all_skills .extend (sorted (PalFrame ._PASSMAP .values ()))
        for skill_name in all_skills :
            skill_list .addItem (skill_name )
        def filter_skills ():
            text =search_edit .text ().lower ()
            for i in range (skill_list .count ()):
                item =skill_list .item (i )
                item .setHidden (text not in item .text ().lower ())
        search_edit .textChanged .connect (filter_skills )
        def select_skill ():
            current_item =skill_list .currentItem ()
            if current_item :
                skill_name =current_item .text ()
                if skill_name and skill_name !=t ("edit_pals.clear_skill"):
                    current_skills =tab .current_active_skills if skill_type =="active"else tab .current_passive_skills 
                    if skill_name in current_skills and current_skills [slot_index ]!=skill_name :
                        QMessageBox .warning (dialog ,"Duplicate Skill",f"This pal already has the skill '{skill_name }'. Please choose a different skill.")
                        return 
                self ._update_skill_slot (tab ,slot_index ,skill_name ,skill_type )
                dialog .accept ()
        skill_list .itemDoubleClicked .connect (lambda :select_skill ())
        if dialog .exec ()==QDialog .Accepted :
            select_skill ()
    def _update_skill_slot (self ,tab ,slot_index ,skill_name ,skill_type ):
        if skill_name ==t ("edit_pals.clear_skill"):
            skill_name =""
        pal_index =getattr (tab ,'selected_pal_index',-1 )
        if pal_index <0 or pal_index >=len (tab .pal_data ):
            return 
        pal_item =tab .pal_data [pal_index ]
        try :
            if 'data'in pal_item :
                raw =pal_item ['data']
            else :
                raw =pal_item ['value']['RawData']['value']['object']['SaveParameter']['value']
            if skill_type =="active":
                e_list =raw .get ('EquipWaza',{}).get ('value',{}).get ('values',[])
                skill_asset =None 
                if skill_name :
                    for asset ,name in PalFrame ._SKILLMAP .items ():
                        if name ==skill_name :
                            skill_asset =asset 
                            break 
                if skill_asset :
                    skill_full =f"EPalWazaID::{skill_asset }"
                else :
                    skill_full =""
                while len (e_list )<=slot_index :
                    e_list .append ("")
                e_list [slot_index ]=skill_full 
                raw ['EquipWaza']['value']['values']=e_list 
            elif skill_type =="passive":
                p_list =raw .get ('PassiveSkillList',{}).get ('value',{}).get ('values',[])
                passive_asset =None 
                if skill_name :
                    for asset ,name in PalFrame ._PASSMAP .items ():
                        if name ==skill_name :
                            passive_asset =asset 
                            break 
                while len (p_list )<=slot_index :
                    p_list .append ("")
                p_list [slot_index ]=passive_asset if passive_asset else ""
                raw ['PassiveSkillList']['value']['values']=p_list 
            self ._update_tab_pal_display (tab ,pal_index )
        except Exception as e :
            print (f"Error updating skill slot: {e }")
    def _do_filter_skills (self ):
        if self .current_filter_combo and self .current_filter_skill_type :
            text =self .current_filter_combo .currentText ()
            self ._filter_skill_dropdown (text ,self .current_filter_combo ,self .current_filter_skill_type )
    def _filter_skill_dropdown (self ,text ,combo ,skill_type ):
        if skill_type =="active":
            all_skills =[t ("edit_pals.clear_skill")]+sorted (PalFrame ._SKILLMAP .values ())
        elif skill_type =="passive":
            all_skills =[t ("edit_pals.clear_skill")]+sorted (PalFrame ._PASSMAP .values ())
        else :
            return 
        combo .clear ()
        if not text :
            for skill_name in all_skills [:50 ]:
                combo .addItem (skill_name )
            return 
        combo .addItem (t ("edit_pals.clear_skill"))
        count =0 
        for skill_name in all_skills [1 :]:
            if text .lower ()in skill_name .lower ():
                combo .addItem (skill_name )
                count +=1 
                if count >=50 :
                    break 
    def _populate_pal_selector (self ):
        self .pal_selector .clear ()
        if self .all_pals :
            for pal_item in self .all_pals :
                try :
                    raw =pal_item ['value']['RawData']['value']['object']['SaveParameter']['value']
                    cid =extract_value (raw ,'CharacterID','')
                    nick =extract_value (raw ,'NickName','')
                    pal_name =PalFrame ._NAMEMAP .get (cid .lower (),cid )
                    if nick :
                        pal_name =f"{pal_name } ({nick })"
                    self .pal_selector .addItem (pal_name )
                except Exception as e :
                    print (f"Error populating dropdown: {e }")
                    self .pal_selector .addItem ("Unknown Pal")
            self ._update_pal_display (0 )
    def _on_pal_selected (self ,index ):
        if 0 <=index <len (self .all_pals ):
            self ._update_pal_display (index )
    def _update_pal_display (self ,index ):
        pal_item =self .all_pals [index ]
        try :
            raw =pal_item ['value']['RawData']['value']['object']['SaveParameter']['value']
            level =extract_value (raw ,'Level',1 )
            cid =extract_value (raw ,'CharacterID','')
            character_key =format_character_key (cid )
            talent_hp =extract_value (raw ,'Talent_HP',0 )
            talent_shot =extract_value (raw ,'Talent_Shot',0 )
            talent_defense =extract_value (raw ,'Talent_Defense',0 )
            rank_hp =extract_value (raw ,'Rank_HP',0 )
            rank_attack =extract_value (raw ,'Rank_Attack',0 )
            rank_defense =extract_value (raw ,'Rank_Defence',0 )
            is_boss =cid .upper ().startswith ('BOSS_')or extract_value (raw ,'IsRarePal',False )
            is_lucky =extract_value (raw ,'IsRarePal',False )
            hp =extract_value (raw ,'Hp',0 )
            atk =extract_value (raw ,'Attack',0 )
            defense =extract_value (raw ,'Defense',0 )
            passive_skill_data =raw .get ('PassiveSkillList',{})
            if isinstance (passive_skill_data ,dict ):
                p_list =passive_skill_data .get ('value',{}).get ('values',[])
            elif isinstance (passive_skill_data ,list ):
                p_list =passive_skill_data 
            else :
                p_list =[]
            equip_waza_data =raw .get ('EquipWaza',{})
            if isinstance (equip_waza_data ,dict ):
                e_list =equip_waza_data .get ('value',{}).get ('values',[])
            elif isinstance (equip_waza_data ,list ):
                e_list =equip_waza_data 
            else :
                e_list =[]
            moves =[]
            for w in e_list :
                w_clean =w .split ('::')[-1 ].lower ()
                move_name =PalFrame ._SKILLMAP .get (w_clean ,w_clean )
                moves .append (move_name )
            passives =[]
            for p in p_list :
                p_clean =p .lower ()
                passive_name =PalFrame ._PASSMAP .get (p_clean ,p_clean )
                passives .append (passive_name )
            self ._update_skills_display (moves ,passives )
        except Exception as e :
            print (f"Error updating display: {e }")
    def _update_skills_display (self ,moves ,passives ):
        for i in reversed (range (self .active_skills_list .count ())):
            widget =self .active_skills_list .itemAt (i ).widget ()
            if widget :
                widget .setParent (None )
        for i in reversed (range (self .passive_skills_list .count ())):
            widget =self .passive_skills_list .itemAt (i ).widget ()
            if widget :
                widget .setParent (None )
        for move in moves [:3 ]:
            label =QLabel (move )
            label .setStyleSheet ("font-size: 12px; padding: 2px; border: 1px solid #ccc; border-radius: 3px;")
            self .active_skills_list .addWidget (label )
        for passive in passives [:4 ]:
            label =QLabel (passive )
            label .setStyleSheet ("font-size: 12px; padding: 2px; border: 1px solid #ccc; border-radius: 3px;")
            self .passive_skills_list .addWidget (label )
    def _update_talent (self ,tab ,talent_type ,value ):
        pal_index =getattr (tab ,'selected_pal_index',-1 )
        if pal_index <0 or pal_index >=len (tab .pal_data ):
            return 
        pal_item =tab .pal_data [pal_index ]
        try :
            if 'data'in pal_item :
                raw =pal_item ['data']
            else :
                raw =pal_item ['value']['RawData']['value']['object']['SaveParameter']['value']
            if talent_type =="hp":
                raw ['Talent_HP']={'id':None ,'type':'ByteProperty','value':{'type':'None','value':value }}
            elif talent_type =="shot":
                raw ['Talent_Shot']={'id':None ,'type':'ByteProperty','value':{'type':'None','value':value }}
            elif talent_type =="defense":
                raw ['Talent_Defense']={'id':None ,'type':'ByteProperty','value':{'type':'None','value':value }}
            self ._update_tab_pal_display (tab ,pal_index )
        except Exception as e :
            print (f"Error updating talent: {e }")
    def _update_level (self ,tab ,value ):
        pal_index =getattr (tab ,'selected_pal_index',-1 )
        if pal_index <0 or pal_index >=len (tab .pal_data ):
            return 
        pal_item =tab .pal_data [pal_index ]
        try :
            if 'data'in pal_item :
                raw =pal_item ['data']
            elif 'value'in pal_item :
                raw =pal_item ['value']['RawData']['value']['object']['SaveParameter']['value']
            else :
                raw =pal_item 
            if not isinstance (raw ,dict ):
                print (f"Warning: Cannot update level - pal data is not a dict (type: {type (raw )})")
                return 
            raw ['Level']={'id':None ,'type':'ByteProperty','value':{'type':'None','value':value }}
            import json 
            base_dir =os .path .dirname (os .path .dirname (os .path .abspath (__file__ )))
            exp_table_path =os .path .join (base_dir ,'resources','game_data','pal_exp_table.json')
            with open (exp_table_path ,'r',encoding ='utf-8')as f :
                PAL_EXP_TABLE =json .load (f )
            try :
                exp =PAL_EXP_TABLE [str (value )]["PalTotalEXP"]
            except Exception :
                exp =0 
            raw ['Exp']={'id':None ,'type':'Int64Property','value':exp }
            self ._update_tab_pal_display (tab ,pal_index )
        except Exception as e :
            print (f"Error updating level: {e }")
    def _update_soul (self ,tab ,soul_type ,value ):
        pal_index =getattr (tab ,'selected_pal_index',-1 )
        if pal_index <0 or pal_index >=len (tab .pal_data ):
            return 
        pal_item =tab .pal_data [pal_index ]
        try :
            if 'data'in pal_item :
                raw =pal_item ['data']
            else :
                raw =pal_item ['value']['RawData']['value']['object']['SaveParameter']['value']
            if soul_type =="hp":
                raw ['Rank_HP']={'id':None ,'type':'ByteProperty','value':{'type':'None','value':value }}
            elif soul_type =="attack":
                raw ['Rank_Attack']={'id':None ,'type':'ByteProperty','value':{'type':'None','value':value }}
            elif soul_type =="defense":
                raw ['Rank_Defence']={'id':None ,'type':'ByteProperty','value':{'type':'None','value':value }}
            elif soul_type =="craftspeed":
                raw ['Rank_CraftSpeed']={'id':None ,'type':'ByteProperty','value':{'type':'None','value':value }}
            self ._update_tab_pal_display (tab ,pal_index )
        except Exception as e :
            print (f"Error updating soul: {e }")
    def _max_souls (self ):
        tab_index =self .tabs .currentIndex ()
        if tab_index ==0 :
            tab =self .party_tab 
        elif tab_index ==1 :
            tab =self .palbox_tab 
        elif tab_index ==2 :
            tab =self .dps_tab 
        else :
            return 
        if hasattr (tab ,'rank_hp_spin'):
            tab .rank_hp_spin .setValue (20 )
            tab .rank_attack_spin .setValue (20 )
            tab .rank_defense_spin .setValue (20 )
            tab .rank_craftspeed_spin .setValue (20 )
            self ._update_tab_pal_display (tab ,getattr (tab ,'selected_pal_index',-1 ))
    def _max_ivs (self ):
        tab_index =self .tabs .currentIndex ()
        if tab_index ==0 :
            tab =self .party_tab 
        elif tab_index ==1 :
            tab =self .palbox_tab 
        elif tab_index ==2 :
            tab =self .dps_tab 
        else :
            return 
        if hasattr (tab ,'talent_hp_spin'):
            tab .talent_hp_spin .setValue (100 )
            tab .talent_shot_spin .setValue (100 )
            tab .talent_defense_spin .setValue (100 )
            self ._update_tab_pal_display (tab ,getattr (tab ,'selected_pal_index',-1 ))
    def _max_rank (self ):
        tab_index =self .tabs .currentIndex ()
        if tab_index ==0 :
            tab =self .party_tab 
        elif tab_index ==1 :
            tab =self .palbox_tab 
        elif tab_index ==2 :
            tab =self .dps_tab 
        else :
            return 
        pal_index =getattr (tab ,'selected_pal_index',-1 )
        if pal_index <0 or pal_index >=len (tab .pal_data ):
            return 
        pal_item =tab .pal_data [pal_index ]
        try :
            if 'data'in pal_item :
                raw =pal_item ['data']
            else :
                raw =pal_item ['value']['RawData']['value']['object']['SaveParameter']['value']
            raw ['Rank']={'id':None ,'type':'ByteProperty','value':{'type':'None','value':5 }}
            self ._update_tab_pal_display (tab ,pal_index )
        except Exception as e :
            print (f"Error maxing rank: {e }")
    def _increase_rank (self ):
        tab_index =self .tabs .currentIndex ()
        if tab_index ==0 :
            tab =self .party_tab 
        elif tab_index ==1 :
            tab =self .palbox_tab 
        elif tab_index ==2 :
            tab =self .dps_tab 
        else :
            return 
        pal_index =getattr (tab ,'selected_pal_index',-1 )
        if pal_index <0 or pal_index >=len (tab .pal_data ):
            return 
        pal_item =tab .pal_data [pal_index ]
        try :
            if 'data'in pal_item :
                raw =pal_item ['data']
            else :
                raw =pal_item ['value']['RawData']['value']['object']['SaveParameter']['value']
            current_rank =extract_value (raw ,'Rank',1 )
            new_rank =min (current_rank +1 ,5 )
            raw ['Rank']={'id':None ,'type':'ByteProperty','value':{'type':'None','value':new_rank }}
            self ._update_tab_pal_display (tab ,pal_index )
        except Exception as e :
            print (f"Error increasing rank: {e }")
    def _decrease_rank (self ):
        tab_index =self .tabs .currentIndex ()
        if tab_index ==0 :
            tab =self .party_tab 
        elif tab_index ==1 :
            tab =self .palbox_tab 
        elif tab_index ==2 :
            tab =self .dps_tab 
        else :
            return 
        pal_index =getattr (tab ,'selected_pal_index',-1 )
        if pal_index <0 or pal_index >=len (tab .pal_data ):
            return 
        pal_item =tab .pal_data [pal_index ]
        try :
            if 'data'in pal_item :
                raw =pal_item ['data']
            else :
                raw =pal_item ['value']['RawData']['value']['object']['SaveParameter']['value']
            current_rank =extract_value (raw ,'Rank',1 )
            new_rank =max (current_rank -1 ,1 )
            raw ['Rank']={'id':None ,'type':'ByteProperty','value':{'type':'None','value':new_rank }}
            self ._update_tab_pal_display (tab ,pal_index )
        except Exception as e :
            print (f"Error decreasing rank: {e }")
    def _set_rank_from_star (self ,tab ,rank ):
        pal_index =getattr (tab ,'selected_pal_index',-1 )
        if pal_index <0 or pal_index >=len (tab .pal_data ):
            return 
        pal_item =tab .pal_data [pal_index ]
        try :
            if 'data'in pal_item :
                raw =pal_item ['data']
            else :
                raw =pal_item ['value']['RawData']['value']['object']['SaveParameter']['value']
            raw ['Rank']={'id':None ,'type':'ByteProperty','value':{'type':'None','value':rank }}
            self ._update_tab_pal_display (tab ,pal_index )
        except Exception as e :
            print (f"Error setting rank: {e }")
    def _reset_rank_to_zero (self ,tab ):
        pal_index =getattr (tab ,'selected_pal_index',-1 )
        if pal_index <0 or pal_index >=len (tab .pal_data ):
            return 
        pal_item =tab .pal_data [pal_index ]
        try :
            if 'data'in pal_item :
                raw =pal_item ['data']
            else :
                raw =pal_item ['value']['RawData']['value']['object']['SaveParameter']['value']
            raw ['Rank']={'id':None ,'type':'ByteProperty','value':{'type':'None','value':1 }}
            self ._update_tab_pal_display (tab ,pal_index )
        except Exception as e :
            print (f"Error resetting rank: {e }")
    def _set_gender (self ,gender_value ):
        tab_index =self .tabs .currentIndex ()
        if tab_index ==0 :
            tab =self .party_tab 
        elif tab_index ==1 :
            tab =self .palbox_tab 
        elif tab_index ==2 :
            tab =self .dps_tab 
        else :
            return 
        pal_index =getattr (tab ,'selected_pal_index',-1 )
        if pal_index <0 or pal_index >=len (tab .pal_data ):
            return 
        pal_item =tab .pal_data [pal_index ]
        try :
            if 'data'in pal_item :
                raw =pal_item ['data']
            else :
                raw =pal_item ['value']['RawData']['value']['object']['SaveParameter']['value']
            raw ['Gender']={
            'id':None ,
            'type':'EnumProperty',
            'value':{
            'type':'EPalGenderType',
            'value':gender_value 
            }
            }
            self ._update_tab_pal_display (tab ,pal_index )
        except Exception as e :
            print (f"Error setting gender: {e }")
    def _swap_gender (self ,gender_combo ):
        current_gender =gender_combo .currentText ()
        if current_gender ==t ("edit_pals.male"):
            gender_combo .setCurrentText (t ("edit_pals.female"))
            self ._set_gender ("EPalGenderType::Female")
        else :
            gender_combo .setCurrentText (t ("edit_pals.male"))
            self ._set_gender ("EPalGenderType::Male")
    def _swap_gender_icon (self ,tab ,gender_icon_label ):
        current_text =gender_icon_label .text ()
        if current_text =="♂":
            gender_icon_label .setText ("♀")
            gender_icon_label .setStyleSheet ("font-size: 16px; color: #FB7185;")
            self ._set_gender ("EPalGenderType::Female")
        else :
            gender_icon_label .setText ("♂")
            gender_icon_label .setStyleSheet ("font-size: 16px; color: #7DD3FC;")
            self ._set_gender ("EPalGenderType::Male")
        tab_index =self .tabs .currentIndex ()
        if tab_index ==0 :
            pal_index =getattr (tab ,'selected_pal_index',-1 )
            if pal_index >=0 :
                widget =tab .pal_layout .itemAt (pal_index ).widget ()
                if widget and hasattr (widget ,'gender_label'):
                    widget .gender_label .setText (gender_icon_label .text ())
                    widget .gender_label .setStyleSheet (gender_icon_label .styleSheet ())
    def _max_stats (self ):
        self ._max_ivs ()
        self ._max_souls ()
        self ._max_rank ()
        tab_index =self .tabs .currentIndex ()
        if tab_index ==0 :
            tab =self .party_tab 
        elif tab_index ==1 :
            tab =self .palbox_tab 
        elif tab_index ==2 :
            tab =self .dps_tab 
        else :
            return 
        if hasattr (tab ,'level_spin'):
            tab .level_spin .setValue (65 )
            self ._update_tab_pal_display (tab ,getattr (tab ,'selected_pal_index',-1 ))
    def _generate_pal_save_parameter (self ,character_id ,nickname ,owner_uid ,container_id ,slot_index ,group_id =None ):
        if group_id is None :
            group_id =str (uuid .uuid4 ()).upper ()
        instance_id =str (uuid .uuid4 ()).upper ()
        empty_uuid ="00000000-0000-0000-0000-000000000000"
        time_val =638486453957560000 
        return {
        "key":{
        "PlayerUId":{
        "struct_type":"Guid",
        "struct_id":empty_uuid ,
        "id":None ,
        "value":empty_uuid ,
        "type":"StructProperty"
        },
        "InstanceId":{
        "struct_type":"Guid",
        "struct_id":empty_uuid ,
        "id":None ,
        "value":instance_id ,
        "type":"StructProperty"
        },
        "DebugName":{
        "id":None ,
        "type":"StrProperty",
        "value":""
        }
        },
        "value":{
        "RawData":{
        "array_type":"ByteProperty",
        "id":None ,
        "value":{
        "object":{
        "SaveParameter":{
        "struct_type":"PalIndividualCharacterSaveParameter",
        "struct_id":empty_uuid ,
        "id":None ,
        "value":{
        "CharacterID":{
        "id":None ,
        "type":"NameProperty",
        "value":character_id 
        },
        "Gender":{
        "id":None ,
        "type":"EnumProperty",
        "value":{
        "type":"EPalGenderType",
        "value":"EPalGenderType::Female"
        }
        },
        "NickName":{
        "id":None ,
        "type":"StrProperty",
        "value":nickname 
        },
        "EquipWaza":{
        "array_type":"EnumProperty",
        "id":None ,
        "value":{
        "values":[
        f"EPalWazaID::Unique_{character_id }_Roll"
        ]if character_id =="SheepBall"else []
        },
        "type":"ArrayProperty"
        },
        "MasteredWaza":{
        "array_type":"EnumProperty",
        "id":None ,
        "value":{
        "values":[]
        },
        "type":"ArrayProperty"
        },
        "Hp":{
        "struct_type":"FixedPoint64",
        "struct_id":empty_uuid ,
        "id":None ,
        "value":{
        "Value":{
        "id":None ,
        "value":545000 ,
        "type":"Int64Property"
        }
        },
        "type":"StructProperty"
        },
        "Talent_HP":{
        "id":None ,
        "type":"ByteProperty",
        "value":{
        "type":"None",
        "value":100 
        }
        },
        "Talent_Shot":{
        "id":None ,
        "type":"ByteProperty",
        "value":{
        "type":"None",
        "value":100 
        }
        },
        "Talent_Defense":{
        "id":None ,
        "type":"ByteProperty",
        "value":{
        "type":"None",
        "value":100 
        }
        },
        "FullStomach":{
        "id":None ,
        "type":"FloatProperty",
        "value":150.0 
        },
        "PassiveSkillList":{
        "array_type":"NameProperty",
        "id":None ,
        "value":{
        "values":[]
        },
        "type":"ArrayProperty"
        },
        "OwnedTime":{
        "struct_type":"DateTime",
        "struct_id":empty_uuid ,
        "id":None ,
        "value":time_val ,
        "type":"StructProperty"
        },
        "OwnerPlayerUId":{
        "struct_type":"Guid",
        "struct_id":empty_uuid ,
        "id":None ,
        "value":owner_uid ,
        "type":"StructProperty"
        },
        "OldOwnerPlayerUIds":{
        "array_type":"StructProperty",
        "id":None ,
        "value":{
        "prop_name":"OldOwnerPlayerUIds",
        "prop_type":"StructProperty",
        "values":[owner_uid ],
        "type_name":"Guid",
        "id":empty_uuid 
        },
        "type":"ArrayProperty"
        },
        "SlotId":{
        "struct_type":"PalCharacterSlotId",
        "struct_id":empty_uuid ,
        "id":None ,
        "value":{
        "ContainerId":{
        "struct_type":"PalContainerId",
        "struct_id":empty_uuid ,
        "id":None ,
        "value":{
        "ID":{
        "struct_type":"Guid",
        "struct_id":empty_uuid ,
        "id":None ,
        "value":container_id ,
        "type":"StructProperty"
        }
        },
        "type":"StructProperty"
        },
        "SlotIndex":{
        "id":None ,
        "type":"IntProperty",
        "value":slot_index 
        }
        },
        "type":"StructProperty"
        },
        "GotStatusPointList":{
        "array_type":"StructProperty",
        "id":None ,
        "value":{
        "prop_name":"GotStatusPointList",
        "prop_type":"StructProperty",
        "values":[
        {
        "StatusName":{
        "id":None ,
        "type":"NameProperty",
        "value":"最大HP"
        },
        "StatusPoint":{
        "id":None ,
        "type":"IntProperty",
        "value":0 
        }
        },
        {
        "StatusName":{
        "id":None ,
        "type":"NameProperty",
        "value":"最大SP"
        },
        "StatusPoint":{
        "id":None ,
        "type":"IntProperty",
        "value":0 
        }
        },
        {
        "StatusName":{
        "id":None ,
        "type":"NameProperty",
        "value":"攻撃力"
        },
        "StatusPoint":{
        "id":None ,
        "type":"IntProperty",
        "value":0 
        }
        },
        {
        "StatusName":{
        "id":None ,
        "type":"NameProperty",
        "value":"所持重量"
        },
        "StatusPoint":{
        "id":None ,
        "type":"IntProperty",
        "value":0 
        }
        },
        {
        "StatusName":{
        "id":None ,
        "type":"NameProperty",
        "value":"捕獲率"
        },
        "StatusPoint":{
        "id":None ,
        "type":"IntProperty",
        "value":0 
        }
        },
        {
        "StatusName":{
        "id":None ,
        "type":"NameProperty",
        "value":"作業速度"
        },
        "StatusPoint":{
        "id":None ,
        "type":"IntProperty",
        "value":0 
        }
        }
        ],
        "type_name":"PalGotStatusPoint",
        "id":empty_uuid 
        },
        "type":"ArrayProperty"
        },
        "GotExStatusPointList":{
        "array_type":"StructProperty",
        "id":None ,
        "value":{
        "prop_name":"GotExStatusPointList",
        "prop_type":"StructProperty",
        "values":[
        {
        "StatusName":{
        "id":None ,
        "type":"NameProperty",
        "value":"最大HP"
        },
        "StatusPoint":{
        "id":None ,
        "type":"IntProperty",
        "value":0 
        }
        },
        {
        "StatusName":{
        "id":None ,
        "type":"NameProperty",
        "value":"最大SP"
        },
        "StatusPoint":{
        "id":None ,
        "type":"IntProperty",
        "value":0 
        }
        },
        {
        "StatusName":{
        "id":None ,
        "type":"NameProperty",
        "value":"攻撃力"
        },
        "StatusPoint":{
        "id":None ,
        "type":"IntProperty",
        "value":0 
        }
        },
        {
        "StatusName":{
        "id":None ,
        "type":"NameProperty",
        "value":"所持重量"
        },
        "StatusPoint":{
        "id":None ,
        "type":"IntProperty",
        "value":0 
        }
        },
        {
        "StatusName":{
        "id":None ,
        "type":"NameProperty",
        "value":"作業速度"
        },
        "StatusPoint":{
        "id":None ,
        "type":"IntProperty",
        "value":0 
        }
        }
        ],
        "type_name":"PalGotStatusPoint",
        "id":empty_uuid 
        },
        "type":"ArrayProperty"
        },
        "LastNickNameModifierPlayerUid":{
        "struct_type":"Guid",
        "struct_id":empty_uuid ,
        "id":None ,
        "value":owner_uid ,
        "type":"StructProperty"
        }
        },
        "type":"StructProperty"
        }
        },
        "unknown_bytes":[0 ,0 ,0 ,0 ],
        "group_id":group_id ,
        "trailing_bytes":[0 ,0 ,0 ,0 ]
        },
        "custom_type":".worldSaveData.CharacterSaveParameterMap.Value.RawData",
        "type":"ArrayProperty"
        }
        }
        }
    def _find_free_slot (self ,container_id ,existing_pals ):
        used_slots =set ()
        for pal_item in existing_pals :
            try :
                rawf =pal_item .get ('value',{}).get ('RawData',{}).get ('value',{})
                raw =rawf .get ('object',{}).get ('SaveParameter',{}).get ('value',{})
                slot_id =raw .get ('SlotId',{}).get ('value',{}).get ('ContainerId',{}).get ('value',{}).get ('ID',{}).get ('value')
                if str (slot_id ).lower ()==str (container_id ).lower ():
                    slot_idx =raw .get ('SlotId',{}).get ('value',{}).get ('SlotIndex',{}).get ('value',0 )
                    used_slots .add (slot_idx )
            except :
                pass 
        slot =0 
        while slot in used_slots :
            slot +=1 
        return slot 
    def _create_pal (self ):
        dialog =QDialog (self )
        dialog .setWindowTitle ("Create New Pal")
        dialog .setModal (True )
        dialog .setMinimumSize (400 ,500 )
        layout =QVBoxLayout (dialog )
        pal_layout =QHBoxLayout ()
        pal_layout .addWidget (QLabel (t ("edit_pals.pal_type")))
        pal_select_btn =QPushButton (t ("edit_pals.select_pal_btn"))
        pal_select_btn .setMinimumWidth (200 )
        pal_select_btn .setStyleSheet ("""
            QPushButton {
                text-align: left;
                padding: 5px;
                border: 1px solid #666;
                border-radius: 3px;
                background-color: #333;
                color: #fff;
                font-weight: normal;
            }
            QPushButton:hover {
                background-color: #555;
                border: 1px solid #888;
            }
            QPushButton:pressed {
                background-color: #222;
            }
        """)
        pal_layout .addWidget (pal_select_btn )
        layout .addLayout (pal_layout )
        selected_pal ={"asset":None ,"name":None }
        def select_pal ():
            pal_dialog =QDialog (dialog )
            pal_dialog .setWindowTitle ("Select Pal Type")
            pal_dialog .setModal (True )
            pal_dialog .setMinimumSize (400 ,500 )
            pal_layout =QVBoxLayout (pal_dialog )
            search_label =QLabel ("Search:")
            pal_layout .addWidget (search_label )
            search_edit =QLineEdit ()
            search_edit .setPlaceholderText ("Type to filter pals...")
            pal_layout .addWidget (search_edit )
            list_label =QLabel ("Available Pals:")
            pal_layout .addWidget (list_label )
            pal_list =QListWidget ()
            pal_list .setMinimumHeight (300 )
            pal_layout .addWidget (pal_list )
            button_layout =QHBoxLayout ()
            button_layout .addStretch ()
            ok_btn =QPushButton ("OK")
            ok_btn .clicked .connect (pal_dialog .accept )
            button_layout .addWidget (ok_btn )
            cancel_btn =QPushButton (t ("edit_pals.cancel"))
            cancel_btn .clicked .connect (pal_dialog .reject )
            button_layout .addWidget (cancel_btn )
            pal_layout .addLayout (button_layout )
            all_pals =sorted (PalFrame ._NAMEMAP .items ())
            for asset ,name in all_pals :
                pal_list .addItem (f"{name } ({asset })")
            def filter_pals ():
                text =search_edit .text ().lower ()
                for i in range (pal_list .count ()):
                    item =pal_list .item (i )
                    item .setHidden (text not in item .text ().lower ())
            search_edit .textChanged .connect (filter_pals )
            if pal_dialog .exec ()==QDialog .Accepted :
                current_item =pal_list .currentItem ()
                if current_item :
                    pal_text =current_item .text ()
                    asset_start =pal_text .rfind ("(")+1 
                    asset_end =pal_text .rfind (")")
                    selected_pal ["asset"]=pal_text [asset_start :asset_end ]
                    selected_pal ["name"]=pal_text [:asset_start -2 ]
                    pal_select_btn .setText (pal_text )
        pal_select_btn .clicked .connect (select_pal )
        nick_layout =QHBoxLayout ()
        nick_layout .addWidget (QLabel (t ("edit_pals.nickname")))
        nick_edit =QLineEdit ()
        nick_edit .setPlaceholderText ("Optional")
        nick_layout .addWidget (nick_edit )
        layout .addLayout (nick_layout )
        container_layout =QHBoxLayout ()
        container_layout .addWidget (QLabel (t ("edit_pals.container")))
        container_combo =QComboBox ()
        container_combo .addItem (t ("edit_pals.party"),("party",self .party_container ))
        container_combo .addItem (t ("edit_pals.palbox"),("palbox",self .palbox_container ))
        container_layout .addWidget (container_combo )
        layout .addLayout (container_layout )
        button_layout =QHBoxLayout ()
        button_layout .addStretch ()
        ok_btn =QPushButton ("Create")
        ok_btn .clicked .connect (dialog .accept )
        button_layout .addWidget (ok_btn )
        cancel_btn =QPushButton (t ("edit_pals.cancel"))
        cancel_btn .clicked .connect (dialog .reject )
        button_layout .addWidget (cancel_btn )
        layout .addLayout (button_layout )
        if dialog .exec ()==QDialog .Accepted :
            if not selected_pal ["asset"]:
                QMessageBox .warning (self ,"Error",t ("edit_pals.error_select_pal_type"))
                return 
            character_id =selected_pal ["asset"]
            nickname =nick_edit .text ().strip ()or f"🆕{selected_pal ['name']}"
            container_name ,container_id =container_combo .currentData ()
            if not container_id :
                QMessageBox .warning (self ,"Error",f"No {container_name } container found.")
                return 
            cmap =constants .loaded_level_json ['properties']['worldSaveData']['value']['CharacterSaveParameterMap']['value']
            all_pals =[item for item in cmap if item .get ('value',{}).get ('RawData',{}).get ('value',{}).get ('object',{}).get ('SaveParameter',{}).get ('struct_type')=='PalIndividualCharacterSaveParameter']
            slot_index =self ._find_free_slot (container_id ,all_pals )
            max_slots =5 if container_name =="party"else 960 
            current_count =sum (1 for pal_item in all_pals if str (pal_item ['value']['RawData']['value']['object']['SaveParameter']['value'].get ('SlotId',{}).get ('value',{}).get ('ContainerId',{}).get ('value',{}).get ('ID',{}).get ('value','')).lower ()==str (container_id ).lower ())
            if current_count >=max_slots :
                QMessageBox .warning (self ,"Error",f"Maximum slots reached for {container_name }.")
                return 
            wsd =constants .loaded_level_json ['properties']['worldSaveData']['value']
            group_id =None 
            if 'GroupSaveDataMap'in wsd :
                for group in wsd ['GroupSaveDataMap']['value']:
                    group_data =group ['value']['RawData']['value']
                    players =group_data .get ('players',[])
                    for player in players :
                        if str (player ['player_uid'])==self .player_uid :
                            group_id =group_data ['group_id']
                            break 
                    if group_id :
                        break 
            if not group_id :
                QMessageBox .warning (self ,"Error",t ("edit_pals.error_no_guild"))
                return 
            pal_data =self ._generate_pal_save_parameter (character_id ,nickname ,self .player_uid ,container_id ,slot_index ,group_id )
            instance_id =pal_data ['key']['InstanceId']['value']
            if 'CharacterContainerSaveData'in wsd :
                for container in wsd ['CharacterContainerSaveData']['value']:
                    cont_id =container ['key']['ID']['value']
                    if cont_id ==container_id :
                        slots =container ['value']['Slots']['value']['values']
                        slot_data ={
                        "SlotIndex":{"id":None ,"type":"IntProperty","value":slot_index },
                        "RawData":{
                        "array_type":"ByteProperty",
                        "id":None ,
                        "value":{
                        "player_uid":"00000000-0000-0000-0000-000000000000",
                        "instance_id":instance_id ,
                        "permission_tribe_id":0 ,
                        },
                        "custom_type":".worldSaveData.CharacterContainerSaveData.Value.Slots.Slots.RawData",
                        "type":"ArrayProperty"
                        }
                        }
                        slots .append (slot_data )
                        break 
            if 'GroupSaveDataMap'in wsd :
                for group in wsd ['GroupSaveDataMap']['value']:
                    g_id =group ['value']['RawData']['value']['group_id']
                    if g_id ==group_id :
                        handle_ids =group ['value']['RawData']['value'].get ('individual_character_handle_ids',[])
                        handle_ids .append ({
                        "guid":"00000000-0000-0000-0000-000000000000",
                        "instance_id":instance_id 
                        })
                        group ['value']['RawData']['value']['individual_character_handle_ids']=handle_ids 
                        break 
            cmap .append (pal_data )
            if self .player_sav_path and os .path .exists (self .player_sav_path ):
                player_json =sav_to_json (self .player_sav_path )
                save_data =player_json ['properties']['SaveData']['value']
                empty_uuid ="00000000-0000-0000-0000-000000000000"
                if "RecordData"not in save_data :
                    save_data ["RecordData"]={
                    "struct_type":"PalLoggedinPlayerSaveDataRecordData",
                    "struct_id":empty_uuid ,
                    "id":None ,
                    "value":{}
                    }
                record_data =save_data ["RecordData"]["value"]
                if "PalCaptureCount"not in record_data :
                    record_data ["PalCaptureCount"]={
                    "key_type":"NameProperty",
                    "value_type":"IntProperty",
                    "key_struct_type":None ,
                    "value_struct_type":None ,
                    "id":None ,
                    "value":[]
                    }
                if "PaldeckUnlockFlag"not in record_data :
                    record_data ["PaldeckUnlockFlag"]={
                    "key_type":"NameProperty",
                    "value_type":"BoolProperty",
                    "key_struct_type":None ,
                    "value_struct_type":None ,
                    "id":None ,
                    "value":[]
                    }
                def handle_special_keys (key ):
                    match key :
                        case 'PlantSlime_Flower':return 'PlantSlime'
                        case 'SheepBall':return 'Sheepball'
                        case 'LazyCatFish':return 'LazyCatfish'
                        case 'Blueplatypus':return 'BluePlatypus'
                        case 'GhostAnglerFish':return 'GhostAnglerfish'
                        case 'GhostAnglerFish_Fire':return 'GhostAnglerfish_Fire'
                        case "Icenarwhal_Fire":return "IceNarwhal_Fire"
                        case "Icenarwhal":return "IceNarwhal"
                    return key 
                pal_key =handle_special_keys (character_id )
                capture_list =record_data ["PalCaptureCount"]["value"]
                found =False 
                for item in capture_list :
                    if item ["key"].lower ()==pal_key .lower ():
                        item ["value"]+=1 
                        found =True 
                        break 
                if not found :
                    capture_list .append ({"key":pal_key ,"value":1 })
                unlock_list =record_data ["PaldeckUnlockFlag"]["value"]
                found =False 
                for item in unlock_list :
                    if item ["key"].lower ()==pal_key .lower ():
                        item ["value"]=True 
                        found =True 
                        break 
                if not found :
                    unlock_list .append ({"key":pal_key ,"value":True })
                json_to_sav (player_json ,self .player_sav_path )
            self ._load_pals ()
            pal_name =selected_pal ["name"]
            QMessageBox .information (self ,"Success",f"Created new {pal_name } in {container_name }.")
    def _delete_pal (self ):
        print (f"DEBUG: Attempting to delete pal")
        tab_index =self .tabs .currentIndex ()
        print (f"DEBUG: Current tab index: {tab_index }")
        if tab_index ==0 :
            tab =self .party_tab 
            tab_name =t ("edit_pals.party")
        elif tab_index ==1 :
            tab =self .palbox_tab 
            tab_name =t ("edit_pals.palbox")
        elif tab_index ==2 :
            tab =self .dps_tab 
            tab_name ="DPS"
        else :
            return 
        pal_index =getattr (tab ,'selected_pal_index',-1 )
        print (f"DEBUG: Pal index: {pal_index }, tab.pal_data length: {len (tab .pal_data )}")
        if pal_index <0 or pal_index >=len (tab .pal_data ):
            return 
        reply =QMessageBox .question (self ,t ("edit_pals.confirm_delete"),f"Are you sure you want to delete this pal from {tab_name }?",QMessageBox .Yes |QMessageBox .No )
        if reply !=QMessageBox .Yes :
            return 
        pal_item =tab .pal_data [pal_index ]
        print (f"DEBUG: Deleting pal_item: {pal_item }")
        if tab_name =="DPS":
            if self .dps_json :
                save_parameter_array =self .dps_json ['properties'].get ('SaveParameterArray',{}).get ('value',{}).get ('values',[])
                if 0 <=pal_item ['index']<len (save_parameter_array ):
                    print (f"DEBUG: Removing DPS entry at index {pal_item ['index']}")
                    save_parameter_array .pop (pal_item ['index'])
            tab .pal_data .pop (pal_index )
            for j in range (len (tab .pal_data )):
                tab .pal_data [j ]['index']=j 
        else :
            cmap =constants .loaded_level_json ['properties']['worldSaveData']['value']['CharacterSaveParameterMap']['value']
            print (f"DEBUG: Before remove, cmap length: {len (cmap )}")
            cmap .remove (pal_item )
            print (f"DEBUG: After remove, cmap length: {len (cmap )}")
            tab .pal_data .pop (pal_index )
        if tab_name !="DPS":
            self ._populate_tab (tab ,tab .pal_data ,tab_name )
    def _clone_pal (self ):
        QMessageBox .information (self ,"Info","Clone Pal functionality not implemented yet")
    def accept (self ):
        try :
            if hasattr (self ,'_pending_deletions')and self ._pending_deletions :
                cmap =constants .loaded_level_json ['properties']['worldSaveData']['value']['CharacterSaveParameterMap']['value']
                wsd =constants .loaded_level_json ['properties']['worldSaveData']['value']
                for deletion in self ._pending_deletions :
                    pal_item =deletion ['pal_item']
                    tab_name =deletion ['tab_name']
                    if tab_name =="DPS":
                        if self .dps_json :
                            save_parameter_array =self .dps_json ['properties'].get ('SaveParameterArray',{}).get ('value',{}).get ('values',[])
                            if 0 <=pal_item ['index']<len (save_parameter_array ):
                                save_parameter_array .pop (pal_item ['index'])
                                for j in range (len (save_parameter_array )):
                                    if j >=pal_item ['index']:
                                        save_parameter_array [j ]['index']=j 
                    else :
                        if pal_item in cmap :
                            cmap .remove (pal_item )
                        raw =pal_item ['value']['RawData']['value']['object']['SaveParameter']['value']
                        container_id =raw .get ('SlotId',{}).get ('value',{}).get ('ContainerId',{}).get ('value',{}).get ('ID',{}).get ('value')
                        if 'CharacterContainerSaveData'in wsd :
                            for container in wsd ['CharacterContainerSaveData']['value']:
                                cont_id =container ['key']['ID']['value']
                                if cont_id ==container_id :
                                    slots =container ['value']['Slots']['value']['values']
                                    slots [:]=[s for s in slots if s .get ('RawData',{}).get ('value',{}).get ('instance_id')!=raw .get ('InstanceId',{}).get ('value')]
                                    break 
                        if 'GroupSaveDataMap'in wsd :
                            for group in wsd ['GroupSaveDataMap']['value']:
                                handle_ids =group ['value']['RawData']['value'].get ('individual_character_handle_ids',[])
                                handle_ids [:]=[h for h in handle_ids if h .get ('instance_id')!=raw .get ('InstanceId',{}).get ('value')]
                                group ['value']['RawData']['value']['individual_character_handle_ids']=handle_ids 
                self ._pending_deletions .clear ()
            if hasattr (self ,'_pending_additions')and self ._pending_additions :
                cmap =constants .loaded_level_json ['properties']['worldSaveData']['value']['CharacterSaveParameterMap']['value']
                wsd =constants .loaded_level_json ['properties']['worldSaveData']['value']
                for addition in self ._pending_additions :
                    pal_item =addition ['pal_item']
                    instance_id =pal_item ['key']['InstanceId']['value']
                    already_in_cmap =any (
                    p .get ('key',{}).get ('InstanceId',{}).get ('value')==instance_id 
                    for p in cmap 
                    )
                    if not already_in_cmap :
                        cmap .append (pal_item )
                    container_id =addition ['container_id']
                    group_id =None 
                    raw =None 
                    try :
                        raw =pal_item ['value']['RawData']['value']['object']['SaveParameter']['value']
                        group_id =pal_item ['value']['RawData']['value'].get ('group_id')
                    except :
                        pass 
                    if 'CharacterContainerSaveData'in wsd and container_id :
                        for container in wsd ['CharacterContainerSaveData']['value']:
                            cont_id =container ['key']['ID']['value']
                            if cont_id ==container_id :
                                slots =container ['value']['Slots']['value']['values']
                                slot_exists =any (s .get ('RawData',{}).get ('value',{}).get ('instance_id')==instance_id for s in slots )
                                if not slot_exists and raw :
                                    try :
                                        slot_index =raw .get ('SlotId',{}).get ('value',{}).get ('SlotIndex',{}).get ('value',0 )
                                        slot_data ={
                                        "SlotIndex":{"id":None ,"type":"IntProperty","value":slot_index },
                                        "RawData":{
                                        "array_type":"ByteProperty",
                                        "id":None ,
                                        "value":{
                                        "player_uid":"00000000-0000-0000-0000-000000000000",
                                        "instance_id":instance_id ,
                                        "permission_tribe_id":0 ,
                                        },
                                        "custom_type":".worldSaveData.CharacterContainerSaveData.Value.Slots.Slots.RawData",
                                        "type":"ArrayProperty"
                                        }
                                        }
                                        slots .append (slot_data )
                                    except :
                                        pass 
                                break 
                    if 'GroupSaveDataMap'in wsd and group_id :
                        for group in wsd ['GroupSaveDataMap']['value']:
                            g_id =group ['value']['RawData']['value'].get ('group_id')
                            if g_id ==group_id :
                                handle_ids =group ['value']['RawData']['value'].get ('individual_character_handle_ids',[])
                                handle_exists =any (h .get ('instance_id')==instance_id for h in handle_ids )
                                if not handle_exists :
                                    handle_ids .append ({
                                    "guid":"00000000-0000-0000-0000-000000000000",
                                    "instance_id":instance_id 
                                    })
                                    group ['value']['RawData']['value']['individual_character_handle_ids']=handle_ids 
                                break 
                self ._pending_additions .clear ()
            pass 
        except Exception as e :
            print (f"Error in accept(): {e }")
            import traceback 
            traceback .print_exc ()
        super ().accept ()
    def _rename_pal (self ):
        tab_index =self .tabs .currentIndex ()
        if tab_index ==0 :
            tab =self .party_tab 
            tab_name =t ("edit_pals.party")
        elif tab_index ==1 :
            tab =self .palbox_tab 
            tab_name =t ("edit_pals.palbox")
        elif tab_index ==2 :
            tab =self .dps_tab 
            tab_name ="DPS"
        else :
            return 
        pal_index =getattr (tab ,'selected_pal_index',-1 )
        if pal_index <0 or pal_index >=len (tab .pal_data ):
            return 
        pal_item =tab .pal_data [pal_index ]
        try :
            if 'data'in pal_item :
                raw =pal_item ['data']
            else :
                raw =pal_item ['value']['RawData']['value']['object']['SaveParameter']['value']
            current_nick =extract_value (raw ,'NickName','')
            new_nick ,ok =QInputDialog .getText (self ,t ("edit_pals.rename_pal"),"Enter new nickname:",text =current_nick )
            if ok and new_nick !=current_nick :
                raw ['NickName']={'id':None ,'type':'StrProperty','value':new_nick }
                self ._update_tab_pal_display (tab ,pal_index )
                cid =extract_value (raw ,'CharacterID','')
                nick =extract_value (raw ,'NickName','')
                pal_name =PalFrame ._NAMEMAP .get (cid .lower (),cid )
                if nick :
                    pal_name =f"{pal_name } ({nick })"
                tab .pal_name_label .setText (pal_name )
                tab .pal_name_label .repaint ()
        except Exception as e :
            print (f"Error renaming pal: {e }")
    def _show_create_pal_dialog (self ,slot_index ,tab_name ):
        try :
            if tab_name =="DPS":
                from PySide6 .QtWidgets import QApplication 
                main_window =QApplication .activeWindow ()
                dialog =QDialog (main_window )
                dialog .setWindowTitle (f"Create New Pal in DPS Slot {slot_index }")
                dialog .setModal (True )
                dialog .setMinimumSize (400 ,300 )
                layout =QVBoxLayout (dialog )
                pal_layout =QHBoxLayout ()
                pal_layout .addWidget (QLabel (t ("edit_pals.pal_type")))
                pal_select_btn =QPushButton (t ("edit_pals.select_pal_btn"))
                pal_select_btn .setMinimumWidth (200 )
                pal_select_btn .setStyleSheet ("""
                    QPushButton {
                        text-align: left;
                        padding: 5px;
                        border: 1px solid #666;
                        border-radius: 3px;
                        background-color: #333;
                        color: #fff;
                        font-weight: normal;
                    }
                    QPushButton:hover {
                        background-color: #555;
                        border: 1px solid #888;
                    }
                    QPushButton:pressed {
                        background-color: #222;
                    }
                """)
                pal_layout .addWidget (pal_select_btn )
                layout .addLayout (pal_layout )
                selected_pal ={"asset":None ,"name":None }
                def select_pal ():
                    pal_dialog =QDialog (dialog )
                    pal_dialog .setWindowTitle ("Select Pal Type")
                    pal_dialog .setModal (True )
                    pal_dialog .setMinimumSize (400 ,500 )
                    pal_layout =QVBoxLayout (pal_dialog )
                    search_label =QLabel ("Search:")
                    pal_layout .addWidget (search_label )
                    search_edit =QLineEdit ()
                    search_edit .setPlaceholderText ("Type to filter pals...")
                    pal_layout .addWidget (search_edit )
                    list_label =QLabel ("Available Pals:")
                    pal_layout .addWidget (list_label )
                    pal_list =QListWidget ()
                    pal_list .setMinimumHeight (300 )
                    pal_layout .addWidget (pal_list )
                    button_layout =QHBoxLayout ()
                    button_layout .addStretch ()
                    ok_btn =QPushButton ("OK")
                    ok_btn .clicked .connect (pal_dialog .accept )
                    button_layout .addWidget (ok_btn )
                    cancel_btn =QPushButton (t ("edit_pals.cancel"))
                    cancel_btn .clicked .connect (pal_dialog .reject )
                    button_layout .addWidget (cancel_btn )
                    pal_layout .addLayout (button_layout )
                    all_pals =sorted (PalFrame ._NAMEMAP .items ())
                    for asset ,name in all_pals :
                        pal_list .addItem (f"{name } ({asset })")
                    def filter_pals ():
                        text =search_edit .text ().lower ()
                        for i in range (pal_list .count ()):
                            item =pal_list .item (i )
                            item .setHidden (text not in item .text ().lower ())
                    search_edit .textChanged .connect (filter_pals )
                    if pal_dialog .exec ()==QDialog .Accepted :
                        current_item =pal_list .currentItem ()
                        if current_item :
                            pal_text =current_item .text ()
                            asset_start =pal_text .rfind ("(")+1 
                            asset_end =pal_text .rfind (")")
                            selected_pal ["asset"]=pal_text [asset_start :asset_end ]
                            selected_pal ["name"]=pal_text [:asset_start -2 ]
                            pal_select_btn .setText (pal_text )
                pal_select_btn .clicked .connect (select_pal )
                nick_layout =QHBoxLayout ()
                nick_layout .addWidget (QLabel (t ("edit_pals.nickname")))
                nick_edit =QLineEdit ()
                nick_edit .setPlaceholderText ("Optional")
                nick_layout .addWidget (nick_edit )
                layout .addLayout (nick_layout )
                button_layout =QHBoxLayout ()
                button_layout .addStretch ()
                ok_btn =QPushButton ("Create")
                ok_btn .clicked .connect (dialog .accept )
                button_layout .addWidget (ok_btn )
                cancel_btn =QPushButton (t ("edit_pals.cancel"))
                cancel_btn .clicked .connect (dialog .reject )
                button_layout .addWidget (cancel_btn )
                layout .addLayout (button_layout )
                if dialog .exec ()==QDialog .Accepted :
                    if not selected_pal ["asset"]:
                        QMessageBox .warning (self ,"Error",t ("edit_pals.error_select_pal_type"))
                        return None 
                    character_id =selected_pal ["asset"]
                    nickname =nick_edit .text ().strip ()or f"🆕{selected_pal ['name']}"
                    container_id ="00000000-0000-0000-0000-000000000000"
                    group_id ="00000000-0000-0000-0000-000000000000"
                    pal_data =self ._generate_pal_save_parameter (character_id ,nickname ,self .player_uid ,container_id ,0 ,group_id )
                    return {
                    'character_id':character_id ,
                    'nickname':nickname ,
                    'container_id':container_id ,
                    'container_name':'DPS',
                    'tab_name':tab_name ,
                    'slot_index':slot_index ,
                    'group_id':group_id ,
                    'pal_item':pal_data ,
                    'pal_name':selected_pal ["name"],
                    'selected_pal':selected_pal 
                    }
                return None 
            if tab_name ==t ("edit_pals.party"):
                container_id =self .party_container 
                container_name =t ("edit_pals.party")
            elif tab_name ==t ("edit_pals.palbox"):
                container_id =self .palbox_container 
                container_name =t ("edit_pals.palbox")
            else :
                return None 
            from PySide6 .QtWidgets import QApplication 
            main_window =QApplication .activeWindow ()
            dialog =QDialog (main_window )
            dialog .setWindowTitle (f"Create New Pal in {container_name } Slot {slot_index }")
            dialog .setModal (True )
            dialog .setMinimumSize (400 ,300 )
            layout =QVBoxLayout (dialog )
            pal_layout =QHBoxLayout ()
            pal_layout .addWidget (QLabel (t ("edit_pals.pal_type")))
            pal_select_btn =QPushButton (t ("edit_pals.select_pal_btn"))
            pal_select_btn .setMinimumWidth (200 )
            pal_select_btn .setStyleSheet ("""
                QPushButton {
                    text-align: left;
                    padding: 5px;
                    border: 1px solid #666;
                    border-radius: 3px;
                    background-color: #333;
                    color: #fff;
                    font-weight: normal;
                }
                QPushButton:hover {
                    background-color: #555;
                    border: 1px solid #888;
                }
                QPushButton:pressed {
                    background-color: #222;
                }
            """)
            pal_layout .addWidget (pal_select_btn )
            layout .addLayout (pal_layout )
            selected_pal ={"asset":None ,"name":None }
            def select_pal ():
                pal_dialog =QDialog (dialog )
                pal_dialog .setWindowTitle ("Select Pal Type")
                pal_dialog .setModal (True )
                pal_dialog .setMinimumSize (400 ,500 )
                pal_layout =QVBoxLayout (pal_dialog )
                search_label =QLabel ("Search:")
                pal_layout .addWidget (search_label )
                search_edit =QLineEdit ()
                search_edit .setPlaceholderText ("Type to filter pals...")
                pal_layout .addWidget (search_edit )
                list_label =QLabel ("Available Pals:")
                pal_layout .addWidget (list_label )
                pal_list =QListWidget ()
                pal_list .setMinimumHeight (300 )
                pal_layout .addWidget (pal_list )
                button_layout =QHBoxLayout ()
                button_layout .addStretch ()
                ok_btn =QPushButton ("OK")
                ok_btn .clicked .connect (pal_dialog .accept )
                button_layout .addWidget (ok_btn )
                cancel_btn =QPushButton (t ("edit_pals.cancel"))
                cancel_btn .clicked .connect (pal_dialog .reject )
                button_layout .addWidget (cancel_btn )
                pal_layout .addLayout (button_layout )
                all_pals =sorted (PalFrame ._NAMEMAP .items ())
                for asset ,name in all_pals :
                    pal_list .addItem (f"{name } ({asset })")
                def filter_pals ():
                    text =search_edit .text ().lower ()
                    for i in range (pal_list .count ()):
                        item =pal_list .item (i )
                        item .setHidden (text not in item .text ().lower ())
                search_edit .textChanged .connect (filter_pals )
                if pal_dialog .exec ()==QDialog .Accepted :
                    current_item =pal_list .currentItem ()
                    if current_item :
                        pal_text =current_item .text ()
                        asset_start =pal_text .rfind ("(")+1 
                        asset_end =pal_text .rfind (")")
                        selected_pal ["asset"]=pal_text [asset_start :asset_end ]
                        selected_pal ["name"]=pal_text [:asset_start -2 ]
                        pal_select_btn .setText (pal_text )
            pal_select_btn .clicked .connect (select_pal )
            nick_layout =QHBoxLayout ()
            nick_layout .addWidget (QLabel (t ("edit_pals.nickname")))
            nick_edit =QLineEdit ()
            nick_edit .setPlaceholderText ("Optional")
            nick_layout .addWidget (nick_edit )
            layout .addLayout (nick_layout )
            button_layout =QHBoxLayout ()
            button_layout .addStretch ()
            ok_btn =QPushButton ("Create")
            ok_btn .clicked .connect (dialog .accept )
            button_layout .addWidget (ok_btn )
            cancel_btn =QPushButton (t ("edit_pals.cancel"))
            cancel_btn .clicked .connect (dialog .reject )
            button_layout .addWidget (cancel_btn )
            layout .addLayout (button_layout )
            if dialog .exec ()==QDialog .Accepted :
                if not selected_pal ["asset"]:
                    QMessageBox .warning (self ,"Error",t ("edit_pals.error_select_pal_type"))
                    return None 
                character_id =selected_pal ["asset"]
                nickname =nick_edit .text ().strip ()or f"🆕{selected_pal ['name']}"
                cmap =constants .loaded_level_json ['properties']['worldSaveData']['value']['CharacterSaveParameterMap']['value']
                all_pals =[item for item in cmap if item .get ('value',{}).get ('RawData',{}).get ('value',{}).get ('object',{}).get ('SaveParameter',{}).get ('struct_type')=='PalIndividualCharacterSaveParameter']
                pending_deletions_for_slot =[]
                if hasattr (self ,'_pending_deletions')and self ._pending_deletions :
                    for deletion in self ._pending_deletions :
                        if deletion ['tab_name']==tab_name :
                            del_pal_item =deletion ['pal_item']
                            del_raw =del_pal_item ['value']['RawData']['value']['object']['SaveParameter']['value']
                            del_container_id =del_raw .get ('SlotId',{}).get ('value',{}).get ('ContainerId',{}).get ('value',{}).get ('ID',{}).get ('value')
                            del_slot_index =del_raw .get ('SlotId',{}).get ('value',{}).get ('SlotIndex',{}).get ('value')
                            if del_container_id ==container_id and del_slot_index ==slot_index :
                                pending_deletions_for_slot .append (deletion )
                for pal_item in all_pals :
                    raw =pal_item ['value']['RawData']['value']['object']['SaveParameter']['value']
                    pal_container_id =raw .get ('SlotId',{}).get ('value',{}).get ('ContainerId',{}).get ('value',{}).get ('ID',{}).get ('value')
                    pal_slot_index =raw .get ('SlotId',{}).get ('value',{}).get ('SlotIndex',{}).get ('value')
                    if pal_container_id ==container_id and pal_slot_index ==slot_index :
                        is_pending_deletion =False 
                        for deletion in pending_deletions_for_slot :
                            if deletion ['pal_item']==pal_item :
                                is_pending_deletion =True 
                                break 
                        if not is_pending_deletion :
                            QMessageBox .warning (self ,"Error",f"Slot {slot_index } is already occupied.")
                            return None 
                wsd =constants .loaded_level_json ['properties']['worldSaveData']['value']
                group_id =None 
                if 'GroupSaveDataMap'in wsd :
                    for group in wsd ['GroupSaveDataMap']['value']:
                        group_data =group ['value']['RawData']['value']
                        players =group_data .get ('players',[])
                        for player in players :
                            if str (player ['player_uid'])==self .player_uid :
                                group_id =group_data ['group_id']
                                break 
                        if group_id :
                            break 
                if not group_id :
                    QMessageBox .warning (self ,"Error",t ("edit_pals.error_no_guild"))
                    return None 
                pal_data =self ._generate_pal_save_parameter (character_id ,nickname ,self .player_uid ,container_id ,slot_index ,group_id )
                return {
                'character_id':character_id ,
                'nickname':nickname ,
                'container_id':container_id ,
                'container_name':container_name ,
                'tab_name':tab_name ,
                'slot_index':slot_index ,
                'group_id':group_id ,
                'pal_item':pal_data ,
                'pal_name':selected_pal ["name"],
                'selected_pal':selected_pal 
                }
            return None 
        except Exception as e :
            print (f"Error in pal creation dialog: {e }")
            QMessageBox .warning (self ,"Error",f"Failed to create pal: {e }")
            return None 
    def _create_pal_at_slot (self ,slot_index ,tab_name ):
        try :
            if tab_name ==t ("edit_pals.party"):
                container_id =self .party_container 
                container_name =t ("edit_pals.party")
            elif tab_name ==t ("edit_pals.palbox"):
                container_id =self .palbox_container 
                container_name =t ("edit_pals.palbox")
            else :
                return 
            dialog =QDialog (self )
            dialog .setWindowTitle (f"Create New Pal in {container_name } Slot {slot_index }")
            dialog .setModal (True )
            dialog .setMinimumSize (400 ,300 )
            layout =QVBoxLayout (dialog )
            pal_layout =QHBoxLayout ()
            pal_layout .addWidget (QLabel (t ("edit_pals.pal_type")))
            pal_select_btn =QPushButton (t ("edit_pals.select_pal_btn"))
            pal_select_btn .setMinimumWidth (200 )
            pal_select_btn .setStyleSheet ("""
                QPushButton {
                    text-align: left;
                    padding: 5px;
                    border: 1px solid #666;
                    border-radius: 3px;
                    background-color: #333;
                    color: #fff;
                    font-weight: normal;
                }
                QPushButton:hover {
                    background-color: #555;
                    border: 1px solid #888;
                }
                QPushButton:pressed {
                    background-color: #222;
                }
            """)
            pal_layout .addWidget (pal_select_btn )
            layout .addLayout (pal_layout )
            selected_pal ={"asset":None ,"name":None }
            def select_pal ():
                pal_dialog =QDialog (dialog )
                pal_dialog .setWindowTitle ("Select Pal Type")
                pal_dialog .setModal (True )
                pal_dialog .setMinimumSize (400 ,500 )
                pal_layout =QVBoxLayout (pal_dialog )
                search_label =QLabel ("Search:")
                pal_layout .addWidget (search_label )
                search_edit =QLineEdit ()
                search_edit .setPlaceholderText ("Type to filter pals...")
                pal_layout .addWidget (search_edit )
                list_label =QLabel ("Available Pals:")
                pal_layout .addWidget (list_label )
                pal_list =QListWidget ()
                pal_list .setMinimumHeight (300 )
                pal_layout .addWidget (pal_list )
                button_layout =QHBoxLayout ()
                button_layout .addStretch ()
                ok_btn =QPushButton ("OK")
                ok_btn .clicked .connect (pal_dialog .accept )
                button_layout .addWidget (ok_btn )
                cancel_btn =QPushButton (t ("edit_pals.cancel"))
                cancel_btn .clicked .connect (pal_dialog .reject )
                button_layout .addWidget (cancel_btn )
                pal_layout .addLayout (button_layout )
                all_pals =sorted (PalFrame ._NAMEMAP .items ())
                for asset ,name in all_pals :
                    pal_list .addItem (f"{name } ({asset })")
                def filter_pals ():
                    text =search_edit .text ().lower ()
                    for i in range (pal_list .count ()):
                        item =pal_list .item (i )
                        item .setHidden (text not in item .text ().lower ())
                search_edit .textChanged .connect (filter_pals )
                if pal_dialog .exec ()==QDialog .Accepted :
                    current_item =pal_list .currentItem ()
                    if current_item :
                        pal_text =current_item .text ()
                        asset_start =pal_text .rfind ("(")+1 
                        asset_end =pal_text .rfind (")")
                        selected_pal ["asset"]=pal_text [asset_start :asset_end ]
                        selected_pal ["name"]=pal_text [:asset_start -2 ]
                        pal_select_btn .setText (pal_text )
            pal_select_btn .clicked .connect (select_pal )
            nick_layout =QHBoxLayout ()
            nick_layout .addWidget (QLabel (t ("edit_pals.nickname")))
            nick_edit =QLineEdit ()
            nick_edit .setPlaceholderText ("Optional")
            nick_layout .addWidget (nick_edit )
            layout .addLayout (nick_layout )
            button_layout =QHBoxLayout ()
            button_layout .addStretch ()
            ok_btn =QPushButton ("Create")
            ok_btn .clicked .connect (dialog .accept )
            button_layout .addWidget (ok_btn )
            cancel_btn =QPushButton (t ("edit_pals.cancel"))
            cancel_btn .clicked .connect (dialog .reject )
            button_layout .addWidget (cancel_btn )
            layout .addLayout (button_layout )
            if dialog .exec ()==QDialog .Accepted :
                if not selected_pal ["asset"]:
                    QMessageBox .warning (self ,"Error",t ("edit_pals.error_select_pal_type"))
                    return 
                character_id =selected_pal ["asset"]
                nickname =nick_edit .text ().strip ()or f"🆕{selected_pal ['name']}"
                cmap =constants .loaded_level_json ['properties']['worldSaveData']['value']['CharacterSaveParameterMap']['value']
                all_pals =[item for item in cmap if item .get ('value',{}).get ('RawData',{}).get ('value',{}).get ('object',{}).get ('SaveParameter',{}).get ('struct_type')=='PalIndividualCharacterSaveParameter']
                for pal_item in all_pals :
                    raw =pal_item ['value']['RawData']['value']['object']['SaveParameter']['value']
                    pal_container_id =raw .get ('SlotId',{}).get ('value',{}).get ('ContainerId',{}).get ('value',{}).get ('ID',{}).get ('value')
                    pal_slot_index =raw .get ('SlotId',{}).get ('value',{}).get ('SlotIndex',{}).get ('value')
                    if pal_container_id ==container_id and pal_slot_index ==slot_index :
                        QMessageBox .warning (self ,"Error",f"Slot {slot_index } is already occupied.")
                        return 
                wsd =constants .loaded_level_json ['properties']['worldSaveData']['value']
                group_id =None 
                if 'GroupSaveDataMap'in wsd :
                    for group in wsd ['GroupSaveDataMap']['value']:
                        group_data =group ['value']['RawData']['value']
                        players =group_data .get ('players',[])
                        for player in players :
                            if str (player ['player_uid'])==self .player_uid :
                                group_id =group_data ['group_id']
                                break 
                        if group_id :
                            break 
                if not group_id :
                    QMessageBox .warning (self ,"Error",t ("edit_pals.error_no_guild"))
                    return 
                pal_data =self ._generate_pal_save_parameter (character_id ,nickname ,self .player_uid ,container_id ,slot_index ,group_id )
                instance_id =pal_data ['key']['InstanceId']['value']
                if 'CharacterContainerSaveData'in wsd :
                    for container in wsd ['CharacterContainerSaveData']['value']:
                        cont_id =container ['key']['ID']['value']
                        if cont_id ==container_id :
                            slots =container ['value']['Slots']['value']['values']
                            slot_data ={
                            "SlotIndex":{"id":None ,"type":"IntProperty","value":slot_index },
                            "RawData":{
                            "array_type":"ByteProperty",
                            "id":None ,
                            "value":{
                            "player_uid":"00000000-0000-0000-0000-000000000000",
                            "instance_id":instance_id ,
                            "permission_tribe_id":0 ,
                            },
                            "custom_type":".worldSaveData.CharacterContainerSaveData.Value.Slots.Slots.RawData",
                            "type":"ArrayProperty"
                            }
                            }
                            slots .append (slot_data )
                            break 
                if 'GroupSaveDataMap'in wsd :
                    for group in wsd ['GroupSaveDataMap']['value']:
                        g_id =group ['value']['RawData']['value']['group_id']
                        if g_id ==group_id :
                            handle_ids =group ['value']['RawData']['value'].get ('individual_character_handle_ids',[])
                            handle_ids .append ({
                            "guid":"00000000-0000-0000-0000-000000000000",
                            "instance_id":instance_id 
                            })
                            group ['value']['RawData']['value']['individual_character_handle_ids']=handle_ids 
                            break 
                cmap .append (pal_data )
                if self .player_sav_path and os .path .exists (self .player_sav_path ):
                    player_json =sav_to_json (self .player_sav_path )
                    save_data =player_json ['properties']['SaveData']['value']
                    empty_uuid ="00000000-0000-0000-0000-000000000000"
                    if "RecordData"not in save_data :
                        save_data ["RecordData"]={
                        "struct_type":"PalLoggedinPlayerSaveDataRecordData",
                        "struct_id":empty_uuid ,
                        "id":None ,
                        "value":{}
                        }
                    record_data =save_data ["RecordData"]["value"]
                    if "PalCaptureCount"not in record_data :
                        record_data ["PalCaptureCount"]={
                        "key_type":"NameProperty",
                        "value_type":"IntProperty",
                        "key_struct_type":None ,
                        "value_struct_type":None ,
                        "id":None ,
                        "value":[]
                        }
                    if "PaldeckUnlockFlag"not in record_data :
                        record_data ["PaldeckUnlockFlag"]={
                        "key_type":"NameProperty",
                        "value_type":"BoolProperty",
                        "key_struct_type":None ,
                        "value_struct_type":None ,
                        "id":None ,
                        "value":[]
                        }
                    def handle_special_keys (key ):
                        match key :
                            case 'PlantSlime_Flower':return 'PlantSlime'
                            case 'SheepBall':return 'Sheepball'
                            case 'LazyCatFish':return 'LazyCatfish'
                            case 'Blueplatypus':return 'BluePlatypus'
                            case 'GhostAnglerFish':return 'GhostAnglerfish'
                            case 'GhostAnglerFish_Fire':return 'GhostAnglerfish_Fire'
                            case "Icenarwhal_Fire":return "IceNarwhal_Fire"
                            case "Icenarwhal":return "IceNarwhal"
                        return key 
                    pal_key =handle_special_keys (character_id )
                    capture_list =record_data ["PalCaptureCount"]["value"]
                    found =False 
                    for item in capture_list :
                        if item ["key"].lower ()==pal_key .lower ():
                            item ["value"]+=1 
                            found =True 
                            break 
                    if not found :
                        capture_list .append ({"key":pal_key ,"value":1 })
                    unlock_list =record_data ["PaldeckUnlockFlag"]["value"]
                    found =False 
                    for item in unlock_list :
                        if item ["key"].lower ()==pal_key .lower ():
                            item ["value"]=True 
                            found =True 
                            break 
                    if not found :
                        unlock_list .append ({"key":pal_key ,"value":True })
                    json_to_sav (player_json ,self .player_sav_path )
                self ._load_pals ()
                if tab_name ==t ("edit_pals.party"):
                    tab =self .party_tab 
                elif tab_name ==t ("edit_pals.palbox"):
                    tab =self .palbox_tab 
                self ._on_pal_widget_selected (slot_index ,tab ,tab_name )
                pal_name =selected_pal ["name"]
                QMessageBox .information (self ,"Success",f"Created new {pal_name } in {container_name } slot {slot_index }.")
        except Exception as e :
            print (f"Error creating pal at slot: {e }")
            QMessageBox .warning (self ,"Error",f"Failed to create pal: {e }")
    def _max_all (self ):
        QMessageBox .information (self ,"Info","Max All functionality not implemented yet")
    def _delete_dps_pal (self ,tab ,slot_index ):
        if not hasattr (tab ,'widget_list'):
            return 
        widget =tab .widget_list [slot_index ]
        if not widget .pal_data :
            return 
        pal_data =widget .pal_data 
        raw_data =pal_data .get ('data')
        widget .pal_data =None 
        widget ._setup_ui ()
        if self .dps_json and raw_data :
            save_parameter_array =self .dps_json ['properties'].get ('SaveParameterArray',{}).get ('value',{}).get ('values',[])
            for i ,entry in enumerate (save_parameter_array ):
                if entry ['SaveParameter']['value']is raw_data :
                    save_parameter_array .pop (i )
                    break 
        for i ,pal_item in enumerate (tab .pal_data ):
            if pal_item .get ('data')is raw_data :
                tab .pal_data .pop (i )
                break 
        tab .selected_pal_index =-1 
        self ._update_tab_pal_display (tab ,-1 )
        tab .pal_name_label .setText (t ("edit_pals.no_pal_selected"))
    def _add_dps_pal (self ,tab ,slot_index ,character_id ,nickname ):
        if not self .dps_json :
            return 
        save_parameter_array =self .dps_json ['properties'].get ('SaveParameterArray',{}).get ('value',{}).get ('values',[])
        if slot_index >=len (save_parameter_array ):
            return 
        widget =tab .widget_list [slot_index ]
        raw =None 
        if widget .pal_data and widget .pal_data .get ('data'):
            target_raw =widget .pal_data .get ('data')
            for e in save_parameter_array :
                if e ['SaveParameter']['value']is target_raw :
                    raw =e ['SaveParameter']['value']
                    break 
        else :
            for e in save_parameter_array :
                entry_raw =e ['SaveParameter']['value']
                cid =extract_value (entry_raw ,'CharacterID','')
                if cid =='None'or cid =='':
                    raw =entry_raw 
                    break 
        if not raw :
            return 
        instance_id =str (uuid .uuid4 ()).upper ()
        empty_uuid ="00000000-0000-0000-0000-000000000000"
        time_val =638486453957560000 
        raw ['CharacterID']={'id':None ,'type':'NameProperty','value':character_id }
        raw ['NickName']={'id':None ,'type':'StrProperty','value':nickname }
        raw ['FilteredNickName']={'id':None ,'type':'StrProperty','value':nickname }
        raw ['Gender']={'id':None ,'type':'EnumProperty','value':{'type':'EPalGenderType','value':'EPalGenderType::Female'}}
        raw ['Level']={'id':None ,'type':'ByteProperty','value':{'type':'None','value':1 }}
        raw ['Exp']={'id':None ,'type':'Int64Property','value':0 }
        raw ['Rank']={'id':None ,'type':'ByteProperty','value':{'type':'None','value':1 }}
        raw ['Talent_HP']={'id':None ,'type':'ByteProperty','value':{'type':'None','value':50 }}
        raw ['Talent_Shot']={'id':None ,'type':'ByteProperty','value':{'type':'None','value':50 }}
        raw ['Talent_Defense']={'id':None ,'type':'ByteProperty','value':{'type':'None','value':50 }}
        raw ['Rank_HP']={'id':None ,'type':'ByteProperty','value':{'type':'None','value':0 }}
        raw ['Rank_Attack']={'id':None ,'type':'ByteProperty','value':{'type':'None','value':0 }}
        raw ['Rank_Defence']={'id':None ,'type':'ByteProperty','value':{'type':'None','value':0 }}
        raw ['Rank_CraftSpeed']={'id':None ,'type':'ByteProperty','value':{'type':'None','value':0 }}
        raw ['Hp']={'struct_type':'FixedPoint64','struct_id':empty_uuid ,'id':None ,'value':{'Value':{'id':None ,'value':545000 ,'type':'Int64Property'}},'type':'StructProperty'}
        raw ['FullStomach']={'id':None ,'type':'FloatProperty','value':150.0 }
        raw ['OwnerPlayerUId']={'struct_type':'Guid','struct_id':empty_uuid ,'id':None ,'value':self .player_uid ,'type':'StructProperty'}
        raw ['IsRarePal']={'value':False ,'id':None ,'type':'BoolProperty'}
        raw ['IsPlayer']={'value':False ,'id':None ,'type':'BoolProperty'}
        raw ['OwnedTime']={'struct_type':'DateTime','struct_id':empty_uuid ,'id':None ,'value':time_val ,'type':'StructProperty'}
        raw ['OldOwnerPlayerUIds']={'array_type':'StructProperty','id':None ,'value':{'prop_name':'OldOwnerPlayerUIds','prop_type':'StructProperty','values':[self .player_uid ],'type_name':'Guid','id':empty_uuid },'type':'ArrayProperty'}
        raw ['LastNickNameModifierPlayerUid']={'struct_type':'Guid','struct_id':empty_uuid ,'id':None ,'value':self .player_uid ,'type':'StructProperty'}
        raw ['EquipWaza']={'array_type':'EnumProperty','id':None ,'value':{'values':[]},'type':'ArrayProperty'}
        raw ['MasteredWaza']={'array_type':'EnumProperty','id':None ,'value':{'values':[]},'type':'ArrayProperty'}
        raw ['PassiveSkillList']={'array_type':'NameProperty','id':None ,'value':{'values':[]},'type':'ArrayProperty'}
        raw ['GotStatusPointList']={'array_type':'StructProperty','id':None ,'value':{'prop_name':'GotStatusPointList','prop_type':'StructProperty','values':[],'type_name':'PalGotStatusPoint','id':empty_uuid },'type':'ArrayProperty'}
        raw ['GotExStatusPointList']={'array_type':'StructProperty','id':None ,'value':{'prop_name':'GotExStatusPointList','prop_type':'StructProperty','values':[],'type_name':'PalGotStatusPoint','id':empty_uuid },'type':'ArrayProperty'}
        raw ['ItemContainerId']={'struct_type':'PalContainerId','struct_id':empty_uuid ,'id':None ,'value':{'ID':{'struct_type':'Guid','struct_id':empty_uuid ,'id':None ,'value':empty_uuid ,'type':'StructProperty'}},'type':'StructProperty'}
        raw ['ShieldHP']={'struct_type':'FixedPoint64','struct_id':empty_uuid ,'id':None ,'value':{'Value':{'id':None ,'value':0 ,'type':'Int64Property'}},'type':'StructProperty'}
        if 'SlotId'in raw :
            raw ['SlotId']['value']['SlotIndex']['value']=slot_index 
        new_pal_item ={'index':slot_index ,'data':raw }
        tab .pal_data .append (new_pal_item )
        if hasattr (tab ,'widget_list')and slot_index <tab .max_slots :
            widget =tab .widget_list [slot_index ]
            widget .pal_data =new_pal_item 
            widget ._setup_ui ()
            widget .set_selected (True )
            widget .update ()
            widget .repaint ()
            QApplication .processEvents ()
        tab .selected_pal_index =slot_index 
        self ._update_tab_pal_display (tab ,slot_index )
    def showEvent (self ,event ):
        super ().showEvent (event )
        if not event .spontaneous ():
            try :
                from palworld_aio .ui .tools_tab import center_on_parent 
                center_on_parent (self )
            except ImportError :
                from ..ui .tools_tab import center_on_parent 
                center_on_parent (self )
            self .activateWindow ()
            self .raise_ ()
class PalFrame (QFrame ):
    _maps_loaded =False 
    _NAMEMAP ={}
    _PASSMAP ={}
    _SKILLMAP ={}
    @classmethod 
    def _load_maps (cls ):
        if cls ._maps_loaded :
            return 
        base_dir =os .path .dirname (os .path .dirname (os .path .abspath (__file__ )))
        def load_map (fname ,key ):
            try :
                fp =os .path .join (base_dir ,'resources','game_data',fname )
                with open (fp ,'r',encoding ='utf-8')as f :
                    js =json .load (f )
                    if not isinstance (js ,dict ):
                        return {}
                    data =js .get (key ,[])
                    result ={}
                    for x in data :
                        if isinstance (x ,dict )and 'asset'in x and 'name'in x :
                            result [x ['asset'].lower ()]=x ['name']
                    return result 
            except Exception as e :
                import traceback 
                traceback .print_exc ()
                return {}
        cls ._PASSMAP =load_map ('passivedata.json','passives')
        cls ._SKILLMAP =load_map ('skilldata.json','skills')
        PALMAP =load_map ('paldata.json','pals')
        NPCMAP =load_map ('npcdata.json','npcs')
        cls ._NAMEMAP ={**PALMAP ,**NPCMAP }
        cls ._maps_loaded =True 
    def __init__ (self ,pal_item ,parent =None ):
        super ().__init__ (parent )
        self ._load_maps ()
        self .pal_item =pal_item 
        self .setFrameStyle (QFrame .Box )
        self .setMinimumSize (400 ,150 )
        self .setMaximumSize (400 ,150 )
        self ._setup_ui ()
    def _setup_ui (self ):
        layout =QHBoxLayout (self )
        layout .setContentsMargins (10 ,10 ,10 ,10 )
        layout .setSpacing (15 )
        image_label =QLabel ("No Image")
        image_label .setAlignment (Qt .AlignCenter )
        image_label .setFixedSize (80 ,80 )
        image_label .setStyleSheet ("""
            QLabel {
                border: 2px solid #ccc;
                border-radius: 40px;
                background-color: #f0f0f0;
                padding: 5px;
            }
        """)
        layout .addWidget (image_label )
        right_layout =QVBoxLayout ()
        right_layout .setSpacing (5 )
        name_label =QLabel ("Unknown Pal")
        name_label .setStyleSheet ("font-weight: bold; font-size: 14px;")
        right_layout .addWidget (name_label )
        level_exp_layout =QHBoxLayout ()
        level_exp_layout .setSpacing (10 )
        level_label =QLabel ("Level: ?")
        level_label .setStyleSheet ("font-size: 12px;")
        level_exp_layout .addWidget (level_label )
        exp_label =QLabel ("Exp: ?")
        exp_label .setStyleSheet ("font-size: 12px;")
        level_exp_layout .addWidget (exp_label )
        level_exp_layout .addStretch ()
        right_layout .addLayout (level_exp_layout )
        stats_label =QLabel ("HP: ? ATK: ? DEF: ?")
        stats_label .setStyleSheet ("font-size: 12px;")
        right_layout .addWidget (stats_label )
        moves_label =QLabel ("Moves: None")
        moves_label .setWordWrap (True )
        moves_label .setStyleSheet ("font-size: 12px;")
        right_layout .addWidget (moves_label )
        passives_label =QLabel ("Passives: None")
        passives_label .setWordWrap (True )
        passives_label .setStyleSheet ("font-size: 12px;")
        right_layout .addWidget (passives_label )
        right_layout .addStretch ()
        layout .addLayout (right_layout )
        self .name_label =name_label 
        self .level_label =level_label 
        self .exp_label =exp_label 
        self .stats_label =stats_label 
        self .moves_label =moves_label 
        self .passives_label =passives_label 
        self ._load_pal_data ()
    def _load_pal_data (self ):
        self .update_pal_data (self .pal_item )
    def update_pal_data (self ,pal_item ):
        self .pal_item =pal_item 
        if not pal_item :
            self .name_label .setText ("No Pals")
            self .level_label .setText ("Level: -")
            self .exp_label .setText ("Exp: -")
            self .stats_label .setText ("HP: - ATK: - DEF: -")
            self .moves_label .setText ("Moves: None")
            self .passives_label .setText ("Passives: None")
            return 
        try :
            raw =pal_item ['value']['RawData']['value']['object']['SaveParameter']['value']
            cid =extract_value (raw ,'CharacterID','')
            character_key =format_character_key (cid )
            level =extract_value (raw ,'Level',1 )
            exp =extract_value (raw ,'Exp',0 )
            talent_hp =extract_value (raw ,'Talent_HP',0 )
            talent_shot =extract_value (raw ,'Talent_Shot',0 )
            talent_defense =extract_value (raw ,'Talent_Defense',0 )
            rank_hp =extract_value (raw ,'Rank_HP',0 )
            rank_attack =extract_value (raw ,'Rank_Attack',0 )
            rank_defense =extract_value (raw ,'Rank_Defence',0 )
            is_boss =cid .upper ().startswith ('BOSS_')or extract_value (raw ,'IsRarePal',False )
            is_lucky =extract_value (raw ,'IsRarePal',False )
            hp =extract_value (raw ,'Hp',0 )
            atk =extract_value (raw ,'Attack',0 )
            defense =extract_value (raw ,'Defense',0 )
            passive_skill_data =raw .get ('PassiveSkillList',{})
            if isinstance (passive_skill_data ,dict ):
                p_list =passive_skill_data .get ('value',{}).get ('values',[])
            elif isinstance (passive_skill_data ,list ):
                p_list =passive_skill_data 
            nick =extract_value (raw ,'NickName','')
            pal_name =self ._NAMEMAP .get (cid .lower (),cid )
            if nick :
                pal_name =f"{pal_name } ({nick })"
            self .name_label .setText (pal_name )
            self .name_label .repaint ()
            self .repaint ()
            self .level_label .setText (f"Level: {level }")
            self .exp_label .setText (f"Exp: {exp }")
            self .stats_label .setText (f"HP: {hp } ATK: {atk } DEF: {defense }")
            equip_waza_data =raw .get ('EquipWaza',{})
            if isinstance (equip_waza_data ,dict ):
                e_list =equip_waza_data .get ('value',{}).get ('values',[])
            elif isinstance (equip_waza_data ,list ):
                e_list =equip_waza_data 
            else :
                e_list =[]
            moves =[]
            for w in e_list :
                if w :
                    w_clean =w .split ('::')[-1 ].lower ()
                    move_name =self ._SKILLMAP .get (w_clean ,w .split ('::')[-1 ])
                    moves .append (move_name )
            self .moves_label .setText (f"Moves: {', '.join (moves )if moves else 'None'}")
            passives =[self ._PASSMAP .get (p .lower (),p )for p in p_list ]
            self .passives_label .setText (f"Passives: {', '.join (passives )if passives else 'None'}")
        except Exception as e :
            pass 
