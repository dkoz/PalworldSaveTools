from import_libs import *
from PySide6 .QtWidgets import (
QHeaderView ,QMainWindow ,QWidget ,QLineEdit ,QTreeWidget ,QTreeWidgetItem ,
QLabel ,QPushButton ,QVBoxLayout ,QHBoxLayout ,QFileDialog ,QMessageBox ,QFrame ,QApplication 
)
from PySide6 .QtGui import QIcon ,QFont 
from PySide6 .QtCore import Qt ,QTimer 
player_list_cache =[]
def fix_save (save_path ,new_guid ,old_guid ,guild_fix =True ):
    def task ():
        fmt =lambda g :'{}-{}-{}-{}-{}'.format (g [:8 ],g [8 :12 ],g [12 :16 ],g [16 :20 ],g [20 :]).lower ()
        old_uid ,new_uid =fmt (old_guid ),fmt (new_guid )
        lvl =os .path .join (save_path ,"Level.sav")
        old_sav =os .path .join (save_path ,"Players",old_guid +".sav")
        new_sav =os .path .join (save_path ,"Players",new_guid +".sav")
        level =sav_to_json (lvl )
        old_j =sav_to_json (old_sav )
        new_j =sav_to_json (new_sav )
        old_j ["properties"]["SaveData"]["value"]["PlayerUId"]["value"]=new_uid 
        old_j ["properties"]["SaveData"]["value"]["IndividualId"]["value"]["PlayerUId"]["value"]=new_uid 
        new_j ["properties"]["SaveData"]["value"]["PlayerUId"]["value"]=old_uid 
        new_j ["properties"]["SaveData"]["value"]["IndividualId"]["value"]["PlayerUId"]["value"]=old_uid 
        old_inst =old_j ["properties"]["SaveData"]["value"]["IndividualId"]["value"]["InstanceId"]["value"]
        new_inst =new_j ["properties"]["SaveData"]["value"]["IndividualId"]["value"]["InstanceId"]["value"]
        cspm =level ["properties"]["worldSaveData"]["value"]["CharacterSaveParameterMap"]["value"]
        for e in cspm :
            if e ["key"]["InstanceId"]["value"]==old_inst :e ["key"]["PlayerUId"]["value"]=new_uid 
            elif e ["key"]["InstanceId"]["value"]==new_inst :e ["key"]["PlayerUId"]["value"]=old_uid 
        if guild_fix :
            for g in level ["properties"]["worldSaveData"]["value"]["GroupSaveDataMap"]["value"]:
                if g ["value"]["GroupType"]["value"]["value"]!="EPalGroupType::Guild":continue 
                raw =g ["value"]["RawData"]["value"]
                for h in raw .get ("individual_character_handle_ids",[]):
                    if h ["instance_id"]==old_inst :h ["guid"]=new_uid 
                    elif h ["instance_id"]==new_inst :h ["guid"]=old_uid 
                if raw .get ("admin_player_uid")==old_uid :raw ["admin_player_uid"]=new_uid 
                elif raw .get ("admin_player_uid")==new_uid :raw ["admin_player_uid"]=old_uid 
                for p in raw .get ("players",[]):
                    if p .get ("player_uid")==old_uid :p ["player_uid"]=new_uid 
                    elif p .get ("player_uid")==new_uid :p ["player_uid"]=old_uid 
        def deep_swap (data ):
            if isinstance (data ,dict ):
                for k in ("OwnerPlayerUId","owner_player_uid","build_player_uid","private_lock_player_uid"):
                    v =data .get (k )
                    if isinstance (v ,dict )and v .get ("value")==old_uid :v ["value"]=new_uid 
                    elif isinstance (v ,dict )and v .get ("value")==new_uid :v ["value"]=old_uid 
                    elif v ==old_uid :data [k ]=new_uid 
                    elif v ==new_uid :data [k ]=old_uid 
                for x in data .values ():deep_swap (x )
            elif isinstance (data ,list ):
                for i in data :deep_swap (i )
        deep_swap (level )
        copy_dps_file (os .path .join (os .path .dirname (lvl ),"Players"),old_guid ,os .path .join (os .path .dirname (lvl ),"Players"),new_guid )
        backup_whole_directory (save_path ,"Backups/Fix Host Save")
        json_to_sav (level ,lvl )
        json_to_sav (old_j ,old_sav )
        json_to_sav (new_j ,new_sav )
        tmp_path =old_sav +".tmp_swap"
        os .rename (old_sav ,tmp_path )
        if os .path .exists (new_sav ):os .rename (new_sav ,os .path .join (save_path ,"Players",old_guid .upper ()+".sav"))
        os .rename (tmp_path ,os .path .join (save_path ,"Players",new_guid .upper ()+".sav"))
        return True 
    def on_finished (_ ):
        QMessageBox .information (None ,t ("Success"),t ("Fix has been applied! Have fun!"))
    run_with_loading (on_finished ,task )
def copy_dps_file (src_folder ,src_uid ,tgt_folder ,tgt_uid ):
    src_file =os .path .join (src_folder ,f"{str (src_uid ).replace ('-','').upper ()}_dps.sav")
    tgt_file =os .path .join (tgt_folder ,f"{str (tgt_uid ).replace ('-','').upper ()}_dps.sav")
    if not os .path .exists (src_file ):
        print (f"Source DPS file missing: {src_file }")
        return None 
    shutil .copy2 (src_file ,tgt_file )
    print (f"DPS save copied from {src_file } to {tgt_file }")
def ask_string_with_icon (title ,prompt ,icon_path ):
    class CustomDialog (QDialog ):
        def __init__ (self ,parent ):
            super ().__init__ (parent )
            self .setWindowTitle (title )
            try :self .setWindowIcon (QIcon (icon_path ))
            except :pass 
            self .setFixedSize (400 ,120 )
            layout =QVBoxLayout (self )
            label =QLabel (prompt )
            layout .addWidget (label )
            self .entry =QLineEdit ()
            layout .addWidget (self .entry )
            button_layout =QHBoxLayout ()
            ok_button =QPushButton (t ("OK"))
            ok_button .clicked .connect (self .accept )
            cancel_button =QPushButton (t ("Cancel"))
            cancel_button .clicked .connect (self .reject )
            button_layout .addWidget (ok_button )
            button_layout .addWidget (cancel_button )
            layout .addLayout (button_layout )
            self .entry .setFocus ()
    dialog =CustomDialog (None )
    result =dialog .exec ()
    return dialog .entry .text ()if result ==QDialog .Accepted else None 
def sav_to_json (filepath ):
    with open (filepath ,"rb")as f :
        data =f .read ()
        raw_gvas ,save_type =decompress_sav_to_gvas (data )
    gvas_file =GvasFile .read (raw_gvas ,PALWORLD_TYPE_HINTS ,SKP_PALWORLD_CUSTOM_PROPERTIES ,allow_nan =True )
    return gvas_file .dump ()
def json_to_sav (json_data ,output_filepath ):
    gvas_file =GvasFile .load (json_data )
    save_type =0x32 if "Pal.PalworldSaveGame"in gvas_file .header .save_game_class_name or "Pal.PalLocalWorldSaveGame"in gvas_file .header .save_game_class_name else 0x31 
    sav_file =compress_gvas_to_sav (gvas_file .write (SKP_PALWORLD_CUSTOM_PROPERTIES ),save_type )
    with open (output_filepath ,"wb")as f :
        f .write (sav_file )
def populate_player_lists (folder_path ):
    global player_list_cache 
    if player_list_cache :
        return player_list_cache 
    players_folder =os .path .join (folder_path ,"Players")
    if not os .path .exists (players_folder ):
        QMessageBox .warning (None ,"Error","Players folder not found next to selected Level.sav")
        return []
    level_json =sav_to_json (os .path .join (folder_path ,'Level.sav'))
    group_data_list =level_json ['properties']['worldSaveData']['value']['GroupSaveDataMap']['value']
    player_files =[]
    for group in group_data_list :
        if group ['value']['GroupType']['value']['value']=='EPalGroupType::Guild':
            key =group ['key']
            if isinstance (key ,dict )and 'InstanceId'in key :
                guild_id =key ['InstanceId']['value']
            else :
                guild_id =str (key )
            players =group ['value']['RawData']['value'].get ('players',[])
            for player in players :
                uid =str (player .get ('player_uid','')).replace ('-','')
                name =player .get ('player_info',{}).get ('player_name','Unknown')
                player_files .append (f"{uid } - {name } - {guild_id }")
    player_list_cache =player_files 
    return player_files 
def populate_player_tree (tree ,folder_path ):
    tree .clear ()
    player_list =populate_player_lists (folder_path )
    existing_iids =set ()
    for player in player_list :
        parts =player .split (' - ')
        uid ,name ,guild =parts [0 ],parts [1 ],parts [2 ]
        orig_uid =uid 
        count =1 
        while uid in existing_iids :
            uid =f"{orig_uid }_{count }"
            count +=1 
        item =QTreeWidgetItem ([orig_uid ,name ,guild ])
        tree .addTopLevelItem (item )
        existing_iids .add (uid )
    tree .original_items =[tree .topLevelItem (i )for i in range (tree .topLevelItemCount ())]
def filter_treeview (tree ,query ):
    query =query .lower ()
    for item in tree .original_items :
        tree .addTopLevelItem (item )
    for item in tree .original_items :
        values =[item .text (col )for col in range (item .columnCount ())]
        if not any (query in str (value ).lower ()for value in values ):
            tree .takeTopLevelItem (tree .indexOfTopLevelItem (item ))
def background_load_task (path ):
    level_json =sav_to_json (path )
    group_data_list =level_json ['properties']['worldSaveData']['value']['GroupSaveDataMap']['value']
    player_files =[]
    for group in group_data_list :
        if group ['value']['GroupType']['value']['value']=='EPalGroupType::Guild':
            guild_id =group ['key']['InstanceId']['value']if isinstance (group ['key'],dict )else str (group ['key'])
            players =group ['value']['RawData']['value'].get ('players',[])
            for p in players :
                uid =str (p .get ('player_uid','')).replace ('-','')
                name =p .get ('player_info',{}).get ('player_name','Unknown')
                player_files .append ((uid ,name ,guild_id ))
    return player_files 
def choose_level_file (window ,level_sav_entry ,old_tree ,new_tree ):
    path ,_ =QFileDialog .getOpenFileName (window ,t ("Select Level.sav file"),"","SAV Files (*.sav)")
    if not path :return 
    def task ():
        return background_load_task (path )
    def on_task_complete (player_data_list ):
        global player_list_cache 
        level_sav_entry .setText (path )
        old_tree .clear ()
        new_tree .clear ()
        for uid ,name ,guild in player_data_list :
            old_tree .addTopLevelItem (QTreeWidgetItem ([uid ,name ,guild ]))
            new_tree .addTopLevelItem (QTreeWidgetItem ([uid ,name ,guild ]))
        old_tree .original_items =[old_tree .topLevelItem (i )for i in range (old_tree .topLevelItemCount ())]
        new_tree .original_items =[new_tree .topLevelItem (i )for i in range (new_tree .topLevelItemCount ())]
        player_list_cache =[f"{u } - {n } - {g }"for u ,n ,g in player_data_list ]
    run_with_loading (on_task_complete ,task )
def extract_guid_from_tree_selection (tree ):
    selected =tree .selectedItems ()
    if not selected :
        return None 
    return selected [0 ].text (0 )
def fix_save_wrapper (window ,level_sav_entry ,old_tree ,new_tree ):
    old_guid =extract_guid_from_tree_selection (old_tree )
    new_guid =extract_guid_from_tree_selection (new_tree )
    file_path =level_sav_entry .text ()
    if not (old_guid and new_guid and file_path ):
        QMessageBox .warning (window ,"Error","Please select old GUID, new GUID and level save file!")
        return 
    if old_guid ==new_guid :
        QMessageBox .warning (window ,"Error","Old GUID and New GUID cannot be the same.")
        return 
    folder_path =os .path .dirname (file_path )
    fix_save (folder_path ,new_guid ,old_guid )
    for i ,entry in enumerate (player_list_cache ):
        if entry .startswith (old_guid ):
            player_list_cache [i ]=entry .replace (old_guid ,new_guid ,1 )
        elif entry .startswith (new_guid ):
            player_list_cache [i ]=entry .replace (new_guid ,old_guid ,1 )
    populate_player_tree (old_tree ,folder_path )
    populate_player_tree (new_tree ,folder_path )
def center_window (win ):
    screen =QApplication .primaryScreen ().availableGeometry ()
    geo =win .frameGeometry ()
    geo .moveCenter (screen .center ())
    win .move (geo .topLeft ())
class FixHostSaveWindow (QWidget ):
    def __init__ (self ):
        super ().__init__ ()
        self .setObjectName ("central")
        self .setWindowTitle (t ("Fix Host Save - GUID Migrator"))
        self .setFixedSize (1200 ,640 )
        try :
            self .setWindowIcon (QIcon (ICON_PATH ))
        except :
            pass 
        self .load_styles ()
        main_layout =QVBoxLayout (self )
        main_layout .setContentsMargins (14 ,14 ,14 ,14 )
        main_layout .setSpacing (12 )
        glass_frame =QFrame ()
        glass_frame .setObjectName ("glass")
        glass_layout =QVBoxLayout (glass_frame )
        glass_layout .setContentsMargins (12 ,12 ,12 ,12 )
        glass_layout .setSpacing (12 )
        file_row =QHBoxLayout ()
        file_label =QLabel (t ('Select Level.sav file:'))
        file_label .setFont (QFont ("Segoe UI",10 ,QFont .Bold ))
        file_row .addWidget (file_label )
        self .level_sav_entry =QLineEdit ()
        self .level_sav_entry .setPlaceholderText (t ("fix_host_save.path_to_level_sav"))
        file_row .addWidget (self .level_sav_entry ,1 )
        self .browse_button =QPushButton (t ("Browse"))
        self .browse_button .setFixedWidth (100 )
        file_row .addWidget (self .browse_button )
        self .migrate_button =QPushButton (t ("Migrate"))
        self .migrate_button .setObjectName ("MigrateButton")
        self .migrate_button .setFixedWidth (140 )
        file_row .addWidget (self .migrate_button )
        glass_layout .addLayout (file_row )
        trees_layout =QHBoxLayout ()
        trees_layout .setSpacing (14 )
        old_panel =QFrame ()
        old_panel .setObjectName ("treePanel")
        old_panel .setStyleSheet ("QFrame { background-color: transparent; }")
        old_panel_layout =QVBoxLayout (old_panel )
        old_panel_layout .setContentsMargins (8 ,8 ,8 ,8 )
        old_panel_layout .setSpacing (8 )
        old_header =QLabel (t ("fix_host_save.source_player"))
        old_header .setFont (QFont ("Segoe UI",11 ,QFont .Bold ))
        old_header .setAlignment (Qt .AlignCenter )
        old_panel_layout .addWidget (old_header )
        old_search_row =QHBoxLayout ()
        old_search_label =QLabel (t ("Search:"))
        old_search_row .addWidget (old_search_label )
        self .old_search_entry =QLineEdit ()
        self .old_search_entry .setPlaceholderText (t ("fix_host_save.search_source_player"))
        old_search_row .addWidget (self .old_search_entry )
        old_panel_layout .addLayout (old_search_row )
        self .old_tree =QTreeWidget ()
        self .old_tree .setHeaderLabels ([t ("GUID"),t ("Name"),t ("Guild ID")])
        self .old_tree .setSortingEnabled (True )
        self .old_tree .setSelectionMode (QTreeWidget .SingleSelection )
        old_panel_layout .addWidget (self .old_tree ,1 )
        self .source_result_label =QLabel (t ("Source Player: N/A"))
        old_panel_layout .addWidget (self .source_result_label )
        trees_layout .addWidget (old_panel ,1 )
        new_panel =QFrame ()
        new_panel .setObjectName ("treePanel")
        new_panel .setStyleSheet ("QFrame { background-color: transparent; }")
        new_panel_layout =QVBoxLayout (new_panel )
        new_panel_layout .setContentsMargins (8 ,8 ,8 ,8 )
        new_panel_layout .setSpacing (8 )
        new_header =QLabel (t ("fix_host_save.target_player"))
        new_header .setFont (QFont ("Segoe UI",11 ,QFont .Bold ))
        new_header .setAlignment (Qt .AlignCenter )
        new_panel_layout .addWidget (new_header )
        new_search_row =QHBoxLayout ()
        new_search_label =QLabel (t ("Search:"))
        new_search_row .addWidget (new_search_label )
        self .new_search_entry =QLineEdit ()
        self .new_search_entry .setPlaceholderText (t ("fix_host_save.search_target_player"))
        new_search_row .addWidget (self .new_search_entry )
        new_panel_layout .addLayout (new_search_row )
        self .new_tree =QTreeWidget ()
        self .new_tree .setHeaderLabels ([t ("GUID"),t ("Name"),t ("Guild ID")])
        self .new_tree .setSortingEnabled (True )
        self .new_tree .setSelectionMode (QTreeWidget .SingleSelection )
        new_panel_layout .addWidget (self .new_tree ,1 )
        self .target_result_label =QLabel (t ("Target Player: N/A"))
        new_panel_layout .addWidget (self .target_result_label )
        trees_layout .addWidget (new_panel ,1 )
        glass_layout .addLayout (trees_layout )
        bottom_label =QLabel (t ("fix_host_save.tip"))
        bottom_label .setAlignment (Qt .AlignCenter )
        bottom_label .setFont (QFont ("Segoe UI",9 ))
        glass_layout .addWidget (bottom_label )
        main_layout .addWidget (glass_frame )
        old_header_widget =self .old_tree .header ()
        old_header_widget .setSectionResizeMode (0 ,QHeaderView .Stretch )
        old_header_widget .setSectionResizeMode (1 ,QHeaderView .Stretch )
        old_header_widget .setSectionResizeMode (2 ,QHeaderView .Stretch )
        new_header_widget =self .new_tree .header ()
        new_header_widget .setSectionResizeMode (0 ,QHeaderView .Stretch )
        new_header_widget .setSectionResizeMode (1 ,QHeaderView .Stretch )
        new_header_widget .setSectionResizeMode (2 ,QHeaderView .Stretch )
        self .browse_button .clicked .connect (lambda :choose_level_file (self ,self .level_sav_entry ,self .old_tree ,self .new_tree ))
        self .migrate_button .clicked .connect (lambda :fix_save_wrapper (self ,self .level_sav_entry ,self .old_tree ,self .new_tree ))
        self .old_search_entry .textChanged .connect (lambda :filter_treeview (self .old_tree ,self .old_search_entry .text ()))
        self .new_search_entry .textChanged .connect (lambda :filter_treeview (self .new_tree ,self .new_search_entry .text ()))
        self .old_tree .itemSelectionChanged .connect (self .update_source_selection )
        self .new_tree .itemSelectionChanged .connect (self .update_target_selection )
        QTimer .singleShot (0 ,lambda :center_window (self ))
    def keyPressEvent (self ,event ):
        if event .key ()==Qt .Key_Escape :
            self .close ()
        else :
            super ().keyPressEvent (event )
    def update_source_selection (self ):
        selected =self .old_tree .selectedItems ()
        if selected :
            values =[selected [0 ].text (col )for col in range (3 )]
            self .source_result_label .setText (t ("Source Player: {name} ({guid})",name =values [1 ],guid =values [0 ]))
        else :
            self .source_result_label .setText (t ("Source Player: N/A"))
    def update_target_selection (self ):
        selected =self .new_tree .selectedItems ()
        if selected :
            values =[selected [0 ].text (col )for col in range (3 )]
            self .target_result_label .setText (t ("Target Player: {name} ({guid})",name =values [1 ],guid =values [0 ]))
        else :
            self .target_result_label .setText (t ("Target Player: N/A"))
    def load_styles (self ):
        user_cfg_path =os .path .join (get_assets_directory (),"data","configs","user.cfg")
        theme ="dark"
        if os .path .exists (user_cfg_path ):
            try :
                with open (user_cfg_path ,"r")as f :
                    data =json .load (f )
                theme =data .get ("theme","dark")
            except :
                pass 
        qss_path =os .path .join (get_assets_directory (),"data","gui",f"{theme }mode.qss")
        if os .path .exists (qss_path ):
            with open (qss_path ,"r")as f :
                self .setStyleSheet (f .read ())
def fix_host_save ():
    window =FixHostSaveWindow ()
    return window 
if __name__ =="__main__":
    if len (sys .argv )>3 :
        import shutil 
        save_path =sys .argv [1 ].strip ().strip ('"')
        old_guid =sys .argv [2 ].strip ()
        new_guid =sys .argv [3 ].strip ()
        if not os .path .exists (save_path ):
            print (f"Error: Path not found {save_path }")
            sys .exit (1 )
        QMessageBox .information =lambda *args ,**kwargs :None 
        QMessageBox .warning =lambda *args ,**kwargs :print (f"Warning: {args }")
        def run_with_loading_mock (on_finished ,task_func ):
            result =task_func ()
            on_finished (result )
        globals ()['run_with_loading']=run_with_loading_mock 
        print (f"Starting migration: {old_guid } -> {new_guid }")
        fix_save (os .path .dirname (save_path )if save_path .endswith ('Level.sav')else save_path ,new_guid ,old_guid )
        print ("Migration complete.")
    else :
        app =QApplication ([])
        w =FixHostSaveWindow ()
        w .show ()
        sys .exit (app .exec ())
