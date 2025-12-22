from import_libs import *
import customtkinter as ctk
from ui_theme import (
    apply_theme, BG as DARK_BG, GLASS as GLASS_BG, TEXT as TEXT_COLOR, ACCENT as ACCENT_COLOR,
    BORDER as BORDER_COLOR, BUTTON_BG, BUTTON_HOVER, MUTED as MUTED_COLOR, EMPHASIS as EMPHASIS_COLOR,
    ALERT as ALERT_COLOR, SUCCESS as SUCCESS_COLOR, ERROR as ERROR_COLOR, BUTTON_FG,
    BUTTON_PRIMARY, BUTTON_SECONDARY, FONT, FONT_BOLD, FONT_LARGE, FONT_SMALL,
    SPACE_SMALL, SPACE_MEDIUM, SPACE_LARGE, CTK_BUTTON_CORNER_RADIUS, CTK_FRAME_CORNER_RADIUS, TREE_ROW_HEIGHT
)
apply_theme()
GITHUB_RAW_URL = "https://raw.githubusercontent.com/deafdudecomputers/PalworldSaveTools/main/Assets/common.py"
def check_for_update():
    try:
        r=urllib.request.urlopen(GITHUB_RAW_URL,timeout=5)
        content=r.read().decode("utf-8")
        match=re.search(r'APP_VERSION\s*=\s*"([^"]+)"',content)
        latest=match.group(1) if match else None
        local,_=get_versions()
        if not latest:
            return None
        local_tuple=tuple(int(x) for x in local.split("."))
        latest_tuple=tuple(int(x) for x in latest.split("."))
        return {"local":local,"latest":latest,"update_available":latest_tuple>local_tuple}
    except Exception as e:
        print("Update check error:",e)
        return None
current_save_path = None
loaded_level_json = None
original_loaded_level_json = None
window = None
stat_labels = None
guild_tree = None
base_tree = None
player_tree = None
guild_members_tree = None
guild_search_var = None
base_search_var = None
player_search_var = None
guild_members_search_var = None
guild_result = None
base_result = None
player_result = None
files_to_delete = set()
PLAYER_PAL_COUNTS = {}
PLAYER_DETAILS_CACHE = {}
PLAYER_REMAPS = {}
def refresh_stats(section):
    stats = get_current_stats()
    section_keys = {
        "Before": "deletion.stats.before",
        "After": "deletion.stats.after",
        "Result": "deletion.stats.result",
        "After Reset": "deletion.stats.after"
    }
    display_section = t(section_keys.get(section, section))
    if section == "Before":
        refresh_stats.stats_before = stats
    if section == "After Reset":
        zero_stats = {k: 0 for k in stats}
        update_stats_section(stat_labels, "After", zero_stats)
        update_stats_section(stat_labels, "Result", zero_stats)
    else:
        update_stats_section(stat_labels, section, stats)
        if section == "After" and hasattr(refresh_stats, "stats_before"):
            before = refresh_stats.stats_before
            result = {k: before[k] - stats.get(k, 0) for k in before}
            update_stats_section(stat_labels, "Result", result)
def as_uuid(val): return str(val).lower() if val else ''
def are_equal_uuids(a,b): return as_uuid(a)==as_uuid(b)
def fast_deepcopy(json_dict): return pickle.loads(pickle.dumps(json_dict, -1))
def sav_to_json(path):
    with open(path,"rb") as f:
        data = f.read()
    raw_gvas, _ = decompress_sav_to_gvas(data)
    g = GvasFile.read(raw_gvas, PALWORLD_TYPE_HINTS, SKP_PALWORLD_CUSTOM_PROPERTIES, allow_nan=True)
    return g.dump()
def json_to_sav(j,path):
    g = GvasFile.load(j)
    t = 0x32 if "Pal.PalworldSaveGame" in g.header.save_game_class_name else 0x31
    data = compress_gvas_to_sav(g.write(SKP_PALWORLD_CUSTOM_PROPERTIES),t)
    with open(path,"wb") as f: f.write(data)
def ask_string_with_icon(title,prompt,icon_path,mode="text"):
    class CustomDialog(simpledialog.Dialog):
        def __init__(self,parent,title):
            self.mode=mode
            super().__init__(parent,title)
        def body(self,master):
            try: self.iconbitmap(icon_path)
            except: pass
            self.geometry("400x150")
            self.configure(bg="#2f2f2f")
            master.configure(bg="#2f2f2f")
            tk.Label(master,text=prompt,bg="#2f2f2f",fg="white",font=("Arial",10)).grid(row=0,column=0,padx=15,pady=15)
            self.entry=tk.Entry(master,bg="#444444",fg="white",insertbackground="white",font=("Arial",10))
            self.entry.grid(row=1,column=0,padx=15)
            return self.entry
        def buttonbox(self):
            box=tk.Frame(self,bg="#2f2f2f")
            tk.Button(box,text="OK",width=10,command=self.ok,bg="#555555",fg="white",font=("Arial",10),relief="flat",activebackground="#666666").pack(side="left",padx=5,pady=5)
            tk.Button(box,text="Cancel",width=10,command=self.cancel,bg="#555555",fg="white",font=("Arial",10),relief="flat",activebackground="#666666").pack(side="left",padx=5,pady=5)
            self.bind("<Return>",lambda e:self.ok())
            self.bind("<Escape>",lambda e:self.cancel())
            box.pack()
        def validate(self):
            if self.mode=="number":
                try:
                    int(self.entry.get())
                    return True
                except ValueError:
                    messagebox.showerror(t("Invalid Input"),t("Please enter a valid number."))
                    return False
            return True
        def apply(self):
            val=self.entry.get()
            if self.mode=="number":
                self.result=int(val)
            else:
                self.result=val
    root=tk.Tk()
    root.withdraw()
    dlg=CustomDialog(root,title)
    root.destroy()
    return dlg.result
def clean_character_save_parameter_map(data_source, valid_uids):
    if "CharacterSaveParameterMap" not in data_source: return
    entries = data_source["CharacterSaveParameterMap"].get("value", [])
    keep = []
    for entry in entries:
        key = entry.get("key", {})
        value = entry.get("value", {}).get("RawData", {}).get("value", {})
        saveparam = value.get("object", {}).get("SaveParameter", {}).get("value", {})
        inst_id = key.get("InstanceId", {}).get("value", "")
        owner_uid_obj = saveparam.get("OwnerPlayerUId")
        if owner_uid_obj is None:
            keep.append(entry)
            continue
        owner_uid = owner_uid_obj.get("value", "")
        no_owner = owner_uid in ("", "00000000-0000-0000-0000-000000000000")
        player_uid = key.get("PlayerUId", {}).get("value", "")
        if (player_uid and str(player_uid).replace("-", "") in valid_uids) or \
           (str(owner_uid).replace("-", "") in valid_uids) or \
           no_owner:
            keep.append(entry)
    entries[:] = keep
from concurrent.futures import ThreadPoolExecutor, as_completed
dps_executor = None
dps_futures = []
dps_tasks = []
def start_dps_processing_background(t0):
    global dps_executor, dps_futures
    futures = start_dps_processing()
    if not futures: return
    start_time = time.perf_counter()
    def monitor(t0_local):
        for future in as_completed(futures):
            try: future.result()
            except Exception as e: print(f"DPS processing failed: {e}")
        t3 = time.perf_counter()
        print(f"DPS processing has completed in: {t3-start_time:.2f}s")
        print(f"Total time (loading + DPS): {t3-t0_local:.2f}s")
    threading.Thread(target=monitor, args=(t0,), daemon=True).start()
def start_dps_processing():
    global dps_executor, dps_futures
    if not dps_tasks: return []
    dps_executor = ThreadPoolExecutor(max_workers=os.cpu_count() or 4)
    dps_futures = [dps_executor.submit(process_dps_save, uid, pname, dps_file, log_folder)
                   for uid, pname, dps_file, log_folder in dps_tasks]
    return dps_futures
def top_process_player(p, playerdir, log_folder):
    uid = p.get('player_uid')
    pname = p.get('player_info', {}).get('player_name', 'Unknown')
    uniques = caught = encounters = 0
    if not uid: return uid, pname, uniques, caught, encounters
    clean_uid = str(uid).replace('-', '')
    sav_file = os.path.join(playerdir, f"{clean_uid}.sav")
    dps_file = os.path.join(playerdir, f"{clean_uid}_dps.sav")
    if os.path.isfile(sav_file):
        try:
            with open(sav_file, "rb") as f: data = f.read()
            raw_gvas, _ = decompress_sav_to_gvas(data)
            gvas_file = GvasFile.read(raw_gvas, PALWORLD_TYPE_HINTS, SKP_PALWORLD_CUSTOM_PROPERTIES, allow_nan=True)
            json_data = gvas_file.dump()
            pal_capture_count_list = json_data.get('properties', {}).get('SaveData', {}).get('value', {}).get('RecordData', {}).get('value', {}).get('PalCaptureCount', {}).get('value', [])
            uniques = len(pal_capture_count_list) if pal_capture_count_list else 0
            caught = sum(e.get('value',0) for e in pal_capture_count_list) if pal_capture_count_list else 0
            pal_deck_unlock_flag_list = json_data.get('properties', {}).get('SaveData', {}).get('value', {}).get('RecordData', {}).get('value', {}).get('PaldeckUnlockFlag', {}).get('value', [])
            encounters = max(len(pal_deck_unlock_flag_list) if pal_deck_unlock_flag_list else 0, uniques)
        except: pass
    if os.path.isfile(dps_file):
        dps_tasks.append((uid, pname, dps_file, log_folder))
    return uid, pname, uniques, caught, encounters
def load_save(path=None):
    global current_save_path, loaded_level_json, backup_save_path, srcGuildMapping, player_levels, original_loaded_level_json, base_guild_lookup
    global PLAYER_PAL_COUNTS 
    base_path = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if path is None:
        p = filedialog.askopenfilename(title="Select Level.sav", filetypes=[("SAV","*.sav")])
    else:
        p = path
    if not p: return
    if not p.endswith("Level.sav"):
        messagebox.showerror(t("error.title"), t("error.not_level_sav"))
        return
    d = os.path.dirname(p)
    playerdir = os.path.join(d, "Players")
    if not os.path.isdir(playerdir):
        messagebox.showerror(t("error.title"), t("error.players_folder_missing"))
        return
    print(t("loading.save"))
    current_save_path = d
    backup_save_path = current_save_path
    t0 = time.perf_counter()
    loaded_level_json = sav_to_json(p)
    t1 = time.perf_counter()
    print(t("loading.converted", seconds=f"{t1 - t0:.2f}"))
    build_player_levels()
    all_in_one_tools.loaded_json = loaded_level_json
    data_source = loaded_level_json["properties"]["worldSaveData"]["value"]
    try:
        srcGuildMapping = MappingCacheObject.get(data_source, use_mp=True)
        if srcGuildMapping._worldSaveData.get('GroupSaveDataMap') is None:
            srcGuildMapping.GroupSaveDataMap = {}
    except Exception as e:
        messagebox.showerror(t("error.title"), t("error.guild_mapping_failed", err=e))
        srcGuildMapping = None
    base_guild_lookup = {}
    guild_name_map = {}
    if srcGuildMapping:
        for gid_uuid, gdata in srcGuildMapping.GroupSaveDataMap.items():
            gid = str(gid_uuid)
            guild_name = gdata['value']['RawData']['value'].get('guild_name', "Unnamed Guild")
            guild_name_map[gid.lower()] = guild_name
            for base_id_uuid in gdata['value']['RawData']['value'].get('base_ids', []):
                base_guild_lookup[str(base_id_uuid)] = {"GuildName": guild_name, "GuildID": gid}
    print(t("loading.done"))
    log_folder = os.path.join(base_path, "Scan Save Logger")
    if os.path.exists(log_folder): shutil.rmtree(log_folder)
    os.makedirs(log_folder, exist_ok=True)
    player_pals_count = {}
    count_pals_found(data_source, player_pals_count, log_folder, current_save_path, sav_to_json, guild_name_map)
    PLAYER_PAL_COUNTS = player_pals_count     
    def count_owned_pals(level_json):
        owned_count = {}
        try:
            char_map = level_json["properties"]["worldSaveData"]["value"]["CharacterSaveParameterMap"]["value"]
            for item in char_map:
                try:
                    owner_uid = item["value"]["RawData"]["value"]["object"]["SaveParameter"]["value"]["OwnerPlayerUId"]["value"]
                    if owner_uid:
                        owned_count[owner_uid] = owned_count.get(owner_uid, 0) + 1
                except (KeyError, TypeError): continue
        except (KeyError, TypeError): pass
        return owned_count
    owned_counts = count_owned_pals(loaded_level_json)
    scan_log_path = os.path.join(log_folder, "scan_save.log")
    logger = logging.getLogger('LoadSaveLogger')
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(message)s')
    fh = logging.FileHandler(scan_log_path, encoding='utf-8')
    fh.setFormatter(formatter)
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(formatter)
    logger.addHandler(fh)
    logger.addHandler(ch)
    def format_duration(seconds):
        seconds = int(seconds)
        if seconds < 60: return f"{seconds}s ago"
        m, s = divmod(seconds, 60)
        if m < 60: return f"{m}m {s}s ago"
        h, m = divmod(m, 60)
        if h < 24: return f"{h}h {m}m ago"
        d, h = divmod(h, 24)
        return f"{d}d {h}h ago"
    tick = data_source['GameTimeSaveData']['value']['RealDateTimeTicks']['value']
    total_players = total_caught = total_owned = total_bases = active_guilds = 0
    if srcGuildMapping:
        for gid, gdata in srcGuildMapping.GroupSaveDataMap.items():
            raw_val = gdata['value']['RawData']['value']
            players = raw_val.get('players', [])
            if not players: continue
            active_guilds += 1
            base_ids = raw_val.get('base_ids', [])
            total_bases += len(base_ids)
            guild_name = raw_val.get('guild_name', "Unnamed Guild")
            guild_leader = players[0].get('player_info', {}).get('player_name', "Unknown")
            logger.info("="*60)
            logger.info("")
            logger.info(f"Guild: {guild_name} | Guild Leader: {guild_leader} | Guild ID: {gid}")
            logger.info(f"Base Locations: {len(base_ids)}")
            for i, base_id in enumerate(base_ids, 1):
                basecamp = srcGuildMapping.BaseCampMapping.get(toUUID(base_id))
                if basecamp:
                    translation = basecamp['value']['RawData']['value']['transform']['translation']
                    tx, ty, tz = translation['x'], translation['y'], translation['z']
                    old_c = palworld_coord.sav_to_map(tx, ty, new=False)
                    new_c = palworld_coord.sav_to_map(tx, ty, new=True)
                    logger.info(f"Base {i}: Base ID: {base_id} | Old: {int(old_c[0])}, {int(old_c[1])} | New: {int(new_c[0])}, {int(new_c[1])} | RawData: {tx}, {ty}, {tz}")
            results = [top_process_player(p, playerdir, log_folder) for p in players]
            for uid, pname, uniques, caught, encounters in results:
                level = player_levels.get(str(uid).replace('-', ''), '?')
                owned = owned_counts.get(uid, 0)
                last = next((p.get('player_info', {}).get('last_online_real_time') for p in players if p.get('player_uid')==uid), None)
                lastseen = "Unknown" if last is None else format_duration((tick - int(last))/1e7)
                logger.info(f"Player: {pname} | UID: {uid} | Level: {level} | Caught: {caught} | Owned: {owned} | Encounters: {encounters} | Uniques: {uniques} | Last Online: {lastseen}")
                total_players += 1
                total_caught += caught
                total_owned += owned
            logger.info("")
            logger.info("="*60)
            logger.info("")
    total_worker_dropped = PLAYER_PAL_COUNTS.get("worker_dropped", 0)
    logger.info("="*60)
    logger.info("********** PST_STATS_BEGIN **********")
    logger.info("")
    logger.info(f"Total Players: {total_players}")
    logger.info(f"Total Caught Pals: {total_caught}")
    logger.info(f"Total Overall Pals: {total_owned + total_worker_dropped}")
    logger.info(f"Total Owned Pals: {total_owned}")
    logger.info(f"Total Worker/Dropped Pals: {total_worker_dropped}")
    logger.info(f"Total Active Guilds: {active_guilds}")
    logger.info(f"Total Bases: {total_bases}")
    logger.info("")
    logger.info("********** PST_STATS_END ************")
    logger.info("="*60)
    for h in logger.handlers[:]:
        logger.removeHandler(h)
        h.close()
    refresh_all()
    refresh_stats("Before")
def extract_value(data, key, default_value=''):
    value = data.get(key, default_value)
    if isinstance(value, dict):
        value = value.get('value', default_value)
        if isinstance(value, dict):
            value = value.get('value', default_value)
    return value
def safe_str(s):
    return s.encode('utf-8', 'replace').decode('utf-8')
def sanitize_filename(name):
    return ''.join(c if c.isalnum() or c in (' ', '_', '-', '(', ')') else '_' for c in name)
def count_pals_found(data, player_pals_count, log_folder, current_save_path, sav_to_json, guild_name_map):
    import os,json,logging,shutil
    from collections import defaultdict
    base_dir=os.path.dirname(os.path.abspath(__file__))
    def load_map(fname,key):
        try:
            fp=os.path.join(base_dir,"resources","game_data",fname)
            with open(fp,"r",encoding="utf-8") as f:
                js=json.load(f)
                return {x["asset"].lower():x["name"] for x in js.get(key,[])}
        except:
            return {}
    PALMAP=load_map("paldata.json","pals")
    NPCMAP=load_map("npcdata.json","npcs")
    PASSMAP=load_map("passivedata.json","passives")
    SKILLMAP=load_map("skilldata.json","skills")
    NAMEMAP={**PALMAP,**NPCMAP}
    miss={"Pals":set(),"Passives":set(),"Skills":set()}
    owner_pals_grouped=defaultdict(lambda: defaultdict(list))
    player_containers={}
    owner_nicknames={}
    players_dir=os.path.join(current_save_path,"Players")
    if os.path.exists(players_dir):
        for filename in os.listdir(players_dir):
            if filename.endswith(".sav") and "_dps" not in filename:
                try:
                    p_json=sav_to_json(os.path.join(players_dir,filename))
                    p_prop=p_json.get("properties",{}).get("SaveData",{}).get("value",{})
                    p_uid_raw=filename.replace(".sav","")
                    p_uid=f"{p_uid_raw[0:8]}-{p_uid_raw[8:12]}-{p_uid_raw[12:16]}-{p_uid_raw[16:20]}-{p_uid_raw[20:32]}".lower()
                    p_box=p_prop.get("PalStorageContainerId",{}).get("value",{}).get("ID",{}).get("value")
                    p_party=p_prop.get("OtomoCharacterContainerId",{}).get("value",{}).get("ID",{}).get("value")
                    if p_box and p_party:
                        player_containers[p_uid]={"Party":str(p_party).lower(),"PalBox":str(p_box).lower()}
                except:
                    pass
    cmap=data.get("CharacterSaveParameterMap",{}).get("value",[])
    for itm in cmap:
        try:
            raw_p=itm.get("value",{}).get("RawData",{}).get("value",{}).get("object",{}).get("SaveParameter",{}).get("value",{})
            if "IsPlayer" in raw_p:
                uid=itm.get("key",{}).get("PlayerUId",{}).get("value")
                nn=raw_p.get("NickName",{}).get("value","Unknown")
                if uid: owner_nicknames[str(uid).lower()]=nn
        except:
            pass
    guild_bases=defaultdict(set)
    for item in cmap:
        rawf=item.get("value",{}).get("RawData",{}).get("value",{})
        raw=rawf.get("object",{}).get("SaveParameter",{}).get("value",{})
        if not isinstance(raw,dict) or "IsPlayer" in raw: continue
        inst=item.get("key",{}).get("InstanceId",{}).get("value")
        gid=str(rawf.get("group_id","Unknown")).lower()
        uid_val=raw.get("OwnerPlayerUId",{}).get("value")
        u_str=str(uid_val).lower() if uid_val else "00000000-0000-0000-0000-000000000000"
        is_worker=(u_str=="00000000-0000-0000-0000-000000000000")
        base=str(raw.get("SlotId",{}).get("value",{}).get("ContainerId",{}).get("value",{}).get("ID",{}).get("value")).lower()
        if is_worker: guild_bases[gid].add(base)
        target_id=u_str if not is_worker else f"WORKER_{gid}_{base}"
        if is_worker and target_id not in owner_nicknames: owner_nicknames[target_id]=f"Base_{base}"
        cid=raw.get("CharacterID",{}).get("value","")
        if cid and cid.lower() not in NAMEMAP: miss["Pals"].add(cid)
        name=NAMEMAP.get(cid.lower(),cid)
        lvl=extract_value(raw,"Level",1)
        rk=extract_value(raw,"Rank",1)
        gv=raw.get("Gender",{}).get("value",{}).get("value","")
        ginfo={"EPalGenderType::Male":"Male","EPalGenderType::Female":"Female"}.get(gv,"Unknown")
        p_list=raw.get("PassiveSkillList",{}).get("value",{}).get("values",[])
        for s in p_list:
            if s.lower() not in PASSMAP: miss["Passives"].add(s)
        pskills=[PASSMAP.get(s.lower(),s) for s in p_list]
        e_list=raw.get("EquipWaza",{}).get("value",{}).get("values",[])
        for w in e_list:
            w_short=w.split("::")[-1]
            if w_short.lower() not in SKILLMAP: miss["Skills"].add(w)
        active=[SKILLMAP.get(w.split("::")[-1].lower(),w.split("::")[-1]) for w in e_list]
        m_list=raw.get("MasteredWaza",{}).get("value",{}).get("values",[])
        for w in m_list:
            w_short=w.split("::")[-1]
            if w_short.lower() not in SKILLMAP: miss["Skills"].add(w)
        learned=[SKILLMAP.get(w.split("::")[-1].lower(),w.split("::")[-1]) for w in m_list]
        rh,ra,rd=int(extract_value(raw,"Rank_HP",0))*3,int(extract_value(raw,"Rank_Attack",0))*3,int(extract_value(raw,"Rank_Defence",0))*3
        iv_str=f"HP: {extract_value(raw,'Talent_HP','0')} (+{rh}%), ATK: {extract_value(raw,'Talent_Shot','0')} (+{ra}%), DEF: {extract_value(raw,'Talent_Defense','0')} (+{rd}%)"
        nick=raw.get("NickName",{}).get("value","Unknown")
        dn=f"{name} (Nickname: {nick})" if nick!="Unknown" else name
        info=(f"\n[{dn}]\n"
              f"  Level: {lvl} | Rank: {rk} | Gender: {ginfo}\n"
              f"  IVs:      {iv_str}\n"
              f"  Passives: {', '.join(pskills) if pskills else 'None'}\n"
              f"  Active:   {', '.join(active) if active else 'None'}\n"
              f"  Learned:  {', '.join(learned) if learned else 'None'}\n"
              f"  IDs:      Container: {base} | Instance: {inst} | Guild: {gid}\n")
        lbl="Base Worker"
        if not is_worker and u_str in player_containers:
            if base==player_containers[u_str]["Party"]: lbl="Current Party"
            elif base==player_containers[u_str]["PalBox"]: lbl="PalBox Storage"
        owner_pals_grouped[target_id][lbl].append(info)
        if is_worker: player_pals_count["worker_dropped"]=player_pals_count.get("worker_dropped",0)+1
        else: player_pals_count[u_str]=player_pals_count.get(u_str,0)+1
    if any(miss.values()):
        with open(os.path.join(log_folder, "missing_assets.log"), "w", encoding="utf-8") as f:
            for cat, items in miss.items():
                if items:
                    f.write(f"[{cat}]\n" + "\n".join(sorted(items)) + "\n\n")
    for uid,containers in owner_pals_grouped.items():
        pname=owner_nicknames.get(uid,'Unknown')
        sname=sanitize_filename(pname.encode('utf-8','replace').decode('utf-8'))
        pal_count=sum(len(p) for p in containers.values())
        if uid.startswith("WORKER_"):
            parts=uid.split("_")
            g_id,b_id=parts[1],parts[2]
            b_count=len(guild_bases[g_id])
            g_name=sanitize_filename(guild_name_map.get(g_id,"Unknown Guild"))
            g_dir=os.path.join(log_folder,"Guilds",f"({g_id})_({g_name})_({b_count})")
            os.makedirs(g_dir,exist_ok=True)
            lf=os.path.join(g_dir,f"({b_id})_({pal_count}).log")
        else:
            p_dir=os.path.join(log_folder,"Players")
            os.makedirs(p_dir,exist_ok=True)
            lf=os.path.join(p_dir,f"({uid})_({sname})_({pal_count}).log")
        lname=''.join(c if c.isalnum() or c in ('_','-') else '_' for c in f"lg_{uid}")
        lg=logging.getLogger(lname)
        lg.setLevel(logging.INFO); lg.propagate=False
        if not lg.hasHandlers():
            try:
                h=logging.FileHandler(lf,mode='w',encoding='utf-8',errors='replace')
                h.setFormatter(logging.Formatter('%(message)s'))
                lg.addHandler(h)
            except: continue
        lg.info(f"{pname}'s {pal_count} Pals\n"+"="*40)
        prio=["Current Party","PalBox Storage","Base Worker"]
        sorted_keys=prio+sorted([k for k in containers.keys() if k not in prio])
        for label in sorted_keys:
            if label in containers:
                lg.info(f"\n{label} (Count: {len(containers[label])})\n"+"-"*40)
                for p_block in sorted(containers[label]):
                    lg.info(p_block); lg.info("-" * 20)
    for uid in owner_pals_grouped.keys():
        lg=logging.getLogger(''.join(c if c.isalnum() or c in ('_','-') else '_' for c in f"lg_{uid}"))
        for h in lg.handlers[:]:
            h.flush(); h.close(); lg.removeHandler(h)
def process_dps_save(player_uid, nickname, dps_file_path, log_folder):
    try:
        with open(dps_file_path, "rb") as f:
            data = f.read()
        raw_gvas, _ = decompress_sav_to_gvas(data)
        gvas = GvasFile.read(raw_gvas, PALWORLD_TYPE_HINTS, SKP_PALWORLD_CUSTOM_PROPERTIES, allow_nan=True)
        json_data = gvas.dump()
        values = json_data.get("properties", {}).get("SaveParameterArray", {}).get("value", {}).get("values", [])
        if not values:
            print(t("dps.none_found", file=os.path.basename(dps_file_path)))
            return
        valid_lines = []
        for item in values:
            pal = item.get("SaveParameter", {}).get("value", {})
            cid = pal.get("CharacterID", {}).get("value", "Unknown")
            name = PAL_NAMES.get(cid, cid)
            if name.lower().startswith("boss_"):
                base = PAL_NAMES.get(name[5:], name[5:])
                name = f"Alpha {base.capitalize()}"
            if name in ["Unknown", "None", None]:
                continue
            nick = pal.get("NickName", {}).get("value", "Unknown")
            nickname_str = f", {nick}" if nick != "Unknown" else ""
            lvl = extract_value(pal, "Level", 1)
            rank = extract_value(pal, "Rank", 1)
            gender = {"EPalGenderType::Male":"Male","EPalGenderType::Female":"Female"}.get(pal.get("Gender", {}).get("value", {}).get("value", ""), "Unknown")
            hp_iv = extract_value(pal, "Talent_HP", "0")
            atk_iv = extract_value(pal, "Talent_Shot", "0")
            def_iv = extract_value(pal, "Talent_Defense", "0")
            rank_hp = int(extract_value(pal, "Rank_HP", 0)) * 3
            rank_atk = int(extract_value(pal, "Rank_Attack", 0)) * 3
            rank_def = int(extract_value(pal, "Rank_Defence", 0)) * 3
            rank_craft = int(extract_value(pal, "Rank_CraftSpeed", 0)) * 3
            if lvl == 1 and all(str(v) == "0" for v in [hp_iv, atk_iv, def_iv]) and all(x == 0 for x in [rank_hp, rank_atk, rank_def]):
                continue
            skills = [PAL_PASSIVES.get(pid, {}).get("Name", pid) for pid in pal.get("PassiveSkillList", {}).get("value", {}).get("values", [])]
            skill_str = ", Skills: " + ", ".join(skills) if skills else ""
            talents = f"HP IV: {hp_iv}({rank_hp}%), ATK IV: {atk_iv}({rank_atk}%), DEF IV: {def_iv}({rank_def}%), Work Speed: ({rank_craft}%)"
            valid_lines.append(f"{name}{nickname_str}, Level: {lvl}, Rank: {rank}, Gender: {gender}, {talents}{skill_str}")
        if not valid_lines:
            print(t("dps.none_valid", file=os.path.basename(dps_file_path)))
            return
        log_name = sanitize_filename(nickname.encode("utf-8", "replace").decode("utf-8"))
        log_file = os.path.join(log_folder, f"({log_name})({player_uid})_dps.log")
        logger = logging.getLogger(f"dps_{player_uid}")
        logger.setLevel(logging.INFO)
        logger.propagate = False
        if logger.hasHandlers():
            for h in logger.handlers[:]:
                h.flush()
                h.close()
                logger.removeHandler(h)
        handler = logging.FileHandler(log_file, mode='w', encoding='utf-8', errors='replace')
        handler.setFormatter(logging.Formatter('%(message)s'))
        logger.addHandler(handler)
        header = f"{nickname}'s {len(valid_lines)} DPS Pals"
        logger.info(header)
        logger.info("-" * len(header))
        for line in valid_lines:
            logger.info(line)
        handler.flush()
        handler.close()
        logger.removeHandler(handler)
    except Exception as e:
        print(t("dps.parse_failed", path=dps_file_path, name=nickname, uid=player_uid, err=e))
def save_changes():
    global files_to_delete
    folder = current_save_path
    if not folder:
        messagebox.showerror(t("Error"), t("guild.rebuild.no_save"))
        return
    if not current_save_path or not loaded_level_json: return
    backup_whole_directory(backup_save_path, "Backups/AllinOneTools")
    level_sav_path = os.path.join(current_save_path, "Level.sav")
    json_to_sav(loaded_level_json, level_sav_path)
    players_folder = os.path.join(current_save_path, 'Players')
    for uid in files_to_delete:
        f = os.path.join(players_folder, uid + '.sav')
        f_dps = os.path.join(players_folder, f"{uid}_dps.sav")
        try: os.remove(f)
        except FileNotFoundError: pass
        try: os.remove(f_dps)
        except FileNotFoundError: pass
    files_to_delete.clear()
    window.focus_force()
    messagebox.showinfo(t("Saved"), t("Changes saved and files deleted!"), parent=window)
def format_duration(s):
    d,h = divmod(int(s),86400); hr, m = divmod(h,3600); mm, ss=divmod(m,60)
    return f"{d}d:{hr}h:{mm}m"
def get_players():
    out = []
    wsd = loaded_level_json['properties']['worldSaveData']['value']
    tick = wsd['GameTimeSaveData']['value']['RealDateTimeTicks']['value']
    for g in wsd['GroupSaveDataMap']['value']:
        if g['value']['GroupType']['value']['value'] != 'EPalGroupType::Guild': continue
        gid = str(g['key'])
        players = g['value']['RawData']['value'].get('players', [])
        for p in players:
            uid_raw = p.get('player_uid')
            uid = str(uid_raw) if uid_raw is not None else ''
            name = p.get('player_info', {}).get('player_name', "Unknown")
            last = p.get('player_info', {}).get('last_online_real_time')
            lastseen = "Unknown" if last is None else format_duration((tick - last) / 1e7)
            level = player_levels.get(uid.replace('-', ''), '?') if uid else '?'
            out.append((uid, name, gid, lastseen, level))
    return out
player_levels = {}
def build_player_levels():
    global player_levels
    char_map = loaded_level_json['properties']['worldSaveData']['value'].get('CharacterSaveParameterMap', {}).get('value', [])
    uid_level_map = defaultdict(lambda: '?')
    for entry in char_map:
        try:
            sp = entry['value']['RawData']['value']['object']['SaveParameter']
            if sp['struct_type'] != 'PalIndividualCharacterSaveParameter':
                continue
            sp_val = sp['value']
            if not sp_val.get('IsPlayer', {}).get('value', False):
                continue
            key = entry.get('key', {})
            uid_obj = key.get('PlayerUId', {})
            uid = str(uid_obj.get('value', '') if isinstance(uid_obj, dict) else uid_obj)
            level = extract_value(sp_val, 'Level', '?')
            if uid:
                uid_level_map[uid.replace('-', '')] = level
        except Exception:
            continue
    player_levels = dict(uid_level_map)
def delete_base_camp(base, guild_id, loaded_json):
    base_val = base['value']
    raw_data = base_val.get('RawData', {}).get('value', {})
    base_id = base['key']
    base_group_id = raw_data.get('group_id_belong_to')
    if guild_id and not are_equal_uuids(base_group_id, guild_id): return False
    wsd = loaded_json['properties']['worldSaveData']['value']
    group_data_map = wsd['GroupSaveDataMap']['value']
    group_data = next((g for g in group_data_map if are_equal_uuids(g['key'], guild_id)), None) if guild_id else None
    if group_data:
        group_raw = group_data['value']['RawData']['value']
        base_ids = group_raw.get('base_ids', [])
        mp_points = group_raw.get('map_object_instance_ids_base_camp_points', [])
        if base_id in base_ids:
            idx = base_ids.index(base_id)
            base_ids.pop(idx)
            if mp_points and idx < len(mp_points): mp_points.pop(idx)
    map_objs = wsd['MapObjectSaveData']['value']['values']
    map_obj_ids_to_delete = {m.get('Model', {}).get('value', {}).get('RawData', {}).get('value', {}).get('instance_id')
                             for m in map_objs
                             if m.get('Model', {}).get('value', {}).get('RawData', {}).get('value', {}).get('base_camp_id_belong_to') == base_id}
    if map_obj_ids_to_delete:
        map_objs[:] = [m for m in map_objs if m.get('Model', {}).get('value', {}).get('RawData', {}).get('value', {}).get('instance_id') not in map_obj_ids_to_delete]
    base_list = wsd['BaseCampSaveData']['value']
    base_list[:] = [b for b in base_list if b['key'] != base_id]
    print(t("base.deleted_camp", base_id=base_id, guild_id=(guild_id or "orphaned")))
    return True
def delete_non_base_map_objects():
    global loaded_level_json
    wsd = loaded_level_json['properties']['worldSaveData']['value']
    base_camp_list = wsd['BaseCampSaveData']['value']
    active_base_ids = {b['key'] for b in base_camp_list}
    map_objs = wsd['MapObjectSaveData']['value']['values']
    initial_count = len(map_objs)
    new_map_objs = []
    for m in map_objs:
        raw_data = m.get('Model', {}).get('value', {}).get('RawData', {}).get('value', {})
        base_camp_id = raw_data.get('base_camp_id_belong_to')
        instance_id = raw_data.get('instance_id', 'UNKNOWN_ID')
        object_name = m.get('MapObjectId', {}).get('value', 'UNKNOWN_OBJECT_TYPE')
        print(t("map_obj.checking_id", object_name=object_name, instance_id=instance_id))
        should_keep = False
        if base_camp_id and base_camp_id in active_base_ids:
            should_keep = True
        if should_keep:
            new_map_objs.append(m)
            print(t("map_obj.keeping_base", instance_id=instance_id, object_name=object_name, base_camp_id=base_camp_id))
        else:
            reason = t("map_obj.reason_null_id")
            if base_camp_id and base_camp_id not in active_base_ids:
                reason = t("map_obj.reason_orphaned", base_camp_id=base_camp_id)
            print(t("map_obj.deleting_orphan", instance_id=instance_id, object_name=object_name, reason=reason))
    deleted_count = initial_count - len(new_map_objs)
    map_objs[:] = new_map_objs
    print(t("map_obj.deleted_summary", deleted_count=deleted_count, remaining_count=len(map_objs)))
    refresh_all()
    refresh_stats("After")
    return deleted_count
def delete_selected_guild():
    global files_to_delete
    folder = current_save_path
    if not folder:
        messagebox.showerror(t("Error"), t("guild.rebuild.no_save"))
        return
    sel = guild_tree.selection()
    src = "guild"
    if not sel:
        sel = player_tree.selection()
        src = "player"
    if not sel:
        messagebox.showerror(t("Error"), t("Select guild"))
        return
    vals = guild_tree.item(sel[0])['values'] if src == "guild" else player_tree.item(sel[0])['values']
    raw_gid = vals[1] if src == "guild" else vals[6]
    gid = raw_gid.replace('-', '')
    if any(gid == ex.replace('-', '') for ex in exclusions.get("guilds", [])):
        print(t("guild.excluded", gid=raw_gid))
        return
    wsd = loaded_level_json['properties']['worldSaveData']['value']
    for b in wsd.get('BaseCampSaveData', {}).get('value', []):
        base_gid_raw = as_uuid(b['value']['RawData']['value'].get('group_id_belong_to'))
        base_gid = base_gid_raw.replace('-', '')
        base_id_raw = as_uuid(b['key'])
        base_id = base_id_raw.replace('-', '')
        if base_gid == gid and any(base_id == ex.replace('-', '') for ex in exclusions.get("bases", [])):
            print(t("guild.excluded_with_base", gid=raw_gid, base_id=base_id_raw))
            return
    deleted_uids = set()
    group_data_list = wsd.get('GroupSaveDataMap', {}).get('value', [])
    for g in group_data_list:
        g_key_raw = str(g['key'])
        g_key = g_key_raw.replace('-', '')
        if g_key == gid:
            for p in g['value']['RawData']['value'].get('players', []):
                pid_raw = str(p.get('player_uid', ''))
                pid = pid_raw.replace('-', '')
                if any(pid == ex.replace('-', '') for ex in exclusions.get("players", [])):
                    continue
                deleted_uids.add(pid)
            group_data_list.remove(g)
            break
    if deleted_uids:
        files_to_delete.update(deleted_uids)
        delete_player_pals(wsd, deleted_uids)
    char_map = wsd.get('CharacterSaveParameterMap', {}).get('value', [])
    char_map[:] = [entry for entry in char_map if str(entry.get('key', {}).get('PlayerUId', {}).get('value', '')).replace('-', '') not in deleted_uids and str(entry.get('value', {}).get('RawData', {}).get('value', {}).get('object', {}).get('SaveParameter', {}).get('value', {}).get('OwnerPlayerUId', {}).get('value', '')).replace('-', '') not in deleted_uids]
    for b in wsd.get('BaseCampSaveData', {}).get('value', [])[:]:
        base_gid_raw = as_uuid(b['value']['RawData']['value'].get('group_id_belong_to'))
        if base_gid_raw.replace('-', '') == gid:
            delete_base_camp(b, gid, loaded_level_json)
    delete_orphaned_bases()
    refresh_all()
    refresh_stats("After")
    messagebox.showinfo(t("Marked"), t("guild.marked_for_deletion", gid=raw_gid, count=len(deleted_uids)))
def delete_selected_base():
    folder = current_save_path
    if not folder:
        messagebox.showerror(t("Error"), t("guild.rebuild.no_save"))
        return
    sel = base_tree.selection()
    if not sel:
        messagebox.showerror(t("Error"), t("Select base"))
        return
    bid = base_tree.item(sel[0])['values'][0]
    if any(bid.replace('-', '') == ex.replace('-', '') for ex in exclusions.get("bases", [])):
        print(t("base.excluded", bid=bid))
        return
    for b in loaded_level_json['properties']['worldSaveData']['value']['BaseCampSaveData']['value'][:]:
        if str(b['key']) == bid:
            delete_base_camp(b, b['value']['RawData']['value'].get('group_id_belong_to'), loaded_level_json)
            break
    delete_orphaned_bases()
    refresh_all()
    refresh_stats("After")
    messagebox.showinfo(t("Deleted"), t("Base deleted"))
def delete_selected_player():
    global files_to_delete
    folder = current_save_path
    if not folder:
        messagebox.showerror(t("Error"), t("guild.rebuild.no_save"))
        return
    sel = player_tree.selection()
    if not sel:
        messagebox.showerror(t("Error"), t("Select player"))
        return
    raw_uid = player_tree.item(sel[0])['values'][4]
    uid = raw_uid.replace('-', '')
    wsd = loaded_level_json['properties']['worldSaveData']['value']
    group_data = wsd['GroupSaveDataMap']['value']
    deleted = False
    for group in group_data[:]:
        if group['value']['GroupType']['value']['value'] != 'EPalGroupType::Guild': continue
        raw = group['value']['RawData']['value']
        players = raw.get('players', [])
        new_players = []
        for p in players:
            pid_raw = str(p.get('player_uid', ''))
            pid = pid_raw.replace('-', '')
            if pid == uid:
                if any(pid == ex.replace('-', '') for ex in exclusions.get("players", [])):
                    print(t("player.excluded", pid=pid_raw))
                    new_players.append(p)
                    continue
                files_to_delete.add(pid)
                deleted = True
            else:
                new_players.append(p)
        if len(new_players) != len(players):
            raw['players'] = new_players
            keep_uids = {str(p.get('player_uid', '')).replace('-', '') for p in new_players}
            admin_uid_raw = str(raw.get('admin_player_uid', ''))
            admin_uid = admin_uid_raw.replace('-', '')
            if not new_players:
                gid = group['key']
                for b in wsd.get('BaseCampSaveData', {}).get('value', [])[:]:
                    if are_equal_uuids(b['value']['RawData']['value'].get('group_id_belong_to'), gid):
                        delete_base_camp(b, gid, loaded_level_json)
                group_data.remove(group)
            elif admin_uid not in keep_uids:
                raw['admin_player_uid'] = new_players[0]['player_uid']
    if deleted:
        char_map = wsd.get('CharacterSaveParameterMap', {}).get('value', [])
        char_map[:] = [entry for entry in char_map
                       if str(entry.get('key', {}).get('PlayerUId', {}).get('value', '')).replace('-', '') != uid
                       and str(entry.get('value', {}).get('RawData', {}).get('value', {})
                               .get('object', {}).get('SaveParameter', {}).get('value', {})
                               .get('OwnerPlayerUId', {}).get('value', '')).replace('-', '') != uid]
        refresh_all()
        refresh_stats("After")
        messagebox.showinfo(t("Marked"), t("player.marked_for_deletion", uid=raw_uid))
    else:
        messagebox.showinfo(t("Info"), t("player.not_found_or_deleted"))
def delete_selected_guild_member():
    global files_to_delete
    folder = current_save_path
    if not folder:
        messagebox.showerror(t("Error"), t("guild.rebuild.no_save"))
        return
    sel = guild_members_tree.selection()
    if not sel:
        messagebox.showerror(t("Error"), t("Select player"))
        return
    uid = guild_members_tree.item(sel[0])['values'][4].replace('-', '')
    wsd = loaded_level_json['properties']['worldSaveData']['value']
    group_data = wsd['GroupSaveDataMap']['value']
    deleted = False
    for group in group_data[:]:
        if group['value']['GroupType']['value']['value'] != 'EPalGroupType::Guild': continue
        raw = group['value']['RawData']['value']
        players = raw.get('players', [])
        new_players = []
        for p in players:
            pid_raw = p.get('player_uid', '')
            pid = str(pid_raw).replace('-', '')
            if pid == uid:
                if any(pid == ex.replace('-', '') for ex in exclusions.get("players", [])):
                    print(f"Player {pid_raw} is excluded from deletion - skipping...")
                    new_players.append(p)
                    continue
                files_to_delete.add(pid)
                deleted = True
            else:
                new_players.append(p)
        if len(new_players) != len(players):
            raw['players'] = new_players
            keep_uids = {str(p.get('player_uid', '')).replace('-', '') for p in new_players}
            admin_uid = str(raw.get('admin_player_uid', '')).replace('-', '')
            if not new_players:
                gid = group['key']
                for b in wsd.get('BaseCampSaveData', {}).get('value', [])[:]:
                    if are_equal_uuids(b['value']['RawData']['value'].get('group_id_belong_to'), gid):
                        delete_base_camp(b, gid, loaded_level_json)
                group_data.remove(group)
            elif admin_uid not in keep_uids:
                raw['admin_player_uid'] = new_players[0]['player_uid']
    if deleted:
        char_map = wsd.get('CharacterSaveParameterMap', {}).get('value', [])
        char_map[:] = [entry for entry in char_map
                       if str(entry.get('key', {}).get('PlayerUId', {}).get('value', '')).replace('-', '') != uid
                       and str(entry.get('value', {}).get('RawData', {}).get('value', {})
                               .get('object', {}).get('SaveParameter', {}).get('value', {})
                               .get('OwnerPlayerUId', {}).get('value', '')).replace('-', '') != uid]
        refresh_all()
        refresh_stats("After")
        messagebox.showinfo(t("Marked"), t("player.marked"))
    else:
        messagebox.showinfo(t("Info"), t("player.not_found_or_deleted"))
def delete_player_pals(wsd, to_delete_uids):
    char_save_map = wsd.get("CharacterSaveParameterMap", {}).get("value", [])
    removed_pals = 0
    uids_set = {uid.replace('-', '') for uid in to_delete_uids if uid}
    new_map = []
    for entry in char_save_map:
        try:
            val = entry['value']['RawData']['value']['object']['SaveParameter']['value']
            struct_type = entry['value']['RawData']['value']['object']['SaveParameter']['struct_type']
            owner_uid = val.get('OwnerPlayerUId', {}).get('value')
            if owner_uid:
                owner_uid = str(owner_uid).replace('-', '')
            if struct_type in ('PalIndividualCharacterSaveParameter', 'PlayerCharacterSaveParameter') and owner_uid in uids_set:
                removed_pals += 1
                continue
        except:
            pass
        new_map.append(entry)
    wsd["CharacterSaveParameterMap"]["value"] = new_map
    return removed_pals
def delete_inactive_bases():
    folder = current_save_path
    if not folder:
        messagebox.showerror(t("Error"), t("guild.rebuild.no_save"))
        return
    d = ask_string_with_icon("Delete Inactive Bases", "Delete bases where ALL players inactive for how many days?", ICON_PATH, mode="number")
    if d is None: return
    wsd = loaded_level_json['properties']['worldSaveData']['value']
    tick = wsd['GameTimeSaveData']['value']['RealDateTimeTicks']['value']
    to_clear = []
    for g in wsd['GroupSaveDataMap']['value']:
        if g['value']['GroupType']['value']['value'] != 'EPalGroupType::Guild': continue
        gid = as_uuid(g['key'])
        allold = True
        for p in g['value']['RawData']['value'].get('players', []):
            pid = str(p.get('player_uid', '')).replace('-', '')
            last_online = p.get('player_info', {}).get('last_online_real_time')
            if last_online is None or ((tick - last_online) / 1e7) / 86400 < d:
                allold = False
                break
        if allold:
            to_clear.append(gid)
    cnt = 0
    for b in wsd['BaseCampSaveData']['value'][:]:
        gid = as_uuid(b['value']['RawData']['value'].get('group_id_belong_to'))
        base_id = as_uuid(b['key'])
        if any(base_id == ex.replace('-', '') for ex in exclusions.get("bases", [])):
            print(f"Base {base_id} is excluded from deletion - skipping...")
            continue
        if gid in to_clear:
            if delete_base_camp(b, gid, loaded_level_json): cnt += 1
    delete_orphaned_bases()
    refresh_all()
    refresh_stats("After")
    messagebox.showinfo(t("Done"), t("bases.deleted_count", count=cnt))
def delete_orphaned_bases():
    folder = current_save_path
    if not folder: return print(t("guild.rebuild.no_save"))
    wsd = loaded_level_json['properties']['worldSaveData']['value']
    valid_guild_ids = {
        as_uuid(g['key']) for g in wsd.get('GroupSaveDataMap', {}).get('value', [])
        if g['value']['GroupType']['value']['value'] == 'EPalGroupType::Guild'
    }
    base_list = wsd.get('BaseCampSaveData', {}).get('value', [])[:]
    cnt = 0
    for b in base_list:
        raw = b['value']['RawData']['value']
        gid_raw = raw.get('group_id_belong_to')
        gid = as_uuid(gid_raw) if gid_raw else None
        if not gid or gid not in valid_guild_ids:
            if delete_base_camp(b, gid, loaded_level_json): cnt += 1
    refresh_all()
    refresh_stats("After")
    if cnt > 0: print(t("bases.orphaned_deleted", count=cnt))
def is_valid_level(level):
    try:
        return int(level) > 0
    except:
        return False
def delete_empty_guilds():
    folder = current_save_path
    if not folder:
        messagebox.showerror(t("Error"), t("guild.rebuild.no_save"))
        return
    build_player_levels()
    wsd = loaded_level_json['properties']['worldSaveData']['value']
    group_data = wsd['GroupSaveDataMap']['value']
    to_delete = []
    for g in group_data:
        if g['value']['GroupType']['value']['value'] != 'EPalGroupType::Guild': continue
        players = g['value']['RawData']['value'].get('players', [])
        if not players:
            to_delete.append(g)
            continue
        all_invalid = True
        for p in players:
            if isinstance(p, dict) and 'player_uid' in p:
                uid_obj = p['player_uid']
                if hasattr(uid_obj, 'hex'):
                    uid = uid_obj.hex
                else:
                    uid = str(uid_obj)
            else:
                uid = str(p)
            uid = uid.replace('-', '')
            level = player_levels.get(uid, None)
            if is_valid_level(level):
                all_invalid = False
                break
        if all_invalid:
            to_delete.append(g)
    for g in to_delete:
        gid = as_uuid(g['key'])
        bases = wsd.get('BaseCampSaveData', {}).get('value', [])[:]
        for b in bases:
            if are_equal_uuids(b['value']['RawData']['value'].get('group_id_belong_to'), gid):
                delete_base_camp(b, gid, loaded_level_json)
        group_data.remove(g)
    delete_orphaned_bases()
    refresh_all()
    refresh_stats("After")
    messagebox.showinfo(t("Done"), t("guilds.deleted_count", count=len(to_delete)))
def delete_inactive_players_button():
    folder = current_save_path
    if not folder:
        messagebox.showerror(t("Error"), t("guild.rebuild.no_save"))
        return
    d = ask_string_with_icon("Delete Inactive Players", "Delete players inactive for days?", ICON_PATH, mode="number")
    if d is None: return
    delete_inactive_players(folder, inactive_days=d)
def delete_unreferenced_data():
    global files_to_delete
    folder_path = current_save_path
    if not folder_path:
        messagebox.showerror(t("Error"), t("guild.rebuild.no_save"))
        return
    players_folder = os.path.join(folder_path, 'Players')
    if not os.path.exists(players_folder):
        print(t("players.folder_not_found"))
        return
    def normalize_uid(uid):
        if isinstance(uid, dict): uid = uid.get('value', '')
        return str(uid).replace('-', '').lower()
    def is_broken_mapobject(obj):
        bp = obj.get('Model', {}).get('value', {}).get('BuildProcess', {}).get('value', {}).get('RawData', {}).get('value', {})
        return bp.get('state') == 0
    def is_dropped_item(obj):
        return obj.get('ConcreteModel', {}).get('value', {}).get('RawData', {}).get('value', {}).get('concrete_model_type') == "PalMapObjectDropItemModel"
    def count_mapobject_ids(wsd):
        total = 0
        map_objects = wsd.get('MapObjectSaveData', {}).get('value', {}).get('values', [])
        for obj in map_objects:
            if "MapObjectId" in obj:
                total += 1
        return total
    wsd = loaded_level_json['properties']['worldSaveData']['value']
    group_data_list = wsd.get('GroupSaveDataMap', {}).get('value', [])
    char_map = wsd.get('CharacterSaveParameterMap', {}).get('value', [])
    char_uids = set()
    for entry in char_map:
        uid_raw = entry.get('key', {}).get('PlayerUId')
        uid = normalize_uid(uid_raw)
        owner_uid_raw = entry.get('value', {}).get('RawData', {}).get('value', {}).get('object', {}).get('SaveParameter', {}).get('value', {}).get('OwnerPlayerUId')
        owner_uid = normalize_uid(owner_uid_raw)
        if uid: char_uids.add(uid)
        if owner_uid: char_uids.add(owner_uid)
    unreferenced_uids, invalid_uids, removed_guilds = [], [], 0
    for group in group_data_list[:]:
        if group['value']['GroupType']['value']['value'] != 'EPalGroupType::Guild': continue
        raw = group['value']['RawData']['value']
        players = raw.get('players', [])
        valid_players = []
        all_invalid = True
        for p in players:
            pid_raw = p.get('player_uid')
            pid = normalize_uid(pid_raw)
            if pid not in char_uids:
                name = p.get('player_info', {}).get('player_name', 'Unknown')
                print(t("player.removing_unreferenced", name=name, pid=pid_raw))
                unreferenced_uids.append(pid)
                continue
            level = player_levels.get(pid, None)
            if is_valid_level(level):
                all_invalid = False
                valid_players.append(p)
            else:
                name = p.get('player_info', {}).get('player_name', 'Unknown')
                print(t("player.removing_invalid", name=name, pid=pid_raw))
                invalid_uids.append(pid)
        if not valid_players or all_invalid:
            gid_raw = group['key']
            gid = normalize_uid(gid_raw)
            for b in wsd.get('BaseCampSaveData', {}).get('value', [])[:]:
                base_gid_raw = b['value']['RawData']['value'].get('group_id_belong_to')
                base_gid = normalize_uid(base_gid_raw)
                if base_gid == gid:
                    delete_base_camp(b, gid_raw, loaded_level_json)
            group_data_list.remove(group)
            removed_guilds += 1
            print(t("guild.removed_empty_or_invalid", gid=gid_raw))
            continue
        raw['players'] = valid_players
        admin_uid_raw = raw.get('admin_player_uid')
        admin_uid = normalize_uid(admin_uid_raw)
        keep_uids = {normalize_uid(p.get('player_uid')) for p in valid_players}
        if admin_uid not in keep_uids:
            raw['admin_player_uid'] = valid_players[0]['player_uid']
            print(t("group.admin_reassigned", gid=group["key"], admin=raw["admin_player_uid"]))
    char_map[:] = [entry for entry in char_map if normalize_uid(entry.get('key', {}).get('PlayerUId')) not in unreferenced_uids + invalid_uids and normalize_uid(entry.get('value', {}).get('RawData', {}).get('value', {}).get('object', {}).get('SaveParameter', {}).get('value', {}).get('OwnerPlayerUId')) not in unreferenced_uids + invalid_uids]
    all_removed_uids = set(unreferenced_uids + invalid_uids)
    files_to_delete.update(all_removed_uids)
    removed_pals = delete_player_pals(wsd, all_removed_uids)
    map_objects_wrapper = wsd.get('MapObjectSaveData', {}).get('value', {})
    map_objects = map_objects_wrapper.get('values', [])
    broken_ids, dropped_ids = [], []
    new_map_objects = []
    for obj in map_objects:
        if is_broken_mapobject(obj):
            instance_id = obj.get('Model', {}).get('value', {}).get('RawData', {}).get('value', {}).get('instance_id')
            broken_ids.append(instance_id)
        elif is_dropped_item(obj):
            instance_id = obj.get('ConcreteModel', {}).get('value', {}).get('RawData', {}).get('value', {}).get('instance_id')
            dropped_ids.append(instance_id)
        else:
            new_map_objects.append(obj)
    map_objects_wrapper['values'] = new_map_objects
    removed_broken, removed_drops = len(broken_ids), len(dropped_ids)
    for bid in broken_ids: print(t("mapobject.deleted_broken", id=bid))
    for did in dropped_ids: print(t("item.deleted_dropped", id=did))
    delete_orphaned_bases()
    build_player_levels()
    refresh_all()
    refresh_stats("After")
    mapobject_count = count_mapobject_ids(wsd)
    result_msg=t(
        "cleanup.summary",
        removed_players=len(all_removed_uids),
        unref=len(unreferenced_uids),
        invalid=len(invalid_uids),
        pals=removed_pals,
        guilds=removed_guilds,
        broken=removed_broken,
        drops=removed_drops,
        mapobjects=mapobject_count
    )
    print(result_msg)
    messagebox.showinfo(t("Done"), result_msg)
def delete_inactive_players(folder_path, inactive_days=30):
    global files_to_delete
    players_folder = os.path.join(folder_path, 'Players')
    if not os.path.exists(players_folder): return
    build_player_levels()
    wsd = loaded_level_json['properties']['worldSaveData']['value']
    tick_now = wsd['GameTimeSaveData']['value']['RealDateTimeTicks']['value']
    group_data_list = wsd['GroupSaveDataMap']['value']
    deleted_info = []
    to_delete_uids = set()
    total_players_before = sum(
        len(g['value']['RawData']['value'].get('players', []))
        for g in group_data_list if g['value']['GroupType']['value']['value'] == 'EPalGroupType::Guild'
    )
    for group in group_data_list[:]:
        if group['value']['GroupType']['value']['value'] != 'EPalGroupType::Guild': continue
        raw = group['value']['RawData']['value']
        original_players = raw.get('players', [])
        keep_players = []
        admin_uid = str(raw.get('admin_player_uid', '')).replace('-', '')
        for player in original_players:
            uid_obj = player.get('player_uid', '')
            uid = str(uid_obj.get('value', '') if isinstance(uid_obj, dict) else uid_obj).replace('-', '')
            if any(uid == ex.replace('-', '') for ex in exclusions.get("players", [])):
                print(f"Player {uid} is excluded from deletion - skipping...")
                keep_players.append(player)
                continue
            player_name = player.get('player_info', {}).get('player_name', 'Unknown')
            last_online = player.get('player_info', {}).get('last_online_real_time')
            level = player_levels.get(uid)
            inactive = last_online is not None and ((tick_now - last_online) / 864000000000) >= inactive_days
            if inactive or not is_valid_level(level):
                reason = "Inactive" if inactive else "Invalid level"
                extra = f" - Inactive for {format_duration((tick_now - last_online)/1e7)}" if inactive and last_online else ""
                deleted_info.append(f"{player_name} ({uid}) - {reason}{extra}")
                to_delete_uids.add(uid)
            else:
                keep_players.append(player)
        if len(keep_players) != len(original_players):
            raw['players'] = keep_players
            keep_uids = {str(p.get('player_uid', '')).replace('-', '') for p in keep_players}
            if not keep_players:
                gid = group['key']
                base_camps = wsd.get('BaseCampSaveData', {}).get('value', [])
                for b in base_camps[:]:
                    if are_equal_uuids(b['value']['RawData']['value'].get('group_id_belong_to'), gid):
                        delete_base_camp(b, gid, loaded_level_json)
                group_data_list.remove(group)
            elif admin_uid not in keep_uids:
                raw['admin_player_uid'] = keep_players[0]['player_uid']
    if to_delete_uids:
        files_to_delete.update(to_delete_uids)
        removed_pals = delete_player_pals(wsd, to_delete_uids)
        char_map = wsd.get('CharacterSaveParameterMap', {}).get('value', [])
        char_map[:] = [entry for entry in char_map
                       if str(entry.get('key', {}).get('PlayerUId', {}).get('value', '')).replace('-', '') not in to_delete_uids
                       and str(entry.get('value', {}).get('RawData', {}).get('value', {})
                               .get('object', {}).get('SaveParameter', {}).get('value', {})
                               .get('OwnerPlayerUId', {}).get('value', '')).replace('-', '') not in to_delete_uids]
        delete_orphaned_bases()
        refresh_all()
        refresh_stats("After")
        total_players_after = sum(
            len(g['value']['RawData']['value'].get('players', []))
            for g in group_data_list if g['value']['GroupType']['value']['value'] == 'EPalGroupType::Guild'
        )
        result_msg=t(
            "cleanup.preview_summary",
            before=total_players_before,
            marked=len(deleted_info),
            after=total_players_after,
            pals=removed_pals
        )
        print(result_msg)
        messagebox.showinfo(t("Success"), result_msg)
    else:
        messagebox.showinfo(t("Info"), t("cleanup.no_players_found"))
def delete_duplicated_players():
    global files_to_delete
    folder = current_save_path
    if not folder:
        messagebox.showerror(t("Error"), t("guild.rebuild.no_save"))
        return
    wsd = loaded_level_json['properties']['worldSaveData']['value']
    tick_now = wsd['GameTimeSaveData']['value']['RealDateTimeTicks']['value']
    group_data_list = wsd['GroupSaveDataMap']['value']
    uid_to_player = {}
    uid_to_group = {}
    deleted_players = []
    format_duration = lambda ticks: f"{int(ticks / 864000000000)}d:{int((ticks % 864000000000) / 36000000000)}h:{int((ticks % 36000000000) / 600000000)}m ago"
    for group in group_data_list:
        if group['value']['GroupType']['value']['value'] != 'EPalGroupType::Guild': continue
        raw = group['value']['RawData']['value']
        players = raw.get('players', [])
        filtered_players = []
        for player in players:
            uid_raw = player.get('player_uid', '')
            uid = str(uid_raw.get('value', '') if isinstance(uid_raw, dict) else uid_raw).replace('-', '')
            last_online = player.get('player_info', {}).get('last_online_real_time') or 0
            player_name = player.get('player_info', {}).get('player_name', 'Unknown')
            days_inactive = (tick_now - last_online) / 864000000000 if last_online else float('inf')
            if uid in uid_to_player:
                prev = uid_to_player[uid]
                prev_group = uid_to_group[uid]
                prev_lo = prev.get('player_info', {}).get('last_online_real_time') or 0
                prev_days_inactive = (tick_now - prev_lo) / 864000000000 if prev_lo else float('inf')
                prev_name = prev.get('player_info', {}).get('player_name', 'Unknown')
                if days_inactive > prev_days_inactive:
                    deleted_players.append({
                        'deleted_uid': uid,
                        'deleted_name': player_name,
                        'deleted_gid': group['key'],
                        'deleted_last_online': last_online,
                        'kept_uid': uid,
                        'kept_name': prev_name,
                        'kept_gid': prev_group['key'],
                        'kept_last_online': prev_lo
                    })
                    continue
                else:
                    prev_group['value']['RawData']['value']['players'] = [
                        p for p in prev_group['value']['RawData']['value'].get('players', [])
                        if str(p.get('player_uid', '')).replace('-', '') != uid
                    ]
                    deleted_players.append({
                        'deleted_uid': uid,
                        'deleted_name': prev_name,
                        'deleted_gid': prev_group['key'],
                        'deleted_last_online': prev_lo,
                        'kept_uid': uid,
                        'kept_name': player_name,
                        'kept_gid': group['key'],
                        'kept_last_online': last_online
                    })
            uid_to_player[uid] = player
            uid_to_group[uid] = group
            filtered_players.append(player)
        raw['players'] = filtered_players
    deleted_uids = {d['deleted_uid'] for d in deleted_players}
    if deleted_uids:
        files_to_delete.update(deleted_uids)
        delete_player_pals(wsd, deleted_uids)
    valid_uids = {
        str(p.get('player_uid', '')).replace('-', '')
        for g in wsd['GroupSaveDataMap']['value']
        if g['value']['GroupType']['value']['value'] == 'EPalGroupType::Guild'
        for p in g['value']['RawData']['value'].get('players', [])
    }
    clean_character_save_parameter_map(wsd, valid_uids)
    delete_orphaned_bases()
    refresh_all()
    refresh_stats("After")
    for d in deleted_players:
        print(t(
            "players.duplicate.kept",
            uid=d["kept_uid"],
            name=d["kept_name"],
            gid=d["kept_gid"],
            last_online=format_duration(tick_now - d["kept_last_online"])
        ))
        print(t(
            "players.duplicate.deleted",
            uid=d["deleted_uid"],
            name=d["deleted_name"],
            gid=d["deleted_gid"],
            last_online=format_duration(tick_now - d["deleted_last_online"])
        ) + "\n")
    print(t("players.duplicate.marked", count=len(deleted_players)))
def refresh_all():
    global guild_tree, base_tree, player_tree, loaded_level_json, PLAYER_PAL_COUNTS, PLAYER_DETAILS_CACHE, guild_result, base_result, player_result, base_guild_lookup
    guild_tree.delete(*guild_tree.get_children())
    base_tree.delete(*base_tree.get_children())
    player_tree.delete(*player_tree.get_children())
    guild_result.configure(text=t("deletion.selected_guild", name="N/A"))
    base_result.configure(text=t("deletion.selected_base", id="N/A"))
    player_result.configure(text=t("deletion.selected_player", name="N/A"))
    if 'PLAYER_DETAILS_CACHE' not in globals():
        globals()['PLAYER_DETAILS_CACHE'] = {}
    PLAYER_DETAILS_CACHE = {}
    wsd = loaded_level_json['properties']['worldSaveData']['value']
    for g in wsd['GroupSaveDataMap']['value']:
        if g['value']['GroupType']['value']['value'] == 'EPalGroupType::Guild':
            name = g['value']['RawData']['value'].get('guild_name', "Unknown")
            gid = as_uuid(g['key'])
            guild_tree.insert("", "end", values=(name, gid))
    base_list = wsd.get('BaseCampSaveData', {}).get('value', [])
    for b in base_list:
        base_id = as_uuid(b['key'])
        info = base_guild_lookup.get(base_id, {"GuildName": "No Guild", "GuildID": "N/A"})
        guild_name = info["GuildName"]
        guild_id = info["GuildID"]
        base_tree.insert("", "end", values=(base_id, guild_id, guild_name))
    used = set()
    for uid, name, gid, seen, level in get_players():
        stripped_uid = uid.replace('-', '').lower()
        PLAYER_DETAILS_CACHE[stripped_uid] = {
            'level': level,
            'seen': seen,
            'name': name,
            'uid_full': uid,
            'gid': gid
        }
        iid = uid
        c = 1
        while iid in used:
            iid = f"{uid}_{c}"
            c += 1
        used.add(iid)
        pal_count = PLAYER_PAL_COUNTS.get(uid, 0)
        guild_name = get_guild_name_by_id(gid)
        player_tree.insert("", "end", iid=iid, values=(name, seen, level, pal_count, uid, guild_name, gid))
def treeview_sort_column(treeview, col, reverse):
    l = [(treeview.set(k, col), k) for k in treeview.get_children('')]
    try:
        l.sort(key=lambda t: int(t[0]) if t[0].isdigit() else t[0], reverse=reverse)
    except Exception:
        l.sort(key=lambda t: t[0], reverse=reverse)    
    for index, (val, k) in enumerate(l):
        treeview.move(k, '', index)    
    treeview.heading(col, command=lambda: treeview_sort_column(treeview, col, not reverse))
def on_guild_search(q=None):
    if q is None:
        q = guild_search_var.get()
    q = q.lower()
    guild_tree.delete(*guild_tree.get_children())
    for g in loaded_level_json['properties']['worldSaveData']['value']['GroupSaveDataMap']['value']:
        if g['value']['GroupType']['value']['value'] != 'EPalGroupType::Guild': continue
        name = g['value']['RawData']['value'].get('guild_name', 'Unknown')
        gid = as_uuid(g['key'])
        if q in name.lower() or q in gid.lower():
            guild_tree.insert("", "end", values=(name, gid))
def on_base_search(q=None):
    global base_tree, base_search_var, base_guild_lookup, guild_tree, loaded_level_json
    if q is None:
        q = base_search_var.get()
    q = q.lower()
    selected_gid = None
    selected_items = guild_tree.selection()
    if selected_items:
        selected_gid = guild_tree.item(selected_items[0], 'values')[1]
    base_tree.delete(*base_tree.get_children())
    if 'base_guild_lookup' not in globals() or not globals().get('base_guild_lookup'):
        return
    wsd = loaded_level_json['properties']['worldSaveData']['value']
    current_base_ids = {as_uuid(b['key']) for b in wsd.get('BaseCampSaveData', {}).get('value', [])}
    for base_id, info in base_guild_lookup.items():
        if base_id not in current_base_ids:
            continue
        guild_name = info["GuildName"]
        guild_id = info["GuildID"]
        if selected_gid is not None and guild_id != selected_gid:
            continue
        if q in base_id.lower() or q in guild_name.lower() or q in guild_id.lower():
            base_tree.insert("", "end", values=(base_id, guild_id, guild_name))
def get_guild_name_by_id(target_gid):
    global loaded_level_json
    if not loaded_level_json:return "Unknown Guild"
    for g in loaded_level_json['properties']['worldSaveData']['value']['GroupSaveDataMap']['value']:
        current_gid=as_uuid(g['key'])
        if g['value']['GroupType']['value']['value']=='EPalGroupType::Guild' and current_gid==target_gid:
            return g['value']['RawData']['value'].get('guild_name',"Unnamed Guild")
    return "No Guild"
def on_player_search(q=None):
    global player_tree, player_search_var, PLAYER_PAL_COUNTS
    if q is None:
        q = player_search_var.get()
    q = q.lower()
    player_tree.delete(*player_tree.get_children())
    for uid, name, gid, seen, level in get_players():
        pal_count = PLAYER_PAL_COUNTS.get(uid, 0)
        guild_name = get_guild_name_by_id(gid)
        if any(q in str(c).lower() for c in (uid, name, gid, seen, level, pal_count, guild_name)):
            player_tree.insert("", "end", values=(name, seen, level, pal_count, uid, guild_name, gid))
def on_guild_select(evt):
    global base_tree, guild_tree, guild_members_tree, loaded_level_json, player_levels, base_guild_lookup, base_search_var, PLAYER_PAL_COUNTS, PLAYER_DETAILS_CACHE
    sel = guild_tree.selection()
    base_tree.delete(*base_tree.get_children())
    guild_members_tree.delete(*guild_members_tree.get_children())
    if not globals().get('base_guild_lookup'):
        return
    if not sel:
        guild_result.configure(text=f"{t('ui.selected.guild')}: {t('ui.none')}")
        base_search_var.set("")
        for base_id, info in base_guild_lookup.items():
            base_tree.insert("", "end", values=(base_id, info["GuildID"], info["GuildName"]))
        return
    name, gid = guild_tree.item(sel[0])['values']
    guild_result.configure(text=f"{t('ui.selected.guild')}: {name} ({gid})")
    for base_id, info in base_guild_lookup.items():
        if info["GuildID"] == gid:
            base_tree.insert("", "end", values=(base_id, info["GuildID"], info["GuildName"]))
    for g in loaded_level_json['properties']['worldSaveData']['value']['GroupSaveDataMap']['value']:
        if are_equal_uuids(g['key'], gid):
            raw = g['value'].get('RawData', {}).get('value', {})
            players = raw.get('players', [])
            for p in players:
                p_name = p.get('player_info', {}).get('player_name', 'Unknown')
                p_uid = str(p.get('player_uid', ''))
                p_uid_key = p_uid.replace('-', '')
                player_details = PLAYER_DETAILS_CACHE.get(p_uid_key, {})
                p_level = player_details.get('level', player_levels.get(p_uid_key, '?'))
                p_seen = player_details.get('seen', 'N/A')
                pal_count = PLAYER_PAL_COUNTS.get(p_uid, 0)
                guild_members_tree.insert("", "end", values=(p_name, p_seen, p_level, pal_count, p_uid))
            break
def on_base_select(evt):
    sel=base_tree.selection()
    if not sel: return
    bid, _, guild_name = base_tree.item(sel[0])['values']
    base_result.configure(text=f"{t('ui.selected.base')}: {bid} ({guild_name})")
def on_player_select(evt):
    sel = player_tree.selection()
    if not sel: return
    name, _, _, _, uid, *_ = player_tree.item(sel[0])['values']
    player_result.configure(text=f"{t('ui.selected.player')}: {name} ({uid})")
def on_guild_member_select(event=None): pass
def on_guild_members_search(q=None):
    global guild_members_tree, guild_members_search_var, loaded_level_json, player_levels, PLAYER_PAL_COUNTS, guild_tree
    player_lookup_map = {
        uid.replace('-', ''): (uid, name, gid, seen, level) 
        for uid, name, gid, seen, level in get_players()
    }    
    if q is None:
        q = guild_members_search_var.get()
    q = q.lower()    
    guild_members_tree.delete(*guild_members_tree.get_children())
    sel = guild_tree.selection()
    if not sel: return
    gid = guild_tree.item(sel[0])['values'][1]    
    for g in loaded_level_json['properties']['worldSaveData']['value']['GroupSaveDataMap']['value']:
        if are_equal_uuids(g['key'], gid):
            raw = g['value'].get('RawData', {}).get('value', {})
            players = raw.get('players', [])            
            for p in players:
                p_name = p.get('player_info', {}).get('player_name', 'Unknown')
                p_uid_full = str(p.get('player_uid', ''))
                p_uid_stripped = p_uid_full.replace('-', '')
                p_level = player_levels.get(p_uid_stripped, '?')
                pal_count = PLAYER_PAL_COUNTS.get(p_uid_full, 0)
                player_data = player_lookup_map.get(p_uid_stripped)
                p_seen = player_data[3] if player_data else 'N/A'
                if any(q in str(c).lower() for c in (p_name, p_level, p_seen, p_uid_stripped, pal_count)):
                    guild_members_tree.insert("", "end", values=(p_name, p_seen, p_level, pal_count, p_uid_full))
            break
def get_current_stats():
    wsd = loaded_level_json['properties']['worldSaveData']['value']
    group_data = wsd.get('GroupSaveDataMap', {}).get('value', [])
    base_data = wsd.get('BaseCampSaveData', {}).get('value', [])
    char_data = wsd.get('CharacterSaveParameterMap', {}).get('value', [])
    total_players = sum(len(g['value']['RawData']['value'].get('players', [])) for g in group_data if g['value']['GroupType']['value']['value'] == 'EPalGroupType::Guild')
    total_guilds = sum(1 for g in group_data if g['value']['GroupType']['value']['value'] == 'EPalGroupType::Guild')
    total_bases = len(base_data)
    total_pals = 0
    for c in char_data:
        val = c.get('value', {}).get('RawData', {}).get('value', {})
        struct_type = val.get('object', {}).get('SaveParameter', {}).get('struct_type')
        if struct_type == 'PalIndividualCharacterSaveParameter':
            if 'IsPlayer' in val.get('object', {}).get('SaveParameter', {}).get('value', {}) and val['object']['SaveParameter']['value']['IsPlayer'].get('value'):
                continue
            total_pals += 1
    return dict(Players=total_players, Guilds=total_guilds, Bases=total_bases, Pals=total_pals)
def update_stats_section(stat_labels, section, stats):
    key_sec = section.lower().replace(" ", "")
    for field_key, value in stats.items():
        label_key = f"{key_sec}_{field_key.lower()}"
        if label_key in stat_labels:
            stat_labels[label_key].configure(text=str(value))
def create_search_panel(parent, label_key, search_var, search_callback, tree_columns, tree_headings, tree_col_widths, width, height, tree_height=12):
    panel = ttk.Frame(parent, style="TFrame")
    panel.columnconfigure(0, weight=1)
    panel.rowconfigure(1, weight=1)
    topbar = ttk.Frame(panel, style="TFrame")
    topbar.grid(row=0, column=0, sticky='ew', padx=5, pady=5)
    topbar.columnconfigure(1, weight=1)
    lbl = ttk.Label(topbar, text=t(label_key), font=("Arial", 10), style="TLabel")
    lbl.grid(row=0, column=0, sticky='w')
    entry = ttk.Entry(topbar, textvariable=search_var)
    entry.grid(row=0, column=1, sticky='ew', padx=(5, 0))
    entry.bind("<KeyRelease>", lambda e: search_callback(entry.get()))
    tree = ttk.Treeview(panel, columns=tree_columns, show='headings', height=tree_height)
    tree.grid(row=1, column=0, sticky='nsew', padx=5, pady=(0, 5))
    vsb = ttk.Scrollbar(panel, orient="vertical", command=tree.yview)
    vsb.grid(row=1, column=1, sticky='ns', padx=(0, 5), pady=(0, 5))
    tree.configure(yscrollcommand=vsb.set)
    for col, head, width_col in zip(tree_columns, tree_headings, tree_col_widths):
        tree.heading(col, text=head)
        tree.column(col, width=width_col, anchor='w')
    return panel, tree, entry, lbl
from PIL import Image, ImageDraw, ImageFont
def pil_text_to_surface(text, size=20, color=(255,255,255)):
    font_paths = [
        r"C:\Windows\Fonts\msgothic.ttc",
        r"C:\Windows\Fonts\YuGothicUI.ttf",
        r"C:\Windows\Fonts\YuGothic.ttf",
        r"C:\Windows\Fonts\meiryo.ttc",
        r"C:\Windows\Fonts\meiryob.ttc",
        r"C:\Windows\Fonts\msmincho.ttc"
    ]
    font = None
    for fp in font_paths:
        if os.path.exists(fp):
            try:
                font = ImageFont.truetype(fp, size)
                break
            except: pass
    if font is None: font = ImageFont.load_default()
    dummy = Image.new("RGBA", (1,1))
    draw = ImageDraw.Draw(dummy)
    bbox = draw.textbbox((0,0), text, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    img = Image.new("RGBA", (w, h), (0,0,0,0))
    ImageDraw.Draw(img).text((-bbox[0], -bbox[1]), text, font=font, fill=color)
    return pygame.image.fromstring(img.tobytes(), img.size, img.mode)
def show_base_map():
    global loaded_level_json
    folder = current_save_path
    if not folder:
        messagebox.showerror(t("error.title"), t("guild.rebuild.no_save"))
        return
    wsd = loaded_level_json['properties']['worldSaveData']['value']
    tick = wsd['GameTimeSaveData']['value']['RealDateTimeTicks']['value']
    pygame.init()
    base_dir = os.path.dirname(os.path.abspath(__file__))
    wm_path = os.path.join(base_dir, "resources", "worldmap.png")
    icon_path = os.path.join(base_dir, "resources", "pal.ico")
    base_icon_path = os.path.join(base_dir, "resources", "baseicon.png")
    font_path = os.path.join(base_dir, "resources", "NotoSansCJKsc-Regular.otf")
    orig_map_raw = pygame.image.load(wm_path)
    mw, mh = orig_map_raw.get_size()
    sidebar_w = 420
    w, h = min(mw, 1200) + sidebar_w, min(mh, 800)
    map_w = w - sidebar_w
    screen = pygame.display.set_mode((w, h), pygame.RESIZABLE)
    pygame.display.set_caption(f"PST - {t('map.viewer')}")
    if os.path.exists(icon_path):
        try:
            icon_surface = pygame.image.load(icon_path)
            pygame.display.set_icon(icon_surface)
        except: pass
    orig_map = orig_map_raw.convert_alpha()
    base_icon = pygame.image.load(base_icon_path).convert_alpha()
    base_icon = pygame.transform.smoothscale(base_icon, (28, 28))
    font = pygame.font.Font(font_path, 13)
    small_font = pygame.font.Font(font_path, 11)
    marker_rects = []
    active_shocks = []
    active_blocked_effects = []
    shake_amount = 0
    def trigger_nuke(px, py):
        nonlocal shake_amount
        shake_amount = 20
        active_shocks.append({'pos': (px, py), 'radius': 0, 'alpha': 255, 'start_time': time.time()})
    def trigger_blocked(px, py, target_id=None):
        active_blocked_effects.append({'pos': (px, py), 'alpha': 255, 'start_time': time.time(), 'target_id': target_id})
    def to_image_coordinates(x_world, y_world, width, height):
        x_min, x_max = -1000, 1000
        y_min, y_max = -1000, 1000
        x_scale, y_scale = width / (x_max - x_min), height / (y_max - y_min)
        return int((x_world - x_min) * x_scale), int((y_max - y_world) * y_scale)
    def from_image_coordinates(x_img, y_img, width, height):
        x_min, x_max = -1000, 1000
        y_min, y_max = -1000, 1000
        x_world = (x_img / width) * (x_max - x_min) + x_min
        y_world = y_max - (y_img / height) * (y_max - y_min)
        return int(x_world), int(y_world)
    def get_base_coords(b_val):
        try:
            translation = b_val['RawData']['value']['transform']['translation']
            return sav_to_map(translation['x'], translation['y'], new=True)
        except: return None, None
    def get_leader_name(g_val):
        admin_uid = str(g_val['RawData']['value'].get('admin_player_uid', ''))
        for p in g_val['RawData']['value'].get('players', []):
            if str(p.get('player_uid', '')) == admin_uid: return p.get('player_info', {}).get('player_name', admin_uid)
        return admin_uid if admin_uid else t("map.unknown.leader")
    def get_last_seen(g_val, current_tick):
        times = [p.get('player_info', {}).get('last_online_real_time') for p in g_val['RawData']['value'].get('players', []) if p.get('player_info', {}).get('last_online_real_time')]
        if not times: return t("map.unknown.lastseen")
        diff = (current_tick - max(times)) / 1e7
        days, hours, mins = int(diff // 86400), int((diff % 86400) // 3600), int((diff % 3600) // 60)
        if days > 0: return f"{days}d {hours}h"
        if hours > 0: return f"{hours}h {mins}m"
        return f"{mins}m"
    def truncate_text(text, max_w, use_font):
        text = text.encode('utf-16', 'surrogatepass').decode('utf-16', 'ignore')
        if use_font.size(text)[0] <= max_w: return text
        while use_font.size(text + "...")[0] > max_w and len(text) > 1: text = text[:-1]
        return text + "..."
    def get_guild_bases_live():
        guilds = {}
        wsd_live = loaded_level_json['properties']['worldSaveData']['value']
        group_map = wsd_live.get('GroupSaveDataMap', {}).get('value', [])
        base_map = {str(b['key']).replace('-', ''): b['value'] for b in wsd_live.get('BaseCampSaveData', {}).get('value', [])}
        for entry in group_map:
            gid, g_val = str(entry['key']), entry['value']
            base_ids = g_val['RawData']['value'].get('base_ids', [])
            valid_bases = []
            for bid in base_ids:
                bid_str = str(bid).replace('-', '')
                if bid_str in base_map:
                    bx, by = get_base_coords(base_map[bid_str])
                    valid_bases.append({'base_id': bid, 'coords': (bx, by), 'data': {'key': bid, 'value': base_map[bid_str]}, 'guild_id': gid, 'guild_name': g_val['RawData']['value'].get('guild_name', t("map.unknown.guild")), 'leader_name': get_leader_name(g_val)})
            if len(valid_bases) > 0:
                guilds[gid] = {'guild_name': g_val['RawData']['value'].get('guild_name', t("map.unknown.guild")), 'leader_name': get_leader_name(g_val), 'last_seen': get_last_seen(g_val, tick), 'bases': valid_bases}
        return guilds
    def filter_guilds_and_bases(guilds, search_text):
        if not search_text: return guilds
        terms = search_text.lower().split()
        filtered = {}
        for gid, g in guilds.items():
            gn, ln, ls = g['guild_name'].lower(), g['leader_name'].lower(), g['last_seen'].lower()
            bases = [b for b in g['bases'] if all(any(term in field for field in [str(b['base_id']).lower(), f"x:{int(b['coords'][0])}, y:{int(b['coords'][1])}" if b['coords'][0] is not None else "", gn, ln, ls]) for term in terms)]
            if bases:
                filtered[gid] = dict(g)
                filtered[gid]['bases'] = bases
        return filtered
    def draw_sidebar_ui(win_w, win_h):
        sidebar_surface = pygame.Surface((sidebar_w, win_h))
        sidebar_surface.fill((35, 35, 35))
        pygame.draw.line(sidebar_surface, (60, 60, 60), (0, 0), (0, win_h), 2)
        input_rect = pygame.Rect(15, 12, sidebar_w - 30, 32)
        pygame.draw.rect(sidebar_surface, (25, 25, 25), input_rect, border_radius=6)
        if active_input: pygame.draw.rect(sidebar_surface, (0, 150, 255), input_rect, width=2, border_radius=6)
        txt = user_input if user_input or active_input else t("map.search.placeholder")
        sidebar_surface.blit(font.render(txt, True, (220, 220, 220) if user_input or active_input else (100, 100, 100)), (input_rect.x + 10, input_rect.y + 7))
        y_h = 60
        pygame.draw.rect(sidebar_surface, (45, 45, 45), (5, y_h, sidebar_w - 10, 30), border_radius=4)
        cols = [(t("map.header.guild"), 15), (t("map.header.leader"), 135), (t("map.header.lastseen"), 245), (t("map.header.bases"), 335)]
        for lbl, off in cols: sidebar_surface.blit(small_font.render(lbl, True, (160, 160, 160)), (off, y_h + 7))
        y_c = 100 - scroll_offset
        for gid, guild in filtered_guilds.items():
            draw_list_item_to_surf(sidebar_surface, gid, guild, y_c, selected_item and selected_item[1] == gid, mouse_pos[0] > map_w and pygame.Rect(map_w + 5, y_c, sidebar_w - 10, item_height).collidepoint(mouse_pos))
            y_c += item_height
            if gid in expanded_guilds:
                for b in guild['bases']:
                    br = pygame.Rect(25, y_c, sidebar_w - 35, item_height - 4)
                    if (selected_item and selected_item[0] == 'base' and selected_item[1] == b): pygame.draw.rect(sidebar_surface, (70, 70, 70), br, border_radius=4)
                    sidebar_surface.blit(small_font.render(f"X: {int(b['coords'][0])} Y: {int(b['coords'][1])}", True, (0, 180, 255)), (br.x + 10, br.y + 6))
                    sidebar_surface.blit(small_font.render(str(b['base_id'])[:12] + "...", True, (130, 130, 130)), (br.x + 120, br.y + 6))
                    y_c += item_height
        screen.blit(sidebar_surface, (win_w - sidebar_w, 0))
    def draw_list_item_to_surf(surf, gid, guild, y, is_selected, is_hovered):
        rect = pygame.Rect(5, y, sidebar_w - 10, item_height - 2)
        if is_selected: pygame.draw.rect(surf, (60, 80, 100), rect, border_radius=4)
        elif is_hovered: pygame.draw.rect(surf, (50, 50, 50), rect, border_radius=4)
        color = (255, 255, 255) if not is_selected else (200, 230, 255)
        surf.blit(font.render(truncate_text(guild['guild_name'], 110, font), True, color), (rect.x + 10, rect.y + 6))
        surf.blit(small_font.render(truncate_text(guild['leader_name'], 100, small_font), True, (200, 200, 200)), (rect.x + 130, rect.y + 8))
        surf.blit(small_font.render(guild['last_seen'], True, (180, 180, 180)), (rect.x + 240, rect.y + 8))
        pygame.draw.circle(surf, (0, 180, 255), (rect.x + 350, rect.y + 14), 10)
        cnt = small_font.render(str(len(guild['bases'])), True, (255, 255, 255))
        surf.blit(cnt, (rect.x + 350 - cnt.get_width()//2, rect.y + 14 - cnt.get_height()//2))
    def draw_tooltip(lines, pos, m_w):
        tw, th = max(small_font.size(l)[0] for l in lines) + 20, len(lines) * 18 + 10
        tx, ty = pos[0] + 15, pos[1] + 15
        if tx + tw > m_w: tx = pos[0] - tw - 15
        if ty + th > h: ty = pos[1] - th - 15
        ts = pygame.Surface((tw, th), pygame.SRCALPHA)
        pygame.draw.rect(ts, (30, 30, 30, 230), (0, 0, tw, th), border_radius=8)
        pygame.draw.rect(ts, (80, 80, 80, 255), (0, 0, tw, th), width=1, border_radius=8)
        for i, l in enumerate(lines):
            col = (0, 180, 255) if i == 0 else (255, 255, 255)
            ts.blit(small_font.render(l, True, col), (10, 5 + i * 18))
        screen.blit(ts, (tx, ty))
    def get_initial_state(m_w, m_h):
        init_min_zoom = min(m_w / mw, m_h / mh)
        init_zoom = max(init_min_zoom, 0.15)
        init_off_x = (mw - m_w / init_zoom) / 2
        init_off_y = (mh - m_h / init_zoom) / 2
        return init_zoom, init_off_x, init_off_y, init_zoom
    zoom, offset_x, offset_y, absolute_min_zoom = get_initial_state(map_w, h)
    target_zoom, target_offset_x, target_offset_y = zoom, offset_x, offset_y
    is_animating, dragging, drag_start, offset_origin = False, False, (0, 0), (0, 0)
    clock = pygame.time.Clock()
    running, user_input, active_input = True, "", False
    scroll_offset, item_height = 0, 30
    expanded_guilds, selected_item, glow_start_time = set(), None, None
    context_menu_pos, context_menu_target, last_click_time = None, None, 0
    guilds_all = get_guild_bases_live()
    while running:
        mouse_pos = pygame.mouse.get_pos()
        w, h = screen.get_size()
        map_w = w - sidebar_w
        if is_animating:
            zoom += (target_zoom - zoom) * 0.1
            offset_x += (target_offset_x - offset_x) * 0.1
            offset_y += (target_offset_y - offset_y) * 0.1
            if abs(offset_x - target_offset_x) < 0.1 and abs(zoom - target_zoom) < 0.001: is_animating = False
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT: running = False
            elif ev.type == pygame.KEYDOWN:
                if active_input:
                    if ev.key == pygame.K_BACKSPACE: user_input = user_input[:-1]
                    elif ev.key == pygame.K_RETURN: active_input = False
                    elif ev.unicode.isprintable(): user_input += ev.unicode
                elif ev.key == pygame.K_f: active_input = True
                elif ev.key == pygame.K_r:
                    target_zoom, target_offset_x, target_offset_y, _ = get_initial_state(map_w, h)
                    is_animating = True
                elif ev.key == pygame.K_ESCAPE: running = False
            elif ev.type == pygame.MOUSEBUTTONDOWN:
                if ev.button == 1:
                    now = time.time()
                    is_double = (now - last_click_time < 0.3)
                    last_click_time = now
                    if context_menu_pos:
                        if context_menu_target[0] == 'base': opts = [t("delete.base"), t("button.export")]
                        else: opts = [t("guild.rename.title"), t("delete.guild"), t("button.import")]
                        cmr = pygame.Rect(context_menu_pos[0], context_menu_pos[1], 160, len(opts) * 32)
                        if cmr.collidepoint(ev.pos):
                            idx = (ev.pos[1] - context_menu_pos[1]) // 32
                            if 0 <= idx < len(opts):
                                act = opts[idx]
                                if act == t("delete.base"):
                                    bid, bx, by = str(context_menu_target[1]['base_id']), context_menu_target[1]['coords'][0], context_menu_target[1]['coords'][1]
                                    for item in base_tree.get_children():
                                        if str(base_tree.item(item)['values'][0]) == bid: base_tree.selection_set(item); delete_selected_base(); break
                                    guilds_all = get_guild_bases_live()
                                    still_exists = any(bid == str(b['base_id']) for g in guilds_all.values() for b in g['bases'])
                                    cx, cy = to_image_coordinates(bx, by, mw, mh)
                                    if not still_exists:
                                        trigger_nuke((cx - offset_x) * zoom, (cy - offset_y) * zoom)
                                        target_zoom, target_offset_x, target_offset_y, _ = get_initial_state(map_w, h); is_animating = True
                                    else: trigger_blocked((cx - offset_x) * zoom, (cy - offset_y) * zoom, bid)
                                elif act == t("delete.guild"):
                                    gid = str(context_menu_target[1])
                                    for item in guild_tree.get_children():
                                        if str(guild_tree.item(item)['values'][1]) == gid: guild_tree.selection_set(item); delete_selected_guild(); break
                                    guilds_all = get_guild_bases_live()
                                    if gid not in guilds_all:
                                        trigger_nuke(map_w // 2, h // 2)
                                        target_zoom, target_offset_x, target_offset_y, _ = get_initial_state(map_w, h); is_animating = True
                                elif act == t("guild.rename.title"):
                                    gid = str(context_menu_target[1])
                                    for item in guild_tree.get_children():
                                        if str(guild_tree.item(item)['values'][1]) == gid: guild_tree.selection_set(item); rename_guild(); break
                                    guilds_all = get_guild_bases_live()
                                elif act == t("button.export"):
                                    bid = str(context_menu_target[1]['base_id'])
                                    exp_data = export_base_json(loaded_level_json, bid)
                                    if exp_data:
                                        save_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")], initialfile=f"base_{bid[:8]}.json")
                                        if save_path:
                                            class CustomEncoder(json.JSONEncoder):
                                                def default(self, obj):
                                                    if hasattr(obj, 'bytes') or obj.__class__.__name__ == 'UUID':
                                                        return str(obj)
                                                    return super().default(obj)
                                            with open(save_path, 'w', encoding='utf-8') as f:
                                                json.dump(exp_data, f, cls=CustomEncoder)
                                            bx, by = context_menu_target[1]['coords']
                                            cx, cy = to_image_coordinates(bx, by, mw, mh)
                                            trigger_nuke((cx - offset_x) * zoom, (cy - offset_y) * zoom)
                                            messagebox.showinfo(t("success.title"), t("base.export.success"))
                                elif act == t("button.import"):
                                    gid_str = str(context_menu_target[1])
                                    import_file = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
                                    if import_file:
                                        with open(import_file, 'r', encoding='utf-8') as f: exp_data = json.load(f)
                                        if import_base_json(loaded_level_json, exp_data, gid_str):
                                            guilds_all = get_guild_bases_live()
                                            try:
                                                raw_t = exp_data["base_camp"]["value"]["RawData"]["value"]["transform"]["translation"]
                                                bx, by = sav_to_map(raw_t['x'], raw_t['y'], new=True)
                                                cx, cy = to_image_coordinates(bx, by, mw, mh)
                                                target_zoom, target_offset_x, target_offset_y = 2.0, cx - map_w/(2*2.0), cy - h/(2*2.0)
                                                is_animating, glow_start_time = True, time.time()
                                                trigger_nuke(map_w // 2, h // 2)
                                            except: pass
                                            messagebox.showinfo(t("success.title"), t("base.import.success"))
                        context_menu_pos = None
                        continue
                    if ev.pos[0] < map_w:
                        hb = next((b for b, r in marker_rects if r.collidepoint(ev.pos)), None)
                        if hb and is_double:
                            bx, by = hb['coords']
                            if bx is not None:
                                cx, cy = to_image_coordinates(bx, by, mw, mh)
                                target_zoom, glow_start_time = 2.5, time.time()
                                target_offset_x, target_offset_y = cx - map_w / (2 * target_zoom), cy - h / (2 * target_zoom)
                                is_animating, selected_item = True, ('base', hb)
                                continue
                        reset_rect = pygame.Rect(map_w - 30, h // 2 - 20, 30, 40)
                        if reset_rect.collidepoint(ev.pos):
                            target_zoom, target_offset_x, target_offset_y, _ = get_initial_state(map_w, h); is_animating = True
                            continue
                        dragging, drag_start, offset_origin, is_animating = True, ev.pos, (offset_x, offset_y), False
                    else:
                        if pygame.Rect(w - sidebar_w + 15, 12, sidebar_w - 30, 32).collidepoint(ev.pos): active_input = True
                        else:
                            active_input, rel_y = False, ev.pos[1] + scroll_offset - 100
                            y_cursor, clicked = 0, False
                            for gid, guild in filtered_guilds.items():
                                if y_cursor <= rel_y < y_cursor + item_height:
                                    if not is_double:
                                        if gid in expanded_guilds: expanded_guilds.remove(gid)
                                        else: expanded_guilds.add(gid)
                                    selected_item, clicked = ('guild', gid), True
                                    break
                                y_cursor += item_height
                                if gid in expanded_guilds:
                                    for b in guild['bases']:
                                        if y_cursor <= rel_y < y_cursor + item_height:
                                            selected_item, clicked = ('base', b), True
                                            if is_double:
                                                bx, by = b['coords']
                                                if bx is not None:
                                                    cx, cy = to_image_coordinates(bx, by, mw, mh)
                                                    target_zoom, glow_start_time = 2.5, time.time()
                                                    target_offset_x, target_offset_y = cx - map_w / (2 * target_zoom), cy - h / (2 * target_zoom)
                                                    is_animating = True
                                            break
                                        y_cursor += item_height
                                if clicked: break
                elif ev.button == 3:
                    found = next((('base', b) for b, r in marker_rects if r.collidepoint(ev.pos)), None)
                    if not found and ev.pos[0] > map_w:
                        rel_y, y_cursor = ev.pos[1] + scroll_offset - 100, 0
                        for gid, guild in filtered_guilds.items():
                            if y_cursor <= rel_y < y_cursor + item_height: found = ('guild', gid); break
                            y_cursor += item_height
                            if gid in expanded_guilds:
                                for b in guild['bases']:
                                    if y_cursor <= rel_y < y_cursor + item_height: found = ('base', b); break
                                    y_cursor += item_height
                            if found: break
                    if found: context_menu_pos, context_menu_target = ev.pos, found
            elif ev.type == pygame.MOUSEBUTTONUP: dragging = False
            elif ev.type == pygame.MOUSEMOTION and dragging:
                dx, dy = ev.pos[0] - drag_start[0], ev.pos[1] - drag_start[1]
                offset_x, offset_y = offset_origin[0] - dx / zoom, offset_origin[1] - dy / zoom
                target_offset_x, target_offset_y = offset_x, offset_y
            elif ev.type == pygame.MOUSEWHEEL:
                if mouse_pos[0] > map_w: scroll_offset = max(0, scroll_offset - ev.y * 40)
                else:
                    new_zoom = zoom * (1.1 if ev.y > 0 else 0.9)
                    if new_zoom < absolute_min_zoom:
                        zoom = absolute_min_zoom
                        target_zoom, target_offset_x, target_offset_y, _ = get_initial_state(map_w, h); is_animating = True
                    else:
                        is_animating, old_z = False, zoom
                        zoom = min(new_zoom, 8.0)
                        offset_x, offset_y = (offset_x + mouse_pos[0] / old_z) - mouse_pos[0] / zoom, (offset_y + mouse_pos[1] / old_z) - mouse_pos[1] / zoom
                        target_zoom, target_offset_x, target_offset_y = zoom, offset_x, offset_y
            elif ev.type == pygame.VIDEORESIZE:
                screen = pygame.display.set_mode((ev.w, ev.h), pygame.RESIZABLE)
                _, _, _, absolute_min_zoom = get_initial_state(ev.w - sidebar_w, ev.h)
                if zoom <= absolute_min_zoom:
                    zoom = absolute_min_zoom
                    target_zoom, target_offset_x, target_offset_y, _ = get_initial_state(ev.w - sidebar_w, ev.h); is_animating = True
        rw, rh = min(int(map_w / zoom), mw), min(int(h / zoom), mh)
        offset_x, offset_y = max(0, min(offset_x, mw - rw)), max(0, min(offset_y, mh - rh))
        screen.fill((20, 20, 20))
        sh_x, sh_y = 0, 0
        if shake_amount > 0:
            sh_x, sh_y = random.randint(-int(shake_amount), int(shake_amount)), random.randint(-int(shake_amount), int(shake_amount))
            shake_amount *= 0.9
            if shake_amount < 0.5: shake_amount = 0
        sub = orig_map.subsurface(pygame.Rect(int(offset_x), int(offset_y), rw, rh))
        screen.blit(pygame.transform.smoothscale(sub, (map_w, h)), (sh_x, sh_y))
        marker_rects.clear()
        filtered_guilds = filter_guilds_and_bases(guilds_all, user_input)
        for gid, guild in filtered_guilds.items():
            for b in guild['bases']:
                bx, by = b['coords']
                if bx is None: continue
                cx, cy = to_image_coordinates(bx, by, mw, mh)
                px, py = (cx - offset_x) * zoom, (cy - offset_y) * zoom
                if 0 <= px < map_w and 0 <= py < h:
                    b_shx, b_shy = 0, 0
                    for eff in active_blocked_effects:
                        if eff['target_id'] == str(b['base_id']):
                            el = time.time() - eff['start_time']
                            if el < 0.8: b_shx, b_shy = random.randint(-5, 5), random.randint(-5, 5)
                    if glow_start_time:
                        el = time.time() - glow_start_time
                        if el < 5:
                            s = pygame.Surface((120, 120), pygame.SRCALPHA)
                            pulse = (math.sin(el * 10) + 1) / 2
                            pygame.draw.circle(s, (0, 200, 255, int(150 * (1 - el/5))), (60, 60), 20 + int(40 * pulse))
                            screen.blit(s, (px - 60 + sh_x + b_shx, py - 60 + sh_y + b_shy))
                            scan_y = int((el % 1.0) * 40) - 20
                            pygame.draw.line(screen, (255, 255, 255, int(200 * (1 - el/5))), (px - 20, py + scan_y), (px + 20, py + scan_y), 2)
                    mr = pygame.Rect(px - 14 + sh_x + b_shx, py - 14 + sh_y + b_shy, 28, 28)
                    screen.blit(base_icon, mr)
                    marker_rects.append((b, mr))
        for shock in active_shocks[:]:
            el = time.time() - shock['start_time']
            if el > 1.0: active_shocks.remove(shock); continue
            shock['radius'] += 20; shock['alpha'] = int(255 * (1 - el))
            s = pygame.Surface((map_w, h), pygame.SRCALPHA)
            pygame.draw.circle(s, (255, 255, 255, shock['alpha']), shock['pos'], shock['radius'], 6)
            flash = pygame.Surface((map_w, h), pygame.SRCALPHA)
            flash.fill((255, 255, 180, int(shock['alpha'] * 0.4)))
            screen.blit(flash, (0, 0)); screen.blit(s, (0, 0))
        for eff in active_blocked_effects[:]:
            el = time.time() - eff['start_time']
            if el > 0.8: active_blocked_effects.remove(eff); continue
            eff['alpha'] = int(255 * (1 - el/0.8))
            px, py = eff['pos']
            ms_shx, ms_shy = random.randint(-5, 5), random.randint(-5, 5)
            sz = 20 + int(10 * math.sin(el * 10))
            pygame.draw.line(screen, (255, 0, 0, eff['alpha']), (px - sz + ms_shx, py - sz + ms_shy), (px + sz + ms_shx, py + sz + ms_shy), 6)
            pygame.draw.line(screen, (255, 0, 0, eff['alpha']), (px + sz + ms_shx, py - sz + ms_shy), (px - sz + ms_shx, py + sz + ms_shy), 6)
        draw_sidebar_ui(w, h)
        reset_rect = pygame.Rect(map_w - 30, h // 2 - 20, 30, 40)
        pygame.draw.rect(screen, (50, 50, 50), reset_rect, border_top_left_radius=6, border_bottom_left_radius=6)
        screen.blit(font.render("R", True, (255, 255, 255)), (reset_rect.x + 10, reset_rect.y + 12))
        hb = next((b for b, r in marker_rects if r.collidepoint(mouse_pos)), None)
        if hb and not context_menu_pos: draw_tooltip([f"Guild: {hb['guild_name']}", f"Leader: {hb['leader_name']}", f"ID: {hb['base_id']}", f"Coords: X:{int(hb['coords'][0])} Y:{int(hb['coords'][1])}"], mouse_pos, map_w)
        if mouse_pos[0] < map_w:
            mx, my = from_image_coordinates(offset_x + (mouse_pos[0]-sh_x)/zoom, offset_y + (mouse_pos[1]-sh_y)/zoom, mw, mh)
            coord_s = small_font.render(f"Cursor: {mx}, {my}", True, (255, 255, 255))
            pygame.draw.rect(screen, (0, 0, 0, 150), (10, h - 30, coord_s.get_width() + 10, 20), border_radius=4)
            screen.blit(coord_s, (15, h - 28))
        if context_menu_pos:
            if context_menu_target[0] == 'base': opts = [t("delete.base"), t("button.export")]
            else: opts = [t("guild.rename.title"), t("delete.guild"), t("button.import")]
            cmr = pygame.Rect(context_menu_pos[0], context_menu_pos[1], 160, len(opts) * 32)
            pygame.draw.rect(screen, (40, 40, 40), cmr, border_radius=4); pygame.draw.rect(screen, (80, 80, 80), cmr, 1, border_radius=4)
            for i, txt in enumerate(opts):
                col = (255, 100, 100) if (txt == t("delete.base") or txt == t("delete.guild")) else (255, 255, 255)
                screen.blit(font.render(txt, True, col), (context_menu_pos[0] + 10, context_menu_pos[1] + 6 + i*32))
        pygame.display.flip()
        clock.tick(60)
    pygame.quit()
class KillNearestBaseDialog(tk.Toplevel):
    def __init__(self, master=None):
        super().__init__(master)
        load_exclusions()
        self.title("Generate PalDefender killnearestbase Commands")
        self.geometry("800x600")
        try: 
            self.iconbitmap(ICON_PATH)
            self.tk.call('wm', 'iconbitmap', '.', ICON_PATH)
        except Exception as e:
            print(f"Error setting window icon: {e}")
        self.config(bg=GLASS_BG)
        font_style = ("Arial", 10)
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure("TFrame", background=GLASS_BG)
        style.configure("TLabel", background=GLASS_BG, foreground=TEXT_COLOR, font=font_style)
        style.configure("TEntry", fieldbackground="#444444", foreground=TEXT_COLOR, font=font_style)
        style.configure("Dark.TButton", background=BUTTON_FG, foreground=TEXT_COLOR, font=font_style, padding=6)
        style.map("Dark.TButton",
            background=[("active", BUTTON_HOVER), ("!disabled", BUTTON_FG)],
            foreground=[("disabled", "#888888"), ("!disabled", TEXT_COLOR)]
        )
        style.configure("TRadiobutton", background=GLASS_BG, foreground=TEXT_COLOR, font=font_style)
        style.map("TRadiobutton",
            background=[("active", "#3a3a3a"), ("!active", GLASS_BG)],
            foreground=[("active", TEXT_COLOR), ("!active", TEXT_COLOR)]
        )
        self.setup_ui()
        self.protocol("WM_DELETE_WINDOW", self.on_exit)
    def setup_ui(self):
        frame = ttk.Frame(self, style="TFrame")
        frame.pack(padx=20, pady=20, fill="both", expand=True)
        ttk.Label(frame, text="Filter Type:", style="TLabel").grid(row=0, column=0, sticky="w")
        self.filter_var = tk.StringVar(value="1")
        for i, txt in enumerate(["Inactivity (days)", "Max Level", "Both"]):
            ttk.Radiobutton(frame, text=txt, variable=self.filter_var, value=str(i+1), style="TRadiobutton").grid(row=0, column=i+1, sticky="w", padx=5)
        instructions = ("Choose filter type:\n"
                        "Inactivity: Select bases with players inactive for given days.\n"
                        "Max Level: Select bases with max player level below given.\n"
                        "Both: Combine both filters.")
        ttk.Label(frame, text=instructions, style="TLabel", justify="left").grid(row=0, column=4, sticky="w", padx=10)
        ttk.Label(frame, text="Inactivity Days:", style="TLabel").grid(row=1, column=0, sticky="w", pady=10)
        self.inactivity_entry = ttk.Entry(frame, style="TEntry", width=15)
        self.inactivity_entry.grid(row=1, column=1, sticky="w")
        ttk.Label(frame, text="Max Level:", style="TLabel").grid(row=1, column=2, sticky="w", pady=10)
        self.maxlevel_entry = ttk.Entry(frame, style="TEntry", width=15)
        self.maxlevel_entry.grid(row=1, column=3, sticky="w")
        run_btn = ttk.Button(frame, text="Run", command=self.on_generate, style="Dark.TButton")
        run_btn.grid(row=2, column=0, columnspan=5, pady=15, sticky="ew")
        self.output_text = tk.Text(frame, bg=GLASS_BG, fg=TEXT_COLOR, font=("Consolas", 10), wrap="word")
        self.output_text.grid(row=3, column=0, columnspan=5, sticky="nsew")
        frame.rowconfigure(3, weight=1)
        frame.columnconfigure(4, weight=1)
    def append_output(self, text):
        self.output_text.insert(tk.END, text + "\n")
        self.output_text.see(tk.END)
    def clear_output(self):
        self.output_text.delete(1.0, tk.END)
    def on_generate(self):
        self.clear_output()
        try:
            ftype = self.filter_var.get()
            inactivity_days = int(self.inactivity_entry.get()) if self.inactivity_entry.get() else None
            max_level = int(self.maxlevel_entry.get()) if self.maxlevel_entry.get() else None
            if ftype == "1" and inactivity_days is None:
                messagebox.showerror("Input Error", "Please enter Inactivity Days.")
                return
            if ftype == "2" and max_level is None:
                messagebox.showerror("Input Error", "Please enter Max Level.")
                return
            if ftype == "3" and (inactivity_days is None or max_level is None):
                messagebox.showerror("Input Error", "Please enter both Inactivity Days and Max Level.")
                return
            result = self.parse_log(
                inactivity_days=inactivity_days if ftype in ("1","3") else None,
                max_level=max_level if ftype in ("2","3") else None)
            if not result:
                self.append_output("No guilds matched the filter criteria.")
        except ValueError:
            messagebox.showerror("Input Error", "Please enter valid numeric values.")
    def parse_log(self, inactivity_days=None, max_level=None):
        global exclusions
        log_file = "Scan Save Logger/scan_save.log"
        if not os.path.exists(log_file):
            self.append_output(f"Log file '{log_file}' not found.")
            return False
        with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        guilds = [g.strip() for g in re.split(r"={60,}", content) if g.strip()]
        inactive_guilds = {}
        kill_commands = []
        guild_count = base_count = excluded_guilds = excluded_bases = 0
        for guild in guilds:
            players_data = re.findall(
                r"Player: (.+?) \| UID: ([a-f0-9-]+) \| Level: (\d+) \| Caught: (\d+) \| Owned: (\d+) \| Encounters: (\d+) \| Uniques: (\d+) \| Last Online: (.+? ago)", guild)
            bases = re.findall(
                r"Base \d+: Base ID: ([a-f0-9-]+) \| .+? \| RawData: (.+)", guild)
            if not players_data or not bases:
                continue
            guild_name = re.search(r"Guild: (.+?) \|", guild)
            guild_leader = re.search(r"Guild Leader: (.+?) \|", guild)
            guild_id = re.search(r"Guild ID: ([a-f0-9-]+)", guild)
            guild_name = guild_name.group(1) if guild_name else "Unnamed Guild"
            guild_leader = guild_leader.group(1) if guild_leader else "Unknown"
            guild_id = guild_id.group(1) if guild_id else "Unknown"
            if guild_id in exclusions.get("guilds", []):
                excluded_guilds += 1
                continue
            filtered_bases = []
            for base_id, raw_data in bases:
                if base_id in exclusions.get("bases", []):
                    excluded_bases += 1
                    continue
                filtered_bases.append((base_id, raw_data))
            if not filtered_bases:
                continue
            if inactivity_days is not None:
                if any(
                    "d" not in player[7] or int(re.search(r"(\d+)d", player[7]).group(1)) < inactivity_days
                    for player in players_data):
                    continue
            if max_level is not None:
                if any(int(player[2]) > max_level for player in players_data):
                    continue
            if guild_id not in inactive_guilds:
                inactive_guilds[guild_id] = {
                    "guild_name": guild_name,
                    "guild_leader": guild_leader,
                    "players": [],
                    "bases": []
                }
            for player in players_data:
                inactive_guilds[guild_id]["players"].append({
                    "name": player[0],
                    "uid": player[1],
                    "level": player[2],
                    "caught": player[3],
                    "owned": player[4],
                    "encounters": player[5],
                    "uniques": player[6],
                    "last_online": player[7]
                })
            inactive_guilds[guild_id]["bases"].extend(filtered_bases)
            guild_count += 1
            base_count += len(filtered_bases)
            for _, raw_data in filtered_bases:
                coords = re.findall(r"[-+]?\d*\.\d+|[-+]?\d+", raw_data)
                if len(coords) >= 3:
                    x, y, z = map(float, coords[:3])
                    base_coords = sav_to_map(x, y)
                    kill_commands.append(f"killnearestbase {base_coords.x:.2f} {base_coords.y:.2f} {z:.2f}")
        for guild_id, info in inactive_guilds.items():
            self.append_output(f"Guild: {info['guild_name']} | Leader: {info['guild_leader']} | ID: {guild_id}")
            self.append_output(f"Players: {len(info['players'])}")
            for p in info['players']:
                self.append_output(f"  Player: {p['name']} | UID: {p['uid']} | Level: {p['level']} | Caught: {p['caught']} | Owned: {p['owned']} | Encounters: {p['encounters']} | Uniques: {p['uniques']} | Last Online: {p['last_online']}")
            self.append_output(f"Bases: {len(info['bases'])}")
            for base_id, raw_data in info['bases']:
                self.append_output(f"  Base ID: {base_id} | RawData: {raw_data}")
            self.append_output("-" * 40)
        self.append_output(f"\nFound {guild_count} guild(s) with {base_count} base(s).")
        if kill_commands:
            os.makedirs("PalDefender", exist_ok=True)
            with open("PalDefender/paldefender_bases.log", "w", encoding='utf-8') as f:
                f.write("\n".join(kill_commands))
            self.append_output(f"Wrote {len(kill_commands)} kill commands to PalDefender/paldefender_bases.log.")
        else:
            self.append_output("No kill commands generated.")
        if inactivity_days is not None:
            self.append_output(f"Inactivity filter applied: >= {inactivity_days} day(s).")
        if max_level is not None:
            self.append_output(f"Level filter applied: <= {max_level}.")
        self.append_output(f"Excluded guilds: {excluded_guilds}")
        self.append_output(f"Excluded bases: {excluded_bases}")
        if guild_count > 0:
            os.makedirs("PalDefender", exist_ok=True)
            with open("PalDefender/paldefender_bases_info.log", "w", encoding="utf-8") as info_log:
                info_log.write("-"*40+"\n")
                for gid, ginfo in inactive_guilds.items():
                    info_log.write(f"Guild: {ginfo['guild_name']} | Leader: {ginfo['guild_leader']} | ID: {gid}\n")
                    info_log.write(f"Players: {len(ginfo['players'])}\n")
                    for p in ginfo['players']:
                        info_log.write(f"  Player: {p['name']} | UID: {p['uid']} | Level: {p['level']} | Caught: {p['caught']} | Owned: {p['owned']} | Encounters: {p['encounters']} | Uniques: {p['uniques']} | Last Online: {p['last_online']}\n")
                    info_log.write(f"Bases: {len(ginfo['bases'])}\n")
                    for base_id, raw_data in ginfo['bases']:
                        coords = re.findall(r"[-+]?\d*\.\d+|[-+]?\d+", raw_data)
                        if len(coords) >= 3:
                            x, y, z = map(float, coords[:3])
                            map_coords = sav_to_map(x, y)
                            info_log.write(f"  Base ID: {base_id} | Map Coords: X: {map_coords.x:.2f}, Y: {map_coords.y:.2f}, Z: {z:.2f}\n")
                        else:
                            info_log.write(f"  Base ID: {base_id} | Invalid RawData: {raw_data}\n")
                    info_log.write("-"*40+"\n")
                info_log.write(f"Found {guild_count} guild(s) with {base_count} base(s).\n")
                info_log.write("-"*40)
        return guild_count > 0
    def on_exit(self):
        self.destroy()
def open_kill_nearest_base_ui(master=None):
    folder = current_save_path
    if not folder:
        messagebox.showerror(t("Error"), t("guild.rebuild.no_save"))
        return
    dlg = KillNearestBaseDialog(master)
    dlg.grab_set()
EXCLUSIONS_FILE = r"Assets\deletion_exclusions.json"
exclusions = {}
def load_exclusions():
    global exclusions
    if not os.path.exists(EXCLUSIONS_FILE):
        template = {"players": [], "guilds": [], "bases": []}
        with open(EXCLUSIONS_FILE, "w") as f:
            json.dump(template, f, indent=4)
        exclusions.update(template)
        return
    with open(EXCLUSIONS_FILE, "r") as f:
        exclusions.update(json.load(f))
load_exclusions()
def get_stat_value(stat_labels, key):
    label_text = stat_labels[key].cget("text")
    if ":" in label_text:
        return label_text.split(":")[1].strip()
    return label_text.strip()
def copy_stats_to_clipboard(stat_labels):
    copy_content = "PalworldSaveTools\n\n"
    sections = ["before", "after", "result"]
    fields = ["guilds", "bases", "players", "pals"]
    header_template = "{type:<15}{before:<12}{after:<12}{result}"
    data_template = "{type:<15}{before:<12}{after:<12}{result}" 
    copy_content += header_template.format(
        type=t('deletion.stats.field'),
        before=t('deletion.stats.before'),
        after=t('deletion.stats.after'),
        result=t('deletion.stats.result')
    ) + "\n"
    for field in fields:
        field_name = t(f"deletion.stats.{field}")
        before_val = get_stat_value(stat_labels, f"before_{field}")
        after_val = get_stat_value(stat_labels, f"after_{field}")
        result_val = get_stat_value(stat_labels, f"result_{field}")        
        copy_content += data_template.format(
            type=field_name,
            before=before_val,
            after=after_val,
            result=result_val
        ) + "\n"        
    try:
        root = tk.Tk()
        root.withdraw()
        root.clipboard_clear()
        root.clipboard_append(copy_content)
        root.update()
        root.destroy()
        messagebox.showinfo(t('status.copy_success_title'), t('status.copy_success_body'))
    except Exception:
        messagebox.showerror(t('status.copy_fail_title'), t('status.copy_fail_body'))
def create_stats_panel(parent, style):
    stat_frame = ctk.CTkFrame(parent, fg_color="transparent", border_width=0, corner_radius=0)
    sections=[("Before","deletion.stats.before"),("After","deletion.stats.after"),("Result","deletion.stats.result")]
    fields=[("Guilds","deletion.stats.guilds"),("Bases","deletion.stats.bases"),("Players","deletion.stats.players"),("Pals","deletion.stats.pals")]
    stat_labels={}
    stat_key_labels_to_refresh=[]
    last_row_index=len(fields)
    copy_btn=ctk.CTkButton(stat_frame,text="📋",width=30,height=24,fg_color="transparent",hover_color="#555555",command=lambda:copy_stats_to_clipboard(stat_labels))
    copy_btn.grid(row=0,column=len(sections)+1,padx=5,pady=3,sticky="ne")
    ctk.CTkLabel(stat_frame,text="",text_color="white",font=("Segoe UI",12,"bold"),fg_color="transparent").grid(row=0,column=0,padx=10,pady=3)
    for col,(sec_key,sec_label_key) in enumerate(sections,start=1):
        lbl=ctk.CTkLabel(stat_frame,text=t(sec_label_key),text_color="white",font=("Segoe UI",12,"bold"),fg_color="transparent")
        lbl.grid(row=0,column=col,padx=10,pady=3)
        stat_key_labels_to_refresh.append((lbl,sec_label_key))
    for row,(field_key,field_label_key) in enumerate(fields,start=1):
        field_label=ctk.CTkLabel(stat_frame,text=t(field_label_key)+":",text_color="white",font=("Segoe UI",11),height=14,fg_color="transparent")
        field_label.grid(row=row,column=0,sticky="w",padx=10,pady=(1,1) if row==last_row_index else (0,0))
        stat_key_labels_to_refresh.append((field_label,field_label_key))
        for col,(sec_key,_) in enumerate(sections,start=1):
            key=f"{sec_key.lower().replace(' ','')}_{field_key.lower()}"
            lbl=ctk.CTkLabel(stat_frame,text="0",text_color="white",font=("Segoe UI",11),height=14,fg_color="transparent")
            lbl.grid(row=row,column=col,sticky="w",padx=10,pady=(1,1) if row==last_row_index else (0,0))
            stat_labels[key]=lbl
    return stat_frame,stat_labels,stat_key_labels_to_refresh
def generate_map():
    folder_path=current_save_path
    if not folder_path:
        messagebox.showerror(t("Error"),t("guild.rebuild.no_save"))
        return
    start_time=time.time()
    script_dir=os.path.dirname(os.path.abspath(__file__))
    main_dir=os.path.dirname(script_dir)
    log_file_path=os.path.join(main_dir,'Scan Save Logger','scan_save.log')
    if not os.path.exists(log_file_path):
        messagebox.showerror(t("Error"),t("map.log_not_found",path=log_file_path))
        return False
    try:
        guild_data,base_keys=parse_logfile(log_file_path)
        write_csv(guild_data,base_keys,'bases.csv')
        create_world_map()
        map_path=os.path.join(main_dir,"updated_worldmap.png")
        if os.path.exists(map_path):
            print(t("map.opening_image"))
            open_file_with_default_app(map_path)
        else:
            messagebox.showerror(t("Error"),t("map.not_found"))
            print(t("map.not_found"))
        end_time=time.time()
        duration=end_time-start_time
        print(t("map.done_in_seconds",sec=f"{duration:.2f}"))
        return True
    except Exception as e:
        messagebox.showerror(t("Error"),t("map.error_generating",err=e))
        print(t("map.error_generating",err=e))
        return False
def reset_anti_air_turrets():
    folder_path=current_save_path
    if not folder_path:
        messagebox.showerror(t("Error"),t("guild.rebuild.no_save"))
        return
    try:
        wsd=loaded_level_json['properties']['worldSaveData']['value']
    except KeyError:
        messagebox.showerror(t("Error"),t("turret.invalid_structure"))
        return
    if "FixedWeaponDestroySaveData" in wsd:
        del wsd["FixedWeaponDestroySaveData"]
        print(t("turret.reset_success"))
        messagebox.showinfo(t("Success"),t("turret.reset_success"))
    else:
        print(t("turret.none_found"))
        messagebox.showinfo(t("Info"),t("turret.none_found"))
    refresh_all()
def reset_dungeons():
    folder_path=current_save_path
    if not folder_path:
        messagebox.showerror(t("Error"),t("guild.rebuild.no_save"))
        return
    try:
        wsd=loaded_level_json['properties']['worldSaveData']['value']
    except KeyError:
        messagebox.showerror(t("Error"),t("turret.invalid_structure"))
        return
    if "DungeonPointMarkerSaveData" in wsd:
        del wsd["DungeonPointMarkerSaveData"]
        print(t("reset_dungeons.reset_success"))
        messagebox.showinfo(t("Success"),t("reset_dungeons.reset_success"))
    else:
        print(t("reset_dungeons.none_found"))
        messagebox.showinfo(t("Info"),t("reset_dungeons.none_found"))
    refresh_all()
def unlock_all_private_chests():
    folder_path=current_save_path
    if not folder_path:
        messagebox.showerror(t("Error"),t("guild.rebuild.no_save"))
        return
    global loaded_level_json
    try:
        wsd=loaded_level_json['properties']['worldSaveData']['value']
    except KeyError:
        messagebox.showinfo(t("Error"),t("chest.invalid_structure"))
        return
    count=0
    def deep_unlock(data):
        nonlocal count
        if isinstance(data,dict):
            ctype=data.get("concrete_model_type","")
            if ctype in("PalMapObjectItemBoothModel","PalMapObjectPalBoothModel"):
                return
            if "private_lock_player_uid" in data:
                data["private_lock_player_uid"]="00000000-0000-0000-0000-000000000000"
                count+=1
            for v in data.values():
                deep_unlock(v)
        elif isinstance(data,list):
            for item in data:
                deep_unlock(item)
    deep_unlock(wsd)
    msg=t("chest.unlocked_summary",count=count)
    print(msg)
    messagebox.showinfo(t("Unlocked"),msg)
    refresh_all()
def delete_all_skins():
    import os
    folder_path=current_save_path
    if not folder_path:
        messagebox.showerror(t("Error"),t("guild.rebuild.no_save"))
        return
    global loaded_level_json
    removed_level_skins=0
    def clean_level_skins(data):
        nonlocal removed_level_skins
        if isinstance(data,dict):
            if "SkinName" in data:
                del data["SkinName"]
                removed_level_skins+=1
            if "SkinAppliedCharacterId" in data:
                del data["SkinAppliedCharacterId"]
            for v in list(data.values()):
                clean_level_skins(v)
        elif isinstance(data,list):
            for item in data:
                clean_level_skins(item)
    try:
        wsd=loaded_level_json["properties"]["worldSaveData"]["value"]
        clean_level_skins(wsd)
    except:
        pass
    players_dir=os.path.join(current_save_path,"Players")
    fixed_player_files=0
    if os.path.exists(players_dir):
        for filename in os.listdir(players_dir):
            if filename.endswith(".sav") and "_dps" not in filename:
                file_path=os.path.join(players_dir,filename)
                try:
                    p_json=sav_to_json(file_path)
                    changed=False
                    def remove_skin_info(data):
                        nonlocal changed
                        if isinstance(data,dict):
                            if "SkinInventoryInfo" in data:
                                del data["SkinInventoryInfo"]
                                changed=True
                            for v in list(data.values()):
                                remove_skin_info(v)
                        elif isinstance(data,list):
                            for item in data:
                                remove_skin_info(item)
                    remove_skin_info(p_json)
                    if changed:
                        json_to_sav(p_json,file_path)
                        fixed_player_files+=1
                except:
                    pass
    msg=t("deletion.menu.remove_invalid_skins_summary",removed_level_skins=removed_level_skins,fixed_player_files=fixed_player_files)
    print(msg)
    refresh_all()
def delete_invalid_structure_map_objects():
    global loaded_level_json
    import json, os
    valid_assets = set()
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        fp = os.path.join(base_dir, "resources", "game_data", "structuredata.json")
        with open(fp, "r", encoding="utf-8") as f:
            js = json.load(f)
            for x in js.get("structures", []):
                asset = x.get("asset")
                if isinstance(asset, str):
                    valid_assets.add(asset.lower())
    except:
        pass
    wsd = loaded_level_json['properties']['worldSaveData']['value']
    map_objs = wsd['MapObjectSaveData']['value']['values']
    initial_count = len(map_objs)
    new_map_objs = []
    for m in map_objs:
        object_id_node = m.get('MapObjectId', {})
        object_name = object_id_node.get('value')
        if isinstance(object_name, str) and object_name.lower() in valid_assets:
            new_map_objs.append(m)
        else:
            instance_id = m.get('Model', {}).get('value', {}).get('RawData', {}).get('value', {}).get('instance_id', 'UNKNOWN_ID')
            print(f"Removing invalid structure: {object_name} (ID: {instance_id})")
    deleted_count = initial_count - len(new_map_objs)
    map_objs[:] = new_map_objs
    print(t("deletion.menu.remove_invalid_structures_summary", deleted_count=deleted_count, remaining_count=len(map_objs)))
    refresh_all()
    refresh_stats("After")
    return deleted_count
def remove_invalid_raw_items_from_level():
    import json,os
    folder_path=current_save_path
    if not folder_path:
        messagebox.showerror(t("Error"),t("guild.rebuild.no_save"))
        return
    global loaded_level_json
    try:
        wsd=loaded_level_json["properties"]["worldSaveData"]["value"]
    except:
        messagebox.showerror(t("Error"),t("itemclean.invalid_structure"))
        return
    valid_items=set()
    try:
        base_dir=os.path.dirname(os.path.abspath(__file__))
        fp=os.path.join(base_dir,"resources","game_data","itemdata.json")
        with open(fp,"r",encoding="utf-8") as f:
            js=json.load(f)
            for x in js.get("items",[]):
                aid=x.get("asset")
                if isinstance(aid,str):
                    valid_items.add(aid.lower())
    except:
        pass
    removed_count=0
    def clean_recursive(data):
        nonlocal removed_count
        if isinstance(data,dict):
            for key in list(data.keys()):
                val=data[key]
                if isinstance(val, (dict, list)):
                    clean_recursive(val)
        elif isinstance(data,list):
            i=len(data)-1
            while i>=0:
                item_obj=data[i]
                if isinstance(item_obj,dict) and "RawData" in item_obj:
                    raw_val=item_obj["RawData"].get("value",{})
                    sid=None
                    if isinstance(raw_val,dict):
                        if "item" in raw_val and isinstance(raw_val["item"],dict):
                            sid=raw_val["item"].get("static_id")
                        elif "id" in raw_val and isinstance(raw_val["id"],dict):
                            sid=raw_val["id"].get("static_id")
                    if isinstance(sid,str) and sid.lower() not in valid_items:
                        print(f"Removing invalid item object: {sid}")
                        data.pop(i)
                        removed_count+=1
                    else:
                        clean_recursive(item_obj)
                else:
                    clean_recursive(item_obj)
                i-=1
    clean_recursive(wsd)
    msg=f"Cleaned Level.sav: Removed {removed_count} invalid item data blocks."
    print(msg)
    refresh_all()
def remove_invalid_items_from_save():
    import json,os
    folder_path=current_save_path
    if not folder_path:
        messagebox.showerror(t("Error"),t("guild.rebuild.no_save"))
        return
    valid_items=set()
    try:
        base_dir=os.path.dirname(os.path.abspath(__file__))
        fp=os.path.join(base_dir,"resources","game_data","itemdata.json")
        with open(fp,"r",encoding="utf-8") as f:
            js=json.load(f)
            for x in js.get("items",[]):
                aid=x.get("asset")
                if isinstance(aid,str):
                    valid_items.add(aid.lower())
    except:
        pass
    players_dir=os.path.join(current_save_path,"Players")
    if not os.path.exists(players_dir):
        messagebox.showerror(t("Error"),t("missions.players_folder_not_found",path=current_save_path))
        return
    total_files=0
    fixed_files=0
    def clean_craft_records(data,filename):
        changed=False
        if isinstance(data,dict):
            if "CraftItemCount" in data and isinstance(data["CraftItemCount"].get("value"),list):
                old_list=data["CraftItemCount"]["value"]
                new_list=[]
                for i in old_list:
                    key=i.get("key")
                    if isinstance(key,str) and key.lower() in valid_items:
                        new_list.append(i)
                    else:
                        print(f"[{filename}] Removed invalid craft record: {key}")
                        changed=True
                if changed:
                    data["CraftItemCount"]["value"]=new_list
            for v in data.values():
                if clean_craft_records(v,filename):changed=True
        elif isinstance(data,list):
            for item in data:
                if clean_craft_records(item,filename):changed=True
        return changed
    for filename in os.listdir(players_dir):
        if filename.endswith(".sav") and "_dps" not in filename:
            total_files+=1
            file_path=os.path.join(players_dir,filename)
            try:
                p_json=sav_to_json(file_path)
                if clean_craft_records(p_json,filename):
                    json_to_sav(p_json,file_path)
                    fixed_files+=1
                    print(f"Successfully updated craft list for {filename}")
            except Exception as e:
                print(f"Error processing player file {filename}: {e}")
    result_msg=f"Processed {total_files} player files. Updated {fixed_files} files."
    print(result_msg)
    refresh_all()
    remove_invalid_raw_items_from_level()
def remove_invalid_pals_from_save():
    def load_assets(fname,key):
        try:
            base_dir=os.path.dirname(os.path.abspath(__file__))
            fp=os.path.join(base_dir,"resources","game_data",fname)
            with open(fp,"r",encoding="utf-8") as f:
                data=json.load(f)
                return set(x["asset"].lower() for x in data.get(key,[]))
        except:
            return set()
    valid_pals=load_assets("paldata.json","pals")
    valid_npcs=load_assets("npcdata.json","npcs")
    valid_all=valid_pals|valid_npcs
    folder_path=current_save_path
    if not folder_path:
        messagebox.showerror(t("Error"),t("guild.rebuild.no_save"))
        return
    global loaded_level_json
    try:
        wsd=loaded_level_json["properties"]["worldSaveData"]["value"]
    except:
        messagebox.showerror(t("Error"),t("palclean.invalid_structure"))
        return
    cmap=wsd.get("CharacterSaveParameterMap",{}).get("value",[])
    removed_ids=set()
    removed=0
    def get_char_id(e):
        try:
            return e["value"]["RawData"]["value"]["object"]["SaveParameter"]["value"]["CharacterID"]["value"]
        except:
            return None
    filtered=[]
    for entry in cmap:
        cid=get_char_id(entry)
        if cid and cid.lower() not in valid_all:
            inst=str(entry["key"]["InstanceId"]["value"])
            removed_ids.add(inst)
            removed+=1
            print(t("palclean.removed_invalid",cid=cid))
            continue
        filtered.append(entry)
    wsd["CharacterSaveParameterMap"]["value"]=filtered
    containers=wsd.get("CharacterContainerSaveData",{}).get("value",[])
    for cont in containers:
        try:
            slots=cont["value"]["Slots"]["value"]["values"]
        except:
            continue
        newslots=[]
        for s in slots:
            inst=s.get("RawData",{}).get("value",{}).get("instance_id")
            if inst and str(inst) in removed_ids:
                continue
            newslots.append(s)
        cont["value"]["Slots"]["value"]["values"]=newslots
    msg=t("palclean.summary",removed=removed)
    refresh_all()
    refresh_stats("After")
    print(msg)
    messagebox.showinfo(t("AutoCleaner"),msg)
def fix_missions():
    folder_path=current_save_path
    if not folder_path:
        messagebox.showerror(t("Error"),t("guild.rebuild.no_save"))
        return
    save_path=os.path.join(current_save_path,"Players")
    if not os.path.exists(save_path):
        messagebox.showerror(t("Error"),t("missions.players_folder_not_found",path=current_save_path))
        return
    total=0
    fixed=0
    skipped=0
    def deep_delete_completed_quest_array(data):
        found=False
        if isinstance(data,dict):
            if "CompletedQuestArray" in data:
                data["CompletedQuestArray"]["value"]["values"]=[]
                return True
            for v in data.values():
                if deep_delete_completed_quest_array(v):
                    found=True
        elif isinstance(data,list):
            for item in data:
                if deep_delete_completed_quest_array(item):
                    found=True
        return found
    for filename in os.listdir(save_path):
        if filename.endswith(".sav") and "_dps" not in filename:
            total+=1
            file_path=os.path.join(save_path,filename)
            try:
                player_json=sav_to_json(file_path)
            except Exception as e:
                skipped+=1
                print(t("missions.unreadable",file=filename,err=e))
                continue
            if deep_delete_completed_quest_array(player_json):
                try:
                    json_to_sav(player_json,file_path)
                    fixed+=1
                    print(t("missions.reset",file=filename))
                except Exception as e:
                    skipped+=1
                    print(t("missions.save_failed",file=filename,err=e))
            else:
                skipped+=1
                print(t("missions.no_array",file=filename))
    result_msg=t("missions.summary",total=total,fixed=fixed,skipped=skipped)
    print(result_msg)
    messagebox.showinfo(t("missions.reset_title"),result_msg)
    refresh_all()
def move_selected_player_to_selected_guild():
    if not current_save_path or not loaded_level_json:
        messagebox.showerror("Error",t("guild.rebuild.no_save"))
        return
    sel_player=player_tree.selection()
    sel_guild=guild_tree.selection()
    if not sel_player:
        messagebox.showerror("Error",t("guild.move.no_player"))
        return
    if not sel_guild:
        messagebox.showerror("Error",t("guild.common.select_guild_first"))
        return
    player_uid_raw = player_tree.item(sel_player[0])['values'][4]
    player_uid = player_uid_raw.replace('-', '')
    target_gid_raw = guild_tree.item(sel_guild[0])['values'][1]
    target_gid=target_gid_raw.replace('-','')
    wsd=loaded_level_json['properties']['worldSaveData']['value']
    group_map=wsd['GroupSaveDataMap']['value']
    base_list=wsd.get('BaseCampSaveData',{}).get('value',[])
    def nu(x): return str(x).replace('-','').lower()
    zero=UUID.from_str("00000000-0000-0000-0000-000000000000")
    origin_group=target_group=found=None
    for g in group_map:
        try:
            if g['value']['GroupType']['value']['value']!="EPalGroupType::Guild":
                continue
            raw=g['value']['RawData']['value']
            if nu(g['key'])==target_gid:
                target_group=g
            for p in raw.get('players',[]):
                if nu(p.get('player_uid',''))==player_uid:
                    origin_group=g
                    found=p
        except:
            pass
    if not found:
        messagebox.showerror(t("Error"), t("guild.move.player_not_found"))
        return
    if not target_group:
        messagebox.showerror(t("Error"), t("guild.move.target_missing"))
        return
    if origin_group is target_group:
        messagebox.showinfo(t("Info"), t("guild.move.already_in_guild"))
        return
    origin_raw=origin_group['value']['RawData']['value']
    newplayers=[p for p in origin_raw.get('players',[]) if nu(p.get('player_uid',''))!=player_uid]
    origin_raw['players']=newplayers
    if not newplayers:
        gid=origin_group['key']
        for b in base_list[:]:
            try:
                if are_equal_uuids(b['value']['RawData']['value'].get('group_id_belong_to'),gid):
                    delete_base_camp(b,gid,loaded_level_json)
            except:
                pass
        group_map.remove(origin_group)
    else:
        admin=nu(origin_raw.get('admin_player_uid',''))
        if admin not in {nu(p['player_uid']) for p in newplayers}:
            origin_raw['admin_player_uid']=newplayers[0]['player_uid']
    target_raw=target_group['value']['RawData']['value']
    tplayers=target_raw.get('players',[])
    if all(nu(p['player_uid'])!=player_uid for p in tplayers):
        tplayers.append(found)
    target_raw['players']=tplayers
    if nu(target_raw.get('admin_player_uid','')) not in {nu(p['player_uid']) for p in tplayers}:
        target_raw['admin_player_uid']=found['player_uid']
    new_gid_obj=target_raw['group_id']
    cmap=wsd['CharacterSaveParameterMap']['value']
    moved_instance_ids=[]
    for character in cmap:
        try:
            raw=character['value']['RawData']['value']
            sp=raw['object']['SaveParameter']['value']
            if nu(sp.get('OwnerPlayerUId',{}).get('value'))==player_uid:
                inst=character['key']['InstanceId']['value']
                moved_instance_ids.append(inst)
                raw['group_id']=new_gid_obj
                sp['OwnerPlayerUId']['value']=found['player_uid']
                try: sp["WorkRegion"]["group_id"]["value"]=zero
                except: pass
                try: sp["WorkerID"]["value"]=zero
                except: pass
                try:
                    if "TaskData" in sp: sp["TaskData"]["value"]={}
                except: pass
                try:
                    if "MapObjectConcreteInstanceIdAssignedToExpedition" in sp:
                        del sp["MapObjectConcreteInstanceIdAssignedToExpedition"]
                except: pass
                try: del sp["WorkSuitabilityOptionInfo"]
                except: pass
        except:
            pass
    for entry in group_map:
        try:
            raw=entry["value"]["RawData"]["value"]
            if raw.get("group_id")!=new_gid_obj:
                continue
            handles=raw.get("individual_character_handle_ids")
            if not isinstance(handles,list):
                handles=[]
                raw["individual_character_handle_ids"]=handles
            for inst in moved_instance_ids:
                try:
                    handles.append({"guid":zero,"instance_id":inst})
                except:
                    pass
            break
        except:
            pass
    refresh_all()
    refresh_stats("After")
    messagebox.showinfo(t("Done"), t("guild.move.moved", player=player_uid_raw, guild=target_gid_raw))
def rebuild_all_players_pals():
    global loaded_level_json,current_save_path
    try:
        wsd=loaded_level_json["properties"]["worldSaveData"]["value"]
        cmap=wsd["CharacterSaveParameterMap"]["value"]
        containers=wsd["CharacterContainerSaveData"]["value"]
        gmap=wsd["GroupSaveDataMap"]["value"]
        mapobjs=wsd.get("MapObjectSaveData",{}).get("value",{}).get("values",[])
    except:
        return False
    zero=UUID.from_str("00000000-0000-0000-0000-000000000000")
    used_ids={str(ch["key"]["InstanceId"]["value"]) for ch in cmap if "key" in ch}
    def bump_guid_str(s):
        v=str(s).lower()
        t=str.maketrans("0123456789abcdef","123456789abcdef0")
        bumped=v.translate(t)
        while bumped in used_ids:
            bumped=bumped.translate(t)
        used_ids.add(bumped)
        return bumped
    players_folder=os.path.join(current_save_path,"Players")
    if not os.path.isdir(players_folder): return False
    real_players={p.get("player_uid") for g in gmap for p in g.get("value",{}).get("RawData",{}).get("value",{}).get("players",[]) if p.get("player_uid")}
    id_map={}
    new_params=[]
    for ch in cmap:
        try:
            raw=ch["value"]["RawData"]["value"]
            sp=raw["object"]["SaveParameter"]["value"]
            owner=sp["OwnerPlayerUId"]["value"]
            if owner not in real_players: continue
        except:
            continue
        cp=fast_deepcopy(ch)
        old_inst=cp["key"]["InstanceId"]["value"]
        new_inst=UUID.from_str(bump_guid_str(old_inst))
        id_map[str(old_inst)]=new_inst
        cp["key"]["InstanceId"]["value"]=new_inst
        raw2=cp["value"]["RawData"]["value"]
        sp2=raw2["object"]["SaveParameter"]["value"]
        sp2["OwnerPlayerUId"]["value"]=owner
        gid=next((g["value"]["RawData"]["value"].get("group_id") for g in gmap for p in g["value"]["RawData"]["value"].get("players",[]) if p.get("player_uid")==owner),zero)
        raw2["group_id"]=gid
        try: sp2["WorkerID"]["value"]=zero
        except: pass
        try: sp2["WorkRegion"]["group_id"]["value"]=zero
        except: pass
        try:
            if "TaskData" in sp2: sp2["TaskData"]["value"]={}
        except: pass
        try: del sp2["WorkSuitabilityOptionInfo"]
        except: pass
        try: del sp2["MapObjectConcreteInstanceIdAssignedToExpedition"]
        except: pass
        new_params.append(cp)
    for c in containers:
        try:
            for s in c["value"]["Slots"]["value"]["values"]:
                inst=s.get("RawData",{}).get("value",{}).get("instance_id")
                if inst and str(inst) in id_map:
                    s["RawData"]["value"]["instance_id"]=id_map[str(inst)]
        except:
            pass
    for m in mapobjs:
        try:
            aid=m["Model"]["value"]["RawData"]["value"].get("assigned_individual_character_handle_id")
            if aid and str(aid["instance_id"]) in id_map:
                aid["instance_id"]=id_map[str(aid["instance_id"])]
        except:
            pass
    for g in gmap:
        try:
            raw=g["value"]["RawData"]["value"]
            for h in raw.get("worker_character_handle_ids",[]):
                if str(h["instance_id"]) in id_map:
                    h["instance_id"]=id_map[str(h["instance_id"])]
            handles=raw.get("individual_character_handle_ids",[])
            handles.clear()
            for n in id_map.values():
                handles.append({"guid":zero,"instance_id":n})
        except:
            pass
    final_cmap=[]
    for ch in cmap:
        try:
            raw=ch["value"]["RawData"]["value"]
            sp=raw["object"]["SaveParameter"]["value"]
            if sp["OwnerPlayerUId"]["value"] in real_players: continue
        except:
            pass
        final_cmap.append(ch)
    final_cmap.extend(new_params)
    wsd["CharacterSaveParameterMap"]["value"]=final_cmap
    return True
def rebuild_all_guilds():
    if not current_save_path or not loaded_level_json:
        messagebox.showerror("Error", t("guild.rebuild.no_save"))
        return
    rebuild_all_players_pals()
    wsd=loaded_level_json['properties']['worldSaveData']['value']
    def nu(x): return str(x).replace('-','').lower()
    zero=UUID.from_str("00000000-0000-0000-0000-000000000000")
    group_map=wsd['GroupSaveDataMap']['value']
    cmap=wsd['CharacterSaveParameterMap']['value']
    guilds={}
    for g in group_map:
        try:
            if g['value']['GroupType']['value']['value']=="EPalGroupType::Guild":
                gid=g['key']
                raw=g['value']['RawData']['value']
                players=raw.get('players',[])
                guilds[nu(gid)]={"gid":gid,"group":g,"players":players,"handles":raw.get("individual_character_handle_ids",[])}
        except:
            pass
    for ginfo in guilds.values():
        g_gid=ginfo["gid"]
        players_clean={nu(p['player_uid']) for p in ginfo["players"]}
        pals=[]
        for ch in cmap:
            try:
                rawf=ch['value']['RawData']['value']
                raw=rawf.get('object',{}).get('SaveParameter',{}).get('value',{})
                owner=raw.get('OwnerPlayerUId',{}).get('value')
                if owner and nu(owner) in players_clean:
                    pals.append(ch)
                    continue
                gid2=rawf.get('group_id')
                if not owner and gid2 and nu(gid2)==nu(g_gid):
                    pals.append(ch)
            except:
                pass
        ginfo["pals"]=pals
    for ginfo in guilds.values():
        gid=ginfo["gid"]
        handles=ginfo["handles"]
        handles.clear()
        existing=set()
        for ch in ginfo["pals"]:
            try:
                inst=ch["key"]["InstanceId"]["value"]
                inst_clean=nu(inst)
                rawf=ch["value"]["RawData"]["value"]
                rawf["group_id"]=gid
                sp=rawf["object"]["SaveParameter"]["value"]
                try: sp["WorkRegion"]["group_id"]["value"]=zero
                except: pass
                try: sp["WorkerID"]["value"]=zero
                except: pass
                try:
                    if "TaskData" in sp: sp["TaskData"]["value"]={}
                except: pass
                try:
                    if "MapObjectConcreteInstanceIdAssignedToExpedition" in sp: del sp["MapObjectConcreteInstanceIdAssignedToExpedition"]
                except: pass
                try: del sp["WorkSuitabilityOptionInfo"]
                except: pass
                if inst_clean not in existing:
                    handles.append({"guid":zero,"instance_id":inst})
                    existing.add(inst_clean)
            except:
                pass
    refresh_all()
    refresh_stats("After")
    messagebox.showinfo("Done", t("guild.rebuild.done"))
def make_selected_member_leader():
    sel=guild_members_tree.selection()
    if not sel: return
    p_name,p_seen,p_level,pal_count,p_uid=guild_members_tree.item(sel[0])['values']
    gsel=guild_tree.selection()
    if not gsel:
        messagebox.showerror("Error",t("guild.common.select_guild_first"))
        return
    guild_name,gid=guild_tree.item(gsel[0])['values']
    wsd=loaded_level_json['properties']['worldSaveData']['value']
    group_data_list=wsd['GroupSaveDataMap']['value']
    old_leader_uid=None
    old_leader_name="Unknown"
    for g in group_data_list:
        if are_equal_uuids(g['key'],gid):
            raw=g['value']['RawData']['value']
            old_leader_uid=raw.get('admin_player_uid')
            break
    if old_leader_uid:
        for child in guild_members_tree.get_children():
            vals=guild_members_tree.item(child)['values']
            if vals and vals[4]==old_leader_uid:
                old_leader_name=vals[0]
                break
    for g in group_data_list:
        if are_equal_uuids(g['key'],gid):
            raw=g['value']['RawData']['value']
            raw['admin_player_uid']=p_uid
            break
    refresh_all()
    refresh_stats("After")
    messagebox.showinfo(t("guild.leader_updated.title"),t("guild.leader_updated.msg").format(old=old_leader_name,new=p_name))
def rename_guild():
    sel = guild_tree.selection()
    src = "guild"
    if not sel:
        sel = player_tree.selection()
        src = "player"
    if not sel:
        messagebox.showerror(t("error.title"), t("guild.rename.select"))
        return
    vals = guild_tree.item(sel[0])['values'] if src == "guild" else player_tree.item(sel[0])['values']
    old_name = vals[0] if src == "guild" else vals[5]
    gid = vals[1] if src == "guild" else vals[6]
    new_name = ask_string_with_icon(t("guild.rename.title"), t("guild.rename.prompt"), ICON_PATH)
    if not new_name:
        return
    wsd = loaded_level_json['properties']['worldSaveData']['value']
    for g in wsd['GroupSaveDataMap']['value']:
        if are_equal_uuids(g['key'], gid):
            g['value']['RawData']['value']['guild_name'] = new_name
            break
    refresh_all()
    refresh_stats("After")
    messagebox.showinfo(t("guild.rename.done_title"), t("guild.rename.done_msg", old=old_name, new=new_name))
def rename_player():
    sel=guild_members_tree.selection()
    src="guild"
    if not sel:
        sel=player_tree.selection()
        src="player"
    if not sel:
        messagebox.showerror(t("error.title"),t("player.rename.select"))
        return
    vals=(guild_members_tree.item(sel[0])['values'] if src=="guild" else player_tree.item(sel[0])['values'])
    if src=="guild":
        old_name=vals[0]
        p_uid=vals[4]
    else:
        old_name=vals[0]
        p_uid=vals[4]
    new_name=ask_string_with_icon(t("player.rename.title"),t("player.rename.prompt"),ICON_PATH)
    if not new_name:
        return
    p_uid_clean=str(p_uid).replace("-","")
    wsd=loaded_level_json['properties']['worldSaveData']['value']
    for g in wsd['GroupSaveDataMap']['value']:
        raw=g['value']['RawData']['value']
        found=False
        for p in raw.get('players',[]):
            uid=str(p.get('player_uid','')).replace("-","")
            if uid==p_uid_clean:
                p.setdefault('player_info',{})['player_name']=new_name
                found=True
                break
        if found:
            break
    char_map=wsd.get('CharacterSaveParameterMap',{}).get('value',[])
    for entry in char_map:
        raw=entry.get('value',{}).get('RawData',{}).get('value',{})
        sp_val=raw.get('object',{}).get('SaveParameter',{}).get('value',{})
        if sp_val.get("IsPlayer",{}).get("value"):
            uid_obj=entry.get('key',{}).get('PlayerUId',{})
            uid=str(uid_obj.get('value','')).replace("-","") if isinstance(uid_obj,dict) else ""
            if uid==p_uid_clean:
                sp_val.setdefault('NickName',{})['value']=new_name
                break
    refresh_all()
    refresh_stats("After")
    messagebox.showinfo(t("player.rename.done_title"),t("player.rename.done_msg",old=old_name,new=new_name))
def rename_world():
    if not current_save_path or not loaded_level_json:
        tk.messagebox.showerror(t("Error"), t("guild.rebuild.no_save"))
        return
    meta_path=os.path.join(current_save_path,"LevelMeta.sav")
    if not os.path.exists(meta_path): return None
    meta_json=sav_to_json(meta_path)
    old=meta_json["properties"]["SaveData"]["value"].get("WorldName",{}).get("value","Unknown World")
    new_name=ask_string_with_icon(t("world.rename.title"),t("world.rename.prompt",old=old),ICON_PATH,mode="text")
    if new_name:
        meta_json["properties"]["SaveData"]["value"]["WorldName"]["value"]=new_name
        json_to_sav(meta_json,meta_path)
        return new_name
    refresh_all()
    refresh_stats("After")
    return None
def clone_base_complete(loaded_level_json, source_base_id, target_guild_id, offset=(8000, 0, 0)):
    import uuid, copy
    from palworld_save_tools.archive import UUID as PalUUID
    try:
        _deep = fast_deepcopy
    except:
        _deep = copy.deepcopy
    def _s(x):
        return str(x).lower()
    def _new_uuid():
        return PalUUID(uuid.uuid4().bytes)
    def _zero():
        return PalUUID(uuid.UUID("00000000-0000-0000-0000-000000000000").bytes)
    def _clear_char_container_slots(container_obj):
        try:
            container_obj["value"]["Slots"]["value"]["values"] = []
        except:
            pass
    def _iter_work_savedata_entries(work_root):
        if not isinstance(work_root, dict): return []
        v = work_root.get("value", {})
        if isinstance(v, dict): return v.get("values", []) if isinstance(v.get("values", []), list) else []
        return []
    def _get_work_raw(work_entry):
        try: return work_entry["RawData"]["value"]
        except: return None
    def _get_model_raw(map_obj):
        try: return map_obj["Model"]["value"]["RawData"]["value"]
        except: return None
    def _get_concrete_raw(map_obj):
        try: return map_obj["ConcreteModel"]["value"]["RawData"]["value"]
        except: return None
    def _offset_translation(t):
        try:
            t["x"] += offset[0]
            t["y"] += offset[1]
            t["z"] += offset[2] if len(offset) > 2 else 0
        except: pass
    raw_prop = loaded_level_json["properties"]["worldSaveData"]["value"]
    data = raw_prop if isinstance(raw_prop, dict) else {}
    groups = data.get("GroupSaveDataMap", {}).get("value", [])
    base_camp_data = data.get("BaseCampSaveData", {}).get("value", [])
    char_containers = data.get("CharacterContainerSaveData", {}).get("value", [])
    item_containers = data.get("ItemContainerSaveData", {}).get("value", [])
    map_objs = data.get("MapObjectSaveData", {}).get("value", {}).get("values", [])
    char_map = data.get("CharacterSaveParameterMap", {}).get("value", [])
    work_root = data.get("WorkSaveData", {})
    z = _zero()
    src_id_str = _s(source_base_id)
    tgt_gid_str = _s(target_guild_id)
    src_base_entry = next((b for b in base_camp_data if _s(b.get("key")) == src_id_str), None)
    if not src_base_entry:
        return False
    try:
        src_worker_container_id = _s(src_base_entry["value"]["WorkerDirector"]["value"]["RawData"]["value"]["container_id"])
    except:
        return False
    palbox_model_id = None
    for obj in map_objs:
        if obj.get("MapObjectId", {}).get("value", "") == "PalBoxV2":
            mr = _get_model_raw(obj)
            if mr and _s(mr.get("base_camp_id_belong_to", "")) == src_id_str:
                palbox_model_id = _s(mr.get("instance_id", ""))
                break
    instance_id_map = {}
    concrete_id_map = {}
    for obj in map_objs:
        mr = _get_model_raw(obj)
        if not isinstance(mr, dict) or _s(mr.get("base_camp_id_belong_to","")) != src_id_str: continue
        oid = str(obj.get("MapObjectId", {}).get("value", ""))
        if oid.startswith("PalEgg") and "Hatching" not in oid and "Incubator" not in oid: continue
        old_inst = _s(mr.get("instance_id",""))
        if not old_inst or old_inst == _s(z): continue
        instance_id_map[old_inst] = _new_uuid()
        old_conc = _s(mr.get("concrete_model_instance_id",""))
        if old_conc and old_conc != _s(z): concrete_id_map[old_conc] = _new_uuid()
    if palbox_model_id and palbox_model_id not in instance_id_map:
        instance_id_map[palbox_model_id] = _new_uuid()
    new_base_id = _new_uuid()
    new_worker_container_id = _new_uuid()
    new_palbox_inst_id = instance_id_map.get(palbox_model_id)
    work_entries = _iter_work_savedata_entries(work_root)
    cloned_works = []
    new_work_ids_for_collection = []
    work_id_map = {}
    source_work_entries = [we for we in work_entries if (wr := _get_work_raw(we)) and _s(wr.get("base_camp_id_belong_to", "")) == src_id_str]
    for we in source_work_entries:
        nwe = _deep(we)
        nwr = _get_work_raw(nwe)
        old_w_id = _s(nwr["id"])
        nw_id = _new_uuid()
        work_id_map[old_w_id] = nw_id
        nwr["id"] = nw_id
        nwr["base_camp_id_belong_to"] = new_base_id
        if "WorkAssignMap" in nwe: nwe["WorkAssignMap"]["value"] = []
        old_om = _s(nwr.get("owner_map_object_model_id", ""))
        if old_om in instance_id_map: nwr["owner_map_object_model_id"] = instance_id_map[old_om]
        old_oc = _s(nwr.get("owner_map_object_concrete_model_id", ""))
        if old_oc in concrete_id_map: nwr["owner_map_object_concrete_model_id"] = concrete_id_map[old_oc]
        for key in ["cached_base_camp_id", "cached_base_camp_ptr", "cached_base_index"]: nwr.pop(key, None)
        try:
            tr = nwr.get("transform", {})
            mid = _s(tr.get("map_object_instance_id",""))
            if mid in instance_id_map: tr["map_object_instance_id"] = instance_id_map[mid]
            if "translation" in tr: _offset_translation(tr["translation"])
        except: pass
        cloned_works.append(nwe)
        new_work_ids_for_collection.append(nw_id)
    nb = _deep(src_base_entry)
    nb["key"] = new_base_id
    try:
        nb_raw = nb["value"]["RawData"]["value"]
        nb_raw["id"] = new_base_id
        nb_raw["group_id_belong_to"] = target_guild_id
    except: pass
    try:
        nb["value"]["WorkerDirector"]["value"]["RawData"]["value"]["id"] = new_base_id
        nb["value"]["WorkerDirector"]["value"]["RawData"]["value"]["container_id"] = new_worker_container_id
        _offset_translation(nb["value"]["WorkerDirector"]["value"]["RawData"]["value"]["spawn_transform"]["translation"])
    except: pass
    try:
        nb["value"]["WorkCollection"]["value"]["RawData"]["value"]["id"] = new_base_id
        nb["value"]["WorkCollection"]["value"]["RawData"]["value"]["work_ids"] = new_work_ids_for_collection
    except: pass
    if new_palbox_inst_id:
        try: nb["value"]["RawData"]["value"]["owner_map_object_instance_id"] = new_palbox_inst_id
        except: pass
    try: _offset_translation(nb["value"]["RawData"]["value"]["transform"]["translation"])
    except: pass
    base_camp_data.append(nb)
    target_group = next((g for g in groups if _s(g.get("key")) == tgt_gid_str), None)
    if target_group:
        try:
            t_raw = target_group["value"]["RawData"]["value"]
            if new_base_id not in t_raw.get("base_ids", []): t_raw.setdefault("base_ids", []).append(new_base_id)
            if new_palbox_inst_id: t_raw.setdefault("map_object_instance_ids_base_camp_points", []).append(new_palbox_inst_id)
        except: pass
    src_worker_container = next((c for c in char_containers if _s(c.get("key",{}).get("ID",{}).get("value")) == src_worker_container_id), None)
    worker_id_map = {}
    if src_worker_container:
        ncnt = _deep(src_worker_container)
        ncnt["key"]["ID"]["value"] = new_worker_container_id
        if "instance_id" in ncnt.get("value", {}): ncnt["value"]["instance_id"] = new_worker_container_id
        old_slots = ncnt["value"]["Slots"]["value"].get("values", [])
        new_slots = []
        for slot in old_slots:
            s_raw = slot.get("RawData", {}).get("value", {})
            old_inst = _s(s_raw.get("instance_id", z))
            if old_inst != _s(z):
                new_inst = _new_uuid()
                worker_id_map[old_inst] = new_inst
                s_raw["instance_id"] = new_inst
                new_slots.append(slot)
        ncnt["value"]["Slots"]["value"]["values"] = new_slots
        char_containers.append(ncnt)
    for old_iid, new_iid in worker_id_map.items():
        char_entry = next((c for c in char_map if _s(c["key"]["InstanceId"]["value"]) == old_iid), None)
        if char_entry:
            n_char = _deep(char_entry)
            n_char["key"]["InstanceId"]["value"] = new_iid
            try:
                c_raw = n_char["value"]["RawData"]["value"]
                c_raw["group_id"] = target_guild_id
                spv = c_raw["object"]["SaveParameter"]["value"]
                spv["SlotId"]["value"]["ContainerId"]["value"]["ID"]["value"] = new_worker_container_id
                if "WorkRegion" in spv: spv["WorkRegion"]["value"]["group_id"]["value"] = z
                if "WorkerID" in spv: spv["WorkerID"]["value"] = z
                if "TaskData" in spv: spv["TaskData"]["value"] = {}
                if "MapObjectConcreteInstanceIdAssignedToExpedition" in spv: spv["MapObjectConcreteInstanceIdAssignedToExpedition"]["value"] = z
            except: pass
            char_map.append(n_char)
            if target_group:
                try: 
                    target_group["value"]["RawData"]["value"].setdefault("individual_character_handle_ids", []).append({"guid": z, "instance_id": new_iid})
                except: pass
    for nwe in cloned_works:
        work_entries.append(nwe)
    for obj in list(map_objs):
        mr = _get_model_raw(obj)
        if not isinstance(mr, dict) or _s(mr.get("base_camp_id_belong_to","")) != src_id_str: continue
        old_inst = _s(mr.get("instance_id",""))
        if old_inst not in instance_id_map: continue
        oid = str(obj.get("MapObjectId", {}).get("value", ""))
        if oid.startswith("PalEgg") and "Hatching" not in oid and "Incubator" not in oid: continue
        no = _deep(obj)
        nmr = _get_model_raw(no)
        new_inst = instance_id_map[old_inst]
        old_conc = _s(nmr.get("concrete_model_instance_id",""))
        new_conc = concrete_id_map.get(old_conc, _new_uuid())
        nmr["instance_id"] = new_inst
        nmr["concrete_model_instance_id"] = new_conc
        nmr["base_camp_id_belong_to"] = new_base_id
        nmr["group_id_belong_to"] = target_guild_id
        try: _offset_translation(nmr["initital_transform_cache"]["translation"])
        except: pass
        cr = _get_concrete_raw(no)
        if isinstance(cr, dict):
            cr["instance_id"] = new_conc
            cr["model_instance_id"] = new_inst
            cr["base_camp_id"] = new_base_id
            if cr.get("concrete_model_type") == "PalMapObjectBreedFarmModel":
                cr["spawned_egg_instance_ids"] = []
            try:
                mm = no["ConcreteModel"]["value"]["ModuleMap"]["value"]
                for mod in mm:
                    raw_mod = mod.get("value", {}).get("RawData", {}).get("value", {})
                    if "target_work_id" in raw_mod:
                        old_twid = _s(raw_mod["target_work_id"])
                        if old_twid in work_id_map: raw_mod["target_work_id"] = work_id_map[old_twid]
                    if "work_ids" in raw_mod and isinstance(raw_mod["work_ids"], list):
                        raw_mod["work_ids"] = [work_id_map.get(_s(wid), wid) for wid in raw_mod["work_ids"]]
                    if "target_container_id" not in raw_mod: continue
                    old_cid = _s(raw_mod.get("target_container_id", ""))
                    new_cid = _new_uuid()
                    raw_mod["target_container_id"] = new_cid
                    if "ItemContainer" in str(mod.get("key", "")):
                        src_ic = next((c for c in item_containers if _s(c.get("key",{}).get("ID",{}).get("value")) == old_cid), None)
                        if src_ic:
                            nic = _deep(src_ic)
                            nic["key"]["ID"]["value"] = new_cid
                            if "instance_id" in nic.get("value", {}): nic["value"]["instance_id"] = new_cid
                            item_containers.append(nic)
                    elif "CharacterContainer" in str(mod.get("key", "")):
                        src_cc = next((c for c in char_containers if _s(c.get("key",{}).get("ID",{}).get("value")) == old_cid), None)
                        if src_cc:
                            ncc = _deep(src_cc)
                            ncc["key"]["ID"]["value"] = new_cid
                            if "instance_id" in ncc.get("value", {}): ncc["value"]["instance_id"] = new_cid
                            _clear_char_container_slots(ncc)
                            char_containers.append(ncc)
            except: pass
        map_objs.append(no)
    return True
def export_base_json(loaded_level_json, source_base_id):
    import copy
    def _s(x): return str(x).lower()
    def _get_model_raw(map_obj):
        try: return map_obj["Model"]["value"]["RawData"]["value"]
        except: return None
    def _iter_work_savedata_entries(work_root):
        if not isinstance(work_root, dict): return []
        v = work_root.get("value", {})
        if isinstance(v, dict): return v.get("values", []) if isinstance(v.get("values", []), list) else []
        return []
    def _get_work_raw(work_entry):
        try: return work_entry["RawData"]["value"]
        except: return None
    raw_prop=loaded_level_json["properties"]["worldSaveData"]["value"]
    data=raw_prop if isinstance(raw_prop,dict) else {}
    base_camp_data=data.get("BaseCampSaveData",{}).get("value",[])
    char_containers=data.get("CharacterContainerSaveData",{}).get("value",[])
    item_containers=data.get("ItemContainerSaveData",{}).get("value",[])
    map_objs=data.get("MapObjectSaveData",{}).get("value",{}).get("values",[])
    char_map=data.get("CharacterSaveParameterMap",{}).get("value",[])
    work_root=data.get("WorkSaveData",{})
    work_entries=_iter_work_savedata_entries(work_root)
    src_id_str=_s(source_base_id)
    src_base_entry=next((b for b in base_camp_data if _s(b.get("key"))==src_id_str),None)
    if not src_base_entry: return None
    export_data={"base_camp":copy.deepcopy(src_base_entry),"map_objects":[],"characters":[],"item_containers":[],"char_containers":[],"works":[]}
    try:
        src_worker_container_id=_s(src_base_entry["value"]["WorkerDirector"]["value"]["RawData"]["value"]["container_id"])
        w_cont=next((c for c in char_containers if _s(c.get("key",{}).get("ID",{}).get("value"))==src_worker_container_id),None)
        if w_cont:
            export_data["char_containers"].append(copy.deepcopy(w_cont))
            for slot in w_cont["value"]["Slots"]["value"].get("values",[]):
                char_inst_id=_s(slot.get("RawData",{}).get("value",{}).get("instance_id","00000000-0000-0000-0000-000000000000"))
                char_entry=next((c for c in char_map if _s(c["key"]["InstanceId"]["value"])==char_inst_id),None)
                if char_entry: export_data["characters"].append(copy.deepcopy(char_entry))
    except: pass
    for obj in map_objs:
        mr=_get_model_raw(obj)
        if not isinstance(mr,dict) or _s(mr.get("base_camp_id_belong_to",""))!=src_id_str: continue
        oid=str(obj.get("MapObjectId",{}).get("value",""))
        if oid.startswith("PalEgg") and "Hatching" not in oid and "Incubator" not in oid: continue
        export_data["map_objects"].append(copy.deepcopy(obj))
        try:
            mm=obj["ConcreteModel"]["value"]["ModuleMap"]["value"]
            for mod in mm:
                raw_mod=mod.get("value",{}).get("RawData",{}).get("value",{})
                if "target_container_id" not in raw_mod: continue
                cid=_s(raw_mod.get("target_container_id",""))
                if "ItemContainer" in str(mod.get("key","")):
                    ic=next((c for c in item_containers if _s(c.get("key",{}).get("ID",{}).get("value"))==cid),None)
                    if ic: export_data["item_containers"].append(copy.deepcopy(ic))
                elif "CharacterContainer" in str(mod.get("key","")):
                    cc=next((c for c in char_containers if _s(c.get("key",{}).get("ID",{}).get("value"))==cid),None)
                    if cc: export_data["char_containers"].append(copy.deepcopy(cc))
        except: pass
    for we in work_entries:
        wr=_get_work_raw(we)
        if wr and _s(wr.get("base_camp_id_belong_to",""))==src_id_str: export_data["works"].append(copy.deepcopy(we))
    return export_data
def import_base_json(loaded_level_json, exported_data, target_guild_id, offset=(8000,0,0), collision_threshold=5000):
    import uuid,copy,math
    from palworld_save_tools.archive import UUID as PalUUID
    try:_deep=fast_deepcopy
    except:_deep=copy.deepcopy
    def _s(x): return str(x).lower()
    def _new_uuid(): return PalUUID(uuid.uuid4().bytes)
    def _zero(): return PalUUID(uuid.UUID("00000000-0000-0000-0000-000000000000").bytes)
    def _clear_char_container_slots(container_obj):
        try: container_obj["value"]["Slots"]["value"]["values"]=[]
        except: pass
    def _iter_work_savedata_entries(work_root):
        if not isinstance(work_root,dict): return []
        v=work_root.get("value",{})
        if isinstance(v,dict): return v.get("values",[]) if isinstance(v.get("values",[]),list) else []
        return []
    def _get_work_raw(work_entry):
        try: return work_entry["RawData"]["value"]
        except: return None
    def _get_model_raw(map_obj):
        try: return map_obj["Model"]["value"]["RawData"]["value"]
        except: return None
    def _get_concrete_raw(map_obj):
        try: return map_obj["ConcreteModel"]["value"]["RawData"]["value"]
        except: return None
    def _offset_translation(t, apply_offset):
        if not apply_offset: return
        try:
            t["x"]+=offset[0];t["y"]+=offset[1];t["z"]+=offset[2] if len(offset)>2 else 0
        except: pass
    raw_prop=loaded_level_json["properties"]["worldSaveData"]["value"]
    data=raw_prop if isinstance(raw_prop,dict) else {}
    groups=data.get("GroupSaveDataMap",{}).get("value",[])
    base_camp_data=data.get("BaseCampSaveData",{}).get("value",[])
    char_containers=data.get("CharacterContainerSaveData",{}).get("value",[])
    item_containers=data.get("ItemContainerSaveData",{}).get("value",[])
    map_objs=data.get("MapObjectSaveData",{}).get("value",{}).get("values",[])
    char_map=data.get("CharacterSaveParameterMap",{}).get("value",[])
    work_root=data.get("WorkSaveData",{})
    work_entries=_iter_work_savedata_entries(work_root)
    z=_zero()
    tgt_gid_str=_s(target_guild_id)
    palbox_model_id=None
    for obj in exported_data.get("map_objects",[]):
        if obj.get("MapObjectId",{}).get("value","")=="PalBoxV2":
            mr=_get_model_raw(obj)
            if mr: palbox_model_id=_s(mr.get("instance_id",""));break
    instance_id_map={}
    concrete_id_map={}
    for obj in exported_data.get("map_objects",[]):
        mr=_get_model_raw(obj)
        if not isinstance(mr,dict): continue
        oid=str(obj.get("MapObjectId",{}).get("value",""))
        if oid.startswith("PalEgg") and "Hatching" not in oid and "Incubator" not in oid: continue
        old_inst=_s(mr.get("instance_id",""))
        if not old_inst or old_inst==_s(z): continue
        instance_id_map[old_inst]=_new_uuid()
        old_conc=_s(mr.get("concrete_model_instance_id",""))
        if old_conc and old_conc!=_s(z): concrete_id_map[old_conc]=_new_uuid()
    if palbox_model_id and palbox_model_id not in instance_id_map: instance_id_map[palbox_model_id]=_new_uuid()
    new_base_id=_new_uuid()
    new_worker_container_id=_new_uuid()
    new_palbox_inst_id=instance_id_map.get(palbox_model_id)
    src_base_raw = exported_data["base_camp"]["value"]["RawData"]["value"]
    src_pos = src_base_raw["transform"]["translation"]
    apply_off = False
    for existing_base in base_camp_data:
        try:
            ex_pos = existing_base["value"]["RawData"]["value"]["transform"]["translation"]
            dist = math.sqrt((src_pos["x"]-ex_pos["x"])**2 + (src_pos["y"]-ex_pos["y"])**2 + (src_pos["z"]-ex_pos["z"])**2)
            if dist < collision_threshold:
                apply_off = True
                break
        except: continue
    cloned_works=[]
    new_work_ids_for_collection=[]
    work_id_map={}
    for we in exported_data.get("works",[]):
        nwe=_deep(we)
        nwr=_get_work_raw(nwe)
        if not isinstance(nwr,dict) or "id" not in nwr: continue
        old_w_id=_s(nwr["id"])
        nw_id=_new_uuid()
        work_id_map[old_w_id]=nw_id
        nwr["id"]=nw_id
        nwr["base_camp_id_belong_to"]=new_base_id
        if "WorkAssignMap" in nwe: nwe["WorkAssignMap"]["value"]=[]
        old_om=_s(nwr.get("owner_map_object_model_id",""))
        if old_om in instance_id_map: nwr["owner_map_object_model_id"]=instance_id_map[old_om]
        old_oc=_s(nwr.get("owner_map_object_concrete_model_id",""))
        if old_oc in concrete_id_map: nwr["owner_map_object_concrete_model_id"]=concrete_id_map[old_oc]
        for key in ["cached_base_camp_id","cached_base_camp_ptr","cached_base_index"]: nwr.pop(key,None)
        try:
            tr=nwr.get("transform",{})
            mid=_s(tr.get("map_object_instance_id",""))
            if mid in instance_id_map: tr["map_object_instance_id"]=instance_id_map[mid]
            if "translation" in tr: _offset_translation(tr["translation"], apply_off)
        except: pass
        cloned_works.append(nwe)
        new_work_ids_for_collection.append(nw_id)
    nb=_deep(exported_data["base_camp"])
    nb["key"]=new_base_id
    try:
        nb_raw = nb["value"]["RawData"]["value"]
        nb_raw["id"] = new_base_id
        nb_raw["group_id_belong_to"] = target_guild_id
    except: pass
    try:
        wd_raw = nb["value"]["WorkerDirector"]["value"]["RawData"]["value"]
        wd_raw["id"] = new_base_id
        wd_raw["container_id"] = new_worker_container_id
        _offset_translation(wd_raw["spawn_transform"]["translation"], apply_off)
    except: pass
    try:
        nb["value"]["WorkCollection"]["value"]["RawData"]["value"]["id"] = new_base_id
        nb["value"]["WorkCollection"]["value"]["RawData"]["value"]["work_ids"] = new_work_ids_for_collection
    except: pass
    if new_palbox_inst_id:
        try: nb["value"]["RawData"]["value"]["owner_map_object_instance_id"] = new_palbox_inst_id
        except: pass
    try: _offset_translation(nb["value"]["RawData"]["value"]["transform"]["translation"], apply_off)
    except: pass
    base_camp_data.append(nb)
    target_group=next((g for g in groups if _s(g.get("key"))==tgt_gid_str),None)
    if target_group:
        try:
            t_raw=target_group["value"]["RawData"]["value"]
            if new_base_id not in t_raw.get("base_ids",[]): t_raw.setdefault("base_ids",[]).append(new_base_id)
            if new_palbox_inst_id: t_raw.setdefault("map_object_instance_ids_base_camp_points",[]).append(new_palbox_inst_id)
        except: pass
    worker_id_map={}
    try: src_worker_container_id=_s(exported_data["base_camp"]["value"]["WorkerDirector"]["value"]["RawData"]["value"]["container_id"])
    except: src_worker_container_id=""
    src_worker_container=next((c for c in exported_data.get("char_containers",[]) if _s(c.get("key",{}).get("ID",{}).get("value"))==src_worker_container_id),None)
    if src_worker_container:
        ncnt=_deep(src_worker_container)
        ncnt["key"]["ID"]["value"]=new_worker_container_id
        if "instance_id" in ncnt.get("value",{}): ncnt["value"]["instance_id"]=new_worker_container_id
        old_slots=ncnt["value"]["Slots"]["value"].get("values",[])
        new_slots=[]
        for slot in old_slots:
            s_raw=slot.get("RawData",{}).get("value",{})
            old_inst=_s(s_raw.get("instance_id",z))
            if old_inst!=_s(z):
                new_inst=_new_uuid()
                worker_id_map[old_inst]=new_inst
                s_raw["instance_id"]=new_inst
                new_slots.append(slot)
        ncnt["value"]["Slots"]["value"]["values"]=new_slots
        char_containers.append(ncnt)
    for old_iid,new_iid in worker_id_map.items():
        char_entry=next((c for c in exported_data.get("characters",[]) if _s(c["key"]["InstanceId"]["value"])==old_iid),None)
        if char_entry:
            n_char=_deep(char_entry)
            n_char["key"]["InstanceId"]["value"]=new_iid
            try:
                c_raw=n_char["value"]["RawData"]["value"]
                c_raw["group_id"]=target_guild_id
                spv=c_raw["object"]["SaveParameter"]["value"]
                spv["SlotId"]["value"]["ContainerId"]["value"]["ID"]["value"]=new_worker_container_id
                if "WorkRegion" in spv: spv["WorkRegion"]["value"]["group_id"]["value"]=z
                if "WorkerID" in spv: spv["WorkerID"]["value"]=z
                if "TaskData" in spv: spv["TaskData"]["value"]={}
                if "MapObjectConcreteInstanceIdAssignedToExpedition" in spv: spv["MapObjectConcreteInstanceIdAssignedToExpedition"]["value"]=z
            except: pass
            char_map.append(n_char)
            if target_group:
                try: target_group["value"]["RawData"]["value"].setdefault("individual_character_handle_ids",[]).append({"guid":z,"instance_id":new_iid})
                except: pass
    for nwe in cloned_works: work_entries.append(nwe)
    for obj in exported_data.get("map_objects",[]):
        mr=_get_model_raw(obj)
        if not isinstance(mr,dict): continue
        old_inst=_s(mr.get("instance_id",""))
        if old_inst not in instance_id_map: continue
        oid=str(obj.get("MapObjectId",{}).get("value",""))
        if oid.startswith("PalEgg") and "Hatching" not in oid and "Incubator" not in oid: continue
        no=_deep(obj)
        nmr=_get_model_raw(no)
        new_inst=instance_id_map[old_inst]
        old_conc=_s(nmr.get("concrete_model_instance_id",""))
        new_conc=concrete_id_map.get(old_conc,_new_uuid())
        nmr["instance_id"]=new_inst
        nmr["concrete_model_instance_id"]=new_conc
        nmr["base_camp_id_belong_to"]=new_base_id
        nmr["group_id_belong_to"]=target_guild_id
        try: _offset_translation(nmr["initital_transform_cache"]["translation"], apply_off)
        except: pass
        cr=_get_concrete_raw(no)
        if isinstance(cr,dict):
            cr["instance_id"]=new_conc
            cr["model_instance_id"]=new_inst
            cr["base_camp_id"]=new_base_id
            if cr.get("concrete_model_type")=="PalMapObjectBreedFarmModel": cr["spawned_egg_instance_ids"]=[]
            try:
                mm=no["ConcreteModel"]["value"]["ModuleMap"]["value"]
                for mod in mm:
                    raw_mod=mod.get("value",{}).get("RawData",{}).get("value",{})
                    if "target_work_id" in raw_mod:
                        old_twid=_s(raw_mod["target_work_id"])
                        if old_twid in work_id_map: raw_mod["target_work_id"]=work_id_map[old_twid]
                    if "work_ids" in raw_mod and isinstance(raw_mod["work_ids"],list):
                        raw_mod["work_ids"]=[work_id_map.get(_s(wid),wid) for wid in raw_mod["work_ids"]]
                    if "target_container_id" not in raw_mod: continue
                    old_cid=_s(raw_mod.get("target_container_id",""))
                    new_cid=_new_uuid()
                    raw_mod["target_container_id"]=new_cid
                    if "ItemContainer" in str(mod.get("key", "")):
                        src_ic=next((c for c in exported_data.get("item_containers",[]) if _s(c.get("key",{}).get("ID",{}).get("value"))==old_cid),None)
                        if src_ic:
                            nic=_deep(src_ic)
                            nic["key"]["ID"]["value"]=new_cid
                            if "instance_id" in nic.get("value",{}): nic["value"]["instance_id"]=new_cid
                            item_containers.append(nic)
                    elif "CharacterContainer" in str(mod.get("key", "")):
                        src_cc=next((c for c in exported_data.get("char_containers",[]) if _s(c.get("key",{}).get("ID",{}).get("value"))==old_cid),None)
                        if src_cc:
                            ncc=_deep(src_cc)
                            ncc["key"]["ID"]["value"]=new_cid
                            if "instance_id" in ncc.get("value",{}): ncc["value"]["instance_id"]=new_cid
                            _clear_char_container_slots(ncc)
                            char_containers.append(ncc)
            except: pass
        map_objs.append(no)
    return True
def all_in_one_tools():
    global window, stat_labels, guild_tree, base_tree, player_tree, guild_members_tree
    global guild_search_var, base_search_var, player_search_var, guild_members_search_var
    global guild_result, base_result, player_result
    base_dir = os.path.dirname(os.path.abspath(__file__))
    try:
        import tkinter as tk
        if not hasattr(tk, '_default_root') or tk._default_root is None or not tk._default_root.winfo_exists():
            tk._default_root = tk.Tk()
            tk._default_root.withdraw()
    except:
        pass
    try:
        window = ctk.CTkToplevel()
    except tk.TclError as e:
        if "application has been destroyed" in str(e):
            try:
                tk._default_root = tk.Tk()
                tk._default_root.withdraw()
                window = ctk.CTkToplevel()
            except:
                messagebox.showerror("Error", "Failed to create window: Tkinter root destroyed")
                return None
        else:
            raise
    window.running=True
    try:
        window.iconbitmap(ICON_PATH)
        window.tk.call('wm', 'iconbitmap', '.', ICON_PATH)
    except:
        pass
    window.refresh_elements = {
        'menu_buttons': [],
        'main_labels': [],
        'version_labels': [],
        'treeview_headings': [],
        'notebook_tabs': [],
        'menus': [],
        'search_labels': [],
        'stat_key_labels': []
    }
    def on_language_change_cmd(lang_code):
        set_language(lang_code)
        load_resources(lang_code)
        window.refresh_texts_all_in_one()
    def refresh_texts_all_in_one():
        tools_version, _ = get_versions()
        window.title(t("app.title", version=tools_version) + " - " + t("tool.deletion"))
        for button, key in window.refresh_elements['menu_buttons']:
            button.configure(text=t(key))
        for menu, items in window.refresh_elements['menus']:
            menu.delete(0, 'end')
            for item in items:
                if item['is_separator']:
                    menu.add_separator()
                else:
                    menu.add_command(label=t(item['label_key']), command=item['command'])
        for label, key, fmt in window.refresh_elements['main_labels']:
            label.configure(text=t(key, **fmt))
        info = check_for_update()
        local_version = get_versions()[0]
        for label, key in window.refresh_elements['version_labels']:
            if key == 'update.current':
                label.configure(text=f"{t(key)}: {local_version}")
            elif key == 'update.latest':
                text = f" | {t('update.latest')}: {info['latest']}" if info and not info['update_available'] else f"{t('update.latest')}: {info['latest']}"
                label.configure(text=text)
            elif key == 'pipe_separator':
                label.configure(text=" | ")
        for tree, col_id, key in window.refresh_elements['treeview_headings']:
            tree.heading(col_id, text=t(key))
        for label, key in window.refresh_elements['search_labels']:
            label.configure(text=t(key))
        for label, key in window.refresh_elements['stat_key_labels']:
            label.configure(text=t(key))
        if hasattr(window, 'notebook'):
            for tab_name, key in window.refresh_elements['notebook_tabs']:
                if tab_name in window.notebook._segmented_button._buttons_dict:
                    window.notebook._segmented_button._buttons_dict[tab_name].configure(text=t(key))
    window.refresh_texts_all_in_one = refresh_texts_all_in_one
    window.on_language_change_cmd = on_language_change_cmd
    import webbrowser
    window.title(t("deletion.title"))
    window.geometry("700x500")
    window.minsize(1000, 700)
    font = ("Segoe UI", 10)
    s = ttk.Style(window)
    s.theme_use('clam')
    s.configure("Treeview.Heading", font=FONT_BOLD, background="#3a3a3a", foreground=EMPHASIS_COLOR)
    s.configure("Treeview", background=GLASS_BG, foreground=TEXT_COLOR, fieldbackground=GLASS_BG, rowheight=TREE_ROW_HEIGHT, bordercolor=BORDER_COLOR, focuscolor=GLASS_BG)
    s.map("Treeview", background=[('selected', ACCENT_COLOR)])
    s.layout("Treeview", [('Treeview.treearea', {'sticky': 'nswe'})])
    s.configure("TFrame", background=GLASS_BG)
    s.configure("TLabel", background=GLASS_BG, foreground=TEXT_COLOR)
    s.configure("TEntry", fieldbackground="#444444", foreground=TEXT_COLOR, bordercolor=BORDER_COLOR)
    s.configure("Vertical.TScrollbar", background=GLASS_BG, troughcolor=GLASS_BG, bordercolor=GLASS_BG, arrowcolor=TEXT_COLOR)
    s.map("Vertical.TScrollbar",
              background=[('active', "#444444"), ('!active', GLASS_BG)],
              troughcolor=[('active', GLASS_BG), ('!active', GLASS_BG)],
              arrowcolor=[('active', TEXT_COLOR), ('!active', TEXT_COLOR)],
              bordercolor=[('active', GLASS_BG), ('!active', GLASS_BG)])
    MENU_BG = GLASS_BG
    MENU_FG = TEXT_COLOR
    MENU_ACTIVE_BG = ACCENT_COLOR
    window.columnconfigure(0, weight=1)
    window.rowconfigure(0, weight=0)
    window.rowconfigure(1, weight=0)
    window.rowconfigure(2, weight=1)
    menu_bar_frame = ctk.CTkFrame(window, fg_color="transparent")
    menu_bar_frame.grid(row=0, column=0, sticky="ew", padx=0)
    menu_button_frame=ctk.CTkFrame(menu_bar_frame, fg_color="transparent")
    menu_button_frame.grid(row=0, column=0, sticky="w", padx=0, pady=0)
    menu_bar_frame.columnconfigure(0, weight=0)
    menu_bar_frame.columnconfigure(1, weight=10)
    menu_bar_frame.columnconfigure(2, weight=0)
    menu_bar_frame.columnconfigure(3, weight=10)
    menu_bar_frame.columnconfigure(4, weight=0)
    menu_button_font = ("Segoe UI", 9)    
    def show_menu(event, menu):
        x = event.winfo_rootx()
        y = event.winfo_rooty() + event.winfo_height()
        menu.tk_popup(x, y)
    def create_menu_button(parent, text_key, menu_object):
        button = ctk.CTkButton(
            parent,
            text=t(text_key),
            fg_color=BUTTON_BG,
            hover_color=BUTTON_HOVER,
            width=50,
            height=18,
            corner_radius=0,
            font=menu_button_font
        )
        button.pack(side="left", padx=1, pady=0)
        button.bind("<Button-1>", lambda e: show_menu(button, menu_object))
        window.refresh_elements['menu_buttons'].append((button, text_key))
        return button
    def create_and_store_menu(menu_name):
        menu = tk.Menu(window, tearoff=0, bg=MENU_BG, fg=MENU_FG, activebackground=MENU_ACTIVE_BG, activeforeground=MENU_FG)
        items = []
        def add_item(label_key, command, is_separator=False):
            if is_separator:
                menu.add_separator()
            else:
                menu.add_command(label=t(label_key), command=command)
            items.append({'label_key': label_key, 'command': command, 'is_separator': is_separator})
        return menu, items, add_item
    def populate_exclusions_trees():
        exclusions_guilds_tree.delete(*exclusions_guilds_tree.get_children())
        for gid in exclusions.get("guilds", []):
            exclusions_guilds_tree.insert("", "end", values=(gid,))
        exclusions_players_tree.delete(*exclusions_players_tree.get_children())
        for pid in exclusions.get("players", []):
            exclusions_players_tree.insert("", "end", values=(pid,))
        exclusions_bases_tree.delete(*exclusions_bases_tree.get_children())
        for bid in exclusions.get("bases", []):
            exclusions_bases_tree.insert("", "end", values=(bid,))
    def add_exclusion(source_tree, key):
        sel = source_tree.selection()
        if not sel:
            tk.messagebox.showwarning(t("Warning"), t("deletion.warn.none_selected", kind=key[:-1].capitalize()))
            return
        val = source_tree.item(sel[0])["values"]
        if source_tree == guild_tree:
            val = val[1]
        elif source_tree == player_tree:
            val = val[4]
        elif source_tree == guild_members_tree:
            val = val[4]
        else:
            val = val[0]
        if val not in exclusions[key]:
            exclusions[key].append(val)
            populate_exclusions_trees()
        else:
            tk.messagebox.showinfo(t("Info"), t("deletion.info.already_in_exclusions", kind=key[:-1].capitalize()))
    def remove_selected_exclusion(tree, key):
        sel = tree.selection()
        if not sel: return
        for item_id in sel:
            val = tree.item(item_id)["values"][0]
            if val in exclusions[key]:
                exclusions[key].remove(val)
        populate_exclusions_trees()
    def remove_selected_from_regular(tree, key):
        sel = tree.selection()
        if not sel: return
        for item_id in sel:
            val = tree.item(item_id)["values"]
            if tree == guild_tree:
                val = val[1]
            elif tree == player_tree:
                val = val[4]
            elif tree == guild_members_tree:
                val = val[4]
            else:
                val = val[0]
            if val in exclusions[key]:
                exclusions[key].remove(val)
        populate_exclusions_trees()
    def save_exclusions_func():
        with open("deletion_exclusions.json", "w") as f: json.dump(exclusions, f, indent=4)
        tk.messagebox.showinfo(t("Saved"), t("deletion.saved_exclusions"))
    file_menu, file_menu_items, file_menu_add = create_and_store_menu("file_menu")
    file_menu_add("menu.file.load_save", load_save)
    file_menu_add("menu.file.save_changes", save_changes)
    file_menu_add("menu.file.rename_world", rename_world)    
    window.refresh_elements['menus'].append((file_menu, file_menu_items))
    create_menu_button(menu_button_frame, "deletion.menu.file", file_menu)
    delete_menu, delete_menu_items, delete_menu_add = create_and_store_menu("delete_menu")
    delete_menu_add("deletion.menu.delete_empty_guilds", delete_empty_guilds)
    delete_menu_add("deletion.menu.delete_inactive_bases", delete_inactive_bases)
    delete_menu_add("deletion.menu.delete_duplicate_players", delete_duplicated_players)
    delete_menu_add("deletion.menu.delete_inactive_players", delete_inactive_players_button)
    delete_menu_add("deletion.menu.delete_unreferenced", delete_unreferenced_data)
    delete_menu_add("deletion.menu.delete_non_base_map_objs", delete_non_base_map_objects)
    delete_menu_add("deletion.menu.delete_all_skins", delete_all_skins)    
    delete_menu_add("deletion.menu.unlock_private_chests", unlock_all_private_chests)
    delete_menu_add("deletion.menu.remove_invalid_items", remove_invalid_items_from_save)
    delete_menu_add("deletion.menu.remove_invalid_structures", delete_invalid_structure_map_objects)
    delete_menu_add("deletion.menu.remove_invalid_pals", remove_invalid_pals_from_save)
    delete_menu_add("deletion.menu.reset_missions", fix_missions)
    delete_menu_add("deletion.menu.reset_anti_air", reset_anti_air_turrets)
    delete_menu_add("deletion.menu.reset_dungeons", reset_dungeons)
    delete_menu_add("deletion.menu.generate_killnearestbase", open_kill_nearest_base_ui)
    delete_menu_add("guild.menu.rebuild_all_guilds", rebuild_all_guilds)
    delete_menu_add("guild.menu.move_selected_player_to_selected_guild", move_selected_player_to_selected_guild)
    window.refresh_elements['menus'].append((delete_menu, delete_menu_items))
    create_menu_button(menu_button_frame, "deletion.menu.delete", delete_menu)
    view_menu, view_menu_items, view_menu_add = create_and_store_menu("view_menu")
    view_menu_add("deletion.menu.show_map", show_base_map)
    view_menu_add("deletion.menu.generate_map", generate_map)
    window.refresh_elements['menus'].append((view_menu, view_menu_items))
    create_menu_button(menu_button_frame, "deletion.menu.view", view_menu)
    exclusions_menu, exclusions_menu_items, exclusions_menu_add = create_and_store_menu("exclusions_menu")
    exclusions_menu_add("deletion.menu.save_exclusions", save_exclusions_func)
    window.refresh_elements['menus'].append((exclusions_menu, exclusions_menu_items))
    create_menu_button(menu_button_frame, "deletion.menu.exclusions", exclusions_menu)
    language_menu, language_menu_items, language_menu_add = create_and_store_menu("language_menu")
    LANG_CODES = ["zh_CN","en_US","ru_RU","fr_FR","es_ES","de_DE","ja_JP","ko_KR"]
    def create_lang_command(lang_code):
        return lambda: window.on_language_change_cmd(lang_code)
    for code in LANG_CODES:
        language_menu_add(f'lang.{code}', create_lang_command(code))
    window.refresh_elements['menus'].append((language_menu, language_menu_items))
    create_menu_button(menu_button_frame, "lang.label", language_menu)    
    right_header_frame = ctk.CTkFrame(menu_bar_frame, fg_color="transparent")
    right_header_frame.grid(row=0, column=4, padx=10, pady=0, sticky="e")    
    try:
        from PIL import Image
        logo_image_path = os.path.join(base_dir, "resources", "PalworldSaveTools_Blue.png")
        logo_image = ctk.CTkImage(Image.open(logo_image_path), size=(450, 40))
        logo_label = ctk.CTkLabel(menu_bar_frame, image=logo_image, text="", fg_color="transparent")
        logo_label.grid(row=0, column=2, padx=(0, 10), pady=0, sticky="n")
        logo_label.image = logo_image
    except Exception as e:
        print(f"Error loading logo: {e}")
    info=check_for_update()
    if info:
        latest,local=info["latest"],info["local"]
        update_available=info["update_available"]
        version_frame=ctk.CTkFrame(right_header_frame, fg_color="transparent")
        version_frame.pack(side="top", anchor="e", pady=0, padx=0)
        current_text = f"{t('update.current')}: {local}"
        current_label = ctk.CTkLabel(version_frame, text=current_text, text_color="white", font=("Consolas",11,"bold"), anchor="w")
        current_label.pack(side="left", anchor="w", pady=0, padx=0)
        window.refresh_elements['version_labels'].append((current_label, 'update.current'))
        if not update_available:
            latest_text = f" | {t('update.latest')}: {latest}"
            latest_label = ctk.CTkLabel(version_frame, text=latest_text, text_color="white", font=("Consolas",11,"bold"), anchor="e")
            latest_label.pack(side="right", anchor="e", pady=0, padx=(4, 0))
            window.refresh_elements['version_labels'].append((latest_label, 'update.latest'))
        else:
            pipe_separator = ctk.CTkLabel(version_frame, text=" | ", text_color="white", font=("Consolas",11,"bold"), anchor="e")
            pipe_separator.pack(side="left", anchor="e", pady=0, padx=0)
            window.refresh_elements['version_labels'].append((pipe_separator, 'pipe_separator'))
            update_label = ctk.CTkLabel(
                version_frame,
                text=f"{t('update.latest')}: {latest}",
                text_color="white",
                font=("Consolas",11,"bold", "underline"),
                cursor="hand2"
            )
            update_label.pack(side="right", anchor="e", pady=0, padx=(4, 0))
            window.refresh_elements['version_labels'].append((update_label, 'update.latest'))            
            update_url = "https://github.com/deafdudecomputers/PalworldSaveTools/releases/latest"
            update_label.bind("<Button-1>", lambda e: webbrowser.open(update_url))
            if window.running:
                def pulse_label():
                    if not window.running: return
                    current_color = update_label.cget("text_color")
                    new_color = "red" if current_color == "white" else "white"
                    update_label.configure(text_color=new_color)
                    window.after(800,pulse_label)
                pulse_label()
    result_frame = ctk.CTkFrame(window, fg_color=GLASS_BG, corner_radius=CTK_FRAME_CORNER_RADIUS)
    result_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
    result_frame.grid_propagate(False)
    result_frame.configure(height=110)
    result_frame.columnconfigure(0, weight=1)
    result_frame.columnconfigure(1, weight=0)
    info_container = ctk.CTkFrame(result_frame, fg_color="transparent")
    info_container.grid(row=0, column=0, sticky="nsew", padx=SPACE_MEDIUM, pady=SPACE_MEDIUM)
    info_container.columnconfigure(0, weight=1)
    info_container.columnconfigure(1, weight=0)
    status_label_frame = ctk.CTkFrame(info_container, fg_color="transparent", width=400)
    status_label_frame.grid(row=0, column=0, sticky="nw", padx=(0, SPACE_MEDIUM))
    status_label_frame.columnconfigure(0, weight=1)
    stat_frame, stat_labels, stat_key_labels_to_refresh = create_stats_panel(info_container, s)
    stat_frame.grid(row=0, column=1, sticky="ne")
    font_large = ("Segoe UI", 11)
    player_result = ctk.CTkLabel(status_label_frame, text=t("deletion.selected_player", name="N/A"), font=font_large, anchor="w")
    player_result.grid(row=0, column=0, sticky="w", pady=(0, 2))
    window.refresh_elements['main_labels'].append((player_result, "deletion.selected_player", {"name": "N/A"}))
    guild_result = ctk.CTkLabel(status_label_frame, text=t("deletion.selected_guild", name="N/A"), font=font_large, anchor="w")
    guild_result.grid(row=1, column=0, sticky="w", pady=(0, 2))
    window.refresh_elements['main_labels'].append((guild_result, "deletion.selected_guild", {"name": "N/A"}))
    base_result = ctk.CTkLabel(status_label_frame, text=t("deletion.selected_base", id="N/A"), font=font_large, anchor="w")
    base_result.grid(row=2, column=0, sticky="w")
    window.refresh_elements['main_labels'].append((base_result, "deletion.selected_base", {"id": "N/A"}))
    window.refresh_elements['stat_key_labels'] = stat_key_labels_to_refresh
    notebook = ctk.CTkTabview(window, width=950)
    notebook.grid(row=2, column=0, padx=10, pady=(0, 5), sticky="nsew")
    window.notebook = notebook
    PLAYER_TAB_NAME = "PlayersTab"
    player_tab = notebook.add(PLAYER_TAB_NAME)
    window.refresh_elements['notebook_tabs'].append((PLAYER_TAB_NAME, "deletion.search_players"))
    player_tab.columnconfigure(0, weight=1)
    player_tab.rowconfigure(0, weight=1)
    player_search_var = tk.StringVar()
    pframe, player_tree, player_search_entry, player_search_label = create_search_panel(
        player_tab,
        "deletion.search_players",
        player_search_var,
        on_player_search,
        ("Name", "Last", "Level", "Pals", "UID", "GName", "GID"),
        (
            t("deletion.col.player_name"),
            t("deletion.col.last_seen"),
            t("deletion.col.level"),
            t("deletion.col.pals"),
            "UID",
            t("deletion.col.guild_name"),
            t("deletion.col.guild_id")
        ),
        (140, 120, 60, 60, 150, 180, 180),
        900,
        600,
        tree_height=25
    )
    window.refresh_elements['search_labels'].append((player_search_label, "deletion.search_players"))
    pframe.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
    player_tree.configure(selectmode='browse')
    player_tree.bind("<<TreeviewSelect>>", on_player_select)
    for col, key in zip(
        ("Name", "Last", "Level", "Pals", "UID", "GName", "GID"),
        (
            "deletion.col.player_name",
            "deletion.col.last_seen",
            "deletion.col.level",
            "deletion.col.pals",
            "UID",
            "deletion.col.guild_name",
            "deletion.col.guild_id"
        )
    ):
        player_tree.heading(col, command=lambda c=col: treeview_sort_column(player_tree, c, False))
        window.refresh_elements['treeview_headings'].append((player_tree, col, key))
    GUILD_TAB_NAME = "GuildsTab"
    guild_tab = notebook.add(GUILD_TAB_NAME)
    window.refresh_elements['notebook_tabs'].append((GUILD_TAB_NAME, "deletion.search_guilds"))
    guild_tab.columnconfigure(0, weight=1)
    guild_tab.rowconfigure(0, weight=2)
    guild_tab.rowconfigure(1, weight=1)
    guild_search_var = tk.StringVar()
    gframe, guild_tree, guild_search_entry, guild_search_label = create_search_panel(
        guild_tab,
        "deletion.search_guilds",
        guild_search_var,
        on_guild_search,
        ("Name", "ID"),
        (t("deletion.col.guild_name"), t("deletion.col.guild_id")),
        (150, 150), 700, 400, tree_height=15)
    window.refresh_elements['search_labels'].append((guild_search_label, "deletion.search_guilds"))
    gframe.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
    guild_tree.bind("<<TreeviewSelect>>", on_guild_select)
    for col, key in zip(("Name", "ID"), ("deletion.col.guild_name", "deletion.col.guild_id")):
        guild_tree.heading(col, command=lambda c=col: treeview_sort_column(guild_tree, c, False))
        window.refresh_elements['treeview_headings'].append((guild_tree, col, key))
    guild_members_search_var = tk.StringVar()
    gm_frame, guild_members_tree, guild_members_search_entry, guild_members_search_label = create_search_panel(
        guild_tab,
        "deletion.guild_members",
        guild_members_search_var,
        on_guild_members_search,
        ("Name", "Last", "Level", "Pals", "UID"),
        (t("deletion.col.member"), t("deletion.col.last_seen"), t("deletion.col.level"), t("deletion.col.pals"), "UID"),
        (200, 120, 60, 100, 300), 800, 200, tree_height=10)
    window.refresh_elements['search_labels'].append((guild_members_search_label, "deletion.guild_members"))
    gm_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
    guild_members_tree.bind("<<TreeviewSelect>>", on_guild_member_select)
    for col, key in zip(("Name", "Last", "Level", "Pals", "UID"), ("deletion.col.member", "deletion.col.last_seen", "deletion.col.level", "deletion.col.pals", "UID")):
        guild_members_tree.heading(col, command=lambda c=col: treeview_sort_column(guild_members_tree, c, False))
        window.refresh_elements['treeview_headings'].append((guild_members_tree, col, key))
    BASES_TAB_NAME = "BasesTab"
    base_tab = notebook.add(BASES_TAB_NAME)
    window.refresh_elements['notebook_tabs'].append((BASES_TAB_NAME, "deletion.search_bases"))
    base_tab.columnconfigure(0, weight=1)
    base_tab.rowconfigure(0, weight=3)
    base_search_var = tk.StringVar()
    bframe, base_tree, base_search_entry, base_search_label = create_search_panel(
        base_tab,
        "deletion.search_bases",
        base_search_var,
        on_base_search,
        ("ID", "GuildID", "GuildName"),
        (t("deletion.col.base_id"), t("deletion.col.guild_id"), t("deletion.col.guild_name")),
        (200, 250, 250),
        800,
        600,
        tree_height=25
    )
    window.refresh_elements['search_labels'].append((base_search_label, "deletion.search_bases"))
    bframe.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
    base_tree.bind("<<TreeviewSelect>>", on_base_select)
    for col, key in zip(("ID", "GuildID", "GuildName"), ("deletion.col.base_id", "deletion.col.guild_id", "deletion.col.guild_name")):
        base_tree.heading(col, command=lambda c=col: treeview_sort_column(base_tree, c, False))
        window.refresh_elements['treeview_headings'].append((base_tree, col, key))
    EXCLUSIONS_TAB_NAME = "ExclusionsTab"
    exclusions_tab = notebook.add(EXCLUSIONS_TAB_NAME)
    window.refresh_elements['notebook_tabs'].append((EXCLUSIONS_TAB_NAME, "deletion.menu.exclusions"))
    exclusions_tab.columnconfigure((0, 1, 2), weight=1)
    exclusions_tab.rowconfigure(0, weight=1)
    player_excl_frame = ctk.CTkFrame(exclusions_tab, fg_color="transparent")
    player_excl_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
    player_excl_frame.columnconfigure(0, weight=1)
    player_excl_frame.rowconfigure(0, weight=1)
    player_excl_label = ctk.CTkLabel(player_excl_frame, text=t("deletion.exclusions.player_label"), font=("Segoe UI", 11, "bold"))
    player_excl_label.pack(pady=(0, 5), padx=5, anchor="w")
    window.refresh_elements['main_labels'].append((player_excl_label, "deletion.exclusions.player_label", {}))
    exclusions_players_tree = ttk.Treeview(player_excl_frame, columns=("ID",), show="headings", style="Treeview")
    exclusions_players_tree.heading("ID", text=t("deletion.excluded_player_uid"))
    window.refresh_elements['treeview_headings'].append((exclusions_players_tree, "ID", "deletion.excluded_player_uid"))
    exclusions_players_tree.column("ID", width=300, stretch=True)
    exclusions_players_tree.pack(fill="both", expand=True, padx=5, pady=0)
    for col in ("ID",):
        exclusions_players_tree.heading(col, command=lambda c=col: treeview_sort_column(exclusions_players_tree, c, False))
    guild_excl_frame = ctk.CTkFrame(exclusions_tab, fg_color="transparent")
    guild_excl_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
    guild_excl_frame.columnconfigure(0, weight=1)
    guild_excl_frame.rowconfigure(0, weight=1)
    guild_excl_label = ctk.CTkLabel(guild_excl_frame, text=t("deletion.exclusions.guild_label"), font=("Segoe UI", 11, "bold"))
    guild_excl_label.pack(pady=(0, 5), padx=5, anchor="w")
    window.refresh_elements['main_labels'].append((guild_excl_label, "deletion.exclusions.guild_label", {}))
    exclusions_guilds_tree = ttk.Treeview(guild_excl_frame, columns=("ID",), show="headings", style="Treeview")
    exclusions_guilds_tree.heading("ID", text=t("deletion.excluded_guild_id"))
    window.refresh_elements['treeview_headings'].append((exclusions_guilds_tree, "ID", "deletion.excluded_guild_id"))
    exclusions_guilds_tree.column("ID", width=300, stretch=True)
    exclusions_guilds_tree.pack(fill="both", expand=True, padx=5, pady=0)
    for col in ("ID",):
        exclusions_guilds_tree.heading(col, command=lambda c=col: treeview_sort_column(exclusions_guilds_tree, c, False))
    base_excl_frame = ctk.CTkFrame(exclusions_tab, fg_color="transparent")
    base_excl_frame.grid(row=0, column=2, padx=5, pady=5, sticky="nsew")
    base_excl_frame.columnconfigure(0, weight=1)
    base_excl_frame.rowconfigure(0, weight=1)
    base_excl_label = ctk.CTkLabel(base_excl_frame, text=t("deletion.exclusions.base_label"), font=("Segoe UI", 11, "bold"))
    base_excl_label.pack(pady=(0, 5), padx=5, anchor="w")
    window.refresh_elements['main_labels'].append((base_excl_label, "deletion.exclusions.base_label", {}))
    exclusions_bases_tree = ttk.Treeview(base_excl_frame, columns=("ID",), show="headings", style="Treeview")
    exclusions_bases_tree.heading("ID", text=t("deletion.excluded_bases"))
    window.refresh_elements['treeview_headings'].append((exclusions_bases_tree, "ID", "deletion.excluded_bases"))
    exclusions_bases_tree.column("ID", width=300, stretch=True)
    exclusions_bases_tree.pack(fill="both", expand=True, padx=5, pady=0)
    for col in ("ID",):
        exclusions_bases_tree.heading(col, command=lambda c=col: treeview_sort_column(exclusions_bases_tree, c, False))
    populate_exclusions_trees()
    def guild_tree_menu(event):
        iid = guild_tree.identify_row(event.y)
        if iid:
            guild_tree.selection_set(iid)
            menu = tk.Menu(window, tearoff=0, bg=MENU_BG, fg=MENU_FG, activebackground=MENU_ACTIVE_BG, activeforeground=MENU_FG)
            menu.add_command(label=t("deletion.ctx.add_exclusion"), command=lambda: add_exclusion(guild_tree, "guilds"))
            menu.add_command(label=t("deletion.ctx.remove_exclusion"), command=lambda: remove_selected_from_regular(guild_tree, "guilds"))
            menu.add_command(label=t("deletion.ctx.delete_guild"), command=delete_selected_guild)
            menu.add_command(label=t("guild.rename.menu"), command=rename_guild)
            menu.add_command(label=t("guild.menu.move_selected_player_to_selected_guild"), command=move_selected_player_to_selected_guild)
            menu.tk_popup(event.x_root, event.y_root)
    def base_tree_menu(event):
        iid = base_tree.identify_row(event.y)
        if iid:
            base_tree.selection_set(iid)
            menu = tk.Menu(window, tearoff=0, bg=MENU_BG, fg=MENU_FG, activebackground=MENU_ACTIVE_BG, activeforeground=MENU_FG)
            menu.add_command(label=t("deletion.ctx.add_exclusion"), command=lambda: add_exclusion(base_tree, "bases"))
            menu.add_command(label=t("deletion.ctx.remove_exclusion"), command=lambda: remove_selected_from_regular(base_tree, "bases"))
            menu.add_command(label=t("deletion.ctx.delete_base"), command=delete_selected_base)
            menu.add_command(label=t("export.base"), command=lambda: trigger_base_transfer(base_tree, loaded_level_json, "export"))
            menu.add_command(label=t("import.base"), command=lambda: trigger_base_transfer(base_tree, loaded_level_json, "import"))
            menu.add_command(label=t("clone.base"), command=lambda: trigger_clone_base(base_tree, loaded_level_json))
            menu.tk_popup(event.x_root, event.y_root)
    def trigger_base_transfer(base_tree, loaded_level_json, mode="export"):
        import json, tkinter.filedialog, tkinter.messagebox
        class CustomEncoder(json.JSONEncoder):
            def default(self, obj):
                if hasattr(obj, 'bytes') or obj.__class__.__name__ == 'UUID':
                    return str(obj)
                return super().default(obj)
        selected = base_tree.selection()
        if not selected:
            tkinter.messagebox.showwarning("Selection Required", "Please select a row from the list.")
            return
        item = base_tree.item(selected[0])
        base_id = item['values'][0]
        guild_id = item['values'][1]
        if mode == "export":
            data = export_base_json(loaded_level_json, base_id)
            if not data:
                tkinter.messagebox.showerror("Error", f"Could not find base data for ID:\n{base_id}")
                return
            path = tkinter.filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")], title="Export Base")
            if path:
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, cls=CustomEncoder)
                tkinter.messagebox.showinfo("Success", "Base exported to JSON successfully.")
        else:
            path = tkinter.filedialog.askopenfilename(filetypes=[("JSON files", "*.json")], title="Import Base")
            if not path: return
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if import_base_json(loaded_level_json, data, guild_id, offset=(8000, 0, 0)):
                    tkinter.messagebox.showinfo("Success", f"Base imported successfully!\nRemember to save Level.sav.")
                else:
                    tkinter.messagebox.showerror("Error", "Import logic failed.")
            except Exception as e:
                tkinter.messagebox.showerror("Error", f"Failed to read JSON file:\n{str(e)}")
    def trigger_clone_base(tree, loaded_level_json):
        selected = tree.selection()
        if not selected: return
        base_id = tree.item(selected[0])['values'][0]
        guild_id = tree.item(selected[0])['values'][1]
        if clone_base_complete(loaded_level_json, base_id, guild_id):
            messagebox.showinfo("Success", "Base cloned successfully with all structures and containers!")
            refresh_all()
        else:
            messagebox.showerror("Error", "Failed to clone base.")
    def player_tree_menu(event):
        global selected_source_player        
        iid = player_tree.identify_row(event.y)
        if iid:
            player_tree.selection_set(iid)        
        selected_iids = player_tree.selection()        
        if selected_iids:
            raw_uid = player_tree.item(selected_iids[0])['values'][4]
            selected_source_player = raw_uid             
            menu = tk.Menu(window, tearoff=0, bg=MENU_BG, fg=MENU_FG, activebackground=MENU_ACTIVE_BG, activeforeground=MENU_FG)
            menu.add_command(label=t("deletion.ctx.add_exclusion"), command=lambda: add_exclusion(player_tree, "players"))
            menu.add_command(label=t("deletion.ctx.remove_exclusion"), command=lambda: remove_selected_from_regular(player_tree, "players"))
            menu.add_command(label=t("deletion.ctx.delete_player"), command=delete_selected_player)
            menu.add_command(label=t("player.rename.menu"), command=rename_player)
            menu.add_separator()
            menu.add_command(label=t("deletion.ctx.delete_guild"), command=delete_selected_guild) 
            menu.add_command(label=t("guild.rename.menu"), command=rename_guild)           
            menu.add_separator()
            menu.add_command(label=t("guild.menu.move_selected_player_to_selected_guild"), command=move_selected_player_to_selected_guild)
            menu.tk_popup(event.x_root, event.y_root)
        else:
            selected_source_player = None
    def guild_members_tree_menu(event):
        iid = guild_members_tree.identify_row(event.y)
        if iid:
            guild_members_tree.selection_set(iid)
            menu = tk.Menu(window, tearoff=0, bg=MENU_BG, fg=MENU_FG, activebackground=MENU_ACTIVE_BG, activeforeground=MENU_FG)
            menu.add_command(label=t("guild.ctx.make_leader"), command=make_selected_member_leader)
            menu.add_command(label=t("deletion.ctx.add_exclusion"), command=lambda: add_exclusion(guild_members_tree, "players"))
            menu.add_command(label=t("deletion.ctx.remove_exclusion"), command=lambda: remove_selected_from_regular(guild_members_tree, "players"))
            menu.add_command(label=t("deletion.ctx.delete_player"), command=lambda: delete_selected_guild_member())
            menu.add_command(label=t("player.rename.menu"), command=rename_player)
            menu.tk_popup(event.x_root, event.y_root)
    def exclusions_guilds_tree_menu(event):
        iid = exclusions_guilds_tree.identify_row(event.y)
        if iid:
            exclusions_guilds_tree.selection_set(iid)
            menu = tk.Menu(window, tearoff=0, bg=MENU_BG, fg=MENU_FG, activebackground=MENU_ACTIVE_BG, activeforeground=MENU_FG)
            menu.add_command(label=t("deletion.ctx.remove_exclusion"), command=lambda: remove_selected_exclusion(exclusions_guilds_tree, "guilds"))
            menu.tk_popup(event.x_root, event.y_root)
    def exclusions_players_tree_menu(event):
        iid = exclusions_players_tree.identify_row(event.y)
        if iid:
            exclusions_players_tree.selection_set(iid)
            menu = tk.Menu(window, tearoff=0, bg=MENU_BG, fg=MENU_FG, activebackground=MENU_ACTIVE_BG, activeforeground=MENU_FG)
            menu.add_command(label=t("deletion.ctx.remove_exclusion"), command=lambda: remove_selected_exclusion(exclusions_players_tree, "players"))
            menu.tk_popup(event.x_root, event.y_root)
    def exclusions_bases_tree_menu(event):
        iid = exclusions_bases_tree.identify_row(event.y)
        if iid:
            exclusions_bases_tree.selection_set(iid)
            menu = tk.Menu(window, tearoff=0, bg=MENU_BG, fg=MENU_FG, activebackground=MENU_ACTIVE_BG, activeforeground=MENU_FG)
            menu.add_command(label=t("deletion.ctx.remove_exclusion"), command=lambda: remove_selected_exclusion(exclusions_bases_tree, "bases"))
            menu.tk_popup(event.x_root, event.y_root)
    guild_tree.bind("<Button-3>", guild_tree_menu)
    base_tree.bind("<Button-3>", base_tree_menu)
    player_tree.bind("<Button-3>", player_tree_menu)
    guild_members_tree.bind("<Button-3>", guild_members_tree_menu)
    exclusions_guilds_tree.bind("<Button-3>", exclusions_guilds_tree_menu)
    exclusions_players_tree.bind("<Button-3>", exclusions_players_tree_menu)
    exclusions_bases_tree.bind("<Button-3>", exclusions_bases_tree_menu)
    def on_f5_press(event):
        folder = current_save_path
        if not folder: return
        refresh_all()
    window.bind("<F5>", on_f5_press)
    window.refresh_texts_all_in_one()
    window.update()
    center_window(window)
    try: window.iconbitmap(ICON_PATH)
    except: pass
    def on_exit():
        window.running=False
        try: window.destroy()
        except: pass
    window.protocol("WM_DELETE_WINDOW", on_exit)
    return window
if __name__=="__main__":
    all_in_one_tools()
    if len(sys.argv) > 1:
        if tk._default_root:
            for w in [tk._default_root]+tk._default_root.winfo_children():
                if isinstance(w, (tk.Tk, tk.Toplevel)):
                    w.withdraw()
        load_save(" ".join(sys.argv[1:]))
        if tk._default_root:
            tk._default_root.destroy()