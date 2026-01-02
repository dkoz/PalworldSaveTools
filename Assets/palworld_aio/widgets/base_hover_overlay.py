from PySide6 .QtWidgets import QWidget ,QVBoxLayout ,QLabel ,QFrame ,QGraphicsDropShadowEffect 
from PySide6 .QtCore import Qt ,QPoint ,QTimer 
from PySide6 .QtGui import QFont ,QColor 
from i18n import t 
try :
    from palworld_aio import constants 
except ImportError :
    from ..import constants 
class BaseHoverOverlay (QWidget ):

    def __init__ (self ,parent =None ):
        super ().__init__ (parent )
        self .setObjectName ("baseHoverOverlay")
        self .setWindowFlags (Qt .ToolTip |Qt .FramelessWindowHint )
        self .setAttribute (Qt .WA_TranslucentBackground )
        self .setAttribute (Qt .WA_ShowWithoutActivating )
        self ._setup_ui ()
        self ._hide_timer =QTimer (self )
        self ._hide_timer .setSingleShot (True )
        self ._hide_timer .timeout .connect (self ._do_hide )
    def _setup_ui (self ):

        self .container =QFrame (self )
        self .container .setObjectName ("hoverOverlayContainer")
        layout =QVBoxLayout (self )
        layout .setContentsMargins (0 ,0 ,0 ,0 )
        layout .addWidget (self .container )
        inner_layout =QVBoxLayout (self .container )
        inner_layout .setContentsMargins (12 ,10 ,12 ,10 )
        inner_layout .setSpacing (6 )
        self .guild_label =QLabel ()
        self .guild_label .setObjectName ("hoverGuildLabel")
        self .guild_label .setFont (QFont (constants .FONT_FAMILY ,11 ,QFont .Bold ))
        inner_layout .addWidget (self .guild_label )
        self .leader_label =QLabel ()
        self .leader_label .setObjectName ("hoverDetailLabel")
        self .leader_label .setFont (QFont (constants .FONT_FAMILY ,9 ))
        inner_layout .addWidget (self .leader_label )
        self .base_id_label =QLabel ()
        self .base_id_label .setObjectName ("hoverDetailLabel")
        self .base_id_label .setFont (QFont (constants .FONT_FAMILY ,9 ))
        inner_layout .addWidget (self .base_id_label )
        self .coords_label =QLabel ()
        self .coords_label .setObjectName ("hoverDetailLabel")
        self .coords_label .setFont (QFont (constants .FONT_FAMILY ,9 ))
        inner_layout .addWidget (self .coords_label )
        shadow =QGraphicsDropShadowEffect (self )
        shadow .setBlurRadius (15 )
        shadow .setOffset (2 ,2 )
        shadow .setColor (QColor (0 ,0 ,0 ,100 ))
        self .container .setGraphicsEffect (shadow )
        self .container .setStyleSheet ("""
            QFrame#hoverOverlayContainer {
                background: rgba(18, 20, 24, 0.95);
                border: 1px solid rgba(125, 211, 252, 0.3);
                border-radius: 8px;
            }
            QLabel#hoverGuildLabel {
                color: #7DD3FC;
            }
            QLabel#hoverDetailLabel {
                color: #a0aec0;
            }
        """)
    def show_for_base (self ,base_data :dict ,global_pos :QPoint ):

        self ._hide_timer .stop ()
        guild_name =base_data .get ('guild_name','Unknown')
        leader_name =base_data .get ('leader_name','Unknown')
        base_id =str (base_data .get ('base_id',''))
        coords =base_data .get ('coords',(0 ,0 ))
        self .guild_label .setText (f"{t ('map.hover.guild')if t else 'Guild'}: {guild_name }")
        self .leader_label .setText (f"{t ('map.hover.leader')if t else 'Leader'}: {leader_name }")
        self .base_id_label .setText (f"{t ('map.hover.base_id')if t else 'Base ID'}: {base_id [:16 ]}...")
        self .coords_label .setText (f"{t ('map.hover.coords')if t else 'Coords'}: X:{int (coords [0 ])}, Y:{int (coords [1 ])}")
        self .adjustSize ()
        offset_x =20 
        offset_y =-self .height ()//2 
        new_pos =QPoint (global_pos .x ()+offset_x ,global_pos .y ()+offset_y )
        self .move (new_pos )
        self .show ()
        self .raise_ ()
    def hide_overlay (self ):

        self ._hide_timer .start (50 )
    def _do_hide (self ):

        self .hide ()
    def cancel_hide (self ):

        self ._hide_timer .stop ()
