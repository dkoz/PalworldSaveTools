import os 
import sys 
import re 
import time 
import csv 
import pandas as pd 
import pygame 
import palworld_coord 
from PIL import Image ,ImageDraw ,ImageFont 
from i18n import t 
from common import open_file_with_default_app 
try :
    from palworld_aio import constants 
except ImportError :
    from .import constants 
from PySide6 .QtWidgets import QApplication ,QMessageBox 
from PySide6 .QtCore import QTimer 
Image .MAX_IMAGE_PIXELS =None 
X_MIN ,X_MAX =-1000 ,1000 
Y_MIN ,Y_MAX =-1000 ,1000 
def _show_message_threadsafe (title ,message ,msg_type ='info'):

    from threading import Event ,current_thread 
    app =QApplication .instance ()
    if not app :
        return 
    main_thread =app .thread ()
    if current_thread ()==main_thread :
        if msg_type =='error':
            QMessageBox .critical (None ,title ,message )
        elif msg_type =='warning':
            QMessageBox .warning (None ,title ,message )
        else :
            QMessageBox .information (None ,title ,message )
        return True 
    result =[None ]
    event =Event ()
    def show ():
        if msg_type =='error':
            QMessageBox .critical (None ,title ,message )
        elif msg_type =='warning':
            QMessageBox .warning (None ,title ,message )
        else :
            QMessageBox .information (None ,title ,message )
        result [0 ]=True 
        event .set ()
    QTimer .singleShot (0 ,show )
    event .wait (timeout =5 )
    return result [0 ]
def to_image_coordinates (x_world ,y_world ,width ,height ):

    x_scale =width /(X_MAX -X_MIN )
    y_scale =height /(Y_MAX -Y_MIN )
    x_img =int ((x_world -X_MIN )*x_scale )
    y_img =int ((Y_MAX -y_world )*y_scale )
    return x_img ,y_img 
def get_stats_from_save ():

    if not constants .loaded_level_json :
        return {}
    wsd =constants .loaded_level_json ['properties']['worldSaveData']['value']
    group_data =wsd .get ('GroupSaveDataMap',{}).get ('value',[])
    base_data =wsd .get ('BaseCampSaveData',{}).get ('value',[])
    char_data =wsd .get ('CharacterSaveParameterMap',{}).get ('value',[])
    total_players =sum (
    len (g ['value']['RawData']['value'].get ('players',[]))
    for g in group_data 
    if g ['value']['GroupType']['value']['value']=='EPalGroupType::Guild'
    )
    total_guilds =sum (
    1 for g in group_data 
    if g ['value']['GroupType']['value']['value']=='EPalGroupType::Guild'
    )
    total_bases =len (base_data )
    total_pals =0 
    total_caught =0 
    total_owned =0 
    total_workers =0 
    for c in char_data :
        val =c .get ('value',{}).get ('RawData',{}).get ('value',{})
        struct_type =val .get ('object',{}).get ('SaveParameter',{}).get ('struct_type')
        if struct_type =='PalIndividualCharacterSaveParameter':
            save_param =val .get ('object',{}).get ('SaveParameter',{}).get ('value',{})
            if 'IsPlayer'in save_param and save_param ['IsPlayer'].get ('value'):
                continue 
            total_pals +=1 
            owner_uid =save_param .get ('OwnerPlayerUId',{}).get ('value','')
            if owner_uid and str (owner_uid )!='00000000-0000-0000-0000-000000000000':
                total_owned +=1 
                total_caught +=1 
            else :
                total_workers +=1 
    return {
    'Total Players':str (total_players ),
    'Total Active Guilds':str (total_guilds ),
    'Total Bases':str (total_bases ),
    'Total Overall Pals':str (total_pals ),
    'Total Owned Pals':str (total_owned ),
    'Total Caught Pals':str (total_caught ),
    'Total Worker/Dropped Pals':str (total_workers )
    }
def get_guild_base_data_from_save ():

    if not constants .loaded_level_json :
        return [],[]
    wsd =constants .loaded_level_json ['properties']['worldSaveData']['value']
    group_data =wsd .get ('GroupSaveDataMap',{}).get ('value',[])
    base_data =wsd .get ('BaseCampSaveData',{}).get ('value',[])
    base_map ={str (b ['key']).replace ('-',''):b ['value']for b in base_data }
    guild_data =[]
    base_keys =set ()
    for entry in group_data :
        try :
            if entry ['value']['GroupType']['value']['value']!='EPalGroupType::Guild':
                continue 
        except :
            continue 
        g_val =entry ['value']
        raw_data =g_val ['RawData']['value']
        guild_name =raw_data .get ('guild_name','Unknown')
        admin_uid =str (raw_data .get ('admin_player_uid',''))
        leader_name ='Unknown'
        for p in raw_data .get ('players',[]):
            if str (p .get ('player_uid',''))==admin_uid :
                leader_name =p .get ('player_info',{}).get ('player_name',admin_uid )
                break 
        if leader_name =='Unknown'and not raw_data .get ('players'):
            continue 
        current ={
        'Guild':guild_name ,
        'Guild Leader':leader_name 
        }
        base_ids =raw_data .get ('base_ids',[])
        for i ,bid in enumerate (base_ids ):
            bid_str =str (bid ).replace ('-','')
            if bid_str in base_map :
                try :
                    translation =base_map [bid_str ]['RawData']['value']['transform']['translation']
                    bx ,by =palworld_coord .sav_to_map (translation ['x'],translation ['y'],new =True )
                    key =f'Base {i +1 }'
                    current [key ]=f"{int (bx )},{int (by )}"
                    base_keys .add (key )
                except :
                    continue 
        guild_data .append (current )
    return guild_data ,sorted (base_keys )
def render_text_pil (text ,size =20 ,color =(255 ,0 ,0 ),font_path =None ):

    font_paths =[
    r"C:\Windows\Fonts\msgothic.ttc",
    r"C:\Windows\Fonts\YuGothicUI.ttf",
    r"C:\Windows\Fonts\YuGothic.ttf",
    r"C:\Windows\Fonts\meiryo.ttc"
    ]
    if font_path :
        font_paths .append (font_path )
    font =None 
    for fp in font_paths :
        if os .path .exists (fp ):
            try :
                font =ImageFont .truetype (fp ,size )
                break 
            except :
                pass 
    if font is None :
        font =ImageFont .load_default ()
    dummy =Image .new ("RGBA",(1 ,1 ))
    d =ImageDraw .Draw (dummy )
    bbox =d .textbbox ((0 ,0 ),text ,font =font )
    w ,h =bbox [2 ]-bbox [0 ],bbox [3 ]-bbox [1 ]
    img =Image .new ("RGBA",(w +10 ,h +10 ),(0 ,0 ,0 ,0 ))
    d2 =ImageDraw .Draw (img )
    d2 .text ((5 ,5 ),text ,font =font ,fill =color )
    return img 
def create_world_map ():

    pygame .init ()
    base_dir =os .path .dirname (os .path .dirname (os .path .abspath (__file__ )))
    worldmap_path =os .path .join (base_dir ,'resources','worldmap.png')
    marker_path =os .path .join (base_dir ,'resources','baseicon.png')
    logo_path =os .path .join (base_dir ,'resources','PalworldSaveTools_Blue.png')
    font_path =os .path .join (base_dir ,'resources','NotoSansCJKsc-Regular.otf')
    image =Image .open (worldmap_path ).convert ('RGBA')
    marker =Image .open (marker_path ).convert ('RGBA')
    guild_data ,base_keys =get_guild_base_data_from_save ()
    fieldnames =['Guild','Guild Leader']+base_keys 
    with open ('bases.csv',"w",newline ="",encoding ="utf-8")as f :
        w =csv .DictWriter (f ,fieldnames =fieldnames )
        w .writeheader ()
        for g in guild_data :
            row ={field :g .get (field ,'')for field in fieldnames }
            w .writerow (row )
    df =pd .read_csv ('bases.csv')
    marker_size =(64 ,64 )
    base_cols =[c for c in df .columns if c .startswith ('Base ')]
    scale =4 
    font =pygame .font .Font (font_path ,20 *scale )
    def render_pygame_text (text ,color =(255 ,0 ,0 )):
        surf =font .render (text ,True ,color )
        data =pygame .image .tostring (surf ,"RGBA")
        return Image .frombytes ("RGBA",surf .get_size (),data )
    overlay =Image .new ('RGBA',(image .width *scale ,image .height *scale ),(0 ,0 ,0 ,0 ))
    draw =ImageDraw .Draw (overlay )
    marker_resized =marker .resize ((marker_size [0 ]*scale ,marker_size [1 ]*scale ),Image .Resampling .LANCZOS )
    for _ ,row in df .iterrows ():
        guild =row .get ('Guild',t ("mapgen.unknown")if t else "Unknown")
        leader =row .get ('Guild Leader',t ("mapgen.unknown")if t else "Unknown")
        for col in base_cols :
            if pd .notna (row [col ])and row [col ]!='':
                try :
                    coords =str (row [col ]).strip ()
                    x ,y =map (int ,coords .split (','))
                    xi ,yi =to_image_coordinates (x ,y ,image .width ,image .height )
                    x_img ,y_img =xi *scale ,yi *scale 
                    r =35 *scale 
                    draw .ellipse ((x_img -r ,y_img -r ,x_img +r ,y_img +r ),outline ='red',width =4 *scale )
                    mx ,my =x_img -marker_resized .width //2 ,y_img -marker_resized .height //2 
                    overlay .paste (marker_resized ,(mx ,my ),marker_resized )
                    text =f"{guild } | {leader }"
                    txt =render_text_pil (text ,size =20 *scale ,color =(255 ,0 ,0 ),font_path =font_path )
                    shadow =render_text_pil (text ,size =20 *scale ,color =(0 ,0 ,0 ),font_path =font_path )
                    for dx ,dy in [(-2 ,-2 ),(-2 ,2 ),(2 ,-2 ),(2 ,2 )]:
                        overlay .paste (shadow ,(x_img -txt .width //2 +dx ,my +marker_resized .height +10 *scale +dy ),shadow )
                    overlay .paste (txt ,(x_img -txt .width //2 ,my +marker_resized .height +10 *scale ),txt )
                except :
                    continue 
    stats =get_stats_from_save ()
    ordered_stats =[
    ("Total Bases","stats.total_bases"),
    ("Total Active Guilds","stats.total_guilds"),
    ("Total Worker/Dropped Pals","stats.total_workers"),
    ("Total Owned Pals","stats.total_owned"),
    ("Total Overall Pals","stats.total_overall"),
    ("Total Caught Pals","stats.total_caught"),
    ("Total Players","stats.total_players")
    ]
    y_offset =overlay .height -50 *scale 
    for raw ,langkey in ordered_stats :
        line =f"{t (langkey )if t else raw }: {stats .get (raw ,'0')}"
        line_img =render_pygame_text (line ,color =(255 ,0 ,0 ))
        shadow_img =render_pygame_text (line ,color =(0 ,0 ,0 ))
        y_offset -=line_img .height 
        overlay .paste (shadow_img ,(overlay .width -line_img .width -50 *scale -2 ,y_offset -2 ),shadow_img )
        overlay .paste (line_img ,(overlay .width -line_img .width -50 *scale ,y_offset ),line_img )
    if os .path .exists (logo_path ):
        try :
            logo =Image .open (logo_path ).convert ('RGBA')
            logo_width =int (overlay .width *0.20 )
            logo_height =int (logo .height *(logo_width /logo .width ))
            logo_resized =logo .resize ((logo_width ,logo_height ),Image .Resampling .LANCZOS )
            logo_x =50 *scale 
            logo_y =50 *scale 
            overlay .paste (logo_resized ,(logo_x ,logo_y ),logo_resized )
        except Exception as e :
            print (f"Could not add logo: {e }")
    small =overlay .resize (image .size ,Image .Resampling .LANCZOS )
    image .alpha_composite (small )
    print (t ("mapgen.populate")if t else "Populating map...")
    print (t ("mapgen.generate")if t else "Generating map...")
    main_dir =os .path .dirname (base_dir )
    output_path =os .path .join (main_dir ,'updated_worldmap.png')
    image .save (output_path ,format ='PNG')
    if os .path .exists ('bases.csv'):
        os .remove ('bases.csv')
    return output_path 
def generate_map (parent =None ):

    if not constants .loaded_level_json :
        _show_message_threadsafe (
        t ('error.title')if t else 'Error',
        t ('guild.rebuild.no_save')if t else 'No save loaded',
        'error'
        )
        return None 
    start_time =time .time ()
    try :
        map_path =create_world_map ()
        if os .path .exists (map_path ):
            print (t ('mapgen.opening')if t else 'Opening updated_worldmap.png...')
            open_file_with_default_app (map_path )
            _show_message_threadsafe (
            t ('success.title')if t else 'Success',
            t ('mapgen.opening')if t else 'Map generated successfully!',
            'info'
            )
        else :
            _show_message_threadsafe (
            t ('error.title')if t else 'Error',
            t ('mapgen.not_found')if t else 'updated_worldmap.png not found.',
            'error'
            )
            print (t ('mapgen.not_found')if t else 'updated_worldmap.png not found.')
            return None 
        end_time =time .time ()
        duration =end_time -start_time 
        print (f"{t ('mapgen.done_time')if t else 'Done in'}: {duration :.2f}s")
        return map_path 
    except Exception as e :
        error_msg =f"{t ('mapgen.error')if t else 'Error generating map'}: {e }"
        _show_message_threadsafe (
        t ('error.title')if t else 'Error',
        error_msg ,
        'error'
        )
        print (error_msg )
        import traceback 
        traceback .print_exc ()
        return None 
