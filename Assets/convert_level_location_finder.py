import sys ,os ,glob ,gc ,threading ,time 
from import_libs import *
from loading_manager import run_with_loading 
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
def file_picker (ext ):
    root =tk .Tk ()
    root .withdraw ()
    path =None 
    if ext =="sav":
        path =filedialog .askopenfilename (title ="Select Level.json",filetypes =[("Level.json","Level.json")])
    elif ext =="json":
        path =filedialog .askopenfilename (title ="Select Level.sav",filetypes =[("Level.sav","Level.sav")])
    root .destroy ()
    return path 
def convert_level_location_finder (ext ):
    level_file =file_picker (ext )
    if not level_file :return False 
    loop =QEventLoop ()
    if ext =="sav":
        output_path =level_file .replace (".json",".sav")
        def task ():
            convert_json_to_sav (level_file ,output_path )
            gc .collect ()
    else :
        output_path =level_file .replace (".sav",".json")
        def task ():
            convert_sav_to_json (level_file ,output_path )
            gc .collect ()
    run_with_loading (lambda _ :loop .quit (),task )
    loop .exec ()
    time .sleep (0.5 )
    print (f"Converted {level_file } to {output_path }")
    return True 
def main ():
    if len (sys .argv )!=2 or sys .argv [1 ]not in ["sav","json"]:
        print ("Usage: script.py <sav|json>")
        exit (1 )
    if not convert_level_location_finder (sys .argv [1 ]):
        exit (1 )
if __name__ =="__main__":
    main ()
