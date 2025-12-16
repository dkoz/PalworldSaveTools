import os, sys, re, time, csv
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import matplotlib.pyplot as plt
sys.path.append(os.path.dirname(__file__))
from import_libs import *
from common import open_file_with_default_app
x_min,x_max=-1000,1000
y_min,y_max=-1000,1000
image_path=os.path.join(os.path.dirname(__file__),"resources","worldmap.png")
image=plt.imread(image_path)
height,width=image.shape[:2]
x_scale=width/(x_max-x_min)
y_scale=height/(y_max-y_min)
def to_image_coordinates(x_world,y_world):
    x_img=(x_world-x_min)*x_scale
    y_img=(y_max-y_world)*y_scale
    return int(x_img),int(y_img)
def parse_logfile(log_path):
    with open(log_path,'r',encoding='utf-8') as file:
        lines=file.readlines()
    guild_data=[]
    current={}
    base_keys=set()
    for line in lines:
        if line.startswith('Guild:'):
            if current: guild_data.append(current); current={}
            m=re.search(r'Guild:\s*(.*?)\s*\|\s*Guild Leader:\s*(.*?)\s*\|',line)
            if m:
                current['Guild']=m.group(1)
                current['Guild Leader']=m.group(2)
        if line.startswith('Base ') and any(line.startswith(f"Base {i}:") for i in range(1,11)):
            key=line.split(':')[0].strip()
            parts=line.strip().split('|')
            if len(parts)>=2:
                current[key]=parts[1].strip()
                base_keys.add(key)
    if current: guild_data.append(current)
    return guild_data,sorted(base_keys)
def write_csv(guild_data,base_keys,output_file):
    print(t("mapgen.write_csv"))
    fieldnames=['Guild','Guild Leader']+base_keys
    with open(output_file,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fieldnames)
        w.writeheader()
        for g in guild_data:
            row={field:g.get(field,'') for field in fieldnames}
            w.writerow(row)
Image.MAX_IMAGE_PIXELS=None
def sanitize_text(text):
    try: return text.encode('utf-8','ignore').decode('utf-8')
    except: return text.replace('\uFFFD','?')
def extract_info_from_log():
    print(t("mapgen.extract"))
    try:
        with open('Scan Save Logger/scan_save.log', 'r', encoding='utf-8') as f:
            log_content = f.read()
    except UnicodeDecodeError:
        raise ValueError("UTF-8 read error.")
    stats = {
        'Total Players': 'N/A',
        'Total Caught Pals': 'N/A',
        'Total Overall Pals': 'N/A',
        'Total Owned Pals': 'N/A',
        'Total Worker/Dropped Pals': 'N/A',
        'Total Active Guilds': 'N/A',
        'Total Bases': 'N/A'
    }
    block = re.search(r"PST_STATS_BEGIN(.*?)PST_STATS_END", log_content, re.S)
    if not block:
        return stats
    text = block.group(1)
    patterns = {
        'Total Players': r":\s*(\d+)",
        'Total Caught Pals': r":\s*(\d+)",
        'Total Overall Pals': r":\s*(\d+)",
        'Total Owned Pals': r":\s*(\d+)",
        'Total Worker/Dropped Pals': r":\s*(\d+)",
        'Total Active Guilds': r":\s*(\d+)",
        'Total Bases': r":\s*(\d+)"
    }
    keys_in_order = [
        'Total Players',
        'Total Caught Pals',
        'Total Overall Pals',
        'Total Owned Pals',
        'Total Worker/Dropped Pals',
        'Total Active Guilds',
        'Total Bases'
    ]
    lines = text.splitlines()
    ki = 0
    for line in lines:
        if ki >= len(keys_in_order):
            break
        key = keys_in_order[ki]
        m = re.search(patterns[key], line)
        if m:
            stats[key] = m.group(1)
            ki += 1
    translation_map = {
        "Total Players": "stats.total_players",
        "Total Caught Pals": "stats.total_caught",
        "Total Overall Pals": "stats.total_overall",
        "Total Owned Pals": "stats.total_owned",
        "Total Worker/Dropped Pals": "stats.total_workers",
        "Total Active Guilds": "stats.total_guilds",
        "Total Bases": "stats.total_bases"
    }
    for key, value in stats.items():
        print(f"{t(translation_map[key])}: {value}")
    return stats
def render_text_pil(text,size=20,color=(255,0,0)):
    font_paths=[
        r"C:\Windows\Fonts\msgothic.ttc",
        r"C:\Windows\Fonts\YuGothicUI.ttf",
        r"C:\Windows\Fonts\YuGothic.ttf",
        r"C:\Windows\Fonts\meiryo.ttc",
        r"C:\Windows\Fonts\meiryob.ttc",
        r"C:\Windows\Fonts\msmincho.ttc"
    ]
    font=None
    for fp in font_paths:
        if os.path.exists(fp):
            try:
                font=ImageFont.truetype(fp,size)
                break
            except: pass
    if font is None: font=ImageFont.load_default()
    dummy=Image.new("RGBA",(10,10))
    d=ImageDraw.Draw(dummy)
    left,top,right,bottom=d.textbbox((0,0),text,font=font)
    w,h=right-left,bottom-top
    img=Image.new("RGBA",(w,h),(0,0,0,0))
    d2=ImageDraw.Draw(img)
    d2.text((0,0),text,font=font,fill=color)
    return img
def create_world_map():
    import pygame
    pygame.init()
    base_dir=os.path.dirname(os.path.abspath(__file__))
    worldmap_path=os.path.join(base_dir,'resources','worldmap.png')
    marker_path=os.path.join(base_dir,'resources','baseicon.png')
    image=Image.open(worldmap_path).convert('RGBA')
    marker=Image.open(marker_path).convert('RGBA')
    df=pd.read_csv('bases.csv')
    marker_size=(64,64)
    base_cols=[c for c in df.columns if c.startswith('Base ')]
    scale=4
    font_path=os.path.join(base_dir,"resources","NotoSansCJKsc-Regular.otf")
    font=pygame.font.Font(font_path,20*scale)
    def render_text(text,color=(255,0,0)):
        surf=font.render(text,True,color)
        data=pygame.image.tostring(surf,"RGBA")
        return Image.frombytes("RGBA",surf.get_size(),data)
    overlay=Image.new('RGBA',(image.width*scale,image.height*scale),(0,0,0,0))
    draw=ImageDraw.Draw(overlay)
    marker_resized=marker.resize((marker_size[0]*scale,marker_size[1]*scale),Image.Resampling.LANCZOS)
    def to_image_coordinates_scaled(x,y):
        xi,yi=to_image_coordinates(x,y)
        return xi*scale,yi*scale
    for _,row in df.iterrows():
        guild=row.get('Guild',t("mapgen.unknown"))
        leader=row.get('Guild Leader',t("mapgen.unknown"))
        for col in base_cols:
            if pd.notna(row[col]):
                coords_str=row[col]
                coords_part=coords_str.split('|')[0].strip()
                try:
                    x_str,y_str=coords_part.split(', ')
                except: continue
                x,y=int(x_str),int(y_str)
                x_img,y_img=to_image_coordinates_scaled(x,y)
                r=35*scale
                draw.ellipse((x_img-r,y_img-r,x_img+r,y_img+r),outline='red',width=4*scale)
                mx=x_img-marker_resized.width//2
                my=y_img-marker_resized.height//2
                overlay.paste(marker_resized,(mx,my),marker_resized)
                text=f"{guild} | {leader}"
                txt=render_text_pil(text,size=20*scale,color=(255,0,0))
                shadow=render_text_pil(text,size=20*scale,color=(0,0,0))
                for dx,dy in [(-1,-1),(-1,1),(1,-1),(1,1)]:
                    overlay.paste(shadow,(x_img-txt.width//2+dx*scale,my+marker_resized.height+10*scale+dy*scale),shadow)
                overlay.paste(txt,(x_img-txt.width//2,my+marker_resized.height+10*scale),txt)
    stats=extract_info_from_log()
    ordered_stats=[
        ("Total Bases","stats.total_bases"),
        ("Total Active Guilds","stats.total_guilds"),
        ("Total Worker/Dropped Pals","stats.total_workers"),
        ("Total Owned Pals","stats.total_owned"),
        ("Total Overall Pals","stats.total_overall"),
        ("Total Caught Pals","stats.total_caught"),
        ("Total Players","stats.total_players")
    ]
    stats_text_lines=[
        f"{t(langkey)}: {stats[raw]}"
        for raw,langkey in ordered_stats
    ]
    stats_text="\n".join(stats_text_lines)
    y_offset=overlay.height-50*scale
    for line in stats_text.split('\n'):
        line_img=render_text(line,color=(255,0,0))
        shadow_img=render_text(line,color=(0,0,0))
        y_offset-=line_img.height
        overlay.paste(shadow_img,(overlay.width-line_img.width-50*scale-1,y_offset-1),shadow_img)
        overlay.paste(line_img,(overlay.width-line_img.width-50*scale,y_offset),line_img)
    small=overlay.resize(image.size,Image.Resampling.LANCZOS)
    image.alpha_composite(small)
    print(t("mapgen.populate"))
    print(t("mapgen.generate"))
    image.save('updated_worldmap.png',format='PNG',dpi=(100,100),optimize=True)
    if os.path.exists('bases.csv'): os.remove('bases.csv')
def generate_map():
    start=time.time()
    script_dir=os.path.dirname(os.path.abspath(__file__))
    main_dir=os.path.dirname(script_dir)
    log_file=os.path.join(main_dir,'Scan Save Logger','scan_save.log')
    if not os.path.exists(log_file):
        print(t("error.no_log"))
        return False
    try:
        guild_data,base_keys=parse_logfile(log_file)
        write_csv(guild_data,base_keys,'bases.csv')
        create_world_map()
        map_path=os.path.join(main_dir,"updated_worldmap.png")
        if os.path.exists(map_path):
            print(t("mapgen.opening"))
            open_file_with_default_app(map_path)
        else:
            print(t("mapgen.not_found"))
        end=time.time()
        print(f"{t('mapgen.done_time')}: {end-start:.2f}s")
        return True
    except Exception as e:
        print(f"{t('mapgen.error')}: {e}")
        return False
if __name__=="__main__": generate_map()