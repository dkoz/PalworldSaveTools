import os 
from PySide6 .QtWidgets import (
QDialog ,QVBoxLayout ,QHBoxLayout ,QLabel ,QPushButton ,
QLineEdit ,QSpinBox ,QComboBox ,QTextEdit ,QFileDialog ,
QMessageBox ,QGroupBox ,QFormLayout ,QCheckBox 
)
from PySide6 .QtCore import Qt 
from PySide6 .QtGui import QIcon ,QFont 
from i18n import t 
try :
    from palworld_aio import constants 
except ImportError :
    from .import constants 
class InputDialog (QDialog ):
    def __init__ (self ,title ,prompt ,parent =None ,mode ='text'):
        super ().__init__ (parent )
        self .setWindowTitle (title )
        self .setModal (True )
        self .setMinimumWidth (400 )
        if os .path .exists (constants .ICON_PATH ):
            self .setWindowIcon (QIcon (constants .ICON_PATH ))
        layout =QVBoxLayout (self )
        label =QLabel (prompt )
        layout .addWidget (label )
        self .input_field =QLineEdit ()
        layout .addWidget (self .input_field )
        button_layout =QHBoxLayout ()
        ok_btn =QPushButton (t ('button.ok')if t else 'OK')
        ok_btn .clicked .connect (self .accept )
        cancel_btn =QPushButton (t ('button.cancel')if t else 'Cancel')
        cancel_btn .clicked .connect (self .reject )
        button_layout .addWidget (ok_btn )
        button_layout .addWidget (cancel_btn )
        layout .addLayout (button_layout )
        self .result_value =None 
    def accept (self ):
        self .result_value =self .input_field .text ()
        super ().accept ()
    def showEvent (self ,event ):
        """Center on parent when first shown."""
        super ().showEvent (event )
        if not event .spontaneous ():
            try :
                from palworld_aio .ui .tools_tab import center_on_parent
                center_on_parent (self )
            except ImportError :
                from ..ui .tools_tab import center_on_parent
                center_on_parent (self )
    @staticmethod
    def get_text (title ,prompt ,parent =None ,mode ='text'):
        dialog =InputDialog (title ,prompt ,parent ,mode )
        if dialog .exec ()==QDialog .Accepted :
            return dialog .result_value 
        return None 
class DaysInputDialog (QDialog ):
    def __init__ (self ,title ,prompt ,parent =None ):
        super ().__init__ (parent )
        self .setWindowTitle (title )
        self .setModal (True )
        self .setMinimumWidth (300 )
        if os .path .exists (constants .ICON_PATH ):
            self .setWindowIcon (QIcon (constants .ICON_PATH ))
        layout =QVBoxLayout (self )
        label =QLabel (prompt )
        layout .addWidget (label )
        self .spin_box =QSpinBox ()
        self .spin_box .setMinimum (1 )
        self .spin_box .setMaximum (365 )
        self .spin_box .setValue (30 )
        layout .addWidget (self .spin_box )
        button_layout =QHBoxLayout ()
        ok_btn =QPushButton (t ('button.ok')if t else 'OK')
        ok_btn .clicked .connect (self .accept )
        cancel_btn =QPushButton (t ('button.cancel')if t else 'Cancel')
        cancel_btn .clicked .connect (self .reject )
        button_layout .addWidget (ok_btn )
        button_layout .addWidget (cancel_btn )
        layout .addLayout (button_layout )
        self .result_value =None 
    def accept (self ):
        self .result_value =self .spin_box .value ()
        super ().accept ()
    def showEvent (self ,event ):
        """Center on parent when first shown."""
        super ().showEvent (event )
        if not event .spontaneous ():
            try :
                from palworld_aio .ui .tools_tab import center_on_parent
                center_on_parent (self )
            except ImportError :
                from ..ui .tools_tab import center_on_parent
                center_on_parent (self )
    @staticmethod
    def get_days (title ,prompt ,parent =None ):
        dialog =DaysInputDialog (title ,prompt ,parent )
        if dialog .exec ()==QDialog .Accepted :
            return dialog .result_value 
        return None 
class KillNearestBaseDialog (QDialog ):
    def __init__ (self ,parent =None ):
        super ().__init__ (parent )
        self .setWindowTitle (t ('kill_nearest_base.title')if t else 'Kill Nearest Base Config')
        self .setModal (True )
        self .setMinimumWidth (500 )
        self .setMinimumHeight (400 )
        if os .path .exists (constants .ICON_PATH ):
            self .setWindowIcon (QIcon (constants .ICON_PATH ))
        layout =QVBoxLayout (self )
        form_group =QGroupBox (t ('kill_nearest_base.settings')if t else 'Settings')
        form_layout =QFormLayout ()
        self .coord_x =QSpinBox ()
        self .coord_x .setRange (-999999 ,999999 )
        self .coord_x .setValue (0 )
        form_layout .addRow ('X:',self .coord_x )
        self .coord_y =QSpinBox ()
        self .coord_y .setRange (-999999 ,999999 )
        self .coord_y .setValue (0 )
        form_layout .addRow ('Y:',self .coord_y )
        self .radius =QSpinBox ()
        self .radius .setRange (1 ,100000 )
        self .radius .setValue (5000 )
        form_layout .addRow (t ('kill_nearest_base.radius')if t else 'Radius:',self .radius )
        self .use_new_coords =QCheckBox (t ('kill_nearest_base.use_new_coords')if t else 'Use New Coordinates')
        self .use_new_coords .setChecked (True )
        form_layout .addRow ('',self .use_new_coords )
        form_group .setLayout (form_layout )
        layout .addWidget (form_group )
        self .output_text =QTextEdit ()
        self .output_text .setReadOnly (True )
        self .output_text .setFont (QFont ('Consolas',9 ))
        layout .addWidget (self .output_text )
        button_layout =QHBoxLayout ()
        generate_btn =QPushButton (t ('kill_nearest_base.generate')if t else 'Generate')
        generate_btn .clicked .connect (self .generate_command )
        copy_btn =QPushButton (t ('kill_nearest_base.copy')if t else 'Copy to Clipboard')
        copy_btn .clicked .connect (self .copy_to_clipboard )
        close_btn =QPushButton (t ('button.close')if t else 'Close')
        close_btn .clicked .connect (self .reject )
        button_layout .addWidget (generate_btn )
        button_layout .addWidget (copy_btn )
        button_layout .addWidget (close_btn )
        layout .addLayout (button_layout )
    def generate_command (self ):
        x =self .coord_x .value ()
        y =self .coord_y .value ()
        radius =self .radius .value ()
        use_new =self .use_new_coords .isChecked ()
        import palworld_coord 
        if use_new :
            sav_x ,sav_y =palworld_coord .map_to_sav (x ,y ,new =True )
        else :
            sav_x ,sav_y =palworld_coord .map_to_sav (x ,y ,new =False )
        command =f'/KillNearestBase {int (sav_x )} {int (sav_y )} {radius }'
        self .output_text .setPlainText (command )
    def copy_to_clipboard (self ):
        from PySide6 .QtWidgets import QApplication
        clipboard =QApplication .clipboard ()
        clipboard .setText (self .output_text .toPlainText ())
    def showEvent (self ,event ):
        """Center on parent when first shown."""
        super ().showEvent (event )
        if not event .spontaneous ():
            try :
                from palworld_aio .ui .tools_tab import center_on_parent
                center_on_parent (self )
            except ImportError :
                from ..ui .tools_tab import center_on_parent
                center_on_parent (self )
class ConfirmDialog (QDialog ):
    def __init__ (self ,title ,message ,parent =None ):
        super ().__init__ (parent )
        self .setWindowTitle (title )
        self .setModal (True )
        self .setMinimumWidth (350 )
        if os .path .exists (constants .ICON_PATH ):
            self .setWindowIcon (QIcon (constants .ICON_PATH ))
        layout =QVBoxLayout (self )
        label =QLabel (message )
        label .setWordWrap (True )
        layout .addWidget (label )
        button_layout =QHBoxLayout ()
        yes_btn =QPushButton (t ('button.yes')if t else 'Yes')
        yes_btn .clicked .connect (self .accept )
        no_btn =QPushButton (t ('button.no')if t else 'No')
        no_btn .clicked .connect (self .reject )
        button_layout .addWidget (yes_btn )
        button_layout .addWidget (no_btn )
        layout .addLayout (button_layout )
    def showEvent (self ,event ):
        """Center on parent when first shown."""
        super ().showEvent (event )
        if not event .spontaneous ():
            try :
                from palworld_aio .ui .tools_tab import center_on_parent
                center_on_parent (self )
            except ImportError :
                from ..ui .tools_tab import center_on_parent
                center_on_parent (self )
    @staticmethod
    def confirm (title ,message ,parent =None ):
        dialog =ConfirmDialog (title ,message ,parent )
        return dialog .exec ()==QDialog .Accepted 
class PalDefenderDialog (QDialog ):
    def __init__ (self ,parent =None ):
        super ().__init__ (parent )
        self .setWindowTitle ('Generate PalDefender killnearestbase Commands')
        self .setMinimumSize (800 ,600 )
        if os .path .exists (constants .ICON_PATH ):
            self .setWindowIcon (QIcon (constants .ICON_PATH ))
        self ._setup_ui ()
    def _setup_ui (self ):
        from PySide6 .QtWidgets import QRadioButton ,QButtonGroup ,QFrame 
        layout =QVBoxLayout (self )
        layout .setSpacing (15 )
        layout .setContentsMargins (20 ,20 ,20 ,20 )
        filter_frame =QFrame ()
        filter_frame .setFrameShape (QFrame .StyledPanel )
        filter_layout =QVBoxLayout (filter_frame )
        filter_label =QLabel (t ('paldefender.filter_type')if t else 'Filter Type:')
        filter_label .setFont (QFont (constants .FONT_FAMILY ,constants .FONT_SIZE ,QFont .Bold ))
        filter_layout .addWidget (filter_label )
        radio_layout =QHBoxLayout ()
        self .filter_group =QButtonGroup (self )
        self .radio_inactivity =QRadioButton (t ('paldefender.inactivity')if t else 'Inactivity (days)')
        self .radio_maxlevel =QRadioButton (t ('paldefender.max_level')if t else 'Max Level')
        self .radio_both =QRadioButton (t ('paldefender.both')if t else 'Both')
        self .filter_group .addButton (self .radio_inactivity ,1 )
        self .filter_group .addButton (self .radio_maxlevel ,2 )
        self .filter_group .addButton (self .radio_both ,3 )
        self .radio_inactivity .setChecked (True )
        radio_layout .addWidget (self .radio_inactivity )
        radio_layout .addWidget (self .radio_maxlevel )
        radio_layout .addWidget (self .radio_both )
        radio_layout .addStretch ()
        filter_layout .addLayout (radio_layout )
        instructions =QLabel (
        t ('paldefender.instructions')if t else 
        'Choose filter type:\n'
        'Inactivity: Select bases with ALL players inactive for given days.\n'
        'Max Level: Select bases with ALL players below given level.\n'
        'Both: Combine both filters (ALL players must match both criteria).'
        )
        instructions .setStyleSheet (f"color: {constants .MUTED }; padding: 10px;")
        instructions .setWordWrap (True )
        filter_layout .addWidget (instructions )
        layout .addWidget (filter_frame )
        input_layout =QHBoxLayout ()
        inactivity_label =QLabel (t ('paldefender.inactivity_days')if t else 'Inactivity Days:')
        input_layout .addWidget (inactivity_label )
        self .inactivity_spin =QSpinBox ()
        self .inactivity_spin .setMinimum (1 )
        self .inactivity_spin .setMaximum (9999 )
        self .inactivity_spin .setValue (30 )
        self .inactivity_spin .setMinimumWidth (100 )
        input_layout .addWidget (self .inactivity_spin )
        input_layout .addSpacing (20 )
        maxlevel_label =QLabel (t ('paldefender.max_level_label')if t else 'Max Level:')
        input_layout .addWidget (maxlevel_label )
        self .maxlevel_spin =QSpinBox ()
        self .maxlevel_spin .setMinimum (1 )
        self .maxlevel_spin .setMaximum (100 )
        self .maxlevel_spin .setValue (10 )
        self .maxlevel_spin .setMinimumWidth (100 )
        input_layout .addWidget (self .maxlevel_spin )
        input_layout .addStretch ()
        layout .addLayout (input_layout )
        run_btn =QPushButton (t ('button.run')if t else 'Run')
        run_btn .setMinimumHeight (40 )
        run_btn .setFont (QFont (constants .FONT_FAMILY ,constants .FONT_SIZE ,QFont .Bold ))
        run_btn .clicked .connect (self ._on_generate )
        layout .addWidget (run_btn )
        output_label =QLabel (t ('paldefender.output')if t else 'Output:')
        output_label .setFont (QFont (constants .FONT_FAMILY ,constants .FONT_SIZE ,QFont .Bold ))
        layout .addWidget (output_label )
        self .output_text =QTextEdit ()
        self .output_text .setReadOnly (True )
        self .output_text .setFont (QFont ('Consolas',10 ))
        self .output_text .setStyleSheet (f"background-color: {constants .GLASS }; color: {constants .TEXT };")
        layout .addWidget (self .output_text )
    def showEvent (self ,event ):
        """Center on parent when first shown."""
        super ().showEvent (event )
        if not event .spontaneous ():
            try :
                from palworld_aio .ui .tools_tab import center_on_parent
                center_on_parent (self )
            except ImportError :
                from ..ui .tools_tab import center_on_parent
                center_on_parent (self )
    def _append_output (self ,text ):
        self .output_text .append (text )
    def _clear_output (self ):
        self .output_text .clear ()
    def _on_generate (self ):
        self ._clear_output ()
        try :
            filter_type =self .filter_group .checkedId ()
            inactivity_days =self .inactivity_spin .value ()if filter_type in (1 ,3 )else None 
            max_level =self .maxlevel_spin .value ()if filter_type in (2 ,3 )else None 
            result =self ._parse_log (inactivity_days =inactivity_days ,max_level =max_level )
            if not result :
                self ._append_output (t ('paldefender.no_match')if t else 'No guilds matched the filter criteria.')
        except Exception as e :
            QMessageBox .critical (self ,t ('error.title')if t else 'Error',str (e ))
    def _parse_log (self ,inactivity_days =None ,max_level =None ):
        import re 
        import palworld_coord 
        base_dir =constants .get_base_path ()
        log_file =os .path .join (base_dir ,'Scan Save Logger','scan_save.log')
        if not os .path .exists (log_file ):
            self ._append_output (f"Log file not found: {log_file }")
            self ._append_output ("Please load a save file first to generate the scan_save.log file.")
            return False 
        with open (log_file ,'r',encoding ='utf-8',errors ='ignore')as f :
            content =f .read ()
        guilds =[g .strip ()for g in re .split ('={60,}',content )if g .strip ()]
        inactive_guilds ={}
        kill_commands =[]
        guild_count =base_count =excluded_guilds =excluded_bases =0 
        for guild in guilds :
            players_data =re .findall (
            r'Player: (.+?) \| UID: ([a-f0-9-]+) \| Level: (\d+) \| Caught: (\d+) \| Owned: (\d+) \| Encounters: (\d+) \| Uniques: (\d+) \| Last Online: (.+? ago)',
            guild 
            )
            bases =re .findall (r'Base \d+: Base ID: ([a-f0-9-]+) \| .+? \| RawData: (.+)',guild )
            if not players_data or not bases :
                continue 
            guild_name_match =re .search (r'Guild: (.+?) \|',guild )
            guild_leader_match =re .search (r'Guild Leader: (.+?) \|',guild )
            guild_id_match =re .search (r'Guild ID: ([a-f0-9-]+)',guild )
            guild_name =guild_name_match .group (1 )if guild_name_match else 'Unnamed Guild'
            guild_leader =guild_leader_match .group (1 )if guild_leader_match else 'Unknown'
            guild_id =guild_id_match .group (1 )if guild_id_match else 'Unknown'
            if guild_id in constants .exclusions .get ('guilds',[]):
                excluded_guilds +=1 
                continue 
            filtered_bases =[]
            for base_id ,raw_data in bases :
                if base_id in constants .exclusions .get ('bases',[]):
                    excluded_bases +=1 
                    continue 
                filtered_bases .append ((base_id ,raw_data ))
            if not filtered_bases :
                continue 
            if inactivity_days is not None :
                all_inactive =True 
                for player in players_data :
                    last_online =player [7 ]
                    if 'd'in last_online :
                        days_match =re .search (r'(\d+)d',last_online )
                        if days_match :
                            days =int (days_match .group (1 ))
                            if days <inactivity_days :
                                all_inactive =False 
                                break 
                        else :
                            all_inactive =False 
                            break 
                    else :
                        all_inactive =False 
                        break 
                if not all_inactive :
                    continue 
            if max_level is not None :
                if any (int (player [2 ])>max_level for player in players_data ):
                    continue 
            if guild_id not in inactive_guilds :
                inactive_guilds [guild_id ]={
                'guild_name':guild_name ,
                'guild_leader':guild_leader ,
                'players':[],
                'bases':[]
                }
            for player in players_data :
                inactive_guilds [guild_id ]['players'].append ({
                'name':player [0 ],
                'uid':player [1 ],
                'level':player [2 ],
                'caught':player [3 ],
                'owned':player [4 ],
                'encounters':player [5 ],
                'uniques':player [6 ],
                'last_online':player [7 ]
                })
            inactive_guilds [guild_id ]['bases'].extend (filtered_bases )
            guild_count +=1 
            base_count +=len (filtered_bases )
            for base_id ,raw_data in filtered_bases :
                coords =re .findall (r'[-+]?\d*\.?\d+',raw_data )
                if len (coords )>=3 :
                    x ,y ,z =map (float ,coords [:3 ])
                    base_coords =palworld_coord .sav_to_map (x ,y )
                    kill_commands .append (f'killnearestbase {base_coords .x :.2f} {base_coords .y :.2f} {z :.2f}')
        for guild_id ,info in inactive_guilds .items ():
            self ._append_output (f"Guild: {info ['guild_name']} | Leader: {info ['guild_leader']} | ID: {guild_id }")
            self ._append_output (f"Players: {len (info ['players'])}")
            for p in info ['players']:
                self ._append_output (f"  Player: {p ['name']} | UID: {p ['uid']} | Level: {p ['level']} | Caught: {p ['caught']} | Owned: {p ['owned']} | Encounters: {p ['encounters']} | Uniques: {p ['uniques']} | Last Online: {p ['last_online']}")
            self ._append_output (f"Bases: {len (info ['bases'])}")
            for base_id ,raw_data in info ['bases']:
                self ._append_output (f'  Base ID: {base_id } | RawData: {raw_data }')
            self ._append_output ('-'*40 )
        self ._append_output (f'\nFound {guild_count } guild(s) with {base_count } base(s).')
        if kill_commands :
            output_dir =os .path .join (constants .get_base_path (),'PalDefender')
            os .makedirs (output_dir ,exist_ok =True )
            commands_file =os .path .join (output_dir ,'paldefender_bases.log')
            with open (commands_file ,'w',encoding ='utf-8')as f :
                f .write ('\n'.join (kill_commands ))
            self ._append_output (f'Wrote {len (kill_commands )} kill commands to {commands_file }')
            info_file =os .path .join (output_dir ,'paldefender_bases_info.log')
            with open (info_file ,'w',encoding ='utf-8')as info_log :
                info_log .write ('-'*40 +'\n')
                for gid ,ginfo in inactive_guilds .items ():
                    info_log .write (f"Guild: {ginfo ['guild_name']} | Leader: {ginfo ['guild_leader']} | ID: {gid }\n")
                    info_log .write (f"Players: {len (ginfo ['players'])}\n")
                    for p in ginfo ['players']:
                        info_log .write (f"  Player: {p ['name']} | UID: {p ['uid']} | Level: {p ['level']} | Caught: {p ['caught']} | Owned: {p ['owned']} | Encounters: {p ['encounters']} | Uniques: {p ['uniques']} | Last Online: {p ['last_online']}\n")
                    info_log .write (f"Bases: {len (ginfo ['bases'])}\n")
                    for base_id ,raw_data in ginfo ['bases']:
                        coords =re .findall (r'[-+]?\d*\.?\d+',raw_data )
                        if len (coords )>=3 :
                            x ,y ,z =map (float ,coords [:3 ])
                            map_coords =palworld_coord .sav_to_map (x ,y )
                            info_log .write (f'  Base ID: {base_id } | Map Coords: X: {map_coords .x :.2f}, Y: {map_coords .y :.2f}, Z: {z :.2f}\n')
                        else :
                            info_log .write (f'  Base ID: {base_id } | Invalid RawData: {raw_data }\n')
                    info_log .write ('-'*40 +'\n')
                info_log .write (f'Found {guild_count } guild(s) with {base_count } base(s).\n')
                info_log .write ('-'*40 )
        else :
            self ._append_output ('No kill commands generated.')
        if inactivity_days is not None :
            self ._append_output (f'Inactivity filter applied: >= {inactivity_days } day(s).')
        if max_level is not None :
            self ._append_output (f'Level filter applied: <= {max_level }.')
        self ._append_output (f'Excluded guilds: {excluded_guilds }')
        self ._append_output (f'Excluded bases: {excluded_bases }')
        return guild_count >0 
