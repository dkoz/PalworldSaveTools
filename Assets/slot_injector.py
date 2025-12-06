from import_libs import *
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
class SlotNumUpdaterApp(tk.Toplevel):
    def __init__(self):
        super().__init__()
        self.title(t("tool.slot_injector"))
        self.config(bg="#2f2f2f")
        self.geometry("600x180")
        try:self.iconbitmap(ICON_PATH)
        except:pass
        style=ttk.Style(self)
        style.theme_use('clam')
        style.configure("TFrame",background="#2f2f2f")
        style.configure("TLabel",background="#2f2f2f",foreground="white")
        style.configure("TEntry",fieldbackground="#444444",foreground="white")
        style.configure("Dark.TButton",background="#555555",foreground="white",padding=6)
        frame=ttk.Frame(self)
        frame.pack(padx=20,pady=10,fill='x')
        row=0
        ttk.Button(frame,text=t("browse"),command=self.browse_file,style="Dark.TButton").grid(row=row,column=0)
        ttk.Label(frame,text=t("slot.select_level_sav"),style="TLabel").grid(row=row,column=1,sticky="w",padx=(10,5))
        self.file_entry=ttk.Entry(frame)
        self.file_entry.grid(row=row,column=2,sticky="ew")
        row+=1
        ttk.Label(frame,text=t("slot.total_pages"),style="TLabel").grid(row=row,column=0,sticky="w")
        self.pages_entry=ttk.Entry(frame,width=10)
        self.pages_entry.grid(row=row,column=1)
        row+=1
        ttk.Label(frame,text=t("slot.total_slots"),style="TLabel").grid(row=row,column=0,sticky="w")
        self.slots_entry=ttk.Entry(frame,width=10)
        self.slots_entry.grid(row=row,column=1)
        row+=1
        ttk.Button(frame,text=t("slot.apply"),command=self.apply_slotnum_update,style="Dark.TButton").grid(row=row,column=0,columnspan=3,pady=10)
        frame.columnconfigure(2,weight=1)
        center_window(self)
        self.protocol("WM_DELETE_WINDOW",self.destroy)
    def browse_file(self):
        file=filedialog.askopenfilename(title=t("slot.select_level_sav_title"),filetypes=[("SAV","Level.sav")])
        if file:
            self.file_entry.delete(0,tk.END)
            self.file_entry.insert(0,file)
            self.load_selected_save()
    def load_selected_save(self):
        fp=self.file_entry.get()
        if not fp.endswith("Level.sav"):
            messagebox.showerror(t("error.title"),t("slot.invalid_file"))
            return
        try:
            self.level_json=sav_to_json(fp)
            messagebox.showinfo(t("slot.loaded_title"),t("slot.loaded_msg"))
        except Exception:
            raise
    def apply_slotnum_update(self):
        filepath=self.file_entry.get()
        if not hasattr(self,"level_json"):
            messagebox.showerror(t("error.title"),t("slot.load_first"))
            return
        try:
            pages=int(self.pages_entry.get())
            slots=int(self.slots_entry.get())
            if pages<1 or slots<1:
                raise ValueError
        except ValueError:
            messagebox.showerror(t("error.title"),t("slot.invalid_numbers"))
            return
        new_value=pages*slots
        level_json=self.level_json
        container=level_json["properties"]["worldSaveData"]["value"].get("CharacterContainerSaveData",{}).get("value",[])
        if not isinstance(container,list):
            messagebox.showerror(t("error.title"),t("slot.invalid_structure"))
            return
        PLAYER_SLOT_THRESHOLD=960
        editable=[entry for entry in container if entry.get("value",{}).get("SlotNum",{}).get("value",0)>=PLAYER_SLOT_THRESHOLD]
        total_players=len(editable)
        if total_players==0:
            messagebox.showinfo(t("info.title"),t("slot.no_entries"))
            return
        resp=messagebox.askyesno(t("slot.confirm_title"),t("slot.confirm_msg",count=total_players,new=new_value))
        if not resp:
            return
        for entry in editable:
            entry["value"]["SlotNum"]["value"]=new_value
        backup_whole_directory(os.path.dirname(filepath),"Backups/Slot Injector")
        json_to_sav(level_json,filepath)
        messagebox.showinfo(t("success.title"),t("slot.success_msg",count=total_players,new=new_value))
def slot_injector():
    return SlotNumUpdaterApp()