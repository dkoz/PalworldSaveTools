import os 
from PySide6 .QtWidgets import (
QWidget ,QHBoxLayout ,QLabel ,QPushButton ,QToolButton ,
QSpacerItem ,QSizePolicy ,QMenu ,QStyle 
)
from PySide6 .QtCore import Qt ,Signal ,QSize ,QPoint ,QTimer 
from PySide6 .QtGui import QPixmap ,QFont ,QCursor ,QFontDatabase 
try :
    import nerdfont as nf 
except :
    class nf :
        icons ={
        'nf-cod-github':'\ue708',
        'nf-fa-save':'\uf0c7',
        'nf-md-menu':'\U000f035c',
        'nf-md-theme_light_dark':'\U000f0cde',
        'nf-md-cog':'\U000f0493',
        'nf-md-information':'\U000f02fd',
        'nf-md-circle_medium':'\U000f09df',
        'nf-fa-close':'\uf00d'
        }
from i18n import t 
from common import get_versions 
try :
    from palworld_aio import constants 
except ImportError :
    from ..import constants 
class HeaderWidget (QWidget ):
    minimize_clicked =Signal ()
    close_clicked =Signal ()
    theme_toggle_clicked =Signal ()
    about_clicked =Signal ()
    sidebar_toggle_clicked =Signal ()
    def __init__ (self ,parent =None ):
        super ().__init__ (parent )
        self .is_dark_mode =True 
        self ._pulse_timer =None 
        self ._update_available =False 
        self ._latest_version =None 
        self ._load_nerd_font ()
        self ._setup_ui ()
        self .update_logo ()
    def __del__ (self ):
        self .stop_pulse_animation ()
    def _load_nerd_font (self ):
        font_path =os .path .join (constants .get_assets_path (),"resources","HackNerdFont-Regular.ttf")
        if os .path .exists (font_path ):
            families =QFontDatabase .families ()
            if "Hack Nerd Font"not in families :
                font_id =QFontDatabase .addApplicationFont (font_path )
                if font_id ==-1 :
                    print ("Warning: Failed to load HackNerdFont-Regular.ttf")
    def _setup_ui (self ):
        layout =QHBoxLayout (self )
        layout .setSpacing (8 )
        layout .setContentsMargins (10 ,5 ,10 ,5 )
        self .logo_label =QLabel ()
        self .logo_label .setObjectName ("title")
        layout .addWidget (self .logo_label )
        layout .addSpacing (8 )
        self .menu_chip_btn =QPushButton (f"{nf .icons ['nf-md-menu']} {t ('menu_button')if t else 'Menu'}")
        self .menu_chip_btn .setObjectName ("menuChip")
        self .menu_chip_btn .setFlat (True )
        self .menu_chip_btn .setToolTip (t ("Open Menu")if t else "Open Menu")
        self .menu_chip_btn .setFont (QFont ("Hack Nerd Font",11 ))
        self .menu_chip_btn .setCursor (QCursor (Qt .PointingHandCursor ))
        self .menu_chip_btn .clicked .connect (self ._show_menu_popup )
        layout .addWidget (self .menu_chip_btn ,alignment =Qt .AlignVCenter )
        layout .addSpacing (8 )
        self ._menu_popup =None 
        tools_version ,game_version =get_versions ()
        self .app_version_label =QLabel (f"{nf .icons ['nf-cod-github']} {tools_version }")
        self .app_version_label .setObjectName ("versionChip")
        self .app_version_label .setCursor (QCursor (Qt .PointingHandCursor ))
        self .app_version_label .setFont (QFont ("Hack Nerd Font",11 ))
        self .app_version_label .setToolTip ("Click to open GitHub repository")
        self .app_version_label .mousePressEvent =self ._open_github 
        layout .addWidget (self .app_version_label ,alignment =Qt .AlignVCenter )
        self .game_version_label =QLabel (f"{nf .icons ['nf-fa-save']} {game_version }")
        self .game_version_label .setObjectName ("gameVersionChip")
        self .game_version_label .setFont (QFont ("Hack Nerd Font",11 ))
        layout .addWidget (self .game_version_label ,alignment =Qt .AlignVCenter )
        layout .addItem (QSpacerItem (20 ,10 ,QSizePolicy .Expanding ,QSizePolicy .Minimum ))
        self .warn_btn =QToolButton ()
        self .warn_btn .setObjectName ("hdrBtn")
        self .warn_btn .setToolTip (f"Warnings (Palworld v{game_version })")
        try :
            self .warn_btn .setIcon (self .style ().standardIcon (QStyle .SP_MessageBoxWarning ))
        except :
            pass 
        self .warn_btn .setStyleSheet ("color: #FFD24D;")
        self .warn_btn .setIconSize (QSize (26 ,26 ))
        self .warn_btn .setVisible (False )
        layout .addWidget (self .warn_btn )
        self .sidebar_btn =QPushButton ("\u25C0")
        self .sidebar_btn .setObjectName ("controlChip")
        self .sidebar_btn .setFlat (True )
        self .sidebar_btn .setToolTip (t ("Collapse Sidebar")if t else "Collapse Sidebar")
        self .sidebar_btn .setFont (QFont ("Consolas",14 ))
        self .sidebar_btn .clicked .connect (self .sidebar_toggle_clicked .emit )
        layout .addWidget (self .sidebar_btn )
        dropdown_btn =QPushButton (nf .icons ['nf-md-menu'])
        dropdown_btn .setObjectName ("controlChip")
        dropdown_btn .setFlat (True )
        dropdown_btn .setToolTip ("Menu")
        dropdown_btn .setFont (QFont ("Hack Nerd Font",14 ))
        self .dropdown_menu =QMenu ()
        self ._update_dropdown_menu ()
        dropdown_btn .clicked .connect (
        lambda :self .dropdown_menu .exec (dropdown_btn .mapToGlobal (QPoint (0 ,dropdown_btn .height ())))
        )
        layout .addWidget (dropdown_btn )
        minimize_btn =QPushButton (nf .icons ['nf-md-circle_medium'])
        minimize_btn .setObjectName ("controlChip")
        minimize_btn .setFlat (True )
        minimize_btn .setToolTip ("Minimize")
        minimize_btn .setFont (QFont ("Hack Nerd Font",14 ))
        minimize_btn .clicked .connect (self .minimize_clicked .emit )
        layout .addWidget (minimize_btn )
        close_btn =QPushButton (nf .icons ['nf-fa-close'])
        close_btn .setObjectName ("controlChip")
        close_btn .setFlat (True )
        close_btn .setToolTip ("Close")
        close_btn .setFont (QFont ("Hack Nerd Font",14 ))
        close_btn .clicked .connect (self .close_clicked .emit )
        layout .addWidget (close_btn )
    def _open_github (self ,event ):
        import webbrowser 
        webbrowser .open ("https://github.com/deafdudecomputers/PalworldSaveTools/releases/latest")
    def update_logo (self ):
        base_path =constants .get_assets_path ()
        logo_name ='PalworldSaveTools_Blue.png'if self .is_dark_mode else 'PalworldSaveTools_Black.png'
        logo_path =os .path .join (base_path ,'resources',logo_name )
        if os .path .exists (logo_path ):
            pixmap =QPixmap (logo_path )
            if not pixmap .isNull ():
                scaled =pixmap .scaledToHeight (44 ,Qt .SmoothTransformation )
                self .logo_label .setPixmap (scaled )
                self .logo_label .setFixedSize (scaled .size ())
        else :
            self .logo_label .setText ("PALWORLD SAVE TOOLS")
            self .logo_label .setFont (QFont ("",14 ,QFont .Bold ))
    def set_theme (self ,is_dark ):
        self .is_dark_mode =is_dark 
        self .update_logo ()
    def show_warning (self ,show =True ):
        self .warn_btn .setVisible (show )
    def set_sidebar_collapsed (self ,collapsed ):
        if collapsed :
            self .sidebar_btn .setText ("\u25B6")
            self .sidebar_btn .setToolTip (t ("Expand Sidebar")if t else "Expand Sidebar")
        else :
            self .sidebar_btn .setText ("\u25C0")
            self .sidebar_btn .setToolTip (t ("Collapse Sidebar")if t else "Collapse Sidebar")
    def start_pulse_animation (self ,latest_version ):
        if self ._pulse_timer is not None :
            return 
        self ._update_available =True 
        self ._latest_version =latest_version 
        self .app_version_label .setProperty ("pulse","true")
        self .app_version_label .style ().polish (self .app_version_label )
        self ._pulse_timer =QTimer ()
        self ._pulse_timer .timeout .connect (self ._toggle_pulse )
        self ._pulse_timer .start (500 )
    def _toggle_pulse (self ):
        current =self .app_version_label .property ("pulse")
        new_val ="false"if current =="true"else "true"
        self .app_version_label .setProperty ("pulse",new_val )
        self .app_version_label .style ().polish (self .app_version_label )
    def stop_pulse_animation (self ):
        if self ._pulse_timer :
            try :
                self ._pulse_timer .stop ()
            except RuntimeError :
                pass 
            self ._pulse_timer =None 
        try :
            self .app_version_label .setProperty ("pulse","false")
            self .app_version_label .style ().polish (self .app_version_label )
        except RuntimeError :
            pass 
        self ._update_available =False 
    def update_version_text (self ,local_version ,latest_version =None ):
        self .app_version_label .setText (f"{nf .icons ['nf-cod-github']} {local_version }")
    def _show_menu_popup (self ):
        from ..widgets import MenuPopup 
        if self ._menu_popup is None :
            self ._menu_popup =MenuPopup (self )
        btn_pos =self .menu_chip_btn .mapToGlobal (QPoint (0 ,self .menu_chip_btn .height ()))
        self ._menu_popup .show_at (btn_pos )
    def _update_dropdown_menu (self ):
        self .dropdown_menu .clear ()
        action_toggle =self .dropdown_menu .addAction (nf .icons ['nf-md-theme_light_dark']+" "+(t ("toggle_theme")if t else "Toggle Theme"))
        self .dropdown_menu .addSeparator ()
        action_about =self .dropdown_menu .addAction (nf .icons ['nf-md-information']+" "+(t ("about.title")if t else "About PST"))
        action_toggle .triggered .connect (self .theme_toggle_clicked .emit )
        action_about .triggered .connect (self .about_clicked .emit )
    def refresh_labels (self ):
        if hasattr (self ,'menu_chip_btn'):
            self .menu_chip_btn .setText (f"{nf .icons ['nf-md-menu']} {t ('menu_button')if t else 'Menu'}")
            self .menu_chip_btn .setToolTip (t ("Open Menu")if t else "Open Menu")
        if hasattr (self ,'sidebar_btn'):
            collapsed =self .sidebar_btn .text ()=="\u25B6"
            self .set_sidebar_collapsed (collapsed )
        if hasattr (self ,'dropdown_menu'):
            self ._update_dropdown_menu ()
    def set_menu_actions (self ,actions_dict ):
        from ..widgets import MenuPopup 
        if self ._menu_popup is None :
            self ._menu_popup =MenuPopup (self )
        self ._menu_popup .set_menu_actions (actions_dict )
    def get_menu_popup (self ):
        from ..widgets import MenuPopup 
        if self ._menu_popup is None :
            self ._menu_popup =MenuPopup (self )
        return self ._menu_popup
