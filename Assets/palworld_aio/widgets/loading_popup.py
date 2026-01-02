"""Loading popup widget with animated GIF for save loading operations."""
import os
import sys
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPixmap, QMovie


class LoadingPopup(QWidget):
    """Frameless popup window that displays an animated loading GIF."""

    def __init__(self, parent=None):
        super().__init__(parent, Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_DeleteOnClose, True)

        # Setup UI
        self._setup_ui()

        # Animation for fade in/out
        self.fade_animation = None
        self._is_visible = False

    def _setup_ui(self):
        """Setup the UI components."""
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Label for the GIF
        self.gif_label = QLabel(self)
        self.gif_label.setAlignment(Qt.AlignCenter)

        # Load the chillet-loading.gif
        gif_path = self._get_gif_path()

        if os.path.exists(gif_path):
            # Use QMovie for animated GIF
            self.movie = QMovie(gif_path)
            if self.movie.isValid():
                self.gif_label.setMovie(self.movie)
                self.movie.start()

                # Get the first frame to determine size
                self.movie.jumpToFrame(0)
                first_frame = self.movie.currentPixmap()
                if not first_frame.isNull():
                    # Set widget size based on GIF size (or scale it)
                    scaled_size = first_frame.size()
                    # You can scale if needed: scaled_size = first_frame.size() * 1.5
                    self.setFixedSize(scaled_size)
                else:
                    self.setFixedSize(300, 300)
            else:
                self._show_fallback()
        else:
            self._show_fallback()

        layout.addWidget(self.gif_label)

    def _get_gif_path(self):
        """Get the path to the chillet-loading.gif file."""
        # Determine base path
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            base_dir = os.path.dirname(sys.executable)
            assets_dir = os.path.join(base_dir, 'Assets')
        else:
            # Running as script
            current_file = os.path.abspath(__file__)
            # Go up from widgets -> palworld_aio -> Assets
            assets_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))

        gif_path = os.path.join(assets_dir, 'data', 'gui', 'chillet-loading.gif')
        return gif_path

    def _show_fallback(self):
        """Show fallback text if GIF cannot be loaded."""
        self.gif_label.setText("Loading...")
        self.gif_label.setStyleSheet("""
            QLabel {
                color: #7DD3FC;
                font-size: 24px;
                font-weight: bold;
                font-family: 'Segoe UI', Arial;
                background: rgba(18, 20, 24, 0.95);
                border-radius: 12px;
                padding: 40px;
            }
        """)
        self.setFixedSize(200, 120)

    def show_with_fade(self):
        """Show the popup with fade-in animation."""
        if self._is_visible:
            return

        # Center on screen
        self._center_on_screen()

        # Start with opacity 0
        self.setWindowOpacity(0.0)
        self.show()

        # Animate fade in
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(300)
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.fade_animation.start()

        self._is_visible = True

    def hide_with_fade(self, on_complete=None):
        """Hide the popup with fade-out animation."""
        if not self._is_visible:
            if on_complete:
                on_complete()
            return

        # Animate fade out
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(300)
        self.fade_animation.setStartValue(1.0)
        self.fade_animation.setEndValue(0.0)
        self.fade_animation.setEasingCurve(QEasingCurve.InOutQuad)

        def on_fade_complete():
            self.hide()
            self._is_visible = False
            if on_complete:
                on_complete()

        self.fade_animation.finished.connect(on_fade_complete)
        self.fade_animation.start()

    def _center_on_screen(self):
        """Center the widget on the screen."""
        from PySide6.QtWidgets import QApplication
        screen = QApplication.primaryScreen().availableGeometry()
        size = self.size()
        x = (screen.width() - size.width()) // 2
        y = (screen.height() - size.height()) // 2
        self.move(x, y)

    def closeEvent(self, event):
        """Handle close event - stop the movie if it's playing."""
        if hasattr(self, 'movie') and self.movie:
            self.movie.stop()
        super().closeEvent(event)
