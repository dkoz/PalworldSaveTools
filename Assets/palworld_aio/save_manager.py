import os 
import sys 
import time 
import shutil 
import json 
import logging 
import threading 
from collections import defaultdict 
from concurrent .futures import ThreadPoolExecutor ,as_completed 
from PySide6 .QtWidgets import QFileDialog ,QMessageBox 
from PySide6 .QtCore import QObject ,Signal 
from palworld_save_tools .gvas import GvasFile 
from palworld_save_tools .palsav import decompress_sav_to_gvas 
from palworld_save_tools .paltypes import PALWORLD_TYPE_HINTS 
from palobject import SKP_PALWORLD_CUSTOM_PROPERTIES 
from palobject import MappingCacheObject ,toUUID 
from import_libs import backup_whole_directory ,run_with_loading 
import palworld_coord 
from i18n import t 
try :
    from palworld_aio import constants 
    from palworld_aio .utils import sav_to_json ,json_to_sav ,extract_value ,sanitize_filename ,format_duration_short 
except ImportError :
    from .import constants 
    from .utils import sav_to_json ,json_to_sav ,extract_value ,sanitize_filename ,format_duration_short 
class SaveManager (QObject ):
    load_started =Signal ()
    load_finished =Signal (bool )
    save_started =Signal ()
    save_finished =Signal (float )
    stats_updated =Signal (str )
    def __init__ (self ):
        super ().__init__ ()
        self .dps_tasks =[]
    def load_save (self ,path =None ,parent =None ):
        if constants .loaded_level_json is not None :
            from .utils import restart_program 
            restart_program ()
        base_path =constants .get_base_path ()
        if path is None :
            p ,_ =QFileDialog .getOpenFileName (parent ,'Select Level.sav','','SAV Files (*.sav)')
        else :
            p =path 
        if not p :
            return False 
        if not p .endswith ('Level.sav'):
            QMessageBox .critical (parent ,t ('error.title'),t ('error.not_level_sav'))
            return False 
        d =os .path .dirname (p )
        playerdir =os .path .join (d ,'Players')
        if not os .path .isdir (playerdir ):
            QMessageBox .critical (parent ,t ('error.title'),t ('error.players_folder_missing'))
            return False 
        self .load_started .emit ()
        print (t ('loading.save'))
        constants .current_save_path =d 
        constants .backup_save_path =constants .current_save_path 
        def load_task ():
            t0 =time .perf_counter ()
            constants .loaded_level_json =sav_to_json (p )
            t1 =time .perf_counter ()
            print (t ('loading.converted',seconds =f'{t1 -t0 :.2f}'))
            self ._build_player_levels ()
            if not constants .loaded_level_json :
                self .load_finished .emit (False )
                return False 
            data_source =constants .loaded_level_json ['properties']['worldSaveData']['value']
            try :
                if hasattr (MappingCacheObject ,'clear_cache'):
                    MappingCacheObject .clear_cache ()
                constants .srcGuildMapping =MappingCacheObject .get (data_source ,use_mp =True )
                if constants .srcGuildMapping ._worldSaveData .get ('GroupSaveDataMap')is None :
                    constants .srcGuildMapping .GroupSaveDataMap ={}
            except Exception as e :
                if path is None :
                    QMessageBox .critical (parent ,t ('error.title'),t ('error.guild_mapping_failed',err =e ))
                else :
                    print (f"Error: {e }")
                constants .srcGuildMapping =None 
            constants .base_guild_lookup ={}
            guild_name_map ={}
            if constants .srcGuildMapping :
                for gid_uuid ,gdata in constants .srcGuildMapping .GroupSaveDataMap .items ():
                    gid =str (gid_uuid )
                    guild_name =gdata ['value']['RawData']['value'].get ('guild_name','Unnamed Guild')
                    guild_name_map [gid .lower ()]=guild_name 
                    for base_id_uuid in gdata ['value']['RawData']['value'].get ('base_ids',[]):
                        constants .base_guild_lookup [str (base_id_uuid )]={'GuildName':guild_name ,'GuildID':gid }
            print (t ('loading.done'))
            log_folder =os .path .join (base_path ,'Scan Save Logger')
            if os .path .exists (log_folder ):
                try :
                    shutil .rmtree (log_folder )
                except :
                    pass 
            os .makedirs (log_folder ,exist_ok =True )
            player_pals_count ={}
            self ._count_pals_found (data_source ,player_pals_count ,log_folder ,constants .current_save_path ,guild_name_map )
            constants .PLAYER_PAL_COUNTS =player_pals_count 
            self ._process_scan_log (data_source ,playerdir ,log_folder ,guild_name_map )
            self .load_finished .emit (True )
            return True 
        run_with_loading (lambda _ :None ,load_task )
    def reload_current_save (self ):
        if not constants .current_save_path :
            raise Exception ("No save is currently loaded")
        level_sav_path =os .path .join (constants .current_save_path ,'Level.sav')
        if not os .path .exists (level_sav_path ):
            raise Exception (f"Level.sav not found at {level_sav_path }")
        print (t ('loading.save'))
        base_path =constants .get_base_path ()
        t0 =time .perf_counter ()
        constants .loaded_level_json =sav_to_json (level_sav_path )
        t1 =time .perf_counter ()
        print (t ('loading.converted',seconds =f'{t1 -t0 :.2f}'))
        self ._build_player_levels ()
        if not constants .loaded_level_json :
            raise Exception ("Failed to parse Level.sav")
        data_source =constants .loaded_level_json ['properties']['worldSaveData']['value']
        try :
            if hasattr (MappingCacheObject ,'clear_cache'):
                MappingCacheObject .clear_cache ()
            constants .srcGuildMapping =MappingCacheObject .get (data_source ,use_mp =True )
            if constants .srcGuildMapping ._worldSaveData .get ('GroupSaveDataMap')is None :
                constants .srcGuildMapping .GroupSaveDataMap ={}
        except Exception as e :
            print (f"Error rebuilding guild mapping: {e }")
            constants .srcGuildMapping =None 
        constants .base_guild_lookup ={}
        guild_name_map ={}
        if constants .srcGuildMapping :
            for gid_uuid ,gdata in constants .srcGuildMapping .GroupSaveDataMap .items ():
                gid =str (gid_uuid )
                guild_name =gdata ['value']['RawData']['value'].get ('guild_name','Unnamed Guild')
                guild_name_map [gid .lower ()]=guild_name 
                for base_id_uuid in gdata ['value']['RawData']['value'].get ('base_ids',[]):
                    constants .base_guild_lookup [str (base_id_uuid )]={'GuildName':guild_name ,'GuildID':gid }
        log_folder =os .path .join (base_path ,'Scan Save Logger')
        if os .path .exists (log_folder ):
            try :
                shutil .rmtree (log_folder )
            except :
                pass 
        os .makedirs (log_folder ,exist_ok =True )
        player_pals_count ={}
        self ._count_pals_found (data_source ,player_pals_count ,log_folder ,constants .current_save_path ,guild_name_map )
        constants .PLAYER_PAL_COUNTS =player_pals_count 
        playerdir =os .path .join (constants .current_save_path ,'Players')
        self ._process_scan_log (data_source ,playerdir ,log_folder ,guild_name_map )
        print (t ('loading.done'))
        return True 
    def save_changes (self ,parent =None ):
        if not constants .current_save_path or not constants .loaded_level_json :
            return 
        self .save_started .emit ()
        backup_whole_directory (constants .backup_save_path ,'Backups/AllinOneTools')
        level_sav_path =os .path .join (constants .current_save_path ,'Level.sav')
        def save_task ():
            t0 =time .perf_counter ()
            json_to_sav (constants .loaded_level_json ,level_sav_path )
            t1 =time .perf_counter ()
            players_folder =os .path .join (constants .current_save_path ,'Players')
            for uid in constants .files_to_delete :
                f =os .path .join (players_folder ,uid +'.sav')
                f_dps =os .path .join (players_folder ,f'{uid }_dps.sav')
                try :
                    os .remove (f )
                except FileNotFoundError :
                    pass 
                try :
                    os .remove (f_dps )
                except FileNotFoundError :
                    pass 
            constants .files_to_delete .clear ()
            duration =t1 -t0 
            print (f'Time taken to save changes: {duration :.2f} seconds')
            self .save_finished .emit (duration )
            return duration 
        run_with_loading (lambda _ :None ,save_task )
    def _build_player_levels (self ):
        char_map =constants .loaded_level_json ['properties']['worldSaveData']['value'].get ('CharacterSaveParameterMap',{}).get ('value',[])
        uid_level_map =defaultdict (lambda :'?')
        for entry in char_map :
            try :
                sp =entry ['value']['RawData']['value']['object']['SaveParameter']
                if sp ['struct_type']!='PalIndividualCharacterSaveParameter':
                    continue 
                sp_val =sp ['value']
                if not sp_val .get ('IsPlayer',{}).get ('value',False ):
                    continue 
                key =entry .get ('key',{})
                uid_obj =key .get ('PlayerUId',{})
                uid =str (uid_obj .get ('value','')if isinstance (uid_obj ,dict )else uid_obj )
                level =extract_value (sp_val ,'Level','?')
                if uid :
                    uid_level_map [uid .replace ('-','')]=level 
            except Exception :
                continue 
        constants .player_levels =dict (uid_level_map )
    def _count_pals_found (self ,data ,player_pals_count ,log_folder ,current_save_path ,guild_name_map ):
        base_dir =os .path .dirname (os .path .dirname (os .path .abspath (__file__ )))
        def load_map (fname ,key ):
            try :
                fp =os .path .join (base_dir ,'resources','game_data',fname )
                with open (fp ,'r',encoding ='utf-8')as f :
                    js =json .load (f )
                    return {x ['asset'].lower ():x ['name']for x in js .get (key ,[])}
            except :
                return {}
        PALMAP =load_map ('paldata.json','pals')
        NPCMAP =load_map ('npcdata.json','npcs')
        PASSMAP =load_map ('passivedata.json','passives')
        SKILLMAP =load_map ('skilldata.json','skills')
        NAMEMAP ={**PALMAP ,**NPCMAP }
        miss ={'Pals':set (),'Passives':set (),'Skills':set ()}
        owner_pals_grouped =defaultdict (lambda :defaultdict (list ))
        player_containers ={}
        owner_nicknames ={}
        players_dir =os .path .join (current_save_path ,'Players')
        if os .path .exists (players_dir ):
            for filename in os .listdir (players_dir ):
                if filename .endswith ('.sav')and '_dps'not in filename :
                    try :
                        p_json =sav_to_json (os .path .join (players_dir ,filename ))
                        p_prop =p_json .get ('properties',{}).get ('SaveData',{}).get ('value',{})
                        p_uid_raw =filename .replace ('.sav','')
                        p_uid =p_uid_raw .lower ()
                        p_box =p_prop .get ('PalStorageContainerId',{}).get ('value',{}).get ('ID',{}).get ('value')
                        p_party =p_prop .get ('OtomoCharacterContainerId',{}).get ('value',{}).get ('ID',{}).get ('value')
                        if p_box and p_party :
                            player_containers [p_uid ]={'Party':str (p_party ).lower (),'PalBox':str (p_box ).lower ()}
                    except :
                        pass 
        cmap =data .get ('CharacterSaveParameterMap',{}).get ('value',[])
        for itm in cmap :
            try :
                raw_p =itm .get ('value',{}).get ('RawData',{}).get ('value',{}).get ('object',{}).get ('SaveParameter',{}).get ('value',{})
                if 'IsPlayer'in raw_p :
                    uid =itm .get ('key',{}).get ('PlayerUId',{}).get ('value')
                    nn =raw_p .get ('NickName',{}).get ('value','Unknown')
                    if uid :
                        owner_nicknames [str (uid ).replace ('-','').lower ()]=nn 
            except :
                pass 
        guild_bases =defaultdict (set )
        for item in cmap :
            rawf =item .get ('value',{}).get ('RawData',{}).get ('value',{})
            raw =rawf .get ('object',{}).get ('SaveParameter',{}).get ('value',{})
            if not isinstance (raw ,dict )or 'IsPlayer'in raw :
                continue 
            inst =item .get ('key',{}).get ('InstanceId',{}).get ('value')
            gid =str (rawf .get ('group_id','Unknown')).lower ()
            uid_val =raw .get ('OwnerPlayerUId',{}).get ('value')
            u_str =str (uid_val ).replace ('-','').lower ()if uid_val else '00000000000000000000000000000000'
            is_worker =u_str =='00000000000000000000000000000000'
            base =str (raw .get ('SlotId',{}).get ('value',{}).get ('ContainerId',{}).get ('value',{}).get ('ID',{}).get ('value')).lower ()
            if is_worker :
                guild_bases [gid ].add (base )
            target_id =u_str if not is_worker else f'WORKER_{gid }_{base }'
            if is_worker and target_id not in owner_nicknames :
                owner_nicknames [target_id ]=f'Base_{base }'
            cid =raw .get ('CharacterID',{}).get ('value','')
            if cid and cid .lower ()not in NAMEMAP :
                miss ['Pals'].add (cid )
            name =NAMEMAP .get (cid .lower (),cid )
            lvl =extract_value (raw ,'Level',1 )
            rk =extract_value (raw ,'Rank',1 )
            gv =raw .get ('Gender',{}).get ('value',{}).get ('value','')
            ginfo ={'EPalGenderType::Male':'Male','EPalGenderType::Female':'Female'}.get (gv ,'Unknown')
            p_list =raw .get ('PassiveSkillList',{}).get ('value',{}).get ('values',[])
            for s in p_list :
                if s .lower ()not in PASSMAP :
                    miss ['Passives'].add (s )
            pskills =[PASSMAP .get (s .lower (),s )for s in p_list ]
            e_list =raw .get ('EquipWaza',{}).get ('value',{}).get ('values',[])
            for w in e_list :
                w_short =w .split ('::')[-1 ]
                if w_short .lower ()not in SKILLMAP :
                    miss ['Skills'].add (w )
            active =[SKILLMAP .get (w .split ('::')[-1 ].lower (),w .split ('::')[-1 ])for w in e_list ]
            m_list =raw .get ('MasteredWaza',{}).get ('value',{}).get ('values',[])
            for w in m_list :
                w_short =w .split ('::')[-1 ]
                if w_short .lower ()not in SKILLMAP :
                    miss ['Skills'].add (w )
            learned =[SKILLMAP .get (w .split ('::')[-1 ].lower (),w .split ('::')[-1 ])for w in m_list ]
            rh ,ra ,rd =(int (extract_value (raw ,'Rank_HP',0 ))*3 ,int (extract_value (raw ,'Rank_Attack',0 ))*3 ,int (extract_value (raw ,'Rank_Defence',0 ))*3 )
            iv_str =f"HP: {extract_value (raw ,'Talent_HP','0')} (+{rh }%), ATK: {extract_value (raw ,'Talent_Shot','0')} (+{ra }%), DEF: {extract_value (raw ,'Talent_Defense','0')} (+{rd }%)"
            nick =raw .get ('NickName',{}).get ('value','Unknown')
            dn =f'{name } (Nickname: {nick })'if nick !='Unknown'else name 
            info =f"\n[{dn }]\n  Level: {lvl } | Rank: {rk } | Gender: {ginfo }\n  IVs:      {iv_str }\n  Passives: {(', '.join (pskills )if pskills else 'None')}\n  Active:   {(', '.join (active )if active else 'None')}\n  Learned:  {(', '.join (learned )if learned else 'None')}\n  IDs:      Container: {base } | Instance: {inst } | Guild: {gid }\n"
            lbl ='Base Worker'
            if not is_worker and u_str in player_containers :
                if base ==player_containers [u_str ]['Party']:
                    lbl ='Current Party'
                elif base ==player_containers [u_str ]['PalBox']:
                    lbl ='PalBox Storage'
            owner_pals_grouped [target_id ][lbl ].append (info )
            if is_worker :
                player_pals_count ['worker_dropped']=player_pals_count .get ('worker_dropped',0 )+1 
            else :
                player_pals_count [u_str ]=player_pals_count .get (u_str ,0 )+1 
        if any (miss .values ()):
            with open (os .path .join (log_folder ,'missing_assets.log'),'w',encoding ='utf-8')as f :
                for cat ,items in miss .items ():
                    if items :
                        f .write (f'[{cat }]\n'+'\n'.join (sorted (items ))+'\n\n')
        for uid ,containers in owner_pals_grouped .items ():
            pname =owner_nicknames .get (uid ,'Unknown')
            sname =sanitize_filename (pname .encode ('utf-8','replace').decode ('utf-8'))
            pal_count =sum ((len (p )for p in containers .values ()))
            if uid .startswith ('WORKER_'):
                parts =uid .split ('_')
                g_id ,b_id =(parts [1 ],parts [2 ])
                b_count =len (guild_bases [g_id ])
                g_name =sanitize_filename (guild_name_map .get (g_id ,'Unknown Guild'))
                g_dir =os .path .join (log_folder ,'Guilds',f'({g_id })_({g_name })_({b_count })')
                os .makedirs (g_dir ,exist_ok =True )
                lf =os .path .join (g_dir ,f'({b_id })_({pal_count }).log')
            else :
                p_dir =os .path .join (log_folder ,'Players')
                os .makedirs (p_dir ,exist_ok =True )
                lf =os .path .join (p_dir ,f'({uid })_({sname })_({pal_count }).log')
            lname =''.join ((c if c .isalnum ()or c in ('_','-')else '_'for c in f'lg_{uid }'))
            lg =logging .getLogger (lname )
            lg .setLevel (logging .INFO )
            lg .propagate =False 
            if not lg .hasHandlers ():
                try :
                    h =logging .FileHandler (lf ,mode ='w',encoding ='utf-8',errors ='replace')
                    h .setFormatter (logging .Formatter ('%(message)s'))
                    lg .addHandler (h )
                except :
                    continue 
            lg .info (f"{pname }'s {pal_count } Pals\n"+'='*40 )
            prio =['Current Party','PalBox Storage','Base Worker']
            sorted_keys =prio +sorted ([k for k in containers .keys ()if k not in prio ])
            for label in sorted_keys :
                if label in containers :
                    lg .info (f'\n{label } (Count: {len (containers [label ])})\n'+'-'*40 )
                    for p_block in sorted (containers [label ]):
                        lg .info (p_block )
                        lg .info ('-'*20 )
        for uid in owner_pals_grouped .keys ():
            lg =logging .getLogger (''.join ((c if c .isalnum ()or c in ('_','-')else '_'for c in f'lg_{uid }')))
            for h in lg .handlers [:]:
                h .flush ()
                h .close ()
                lg .removeHandler (h )
    def _process_scan_log (self ,data_source ,playerdir ,log_folder ,guild_name_map ):
        def count_owned_pals (level_json ):
            owned_count ={}
            try :
                char_map =level_json ['properties']['worldSaveData']['value']['CharacterSaveParameterMap']['value']
                for item in char_map :
                    try :
                        owner_uid =item ['value']['RawData']['value']['object']['SaveParameter']['value']['OwnerPlayerUId']['value']
                        if owner_uid :
                            owned_count [owner_uid ]=owned_count .get (owner_uid ,0 )+1 
                    except :
                        continue 
            except :
                pass 
            return owned_count 
        owned_counts =count_owned_pals (constants .loaded_level_json )
        scan_log_path =os .path .join (log_folder ,'scan_save.log')
        logger =logging .getLogger ('LoadSaveLogger')
        logger .handlers .clear ()
        logger .setLevel (logging .DEBUG )
        logger .propagate =False 
        formatter =logging .Formatter ('%(message)s')
        fh =logging .FileHandler (scan_log_path ,encoding ='utf-8')
        fh .setFormatter (formatter )
        ch =logging .StreamHandler (sys .stdout )
        ch .setFormatter (formatter )
        logger .addHandler (fh )
        logger .addHandler (ch )
        tick =data_source ['GameTimeSaveData']['value']['RealDateTimeTicks']['value']
        total_players =total_caught =total_owned =total_bases =active_guilds =0 
        if constants .srcGuildMapping :
            for gid ,gdata in constants .srcGuildMapping .GroupSaveDataMap .items ():
                raw_val =gdata ['value']['RawData']['value']
                players =raw_val .get ('players',[])
                if not players :
                    continue 
                active_guilds +=1 
                base_ids =raw_val .get ('base_ids',[])
                total_bases +=len (base_ids )
                guild_name =raw_val .get ('guild_name','Unnamed Guild')
                guild_leader =players [0 ].get ('player_info',{}).get ('player_name','Unknown')
                logger .info ('='*60 )
                logger .info (f'Guild: {guild_name } | Guild Leader: {guild_leader } | Guild ID: {gid }')
                logger .info (f'Base Locations: {len (base_ids )}')
                for i ,base_id in enumerate (base_ids ,1 ):
                    basecamp =constants .srcGuildMapping .BaseCampMapping .get (toUUID (base_id ))
                    if basecamp :
                        translation =basecamp ['value']['RawData']['value']['transform']['translation']
                        tx ,ty ,tz =(translation ['x'],translation ['y'],translation ['z'])
                        old_c =palworld_coord .sav_to_map (tx ,ty ,new =False )
                        new_c =palworld_coord .sav_to_map (tx ,ty ,new =True )
                        logger .info (f'Base {i }: Base ID: {base_id } | Old: {int (old_c [0 ])}, {int (old_c [1 ])} | New: {int (new_c [0 ])}, {int (new_c [1 ])} | RawData: {tx }, {ty }, {tz }')
                with ThreadPoolExecutor ()as executor :
                    results =list (executor .map (lambda p :self ._top_process_player (p ,playerdir ,log_folder ),players ))
                for uid ,pname ,uniques ,caught ,encounters in results :
                    level =constants .player_levels .get (str (uid ).replace ('-',''),'?')
                    owned =owned_counts .get (uid ,0 )
                    last =next ((p .get ('player_info',{}).get ('last_online_real_time')for p in players if p .get ('player_uid')==uid ),None )
                    lastseen ='Unknown'if last is None else format_duration_short ((tick -int (last ))/10000000.0 )
                    logger .info (f'Player: {pname } | UID: {uid } | Level: {level } | Caught: {caught } | Owned: {owned } | Encounters: {encounters } | Uniques: {uniques } | Last Online: {lastseen }')
                    total_players +=1 
                    total_caught +=caught 
                    total_owned +=owned 
                logger .info ('')
                logger .info ('='*60 )
        total_worker_dropped =constants .PLAYER_PAL_COUNTS .get ('worker_dropped',0 )
        logger .info ('********** PST_STATS_BEGIN **********')
        logger .info (f'Total Players: {total_players }')
        logger .info (f'Total Caught Pals: {total_caught }')
        logger .info (f'Total Overall Pals: {total_owned +total_worker_dropped }')
        logger .info (f'Total Owned Pals: {total_owned }')
        logger .info (f'Total Worker/Dropped Pals: {total_worker_dropped }')
        logger .info (f'Total Active Guilds: {active_guilds }')
        logger .info (f'Total Bases: {total_bases }')
        logger .info ('********** PST_STATS_END ************')
        for h in logger .handlers [:]:
            logger .removeHandler (h )
            h .close ()
    def _top_process_player (self ,p ,playerdir ,log_folder ):
        uid =p .get ('player_uid')
        pname =p .get ('player_info',{}).get ('player_name','Unknown')
        uniques =caught =encounters =0 
        if not uid :
            return (uid ,pname ,uniques ,caught ,encounters )
        clean_uid =str (uid ).replace ('-','')
        sav_file =os .path .join (playerdir ,f'{clean_uid }.sav')
        dps_file =os .path .join (playerdir ,f'{clean_uid }_dps.sav')
        if os .path .isfile (sav_file ):
            try :
                with open (sav_file ,'rb')as f :
                    data =f .read ()
                raw_gvas ,_ =decompress_sav_to_gvas (data )
                gvas_file =GvasFile .read (raw_gvas ,PALWORLD_TYPE_HINTS ,SKP_PALWORLD_CUSTOM_PROPERTIES ,allow_nan =True )
                json_data =gvas_file .dump ()
                pal_capture_count_list =json_data .get ('properties',{}).get ('SaveData',{}).get ('value',{}).get ('RecordData',{}).get ('value',{}).get ('PalCaptureCount',{}).get ('value',[])
                uniques =len (pal_capture_count_list )if pal_capture_count_list else 0 
                caught =sum ((e .get ('value',0 )for e in pal_capture_count_list ))if pal_capture_count_list else 0 
                pal_deck_unlock_flag_list =json_data .get ('properties',{}).get ('SaveData',{}).get ('value',{}).get ('RecordData',{}).get ('value',{}).get ('PaldeckUnlockFlag',{}).get ('value',[])
                encounters =max (len (pal_deck_unlock_flag_list )if pal_deck_unlock_flag_list else 0 ,uniques )
            except :
                pass 
        if os .path .isfile (dps_file ):
            self .dps_tasks .append ((uid ,pname ,dps_file ,log_folder ))
        return (uid ,pname ,uniques ,caught ,encounters )
    def get_current_stats (self ):
        if not constants .loaded_level_json :
            return {'Players':0 ,'Guilds':0 ,'Bases':0 ,'Pals':0 }
        wsd =constants .loaded_level_json ['properties']['worldSaveData']['value']
        group_data =wsd .get ('GroupSaveDataMap',{}).get ('value',[])
        base_data =wsd .get ('BaseCampSaveData',{}).get ('value',[])
        char_data =wsd .get ('CharacterSaveParameterMap',{}).get ('value',[])
        total_players =sum ((len (g ['value']['RawData']['value'].get ('players',[]))for g in group_data if g ['value']['GroupType']['value']['value']=='EPalGroupType::Guild'))
        total_guilds =sum ((1 for g in group_data if g ['value']['GroupType']['value']['value']=='EPalGroupType::Guild'))
        total_bases =len (base_data )
        total_pals =0 
        for c in char_data :
            val =c .get ('value',{}).get ('RawData',{}).get ('value',{})
            struct_type =val .get ('object',{}).get ('SaveParameter',{}).get ('struct_type')
            if struct_type =='PalIndividualCharacterSaveParameter':
                if 'IsPlayer'in val .get ('object',{}).get ('SaveParameter',{}).get ('value',{})and val ['object']['SaveParameter']['value']['IsPlayer'].get ('value'):
                    continue 
                total_pals +=1 
        return dict (Players =total_players ,Guilds =total_guilds ,Bases =total_bases ,Pals =total_pals )
    def get_players (self ):
        if not constants .loaded_level_json :
            return []
        out =[]
        wsd =constants .loaded_level_json ['properties']['worldSaveData']['value']
        tick =wsd ['GameTimeSaveData']['value']['RealDateTimeTicks']['value']
        for g in wsd ['GroupSaveDataMap']['value']:
            if g ['value']['GroupType']['value']['value']!='EPalGroupType::Guild':
                continue 
            gid =str (g ['key'])
            players =g ['value']['RawData']['value'].get ('players',[])
            for p in players :
                uid_raw =p .get ('player_uid')
                uid =str (uid_raw )if uid_raw is not None else ''
                name =p .get ('player_info',{}).get ('player_name','Unknown')
                last =p .get ('player_info',{}).get ('last_online_real_time')
                lastseen ='Unknown'if last is None else format_duration_short ((tick -last )/10000000.0 )
                level =constants .player_levels .get (uid .replace ('-',''),'?')if uid else '?'
                out .append ((uid ,name ,gid ,lastseen ,level ))
        return out 
    def get_guild_name_by_id (self ,target_gid ):
        if not constants .loaded_level_json :
            return 'Unknown Guild'
        from .utils import as_uuid 
        for g in constants .loaded_level_json ['properties']['worldSaveData']['value']['GroupSaveDataMap']['value']:
            current_gid =as_uuid (g ['key'])
            if g ['value']['GroupType']['value']['value']=='EPalGroupType::Guild'and current_gid ==target_gid :
                return g ['value']['RawData']['value'].get ('guild_name','Unnamed Guild')
        return 'No Guild'
save_manager =SaveManager ()
