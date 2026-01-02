import sys ,os ,gc ,time 
from import_libs import *
from Assets .loading_manager import run_with_loading 
import tkinter as tk 
from tkinter import filedialog 
from PySide6 .QtCore import QEventLoop 
sys .path .insert (0 ,os .path .join (os .path .dirname (__file__ ),"palworld_save_tools","commands"))
from convert import main as convert_main 
def convert_sav_to_json (input_file ,output_file ):
    old_argv =sys .argv 
    try :
        sys .argv =["convert",input_file ,"--output",output_file ,"--force"]
        convert_main ()
    finally :
        sys .argv =old_argv 
def convert_json_to_sav (input_file ,output_file ):
    old_argv =sys .argv 
    try :
        sys .argv =["convert",input_file ,"--output",output_file ,"--force"]
        convert_main ()
    finally :
        sys .argv =old_argv 
def pick_players_folder ():
    root =tk .Tk ()
    root .withdraw ()
    folder =filedialog .askdirectory (title ="Select Players Folder")
    root .destroy ()
    if folder and os .path .basename (folder )=="Players":
        return folder 
    print ("Invalid folder or no folder selected.")
    return None 
def convert_players_location_finder (ext ):
    players_folder =pick_players_folder ()
    if not players_folder :return False 
    files_to_convert =[]
    for root ,_ ,files in os .walk (players_folder ):
        for file in files :
            path =os .path .join (root ,file )
            if ext =="sav"and file .endswith (".json"):
                files_to_convert .append ((path ,path .replace (".json",".sav")))
            elif ext =="json"and file .endswith (".sav"):
                files_to_convert .append ((path ,path .replace (".sav",".json")))
    if not files_to_convert :
        print ("No valid files found for conversion.")
        return True 
    loop =QEventLoop ()
    def task ():
        for src ,dst in files_to_convert :
            if ext =="sav":
                convert_json_to_sav (src ,dst )
            else :
                convert_sav_to_json (src ,dst )
            print (f"Converted {src } to {dst }")
        gc .collect ()
    run_with_loading (lambda _ :loop .quit (),task )
    loop .exec ()
    time .sleep (0.5 )
    return True 
def main ():
    if len (sys .argv )!=2 or sys .argv [1 ]not in ["sav","json"]:
        print ("Usage: script.py <sav|json>")
        exit (1 )
    if not convert_players_location_finder (sys .argv [1 ]):
        exit (1 )
if __name__ =="__main__":
    main ()
