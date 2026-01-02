from PySide6 .QtWidgets import QWidget ,QVBoxLayout ,QLabel ,QFrame ,QSizePolicy 
from PySide6 .QtCore import Qt 
from PySide6 .QtGui import QFont 
from i18n import t 
try :
    from palworld_aio import constants 
    from palworld_aio .widgets import StatsPanel 
except ImportError :
    from ..import constants 
    from ..widgets import StatsPanel 
class ResultsWidget (QWidget ):

    def __init__ (self ,parent =None ):
        super ().__init__ (parent )
        self .setObjectName ("resultsWidget")
        self ._setup_ui ()
    def _setup_ui (self ):
        self .setMinimumWidth (350 )
        self .setMaximumWidth (350 )
        self .setSizePolicy (QSizePolicy .Fixed ,QSizePolicy .Expanding )
        layout =QVBoxLayout (self )
        layout .setContentsMargins (16 ,16 ,16 ,16 )
        layout .setSpacing (16 )
        layout .setAlignment (Qt .AlignTop )
        title =QLabel (t ('deletion.results_panel')if t else 'Selection & Stats')
        title .setObjectName ("sectionHeader")
        title .setFont (QFont (constants .FONT_FAMILY ,14 ,QFont .Bold ))
        layout .addWidget (title )
        separator =self ._create_gradient_separator ()
        layout .addWidget (separator )
        selection_frame =QFrame ()
        selection_frame .setObjectName ("glassPanel")
        selection_layout =QVBoxLayout (selection_frame )
        selection_layout .setSpacing (8 )
        player_card =self ._create_value_card (
        t ('deletion.selected_player_label')if t else 'Selected Player:'
        )
        self .player_value =player_card ['value_label']
        selection_layout .addWidget (player_card ['container'])
        guild_card =self ._create_value_card (
        t ('deletion.selected_guild_label')if t else 'Selected Guild:'
        )
        self .guild_value =guild_card ['value_label']
        selection_layout .addWidget (guild_card ['container'])
        base_card =self ._create_value_card (
        t ('deletion.selected_base_label')if t else 'Selected Base:'
        )
        self .base_value =base_card ['value_label']
        selection_layout .addWidget (base_card ['container'])
        layout .addWidget (selection_frame )
        separator2 =self ._create_gradient_separator ()
        layout .addWidget (separator2 )
        stats_title =QLabel (t ('deletion.stats_panel')if t else 'Statistics')
        stats_title .setObjectName ("sectionHeader")
        stats_title .setFont (QFont (constants .FONT_FAMILY ,14 ,QFont .Bold ))
        layout .addWidget (stats_title )
        stats_frame =QFrame ()
        stats_frame .setObjectName ("glassPanel")
        stats_layout =QVBoxLayout (stats_frame )
        self .stats_panel =StatsPanel ()
        self .stats_panel .setObjectName ("statsGrid")
        stats_layout .addWidget (self .stats_panel )
        layout .addWidget (stats_frame )
    def _create_gradient_separator (self ):

        separator =QFrame ()
        separator .setObjectName ("gradientSeparator")
        separator .setFrameShape (QFrame .HLine )
        separator .setMaximumHeight (2 )
        return separator 
    def _create_value_card (self ,label_text ):

        container =QFrame ()
        container .setObjectName ("valueCard")
        card_layout =QVBoxLayout (container )
        card_layout .setContentsMargins (8 ,6 ,8 ,6 )
        card_layout .setSpacing (4 )
        label =QLabel (label_text )
        label .setFont (QFont (constants .FONT_FAMILY ,9 ,QFont .Bold ))
        label .setStyleSheet (f"color: {constants .MUTED };")
        card_layout .addWidget (label )
        value_label =QLabel ('N/A')
        value_label .setFont (QFont (constants .FONT_FAMILY ,constants .FONT_SIZE ))
        value_label .setStyleSheet (f"color: {constants .TEXT };")
        value_label .setWordWrap (True )
        card_layout .addWidget (value_label )
        return {'container':container ,'value_label':value_label }
    def set_player (self ,name ):

        if name :
            self .player_value .setText (str (name ))
        else :
            self .player_value .setText ('N/A')
    def set_guild (self ,name ):

        if name :
            self .guild_value .setText (str (name ))
        else :
            self .guild_value .setText ('N/A')
    def set_base (self ,base_id ):

        if base_id :
            self .base_value .setText (str (base_id ))
        else :
            self .base_value .setText ('N/A')
    def clear_selection (self ):

        self .player_value .setText ('N/A')
        self .guild_value .setText ('N/A')
        self .base_value .setText ('N/A')
    def update_stats (self ,stats ):

        if hasattr (self ,'stats_panel')and self .stats_panel :
            self .stats_panel .update_stats (stats )
    def refresh_stats_before (self ):

        from ..save_manager import save_manager 
        stats =save_manager .get_current_stats ()
        if hasattr (self ,'stats_panel')and self .stats_panel :
            self .stats_panel .refresh_stats_before (stats )
    def refresh_stats_after (self ):

        from ..save_manager import save_manager 
        stats =save_manager .get_current_stats ()
        if hasattr (self ,'stats_panel')and self .stats_panel :
            self .stats_panel .refresh_stats_after (stats )
