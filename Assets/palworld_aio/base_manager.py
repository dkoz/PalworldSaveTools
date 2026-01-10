import os 
import json 
import uuid 
import copy 
import math 
import random 
from palworld_save_tools .archive import UUID as PalUUID 
from i18n import t 
try :
    from palworld_aio import constants 
    from palworld_aio .utils import fast_deepcopy ,are_equal_uuids ,as_uuid 
    from palworld_aio .data_manager import delete_base_camp 
except ImportError :
    from .import constants 
    from .utils import fast_deepcopy ,are_equal_uuids ,as_uuid 
    from .data_manager import delete_base_camp 
def _s (x ):
    return str (x ).lower ()
def _new_uuid ():
    return PalUUID (uuid .uuid4 ().bytes )
def _zero ():
    return PalUUID (uuid .UUID ('00000000-0000-0000-0000-000000000000').bytes )
def _clear_char_container_slots (container_obj ):
    try :
        container_obj ['value']['Slots']['value']['values']=[]
    except :
        pass 
def _iter_work_savedata_entries (work_root ):
    if not isinstance (work_root ,dict ):
        return []
    v =work_root .get ('value',{})
    if isinstance (v ,dict ):
        return v .get ('values',[])if isinstance (v .get ('values',[]),list )else []
    return []
def _get_work_raw (work_entry ):
    try :
        return work_entry ['RawData']['value']
    except :
        return None 
def _get_model_raw (map_obj ):
    try :
        return map_obj ['Model']['value']['RawData']['value']
    except :
        return None 
def _get_concrete_raw (map_obj ):
    try :
        return map_obj ['ConcreteModel']['value']['RawData']['value']
    except :
        return None 
def _offset_translation (t_vec ,final_offset ):
    try :
        t_vec ['x']+=final_offset [0 ]
        t_vec ['y']+=final_offset [1 ]
        t_vec ['z']+=final_offset [2 ]
    except :
        pass 
def is_old_blueprint (exported_data ):
    if not isinstance (exported_data ,dict ):
        return True 
    return 'dynamic_items'not in exported_data or 'base_camp_level'not in exported_data 
def validate_blueprint_version (exported_data ):
    if is_old_blueprint (exported_data ):
        msg =t ('blueprint.error.outdated')if t else 'This blueprint was created with an older version. Please re-export the base.'
        return (False ,msg )
    msg =t ('blueprint.status.up_to_date')if t else 'Blueprint is up to date.'
    return (True ,msg )
def export_base_json (loaded_level_json ,source_base_id ):
    raw_prop =loaded_level_json ['properties']['worldSaveData']['value']
    data =raw_prop if isinstance (raw_prop ,dict )else {}
    base_camp_data =data .get ('BaseCampSaveData',{}).get ('value',[])
    char_containers =data .get ('CharacterContainerSaveData',{}).get ('value',[])
    item_containers =data .get ('ItemContainerSaveData',{}).get ('value',[])
    map_objs =data .get ('MapObjectSaveData',{}).get ('value',{}).get ('values',[])
    char_map =data .get ('CharacterSaveParameterMap',{}).get ('value',[])
    group_map =data .get ('GroupSaveDataMap',{}).get ('value',[])
    work_root =data .get ('WorkSaveData',{})
    work_entries =_iter_work_savedata_entries (work_root )
    src_id_str =_s (source_base_id )
    src_base_entry =next ((b for b in base_camp_data if _s (b .get ('key'))==src_id_str ),None )
    if not src_base_entry :
        return None 
    base_level =1 
    group_id_str =_s (src_base_entry ['value']['RawData']['value'].get ('group_id_belong_to',''))
    for g in group_map :
        if _s (g ['key'])==group_id_str :
            base_level =g ['value']['RawData']['value'].get ('base_camp_level',1 )
            break 
    try :
        _deep =fast_deepcopy 
    except :
        _deep =copy .deepcopy 
    export_data ={
    'base_camp':_deep (src_base_entry ),
    'base_camp_level':base_level ,
    'map_objects':[],
    'characters':[],
    'item_containers':[],
    'char_containers':[],
    'works':[],
    'dynamic_items':[]
    }
    all_dyn_items =data .get ('DynamicItemSaveData',{}).get ('value',{}).get ('values',[])
    try :
        src_worker_container_id =_s (src_base_entry ['value']['WorkerDirector']['value']['RawData']['value']['container_id'])
        w_cont =next ((c for c in char_containers if _s (c .get ('key',{}).get ('ID',{}).get ('value'))==src_worker_container_id ),None )
        if w_cont :
            export_data ['char_containers'].append (_deep (w_cont ))
            char_instance_ids ={_s (slot .get ('RawData',{}).get ('value',{}).get ('instance_id','00000000-0000-0000-0000-000000000000'))
            for slot in w_cont ['value']['Slots']['value'].get ('values',[])}
            for char_entry in char_map :
                if _s (char_entry ['key']['InstanceId']['value'])in char_instance_ids :
                    export_data ['characters'].append (_deep (char_entry ))
    except :
        pass 
    base_map_objects =[obj for obj in map_objs 
    if isinstance (_get_model_raw (obj ),dict )and 
    _s (_get_model_raw (obj ).get ('base_camp_id_belong_to',''))==src_id_str ]
    for obj in base_map_objects :
        oid =str (obj .get ('MapObjectId',{}).get ('value',''))
        if oid in ['PalBooth','ItemBooth']:
            print (f"Skipping map object {oid } due to known issues")
            continue 
        if oid .startswith ('PalEgg')and 'Hatching'not in oid and ('Incubator'not in oid ):
            continue 
        export_data ['map_objects'].append (_deep (obj ))
        try :
            mm =obj ['ConcreteModel']['value']['ModuleMap']['value']
            for mod in mm :
                raw_mod =mod .get ('value',{}).get ('RawData',{}).get ('value',{})
                if 'target_container_id'not in raw_mod :
                    continue 
                cid =_s (raw_mod .get ('target_container_id',''))
                if 'ItemContainer'in str (mod .get ('key','')):
                    ic =next ((c for c in item_containers if _s (c .get ('key',{}).get ('ID',{}).get ('value'))==cid ),None )
                    if ic :
                        nic =_deep (ic )
                        item_slots =nic ['value']['Slots']['value'].get ('values',[])
                        cleaned_slots =[]
                        for slot in item_slots :
                            s_raw =slot .get ('RawData',{}).get ('value',{})
                            s_id =str (s_raw .get ('item',{}).get ('static_id',''))
                            if s_id .startswith ('PalEgg_'):
                                continue 
                            loc_id =_s (s_raw .get ('item',{}).get ('dynamic_id',{}).get ('local_id_in_created_world','00000000-0000-0000-0000-000000000000'))
                            if loc_id !='00000000-0000-0000-0000-000000000000':
                                d_entry =next ((d for d in all_dyn_items if _s (d ['RawData']['value']['id']['local_id_in_created_world'])==loc_id ),None )
                                if d_entry :
                                    export_data ['dynamic_items'].append (_deep (d_entry ))
                            cleaned_slots .append (slot )
                        nic ['value']['Slots']['value']['values']=cleaned_slots 
                        export_data ['item_containers'].append (nic )
                elif 'CharacterContainer'in str (mod .get ('key','')):
                    cc =next ((c for c in char_containers if _s (c .get ('key',{}).get ('ID',{}).get ('value'))==cid ),None )
                    if cc :
                        export_data ['char_containers'].append (_deep (cc ))
        except :
            pass 
    for we in work_entries :
        wr =_get_work_raw (we )
        if wr and _s (wr .get ('base_camp_id_belong_to',''))==src_id_str :
            export_data ['works'].append (_deep (we ))
    return export_data 
def import_base_json (loaded_level_json ,exported_data ,target_guild_id ,offset =(8000 ,0 ,0 ),collision_threshold =5000 ):
    success ,msg =validate_blueprint_version (exported_data )
    if not success :
        return False 
    try :
        _deep =fast_deepcopy 
    except :
        _deep =copy .deepcopy 
    raw_prop =loaded_level_json ['properties']['worldSaveData']['value']
    data =raw_prop if isinstance (raw_prop ,dict )else {}
    base_camp_data =data .get ('BaseCampSaveData',{}).get ('value',[])
    if not base_camp_data or len (base_camp_data )==0 :
        return False 
    groups =data .get ('GroupSaveDataMap',{}).get ('value',[])
    char_containers =data .get ('CharacterContainerSaveData',{}).get ('value',[])
    item_containers =data .get ('ItemContainerSaveData',{}).get ('value',[])
    dynamic_item_data =data .get ('DynamicItemSaveData',{}).get ('value',{}).get ('values',[])
    map_objs =data .get ('MapObjectSaveData',{}).get ('value',{}).get ('values',[])
    char_map =data .get ('CharacterSaveParameterMap',{}).get ('value',[])
    work_root =data .get ('WorkSaveData',{})
    work_entries =_iter_work_savedata_entries (work_root )
    z =_zero ()
    tgt_gid_str =_s (target_guild_id )
    target_group =next ((g for g in groups if _s (g .get ('key'))==tgt_gid_str ),None )
    if target_group :
        try :
            imported_level =exported_data .get ('base_camp_level',1 )
            current_level =target_group ['value']['RawData']['value'].get ('base_camp_level',1 )
            if imported_level >current_level :
                target_group ['value']['RawData']['value']['base_camp_level']=imported_level 
        except :
            pass 
    palbox_model_id =None 
    for obj in exported_data .get ('map_objects',[]):
        if obj .get ('MapObjectId',{}).get ('value','')=='PalBoxV2':
            mr =_get_model_raw (obj )
            if mr :
                palbox_model_id =_s (mr .get ('instance_id',''))
                break 
    exported_item_container_ids =set (_s (c ['key']['ID']['value'])for c in exported_data .get ('item_containers',[]))
    exported_char_container_ids =set (_s (c ['key']['ID']['value'])for c in exported_data .get ('char_containers',[]))
    instance_id_map ={}
    concrete_id_map ={}
    for obj in exported_data .get ('map_objects',[]):
        mr =_get_model_raw (obj )
        if not isinstance (mr ,dict ):
            continue 
        oid =str (obj .get ('MapObjectId',{}).get ('value',''))
        if oid in ['ItemBooth','PalBooth']:
            continue 
        if oid .startswith ('PalEgg')and 'Hatching'not in oid and ('Incubator'not in oid ):
            continue 
        old_inst =_s (mr .get ('instance_id',''))
        if not old_inst or old_inst ==_s (z ):
            continue 
        instance_id_map [old_inst ]=_new_uuid ()
        old_conc =_s (mr .get ('concrete_model_instance_id',''))
        if old_conc and old_conc !=_s (z ):
            concrete_id_map [old_conc ]=_new_uuid ()
    if palbox_model_id and palbox_model_id not in instance_id_map :
        instance_id_map [palbox_model_id ]=_new_uuid ()
    new_base_id =_new_uuid ()
    new_worker_container_id =_new_uuid ()
    new_palbox_inst_id =instance_id_map .get (palbox_model_id )
    src_base_raw =exported_data ['base_camp']['value']['RawData']['value']
    cur_pos =_deep (src_base_raw ['transform']['translation'])
    total_offset =[0 ,0 ,0 ]
    collision =True 
    while collision :
        collision =False 
        for existing_base in base_camp_data :
            try :
                ex_pos =existing_base ['value']['RawData']['value']['transform']['translation']
                dist =math .sqrt ((cur_pos ['x']-ex_pos ['x'])**2 +(cur_pos ['y']-ex_pos ['y'])**2 +(cur_pos ['z']-ex_pos ['z'])**2 )
                if dist <collision_threshold :
                    off_x =random .uniform (collision_threshold ,collision_threshold *1.5 )*random .choice ([-1 ,1 ])
                    off_y =random .uniform (collision_threshold ,collision_threshold *1.5 )*random .choice ([-1 ,1 ])
                    cur_pos ['x']+=off_x 
                    cur_pos ['y']+=off_y 
                    total_offset [0 ]+=off_x 
                    total_offset [1 ]+=off_y 
                    collision =True 
                    break 
            except :
                continue 
    work_id_map ={}
    cloned_works =[]
    new_work_ids_for_collection =[]
    for we in exported_data .get ('works',[]):
        nwe =_deep (we )
        nwr =_get_work_raw (nwe )
        if not isinstance (nwr ,dict )or 'id'not in nwr :
            continue 
        old_w_id =_s (nwr ['id'])
        nw_id =_new_uuid ()
        work_id_map [old_w_id ]=nw_id 
        nwr ['id']=nw_id 
        nwr ['base_camp_id_belong_to']=new_base_id 
        if 'WorkAssignMap'in nwe :
            nwe ['WorkAssignMap']['value']=[]
        old_om =_s (nwr .get ('owner_map_object_model_id',''))
        if old_om in instance_id_map :
            nwr ['owner_map_object_model_id']=instance_id_map [old_om ]
        old_oc =_s (nwr .get ('owner_map_object_concrete_model_id',''))
        if old_oc in concrete_id_map :
            nwr ['owner_map_object_concrete_model_id']=concrete_id_map [old_oc ]
        for key in ['cached_base_camp_id','cached_base_camp_ptr','cached_base_index']:
            nwr .pop (key ,None )
        try :
            tr =nwr .get ('transform',{})
            mid =_s (tr .get ('map_object_instance_id',''))
            if mid in instance_id_map :
                tr ['map_object_instance_id']=instance_id_map [mid ]
            if 'translation'in tr :
                _offset_translation (tr ['translation'],total_offset )
        except :
            pass 
        cloned_works .append (nwe )
        new_work_ids_for_collection .append (nw_id )
    nb =_deep (exported_data ['base_camp'])
    nb ['key']=new_base_id 
    try :
        nb_raw =nb ['value']['RawData']['value']
        nb_raw ['id']=new_base_id 
        nb_raw ['group_id_belong_to']=target_guild_id 
    except :
        pass 
    try :
        wd_raw =nb ['value']['WorkerDirector']['value']['RawData']['value']
        wd_raw ['id']=new_base_id 
        wd_raw ['container_id']=new_worker_container_id 
        _offset_translation (wd_raw ['spawn_transform']['translation'],total_offset )
    except :
        pass 
    try :
        nb ['value']['WorkCollection']['value']['RawData']['value']['id']=new_base_id 
        nb ['value']['WorkCollection']['value']['RawData']['value']['work_ids']=new_work_ids_for_collection 
    except :
        pass 
    if new_palbox_inst_id :
        try :
            nb ['value']['RawData']['value']['owner_map_object_instance_id']=new_palbox_inst_id 
        except :
            pass 
    try :
        _offset_translation (nb ['value']['RawData']['value']['transform']['translation'],total_offset )
    except :
        pass 
    base_camp_data .append (nb )
    if target_group :
        try :
            t_raw =target_group ['value']['RawData']['value']
            if new_base_id not in t_raw .get ('base_ids',[]):
                t_raw .setdefault ('base_ids',[]).append (new_base_id )
            if new_palbox_inst_id :
                t_raw .setdefault ('map_object_instance_ids_base_camp_points',[]).append (new_palbox_inst_id )
        except :
            pass 
    if target_group :
        guild_name =target_group ['value']['RawData']['value'].get ('guild_name','Unknown')
        constants .base_guild_lookup [str (new_base_id )]={'GuildName':guild_name ,'GuildID':tgt_gid_str }
    worker_id_map ={}
    try :
        src_worker_container_id =_s (exported_data ['base_camp']['value']['WorkerDirector']['value']['RawData']['value']['container_id'])
    except :
        src_worker_container_id =''
    src_worker_container =next ((c for c in exported_data .get ('char_containers',[])if _s (c .get ('key',{}).get ('ID',{}).get ('value'))==src_worker_container_id ),None )
    if src_worker_container :
        ncnt =_deep (src_worker_container )
        ncnt ['key']['ID']['value']=new_worker_container_id 
        if 'instance_id'in ncnt .get ('value',{}):
            ncnt ['value']['instance_id']=new_worker_container_id 
        old_slots =ncnt ['value']['Slots']['value'].get ('values',[])
        new_slots =[]
        for slot in old_slots :
            s_raw =slot .get ('RawData',{}).get ('value',{})
            old_inst =_s (s_raw .get ('instance_id',z ))
            if old_inst !=_s (z ):
                new_inst =_new_uuid ()
                worker_id_map [old_inst ]=new_inst 
                s_raw ['instance_id']=new_inst 
                new_slots .append (slot )
        ncnt ['value']['Slots']['value']['values']=new_slots 
        char_containers .append (ncnt )
    for old_iid ,new_iid in worker_id_map .items ():
        char_entry =next ((c for c in exported_data .get ('characters',[])if _s (c ['key']['InstanceId']['value'])==old_iid ),None )
        if char_entry :
            n_char =_deep (char_entry )
            n_char ['key']['InstanceId']['value']=new_iid 
            try :
                c_raw =n_char ['value']['RawData']['value']
                c_raw ['group_id']=target_guild_id 
                spv =c_raw ['object']['SaveParameter']['value']
                spv ['SlotId']['value']['ContainerId']['value']['ID']['value']=new_worker_container_id 
                if 'MapObjectConcreteInstanceIdAssignedToExpedition'in spv :
                    spv ['MapObjectConcreteInstanceIdAssignedToExpedition']['value']=z 
            except :
                pass 
            char_map .append (n_char )
            if target_group :
                try :
                    raw =target_group ['value']['RawData']['value']
                    handles =raw .setdefault ('individual_character_handle_ids',[])
                    seen ={}
                    unique_handles =[]
                    for h in handles :
                        try :
                            inst =str (h ['instance_id'])
                            if inst not in seen :
                                seen [inst ]=True 
                                unique_handles .append (h )
                        except :
                            unique_handles .append (h )
                    handles [:]=unique_handles 
                    if str (new_iid )not in seen :
                        handles .append ({'guid':z ,'instance_id':new_iid })
                except :
                    pass 
    for nwe in cloned_works :
        work_entries .append (nwe )
    for obj in exported_data .get ('map_objects',[]):
        mr =_get_model_raw (obj )
        if not isinstance (mr ,dict ):
            continue 
        oid =str (obj .get ('MapObjectId',{}).get ('value',''))
        if oid in ['ItemBooth','PalBooth']:
            continue 
        old_inst =_s (mr .get ('instance_id',''))
        if old_inst not in instance_id_map :
            continue 
        if oid .startswith ('PalEgg')and 'Hatching'not in oid and ('Incubator'not in oid ):
            continue 
        no =_deep (obj )
        nmr =_get_model_raw (no )
        new_inst =instance_id_map [old_inst ]
        old_conc =_s (nmr .get ('concrete_model_instance_id',''))
        new_conc =concrete_id_map .get (old_conc ,_new_uuid ())
        nmr ['instance_id']=new_inst 
        nmr ['concrete_model_instance_id']=new_conc 
        nmr ['base_camp_id_belong_to']=new_base_id 
        nmr ['group_id_belong_to']=target_guild_id 
        try :
            _offset_translation (nmr ['initital_transform_cache']['translation'],total_offset )
        except :
            pass 
        cr =_get_concrete_raw (no )
        if isinstance (cr ,dict ):
            cr ['instance_id']=new_conc 
            cr ['model_instance_id']=new_inst 
            cr ['base_camp_id']=new_base_id 
            if cr .get ('concrete_model_type')=='PalMapObjectBreedFarmModel':
                cr ['spawned_egg_instance_ids']=[]
            has_invalid =False 
            try :
                mm =no ['ConcreteModel']['value']['ModuleMap']['value']
                for mod in mm :
                    raw_mod =mod .get ('value',{}).get ('RawData',{}).get ('value',{})
                    if 'work_ids'in raw_mod and isinstance (raw_mod ['work_ids'],list ):
                        for wid in raw_mod ['work_ids']:
                            if _s (wid )not in work_id_map :
                                has_invalid =True 
                    if 'target_work_id'in raw_mod :
                        twid =_s (raw_mod ['target_work_id'])
                        if twid and twid not in work_id_map :
                            has_invalid =True 
                    if 'target_container_id'in raw_mod :
                        cid =_s (raw_mod ['target_container_id'])
                        if cid and cid not in exported_item_container_ids and cid not in exported_char_container_ids :
                            has_invalid =True 
            except :
                pass 
            if has_invalid :
                continue 
            try :
                mm =no ['ConcreteModel']['value']['ModuleMap']['value']
                for mod in mm :
                    raw_mod =mod .get ('value',{}).get ('RawData',{}).get ('value',{})
                    if 'target_work_id'in raw_mod :
                        old_twid =_s (raw_mod ['target_work_id'])
                        if old_twid in work_id_map :
                            raw_mod ['target_work_id']=work_id_map [old_twid ]
                    if 'work_ids'in raw_mod and isinstance (raw_mod ['work_ids'],list ):
                        raw_mod ['work_ids']=[work_id_map .get (_s (wid ),wid )for wid in raw_mod ['work_ids']]
                    if 'target_container_id'not in raw_mod :
                        continue 
                    old_cid =_s (raw_mod .get ('target_container_id',''))
                    new_cid =_new_uuid ()
                    raw_mod ['target_container_id']=new_cid 
                    if 'ItemContainer'in str (mod .get ('key','')):
                        src_ic =next ((c for c in exported_data .get ('item_containers',[])if _s (c .get ('key',{}).get ('ID',{}).get ('value'))==old_cid ),None )
                        if src_ic :
                            nic =_deep (src_ic )
                            nic ['key']['ID']['value']=new_cid 
                            if 'instance_id'in nic .get ('value',{}):
                                nic ['value']['instance_id']=new_cid 
                            item_slots =nic ['value']['Slots']['value'].get ('values',[])
                            cleaned_slots =[]
                            for slot in item_slots :
                                slot_raw =slot .get ('RawData',{}).get ('value',{})
                                item_meta =slot_raw .get ('item',{})
                                s_id =str (item_meta .get ('static_id',''))
                                if s_id .startswith ('PalEgg_'):
                                    continue 
                                dyn_id =item_meta .get ('dynamic_id',{})
                                old_local_id =_s (dyn_id .get ('local_id_in_created_world',z ))
                                if old_local_id !=_s (z ):
                                    new_local_id =_new_uuid ()
                                    dyn_id ['local_id_in_created_world']=new_local_id 
                                    source_dyn =next ((d for d in exported_data .get ('dynamic_items',[])if _s (d ['RawData']['value']['id']['local_id_in_created_world'])==old_local_id ),None )
                                    if source_dyn :
                                        new_dyn =_deep (source_dyn )
                                        new_dyn ['RawData']['value']['id']['local_id_in_created_world']=new_local_id 
                                        dynamic_item_data .append (new_dyn )
                                cleaned_slots .append (slot )
                            nic ['value']['Slots']['value']['values']=cleaned_slots 
                            item_containers .append (nic )
                    elif 'CharacterContainer'in str (mod .get ('key','')):
                        src_cc =next ((c for c in char_containers if _s (c .get ('key',{}).get ('ID',{}).get ('value'))==old_cid ),None )
                        if src_cc :
                            ncc =_deep (src_cc )
                            ncc ['key']['ID']['value']=new_cid 
                            if 'instance_id'in ncc .get ('value',{}):
                                ncc ['value']['instance_id']=new_cid 
                            _clear_char_container_slots (ncc )
                            char_containers .append (ncc )
            except :
                pass 
        map_objs .append (no )
    return True 
def clone_base_complete (loaded_level_json ,source_base_id ,target_guild_id ,offset =(8000 ,0 ,0 )):
    exported =export_base_json (loaded_level_json ,source_base_id )
    if not exported :
        return False 
    return import_base_json (loaded_level_json ,exported ,target_guild_id ,offset )
