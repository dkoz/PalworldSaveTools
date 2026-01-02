from PySide6 .QtWidgets import (
QWidget ,QVBoxLayout ,QHBoxLayout ,QPushButton ,QFrame ,
QGraphicsDropShadowEffect ,QMenu ,QLabel 
)
from PySide6 .QtCore import Qt ,QPoint ,Signal 
from PySide6 .QtGui import QFont ,QColor ,QCursor 
try :
    import nerdfont as nf 
except :
    class nf :
        icons ={
        'nf-md-file':'\U000f0214',
        'nf-md-function':'\U000f0295',
        'nf-md-map':'\U000f034d',
        'nf-md-playlist_remove':'\U000f0413',
        'nf-md-translate':'\U000f05ca',
        'nf-md-chevron_right':'\U000f0142',
        }
from i18n import t 
try :
    from palworld_aio import constants 
except ImportError :
    from ..import constants 
class MenuPopup (QWidget ):

    popup_closed =Signal ()
    def __init__ (self ,parent =None ):
        super ().__init__ (parent )
        self .setObjectName ("menuPopup")
        self .setWindowFlags (Qt .Popup |Qt .FramelessWindowHint )
        self .setAttribute (Qt .WA_TranslucentBackground )
        self ._menu_actions ={}
        self ._setup_ui ()
    def _setup_ui (self ):

        self .container =QFrame (self )
        self .container .setObjectName ("menuPopupContainer")
        layout =QVBoxLayout (self )
        layout .setContentsMargins (0 ,0 ,0 ,0 )
        layout .addWidget (self .container )
        inner_layout =QVBoxLayout (self .container )
        inner_layout .setContentsMargins (8 ,8 ,8 ,8 )
        inner_layout .setSpacing (4 )
        self .menu_buttons ={}
        categories =[
        ('file','nf-md-file',t ('deletion.menu.file')if t else 'File'),
        ('functions','nf-md-function',t ('deletion.menu.delete')if t else 'Functions'),
        ('maps','nf-md-map',t ('deletion.menu.view')if t else 'Maps'),
        ('exclusions','nf-md-playlist_remove',t ('deletion.menu.exclusions')if t else 'Exclusions'),
        ('languages','nf-md-translate',t ('lang.label')if t else 'Languages'),
        ]
        for key ,icon_key ,label in categories :
            btn =self ._create_menu_button (key ,icon_key ,label )
            inner_layout .addWidget (btn )
            self .menu_buttons [key ]=btn 
        shadow =QGraphicsDropShadowEffect (self )
        shadow .setBlurRadius (20 )
        shadow .setOffset (3 ,3 )
        shadow .setColor (QColor (0 ,0 ,0 ,120 ))
        self .container .setGraphicsEffect (shadow )
        self .container .setStyleSheet ("""
            QFrame#menuPopupContainer {
                background: rgba(18, 20, 24, 0.95);
                border: 1px solid rgba(125, 211, 252, 0.2);
                border-radius: 10px;
            }
        """)
    def _create_menu_button (self ,key ,icon_key ,label ):

        try :
            icon =nf .icons .get (icon_key ,'')
        except :
            icon =''
        chevron ='\u25B6'
        btn =QPushButton (f"  {icon }  {label }  {chevron }")
        btn .setObjectName ("menuPopupButton")
        btn .setFlat (True )
        btn .setCursor (QCursor (Qt .PointingHandCursor ))
        btn .setFont (QFont (constants .FONT_FAMILY ,11 ))
        btn .setMinimumWidth (180 )
        btn .setMinimumHeight (36 )
        btn .clicked .connect (lambda checked ,k =key ,b =btn :self ._show_submenu (k ,b ))
        btn .setStyleSheet ("""
            QPushButton#menuPopupButton {
                background: transparent;
                border: none;
                padding: 8px 12px;
                border-radius: 6px;
                text-align: left;
                color: #A6B8C8;
            }
            QPushButton#menuPopupButton:hover {
                background: rgba(125, 211, 252, 0.1);
                color: #7DD3FC;
            }
            QPushButton#menuPopupButton:pressed {
                background: rgba(125, 211, 252, 0.2);
            }
        """)
        return btn 
    def set_menu_actions (self ,actions_dict ):

        self ._menu_actions =actions_dict 
    def _show_submenu (self ,category ,button ):

        if category not in self ._menu_actions :
            return 
        actions =self ._menu_actions .get (category ,[])
        if not actions :
            return 
        menu =QMenu (self )
        for item in actions :
            if len (item )>=3 and item [2 ]=='separator':
                menu .addSeparator ()
            text ,callback =item [0 ],item [1 ]
            action =menu .addAction (text )
            action .triggered .connect (callback )
            if len (item )>=3 and item [2 ]=='separator_after':
                menu .addSeparator ()
        btn_pos =button .mapToGlobal (QPoint (button .width (),0 ))
        menu .exec (btn_pos )
        self .close ()
    def show_at (self ,global_pos ):

        self .adjustSize ()
        self .move (global_pos )
        self .show ()
        self .raise_ ()
