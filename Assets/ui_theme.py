import customtkinter as ctk
BG = "#0A0B0E"
GLASS = "#121418"
ACCENT = "#3B8ED0"
TEXT = "#E6EEF6"  
MUTED = "#A6B8C8" 
EMPHASIS = "#FFFFFF"
ALERT = "#FFD24D" 
SUCCESS = "#4CAF50"
ERROR = "#F44336" 
BORDER = "#1E2128"
BUTTON_FG = "#0078D7"
BUTTON_BG = "transparent"
BUTTON_HOVER = "#2A2D3A"
BUTTON_PRIMARY = ACCENT 
BUTTON_SECONDARY = GLASS
FONT = ("Segoe UI", 10)
FONT_BOLD = ("Segoe UI", 10, "bold")
FONT_LARGE = ("Segoe UI", 12)
FONT_SMALL = ("Segoe UI", 9)
SPACE_SMALL = 5
SPACE_MEDIUM = 10
SPACE_LARGE = 15
CTK_BUTTON_CORNER_RADIUS = 6
CTK_FRAME_CORNER_RADIUS = 8
TREE_ROW_HEIGHT = 22
def apply_theme():
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("dark-blue")