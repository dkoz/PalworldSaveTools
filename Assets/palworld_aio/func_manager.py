import os 
import json 
from collections import defaultdict 
from palworld_save_tools .archive import UUID 
from PySide6 .QtWidgets import QMessageBox ,QInputDialog 
from i18n import t 
try :
    from palworld_aio import constants 
    from palworld_aio .utils import sav_to_json ,json_to_sav ,are_equal_uuids ,as_uuid ,is_valid_level ,extract_value ,format_duration 
    from palworld_aio .data_manager import delete_base_camp 
except ImportError :
    from .import constants 
    from .utils import sav_to_json ,json_to_sav ,are_equal_uuids ,as_uuid ,is_valid_level ,extract_value ,format_duration 
    from .data_manager import delete_base_camp 
def build_player_levels ():
    if not constants .loaded_level_json :
        return 
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
        except :
            continue 
    constants .player_levels =dict (uid_level_map )
def delete_player_pals (wsd ,to_delete_uids ):
    char_save_map =wsd .get ('CharacterSaveParameterMap',{}).get ('value',[])
    removed_pals =0 
    uids_set ={uid .replace ('-','')for uid in to_delete_uids if uid }
    new_map =[]
    for entry in char_save_map :
        try :
            val =entry ['value']['RawData']['value']['object']['SaveParameter']['value']
            struct_type =entry ['value']['RawData']['value']['object']['SaveParameter']['struct_type']
            owner_uid =val .get ('OwnerPlayerUId',{}).get ('value')
            if owner_uid :
                owner_uid =str (owner_uid ).replace ('-','')
            if struct_type in ('PalIndividualCharacterSaveParameter','PlayerCharacterSaveParameter')and owner_uid in uids_set :
                removed_pals +=1 
                continue 
        except :
            pass 
        new_map .append (entry )
    wsd ['CharacterSaveParameterMap']['value']=new_map 
    return removed_pals 
def clean_character_save_parameter_map (data_source ,valid_uids ):
    if 'CharacterSaveParameterMap'not in data_source :
        return 
    entries =data_source ['CharacterSaveParameterMap'].get ('value',[])
    keep =[]
    for entry in entries :
        key =entry .get ('key',{})
        value =entry .get ('value',{}).get ('RawData',{}).get ('value',{})
        saveparam =value .get ('object',{}).get ('SaveParameter',{}).get ('value',{})
        owner_uid_obj =saveparam .get ('OwnerPlayerUId')
        if owner_uid_obj is None :
            keep .append (entry )
            continue 
        owner_uid =owner_uid_obj .get ('value','')
        no_owner =owner_uid in ('','00000000-0000-0000-0000-000000000000')
        player_uid =key .get ('PlayerUId',{}).get ('value','')
        if player_uid and str (player_uid ).replace ('-','')in valid_uids or str (owner_uid ).replace ('-','')in valid_uids or no_owner :
            keep .append (entry )
    entries [:]=keep 
def delete_empty_guilds (parent =None ):
    if not constants .loaded_level_json :
        return 0 
    build_player_levels ()
    wsd =constants .loaded_level_json ['properties']['worldSaveData']['value']
    group_data =wsd ['GroupSaveDataMap']['value']
    to_delete =[]
    for g in group_data :
        if g ['value']['GroupType']['value']['value']!='EPalGroupType::Guild':
            continue 
        gid_str =str (g ['key'])
        gid_clean =gid_str .replace ('-','').lower ()
        if any (gid_clean ==ex .replace ('-','').lower ()for ex in constants .exclusions .get ('guilds',[])):
            continue 
        players =g ['value']['RawData']['value'].get ('players',[])
        if not players :
            to_delete .append (g )
            continue 
        all_invalid =True 
        for p in players :
            if isinstance (p ,dict )and 'player_uid'in p :
                uid_obj =p ['player_uid']
                if hasattr (uid_obj ,'hex'):
                    uid =uid_obj .hex 
                else :
                    uid =str (uid_obj )
            else :
                uid =str (p )
            uid =uid .replace ('-','')
            level =constants .player_levels .get (uid ,None )
            if is_valid_level (level ):
                all_invalid =False 
                break 
        if all_invalid :
            to_delete .append (g )
    for g in to_delete :
        gid =as_uuid (g ['key'])
        bases =wsd .get ('BaseCampSaveData',{}).get ('value',[])[:]
        for b in bases :
            if are_equal_uuids (b ['value']['RawData']['value'].get ('group_id_belong_to'),gid ):
                delete_base_camp (b ,gid )
        group_data .remove (g )
    return len (to_delete )
def delete_inactive_players (days_threshold ,parent =None ):
    if not constants .loaded_level_json :
        return 0 
    build_player_levels ()
    wsd =constants .loaded_level_json ['properties']['worldSaveData']['value']
    tick_now =wsd ['GameTimeSaveData']['value']['RealDateTimeTicks']['value']
    group_data_list =wsd ['GroupSaveDataMap']['value']
    deleted_info =[]
    to_delete_uids =set ()
    total_players_before =sum ((len (g ['value']['RawData']['value'].get ('players',[]))for g in group_data_list if g ['value']['GroupType']['value']['value']=='EPalGroupType::Guild'))
    excluded_players ={ex .replace ('-','')for ex in constants .exclusions .get ('players',[])}
    for group in group_data_list [:]:
        if group ['value']['GroupType']['value']['value']!='EPalGroupType::Guild':
            continue 
        raw =group ['value']['RawData']['value']
        original_players =raw .get ('players',[])
        keep_players =[]
        admin_uid =str (raw .get ('admin_player_uid','')).replace ('-','')
        for player in original_players :
            uid_obj =player .get ('player_uid','')
            uid =str (uid_obj .get ('value','')if isinstance (uid_obj ,dict )else uid_obj ).replace ('-','')
            if uid in excluded_players :
                keep_players .append (player )
                continue 
            player_name =player .get ('player_info',{}).get ('player_name','Unknown')
            last_online =player .get ('player_info',{}).get ('last_online_real_time')
            level =constants .player_levels .get (uid )
            inactive =last_online is not None and (tick_now -last_online )/864000000000 >=days_threshold 
            if inactive or not is_valid_level (level ):
                reason ='Inactive'if inactive else 'Invalid level'
                extra =f' - Inactive for {format_duration ((tick_now -last_online )/10000000.0 )}'if inactive and last_online else ''
                deleted_info .append (f'{player_name } ({uid }) - {reason }{extra }')
                to_delete_uids .add (uid )
            else :
                keep_players .append (player )
        if len (keep_players )!=len (original_players ):
            raw ['players']=keep_players 
            keep_uids ={str (p .get ('player_uid','')).replace ('-','')for p in keep_players }
            if not keep_players :
                gid =group ['key']
                base_camps =wsd .get ('BaseCampSaveData',{}).get ('value',[])
                for b in base_camps [:]:
                    if are_equal_uuids (b ['value']['RawData']['value'].get ('group_id_belong_to'),gid ):
                        delete_base_camp (b ,gid )
                group_data_list .remove (group )
            elif admin_uid not in keep_uids :
                raw ['admin_player_uid']=keep_players [0 ]['player_uid']
    if to_delete_uids :
        constants .files_to_delete .update (to_delete_uids )
        removed_pals =delete_player_pals (wsd ,to_delete_uids )
        char_map =wsd .get ('CharacterSaveParameterMap',{}).get ('value',[])
        char_map [:]=[
        entry for entry in char_map 
        if str (entry .get ('key',{}).get ('PlayerUId',{}).get ('value','')).replace ('-','')not in to_delete_uids 
        and str (entry .get ('value',{}).get ('RawData',{}).get ('value',{}).get ('object',{}).get ('SaveParameter',{}).get ('value',{}).get ('OwnerPlayerUId',{}).get ('value','')).replace ('-','')not in to_delete_uids 
        ]
        total_players_after =sum ((len (g ['value']['RawData']['value'].get ('players',[]))for g in group_data_list if g ['value']['GroupType']['value']['value']=='EPalGroupType::Guild'))
    return len (to_delete_uids )
def delete_inactive_bases (days_threshold ,parent =None ):
    if not constants .loaded_level_json :
        return 0 
    wsd =constants .loaded_level_json ['properties']['worldSaveData']['value']
    tick =wsd ['GameTimeSaveData']['value']['RealDateTimeTicks']['value']
    inactive_guild_ids =[]
    for g in wsd ['GroupSaveDataMap']['value']:
        if g ['value']['GroupType']['value']['value']!='EPalGroupType::Guild':
            continue 
        gid =as_uuid (g ['key'])
        players =g ['value']['RawData']['value'].get ('players',[])
        if not players :
            inactive_guild_ids .append (gid )
            continue 
        all_inactive =True 
        for p in players :
            last_online =p .get ('player_info',{}).get ('last_online_real_time')
            if last_online is None or (tick -last_online )/10000000.0 /86400 <days_threshold :
                all_inactive =False 
                break 
        if all_inactive :
            inactive_guild_ids .append (gid )
    base_list =wsd .get ('BaseCampSaveData',{}).get ('value',[])
    removed =0 
    excluded_bases ={ex .replace ('-','').lower ()for ex in constants .exclusions .get ('bases',[])}
    for b in base_list [:]:
        gid =as_uuid (b ['value']['RawData']['value'].get ('group_id_belong_to'))
        base_id =as_uuid (b ['key'])
        if base_id .replace ('-','').lower ()in excluded_bases :
            continue 
        if gid in inactive_guild_ids :
            if delete_base_camp (b ,gid ):
                removed +=1 
    return removed 
def delete_duplicated_players (parent =None ):
    if not constants .current_save_path or not constants .loaded_level_json :
        return 0 
    wsd =constants .loaded_level_json ['properties']['worldSaveData']['value']
    tick_now =wsd ['GameTimeSaveData']['value']['RealDateTimeTicks']['value']
    group_data_list =wsd ['GroupSaveDataMap']['value']
    uid_to_player ={}
    uid_to_group ={}
    deleted_players =[]
    format_duration_lambda =lambda ticks :f'{int (ticks /864000000000 )}d:{int (ticks %864000000000 /36000000000 )}h:{int (ticks %36000000000 /600000000 )}m ago'
    for group in group_data_list :
        if group ['value']['GroupType']['value']['value']!='EPalGroupType::Guild':
            continue 
        raw =group ['value']['RawData']['value']
        players =raw .get ('players',[])
        filtered_players =[]
        for player in players :
            uid_raw =player .get ('player_uid','')
            uid =str (uid_raw .get ('value','')if isinstance (uid_raw ,dict )else uid_raw ).replace ('-','')
            last_online =player .get ('player_info',{}).get ('last_online_real_time')or 0 
            player_name =player .get ('player_info',{}).get ('player_name','Unknown')
            days_inactive =(tick_now -last_online )/864000000000 if last_online else float ('inf')
            if uid in uid_to_player :
                prev =uid_to_player [uid ]
                prev_group =uid_to_group [uid ]
                prev_lo =prev .get ('player_info',{}).get ('last_online_real_time')or 0 
                prev_days_inactive =(tick_now -prev_lo )/864000000000 if prev_lo else float ('inf')
                prev_name =prev .get ('player_info',{}).get ('player_name','Unknown')
                if days_inactive >prev_days_inactive :
                    deleted_players .append ({
                    'deleted_uid':uid ,
                    'deleted_name':player_name ,
                    'deleted_gid':group ['key'],
                    'deleted_last_online':last_online ,
                    'kept_uid':uid ,
                    'kept_name':prev_name ,
                    'kept_gid':prev_group ['key'],
                    'kept_last_online':prev_lo 
                    })
                    continue 
                else :
                    prev_group ['value']['RawData']['value']['players']=[
                    p for p in prev_group ['value']['RawData']['value'].get ('players',[])
                    if str (p .get ('player_uid','')).replace ('-','')!=uid 
                    ]
                    deleted_players .append ({
                    'deleted_uid':uid ,
                    'deleted_name':prev_name ,
                    'deleted_gid':prev_group ['key'],
                    'deleted_last_online':prev_lo ,
                    'kept_uid':uid ,
                    'kept_name':player_name ,
                    'kept_gid':group ['key'],
                    'kept_last_online':last_online 
                    })
            uid_to_player [uid ]=player 
            uid_to_group [uid ]=group 
            filtered_players .append (player )
        raw ['players']=filtered_players 
    deleted_uids ={d ['deleted_uid']for d in deleted_players }
    if deleted_uids :
        constants .files_to_delete .update (deleted_uids )
        delete_player_pals (wsd ,deleted_uids )
    valid_uids ={
    str (p .get ('player_uid','')).replace ('-','')
    for g in wsd ['GroupSaveDataMap']['value']
    if g ['value']['GroupType']['value']['value']=='EPalGroupType::Guild'
    for p in g ['value']['RawData']['value'].get ('players',[])
    }
    clean_character_save_parameter_map (wsd ,valid_uids )
    return len (deleted_players )
def delete_unreferenced_data (parent =None ):
    if not constants .loaded_level_json :
        return {}
    build_player_levels ()
    def normalize_uid (uid ):
        if isinstance (uid ,dict ):
            uid =uid .get ('value','')
        return str (uid ).replace ('-','').lower ()
    def is_broken_mapobject (obj ):
        bp =obj .get ('Model',{}).get ('value',{}).get ('BuildProcess',{}).get ('value',{}).get ('RawData',{}).get ('value',{})
        return bp .get ('state')==0 
    def is_dropped_item (obj ):
        return obj .get ('ConcreteModel',{}).get ('value',{}).get ('RawData',{}).get ('value',{}).get ('concrete_model_type')=='PalMapObjectDropItemModel'
    wsd =constants .loaded_level_json ['properties']['worldSaveData']['value']
    group_data_list =wsd .get ('GroupSaveDataMap',{}).get ('value',[])
    char_map =wsd .get ('CharacterSaveParameterMap',{}).get ('value',[])
    char_uids =set ()
    for entry in char_map :
        uid_raw =entry .get ('key',{}).get ('PlayerUId')
        uid =normalize_uid (uid_raw )
        owner_uid_raw =entry .get ('value',{}).get ('RawData',{}).get ('value',{}).get ('object',{}).get ('SaveParameter',{}).get ('value',{}).get ('OwnerPlayerUId')
        owner_uid =normalize_uid (owner_uid_raw )
        if uid :
            char_uids .add (uid )
        if owner_uid :
            char_uids .add (owner_uid )
    unreferenced_uids ,invalid_uids ,removed_guilds =([],[],0 )
    for group in group_data_list [:]:
        if group ['value']['GroupType']['value']['value']!='EPalGroupType::Guild':
            continue 
        raw =group ['value']['RawData']['value']
        players =raw .get ('players',[])
        valid_players =[]
        all_invalid =True 
        for p in players :
            pid_raw =p .get ('player_uid')
            pid =normalize_uid (pid_raw )
            if pid not in char_uids :
                unreferenced_uids .append (pid )
                continue 
            level =constants .player_levels .get (pid ,None )
            if is_valid_level (level ):
                all_invalid =False 
                valid_players .append (p )
            else :
                invalid_uids .append (pid )
        if not valid_players or all_invalid :
            gid_raw =group ['key']
            gid =normalize_uid (gid_raw )
            for b in wsd .get ('BaseCampSaveData',{}).get ('value',[])[:]:
                base_gid_raw =b ['value']['RawData']['value'].get ('group_id_belong_to')
                base_gid =normalize_uid (base_gid_raw )
                if base_gid ==gid :
                    delete_base_camp (b ,gid_raw )
            group_data_list .remove (group )
            removed_guilds +=1 
            continue 
        raw ['players']=valid_players 
        admin_uid_raw =raw .get ('admin_player_uid')
        admin_uid =normalize_uid (admin_uid_raw )
        keep_uids ={normalize_uid (p .get ('player_uid'))for p in valid_players }
        if admin_uid not in keep_uids :
            raw ['admin_player_uid']=valid_players [0 ]['player_uid']
    char_map [:]=[
    entry for entry in char_map 
    if normalize_uid (entry .get ('key',{}).get ('PlayerUId'))not in unreferenced_uids +invalid_uids 
    and normalize_uid (entry .get ('value',{}).get ('RawData',{}).get ('value',{}).get ('object',{}).get ('SaveParameter',{}).get ('value',{}).get ('OwnerPlayerUId'))not in unreferenced_uids +invalid_uids 
    ]
    all_removed_uids =set (unreferenced_uids +invalid_uids )
    constants .files_to_delete .update (all_removed_uids )
    removed_pals =delete_player_pals (wsd ,all_removed_uids )
    map_objects_wrapper =wsd .get ('MapObjectSaveData',{}).get ('value',{})
    map_objects =map_objects_wrapper .get ('values',[])
    broken_ids ,dropped_ids =([],[])
    new_map_objects =[]
    for obj in map_objects :
        if is_broken_mapobject (obj ):
            instance_id =obj .get ('Model',{}).get ('value',{}).get ('RawData',{}).get ('value',{}).get ('instance_id')
            broken_ids .append (instance_id )
        elif is_dropped_item (obj ):
            instance_id =obj .get ('ConcreteModel',{}).get ('value',{}).get ('RawData',{}).get ('value',{}).get ('instance_id')
            dropped_ids .append (instance_id )
        else :
            new_map_objects .append (obj )
    map_objects_wrapper ['values']=new_map_objects 
    removed_broken ,removed_drops =(len (broken_ids ),len (dropped_ids ))
    return {
    'characters':len (all_removed_uids ),
    'pals':removed_pals ,
    'guilds':removed_guilds ,
    'broken_objects':removed_broken ,
    'dropped_items':removed_drops 
    }
def delete_non_base_map_objects (parent =None ):
    if not constants .loaded_level_json :
        return 0 
    wsd =constants .loaded_level_json ['properties']['worldSaveData']['value']
    base_camp_list =wsd ['BaseCampSaveData']['value']
    active_base_ids ={b ['key']for b in base_camp_list }
    map_objs =wsd ['MapObjectSaveData']['value']['values']
    initial_count =len (map_objs )
    new_map_objs =[]
    for m in map_objs :
        raw_data =m .get ('Model',{}).get ('value',{}).get ('RawData',{}).get ('value',{})
        base_camp_id =raw_data .get ('base_camp_id_belong_to')
        instance_id =raw_data .get ('instance_id','UNKNOWN_ID')
        object_name =m .get ('MapObjectId',{}).get ('value','UNKNOWN_OBJECT_TYPE')
        should_keep =False 
        if base_camp_id and base_camp_id in active_base_ids :
            should_keep =True 
        if should_keep :
            new_map_objs .append (m )
        else :
            pass 
    deleted_count =initial_count -len (new_map_objs )
    map_objs [:]=new_map_objs 
    return deleted_count 
def delete_invalid_structure_map_objects (parent =None ):
    if not constants .loaded_level_json :
        return 0 
    import json ,os 
    valid_assets =set ()
    try :
        base_dir =os .path .dirname (os .path .dirname (os .path .abspath (__file__ )))
        fp =os .path .join (base_dir ,'resources','game_data','structuredata.json')
        with open (fp ,'r',encoding ='utf-8')as f :
            js =json .load (f )
            for x in js .get ('structures',[]):
                asset =x .get ('asset')
                if isinstance (asset ,str ):
                    valid_assets .add (asset .lower ())
    except Exception as e :
        return 0 
    wsd =constants .loaded_level_json ['properties']['worldSaveData']['value']
    map_objs =wsd ['MapObjectSaveData']['value']['values']
    initial_count =len (map_objs )
    new_map_objs =[]
    for m in map_objs :
        object_id_node =m .get ('MapObjectId',{})
        object_name =object_id_node .get ('value')
        if isinstance (object_name ,str )and object_name .lower ()in valid_assets :
            new_map_objs .append (m )
        else :
            pass 
    deleted_count =initial_count -len (new_map_objs )
    map_objs [:]=new_map_objs 
    return deleted_count 
def delete_all_skins (parent =None ):
    if not constants .loaded_level_json :
        return 0 
    removed_level_skins =0 
    def clean_level_skins (data ):
        nonlocal removed_level_skins 
        if isinstance (data ,dict ):
            if 'SkinName'in data :
                del data ['SkinName']
                removed_level_skins +=1 
            if 'SkinAppliedCharacterId'in data :
                del data ['SkinAppliedCharacterId']
            for v in list (data .values ()):
                clean_level_skins (v )
        elif isinstance (data ,list ):
            for item in data :
                clean_level_skins (item )
    try :
        wsd =constants .loaded_level_json ['properties']['worldSaveData']['value']
        clean_level_skins (wsd )
    except :
        pass 
    players_dir =os .path .join (constants .current_save_path ,'Players')
    fixed_player_files =0 
    if os .path .exists (players_dir ):
        for filename in os .listdir (players_dir ):
            if filename .endswith ('.sav')and '_dps'not in filename :
                file_path =os .path .join (players_dir ,filename )
                try :
                    p_json =sav_to_json (file_path )
                    changed =False 
                    def remove_skin_info (data ):
                        nonlocal changed 
                        if isinstance (data ,dict ):
                            if 'SkinInventoryInfo'in data :
                                del data ['SkinInventoryInfo']
                                changed =True 
                            for v in list (data .values ()):
                                remove_skin_info (v )
                        elif isinstance (data ,list ):
                            for item in data :
                                remove_skin_info (item )
                    remove_skin_info (p_json )
                    if changed :
                        json_to_sav (p_json ,file_path )
                        fixed_player_files +=1 
                except :
                    pass 
    return removed_level_skins +fixed_player_files 
def unlock_all_private_chests (parent =None ):
    if not constants .loaded_level_json :
        return 0 
    try :
        wsd =constants .loaded_level_json ['properties']['worldSaveData']['value']
    except KeyError :
        return 0 
    count =0 
    def deep_unlock (data ):
        nonlocal count 
        if isinstance (data ,dict ):
            ctype =data .get ('concrete_model_type','')
            if ctype in ('PalMapObjectItemBoothModel','PalMapObjectPalBoothModel'):
                return 
            if 'private_lock_player_uid'in data :
                data ['private_lock_player_uid']='00000000-0000-0000-0000-000000000000'
                count +=1 
            for v in data .values ():
                deep_unlock (v )
        elif isinstance (data ,list ):
            for item in data :
                deep_unlock (item )
    deep_unlock (wsd )
    return count 
def remove_invalid_items_from_level (parent =None ):
    if not constants .loaded_level_json :
        return 0 
    try :
        wsd =constants .loaded_level_json ['properties']['worldSaveData']['value']
    except :
        return 0 
    base_dir =os .path .dirname (os .path .dirname (os .path .abspath (__file__ )))
    valid_items =set ()
    try :
        fp =os .path .join (base_dir ,'resources','game_data','itemdata.json')
        with open (fp ,'r',encoding ='utf-8')as f :
            js =json .load (f )
            for x in js .get ('items',[]):
                aid =x .get ('asset')
                if isinstance (aid ,str ):
                    valid_items .add (aid .lower ())
    except :
        pass 
    removed_count =0 
    def clean_recursive (data ):
        nonlocal removed_count 
        if isinstance (data ,dict ):
            for key in list (data .keys ()):
                val =data [key ]
                if isinstance (val ,(dict ,list )):
                    clean_recursive (val )
        elif isinstance (data ,list ):
            i =len (data )-1 
            while i >=0 :
                item_obj =data [i ]
                if isinstance (item_obj ,dict )and 'RawData'in item_obj :
                    raw_val =item_obj ['RawData'].get ('value',{})
                    sid =None 
                    if isinstance (raw_val ,dict ):
                        if 'item'in raw_val and isinstance (raw_val ['item'],dict ):
                            sid =raw_val ['item'].get ('static_id')
                        elif 'id'in raw_val and isinstance (raw_val ['id'],dict ):
                            sid =raw_val ['id'].get ('static_id')
                    if isinstance (sid ,str )and sid .lower ()not in valid_items :
                        data .pop (i )
                        removed_count +=1 
                    else :
                        clean_recursive (item_obj )
                else :
                    clean_recursive (item_obj )
                i -=1 
    clean_recursive (wsd )
    return removed_count 
def remove_invalid_items_from_save (parent =None ):
    if not constants .current_save_path :
        return 0 
    base_dir =os .path .dirname (os .path .dirname (os .path .abspath (__file__ )))
    valid_items =set ()
    try :
        fp =os .path .join (base_dir ,'resources','game_data','itemdata.json')
        with open (fp ,'r',encoding ='utf-8')as f :
            js =json .load (f )
            for x in js .get ('items',[]):
                aid =x .get ('asset')
                if isinstance (aid ,str ):
                    valid_items .add (aid .lower ())
    except :
        pass 
    players_dir =os .path .join (constants .current_save_path ,'Players')
    if not os .path .exists (players_dir ):
        return 0 
    total_files =0 
    fixed_files =0 
    total_removed =0 
    def clean_craft_records (data ,filename ):
        nonlocal total_removed 
        changed =False 
        if isinstance (data ,dict ):
            if 'CraftItemCount'in data and isinstance (data ['CraftItemCount'].get ('value'),list ):
                old_list =data ['CraftItemCount']['value']
                new_list =[]
                for i in old_list :
                    key =i .get ('key')
                    if isinstance (key ,str )and key .lower ()in valid_items :
                        new_list .append (i )
                    else :
                        changed =True 
                        total_removed +=1 
                if changed :
                    data ['CraftItemCount']['value']=new_list 
            for v in data .values ():
                if clean_craft_records (v ,filename ):
                    changed =True 
        elif isinstance (data ,list ):
            for item in data :
                if clean_craft_records (item ,filename ):
                    changed =True 
        return changed 
    for filename in os .listdir (players_dir ):
        if filename .endswith ('.sav')and '_dps'not in filename :
            total_files +=1 
            file_path =os .path .join (players_dir ,filename )
            try :
                p_json =sav_to_json (file_path )
                if clean_craft_records (p_json ,filename ):
                    json_to_sav (p_json ,file_path )
                    fixed_files +=1 
            except Exception as e :
                pass 
    remove_invalid_items_from_level (parent )
    return fixed_files 
def remove_invalid_pals_from_save (parent =None ):
    base_dir =os .path .dirname (os .path .dirname (os .path .abspath (__file__ )))
    def load_assets (fname ,key ):
        try :
            fp =os .path .join (base_dir ,'resources','game_data',fname )
            with open (fp ,'r',encoding ='utf-8')as f :
                data =json .load (f )
                return set ((x ['asset'].lower ()for x in data .get (key ,[])))
        except :
            return set ()
    valid_pals =load_assets ('paldata.json','pals')
    valid_npcs =load_assets ('npcdata.json','npcs')
    valid_all =valid_pals |valid_npcs 
    if not constants .current_save_path or not constants .loaded_level_json :
        return 0 
    try :
        wsd =constants .loaded_level_json ['properties']['worldSaveData']['value']
    except :
        return 0 
    cmap =wsd .get ('CharacterSaveParameterMap',{}).get ('value',[])
    removed_ids =set ()
    removed =0 
    def get_char_id (e ):
        try :
            return e ['value']['RawData']['value']['object']['SaveParameter']['value']['CharacterID']['value']
        except :
            return None 
    filtered =[]
    for entry in cmap :
        cid =get_char_id (entry )
        if cid and cid .lower ()not in valid_all :
            inst =str (entry ['key']['InstanceId']['value'])
            removed_ids .add (inst )
            removed +=1 
            continue 
        filtered .append (entry )
    wsd ['CharacterSaveParameterMap']['value']=filtered 
    containers =wsd .get ('CharacterContainerSaveData',{}).get ('value',[])
    for cont in containers :
        try :
            slots =cont ['value']['Slots']['value']['values']
        except :
            continue 
        newslots =[]
        for s in slots :
            inst =s .get ('RawData',{}).get ('value',{}).get ('instance_id')
            if inst and str (inst )in removed_ids :
                continue 
            newslots .append (s )
        cont ['value']['Slots']['value']['values']=newslots 
    return removed 
def fix_missions (parent =None ):
    if not constants .current_save_path :
        return {'total':0 ,'fixed':0 ,'skipped':0 }
    save_path =os .path .join (constants .current_save_path ,'Players')
    if not os .path .exists (save_path ):
        return {'total':0 ,'fixed':0 ,'skipped':0 }
    total =0 
    fixed =0 
    skipped =0 
    def deep_delete_completed_quest_array (data ):
        found =False 
        if isinstance (data ,dict ):
            if 'CompletedQuestArray'in data :
                data ['CompletedQuestArray']['value']['values']=[]
                return True 
            for v in data .values ():
                if deep_delete_completed_quest_array (v ):
                    found =True 
        elif isinstance (data ,list ):
            for item in data :
                if deep_delete_completed_quest_array (item ):
                    found =True 
        return found 
    for filename in os .listdir (save_path ):
        if filename .endswith ('.sav')and '_dps'not in filename :
            total +=1 
            file_path =os .path .join (save_path ,filename )
            try :
                player_json =sav_to_json (file_path )
            except Exception as e :
                skipped +=1 
                continue 
            if deep_delete_completed_quest_array (player_json ):
                try :
                    json_to_sav (player_json ,file_path )
                    fixed +=1 
                except Exception as e :
                    skipped +=1 
            else :
                skipped +=1 
    return {'total':total ,'fixed':fixed ,'skipped':skipped }
def reset_anti_air_turrets (parent =None ):
    if not constants .loaded_level_json :
        return None 
    try :
        wsd =constants .loaded_level_json ['properties']['worldSaveData']['value']
    except KeyError :
        return None 
    if 'FixedWeaponDestroySaveData'in wsd :
        data =wsd ['FixedWeaponDestroySaveData']
        count =0 
        if isinstance (data ,dict ):
            values =data .get ('value',[])
            if isinstance (values ,list ):
                count =len (values )
            elif isinstance (values ,dict ):
                count =len (values .get ('values',[]))
        del wsd ['FixedWeaponDestroySaveData']
        return count if count >0 else 1 
    return 0 
def reset_dungeons (parent =None ):
    if not constants .loaded_level_json :
        return None 
    try :
        wsd =constants .loaded_level_json ['properties']['worldSaveData']['value']
    except KeyError :
        return None 
    if 'DungeonPointMarkerSaveData'in wsd :
        data =wsd ['DungeonPointMarkerSaveData']
        count =0 
        if isinstance (data ,dict ):
            values =data .get ('value',[])
            if isinstance (values ,list ):
                count =len (values )
            elif isinstance (values ,dict ):
                count =len (values .get ('values',[]))
        del wsd ['DungeonPointMarkerSaveData']
        return count if count >0 else 1 
    return 0 
def unlock_viewing_cage_for_player (player_uid ,parent =None ):
    if not constants .current_save_path :
        return False 
    player_id =str (player_uid ).replace ('-','').lower ()
    file_path =os .path .join (constants .current_save_path ,'Players',f'{player_id .zfill (32 )}.sav')
    if not os .path .exists (file_path ):
        return False 
    try :
        p_json =sav_to_json (file_path )
        changed =False 
        def inject_viewing_cage (data ):
            nonlocal changed 
            if isinstance (data ,dict ):
                if 'UnlockedRecipeTechnologyNames'in data :
                    values_list =data ['UnlockedRecipeTechnologyNames']['value']['values']
                    if 'DisplayCharacter'not in values_list :
                        values_list .append ('DisplayCharacter')
                        changed =True 
                for v in data .values ():
                    inject_viewing_cage (v )
            elif isinstance (data ,list ):
                for item in data :
                    inject_viewing_cage (item )
        inject_viewing_cage (p_json )
        if changed :
            json_to_sav (p_json ,file_path )
            return True 
        return False 
    except Exception as e :
        return False 
def detect_and_trim_overfilled_inventories (parent =None ):
    import copy 
    if not constants .current_save_path :
        return 0 
    players_dir =os .path .join (constants .current_save_path ,'Players')
    if not os .path .exists (players_dir ):
        return 0 
    player_files =[f for f in os .listdir (players_dir )if f .endswith ('.sav')and '_dps'not in f ]
    fixed_containers =0 
    try :
        wsd =constants .loaded_level_json ['properties']['worldSaveData']['value']
        item_containers =wsd .get ('ItemContainerSaveData',{}).get ('value',[])
        container_lookup ={str (c ['key']['ID']['value']):c for c in item_containers if 'key'in c }
        for player_file in player_files :
            player_uid =player_file .replace ('.sav','')
            try :
                player_path =os .path .join (players_dir ,player_file )
                player_json =sav_to_json (player_path )
                if 'properties'in player_json and 'SaveData'in player_json ['properties']:
                    inv_info =player_json ['properties']['SaveData']['value']['InventoryInfo']['value']
                elif 'SaveData'in player_json :
                    inv_info =player_json ['SaveData']['value']['InventoryInfo']['value']
                else :
                    continue 
                main_id =str (inv_info ['CommonContainerId']['value']['ID']['value'])
                key_id =str (inv_info ['EssentialContainerId']['value']['ID']['value'])
                additional_inventory_count =0 
                if key_id in container_lookup :
                    key_slots =container_lookup [key_id ]['value']['Slots']['value']['values']
                    additional_items =['AdditionalInventory_001','AdditionalInventory_002','AdditionalInventory_003','AdditionalInventory_004']
                    for slot in key_slots :
                        try :
                            item_id =slot .get ('RawData',{}).get ('value',{}).get ('item',{}).get ('static_id','')
                            if item_id in additional_items :
                                additional_inventory_count +=1 
                        except :
                            continue 
                player_max_slots =42 +(additional_inventory_count *3 )
                if main_id in container_lookup :
                    container =container_lookup [main_id ]
                    slots =container ['value']['Slots']['value']['values']
                    current_slot_num =container ['value'].get ('SlotNum',{}).get ('value',0 )
                    if len (slots )!=player_max_slots or current_slot_num !=player_max_slots :
                        if len (slots )>=player_max_slots or (len (slots )<player_max_slots and len (slots )>=42 ):
                            if len (slots )>player_max_slots :
                                slots [:]=slots [:player_max_slots ]
                            elif len (slots )<player_max_slots :
                                if len (slots )>0 :
                                    template_slot =copy .deepcopy (slots [0 ])
                                    template_slot ['RawData']['value']['item']['static_id']=""
                                    template_slot ['RawData']['value']['item']['dynamic_id']['created_world_id']="00000000-0000-0000-0000-000000000000"
                                    template_slot ['RawData']['value']['item']['dynamic_id']['local_id']="00000000-0000-0000-0000-000000000000"
                                    template_slot ['RawData']['value']['count']=0 
                                    while len (slots )<player_max_slots :
                                        slots .append (copy .deepcopy (template_slot ))
                            if 'SlotNum'in container ['value']:
                                container ['value']['SlotNum']['value']=len (slots )
                            fixed_containers +=1 
            except Exception as e :
                pass 
        return fixed_containers 
    except Exception as e :
        return 0 
def fix_all_negative_timestamps (parent =None ):
    if not constants .loaded_level_json :
        return 0 
    fixed_count =0 
    try :
        wsd =constants .loaded_level_json ['properties']['worldSaveData']['value']
        if 'GameTimeSaveData'not in wsd :
            return 0 
        current_tick =int (wsd ['GameTimeSaveData']['value']['RealDateTimeTicks']['value'])
        if 'CharacterSaveParameterMap'in wsd :
            for char in wsd ['CharacterSaveParameterMap']['value']:
                try :
                    raw =char ['value']['RawData']['value']
                    if 'last_online_real_time'in raw :
                        last_time =raw .get ('last_online_real_time')
                        if last_time and int (last_time )>current_tick :
                            raw ['last_online_real_time']=current_tick 
                            fixed_count +=1 
                    if 'object'in raw and 'SaveParameter'in raw ['object']:
                        p =raw ['object']['SaveParameter']['value']
                        if 'LastOnlineRealTime'in p :
                            last_time =p ['LastOnlineRealTime'].get ('value')
                            if last_time and int (last_time )>current_tick :
                                p ['LastOnlineRealTime']['value']=current_tick 
                                fixed_count +=1 
                except :
                    continue 
        if 'GroupSaveDataMap'in wsd :
            group_map =wsd ['GroupSaveDataMap']['value']
            for gdata in group_map :
                try :
                    if gdata ['value']['GroupType']['value']['value']!='EPalGroupType::Guild':
                        continue 
                    players =gdata ['value']['RawData']['value'].get ('players',[])
                    for p_info in players :
                        if 'player_info'in p_info and 'last_online_real_time'in p_info ['player_info']:
                            last_time =p_info ['player_info'].get ('last_online_real_time')
                            if last_time and int (last_time )>current_tick :
                                p_info ['player_info']['last_online_real_time']=current_tick 
                                fixed_count +=1 
                except :
                    continue 
    except Exception as e :
        pass 
    return fixed_count 
def reset_selected_player_timestamp (player_uid ,parent =None ):
    if not constants .loaded_level_json :
        return False 
    try :
        uid_clean =str (player_uid ).replace ('-','').lower ()
        wsd =constants .loaded_level_json ['properties']['worldSaveData']['value']
        current_tick =int (wsd ['GameTimeSaveData']['value']['RealDateTimeTicks']['value'])
        if 'CharacterSaveParameterMap'in wsd :
            for char in wsd ['CharacterSaveParameterMap']['value']:
                char_uid =str (char ['key']['PlayerUId']['value']).replace ('-','').lower ()
                if char_uid ==uid_clean :
                    raw =char ['value']['RawData']['value']
                    raw ['last_online_real_time']=current_tick 
                    if 'object'in raw and 'SaveParameter'in raw ['object']:
                        p =raw ['object']['SaveParameter']['value']
                        if 'LastOnlineRealTime'in p :
                            p ['LastOnlineRealTime']['value']=current_tick 
        if 'GroupSaveDataMap'in wsd :
            group_map =wsd ['GroupSaveDataMap']['value']
            items =group_map .items ()if isinstance (group_map ,dict )else enumerate (group_map )
            for _ ,gdata in items :
                players =gdata ['value']['RawData']['value'].get ('players',[])
                for p_info in players :
                    if str (p_info .get ('player_uid','')).replace ('-','').lower ()==uid_clean :
                        if 'player_info'in p_info :
                            p_info ['player_info']['last_online_real_time']=current_tick 
        return True 
    except Exception as e :
        return False 
