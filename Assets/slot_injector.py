from import_libs import *
def sav_to_json(filepath):
    with open(filepath, "rb") as f:
        data = f.read()
        raw_gvas, save_type = decompress_sav_to_gvas(data)
    gvas_file = GvasFile.read(raw_gvas, PALWORLD_TYPE_HINTS, SKP_PALWORLD_CUSTOM_PROPERTIES, allow_nan=True)
    return gvas_file.dump()
def json_to_sav(json_data, output_filepath):
    gvas_file = GvasFile.load(json_data)
    save_type = 0x32 if "Pal.PalworldSaveGame" in gvas_file.header.save_game_class_name or "Pal.PalLocalWorldSaveGame" in gvas_file.header.save_game_class_name else 0x31
    sav_file = compress_gvas_to_sav(gvas_file.write(SKP_PALWORLD_CUSTOM_PROPERTIES), save_type)
    with open(output_filepath, "wb") as f:
        f.write(sav_file)
class SlotNumUpdaterApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(t("tool.slot_injector"))
        self.geometry("600x180")
        self.config(bg="#2f2f2f")
        try: self.iconbitmap(ICON_PATH)
        except Exception as e: print(f"Could not set icon: {e}")
        font_style = ("Arial", 10)
        style = ttk.Style(self)
        style.theme_use('clam')
        for opt in [
            ("TFrame", {"background": "#2f2f2f"}),
            ("TLabel", {"background": "#2f2f2f", "foreground": "white", "font": font_style}),
            ("TEntry", {"fieldbackground": "#444444", "foreground": "white", "font": font_style}),
            ("Dark.TButton", {"background": "#555555", "foreground": "white", "font": font_style, "padding": 6}),
        ]: style.configure(opt[0], **opt[1])
        style.map("Dark.TButton",
            background=[("active", "#666666"), ("!disabled", "#555555")],
            foreground=[("disabled", "#888888"), ("!disabled", "white")]
        )
        frame = ttk.Frame(self, style="TFrame")
        frame.pack(padx=20, pady=10, fill='x', expand=True)
        row = 0
        ttk.Button(frame, text=t("Browse"), command=self.browse_file, style="Dark.TButton").grid(row=row, column=0, sticky='w')
        ttk.Label(frame, text=t("Select Level.sav File:"), style="TLabel").grid(row=row, column=1, sticky='w', padx=(10,5))
        self.file_entry = ttk.Entry(frame, style="TEntry")
        self.file_entry.grid(row=row, column=2, sticky='ew')
        row += 1
        ttk.Label(frame, text=t("Total Pages:"), style="TLabel").grid(row=row, column=0, sticky='w', pady=5)
        self.pages_entry = ttk.Entry(frame, style="TEntry", width=10)
        self.pages_entry.grid(row=row, column=1, sticky='w', pady=5)
        row += 1
        ttk.Label(frame, text=t("Total Slots:"), style="TLabel").grid(row=row, column=0, sticky='w', pady=5)
        self.slots_entry = ttk.Entry(frame, style="TEntry", width=10)
        self.slots_entry.grid(row=row, column=1, sticky='w', pady=5)
        row += 1
        ttk.Button(frame, text=t("Apply Slot Injection"), command=self.apply_slotnum_update, style="Dark.TButton").grid(row=row, column=0, columnspan=3, pady=10)
        frame.columnconfigure(2, weight=1)
        center_window(self)
    def browse_file(self):
        file = filedialog.askopenfilename(title=t("Select Level.sav file"), filetypes=[("SAV files", "Level.sav")])
        if file:
            self.file_entry.delete(0, tk.END)
            self.file_entry.insert(0, file)
    def apply_slotnum_update(self):
        filepath = self.file_entry.get()
        if not filepath or not os.path.isfile(filepath) or not filepath.endswith("Level.sav"):
            print("Error: Select a valid Level.sav file")
            return
        try:
            pages = int(self.pages_entry.get())
            slots = int(self.slots_entry.get())
            if pages < 1 or slots < 1: raise ValueError
        except ValueError:
            print("Error: Please enter valid positive integers for pages and slots")
            return
        new_value = pages * slots
        level_json = sav_to_json(filepath)
        container = level_json['properties']['worldSaveData']['value'].get('CharacterContainerSaveData', {}).get('value', [])
        if not isinstance(container, list):
            print("Error: CharacterContainerSaveData.value is not a list.")
            return
        PLAYER_SLOT_THRESHOLD = 960
        editable_entries = [(idx, val.get('SlotNum', {}).get('value', 0), entry)
                            for idx, entry in enumerate(container)
                            if (val := entry.get('value', {})).get('SlotNum', {}).get('value', 0) >= PLAYER_SLOT_THRESHOLD]
        player_count = len(editable_entries)
        if player_count == 0:
            print("Info: No editable player entries found.")
            return
        print(f"Found {player_count} editable player(s):")
        for idx, cur_val, _ in editable_entries:
            print(f"  Entry {idx}: current SlotNum = {cur_val} → new = {new_value}")
        updated_count = 0
        for idx, cur_val, entry in editable_entries:
            slotnum = entry.get('value', {}).get('SlotNum', {})
            if slotnum.get('value') == cur_val:
                slotnum['value'] = new_value
                updated_count += 1
        backup_whole_directory(os.path.dirname(filepath), "Backups/Slot Injector")
        json_to_sav(level_json, filepath)
        print(f"Success: Updated {updated_count} SlotNum entries to {new_value} in Level.sav!")
def slot_injector():
    def on_exit(): app.destroy()
    app = SlotNumUpdaterApp()
    app.protocol("WM_DELETE_WINDOW", app.destroy)
    return app
if __name__ == "__main__":
    app = slot_injector()
    app.mainloop()