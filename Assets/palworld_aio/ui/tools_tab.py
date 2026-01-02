import os 
import sys 
import json 
import traceback 
from PySide6 .QtWidgets import (
QWidget ,QVBoxLayout ,QHBoxLayout ,QLabel ,QPushButton ,
QFrame ,QScrollArea ,QMessageBox ,QSizePolicy ,QSpacerItem ,QGridLayout ,QApplication ,QDialog
)
from PySide6 .QtCore import Qt ,QSize ,Signal ,QPropertyAnimation ,QEasingCurve
from PySide6 .QtGui import QPixmap ,QIcon ,QFont ,QCursor 
from i18n import t 
try :
    from palworld_aio import constants 
except ImportError :
    from ..import constants 
def get_assets_path ():
    """Get the Assets path, compatible with both frozen and development modes."""
    env =os .environ .get ("ASSETS_PATH")
    if env :
        return os .path .abspath (env )
    if getattr (sys ,'frozen',False ):
        exe_dir =os .path .dirname (sys .executable )
        assets =os .path .join (exe_dir ,"Assets")
        if os .path .isdir (assets ):
            return assets
    try :
        base =os .path .dirname (os .path .dirname (os .path .dirname (os .path .abspath (__file__ ))))
    except NameError :
        base =os .path .dirname (os .path .abspath (sys .argv [0 ]))
    if os .path .isdir (base ):
        return base
    return os .path .abspath (base )
def load_tool_icons ():
    """Load tool icon mappings from toolicon.json in data/configs."""
    icon_file =os .path .join (get_assets_path (),"data","configs","toolicon.json")
    if not os .path .exists (icon_file ):
        return {}
    try :
        with open (icon_file ,'r',encoding ='utf-8')as f :
            data =json .load (f )
        return data if isinstance (data ,dict )else {}
    except Exception :
        return {}
CONVERTING_TOOL_KEYS =[
"tool.convert.saves",
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
def center_on_parent (dialog ):
    """Center a dialog on its parent window."""
    from PySide6 .QtWidgets import QApplication
    from PySide6 .QtCore import QPoint

    parent =dialog .parent ()
    if parent is None :
        parent =QApplication .activeWindow ()

    dialog .adjustSize ()
    dialog_size =dialog .size ()

    if parent :
        # Get parent's geometry in screen coordinates
        parent_geo =parent .frameGeometry ()
        x =parent_geo .x ()+(parent_geo .width ()-dialog_size .width ())//2
        y =parent_geo .y ()+(parent_geo .height ()-dialog_size .height ())//2
    else :
        # Fallback to screen center
        screen =QApplication .primaryScreen ()
        screen_geo =screen .availableGeometry ()
        x =screen_geo .x ()+(screen_geo .width ()-dialog_size .width ())//2
        y =screen_geo .y ()+(screen_geo .height ()-dialog_size .height ())//2

    # Clamp to screen boundaries
    screen =QApplication .screenAt (QPoint (x ,y ))
    if screen is None :
        screen =QApplication .primaryScreen ()
    screen_geo =screen .availableGeometry ()

    x =max (screen_geo .x (),min (x ,screen_geo .x ()+screen_geo .width ()-dialog_size .width ()))
    y =max (screen_geo .y (),min (y ,screen_geo .y ()+screen_geo .height ()-dialog_size .height ()))

    dialog .move (x ,y )
class ConversionOptionsDialog (QDialog ):
    """Dialog for selecting conversion options."""
    def __init__ (self ,parent =None ):
        super ().__init__ (parent )
        self .selected_option =None
        self .setWindowTitle (t ("tool.convert.saves")if t else "Convert Save Files")
        self .setModal (True )
        self .setFixedWidth (380 )
        self ._setup_ui ()
    def _setup_ui (self ):
        layout =QVBoxLayout (self )
        layout .setContentsMargins (16 ,16 ,16 ,16 )
        layout .setSpacing (8 )
        # Title
        title_label =QLabel (t ("tool.convert.saves")if t else "Convert Save Files")
        title_label .setObjectName ("dialogTitle")
        title_label .setAlignment (Qt .AlignCenter )
        layout .addWidget (title_label )
        # Separator
        separator =QFrame ()
        separator .setFrameShape (QFrame .HLine )
        separator .setObjectName ("dialogSeparator")
        layout .addWidget (separator )
        layout .addSpacing (4 )
        # Options in a more compact layout
        options =[
            ("tool.convert.level.to_json",0 ),
            ("tool.convert.level.to_sav",1 ),
            ("tool.convert.players.to_json",2 ),
            ("tool.convert.players.to_sav",3 ),
        ]
        for key ,index in options :
            btn =QPushButton (t (key )if t else key )
            btn .setObjectName ("dialogOption")
            btn .setFixedHeight (36 )
            btn .setCursor (QCursor (Qt .PointingHandCursor ))
            btn .clicked .connect (lambda checked ,idx =index :self ._on_option_selected (idx ))
            layout .addWidget (btn )
        layout .addSpacing (8 )
        # Cancel button
        cancel_btn =QPushButton (t ("Cancel")if t else "Cancel")
        cancel_btn .setObjectName ("dialogCancel")
        cancel_btn .setFixedHeight (32 )
        cancel_btn .setCursor (QCursor (Qt .PointingHandCursor ))
        cancel_btn .clicked .connect (self .reject )
        layout .addWidget (cancel_btn )
    def _on_option_selected (self ,index ):
        self .selected_option =index
        self .accept ()
class ToolButton (QWidget ):
    clicked =Signal ()
    def __init__ (self ,label_text ,tooltip_text ,icon_path =None ,parent =None ):
        super ().__init__ (parent )
        self .setProperty ("class","toolRow")
        self .setCursor (QCursor (Qt .PointingHandCursor ))
        self .setMouseTracking (True )
        self .is_hovered =False
        self .hover_animation =None
        layout =QHBoxLayout (self )
        layout .setContentsMargins (8 ,6 ,8 ,6 )
        layout .setSpacing (12 )
        self .icon_label =QLabel ()
        self .icon_label .setFixedSize (48 ,48 )
        if icon_path and os .path .exists (icon_path ):
            pix =QPixmap (icon_path )
            # Use FastTransformation for ICO files to preserve crisp pixels
            if pix .width () >48 or pix .height () >48 :
                pix =pix .scaled (48 ,48 ,Qt .KeepAspectRatio ,Qt .FastTransformation )
            self .icon_label .setPixmap (pix )
        else :
            default_icon =os .path .join (get_assets_path (),'resources','pal.ico')
            if os .path .exists (default_icon ):
                pix =QPixmap (default_icon )
                # Use FastTransformation for ICO files to preserve crisp pixels
                if pix .width () >48 or pix .height () >48 :
                    pix =pix .scaled (48 ,48 ,Qt .KeepAspectRatio ,Qt .FastTransformation )
                self .icon_label .setPixmap (pix )
        layout .addWidget (self .icon_label )
        self .text_label =QLabel (label_text )
        self .text_label .setToolTip (tooltip_text )
        self .text_label .setFont (QFont ("Segoe UI",11 ))
        layout .addWidget (self .text_label ,1 )
    def enterEvent (self ,event ):
        self .is_hovered =True
        self ._animate_hover (True )
        super ().enterEvent (event )
    def leaveEvent (self ,event ):
        self .is_hovered =False
        self ._animate_hover (False )
        super ().leaveEvent (event )
    def _animate_hover (self ,hovering ):
        """Animate hover effects with smooth transitions."""
        # Animate background color
        if not hasattr (self ,'_bg_animation'):
            self ._bg_animation =QPropertyAnimation (self ,b"bg_opacity")
            self ._bg_animation .setDuration (200 )
            self ._bg_animation .setEasingCurve (QEasingCurve .InOutQuad )

        target_opacity =0.15 if hovering else 0.0
        self ._bg_animation .setStartValue (self ._current_bg_opacity if hasattr (self ,'_current_bg_opacity')else 0.0 )
        self ._bg_animation .setEndValue (target_opacity )
        self ._bg_animation .start ()

        # Animate text color
        if not hasattr (self ,'_text_animation'):
            self ._text_animation =QPropertyAnimation (self ,b"text_opacity")
            self ._text_animation .setDuration (200 )
            self ._text_animation .setEasingCurve (QEasingCurve .InOutQuad )

        target_text_opacity =1.0 if hovering else 0.8
        self ._text_animation .setStartValue (self ._current_text_opacity if hasattr (self ,'_current_text_opacity')else 0.8 )
        self ._text_animation .setEndValue (target_text_opacity )
        self ._text_animation .start ()

        self ._current_bg_opacity =target_opacity
        self ._current_text_opacity =target_text_opacity
        self .update ()
    def get_bg_opacity (self ):
        return self ._current_bg_opacity if hasattr (self ,'_current_bg_opacity')else 0.0
    def set_bg_opacity (self ,opacity ):
        self ._current_bg_opacity =opacity
        self .update ()
    def get_text_opacity (self ):
        return self ._current_text_opacity if hasattr (self ,'_current_text_opacity')else 0.8
    def set_text_opacity (self ,opacity ):
        self ._current_text_opacity =opacity
        self .update ()
    bg_opacity =property (get_bg_opacity ,set_bg_opacity )
    text_opacity =property (get_text_opacity ,set_text_opacity )
    def paintEvent (self ,event ):
        """Custom paint event to handle animated colors."""
        from PySide6 .QtGui import QPainter ,QColor ,QPen ,QPainterPath
        from PySide6 .QtCore import QRectF
        painter =QPainter (self )
        painter .setRenderHint (QPainter .Antialiasing )

        # Draw background with animated opacity
        bg_opacity =self ._current_bg_opacity if hasattr (self ,'_current_bg_opacity')else 0.0
        if bg_opacity >0 :
            bg_color =QColor (125 ,211 ,252 ,int (bg_opacity *255 ))
            painter .fillRect (self .rect (),bg_color )

        # Draw 2px stroke around icon
        icon_rect =self .icon_label .geometry ()
        stroke_color =QColor (125 ,211 ,252 ,255 )# #7DD3FC
        stroke_pen =QPen (stroke_color )
        stroke_pen .setWidth (2 )

        path =QPainterPath ()
        path .addRoundedRect (QRectF (icon_rect ),6 ,6 )
        painter .strokePath (path ,stroke_pen )

        # Call parent paint event for other elements
        super ().paintEvent (event )
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
        main_layout .setContentsMargins (30 ,30 ,30 ,30 )
        main_layout .setSpacing (30 )
        scroll =QScrollArea ()
        scroll .setWidgetResizable (True )
        scroll .setFrameShape (QFrame .NoFrame )
        scroll .setObjectName ("toolsScrollArea")
        content =QWidget ()
        content_layout =QHBoxLayout (content )
        content_layout .setSpacing (25 )
        content_layout .setContentsMargins (15 ,15 ,15 ,15 )
        left_frame =QFrame ()
        left_frame .setObjectName ("glass")
        left_layout =QVBoxLayout (left_frame )
        left_layout .setContentsMargins (20 ,20 ,20 ,20 )
        left_layout .setSpacing (12 )
        for idx ,key in enumerate (CONVERTING_TOOL_KEYS ):
            icon_path =self ._get_tool_icon_path (key )
            btn =ToolButton (t (key )if t else key ,t (key )if t else key ,icon_path )
            btn .clicked .connect (lambda i =idx :self ._run_converting_tool (i ))
            left_layout .addWidget (btn )
        left_layout .addStretch (1 )
        right_frame =QFrame ()
        right_frame .setObjectName ("glass")
        right_layout =QVBoxLayout (right_frame )
        right_layout .setContentsMargins (20 ,20 ,20 ,20 )
        right_layout .setSpacing (12 )
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
    def _get_tool_icon_path (self ,tool_key ):
        """Get icon path for a tool key, supporting both .ico and .png formats."""
        if tool_key in self .tool_icons :
            icon_name =self .tool_icons [tool_key ]
            icon_dir =os .path .join (get_assets_path (),"data","icon")
            for ext in ['.ico','.png']:
                icon_path =os .path .join (icon_dir ,f"{icon_name }{ext }")
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
                # Show conversion options dialog
                options_dialog =ConversionOptionsDialog (self )
                self ._animate_dialog_slide_in (options_dialog )
                if options_dialog .exec () ==QDialog .Accepted and options_dialog .selected_option is not None :
                    # Run the selected conversion
                    if options_dialog .selected_option ==0 :
                        self ._import_and_call ("convert_level_location_finder","convert_level_location_finder","json")
                    elif options_dialog .selected_option ==1 :
                        self ._import_and_call ("convert_level_location_finder","convert_level_location_finder","sav")
                    elif options_dialog .selected_option ==2 :
                        self ._import_and_call ("convert_players_location_finder","convert_players_location_finder","json")
                    elif options_dialog .selected_option ==3 :
                        self ._import_and_call ("convert_players_location_finder","convert_players_location_finder","sav")
            elif index ==1 :
                dialog =self ._import_and_call ("game_pass_save_fix","game_pass_save_fix")
            elif index ==2 :
                dialog =self ._import_and_call ("convertids","convert_steam_id")
            if dialog is not None :
                self ._animate_dialog_slide_in (dialog )
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
                self ._animate_dialog_slide_in (dialog )
                if not hasattr (self ,'_active_dialogs'):
                    self ._active_dialogs =[]
                self ._active_dialogs .append (dialog )
        except Exception as e :
            print (f"Error running management tool {index }: {e }")
    def _animate_dialog_slide_in (self ,dialog ):
        """Animate dialog fade-in with smooth opacity transition, centered on parent."""
        if dialog is None :
            return

        # Ensure dialog size is calculated properly
        dialog .adjustSize ()

        # Center on parent window
        center_on_parent (dialog )

        # Set initial opacity to 0 (invisible)
        dialog .setWindowOpacity (0.0 )
        dialog .show ()

        # Create fade-in animation
        self .fade_animation =QPropertyAnimation (dialog ,b"windowOpacity")
        self .fade_animation .setDuration (400 )
        self .fade_animation .setStartValue (0.0 )
        self .fade_animation .setEndValue (1.0 )
        self .fade_animation .setEasingCurve (QEasingCurve .OutCubic )
        self .fade_animation .start ()
    def refresh (self ):
        pass
