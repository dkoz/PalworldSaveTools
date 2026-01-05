import os ,sys ,subprocess 
APP_NAME ="PalworldSaveTools"
APP_VERSION ="1.1.49"
GAME_VERSION ="0.7.0"
def get_base_directory ():
    if getattr (sys ,'frozen',False ):
        return os .path .dirname (sys .executable )
    else :
        return os .path .dirname (os .path .abspath (__file__ ))
def get_assets_directory ():
    base_dir =get_base_directory ()
    if getattr (sys ,'frozen',False ):
        return os .path .join (base_dir ,"Assets")
    else :
        return base_dir 
def get_resources_directory ():
    return os .path .join (get_assets_directory (),"resources")
ICON_PATH =os .path .join (get_resources_directory (),"pal.ico")
BACKUP_BASE_DIR =os .path .join (get_base_directory (),"Backups")
def get_backup_directory (tool_name ):
    return os .path .join (BACKUP_BASE_DIR ,tool_name )
BACKUP_DIRS ={
"all_in_one_tools":"AllinOneTools",
"slot_injector":"Slot Injector",
"character_transfer":"Character Transfer",
"fix_host_save":"Fix Host Save",
"restore_map":"Restore Map"
}
def is_frozen ():
    return getattr (sys ,'frozen',False )
def get_python_executable ():
    if is_frozen ():
        return sys .executable 
    else :
        return sys .executable 
def get_versions ():
    return APP_VERSION ,GAME_VERSION 
def open_file_with_default_app (file_path ):
    import platform 
    if not os .path .exists (file_path ):
        print (f"File not found: {file_path }")
        return False 
    try :
        if platform .system ()=="Windows":
            os .startfile (file_path )
        elif platform .system ()=="Darwin":
            import subprocess 
            subprocess .run (["open",file_path ])
        else :
            import subprocess 
            subprocess .run (["xdg-open",file_path ])
        return True 
    except Exception as e :
        print (f"Error opening file {file_path }: {e }")
        return False 
def unlock_self_folder ():
    if getattr (sys ,'frozen',False ):
        folder =os .path .dirname (os .path .abspath (sys .executable ))
    else :
        script_dir =os .path .dirname (os .path .abspath (sys .argv [0 ]))
        assets_dir =os .path .dirname (script_dir )
        folder =os .path .dirname (assets_dir )
    folder_escaped =folder .replace ("\\","\\\\").replace ("'","''")
    parent_pid =os .getpid ()
    ps_command =(
    f"$ErrorActionPreference = 'SilentlyContinue'; "
    f"$target = '{folder_escaped }'; "
    f"$pPid = {parent_pid }; "
    f"$currentPid = $PID; "
    "function Global-Nuke { "
    "  try { "
    "    $procs = Get-Process | Where-Object { $_.Path -like \"$target*\" -and $_.Id -ne $PID }; "
    "    $handleProcs = @(); "
    "    try { "
    "      $allProcs = Get-Process; "
    "      foreach($p in $allProcs){ "
    "        if($p.Id -ne $PID){ "
    "          try { "
    "            $handles = Get-WmiObject Win32_ProcessHandle -Filter \"ProcessId=$($p.Id)\" 2>$null; "
    "            foreach($h in $handles){ "
    "              if($h.Handle -and $h.Handle.Name -like \"$target*\"){ "
    "                $handleProcs += $p; "
    "                break; "
    "              } "
    "            } "
    "          } catch { } "
    "        } "
    "      } "
    "    } catch { } "
    "    $allProcsToKill = $procs + $handleProcs | Select-Object -Unique; "
    "    foreach($p in $allProcsToKill){ "
    "      try { "
    "        Stop-Process -Id $p.Id -Force -ErrorAction Stop; "
    "      } catch { "
    "        try { taskkill /F /T /PID $p.Id /NoWindow 2>$null; } catch { } "
    "      } "
    "    } "
    "  } catch { } "
    "}; "
    "$monitorCount = 0; "
    "while($true){ "
    "  Start-Sleep -Milliseconds 500; "
    "  $monitorCount++; "
    "  try { "
    "    $parent = Get-Process -Id $pPid -ErrorAction Stop; "
    "  } catch { "
    "    Global-Nuke; "
    "    break; "
    "  } "
    "}; "
    "Stop-Process -Id $currentPid -Force"
    )
    si =subprocess .STARTUPINFO ()
    si .dwFlags =subprocess .STARTF_USESHOWWINDOW 
    si .dwFlags |=subprocess .STARTF_USESHOWWINDOW 
    si .wShowWindow =subprocess .SW_HIDE 
    try :
        subprocess .Popen (
        ["powershell","-WindowStyle","Hidden","-ExecutionPolicy","Bypass","-Command",ps_command ],
        startupinfo =si ,
        creationflags =subprocess .CREATE_NO_WINDOW ,
        cwd =os .path .dirname (folder )
        )
    except Exception :
        pass 
