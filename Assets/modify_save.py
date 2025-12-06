from import_libs import *
def _format_bytes(num:int)->str:
    for unit in("B","KB","MB","GB"):
        if num<1024 or unit=="GB":
            return f"{num:.1f}{unit}" if unit!="B" else f"{num}{unit}"
        num/=1024
def download_from_github(repo_owner, repo_name, version, download_path):
    file_url=get_release_assets(repo_owner,repo_name,version)
    if not file_url: print("Error: No valid asset found."); return None
    try:
        file_name=file_url.split("/")[-1]
        file_path=os.path.join(download_path,file_name)
        req=urllib.request.Request(file_url,headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req,timeout=60) as response, open(file_path,"wb") as f:
            total=int(response.getheader("Content-Length","0") or 0)
            downloaded=0
            block=1024*128
            last_pct=-1
            while True:
                chunk=response.read(block)
                if not chunk: break
                f.write(chunk)
                downloaded+=len(chunk)
                if total:
                    pct=int(downloaded*100/total)
                    if pct!=last_pct and pct%5==0:
                        print(f"Downloading... {pct}% ({_format_bytes(downloaded)}/{_format_bytes(total)})")
                        sys.stdout.flush()
                        last_pct=pct
        print(f"File '{file_name}' downloaded successfully to '{download_path}'")
        return file_path
    except Exception as e:
        print(f"Error downloading file: {e}")
        return None
def get_release_assets(repo_owner, repo_name, version):
    api_url=f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/tags/{version}"
    try:
        with urllib.request.urlopen(api_url) as response:
            release_data=json.load(response)
            for asset in release_data.get('assets',[]):
                name=asset['name'].lower()
                if 'windows-standalone' in name and name.endswith('.zip'):
                    return asset['browser_download_url']
    except Exception as e:
        print(f"Error fetching release info: {e}")
    return None
def get_release_asset_url_filtered(repo_owner,repo_name,version,keywords,extensions):
    api_url=f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/tags/{version}"
    try:
        with urllib.request.urlopen(api_url) as response:
            release_data=json.load(response)
            for asset in release_data.get('assets',[]):
                name=asset.get('name','').lower()
                if any(k in name for k in keywords) and any(name.endswith(ext) for ext in extensions):
                    return asset.get('browser_download_url')
    except Exception as e:
        print(f"Error fetching filtered release info: {e}")
    return None
def extract_zip(directory,partial_name,extract_to):
    for root,_,files in os.walk(directory):
        for file in files:
            if file.endswith('.zip') and partial_name in file:
                zpath=os.path.join(root,file)
                try:
                    with zipfile.ZipFile(zpath,'r') as zip_ref:
                        zip_ref.extractall(extract_to)
                    print(f"Extracted {file} to {extract_to}")
                except Exception as e:
                    print(f"Error extracting {file}: {e}")
def extract_exact_zip(zip_path,extract_to):
    try:
        with zipfile.ZipFile(zip_path,'r') as zip_ref:
            zip_ref.extractall(extract_to)
        print(f"Extracted {os.path.basename(zip_path)} to {extract_to}")
        return True
    except Exception as e:
        print(f"Error extracting {zip_path}: {e}")
        return False
def get_latest_version(repo_owner,repo_name):
    api_url=f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/latest"
    try:
        with urllib.request.urlopen(api_url) as response:
            latest_release=json.load(response)
            return latest_release['tag_name']
    except Exception as e:
        print(f"Error fetching release info: {e}")
        return None
def find_exe(folder):
    for root,_,files in os.walk(folder):
        for f in files:
            if f.lower()=="psp.exe": return os.path.join(root,f)
    return None
def find_any_exe(folder):
    for root,_,files in os.walk(folder):
        for f in files:
            if f.lower().endswith('.exe'): return os.path.join(root,f)
    return None
def open_exe_with_cwd(exe_path):
    subprocess.Popen([exe_path], cwd=os.path.dirname(exe_path))
def _launch_save_pal():
    repo_owner="oMaN-Rod"; repo_name="palworld-save-pal"; version=get_latest_version(repo_owner,repo_name)
    if not version: print("Unable to fetch latest release version."); return
    exe_path=find_exe("psp_windows")
    if exe_path: print("Opening Palworld Save Pal..."); open_exe_with_cwd(exe_path); return
    print("Downloading Palworld Save Pal...")
    zip_file=download_from_github(repo_owner,repo_name,version,".")
    if zip_file:
        extract_zip(".","windows-standalone","psp_windows")
        try: os.remove(zip_file)
        except FileNotFoundError: pass
        exe_path=find_exe("psp_windows")
        if exe_path: print("Opening Palworld Save Pal..."); open_exe_with_cwd(exe_path)
        else: print("Extraction succeeded but could not find psp.exe.")
    else: print("Failed to download Palworld Save Pal...")
def _download_to(path_dir,file_url):
    try:
        os.makedirs(path_dir,exist_ok=True)
        file_name=file_url.split("/")[-1]; file_path=os.path.join(path_dir,file_name)
        req=urllib.request.Request(file_url,headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req,timeout=60) as response, open(file_path,"wb") as f:
            total=int(response.getheader("Content-Length","0") or 0); downloaded=0; block=1024*128; last_pct=-1
            while True:
                chunk=response.read(block)
                if not chunk: break
                f.write(chunk); downloaded+=len(chunk)
                if total:
                    pct=int(downloaded*100/total)
                    if pct!=last_pct and pct%5==0:
                        print(f"Downloading... {pct}%"); sys.stdout.flush(); last_pct=pct
        print(f"File '{file_name}' downloaded successfully to '{path_dir}'")
        return file_path
    except Exception as e:
        print(f"Error downloading file: {e}"); return None
def _launch_pal_editor():
    repo_owner="KrisCris"; repo_name="Palworld-Pal-Editor"; version=get_latest_version(repo_owner,repo_name)
    if not version: print("Unable to fetch latest release version."); open_file_with_default_app("https://github.com/KrisCris/Palworld-Pal-Editor"); return
    target_dir="ppe_windows"; exe_path=find_any_exe(target_dir)
    if exe_path: print("Opening Palworld Pal Editor..."); open_exe_with_cwd(exe_path); return
    print("Downloading Palworld Pal Editor...")
    file_url=get_release_asset_url_filtered(repo_owner,repo_name,version,keywords=["win","windows"],extensions=[".zip",".exe"])
    if not file_url: print("No suitable asset found for Pal Editor."); open_file_with_default_app("https://github.com/KrisCris/Palworld-Pal-Editor"); return
    downloaded=_download_to(".",""+file_url)
    if not downloaded: print("Failed to download Pal Editor."); return
    if downloaded.lower().endswith('.zip'):
        os.makedirs(target_dir,exist_ok=True)
        if extract_exact_zip(downloaded,target_dir):
            try: os.remove(downloaded)
            except FileNotFoundError: pass
            exe_path=find_any_exe(target_dir)
            if exe_path: print("Opening Palworld Pal Editor..."); open_exe_with_cwd(exe_path)
            else: print("Extraction succeeded but could not find an exe.")
        else: print("Extraction failed for Pal Editor archive.")
    elif downloaded.lower().endswith('.exe'):
        os.makedirs(target_dir,exist_ok=True)
        try:
            dest=os.path.join(target_dir,os.path.basename(downloaded))
            if os.path.abspath(downloaded)!=os.path.abspath(dest):
                try: shutil.move(downloaded,dest)
                except Exception: shutil.copy2(downloaded,dest); os.remove(downloaded)
            open_exe_with_cwd(dest)
        except Exception as e: print(f"Error preparing Pal Editor executable: {e}")
    else: print("Downloaded file is not a supported type.")
def _build_selector_window():
    win=tk.Toplevel(); win.title(t("modify.dialog.title")); win.resizable(False,False)
    frm=ttk.Frame(win,padding=10); frm.pack(fill="both",expand=True)
    ttk.Label(frm,text=t("modify.dialog.choose_editor")).pack(anchor="w",pady=(0,6))
    ttk.Label(frm,text=t("modify.dialog.note_backup"),foreground="#f44").pack(anchor="w",pady=(0,10))
    btns=ttk.Frame(frm); btns.pack(fill="x")
    try:
        if os.name == 'nt':
            ico_path = os.path.abspath('Assets/resources/pal.ico')
            if os.path.exists(ico_path): win.iconbitmap(ico_path)
    except Exception as e: print(f"Error setting icon: {e}")
    style=ttk.Style(win); style.theme_use("clam"); style.configure("Dark.TButton",background="#555555",foreground="white",padding=6); style.map("Dark.TButton",background=[("active","#666666")],foreground=[("disabled","#888888"),("!disabled","white")])    
    def on_savepal():
        _launch_save_pal()
        win.destroy()    
    def on_paleditor():
        _launch_pal_editor()
        win.destroy()    
    ttk.Button(btns,text=t("modify.dialog.option.savepal"),style="Dark.TButton",command=on_savepal).pack(side="left",padx=(0,8))
    ttk.Button(btns,text=t("modify.dialog.option.paleditor"),style="Dark.TButton",command=on_paleditor).pack(side="left",padx=(0,8))
    ttk.Button(btns,text=t("modify.dialog.cancel"),style="Dark.TButton",command=win.destroy).pack(side="right")    
    try: win.grab_set()
    except Exception: pass
    win.update_idletasks(); w,h=win.winfo_width(),win.winfo_height(); ws,hs=win.winfo_screenwidth(),win.winfo_screenheight(); x,y=(ws-w)//2,(hs-h)//2; win.geometry(f"{w}x{h}+{x}+{y}")
    win.wait_window()
    return win
def modify_save():
    return _build_selector_window()
class MenuGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        try: self.iconbitmap("Assets/resources/pal.ico")
        except Exception: pass
        style=ttk.Style(self); style.theme_use("clam")
        style.configure("TFrame",background="#2f2f2f"); style.configure("TLabel",background="#2f2f2f",foreground="white")
        style.configure("TEntry",fieldbackground="#444444",foreground="white")
        style.configure("Treeview.Heading",font=("Arial",12,"bold"),background="#444444",foreground="white")
        style.configure("Treeview",background="#333333",foreground="white",rowheight=25,fieldbackground="#333333",borderwidth=0)
        style.configure("Dark.TButton",background="#555555",foreground="white",padding=6)
        style.map("Dark.TButton",background=[("active","#666666"),("!disabled","#555555")],foreground=[("disabled","#888888"),("!disabled","white")])
        self.title(t("app.title")); self.configure(bg="#2f2f2f"); self.geometry("800x530"); self.resizable(False,True)
        self.info_labels=[]; self.category_frames=[]; self.tool_buttons=[]; self.lang_combo=None; self.setup_ui(); self._add_pal_tools_button()
    def setup_ui(self):
        root_frame=ttk.Frame(self,style="TFrame"); root_frame.pack(fill="both",expand=True,padx=10,pady=10)
        canvas=tk.Canvas(root_frame,bg="#2f2f2f",highlightthickness=0); vbar=ttk.Scrollbar(root_frame,orient="vertical",command=canvas.yview); canvas.configure(yscrollcommand=vbar.set); canvas.pack(side="left",fill="both",expand=True); vbar.pack(side="right",fill="y")
        container=ttk.Frame(canvas,style="TFrame"); win=canvas.create_window((0,0),window=container,anchor="nw")
        container.bind("<Configure>",lambda e: canvas.configure(scrollregion=canvas.bbox("all"))); canvas.bind("<Configure>",lambda e: canvas.itemconfigure(win,width=e.width))
        canvas.bind_all("<MouseWheel>",lambda e: canvas.yview_scroll(-1*int(e.delta/120) if e.delta else 0,"units"))
        topbar=ttk.Frame(container,style="TFrame"); topbar.pack(fill="x",pady=(0,6))
        ttk.Label(topbar,text=t("lang.label")+":",style="TLabel").pack(side="left",padx=(0,6))
        self.lang_combo=ttk.Combobox(topbar,state="readonly",values=[]); self.lang_combo.pack(side="left"); self.lang_combo.bind("<<ComboboxSelected>>",lambda e:self.on_language_change())
        logo_path=os.path.join("Assets","resources","PalworldSaveTools.png")
        if os.path.exists(logo_path): img=Image.open(logo_path).resize((400,100),Image.LANCZOS); self.logo_img=ImageTk.PhotoImage(img); ttk.Label(container,image=self.logo_img,style="TLabel").pack(anchor="center",pady=(0,10))
        tools_version="1.0"; info_items=[("app.subtitle",{}, "#6f9",("Consolas",10)),("notice.backup",{}, "#f44",("Consolas",9,"bold")),("notice.patch",{}, "#f44",("Consolas",9,"bold")),("notice.errors",{}, "#f44",("Consolas",9,"bold"))]
        for key,fmt,color,font in info_items: label=ttk.Label(container,text=t(key,**fmt),style="TLabel"); label.configure(foreground=color,font=font); label.pack(pady=(0,2)); self.info_labels.append((label,key,fmt))
        ttk.Label(container,text="="*85,font=("Consolas",12),style="TLabel").pack(pady=(5,10))
        tools_frame=ttk.Frame(container,style="TFrame"); tools_frame.pack(fill="both",expand=True); tools_frame.columnconfigure(0,weight=1); tools_frame.columnconfigure(1,weight=1)
        left_frame=ttk.Frame(tools_frame,style="TFrame"); left_frame.grid(row=0,column=0,sticky="nsew",padx=(0,6))
        right_frame=ttk.Frame(tools_frame,style="TFrame"); right_frame.grid(row=0,column=1,sticky="nsew",padx=(6,0))
        for i,frame in enumerate([left_frame,right_frame]): self.category_frames.append(frame)
    def _add_pal_tools_button(self):
        btn=ttk.Button(self.category_frames[0],text=t("pal.tools.title"),style="Dark.TButton",command=_build_selector_window); btn.pack(fill="x",pady=(0,4)); self.tool_buttons.append(btn)
    def on_language_change(self):
        lang=self.lang_combo.get(); set_language(lang); load_resources(lang)
        for label,key,fmt in self.info_labels: label.configure(text=t(key,**fmt))
if __name__ == "__main__":
    modify_save()