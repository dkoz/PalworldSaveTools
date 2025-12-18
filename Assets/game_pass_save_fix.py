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
    def find_valid_saves(self, base_path):
        valid=[]
        if not os.path.isdir(base_path):return valid
        for name in os.listdir(base_path):
            root=os.path.join(base_path,name)
            level=os.path.join(root,"Level")
            if not os.path.isdir(level):continue
            if os.path.isfile(os.path.join(level,"01.sav")):
                valid.append(root)
        return valid
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
        default=os.path.expandvars(r"%LOCALAPPDATA%\Packages\PocketpairInc.Palworld_ad4psfrxyesvt\SystemAppData\wgs")
        folder=QFileDialog.getExistingDirectory(self,"Select XGP Save Folder",default)
        if not folder:return
        self.xgp_source_folder=folder
        def is_xgp_container(path):
            for root,_,files in os.walk(path):
                for f in files:
                    if f.lower().startswith("container.") or f.lower().endswith((".dat",".bin")):
                        return True
            return False
        if is_xgp_container(folder):
            if os.path.exists("./saves"):shutil.rmtree("./saves")
            threading.Thread(target=self.run_save_extractor,daemon=True).start()
            return
        saves=self.find_valid_saves(folder)
        if not saves:
            self.message_signal.emit("critical",t("Error"),t("xgp.err.no_valid_saves"))
            return
        self.direct_saves_map={os.path.basename(s):s for s in saves}
        self.update_combobox_signal.emit(list(self.direct_saves_map.keys()))
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
            zip_path=extractor.main()
            if not zip_path or not os.path.isfile(zip_path):
                raise RuntimeError("Extractor did not return a valid zip")
            if os.path.exists("./saves"):shutil.rmtree("./saves")
            if not self.unzip_file(zip_path,"./saves"):
                self.message_signal.emit("critical",t("Error"),t("xgp.err.unzip_failed"))
                return
            saves=self.find_valid_saves("./saves")
            if not saves:
                self.message_signal.emit("critical",t("Error"),t("xgp.err.no_valid_saves"))
                return
            self.update_combobox_signal.emit([os.path.basename(s) for s in saves])
        except Exception as e:
            print(f"Extractor error: {e}")
            traceback.print_exc()
            self.message_signal.emit("critical",t("Error"),t("xgp.err.extract_failed",err=e))
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
        source_base=getattr(self,"direct_saves_map",{}).get(saveName,os.path.join(root_dir,"saves",saveName))
        json_path=os.path.join(source_base,"Level","01.sav.json")
        sav_path=os.path.join(source_base,"Level","01.sav")
        out_level=os.path.join(source_base,"Level.sav")
        if os.path.exists(sav_path) and not os.path.exists(json_path):
            from palworld_save_tools.commands import convert
            old=sys.argv
            try:
                sys.argv=["convert",sav_path]
                convert.main()
            finally:sys.argv=old
        if not os.path.exists(json_path):
            self.message_signal.emit("critical",t("Error"),t("xgp.err.no_valid_saves"))
            return
        from palworld_save_tools.commands import convert
        old=sys.argv
        try:
            sys.argv=["convert",json_path,"--output",out_level]
            convert.main()
        finally:sys.argv=old
        try:os.remove(json_path)
        except:pass
        self.move_save_steam(saveName)
    @staticmethod
    def generate_random_name(length=32):
        return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))
    def move_save_steam(self, saveName):
        try:
            steam_default=os.path.expandvars(r"%localappdata%\Pal\Saved\SaveGames")
            initial=steam_default if os.path.isdir(steam_default) else root_dir
            destination=QFileDialog.getExistingDirectory(self,"Select where to place converted save",initial)
            if not destination:return
            source_base=getattr(self,"direct_saves_map",{}).get(saveName,os.path.join(root_dir,"saves",saveName))
            if not os.path.isdir(source_base):
                raise FileNotFoundError(t("xgp.err.source_not_found",src=source_base))
            if not os.path.isfile(os.path.join(source_base,"Level.sav")):
                self.message_signal.emit("critical",t("Error"),t("xgp.err.convert_failed",err="Missing Level.sav in save root"))
                return
            def ignore(_,names):return{n for n in names if n in{"Level","Slot1","Slot2","Slot3"}}
            new_name=self.generate_random_name()
            xgp_out=os.path.join(root_dir,"XGP_converted_saves")
            os.makedirs(xgp_out,exist_ok=True)
            shutil.copytree(source_base,os.path.join(xgp_out,new_name),dirs_exist_ok=True,ignore=ignore)
            shutil.copytree(source_base,os.path.join(destination,new_name),dirs_exist_ok=True,ignore=ignore)
            self.message_signal.emit("info",t("Success"),t("xgp.msg.convert_copied",dest=destination))
        except Exception as e:
            print(t("xgp.err.copy_exception",err=e))
            traceback.print_exc()
            self.message_signal.emit("critical",t("Error"),t("xgp.err.copy_failed",err=e))
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