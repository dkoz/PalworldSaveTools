from PySide6 .QtWidgets import (
QWidget ,QVBoxLayout ,QHBoxLayout ,QPushButton ,QFrame ,
QGraphicsDropShadowEffect ,QMenu ,QLabel 
)
from PySide6 .QtCore import Qt ,QPoint ,Signal ,QTimer ,QEvent ,QRect 
from PySide6 .QtGui import QFont ,QColor ,QCursor ,QEnterEvent ,QGuiApplication 
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
class HoverMenuButton (QPushButton ):
    def __init__ (self ,category ,icon_key ,label ,parent =None ):
        try :
            icon =nf .icons .get (icon_key ,'')
        except :
            icon =''
        chevron ='\u25B6'
        super ().__init__ (f"  {icon }  {label }  {chevron }",parent )
        self .category =category 
        self .setObjectName ("menuPopupButton")
        self .setFlat (True )
        self .setCursor (QCursor (Qt .PointingHandCursor ))
        self .setFont (QFont (constants .FONT_FAMILY ,11 ))
        self .setMinimumWidth (180 )
        self .setMinimumHeight (36 )
        self .clicked .connect (self ._on_clicked )
        self .setStyleSheet ("""
            QPushButton#menuPopupButton {
                background: transparent;
                border: none;
                padding: 8px 12px;
                border-radius: 6px;
                text-align: left;
                color: #A6B8C8;
            }
            QPushButton#menuPopupButton[hovered="true"] {
                background: rgba(125, 211, 252, 0.1);
                color: #7DD3FC;
            }
            QPushButton#menuPopupButton[active="true"] {
                background: rgba(125, 211, 252, 0.15);
                color: #7DD3FC;
                border-left: 3px solid #7DD3FC;
            }
            QPushButton#menuPopupButton:pressed {
                background: rgba(125, 211, 252, 0.2);
            }
        """)
    def _on_clicked (self ):
        self ._show_submenu ()
    def _show_submenu (self ):
        parent_popup =self .parent ()
        while parent_popup and not isinstance (parent_popup ,MenuPopup ):
            parent_popup =parent_popup .parent ()
        if parent_popup and isinstance (parent_popup ,MenuPopup ):
            parent_popup ._show_submenu (self .category ,self )
class MenuPopup (QWidget ):
    popup_closed =Signal ()
    def __init__ (self ,parent =None ):
        super ().__init__ (parent )
        self .setObjectName ("menuPopup")
        self .setWindowFlags (Qt .Popup |Qt .FramelessWindowHint )
        self .setAttribute (Qt .WA_TranslucentBackground )
        self ._menu_actions ={}
        self ._current_menu =None 
        self ._current_category =None 
        self ._cursor_timer =QTimer (self )
        self ._cursor_timer .timeout .connect (self ._check_cursor_position )
        self ._setup_ui ()
    def _is_point_in_widget (self ,point ,widget ):
        if not widget .isVisible ():
            return False 
        global_pos =widget .mapToGlobal (QPoint (0 ,0 ))
        rect =widget .rect ()
        global_rect =QRect (global_pos ,rect .size ())
        return global_rect .contains (point )
    def _check_cursor_position (self ):
        cursor_pos =QGuiApplication .primaryScreen ().availableGeometry ().topLeft ()+QCursor .pos ()
        cursor_pos =QCursor .pos ()
        over_button =None
        for category ,btn in self .menu_buttons .items ():
            is_hovered =self ._is_point_in_widget (cursor_pos ,btn )
            btn .setProperty ("hovered",is_hovered )
            btn .style ().unpolish (btn )
            btn .style ().polish (btn )
            if is_hovered :
                over_button =category
        over_popup =self ._is_point_in_widget (cursor_pos ,self )
        over_submenu =self ._current_menu and self ._is_point_in_widget (cursor_pos ,self ._current_menu )
        if over_button and over_button !=self ._current_category :
            self ._show_submenu (over_button ,self .menu_buttons [over_button ])
        elif not over_button and not over_popup and not over_submenu :
            self ._close_current_menu ()
    def _close_current_menu (self ):
        if self ._current_menu :
            self ._current_menu .hide ()
            self ._current_menu =None 
        old_category =self ._current_category 
        self ._current_category =None 
        if old_category :
            self ._update_button_highlight (old_category ,False )
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
        btn =HoverMenuButton (key ,icon_key ,label ,self .container )
        return btn
    def set_menu_actions (self ,actions_dict ):
        self ._menu_actions =actions_dict 
    def _show_submenu (self ,category ,button ):
        self ._close_current_menu ()
        if category not in self ._menu_actions :
            return 
        actions =self ._menu_actions .get (category ,[])
        if not actions :
            return 
        self ._clear_all_highlights ()
        menu =QMenu (self )
        menu .setWindowFlags (Qt .Popup |Qt .FramelessWindowHint )
        menu .setAttribute (Qt .WA_TranslucentBackground )
        for item in actions :
            if len (item )>=3 and item [2 ]=='separator':
                menu .addSeparator ()
            text ,callback =item [0 ],item [1 ]
            action =menu .addAction (text )
            action .triggered .connect (lambda checked ,cb =callback :self ._on_menu_action (cb ))
        btn_pos =button .mapToGlobal (QPoint (button .width (),0 ))
        self ._current_menu =menu 
        self ._current_category =category 
        self ._update_button_highlight (category ,True )
        menu .aboutToHide .connect (self ._on_menu_hidden )
        menu .show ()
        menu .move (btn_pos )
        menu .raise_ ()
    def _clear_all_highlights (self ):
        for category ,btn in self .menu_buttons .items ():
            btn .setProperty ("active",False )
            btn .setProperty ("hovered",False )
            btn .style ().unpolish (btn )
            btn .style ().polish (btn )
    def _update_button_highlight (self ,category ,active ):
        if category in self .menu_buttons :
            btn =self .menu_buttons [category ]
            btn .setProperty ("active",active )
            btn .style ().unpolish (btn )
            btn .style ().polish (btn )
    def _on_menu_action (self ,callback ):
        self .close ()
        callback ()
    def _on_menu_hidden (self ):
        self ._current_menu =None 
    def hideEvent (self ,event ):
        self ._cursor_timer .stop ()
        self ._close_current_menu ()
        self ._clear_all_highlights ()
        super ().hideEvent (event )
    def refresh_labels (self ):
        labels ={
        'file':t ('deletion.menu.file')if t else 'File',
        'functions':t ('deletion.menu.delete')if t else 'Functions',
        'maps':t ('deletion.menu.view')if t else 'Maps',
        'exclusions':t ('deletion.menu.exclusions')if t else 'Exclusions',
        'languages':t ('lang.label')if t else 'Languages',
        }
        for category ,btn in self .menu_buttons .items ():
            if category in labels :
                try :
                    icon =nf .icons .get ({
                    'file':'nf-md-file',
                    'functions':'nf-md-function',
                    'maps':'nf-md-map',
                    'exclusions':'nf-md-playlist_remove',
                    'languages':'nf-md-translate'
                    }.get (category ,''),'')
                except :
                    icon =''
                chevron ='\u25B6'
                btn .setText (f"  {icon }  {labels [category ]}  {chevron }")
    def show_at (self ,global_pos ):
        self .adjustSize ()
        self .move (global_pos )
        self .show ()
        self .raise_ ()
        self ._cursor_timer .start (10 )
