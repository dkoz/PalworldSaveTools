import os 
import time 
import json 
from PIL import Image ,ImageDraw ,ImageFont 
import pygame 
import palworld_coord 
from i18n import t 
try :
    from palworld_aio import constants 
except ImportError :
    from .import constants 
def extract_guild_bases_from_save ():
    if not constants .loaded_level_json :
        return []
    wsd =constants .loaded_level_json ['properties']['worldSaveData']['value']
    base_map ={str (b ['key']).replace ('-',''):b ['value']
    for b in wsd .get ('BaseCampSaveData',{}).get ('value',[])}
    group_map =wsd .get ('GroupSaveDataMap',{}).get ('value',[])
    guild_bases =[]
    for entry in group_map :
        try :
            if entry ['value']['GroupType']['value']['value']!='EPalGroupType::Guild':
                continue 
        except :
            continue 
        g_val =entry ['value']
        guild_name =g_val ['RawData']['value'].get ('guild_name','Unknown Guild')
        admin_uid =str (g_val ['RawData']['value'].get ('admin_player_uid',''))
        leader_name ='Unknown'
        for p in g_val ['RawData']['value'].get ('players',[]):
            if str (p .get ('player_uid',''))==admin_uid :
                leader_name =p .get ('player_info',{}).get ('player_name',admin_uid )
                break 
        for bid in g_val ['RawData']['value'].get ('base_ids',[]):
            bid_str =str (bid ).replace ('-','')
            if bid_str in base_map :
                try :
                    translation =base_map [bid_str ]['RawData']['value']['transform']['translation']
                    x ,y =palworld_coord .sav_to_map (translation ['x'],translation ['y'],new =True )
                    guild_bases .append ({
                    'guild':guild_name ,
                    'leader':leader_name ,
                    'x':x ,
                    'y':y 
                    })
                except :
                    continue 
    return guild_bases 
def extract_stats_from_save ():
    if not constants .loaded_level_json :
        return {}
    wsd =constants .loaded_level_json ['properties']['worldSaveData']['value']
    group_map =wsd .get ('GroupSaveDataMap',{}).get ('value',[])
    guild_count =sum (1 for e in group_map 
    if e ['value']['GroupType']['value']['value']=='EPalGroupType::Guild')
    base_count =len (wsd .get ('BaseCampSaveData',{}).get ('value',[]))
    player_count =len (constants .player_levels )
    total_pals =sum (constants .PLAYER_PAL_COUNTS .values ())if constants .PLAYER_PAL_COUNTS else 0 
    return {
    'Total Bases':base_count ,
    'Total Active Guilds':guild_count ,
    'Total Players':player_count ,
    'Total Overall Pals':total_pals ,
    'Total Caught Pals':total_pals ,
    'Total Owned Pals':total_pals ,
    'Total Worker/Dropped Pals':0 
    }
def add_logo_overlay (overlay ,scale ,base_dir ,is_dark_mode =True ):
    logo_name ='PalworldSaveTools_Blue.png'if is_dark_mode else 'PalworldSaveTools_Black.png'
    logo_path =os .path .join (base_dir ,'resources',logo_name )
    if os .path .exists (logo_path ):
        try :
            logo =Image .open (logo_path ).convert ('RGBA')
            logo_width =int (overlay .width *0.18 )
            logo_height =int (logo .height *(logo_width /logo .width ))
            logo_resized =logo .resize ((logo_width ,logo_height ),Image .Resampling .LANCZOS )
            logo_x =50 *scale 
            logo_y =50 *scale 
            overlay .paste (logo_resized ,(logo_x ,logo_y ),logo_resized )
            return True 
        except Exception as e :
            print (f"Logo overlay failed: {e }")
    return False 
def render_text_pil (text ,size =20 ,color =(255 ,0 ,0 )):
    font_paths =[
    r"C:\Windows\Fonts\msgothic.ttc",
    r"C:\Windows\Fonts\YuGothicUI.ttf",
    r"C:\Windows\Fonts\YuGothic.ttf",
    r"C:\Windows\Fonts\meiryo.ttc"
    ]
    font_obj =None 
    for fp in font_paths :
        if os .path .exists (fp ):
            try :
                font_obj =ImageFont .truetype (fp ,size )
                break 
            except :
                pass 
    if font_obj is None :
        font_obj =ImageFont .load_default ()
    dummy =Image .new ("RGBA",(1 ,1 ))
    d =ImageDraw .Draw (dummy )
    bbox =d .textbbox ((0 ,0 ),text ,font =font_obj )
    w ,h =bbox [2 ]-bbox [0 ],bbox [3 ]-bbox [1 ]
    img =Image .new ("RGBA",(w +10 ,h +10 ),(0 ,0 ,0 ,0 ))
    d2 =ImageDraw .Draw (img )
    d2 .text ((5 ,5 ),text ,font =font_obj ,fill =color )
    return img 
def generate_world_map (output_path =None ):
    if not constants .loaded_level_json :
        print (t ('error.no_save_loaded')if t else 'No save file loaded.')
        return None 
    start_time =time .time ()
    base_dir =os .path .dirname (os .path .dirname (os .path .abspath (__file__ )))
    user_cfg_path =os .path .join (base_dir ,'data','configs','user.cfg')
    is_dark_mode =True 
    if os .path .exists (user_cfg_path ):
        try :
            with open (user_cfg_path ,'r')as f :
                settings =json .load (f )
                is_dark_mode =settings .get ('theme','dark')=='dark'
        except :
            pass 
    guild_bases =extract_guild_bases_from_save ()
    stats =extract_stats_from_save ()
    worldmap_path =os .path .join (base_dir ,'resources','worldmap.png')
    marker_path =os .path .join (base_dir ,'resources','baseicon.png')
    font_path =os .path .join (base_dir ,'resources','NotoSansCJKsc-Regular.otf')
    if not os .path .exists (worldmap_path ):
        print (f"World map not found: {worldmap_path }")
        return None 
    if not os .path .exists (marker_path ):
        print (f"Marker icon not found: {marker_path }")
        return None 
    image =Image .open (worldmap_path ).convert ('RGBA')
    marker =Image .open (marker_path ).convert ('RGBA')
    scale =4 
    marker_size =(64 ,64 )
    pygame .init ()
    if os .path .exists (font_path ):
        font =pygame .font .Font (font_path ,20 *scale )
    else :
        font =pygame .font .Font (None ,20 *scale )
    def render_pygame_text (text ,color =(255 ,0 ,0 )):
        surf =font .render (text ,True ,color )
        data =pygame .image .tostring (surf ,"RGBA")
        return Image .frombytes ("RGBA",surf .get_size (),data )
    overlay =Image .new ('RGBA',(image .width *scale ,image .height *scale ),(0 ,0 ,0 ,0 ))
    draw =ImageDraw .Draw (overlay )
    marker_resized =marker .resize ((marker_size [0 ]*scale ,marker_size [1 ]*scale ),
    Image .Resampling .LANCZOS )
    def to_image_coordinates (x_world ,y_world ):
        x_min ,x_max =(-1000 ,1000 )
        y_min ,y_max =(-1000 ,1000 )
        x_scale =image .width /(x_max -x_min )
        y_scale =image .height /(y_max -y_min )
        x_img =int ((x_world -x_min )*x_scale )
        y_img =int ((y_max -y_world )*y_scale )
        return (x_img ,y_img )
    for base_data in guild_bases :
        try :
            xi ,yi =to_image_coordinates (base_data ['x'],base_data ['y'])
            x_img ,y_img =xi *scale ,yi *scale 
            r =35 *scale 
            draw .ellipse ((x_img -r ,y_img -r ,x_img +r ,y_img +r ),
            outline ='red',width =4 *scale )
            mx =x_img -marker_resized .width //2 
            my =y_img -marker_resized .height //2 
            overlay .paste (marker_resized ,(mx ,my ),marker_resized )
            text =f"{base_data ['guild']} | {base_data ['leader']}"
            txt =render_text_pil (text ,size =20 *scale ,color =(255 ,0 ,0 ))
            shadow =render_text_pil (text ,size =20 *scale ,color =(0 ,0 ,0 ))
            for dx ,dy in [(-2 ,-2 ),(-2 ,2 ),(2 ,-2 ),(2 ,2 )]:
                shadow_x =x_img -txt .width //2 +dx 
                shadow_y =my +marker_resized .height +10 *scale +dy 
                overlay .paste (shadow ,(shadow_x ,shadow_y ),shadow )
            txt_x =x_img -txt .width //2 
            txt_y =my +marker_resized .height +10 *scale 
            overlay .paste (txt ,(txt_x ,txt_y ),txt )
        except Exception as e :
            print (f"Error rendering base: {e }")
            continue 
    ordered_stats =[
    ("Total Bases","stats.total_bases"),
    ("Total Active Guilds","stats.total_guilds"),
    ("Total Overall Pals","stats.total_overall"),
    ("Total Players","stats.total_players")
    ]
    y_offset =overlay .height -50 *scale 
    for raw_key ,lang_key in ordered_stats :
        line =f"{t (lang_key )if t else raw_key }: {stats .get (raw_key ,'0')}"
        line_img =render_pygame_text (line ,(255 ,0 ,0 ))
        shadow_img =render_pygame_text (line ,(0 ,0 ,0 ))
        y_offset -=line_img .height 
        overlay .paste (shadow_img ,(overlay .width -line_img .width -50 *scale -2 ,y_offset -2 ),shadow_img )
        overlay .paste (line_img ,(overlay .width -line_img .width -50 *scale ,y_offset ),line_img )
    add_logo_overlay (overlay ,scale ,base_dir ,is_dark_mode )
    small =overlay .resize (image .size ,Image .Resampling .LANCZOS )
    image .alpha_composite (small )
    if output_path is None :
        main_dir =os .path .dirname (base_dir )
        output_path =os .path .join (main_dir ,'updated_worldmap.png')
    try :
        image .save (output_path ,format ='PNG')
        duration =time .time ()-start_time 
        print (f"{t ('mapgen.done_time')if t else 'Done in'}: {duration :.2f}s")
        print (f"Map saved to: {output_path }")
        return output_path 
    except Exception as e :
        print (f"Error saving map: {e }")
        return None 
    finally :
        pygame .quit ()
