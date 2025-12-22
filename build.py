import os,sys,subprocess,shutil,re
VENV_DIR="pst_venv"
PYTHON_EXE=os.path.join(VENV_DIR,"Scripts","python.exe") if os.name=="nt" else os.path.join(VENV_DIR,"bin","python")
def create_venv():
    if not os.path.exists(VENV_DIR):
        print("Creating virtual environment...")
        subprocess.check_call([sys.executable,"-m","venv",VENV_DIR])
    else:
        print("Virtual environment already exists.")
def install_deps():
    print("Installing dependencies in venv...")
    subprocess.check_call([PYTHON_EXE,"-m","pip","install","pip==24.3.1","setuptools==75.6.0","wheel"])
    subprocess.check_call([PYTHON_EXE,"-m","pip","install","numpy==2.1.3"])
    subprocess.check_call([PYTHON_EXE,"-m","pip","install","PySide6-Essentials","cx_Freeze==8.5.1"])
    if os.path.exists("requirements.txt"):
        subprocess.check_call([PYTHON_EXE,"-m","pip","install","-r","requirements.txt"])
def sync_version():
    common_file=os.path.join("Assets","common.py")
    pyproject_file="pyproject.toml"
    setup_file="setup_freeze.py"
    version="1.1.37"
    if os.path.exists(common_file):
        with open(common_file,"r",encoding="utf-8") as f:
            for line in f:
                if line.strip().startswith("APP_VERSION"):
                    version=line.split("=")[1].strip().strip('"').strip("'")
                    break
    for file_path,pattern,replacement in [
        (pyproject_file,r'version\s*=\s*["\'].*?["\']',f'version = "{version}"'),
        (setup_file,r'version\s*=\s*["\'].*?["\']',f'version="{version}"')
    ]:
        if not os.path.exists(file_path): continue
        with open(file_path,"r",encoding="utf-8") as f:
            content=f.read()
        content=re.sub(pattern,replacement,content)
        with open(file_path,"w",encoding="utf-8") as f:
            f.write(content)
    print(f"Synchronized version to {version}")
def build_with_cx_freeze():
    print("Running cx_Freeze build...")
    subprocess.check_call([PYTHON_EXE,"setup_freeze.py","build"])
    lib_folder=os.path.join("PST_standalone","Assets","palworld_save_tools","lib")
    if os.path.exists(lib_folder):
        print(f"Removing {lib_folder}...")
        shutil.rmtree(lib_folder)
def clean_build_artifacts(full_clean=False):
    items=["build","PalworldSaveTools.egg-info","PST_standalone"]
    if full_clean:
        items.append(VENV_DIR)
    for item in items:
        if os.path.exists(item):
            print(f"Removing {item}...")
            if os.path.isdir(item): shutil.rmtree(item,ignore_errors=True)
            else: os.remove(item)
    for root,dirs,files in os.walk(".",topdown=False):
        for d in dirs:
            if d=="__pycache__":
                path=os.path.join(root,d)
                shutil.rmtree(path,ignore_errors=True)
def run_upx_on_build():
    build_dir="PST_standalone"
    if not os.path.exists(build_dir) or shutil.which("upx") is None: return
    targets=[]
    skip_names=("vcruntime","msvcp","python3.dll")
    for root,dirs,files in os.walk(build_dir):
        for f in files:
            lf=f.lower()
            if not (lf.endswith(".exe") or lf.endswith(".dll")): continue
            if any(k in lf for k in skip_names): continue
            targets.append(os.path.join(root,f))
    if not targets: return
    targets.sort(key=lambda x: 0 if x.lower().endswith(".exe") else 1)
    print("Running UPX compression...")
    cmd=["upx","--best","--lzma","--no-progress"]+targets
    subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
def get_app_version():
    common_file=os.path.join("Assets","common.py")
    if not os.path.exists(common_file): return "unknown"
    with open(common_file,"r",encoding="utf-8") as f:
        for line in f:
            if line.strip().startswith("APP_VERSION"):
                return line.split("=")[1].strip().strip('"').strip("'")
    return "unknown"
def create_release_archive():
    version=get_app_version()
    build_dir="PST_standalone"
    if not os.path.exists(build_dir): return
    archive_name=f"PST_standalone_v{version}.7z"
    if os.path.exists(archive_name): os.remove(archive_name)
    print(f"Creating 7z archive: {archive_name}...")
    old=os.getcwd()
    os.chdir(build_dir)
    items=os.listdir(".")
    cmd=["7z","a","-t7z","-m0=lzma2","-mx=9","-mfb=273","-md=256m","-ms=on",os.path.join("..",archive_name)]+items
    subprocess.check_call(cmd)
    os.chdir(old)
def main():
    print("="*40)
    print("STARTING CLEAN AUTOMATED BUILD")
    clean_build_artifacts(full_clean=True)
    create_venv()
    install_deps()
    sync_version()
    build_with_cx_freeze()
    run_upx_on_build()
    create_release_archive()
    clean_build_artifacts(full_clean=False)
    print("="*40)
    print("Build Completed Successfully")
if __name__=="__main__": main()