from import_libs import *
def get_steam_id_from_local():
    local_app_data_path = os.path.expandvars(r"%localappdata%\Pal\Saved\SaveGames")
    if os.path.exists(local_app_data_path):
        subdirs = [d for d in os.listdir(local_app_data_path) if os.path.isdir(os.path.join(local_app_data_path, d))]
        return subdirs[0] if subdirs else None
    return None
def convert_steam_id():
    def do_convert(steam_input=None):
        steam_input = steam_entry.get().strip() if steam_input is None else steam_input
        if not steam_input:
            messagebox.showwarning(t("Warning"), t("steamid.warn.enter_id"))
            return
        if "steamcommunity.com/profiles/" in steam_input:
            steam_input = steam_input.split("steamcommunity.com/profiles/")[1].split("/")[0]
        elif steam_input.startswith("steam_"):
            steam_input = steam_input[6:]
        try:
            steam_id = int(steam_input)
            palworld_uid = steamIdToPlayerUid(steam_id)
            nosteam_uid = PlayerUid2NoSteam(int.from_bytes(toUUID(palworld_uid).raw_bytes[0:4], byteorder='little')) + "-0000-0000-0000-000000000000"
            steam_result.set(t("steamid.result", pal=str(palworld_uid).upper(), nosteam=nosteam_uid.upper()))
        except ValueError:
            messagebox.showerror(t("Error"), t("steamid.err.invalid"))
    steam_id_from_local = get_steam_id_from_local()
    window = tk.Toplevel()
    window.title(t("steamid.title"))
    window.geometry("600x250")
    window.config(bg="#2f2f2f")
    try:
        window.iconbitmap(ICON_PATH)
    except:
        pass
    font_style = ("Arial", 10)
    style = ttk.Style(window)
    style.theme_use("clam")
    style.configure("TLabel", background="#2f2f2f", foreground="white", font=font_style)
    style.configure("Dark.TButton", background="#555555", foreground="white", font=font_style, padding=6)
    style.map("Dark.TButton", background=[("active", "#666666"), ("!disabled", "#555555")])
    ttk.Label(window, text=t("steamid.tip"), anchor="center", justify="center", style="TLabel").pack(fill="x", pady=(10,5))
    ttk.Label(window, text=t("steamid.local_hint"), anchor="center", justify="center", style="TLabel").pack(fill="x", pady=(0,10))
    steam_entry = ttk.Entry(window, width=40, font=font_style)
    steam_entry.pack(pady=5)
    ttk.Button(window, text=t("steamid.btn.convert"), style="Dark.TButton", command=lambda: do_convert()).pack(pady=10)
    steam_result = tk.StringVar()
    ttk.Label(window, textvariable=steam_result, font=font_style, style="TLabel").pack(pady=(10,0))
    def copy_result():
        window.clipboard_clear()
        window.clipboard_append(steam_result.get())
    ttk.Button(window, text="📋", style="Dark.TButton", width=3, command=copy_result).pack(pady=(5,10))
    if steam_id_from_local:
        try:
            steam_entry.insert(0, steam_id_from_local)
            do_convert(steam_id_from_local)
        except Exception as e:
            print(t("steamid.err.autoconvert"), e)
    center_window(window)
    window.protocol("WM_DELETE_WINDOW", lambda: window.destroy())
    window.grab_set()
    return window
def center_window(win):
    win.update_idletasks()
    w, h = win.winfo_width(), win.winfo_height()
    ws, hs = win.winfo_screenwidth(), win.winfo_screenheight()
    x, y = (ws - w) // 2, (hs - h) // 2
    win.geometry(f'{w}x{h}+{x}+{y}')
def main(): convert_steam_id()
if __name__ == "__main__": main()