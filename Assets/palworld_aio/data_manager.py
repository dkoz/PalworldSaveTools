import os 
import json 
import palworld_coord 
from palworld_save_tools .archive import UUID 
from i18n import t 
try :
    from palworld_aio import constants 
    from palworld_aio .utils import are_equal_uuids ,as_uuid ,fast_deepcopy 
except ImportError :
    from .import constants 
    from .utils import are_equal_uuids ,as_uuid ,fast_deepcopy 
def get_tick ():
    return constants .loaded_level_json ['properties']['worldSaveData']['value']['GameTimeSaveData']['value']['RealDateTimeTicks']['value']
def get_guilds ():
    if not constants .loaded_level_json :
        return []
    out =[]
    wsd =constants .loaded_level_json ['properties']['worldSaveData']['value']
    for g in wsd ['GroupSaveDataMap']['value']:
        if g ['value']['GroupType']['value']['value']!='EPalGroupType::Guild':
            continue 
        gid =str (g ['key'])
        gname =g ['value']['RawData']['value'].get ('guild_name','Unknown')
        out .append ({'id':gid ,'name':gname })
    return out 
def get_guild_members (gid ):
    if not constants .loaded_level_json :
        return []
    wsd =constants .loaded_level_json ['properties']['worldSaveData']['value']
    tick =get_tick ()
    target =as_uuid (gid )
    for g in wsd ['GroupSaveDataMap']['value']:
        if g ['value']['GroupType']['value']['value']!='EPalGroupType::Guild':
            continue 
        if as_uuid (g ['key'])!=target :
            continue 
        admin_uid =as_uuid (g ['value']['RawData']['value'].get ('admin_player_uid',''))
        out =[]
        for p in g ['value']['RawData']['value'].get ('players',[]):
            uid =str (p .get ('player_uid',''))
            name =p .get ('player_info',{}).get ('player_name','Unknown')
            last =p .get ('player_info',{}).get ('last_online_real_time')
            lastseen ='Unknown'
            if last is not None :
                from .utils import format_duration_short 
                lastseen =format_duration_short ((tick -last )/10000000.0 )
            level =constants .player_levels .get (uid .replace ('-',''),'?')
            pals =constants .PLAYER_PAL_COUNTS .get (uid .lower (),0 )
            is_leader =as_uuid (uid )==admin_uid 
            out .append ({'uid':uid ,'name':name ,'lastseen':lastseen ,'level':level ,'pals':pals ,'is_leader':is_leader })
        return out 
    return []
def get_bases ():
    if not constants .loaded_level_json :
        return []
    out =[]
    wsd =constants .loaded_level_json ['properties']['worldSaveData']['value']
    base_list =wsd .get ('BaseCampSaveData',{}).get ('value',[])
    for b in base_list :
        bid =str (b ['key'])
        lookup =constants .base_guild_lookup .get (bid .lower (),{})
        gid =lookup .get ('GuildID','Unknown')
        gname =lookup .get ('GuildName','Unknown')
        out .append ({'id':bid ,'guild_id':gid ,'guild_name':gname })
    return out 
def get_base_coords (base_id ):
    if not constants .loaded_level_json :
        return (None ,None )
    wsd =constants .loaded_level_json ['properties']['worldSaveData']['value']
    for b in wsd .get ('BaseCampSaveData',{}).get ('value',[]):
        if are_equal_uuids (b ['key'],base_id ):
            try :
                trans =b ['value']['RawData']['value']['transform']['translation']
                return palworld_coord .sav_to_map (trans ['x'],trans ['y'],new =True )
            except :
                return (None ,None )
    return (None ,None )
def delete_base_camp (base_entry ,guild_id ,level_json =None ):
    if level_json is None :
        level_json =constants .loaded_level_json 
    wsd =level_json ['properties']['worldSaveData']['value']
    group_map =wsd .get ('GroupSaveDataMap',{}).get ('value',[])
    base_list =wsd .get ('BaseCampSaveData',{}).get ('value',[])
    containers_char =wsd .get ('CharacterContainerSaveData',{}).get ('value',[])
    containers_item =wsd .get ('ItemContainerSaveData',{}).get ('value',[])
    map_objs =wsd .get ('MapObjectSaveData',{}).get ('value',{}).get ('values',[])
    work_root =wsd .get ('WorkSaveData',{})
    work_entries =work_root .get ('value',{}).get ('values',[])if isinstance (work_root .get ('value'),dict )else []
    char_map =wsd .get ('CharacterSaveParameterMap',{}).get ('value',[])
    base_id_str =str (base_entry ['key'])
    base_id_low =base_id_str .replace ('-','').lower ()
    worker_cont_id =None 
    try :
        worker_cont_id =str (base_entry ['value']['WorkerDirector']['value']['RawData']['value']['container_id']).replace ('-','').lower ()
    except :
        pass 
    cont_ids_to_del =set ()
    if worker_cont_id :
        cont_ids_to_del .add (worker_cont_id )
    for obj in map_objs :
        mr =obj .get ('Model',{}).get ('value',{}).get ('RawData',{}).get ('value',{})
        if str (mr .get ('base_camp_id_belong_to','')).replace ('-','').lower ()==base_id_low :
            try :
                mm =obj ['ConcreteModel']['value']['ModuleMap']['value']
                for mod in mm :
                    raw_mod =mod .get ('value',{}).get ('RawData',{}).get ('value',{})
                    if 'target_container_id'in raw_mod :
                        cont_ids_to_del .add (str (raw_mod ['target_container_id']).replace ('-','').lower ())
            except :
                pass 
    map_objs [:]=[obj for obj in map_objs if str (obj .get ('Model',{}).get ('value',{}).get ('RawData',{}).get ('value',{}).get ('base_camp_id_belong_to','')).replace ('-','').lower ()!=base_id_low ]
    containers_item [:]=[c for c in containers_item if str (c .get ('key',{}).get ('ID',{}).get ('value','')).replace ('-','').lower ()not in cont_ids_to_del ]
    containers_char [:]=[c for c in containers_char if str (c .get ('key',{}).get ('ID',{}).get ('value','')).replace ('-','').lower ()not in cont_ids_to_del ]
    def should_keep_work_entry (we ):
        try :
            wr =we ['RawData']['value']
            return str (wr .get ('base_camp_id_belong_to','')).replace ('-','').lower ()!=base_id_low 
        except :
            return True 
    work_entries [:]=[we for we in work_entries if should_keep_work_entry (we )]
    zero =UUID .from_str ('00000000-0000-0000-0000-000000000000')
    if worker_cont_id :
        for ch in char_map :
            try :
                raw =ch ['value']['RawData']['value']
                sp =raw ['object']['SaveParameter']['value']
                if sp .get ('IsPlayer',{}).get ('value'):
                    continue 
                slot_id =sp .get ('SlotId',{}).get ('value',{}).get ('ContainerId',{}).get ('value',{}).get ('ID',{}).get ('value')
                if slot_id and str (slot_id ).replace ('-','').lower ()==worker_cont_id :
                    sp ['SlotId']['value']['ContainerId']['value']['ID']['value']=zero 
                    raw ['group_id']=zero 
            except :
                pass 
    base_list [:]=[b for b in base_list if b !=base_entry ]
    for g in group_map :
        if are_equal_uuids (g ['key'],guild_id ):
            raw =g ['value']['RawData']['value']
            raw ['base_ids']=[b for b in raw .get ('base_ids',[])if not are_equal_uuids (b ,base_id_str )]
            raw ['map_object_instance_ids_base_camp_points']=[i for i in raw .get ('map_object_instance_ids_base_camp_points',[])if not are_equal_uuids (i ,base_id_str )]
            break 
def delete_guild (guild_id ):
    wsd =constants .loaded_level_json ['properties']['worldSaveData']['value']
    group_map =wsd .get ('GroupSaveDataMap',{}).get ('value',[])
    base_list =wsd .get ('BaseCampSaveData',{}).get ('value',[])
    char_map =wsd .get ('CharacterSaveParameterMap',{}).get ('value',[])
    load_exclusions ()
    guild_id_clean =str (guild_id ).replace ('-','').lower ()
    if guild_id_clean in [ex .replace ('-','').lower ()for ex in constants .exclusions .get ('guilds',[])]:
        print (f'Guild {guild_id } is in exclusion list - skipping deletion')
        return False 
    target_g =None 
    for g in group_map :
        if are_equal_uuids (g ['key'],guild_id ):
            if g ['value']['GroupType']['value']['value']=='EPalGroupType::Guild':
                target_g =g 
            break 
    if not target_g :
        return False 
    for b in base_list [:]:
        try :
            if are_equal_uuids (b ['value']['RawData']['value'].get ('group_id_belong_to'),guild_id ):
                base_id =str (b ['key']).replace ('-','').lower ()
                if base_id in [ex .replace ('-','').lower ()for ex in constants .exclusions .get ('bases',[])]:
                    print (f'Guild {guild_id } has excluded base {base_id } - cannot delete guild')
                    return False 
        except :
            pass 
    deleted_uids =set ()
    for p in target_g ['value']['RawData']['value'].get ('players',[]):
        player_id =str (p .get ('player_uid','')).replace ('-','').lower ()
        if player_id in [ex .replace ('-','').lower ()for ex in constants .exclusions .get ('players',[])]:
            print (f'Guild {guild_id } has excluded player {player_id } - cannot delete guild')
            return False 
        deleted_uids .add (player_id )
    for b in base_list [:]:
        try :
            if are_equal_uuids (b ['value']['RawData']['value'].get ('group_id_belong_to'),guild_id ):
                delete_base_camp (b ,guild_id )
        except :
            pass 
    for ch in char_map [:]:
        try :
            raw =ch ['value']['RawData']['value']
            sp =raw ['object']['SaveParameter']['value']
            if sp .get ('IsPlayer',{}).get ('value'):
                char_uid =str (ch ['key']['PlayerUId']['value']).replace ('-','').lower ()
                if char_uid in deleted_uids :
                    char_map .remove (ch )
                    continue 
            owner =sp .get ('OwnerPlayerUId',{}).get ('value')
            if owner and str (owner ).replace ('-','').lower ()in deleted_uids :
                char_map .remove (ch )
        except :
            pass 
    for uid in deleted_uids :
        constants .files_to_delete .add (uid )
    group_map .remove (target_g )
    return True 
def delete_player (uid ,delete_files =True ):
    wsd =constants .loaded_level_json ['properties']['worldSaveData']['value']
    group_map =wsd .get ('GroupSaveDataMap',{}).get ('value',[])
    char_map =wsd .get ('CharacterSaveParameterMap',{}).get ('value',[])
    base_list =wsd .get ('BaseCampSaveData',{}).get ('value',[])
    uid_clean =str (uid ).replace ('-','').lower ()
    zero =UUID .from_str ('00000000-0000-0000-0000-000000000000')
    for ch in char_map [:]:
        try :
            raw =ch ['value']['RawData']['value']
            sp =raw ['object']['SaveParameter']['value']
            if sp .get ('IsPlayer',{}).get ('value'):
                p_uid =ch ['key']['PlayerUId']['value']
                if str (p_uid ).replace ('-','').lower ()==uid_clean :
                    char_map .remove (ch )
                    continue 
            owner =sp .get ('OwnerPlayerUId',{}).get ('value')
            if owner and str (owner ).replace ('-','').lower ()==uid_clean :
                char_map .remove (ch )
        except :
            pass 
    for g in group_map [:]:
        if g ['value']['GroupType']['value']['value']!='EPalGroupType::Guild':
            continue 
        raw =g ['value']['RawData']['value']
        players =raw .get ('players',[])
        new_players =[p for p in players if str (p .get ('player_uid','')).replace ('-','').lower ()!=uid_clean ]
        if len (new_players )==len (players ):
            continue 
        raw ['players']=new_players 
        if not new_players :
            gid =g ['key']
            for b in base_list [:]:
                try :
                    if are_equal_uuids (b ['value']['RawData']['value'].get ('group_id_belong_to'),gid ):
                        delete_base_camp (b ,gid )
                except :
                    pass 
            group_map .remove (g )
        else :
            admin =str (raw .get ('admin_player_uid','')).replace ('-','').lower ()
            if admin ==uid_clean :
                raw ['admin_player_uid']=new_players [0 ]['player_uid']
    if delete_files :
        constants .files_to_delete .add (uid_clean )
    return True 
def load_exclusions ():
    try :
        with open (constants .EXCLUSIONS_FILE ,'r',encoding ='utf-8')as f :
            data =json .load (f )
            constants .exclusions ={
            'guilds':data .get ('guilds',[]),
            'players':data .get ('players',[]),
            'bases':data .get ('bases',[])
            }
    except :
        constants .exclusions ={'guilds':[],'players':[],'bases':[]}
def save_exclusions ():
    with open (constants .EXCLUSIONS_FILE ,'w',encoding ='utf-8')as f :
        json .dump (constants .exclusions ,f ,indent =4 )
