#!/usr/bin/env python3
from __future__ import annotations
import os,sys,shutil,subprocess,threading,queue,argparse,re
from pathlib import Path
from typing import Optional
PROJECT_DIR=Path(__file__).resolve().parent
VENV_DIR=PROJECT_DIR/"pst_venv"
SENTINEL=VENV_DIR/".ready"
USE_ANSI=True
if os.name=="nt":
    try:
        import ctypes
        kernel32=ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11),5)
    except Exception:pass
def ansi(code:str)->str:return code if USE_ANSI else ""
RESET,BOLD,GREEN,YELLOW,RED,CYAN,DIM=ansi("\x1b[0m"),ansi("\x1b[1m"),ansi("\x1b[32m"),ansi("\x1b[33m"),ansi("\x1b[31m"),ansi("\x1b[36m"),ansi("\x1b[2m")
def step_label(n:int,total:int,text:str)->str:return f"[{n}/{total}] {text}"
def print_step_working(label:str):
    sys.stdout.write(f"{BOLD}{label}...{RESET}\r")
    sys.stdout.flush()
def print_ok(label:str):
    sys.stdout.write("\r"+" "*120+"\r")
    print(f"{BOLD}{label} {GREEN}OK{RESET}")
def print_fail(label:str):
    sys.stdout.write("\r"+" "*120+"\r")
    print(f"{BOLD}{label} {RED}FAILED{RESET}")
def reader_thread(proc:subprocess.Popen,q:queue.Queue):
    assert proc.stdout is not None
    try:
        for raw in proc.stdout:q.put(raw.rstrip("\n"))
    except Exception:pass
    finally:
        try:proc.stdout.close()
        except Exception:pass
        q.put(None)
def progress_bar(pct:int,width:int=30)->str:
    filled=int((pct/100.0)*width)
    return "["+"#"*filled+"-"*(width-filled)+"]"
def run_and_watch(cmd,cwd=None,env=None):
    filter_keys=("Collecting","Downloading","%","Building wheel for","Installing collected packages","Successfully installed","ERROR","Failed")
    cmd_list=list(map(str,cmd))
    proc=subprocess.Popen(cmd_list,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1,cwd=cwd,env=env)
    q:queue.Queue=queue.Queue()
    threading.Thread(target=reader_thread,args=(proc,q),daemon=True).start()
    progress_pct,last_shown_msg=None,None
    try:
        while True:
            try:line=q.get(timeout=0.08)
            except queue.Empty:line=None
            if line is None:
                if proc.poll() is not None and q.empty():break
                continue
            s=line.rstrip()
            m=re.search(r"(\d{1,3})\s*%+",s)
            pct=int(m.group(1)) if m else None
            if pct is not None:progress_pct=max(0,min(100,pct))
            if any(key in s for key in filter_keys) or progress_pct is not None:
                if s!=last_shown_msg:
                    if progress_pct is not None:
                        sys.stdout.write(f"\r{CYAN}{progress_bar(progress_pct,width=28)} {progress_pct:3d}%{RESET}")
                        sys.stdout.flush()
                    else:
                        sys.stdout.write("\r"+" "*120+"\r")
                        print(f"{CYAN}> {s}{RESET}")
                    last_shown_msg=s
    finally:
        sys.stdout.write("\r"+" "*120+"\r")
        sys.stdout.flush()
    return proc.wait()
def nuke_build_artifacts():
    print_step_working("Cleaning environment")
    for item in ["build","dist"]:
        path=PROJECT_DIR/item
        if path.exists():shutil.rmtree(path,ignore_errors=True)
    for p in PROJECT_DIR.rglob("*.egg-info"):
        if p.is_dir():shutil.rmtree(p,ignore_errors=True)
    print_ok("Environment cleaned")
def venv_python_path()->Path:
    if os.name=="nt":return VENV_DIR/"Scripts"/"python.exe"
    return VENV_DIR/"bin"/"python"
def main():
    msg = r"""
  ___      _                _    _ ___              _____         _    
 | _ \__ _| |_ __ _____ _ _| |__| / __| __ ___ ____|_   _|__  ___| |___
 |  _/ _` | \ V  V / _ \ '_| / _` \__ \/ _` \ V / -_)| |/ _ \/ _ \ (_-<
 |_| \__,_|_|\_/\_/\___/_| |_\__,_|___/\__,_|\_/\___||_|\___/\___/_/__/
    """
    print(msg)
    if not SENTINEL.exists():
        nuke_build_artifacts()
        if not VENV_DIR.exists():
            print_step_working(step_label(1,3,"Creating Virtual Environment"))
            subprocess.run([sys.executable,"-m","venv",str(VENV_DIR)])
            print_ok(step_label(1,3,"Venv created"))
        vpy=venv_python_path()
        print_step_working(step_label(2,3,"Updating Dependencies"))
        ret=run_and_watch([str(vpy),"-m","pip","install","pip==24.3.1","setuptools==75.6.0","wheel","numpy==2.1.3","PySide6-Essentials","shiboken6","packaging"])
        if ret==0:
            SENTINEL.touch()
            print_ok(step_label(2,3,"Dependencies updated"))
        else:
            print_fail(step_label(2,3,"Dependency update failed"))
            return
    vpy=venv_python_path()
    start_py=PROJECT_DIR/"start.py"
    if start_py.exists():
        if SENTINEL.exists():
            print(f"{DIM}{step_label(3,3,'Environment ready, bypassing checks')}{RESET}")
        print(f"{BOLD}{step_label(3,3,'Launching Application')}{RESET}")
        subprocess.call([str(vpy),str(start_py)])
if __name__=="__main__":
    main()