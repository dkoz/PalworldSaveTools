import os, sys, subprocess, shutil, re
VENV_DIR = "pst_venv"
PYTHON_EXE = os.path.join(VENV_DIR, "Scripts", "python.exe") if os.name == "nt" else os.path.join(VENV_DIR, "bin", "python")
def create_venv():
    if not os.path.exists(VENV_DIR):
        print("Creating virtual environment...")
        subprocess.check_call([sys.executable, "-m", "pst_venv", VENV_DIR])
    else:
        print("Virtual environment already exists.")
def install_deps():
    print("Installing dependencies in venv...")
    subprocess.check_call([PYTHON_EXE, "-m", "pip", "install", "--upgrade", "pip"])
    subprocess.check_call([PYTHON_EXE, "-m", "pip", "install", "-e", "."])
    subprocess.check_call([PYTHON_EXE, "-m", "pip", "install", "cx_Freeze"])
def sync_version():
    common_file = os.path.join("Assets", "common.py")
    pyproject_file = "pyproject.toml"
    setup_file = "setup_freeze.py"
    with open(common_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip().startswith("APP_VERSION"):
                version = line.split("=")[1].strip().strip('"').strip("'")
                break
        else:
            print("APP_VERSION not found in common.py")
            return
    for file_path, pattern, replacement in [
        (pyproject_file, r'version\s*=\s*["\'].*?["\']', f'version = "{version}"'),
        (setup_file, r'version\s*=\s*["\'].*?["\']', f'version="{version}"')
    ]:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        content = re.sub(pattern, replacement, content)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
    print(f"Synchronized version to {version} in pyproject.toml and setup_freeze.py")
def build_with_cx_freeze():
    print("Running cx_Freeze build...")
    subprocess.check_call([PYTHON_EXE, "setup_freeze.py", "build"])
    lib_folder = os.path.join("PST_standalone", "Assets", "palworld_save_tools", "lib")
    if os.path.exists(lib_folder):
        print(f"Removing {lib_folder}...")
        shutil.rmtree(lib_folder)
def clean_build_artifacts():
    for item in ["build","PalworldSaveTools.egg-info","Backups","PST_standalone","Scan Save Logger","psp_windows","ppe_windows","updated_worldmap.png","PalDefender","XGP_converted_saves"]:
        if os.path.exists(item):
            print(f"Removing {item}...")
            if os.path.isdir(item):
                shutil.rmtree(item,ignore_errors=True)
            else:
                os.remove(item)
    for root,dirs,files in os.walk(".",topdown=False):
        for d in dirs:
            if d=="__pycache__":
                path=os.path.join(root,d)
                print(f"Removing {path}...")
                shutil.rmtree(path,ignore_errors=True)
def run_upx_on_build():
    build_dir="PST_standalone"
    if not os.path.exists(build_dir):
        print("Build folder not found, skipping UPX compression...")
        return
    if shutil.which("upx") is None:
        print("UPX not found on PATH, skipping UPX compression...")
        return
    targets=[]
    skip_names=("vcruntime","msvcp","python3.dll")
    for root,dirs,files in os.walk(build_dir):
        for f in files:
            lf=f.lower()
            if not (lf.endswith(".exe") or lf.endswith(".dll")):
                continue
            if any(k in lf for k in skip_names):
                continue
            targets.append(os.path.join(root,f))
    if not targets:
        print("No EXE/DLL files found for UPX compression...")
        return
    targets.sort(key=lambda x: 0 if x.lower().endswith(".exe") else 1)
    print("Running UPX compression on built binaries...")
    cmd=["upx","--best","--lzma","--no-progress"]+targets
    result=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    print("\n".join([l for l in result.stdout.splitlines() if l.strip()]))
    if result.stderr:
        print("UPX completed with some warnings (expected):")
        print(result.stderr)
def get_app_version():
    common_file=os.path.join("Assets","common.py")
    with open(common_file,"r",encoding="utf-8") as f:
        for line in f:
            if line.strip().startswith("APP_VERSION"):
                return line.split("=")[1].strip().strip('"').strip("'")
    return "unknown"
def create_release_archive():
    version=get_app_version()
    build_dir="PST_standalone"
    if not os.path.exists(build_dir):
        print("Build folder not found, skipping archive...")
        return
    archive_name=f"PST_standalone_v{version}.7z"
    if os.path.exists(archive_name):
        os.remove(archive_name)
    print(f"Creating 7z Ultra archive: {archive_name}...")
    old=os.getcwd()
    os.chdir(build_dir)
    items=os.listdir(".")
    cmd=["7z","a","-t7z","-m0=lzma2","-mx=9","-mfb=273","-md=256m","-ms=on",os.path.join("..",archive_name)]+items
    subprocess.check_call(cmd)
    os.chdir(old)
    print("7z archive created:",archive_name)
def main():
    print("="*40)
    print("PalworldSaveTools Directory Cleaner")
    print("="*40)
    clean_build_artifacts()
    print("="*40)
    print("PalworldSaveTools VENV Builder")
    print("="*40)
    create_venv()
    print("="*40)
    print("PalworldSaveTools VENV Deps")
    print("="*40)
    install_deps()
    print("="*40)
    print("Syncing Version Across Files")
    print("="*40)
    sync_version()
    print("="*40)
    print("PalworldSaveTools Exe Builder")
    print("="*40)
    build_with_cx_freeze()
    print("="*40)
    print("PalworldSaveTools UPX Compressor")
    print("="*40)
    run_upx_on_build()
    print("="*40)
    print("PalworldSaveTools Release Archiver")
    print("="*40)
    create_release_archive()
    print("="*40)
    print("PalworldSaveTools Directory Cleaner")
    print("="*40)
    clean_build_artifacts()
    print("="*40)
    print("PalworldSaveTools Exe Builder Completed")
    print("="*40)
if __name__=="__main__": main()