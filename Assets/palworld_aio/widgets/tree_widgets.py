from PySide6 .QtWidgets import QTreeWidget ,QTreeWidgetItem ,QHeaderView ,QMenu ,QAbstractItemView 
from PySide6 .QtCore import Qt ,Signal 
from PySide6 .QtGui import QAction 
try :
    from palworld_aio import constants 
except ImportError :
    from ..import constants 
class SortableTreeWidget (QTreeWidget ):
    context_menu_requested =Signal (object ,object )
    def __init__ (self ,columns ,column_widths =None ,parent =None ):
        super ().__init__ (parent )
        self .columns =columns 
        self .column_widths =column_widths or []
        self ._setup_ui ()
    def _setup_ui (self ):
        self .setHeaderLabels (self .columns )
        self .setAlternatingRowColors (True )
        self .setRootIsDecorated (False )
        self .setSelectionMode (QAbstractItemView .SingleSelection )
        self .setSortingEnabled (True )
        self .setContextMenuPolicy (Qt .CustomContextMenu )
        self .customContextMenuRequested .connect (self ._on_context_menu )
        self .setStyleSheet (f"""
            QTreeWidget {{
                background-color: {constants .GLASS };
                color: {constants .TEXT };
                border: 1px solid {constants .BORDER };
                border-radius: 4px;
            }}
            QTreeWidget::item {{
                padding: 4px;
            }}
            QTreeWidget::item:selected {{
                background-color: {constants .ACCENT };
            }}
            QTreeWidget::item:hover {{
                background-color: {constants .BUTTON_HOVER };
            }}
            QHeaderView::section {{
                background-color: #3a3a3a;
                color: {constants .EMPHASIS };
                padding: 6px;
                border: none;
                font-weight: bold;
            }}
        """)
        header =self .header ()
        for i ,width in enumerate (self .column_widths ):
            if i <len (self .columns ):
                self .setColumnWidth (i ,width )
        header .setStretchLastSection (True )
    def _on_context_menu (self ,pos ):
        item =self .itemAt (pos )
        if item :
            self .setCurrentItem (item )
            global_pos =self .viewport ().mapToGlobal (pos )
            self .context_menu_requested .emit (item ,global_pos )
    def add_item (self ,values ,data =None ):
        item =QTreeWidgetItem ([str (v )for v in values ])
        if data :
            item .setData (0 ,Qt .UserRole ,data )
        self .addTopLevelItem (item )
        return item 
    def get_selected_values (self ):
        items =self .selectedItems ()
        if items :
            item =items [0 ]
            return [item .text (i )for i in range (item .columnCount ())]
        return None 
    def get_selected_data (self ):
        items =self .selectedItems ()
        if items :
            return items [0 ].data (0 ,Qt .UserRole )
        return None 
