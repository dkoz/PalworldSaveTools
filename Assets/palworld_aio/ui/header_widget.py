import os 
from PySide6 .QtWidgets import (
QWidget ,QHBoxLayout ,QLabel ,QPushButton ,QToolButton ,
QSpacerItem ,QSizePolicy ,QStyle 
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
        'nf-fa-window_maximize':'\uf2d0',
        'nf-fa-close':'\uf00d',
        'nf-fa-discord':'\uf392',
        'nf-cod-triangle_left':'\ueb9b',
        'nf-cod-triangle_right':'\ueb9c'
        }
from i18n import t 
from common import get_versions 
try :
    from palworld_aio import constants 
except ImportError :
    from ..import constants 
class HeaderWidget (QWidget ):
    minimize_clicked =Signal ()
    maximize_clicked =Signal ()
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
        self.game_version_label = QLabel(f"{nf.icons['nf-fa-save']} {game_version}")
        self.game_version_label.setObjectName("gameVersionChip")
        self.game_version_label.setFont(QFont("Hack Nerd Font", 11))
        layout.addWidget(self.game_version_label, alignment=Qt.AlignVCenter)
        info_btn = QToolButton()
        info_btn.setObjectName("hdrBtn")
        info_btn.setToolTip(t("about.title") if t else "About PST")
        try:
            info_btn.setIcon(self.style().standardIcon(QStyle.SP_MessageBoxInformation))
        except:
            pass
        info_btn.setIconSize(QSize(26, 26))
        info_btn.clicked.connect(self.about_clicked.emit)
        layout.addWidget(info_btn)
        self.warn_btn = QToolButton()
        self.warn_btn.setObjectName("hdrBtn")
        self.warn_btn.setToolTip(f"Warnings (Palworld v{game_version})")
        try:
            self.warn_btn.setIcon(self.style().standardIcon(QStyle.SP_MessageBoxWarning))
        except:
            pass
        self.warn_btn.setStyleSheet("color: #FFD24D;")
        self.warn_btn.setIconSize(QSize(26, 26))
        self.warn_btn.setVisible(False)
        layout.addWidget(self.warn_btn)
        layout.addItem(QSpacerItem(20, 10, QSizePolicy.Expanding, QSizePolicy.Minimum))
        self .sidebar_btn =QPushButton (nf.icons['nf-cod-triangle_left'])
        self .sidebar_btn .setObjectName ("sidebarChip")
        self .sidebar_btn .setFlat (True )
        self .sidebar_btn .setToolTip (t ("Collapse Sidebar")if t else "Collapse Sidebar")
        self .sidebar_btn .setFont (QFont ("Hack Nerd Font",14 ))
        self .sidebar_btn .clicked .connect (self .sidebar_toggle_clicked .emit )
        layout .addWidget (self .sidebar_btn )
        theme_btn = QPushButton(nf.icons['nf-md-theme_light_dark'])
        theme_btn.setObjectName("themeChip")
        theme_btn.setFlat(True)
        theme_btn.setToolTip(t("toggle_theme") if t else "Toggle Theme")
        theme_btn.setFont(QFont("Hack Nerd Font", 14))
        theme_btn.clicked.connect(self.theme_toggle_clicked.emit)
        layout.addWidget(theme_btn)
        discord_btn = QPushButton(nf.icons['nf-fa-discord'])
        discord_btn.setObjectName("discordChip")
        discord_btn.setFlat(True)
        discord_btn.setToolTip("Join Discord")
        discord_btn.setFont(QFont("Hack Nerd Font", 14))
        discord_btn.clicked.connect(self._open_discord)
        layout.addWidget(discord_btn)
        minimize_btn =QPushButton (nf .icons ['nf-md-circle_medium'])
        minimize_btn .setObjectName ("controlChip")
        minimize_btn .setFlat (True )
        minimize_btn .setToolTip ("Minimize")
        minimize_btn .setFont (QFont ("Hack Nerd Font",14 ))
        minimize_btn .clicked .connect (self .minimize_clicked .emit )
        layout .addWidget (minimize_btn )
        maximize_btn =QPushButton (nf .icons ['nf-fa-window_maximize'])
        maximize_btn .setObjectName ("controlChip")
        maximize_btn .setFlat (True )
        maximize_btn .setToolTip ("Maximize")
        maximize_btn .setFont (QFont ("Hack Nerd Font",14 ))
        maximize_btn .clicked .connect (self .maximize_clicked .emit )
        layout .addWidget (maximize_btn )
        close_btn =QPushButton (nf .icons ['nf-fa-close'])
        close_btn .setObjectName ("controlChip")
        close_btn .setFlat (True )
        close_btn .setToolTip ("Close")
        close_btn .setFont (QFont ("Hack Nerd Font",14 ))
        close_btn .clicked .connect (self .close_clicked .emit )
        layout .addWidget (close_btn )
    def _open_github (self ,event ):
        import webbrowser
        import webbrowser
        webbrowser .open ("https://github.com/deafdudecomputers/PalworldSaveTools/releases/latest")
    def _open_discord(self):
        import webbrowser
        webbrowser.open("https://discord.gg/YWZFPy9G8J")
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
            self .sidebar_btn .setText (nf.icons['nf-cod-triangle_right'])
            self .sidebar_btn .setToolTip (t ("Expand Sidebar")if t else "Expand Sidebar")
        else :
            self .sidebar_btn .setText (nf.icons['nf-cod-triangle_left'])
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
    def refresh_labels (self ):
        if hasattr (self ,'menu_chip_btn'):
            self .menu_chip_btn .setText (f"{nf .icons ['nf-md-menu']} {t ('menu_button')if t else 'Menu'}")
            self .menu_chip_btn .setToolTip (t ("Open Menu")if t else "Open Menu")
        if hasattr (self ,'sidebar_btn'):
            collapsed =self .sidebar_btn .text ()==nf.icons['nf-cod-triangle_right']
            self .set_sidebar_collapsed (collapsed )
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
