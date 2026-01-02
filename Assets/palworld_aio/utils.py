import os 
import sys 
import re 
import ssl 
import mmap 
import pickle 
import urllib .request 
from palworld_save_tools .archive import UUID 
from palworld_save_tools .gvas import GvasFile 
from palworld_save_tools .palsav import decompress_sav_to_gvas ,compress_gvas_to_sav 
from palworld_save_tools .paltypes import PALWORLD_TYPE_HINTS 
from common import get_versions 
from palobject import SKP_PALWORLD_CUSTOM_PROPERTIES 
try :
    from palworld_aio import constants 
except ImportError :
    from .import constants 
def check_for_update ():
    try :
        context =ssl ._create_unverified_context ()
        req =urllib .request .Request (constants .GITHUB_RAW_URL )
        req .add_header ('Range','bytes=0-1024')
        with urllib .request .urlopen (req ,timeout =10 ,context =context )as r :
            content =r .read ().decode ('utf-8')
        match =re .search ('APP_VERSION\\s*=\\s*"([^"]+)"',content )
        latest =match .group (1 )if match else None 
        local ,_ =get_versions ()
        if not latest :
            return None 
        local_tuple =tuple ((int (x )for x in local .split ('.')))
        latest_tuple =tuple ((int (x )for x in latest .split ('.')))
        return {'local':local ,'latest':latest ,'update_available':latest_tuple >local_tuple }
    except Exception as e :
        print ('Update check error:',e )
        return None 
def as_uuid (val ):
    return str (val ).lower ()if val else ''
def are_equal_uuids (a ,b ):
    return as_uuid (a )==as_uuid (b )
def fast_deepcopy (json_dict ):
    return pickle .loads (pickle .dumps (json_dict ,-1 ))
def sav_to_json (path ):
    file_size =os .path .getsize (path )
    if file_size >100 *1024 *1024 :
        print (f'Large file detected ({file_size /(1024 *1024 ):.1f}MB), using memory mapping for decompression...')
        with open (path ,'rb')as f :
            with mmap .mmap (f .fileno (),0 ,access =mmap .ACCESS_READ )as mm :
                raw_gvas ,_ =decompress_sav_to_gvas (mm .read ())
    else :
        with open (path ,'rb')as f :
            data =f .read ()
        raw_gvas ,_ =decompress_sav_to_gvas (data )
    g =GvasFile .read (raw_gvas ,PALWORLD_TYPE_HINTS ,SKP_PALWORLD_CUSTOM_PROPERTIES ,allow_nan =True )
    return g .dump ()
def json_to_sav (j ,path ):
    g =GvasFile .load (j )
    t =50 if 'Pal.PalworldSaveGame'in g .header .save_game_class_name else 49 
    data =compress_gvas_to_sav (g .write (SKP_PALWORLD_CUSTOM_PROPERTIES ),t )
    with open (path ,'wb')as f :
        f .write (data )
def extract_value (data ,key ,default_value =''):
    value =data .get (key ,default_value )
    if isinstance (value ,dict ):
        value =value .get ('value',default_value )
        if isinstance (value ,dict ):
            value =value .get ('value',default_value )
    return value 
def safe_str (s ):
    return s .encode ('utf-8','replace').decode ('utf-8')
def sanitize_filename (name ):
    return ''.join ((c if c .isalnum ()or c in (' ','_','-','(',')')else '_'for c in name ))
def format_duration (s ):
    d ,h =divmod (int (s ),86400 )
    hr ,m =divmod (h ,3600 )
    mm ,ss =divmod (m ,60 )
    return f'{d }d:{hr }h:{mm }m'
def format_duration_short (seconds ):
    seconds =int (seconds )
    if seconds <60 :
        return f'{seconds }s ago'
    m ,s =divmod (seconds ,60 )
    if m <60 :
        return f'{m }m {s }s ago'
    h ,m =divmod (m ,60 )
    if h <24 :
        return f'{h }h {m }m ago'
    d ,h =divmod (h ,24 )
    return f'{d }d {h }h ago'
def is_valid_level (level ):
    try :
        return int (level )>0 
    except :
        return False 
def normalize_uid (uid ):
    if isinstance (uid ,dict ):
        uid =uid .get ('value','')
    return str (uid ).replace ('-','').lower ()
def toUUID (val ):
    if hasattr (val ,'bytes'):
        return val 
    s =str (val ).replace ('-','').lower ()
    if len (s )==32 :
        return UUID .from_str (f'{s [:8 ]}-{s [8 :12 ]}-{s [12 :16 ]}-{s [16 :20 ]}-{s [20 :]}')
    return val 
def restart_program ():
    python =sys .executable 
    os .execl (python ,python ,*sys .argv )
