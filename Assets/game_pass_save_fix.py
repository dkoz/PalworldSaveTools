from import_libs import *
saves = []
save_extractor_done = threading.Event()
save_converter_done = threading.Event()
if getattr(sys, 'frozen', False):
    base_dir = os.path.dirname(sys.executable)
else:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
root_dir = base_dir
def get_save_game_pass():
    if os.path.exists("./saves"): shutil.rmtree("./saves")
    default_source=os.path.expandvars(r"%LOCALAPPDATA%\Packages\PocketpairInc.Palworld_ad4psfrxyesvt\SystemAppData\wgs")
    source_folder=filedialog.askdirectory(title="Select your XGP Palworld save folder",initialdir=default_source)
    if not source_folder:
        print("No folder selected.")
        return
    global xgp_source_folder
    xgp_source_folder=source_folder
    print(f"Using XGP folder: {xgp_source_folder}")
    save_extractor_done.clear()
    threading.Thread(target=run_save_extractor, daemon=True).start()
    threading.Thread(target=check_progress, daemon=True).start()
def get_save_steam():
    folder = filedialog.askdirectory(title="Select Steam Save Folder to Transfer")
    if not folder: return
    threading.Thread(target=transfer_steam_to_gamepass, args=(folder,), daemon=True).start()
def check_progress():
    if save_extractor_done.is_set():
        print("Extraction complete. Converting save files...")
        threading.Thread(target=convert_save_files, daemon=True).start()
    else:
        window.after(500, check_progress)
def check_for_zip_files():
    zip_files=find_zip_files("./")
    if not zip_files:
        print("No palworld_*.zip detected. Running extractor...")
        threading.Thread(target=run_save_extractor, daemon=True).start()
        return
    print("palworld_*.zip detected. Processing...")
    process_zip_files()
def process_zip_files():
    if is_folder_empty("./saves"):
        zip_files=find_zip_files("./")
        if zip_files:
            print(f"Unzipping {zip_files[0]}...")
            unzip_file(zip_files[0], "./saves")
            save_extractor_done.set()
            return
        print("No save files found on XGP. Reinstall Palworld on GamePass and try again.")
        window.quit()
    else:
        save_extractor_done.set()
def process_zip_file(file_path: str):
    saves_path = os.path.join(root_dir, "saves")
    unzip_file(file_path, saves_path)
    xgp_original_saves_path = os.path.join(root_dir, "XGP_original_saves")
    os.makedirs(xgp_original_saves_path, exist_ok=True)
    shutil.copy2(file_path, os.path.join(xgp_original_saves_path, os.path.basename(file_path)))
    save_extractor_done.set()
def convert_save_files():
    saveFolders=list_folders_in_directory("./saves")
    if not saveFolders:
        print("No save files found")
        return
    saveList=[]
    for saveName in saveFolders:
        name=convert_sav_JSON(saveName)
        if name: saveList.append(name)
    window.after(0, lambda: update_combobox(saveList))
    print("Choose a save to convert:")
def run_save_extractor():
    try:
        import xgp_save_extract as extractor
        zip_file_path = extractor.main()
        print("Extractor finished successfully")
        process_zip_files()
    except Exception as e:
        print(f"Extractor error: {e}")
def list_folders_in_directory(directory):
    try:
        if not os.path.exists(directory): os.makedirs(directory)
        return [item for item in os.listdir(directory) if os.path.isdir(os.path.join(directory, item))]
    except: return []
def is_folder_empty(directory):
    try:
        if not os.path.exists(directory): os.makedirs(directory)
        return len(os.listdir(directory)) == 0
    except: return False
def find_zip_files(directory):
    if not os.path.exists(directory): return []
    return [f for f in os.listdir(directory) if f.endswith(".zip") and f.startswith("palworld_") and is_valid_zip(os.path.join(directory, f))]
def is_valid_zip(zip_file_path):
    try:
        with zipfile.ZipFile(zip_file_path, "r") as zip_ref: zip_ref.testzip()
        return True
    except: return False
def unzip_file(zip_file_path, extract_to_folder):
    os.makedirs(extract_to_folder, exist_ok=True)
    with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
        zip_ref.extractall(extract_to_folder)
def convert_sav_JSON(saveName):
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
def convert_JSON_sav(saveName):
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
            move_save_steam(saveName)
        except Exception as e: print(t("xgp.err.convert_json", err=e))
        finally: sys.argv = old_argv
    except ImportError:
        print("palworld_save_tools module not found. Please ensure it's installed.")
def generate_random_name(length=32):
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))
def move_save_steam(saveName):
    try:
        destination_folder=getattr(save_converter_done,"destination_folder",None)
        if not destination_folder:
            default_dest=os.path.expandvars(r"%localappdata%\Pal\Saved\SaveGames")
            initial_dir=default_dest if os.path.exists(default_dest) else root_dir
            destination_folder=filedialog.askdirectory(title=t("xgp.dialog.select_output_folder"),initialdir=initial_dir)
            if not destination_folder:return
            save_converter_done.destination_folder=destination_folder
        source_folder=os.path.join(root_dir,"saves",saveName)
        if not os.path.exists(source_folder):
            raise FileNotFoundError(t("xgp.err.source_not_found",src=source_folder))
        def ignore_folders(_,names):return {n for n in names if n in {"Level","Slot1","Slot2","Slot3"}}
        new_name=generate_random_name()
        xgp_converted_saves_path=os.path.join(root_dir,"XGP_converted_saves")
        os.makedirs(xgp_converted_saves_path,exist_ok=True)
        new_converted_target_folder=os.path.join(xgp_converted_saves_path,new_name)
        shutil.copytree(source_folder,new_converted_target_folder,dirs_exist_ok=True,ignore=ignore_folders)
        new_target_folder=os.path.join(destination_folder,new_name)
        shutil.copytree(source_folder,new_target_folder,dirs_exist_ok=True,ignore=ignore_folders)
        messagebox.showinfo(t("Success"),t("xgp.msg.convert_copied",dest=destination_folder))
    except Exception as e:
        print(t("xgp.err.copy_exception",err=e))
        traceback.print_exc()
        messagebox.showerror(t("Error"),t("xgp.err.copy_failed",err=e))
def transfer_steam_to_gamepass(source_folder):
    try:
        import_path = os.path.join(base_dir, "palworld_xgp_import")
        sys.path.insert(0, import_path)
        from palworld_xgp_import import main as xgp_main
        old_argv = sys.argv
        try:
            sys.argv = ["main.py", source_folder]
            xgp_main.main()
            messagebox.showinfo(t("Success"), t("xgp.msg.steam_to_xgp_ok"))
        except Exception as e:
            print(t("xgp.err.conversion_exception", err=e))
            messagebox.showerror(t("Error"), t("xgp.err.conversion_failed", err=e))
        finally:
            sys.argv = old_argv
            if import_path in sys.path: sys.path.remove(import_path)
    except ImportError as e:
        print(t("xgp.err.import_exception", err=e))
        messagebox.showerror(t("Error"), t("xgp.err.import_failed", err=e))
def update_combobox(saveList):
    global saves
    saves = saveList
    for widget in save_frame.winfo_children(): widget.destroy()
    if saves:
        combobox = ttk.Combobox(save_frame, values=saves, font=("Arial", 12))
        combobox.pack(pady=(10, 10), fill='x')
        combobox.set(t("xgp.ui.choose_save"))
        button = ttk.Button(save_frame, text=t("xgp.ui.convert"), command=lambda: convert_JSON_sav(combobox.get()))
        button.pack(pady=(0, 10), fill='x')
def game_pass_save_fix():
    default_source = os.path.join(root_dir, "saves")
    if os.path.exists(default_source): shutil.rmtree(default_source)
    global window, save_frame
    window = tk.Toplevel()
    window.title(t("xgp.title.converter"))
    window.geometry("480x230")
    window.config(bg="#2f2f2f")
    try: window.iconbitmap(ICON_PATH)
    except Exception as e: print(f"Could not set icon: {e}")
    font_style = ("Arial", 11)
    style = ttk.Style(window)
    style.theme_use('clam')
    for opt in [
        ("TFrame", {"background": "#2f2f2f"}),
        ("TLabel", {"background": "#2f2f2f", "foreground": "white", "font": font_style}),
        ("TButton", {"background": "#555555", "foreground": "white", "font": font_style, "padding": 6}),
        ("TCombobox", {"fieldbackground": "#444444", "background": "#333333", "foreground": "white", "font": font_style}),
    ]: style.configure(opt[0], **opt[1])
    style.map("TButton", background=[("active", "#666666"), ("!disabled", "#555555")], foreground=[("disabled", "#888888"), ("!disabled", "white")])
    main_frame = ttk.Frame(window, style="TFrame")
    main_frame.pack(expand=True, fill="both", padx=20, pady=20)
    xgp_button = ttk.Button(main_frame, text=t("xgp.ui.btn_xgp_folder"), command=get_save_game_pass)
    xgp_button.pack(pady=(0, 10), fill='x')
    steam_button = ttk.Button(main_frame, text=t("xgp.ui.btn_steam_folder"), command=get_save_steam)
    steam_button.pack(pady=(0, 20), fill='x')
    save_frame = ttk.Frame(main_frame, style="TFrame")
    save_frame.pack(fill='both', expand=True)
    center_window(window)
    def on_exit(): shutil.rmtree(os.path.join(root_dir, "saves"), ignore_errors=True); window.destroy()
    window.protocol("WM_DELETE_WINDOW", on_exit)
    return window
if __name__ == "__main__": game_pass_save_fix()