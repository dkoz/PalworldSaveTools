from import_libs import *
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QMessageBox,
    QLineEdit, QFileDialog, QApplication, QFrame, QGridLayout
)
from PySide6.QtGui import QIcon, QFont
from PySide6.QtCore import Qt, QTimer
def sav_to_json(filepath):
    with open(filepath,"rb") as f:
        data=f.read()
        raw_gvas,save_type=decompress_sav_to_gvas(data)
    gvas_file=GvasFile.read(raw_gvas,PALWORLD_TYPE_HINTS,SKP_PALWORLD_CUSTOM_PROPERTIES,allow_nan=True)
    return gvas_file.dump()
def json_to_sav(json_data,output_filepath):
    gvas_file=GvasFile.load(json_data)
    save_type=0x32 if ("Pal.PalworldSaveGame" in gvas_file.header.save_game_class_name or "Pal.PalLocalWorldSaveGame" in gvas_file.header.save_game_class_name) else 0x31
    sav_file=compress_gvas_to_sav(gvas_file.write(SKP_PALWORLD_CUSTOM_PROPERTIES),save_type)
    with open(output_filepath,"wb") as f:
        f.write(sav_file)
def center_window(win):
    screen = QApplication.primaryScreen().availableGeometry()
    size = win.sizeHint()
    if not size.isValid():
        win.adjustSize()
        size = win.size()
    win.move((screen.width() - size.width()) // 2, (screen.height() - size.height()) // 2)
class SlotNumUpdaterApp(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(t("tool.slot_injector"))
        self.setFixedSize(560, 280)
        self.setStyleSheet("""
QDialog {
    background: qlineargradient(spread:pad, x1:0.0, y1:0.0, x2:1.0, y2:1.0,
                stop:0 #07080a, stop:0.5 #08101a, stop:1 #05060a);
    color: #dfeefc;
    font-family: "Segoe UI", Roboto, Arial;
}
QFrame#glass {
    background: rgba(18,20,24,0.68);
    border-radius: 12px;
    border: 1px solid rgba(255,255,255,0.04);
    padding: 12px;
}
QLabel {
    color: #dfeefc;
    font-size: 12px;
}
QLineEdit {
    background-color: rgba(255,255,255,0.04);
    color: #dfeefc;
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 8px;
    padding: 6px;
}
QPushButton {
    background-color: #555555;
    color: white;
    padding: 8px 14px;
    border-radius: 8px;
    min-width: 100px;
}
QPushButton#ApplyButton {
    background-color: #007bff;
    border: 1px solid #0056b3;
    min-width: 140px;
}
QPushButton:hover { background-color: #666666; }
QPushButton:disabled {
    background-color: #333333;
    color: #888888;
    border: 1px solid #444444;
}
""")
        try:
            if ICON_PATH and os.path.exists(ICON_PATH):
                self.setWindowIcon(QIcon(ICON_PATH))
        except Exception:
            pass
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(12)
        glass = QFrame()
        glass.setObjectName("glass")
        glass_layout = QVBoxLayout(glass)
        glass_layout.setContentsMargins(12, 12, 12, 12)
        glass_layout.setSpacing(12)
        title = QLabel(t("tool.slot_injector"))
        title.setFont(QFont("Segoe UI", 13, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        glass_layout.addWidget(title)
        input_grid = QGridLayout()
        input_grid.setSpacing(10)
        self.browse_button = QPushButton(t("browse"))
        self.browse_button.setFixedWidth(110)
        self.browse_button.clicked.connect(self.browse_file)
        self.file_label = QLabel(t("slot.select_level_sav"))
        self.file_entry = QLineEdit()
        self.file_entry.setPlaceholderText(t("Path to Level.sav"))
        input_grid.addWidget(self.browse_button, 0, 0)
        input_grid.addWidget(self.file_label, 0, 1, alignment=Qt.AlignLeft)
        input_grid.addWidget(self.file_entry, 0, 2, 1, 2)
        self.pages_label = QLabel(t("slot.total_pages"))
        self.pages_entry = QLineEdit()
        self.pages_entry.setFixedWidth(90)
        self.pages_entry.setPlaceholderText("e.g. 32")
        input_grid.addWidget(self.pages_label, 1, 1, alignment=Qt.AlignLeft)
        input_grid.addWidget(self.pages_entry, 1, 2, alignment=Qt.AlignLeft)
        self.slots_label = QLabel(t("slot.total_slots"))
        self.slots_entry = QLineEdit()
        self.slots_entry.setFixedWidth(90)
        self.slots_entry.setPlaceholderText("e.g. 30")
        input_grid.addWidget(self.slots_label, 2, 1, alignment=Qt.AlignLeft)
        input_grid.addWidget(self.slots_entry, 2, 2, alignment=Qt.AlignLeft)
        input_grid.setColumnStretch(3, 1)
        glass_layout.addLayout(input_grid)
        glass_layout.addStretch(1)
        self.apply_button = QPushButton(t("slot.apply"))
        self.apply_button.setObjectName("ApplyButton")
        self.apply_button.clicked.connect(self.apply_slotnum_update)
        glass_layout.addWidget(self.apply_button, alignment=Qt.AlignCenter)
        main_layout.addWidget(glass)
        QTimer.singleShot(0, lambda: center_window(self))
    def browse_file(self):
        file, _ = QFileDialog.getOpenFileName(self, t("slot.select_level_sav_title"), "", "SAV Files (Level.sav)")
        if file:
            self.file_entry.setText(file)
            self.load_selected_save()
    def load_selected_save(self):
        fp = self.file_entry.text()
        if not fp.endswith("Level.sav"):
            QMessageBox.critical(self, t("error.title"), t("slot.invalid_file"))
            return
        try:
            self.level_json = sav_to_json(fp)
            QMessageBox.information(self, t("slot.loaded_title"), t("slot.loaded_msg"))
        except Exception:
            raise
    def apply_slotnum_update(self):
        filepath = self.file_entry.text()
        if not hasattr(self, "level_json"):
            QMessageBox.critical(self, t("error.title"), t("slot.load_first"))
            return
        try:
            pages = int(self.pages_entry.text())
            slots = int(self.slots_entry.text())
            if pages < 1 or slots < 1:
                raise ValueError
        except ValueError:
            QMessageBox.critical(self, t("error.title"), t("slot.invalid_numbers"))
            return
        new_value = pages * slots
        level_json = self.level_json
        container = level_json["properties"]["worldSaveData"]["value"].get("CharacterContainerSaveData", {}).get("value", [])
        if not isinstance(container, list):
            QMessageBox.critical(self, t("error.title"), t("slot.invalid_structure"))
            return
        PLAYER_SLOT_THRESHOLD = 960
        editable = [entry for entry in container if entry.get("value", {}).get("SlotNum", {}).get("value", 0) >= PLAYER_SLOT_THRESHOLD]
        total_players = len(editable)
        if total_players == 0:
            QMessageBox.information(self, t("info.title"), t("slot.no_entries"))
            return
        resp = QMessageBox.question(self, t("slot.confirm_title"), t("slot.confirm_msg", count=total_players, new=new_value),
                                   QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if resp != QMessageBox.Yes:
            return
        for entry in editable:
            entry["value"]["SlotNum"]["value"] = new_value
        backup_whole_directory(os.path.dirname(filepath), "Backups/Slot Injector")
        json_to_sav(level_json, filepath)
        QMessageBox.information(self, t("success.title"), t("slot.success_msg", count=total_players, new=new_value))
def slot_injector():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    window = SlotNumUpdaterApp()
    return window