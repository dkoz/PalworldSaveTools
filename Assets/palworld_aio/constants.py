import os 
import sys 
BG ="#0A0B0E"
GLASS ="#121418"
ACCENT ="#3B8ED0"
TEXT ="#E6EEF6"
MUTED ="#A6B8C8"
EMPHASIS ="#FFFFFF"
ALERT ="#FFD24D"
SUCCESS ="#4CAF50"
ERROR ="#F44336"
BORDER ="#1E2128"
BUTTON_FG ="#0078D7"
BUTTON_BG ="transparent"
BUTTON_HOVER ="#2A2D3A"
BUTTON_PRIMARY =ACCENT 
BUTTON_SECONDARY =GLASS 
FONT_FAMILY ="Segoe UI"
FONT_SIZE =10 
FONT_SIZE_BOLD =10 
FONT_SIZE_LARGE =12 
FONT_SIZE_SMALL =9 
SPACE_SMALL =5 
SPACE_MEDIUM =10 
SPACE_LARGE =15 
CORNER_RADIUS =6 
FRAME_CORNER_RADIUS =8 
TREE_ROW_HEIGHT =22 
GITHUB_RAW_URL ='https://raw.githubusercontent.com/deafdudecomputers/PalworldSaveTools/main/Assets/common.py'
def get_base_path ():
    if getattr (sys ,'frozen',False ):
        return os .path .dirname (sys .executable )
    return os .getcwd ()
def get_assets_path ():
    if getattr (sys ,'frozen',False ):
        return os .path .join (os .path .dirname (sys .executable ),"Assets")
    return os .path .dirname (os .path .dirname (os .path .abspath (__file__ )))
def get_icon_path ():
    return os .path .join (get_assets_path (),'resources','pal.ico')
ICON_PATH =get_icon_path ()
EXCLUSIONS_FILE =os .path .join (get_assets_path (),'data','configs','deletion_exclusions.json')
current_save_path =None 
loaded_level_json =None 
original_loaded_level_json =None 
backup_save_path =None 
srcGuildMapping =None 
player_levels ={}
base_guild_lookup ={}
files_to_delete =set ()
PLAYER_PAL_COUNTS ={}
PLAYER_DETAILS_CACHE ={}
PLAYER_REMAPS ={}
exclusions ={}
selected_source_player =None 
dps_executor =None 
dps_futures =[]
dps_tasks =[]
