import os ,sys ,re ,time ,csv 
import pandas as pd 
from PIL import Image ,ImageDraw ,ImageFont 
import matplotlib .pyplot as plt 
sys .path .append (os .path .dirname (__file__ ))
from import_libs import *
from common import open_file_with_default_app 
try :
    from palworld_aio import constants 
except ImportError :
    import constants 
x_min ,x_max =-1000 ,1000 
y_min ,y_max =-1000 ,1000 
image_path =os .path .join (os .path .dirname (__file__ ),"resources","worldmap.png")
image =plt .imread (image_path )
height ,width =image .shape [:2 ]
x_scale =width /(x_max -x_min )
y_scale =height /(y_max -y_min )
def to_image_coordinates (x_world ,y_world ):
    x_img =(x_world -x_min )*x_scale 
    y_img =(y_max -y_world )*y_scale 
    return int (x_img ),int (y_img )
def parse_logfile (log_path ):
    with open (log_path ,'r',encoding ='utf-8')as file :
        lines =file .readlines ()
    guild_data =[]
    current ={}
    base_keys =set ()
    for line in lines :
        line =line .strip ()
        if line .startswith ('Guild:'):
            if current :guild_data .append (current )
            current ={}
            m =re .search (r'Guild:\s*(.*?)\s*\|\s*Guild Leader:\s*(.*?)\s*\|',line )
            if m :
                current ['Guild']=m .group (1 ).strip ()
                current ['Guild Leader']=m .group (2 ).strip ()
        elif line .startswith ('Base ')and 'New:'in line :
            parts =line .split (':')
            key_part =parts [0 ].strip ()
            m =re .search (r'New:\s*(-?\d+)\s*,\s*(-?\d+)',line )
            if m :
                current [key_part ]=f"{m .group (1 )},{m .group (2 )}"
                base_keys .add (key_part )
    if current :guild_data .append (current )
    return guild_data ,sorted (base_keys )
def write_csv (guild_data ,base_keys ,output_file ):
    print (t ("mapgen.write_csv"))
    fieldnames =['Guild','Guild Leader']+base_keys 
    with open (output_file ,"w",newline ="",encoding ="utf-8")as f :
        w =csv .DictWriter (f ,fieldnames =fieldnames )
        w .writeheader ()
        for g in guild_data :
            row ={field :g .get (field ,'')for field in fieldnames }
            w .writerow (row )
Image .MAX_IMAGE_PIXELS =None 
def extract_info_from_log ():
    print (t ("mapgen.extract"))
    try :
        log_file =os .path .join (constants .get_base_path (),'Scan Save Logger','scan_save.log')
        with open (log_file ,'r',encoding ='utf-8')as f :
            log_content =f .read ()
    except :
        raise ValueError ("UTF-8 read error.")
    stats ={}
    patterns ={
    'Total Players':r"Total Players:\s*(\d+)",
    'Total Caught Pals':r"Total Caught Pals:\s*(\d+)",
    'Total Overall Pals':r"Total Overall Pals:\s*(\d+)",
    'Total Owned Pals':r"Total Owned Pals:\s*(\d+)",
    'Total Worker/Dropped Pals':r"Total Worker/Dropped Pals:\s*(\d+)",
    'Total Active Guilds':r"Total Active Guilds:\s*(\d+)",
    'Total Bases':r"Total Bases:\s*(\d+)"
    }
    translation_map ={
    "Total Players":"stats.total_players",
    "Total Caught Pals":"stats.total_caught",
    "Total Overall Pals":"stats.total_overall",
    "Total Owned Pals":"stats.total_owned",
    "Total Worker/Dropped Pals":"stats.total_workers",
    "Total Active Guilds":"stats.total_guilds",
    "Total Bases":"stats.total_bases"
    }
    for key ,pattern in patterns .items ():
        m =re .search (pattern ,log_content )
        val =m .group (1 )if m else '0'
        stats [key ]=val 
        print (f"{t (translation_map [key ])}: {val }")
    return stats 
def render_text_pil (text ,size =20 ,color =(255 ,0 ,0 )):
    font_paths =[r"C:\Windows\Fonts\msgothic.ttc",r"C:\Windows\Fonts\YuGothicUI.ttf",r"C:\Windows\Fonts\YuGothic.ttf",r"C:\Windows\Fonts\meiryo.ttc"]
    font =None 
    for fp in font_paths :
        if os .path .exists (fp ):
            try :
                font =ImageFont .truetype (fp ,size )
                break 
            except :pass 
    if font is None :font =ImageFont .load_default ()
    dummy =Image .new ("RGBA",(1 ,1 ))
    d =ImageDraw .Draw (dummy )
    bbox =d .textbbox ((0 ,0 ),text ,font =font )
    w ,h =bbox [2 ]-bbox [0 ],bbox [3 ]-bbox [1 ]
    img =Image .new ("RGBA",(w +10 ,h +10 ),(0 ,0 ,0 ,0 ))
    d2 =ImageDraw .Draw (img )
    d2 .text ((5 ,5 ),text ,font =font ,fill =color )
    return img 
def create_world_map ():
    import pygame 
    pygame .init ()
    base_dir =os .path .dirname (os .path .abspath (__file__ ))
    worldmap_path =os .path .join (base_dir ,'resources','worldmap.png')
    marker_path =os .path .join (base_dir ,'resources','baseicon.png')
    image =Image .open (worldmap_path ).convert ('RGBA')
    marker =Image .open (marker_path ).convert ('RGBA')
    df =pd .read_csv ('bases.csv')
    marker_size =(64 ,64 )
    base_cols =[c for c in df .columns if c .startswith ('Base ')]
    scale =4 
    font_path =os .path .join (base_dir ,"resources","NotoSansCJKsc-Regular.otf")
    font =pygame .font .Font (font_path ,20 *scale )
    def render_pygame_text (text ,color =(255 ,0 ,0 )):
        surf =font .render (text ,True ,color )
        data =pygame .image .tostring (surf ,"RGBA")
        return Image .frombytes ("RGBA",surf .get_size (),data )
    overlay =Image .new ('RGBA',(image .width *scale ,image .height *scale ),(0 ,0 ,0 ,0 ))
    draw =ImageDraw .Draw (overlay )
    marker_resized =marker .resize ((marker_size [0 ]*scale ,marker_size [1 ]*scale ),Image .Resampling .LANCZOS )
    for _ ,row in df .iterrows ():
        guild =row .get ('Guild',t ("mapgen.unknown"))
        leader =row .get ('Guild Leader',t ("mapgen.unknown"))
        for col in base_cols :
            if pd .notna (row [col ])and row [col ]!='':
                try :
                    coords =str (row [col ]).strip ()
                    x ,y =map (int ,coords .split (','))
                    xi ,yi =to_image_coordinates (x ,y )
                    x_img ,y_img =xi *scale ,yi *scale 
                    r =35 *scale 
                    draw .ellipse ((x_img -r ,y_img -r ,x_img +r ,y_img +r ),outline ='red',width =4 *scale )
                    mx ,my =x_img -marker_resized .width //2 ,y_img -marker_resized .height //2 
                    overlay .paste (marker_resized ,(mx ,my ),marker_resized )
                    text =f"{guild } | {leader }"
                    txt =render_text_pil (text ,size =20 *scale ,color =(255 ,0 ,0 ))
                    shadow =render_text_pil (text ,size =20 *scale ,color =(0 ,0 ,0 ))
                    for dx ,dy in [(-2 ,-2 ),(-2 ,2 ),(2 ,-2 ),(2 ,2 )]:
                        overlay .paste (shadow ,(x_img -txt .width //2 +dx ,my +marker_resized .height +10 *scale +dy ),shadow )
                    overlay .paste (txt ,(x_img -txt .width //2 ,my +marker_resized .height +10 *scale ),txt )
                except :continue 
    stats =extract_info_from_log ()
    ordered_stats =[("Total Bases","stats.total_bases"),("Total Active Guilds","stats.total_guilds"),("Total Worker/Dropped Pals","stats.total_workers"),("Total Owned Pals","stats.total_owned"),("Total Overall Pals","stats.total_overall"),("Total Caught Pals","stats.total_caught"),("Total Players","stats.total_players")]
    y_offset =overlay .height -50 *scale 
    for raw ,langkey in ordered_stats :
        line =f"{t (langkey )}: {stats .get (raw ,'0')}"
        line_img =render_pygame_text (line ,color =(255 ,0 ,0 ))
        shadow_img =render_pygame_text (line ,color =(0 ,0 ,0 ))
        y_offset -=line_img .height 
        overlay .paste (shadow_img ,(overlay .width -line_img .width -50 *scale -2 ,y_offset -2 ),shadow_img )
        overlay .paste (line_img ,(overlay .width -line_img .width -50 *scale ,y_offset ),line_img )
    small =overlay .resize (image .size ,Image .Resampling .LANCZOS )
    image .alpha_composite (small )
    print (t ("mapgen.populate"))
    print (t ("mapgen.generate"))
    image .save ('updated_worldmap.png',format ='PNG')
    if os .path .exists ('bases.csv'):os .remove ('bases.csv')
def generate_map ():
    start =time .time ()
    main_dir =constants .get_base_path ()
    log_file =os .path .join (main_dir ,'Scan Save Logger','scan_save.log')
    if not os .path .exists (log_file ):
        print (t ("error.no_log"))
        return False 
    try :
        guild_data ,base_keys =parse_logfile (log_file )
        write_csv (guild_data ,base_keys ,'bases.csv')
        create_world_map ()
        map_path =os .path .join (main_dir ,"updated_worldmap.png")
        if os .path .exists (map_path ):
            print (t ("mapgen.opening"))
            open_file_with_default_app (map_path )
        else :
            print (t ("mapgen.not_found"))
        end =time .time ()
        print (f"{t ('mapgen.done_time')}: {end -start :.2f}s")
        return True 
    except Exception as e :
        print (f"{t ('mapgen.error')}: {e }")
        return False 
if __name__ =="__main__":generate_map ()
