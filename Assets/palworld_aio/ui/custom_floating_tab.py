from PySide6.QtWidgets import QTabBar
from PySide6.QtCore import Qt, QSize, QRectF
from PySide6.QtGui import QPainter, QPainterPath, QColor, QFont, QPen, QBrush, QFontMetrics


class FloatingTabBar(QTabBar):
    """Custom tab bar with floating chip design and slanted top-right corners."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDrawBase(False)
        self.is_dark_mode = True
        self._hovered_tab = -1

    def set_theme(self, is_dark):
        """Update theme and repaint."""
        self.is_dark_mode = is_dark
        self.update()

    def tabSizeHint(self, index):
        """Add extra space for floating effect margins."""
        size = super().tabSizeHint(index)
        return QSize(size.width() + 20, size.height() + 12)

    def paintEvent(self, event):
        """Custom paint all tabs with floating chip design."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        for i in range(self.count()):
            self._draw_custom_tab(painter, i)

    def _draw_custom_tab(self, painter, index):
        """Draw individual tab with slanted top-right corner."""
        rect = self.tabRect(index)
        is_selected = (index == self.currentIndex())
        is_hovered = (index == self._hovered_tab)

        # Add margins for floating effect
        rect = rect.adjusted(4, 6, -4, -4)

        # Create path with slanted top-right corner
        path = self._create_tab_path(rect)

        # Get colors based on state and theme
        bg_color, border_color, text_color = self._get_colors(is_selected, is_hovered)

        # Draw shadow for floating effect (subtle glow)
        self._draw_shadow(painter, path)

        # Fill background
        painter.fillPath(path, QBrush(bg_color))

        # Draw border
        painter.setPen(QPen(border_color, 1))
        painter.drawPath(path)

        # Draw text
        painter.setPen(text_color)
        font = QFont("Segoe UI", 11, QFont.Bold if is_selected else QFont.DemiBold)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignCenter, self.tabText(index))

    def _create_tab_path(self, rect):
        """Create QPainterPath with slanted top-right corner."""
        path = QPainterPath()
        radius = 10
        slant = 15

        # Start top-left
        path.moveTo(rect.left() + radius, rect.top())

        # Top-left rounded corner
        path.arcTo(rect.left(), rect.top(), radius * 2, radius * 2, 90, 90)

        # Left edge
        path.lineTo(rect.left(), rect.bottom() - radius)

        # Bottom-left rounded corner
        path.arcTo(rect.left(), rect.bottom() - radius * 2, radius * 2, radius * 2, 180, 90)

        # Bottom edge
        path.lineTo(rect.right() - radius, rect.bottom())

        # Bottom-right rounded corner
        path.arcTo(rect.right() - radius * 2, rect.bottom() - radius * 2, radius * 2, radius * 2, 270, 90)

        # Right edge to slant start
        path.lineTo(rect.right(), rect.top() + slant)

        # SLANTED top-right corner
        path.lineTo(rect.right() - slant, rect.top())

        path.closeSubpath()
        return path

    def _draw_shadow(self, painter, path):
        """Draw subtle shadow/glow for floating effect."""
        shadow_color = QColor(125, 211, 252, 25) if self.is_dark_mode else QColor(37, 150, 190, 25)

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(shadow_color))

        # Draw shadow offset slightly down and right
        painter.save()
        painter.translate(0, 2)
        painter.fillPath(path, shadow_color)
        painter.restore()

    def _get_colors(self, is_selected, is_hovered):
        """Get colors based on tab state and theme."""
        if self.is_dark_mode:
            if is_selected:
                bg = QColor(125, 211, 252, 31)  # rgba(125,211,252,0.12)
                border = QColor(125, 211, 252, 76)  # rgba(125,211,252,0.3)
                text = QColor("#7DD3FC")
            elif is_hovered:
                bg = QColor(125, 211, 252, 13)  # rgba(125,211,252,0.05)
                border = QColor(125, 211, 252, 38)  # rgba(125,211,252,0.15)
                text = QColor("#E6EEF6")
            else:
                bg = QColor(30, 33, 40, 178)  # rgba(30,33,40,0.7)
                border = QColor(125, 211, 252, 26)  # rgba(125,211,252,0.1)
                text = QColor("#A6B8C8")
        else:  # Light mode
            if is_selected:
                bg = QColor(37, 150, 190, 38)  # rgba(37,150,190,0.15)
                border = QColor(37, 150, 190, 102)  # rgba(37,150,190,0.4)
                text = QColor("#1A365D")
            elif is_hovered:
                bg = QColor(37, 150, 190, 20)  # rgba(37,150,190,0.08)
                border = QColor(37, 150, 190, 51)  # rgba(37,150,190,0.2)
                text = QColor("#2C3E50")
            else:
                bg = QColor(200, 215, 235, 128)  # rgba(200,215,235,0.5)
                border = QColor(180, 200, 220, 76)  # rgba(180,200,220,0.3)
                text = QColor("#2C3E50")

        return bg, border, text

    def mouseMoveEvent(self, event):
        """Track hovered tab for hover effects."""
        old_hovered = self._hovered_tab
        self._hovered_tab = self.tabAt(event.pos())
        if old_hovered != self._hovered_tab:
            self.update()
        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        """Clear hover state when mouse leaves."""
        self._hovered_tab = -1
        self.update()
        super().leaveEvent(event)
