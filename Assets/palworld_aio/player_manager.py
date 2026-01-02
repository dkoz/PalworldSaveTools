import os 
from i18n import t 
try :
    from palworld_aio import constants 
    from palworld_aio .utils import are_equal_uuids ,as_uuid ,sav_to_json ,json_to_sav 
    from palworld_aio .data_manager import delete_player 
except ImportError :
    from .import constants 
    from .utils import are_equal_uuids ,as_uuid ,sav_to_json ,json_to_sav 
    from .data_manager import delete_player 
def rename_player (player_uid ,new_name ):
    if not constants .loaded_level_json :
        return False 
    p_uid_clean =str (player_uid ).replace ('-','')
    wsd =constants .loaded_level_json ['properties']['worldSaveData']['value']
    for g in wsd ['GroupSaveDataMap']['value']:
        raw =g ['value']['RawData']['value']
        found =False 
        for p in raw .get ('players',[]):
            uid =str (p .get ('player_uid','')).replace ('-','')
            if uid ==p_uid_clean :
                p .setdefault ('player_info',{})['player_name']=new_name 
                found =True 
                break 
        if found :
            break 
    char_map =wsd .get ('CharacterSaveParameterMap',{}).get ('value',[])
    for entry in char_map :
        raw =entry .get ('value',{}).get ('RawData',{}).get ('value',{})
        sp_val =raw .get ('object',{}).get ('SaveParameter',{}).get ('value',{})
        if sp_val .get ('IsPlayer',{}).get ('value'):
            uid_obj =entry .get ('key',{}).get ('PlayerUId',{})
            uid =str (uid_obj .get ('value','')).replace ('-','')if isinstance (uid_obj ,dict )else ''
            if uid ==p_uid_clean :
                sp_val .setdefault ('NickName',{})['value']=new_name 
                break 
    return True 
def get_player_info (player_uid ):
    if not constants .loaded_level_json :
        return None 
    uid_clean =str (player_uid ).replace ('-','').lower ()
    wsd =constants .loaded_level_json ['properties']['worldSaveData']['value']
    tick =wsd ['GameTimeSaveData']['value']['RealDateTimeTicks']['value']
    for g in wsd ['GroupSaveDataMap']['value']:
        if g ['value']['GroupType']['value']['value']!='EPalGroupType::Guild':
            continue 
        gid =str (g ['key'])
        gname =g ['value']['RawData']['value'].get ('guild_name','Unknown Guild')
        for p in g ['value']['RawData']['value'].get ('players',[]):
            uid =str (p .get ('player_uid','')).replace ('-','').lower ()
            if uid ==uid_clean :
                name =p .get ('player_info',{}).get ('player_name','Unknown')
                last =p .get ('player_info',{}).get ('last_online_real_time')
                from .utils import format_duration_short 
                lastseen ='Unknown'if last is None else format_duration_short ((tick -last )/10000000.0 )
                level =constants .player_levels .get (uid ,'?')
                pals =constants .PLAYER_PAL_COUNTS .get (uid ,0 )
                return {
                'uid':player_uid ,
                'name':name ,
                'level':level ,
                'pals':pals ,
                'lastseen':lastseen ,
                'guild_id':gid ,
                'guild_name':gname 
                }
    return None 
def get_player_pal_count (player_uid ):
    uid =str (player_uid ).replace ('-','').lower ()
    return constants .PLAYER_PAL_COUNTS .get (uid ,0 )
def unlock_viewing_cage (player_uid ):
    if not constants .current_save_path :
        return False 
    uid_clean =str (player_uid ).replace ('-','')
    sav_file =os .path .join (constants .current_save_path ,'Players',f'{uid_clean }.sav')
    if not os .path .exists (sav_file ):
        return False 
    try :
        p_json =sav_to_json (sav_file )
        save_data =p_json .get ('properties',{}).get ('SaveData',{}).get ('value',{})
        if 'bIsViewingCageCanUse'not in save_data :
            return False 
        save_data ['bIsViewingCageCanUse']['value']=True 
        json_to_sav (p_json ,sav_file )
        return True 
    except Exception as e :
        print (f'Error unlocking viewing cage: {e }')
        return False 
