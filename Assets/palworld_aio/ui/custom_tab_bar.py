from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QSpacerItem, QSizePolicy
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont, QCursor

try:
    import nerdfont as nf
except:
    class nf:
        icons = {
            'nf-cod-triangle_left': '\ueb9b',
            'nf-cod-triangle_right': '\ueb9c'
        }

from i18n import t
from .custom_floating_tab import FloatingTabBar


class TabBarContainer(QWidget):
    """Container widget that holds the tab bar and a collapse button on the right."""

    sidebar_toggle_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        """Set up the UI with tab bar and collapse button."""
        # Set object name for styling (border-bottom)
        self.setObjectName("tabBarContainer")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 10, 0)  # Right margin to match header padding
        layout.setSpacing(8)

        # Create the tab bar
        self.tab_bar = FloatingTabBar()
        self.tab_bar.setObjectName("customTabBar")
        self.tab_bar.setExpanding(False)
        layout.addWidget(self.tab_bar)

        # Add spacer to push collapse button to the right
        layout.addItem(QSpacerItem(20, 10, QSizePolicy.Expanding, QSizePolicy.Minimum))

        # Create collapse button with icon and text
        self.collapse_btn = QPushButton()
        self.collapse_btn.setObjectName("sidebarChip")
        self.collapse_btn.setFlat(True)
        self.collapse_btn.setFont(QFont("Hack Nerd Font", 14))
        self.collapse_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.collapse_btn.clicked.connect(self.sidebar_toggle_clicked.emit)

        # Set initial state (expanded)
        self.set_sidebar_collapsed(False)

        layout.addWidget(self.collapse_btn)

    def set_sidebar_collapsed(self, collapsed):
        """Update the button icon and text based on sidebar state.

        Args:
            collapsed: True if sidebar is collapsed (hidden), False if expanded (visible)
        """
        if collapsed:
            # Sidebar is hidden, show "Open" action
            icon = nf.icons['nf-cod-triangle_left']
            text = t('sidebar.open') if t else 'Open'
            tooltip = t('sidebar.open') if t else 'Open'
        else:
            # Sidebar is visible, show "Close" action
            icon = nf.icons['nf-cod-triangle_right']
            text = t('sidebar.close') if t else 'Close'
            tooltip = t('sidebar.close') if t else 'Close'

        self.collapse_btn.setText(f"{icon} {text}")
        self.collapse_btn.setToolTip(tooltip)

    def refresh_labels(self):
        """Refresh button text after language change."""
        # Determine current state by checking the icon
        collapsed = self.collapse_btn.text().startswith(nf.icons['nf-cod-triangle_left'])
        self.set_sidebar_collapsed(collapsed)

    def set_theme(self, is_dark):
        """Update tab bar theme."""
        if hasattr(self.tab_bar, 'set_theme'):
            self.tab_bar.set_theme(is_dark)
