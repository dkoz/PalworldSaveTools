from import_libs import *
import nerdfont as nf
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox, QFrame, QMessageBox, QFileDialog, QStyleFactory, QApplication
from PySide6.QtCore import Qt, Signal, QObject, QTimer, QMetaObject, Q_ARG
from PySide6.QtGui import QIcon, QFont
saves = []
save_extractor_done = threading.Event()
save_converter_done = threading.Event()
if getattr(sys, 'frozen', False):
    base_dir = os.path.dirname(sys.executable)
else:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
root_dir = base_dir
class GamePassSaveFixWidget(QWidget):
    update_combobox_signal = Signal(list)
    extraction_complete_signal = Signal()
    message_signal = Signal(str, str, str)
    def __init__(self):
        super().__init__()
        self.save_frame = None
        self.update_combobox_signal.connect(self.update_combobox_slot)
        self.extraction_complete_signal.connect(self.start_conversion)
        self.message_signal.connect(self.handle_message)
        self.setup_ui()
    def setup_ui(self):
        self.setWindowTitle(t("xgp.title.converter"))
        self.setFixedSize(600, 200)
        self.setStyleSheet("""
QWidget {
    background: qlineargradient(spread:pad, x1:0.0, y1:0.0, x2:1.0, y2:1.0,
                stop:0 #07080a, stop:0.5 #08101a, stop:1 #05060a);
    color: #dfeefc;
    font-family: "Segoe UI", Roboto, Arial;
}
QFrame#glass {
    background: rgba(18,20,24,0.65);
    border-radius: 10px;
    border: 1px solid rgba(255,255,255,0.04);
    padding: 10px;
}
QPushButton {
    background-color: #555555;
    color: white;
    padding: 6px;
    border-radius: 4px;
}
QPushButton:hover {
    background-color: #666666;
}
QLineEdit {
    background-color: rgba(255,255,255,0.1);
    color: white;
    border: 1px solid rgba(255,255,255,0.2);
    border-radius: 4px;
    padding: 4px;
}
QLabel {
    color: #dfeefc;
    background-color: rgba(18,20,24,0);
}
QComboBox {
    background-color: #444444;
    color: white;
    border: 1px solid #555555;
    padding: 4px;
    border-radius: 4px;
}
QComboBox::drop-down {
    border: none;
}
""")
        try:
            if ICON_PATH and os.path.exists(ICON_PATH):
                self.setWindowIcon(QIcon(ICON_PATH))
        except Exception as e:
            print(f"Could not set icon: {e}")
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(12)
        glass_frame = QFrame()
        glass_frame.setObjectName("glass")
        glass_layout = QVBoxLayout(glass_frame)
        glass_layout.setContentsMargins(12, 12, 12, 12)
        glass_layout.addStretch(1)
        desc_label = QLabel(t("xgp.ui.description") if hasattr(t, '__call__') else "Select an option to convert your Palworld saves:")
        desc_label.setFont(QFont("Segoe UI", 13))
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setWordWrap(True)
        glass_layout.addWidget(desc_label)
        glass_layout.addStretch(1)
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        xgp_button = QPushButton(f"{nf.icons['nf-fa-xbox']}  {t('xgp.ui.btn_xgp_folder')}")
        xgp_button.setFont(QFont("Segoe UI", 13))
        xgp_button.setFixedWidth(250)
        buttons_layout.addWidget(xgp_button)
        steam_button = QPushButton(f"{nf.icons['nf-fa-steam']}  {t('xgp.ui.btn_steam_folder')}")
        steam_button.setFont(QFont("Segoe UI", 13))
        steam_button.setFixedWidth(250)
        buttons_layout.addWidget(steam_button)
        buttons_layout.addStretch()
        glass_layout.addLayout(buttons_layout)
        xgp_button.clicked.connect(self.get_save_game_pass)
        steam_button.clicked.connect(self.get_save_steam)
        self.save_frame = QFrame()
        self.save_frame.setStyleSheet("QFrame { background-color: transparent; }")
        save_layout = QVBoxLayout(self.save_frame)
        save_layout.setContentsMargins(0, 0, 0, 0)
        save_layout.setSpacing(12)
        glass_layout.addWidget(self.save_frame, 1)
        main_layout.addWidget(glass_frame)
        center_window(self)
    def handle_message(self, message_type: str, title: str, text: str):
        if message_type == "info":
            QMessageBox.information(self, title, text)
        elif message_type == "critical":
            QMessageBox.critical(self, title, text)
    def start_conversion(self):
        print("Extraction complete. Converting save files...")
        threading.Thread(target=self.convert_save_files, daemon=True).start()
    def update_combobox_slot(self, saveList):
        self.update_combobox(saveList)
    def closeEvent(self, event):
        shutil.rmtree(os.path.join(root_dir, "saves"), ignore_errors=True)
        event.accept()
    def get_save_game_pass(self):
        if os.path.exists("./saves"): shutil.rmtree("./saves")
        default_source=os.path.expandvars(r"%LOCALAPPDATA%\Packages\PocketpairInc.Palworld_ad4psfrxyesvt\SystemAppData\wgs")
        source_folder = QFileDialog.getExistingDirectory(self, "Select your XGP Palworld save folder", default_source)
        if not source_folder:
            print("No folder selected.")
            return
        global xgp_source_folder
        xgp_source_folder=source_folder
        print(f"Using XGP folder: {xgp_source_folder}")
        save_extractor_done.clear()
        threading.Thread(target=self.run_save_extractor, daemon=True).start()
    def get_save_steam(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Steam Save Folder to Transfer")
        if not folder: return
        threading.Thread(target=self.transfer_steam_to_gamepass, args=(folder,), daemon=True).start()
    @staticmethod
    def list_folders_in_directory(directory):
        try:
            if not os.path.exists(directory): os.makedirs(directory)
            return [item for item in os.listdir(directory) if os.path.isdir(os.path.join(directory, item))]
        except: return []
    @staticmethod
    def is_folder_empty(directory):
        try:
            if not os.path.exists(directory): os.makedirs(directory)
            return len(os.listdir(directory)) == 0
        except: return False
    @staticmethod
    def find_zip_files(directory):
        if not os.path.exists(directory): return []
        return [f for f in os.listdir(directory) if f.endswith(".zip") and f.startswith("palworld_") and GamePassSaveFixWidget.is_valid_zip(os.path.join(directory, f))]
    @staticmethod
    def is_valid_zip(zip_file_path):
        try:
            with zipfile.ZipFile(zip_file_path, "r") as zip_ref: zip_ref.testzip()
            return True
        except: return False
    @staticmethod
    def unzip_file(zip_file_path, extract_to_folder):
        os.makedirs(extract_to_folder, exist_ok=True)
        print(f"DEBUG: Attempting extraction of {zip_file_path}...")
        try:
            with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
                zip_ref.extractall(extract_to_folder)
            print("DEBUG: Extraction completed successfully.")
            return True
        except Exception as e:
            print(f"DEBUG: Error extracting zip file {zip_file_path}: {e}")
            return False
    def process_zip_files(self):
        if self.is_folder_empty("./saves"):
            zip_files = self.find_zip_files("./")
            if zip_files:
                print(f"Unzipping {zip_files[0]}...")
                if self.unzip_file(zip_files[0], "./saves"):
                    save_extractor_done.set()
                    self.extraction_complete_signal.emit()
                else:
                    self.message_signal.emit("critical", t("Error"), t("xgp.err.unzip_failed"))
                return
            print("No save files found on XGP. Reinstall Palworld on GamePass and try again.")
            self.close()
        else:
            save_extractor_done.set()
            self.extraction_complete_signal.emit()
    def process_zip_file(self, file_path: str):
        saves_path = os.path.join(root_dir, "saves")
        if self.unzip_file(file_path, saves_path):
            xgp_original_saves_path = os.path.join(root_dir, "XGP_original_saves")
            os.makedirs(xgp_original_saves_path, exist_ok=True)
            shutil.copy2(file_path, os.path.join(xgp_original_saves_path, os.path.basename(file_path)))
            save_extractor_done.set()
    def convert_save_files(self):
        saveFolders = self.list_folders_in_directory("./saves")
        if not saveFolders:
            print("No save files found")
            return
        saveList = []
        for saveName in saveFolders:
            name = self.convert_sav_JSON(saveName)
            if name: saveList.append(name)
        self.update_combobox_signal.emit(saveList)
        print("Choose a save to convert:")
    def run_save_extractor(self):
        try:
            import xgp_save_extract as extractor
            zip_file_path = extractor.main()
            print("Extractor finished successfully")
            self.process_zip_files()
        except Exception as e:
            print(f"Extractor error: {e}")
    def convert_sav_JSON(self, saveName):
        save_path = os.path.join(root_dir, "saves", saveName, "Level", "01.sav")
        if not os.path.exists(save_path): return None
        try:
            from palworld_save_tools.commands import convert
            old_argv = sys.argv
            try:
                sys.argv = ["convert", save_path]
                convert.main()
            except Exception as e:
                print(f"Error converting save: {e}")
                return None
            finally: sys.argv = old_argv
        except ImportError:
            print(t("xgp.err.module_missing"))
            return None
        return saveName
    def convert_JSON_sav(self, saveName):
        json_path = os.path.join(root_dir, "saves", saveName, "Level", "01.sav.json")
        output_path = os.path.join(root_dir, "saves", saveName, "Level.sav")
        if not os.path.exists(json_path): return
        try:
            from palworld_save_tools.commands import convert
            old_argv = sys.argv
            try:
                sys.argv = ["convert", json_path, "--output", output_path]
                convert.main()
                os.remove(json_path)
                self.move_save_steam(saveName)
            except Exception as e: print(t("xgp.err.convert_json", err=e))
            finally: sys.argv = old_argv
        except ImportError:
            print("palworld_save_tools module not found. Please ensure it's installed.")
    @staticmethod
    def generate_random_name(length=32):
        return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))
    def move_save_steam(self, saveName):
        try:
            destination_folder = getattr(save_converter_done, "destination_folder", None)
            if not destination_folder:
                default_dest = os.path.expandvars(r"%localappdata%\Pal\Saved\SaveGames")
                initial_dir = default_dest if os.path.exists(default_dest) else root_dir
                destination_folder = QFileDialog.getExistingDirectory(self, "Select output folder", initial_dir)
                if not destination_folder: return
                save_converter_done.destination_folder = destination_folder
            source_folder = os.path.join(root_dir, "saves", saveName)
            if not os.path.exists(source_folder):
                raise FileNotFoundError(t("xgp.err.source_not_found", src=source_folder))
            def ignore_folders(_, names): return {n for n in names if n in {"Level", "Slot1", "Slot2", "Slot3"}}
            new_name = self.generate_random_name()
            xgp_converted_saves_path = os.path.join(root_dir, "XGP_converted_saves")
            os.makedirs(xgp_converted_saves_path, exist_ok=True)
            new_converted_target_folder = os.path.join(xgp_converted_saves_path, new_name)
            shutil.copytree(source_folder, new_converted_target_folder, dirs_exist_ok=True, ignore=ignore_folders)
            new_target_folder = os.path.join(destination_folder, new_name)
            shutil.copytree(source_folder, new_target_folder, dirs_exist_ok=True, ignore=ignore_folders)
            self.message_signal.emit("info", t("Success"), t("xgp.msg.convert_copied", dest=destination_folder))
        except Exception as e:
            print(t("xgp.err.copy_exception", err=e))
            traceback.print_exc()
            self.message_signal.emit("critical", t("Error"), t("xgp.err.copy_failed", err=e))
    def transfer_steam_to_gamepass(self, source_folder):
        try:
            import_path = os.path.join(base_dir, "palworld_xgp_import")
            sys.path.insert(0, import_path)
            from palworld_xgp_import import main as xgp_main
            old_argv = sys.argv
            try:
                sys.argv = ["main.py", source_folder]
                xgp_main.main()
                self.message_signal.emit("info", t("Success"), t("xgp.msg.steam_to_xgp_ok"))
            except Exception as e:
                print(t("xgp.err.conversion_exception", err=e))
                self.message_signal.emit("critical", t("Error"), t("xgp.err.conversion_failed", err=e))
            finally:
                sys.argv = old_argv
                if import_path in sys.path: sys.path.remove(import_path)
        except ImportError as e:
            print(t("xgp.err.import_exception", err=e))
            self.message_signal.emit("critical", t("Error"), t("xgp.err.import_failed", err=e))
    def update_combobox(self, saveList):
        global saves
        saves = saveList
        layout = self.save_frame.layout()
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        if saves:
            combo_layout = QHBoxLayout()
            combo_layout.addStretch()
            combobox = QComboBox()
            combobox.setFont(QFont("Segoe UI", 10))
            combobox.setMaximumWidth(400)
            combobox.addItems(saves)
            combobox.setCurrentText(t("xgp.ui.choose_save"))
            combo_layout.addWidget(combobox)
            combo_layout.addStretch()
            layout.addLayout(combo_layout)
            button_layout = QHBoxLayout()
            button_layout.addStretch()
            button = QPushButton(t("xgp.ui.convert"))
            button.setFont(QFont("Segoe UI", 10))
            button.setMaximumWidth(250)
            button.clicked.connect(lambda: self.convert_JSON_sav(combobox.currentText()))
            button_layout.addWidget(button)
            button_layout.addStretch()
            layout.addLayout(button_layout)
def center_window(win):
    screen = QApplication.primaryScreen().availableGeometry()
    size = win.sizeHint()
    if not size.isValid():
        win.adjustSize()
        size = win.size()
    win.move((screen.width() - size.width()) // 2, (screen.height() - size.height()) // 2)
def game_pass_save_fix():
    default_source = os.path.join(root_dir, "saves")
    if os.path.exists(default_source): shutil.rmtree(default_source)
    return GamePassSaveFixWidget()
if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    widget = game_pass_save_fix()
    widget.show()
    sys.exit(app.exec())