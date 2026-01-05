import os 
import json 
import sys 
import subprocess 
import tempfile 
import shutil 
sys .stdout .reconfigure (encoding ='utf-8')
def create_temp_venv ():
    script_dir =os .path .dirname (os .path .abspath (__file__ ))
    temp_dir =os .path .join (script_dir ,"temp_translate_env")
    venv_path =os .path .join (temp_dir ,"venv")
    if os .path .exists (temp_dir ):
        shutil .rmtree (temp_dir ,ignore_errors =True )
    try :
        subprocess .check_call ([sys .executable ,"-m","venv",venv_path ])
        return temp_dir ,venv_path 
    except :
        return None ,None 
def install_packages_in_venv (venv_path ,packages ):
    python_exe =os .path .join (venv_path ,"Scripts","python.exe")if sys .platform =="win32"else os .path .join (venv_path ,"bin","python")
    try :
        subprocess .check_call ([python_exe ,"-m","pip","install"]+packages )
        return python_exe 
    except :
        return None 
def run_translation_in_venv (python_exe ,missing_translations ):
    try :
        script_content =f'''
import os
import json
import sys
from concurrent.futures import ProcessPoolExecutor
sys.stdout.reconfigure(encoding='utf-8')
project_dir = r"{os .path .dirname (__file__ )}"
def init_worker():
    import argostranslate.translate
def translate_single(args):
    text, from_code, to_code = args
    import argostranslate.translate
    try: return argostranslate.translate.translate(text, from_code, to_code)
    except: return text
def translate_missing(missing_translations):
    try:
        import argostranslate.package
        import argostranslate.translate
        from tqdm import tqdm
    except ImportError:
        return False
    LANG_MAP = {{'de_DE': 'de', 'es_ES': 'es', 'fr_FR': 'fr', 'ja_JP': 'ja', 'ko_KR': 'ko', 'ru_RU': 'ru', 'zh_CN': 'zh'}}
    argostranslate.package.update_package_index()
    available_packages = argostranslate.package.get_available_packages()
    installed_packages = argostranslate.package.get_installed_packages()
    i18n_dir = os.path.join(project_dir, 'Assets', 'resources', 'i18n')
    for lang_code, translations in missing_translations.items():
        argos_code = LANG_MAP[lang_code]
        if not any(p.from_code == 'en' and p.to_code == argos_code for p in installed_packages):
            pkg = next((p for p in available_packages if p.from_code == 'en' and p.to_code == argos_code), None)
            if pkg: argostranslate.package.install_from_path(pkg.download())
        lang_file = os.path.join(i18n_dir, f"{{lang_code}}.json")
        try:
            with open(lang_file, 'r', encoding='utf-8') as f: data = json.load(f)
        except: data = {{}}
        keys = list(translations.keys())
        tasks = [(translations[k], 'en', argos_code) for k in keys]
        results = []
        print(f"\\n🚀 Translating {{lang_code}} ({{len(keys)}} items):")
        with ProcessPoolExecutor(initializer=init_worker) as executor:
            for res in tqdm(executor.map(translate_single, tasks), total=len(tasks), unit="str"):
                results.append(res)
        for i, key in enumerate(keys):
            data[key] = results[i]
        sorted_data = dict(sorted(data.items()))
        with open(lang_file, 'w', encoding='utf-8') as f:
            json.dump(sorted_data, f, indent=2, ensure_ascii=False)
    return True
if __name__ == "__main__":
    if translate_missing({missing_translations !r }):
        print("TRANSLATION_SUCCESS")
'''
        with tempfile .NamedTemporaryFile (mode ='w',suffix ='.py',delete =False ,encoding ='utf-8')as f :
            f .write (script_content )
            temp_script =f .name 
        try :
            env =os .environ .copy ()
            env ["PYTHONIOENCODING"]="utf-8"
            subprocess .run ([python_exe ,temp_script ],cwd =os .path .dirname (__file__ ),env =env )
            return True 
        finally :
            try :os .unlink (temp_script )
            except :pass 
    except Exception as e :
        print (f"✗ Error: {e }")
        return False 
def sort_all_jsons ():
    i18n_dir =os .path .join (os .path .dirname (__file__ ),'Assets','resources','i18n')
    print ("\n🧹 Final cleanup: Sorting all language files...")
    for filename in os .listdir (i18n_dir ):
        if filename .endswith (".json"):
            file_path =os .path .join (i18n_dir ,filename )
            try :
                with open (file_path ,'r',encoding ='utf-8')as f :
                    data =json .load (f )
                sorted_data =dict (sorted (data .items ()))
                with open (file_path ,'w',encoding ='utf-8')as f :
                    json .dump (sorted_data ,f ,indent =2 ,ensure_ascii =False )
                print (f"  ✓ Sorted {filename }")
            except :
                print (f"  ✗ Failed to sort {filename }")
def scan_missing_translations ():
    i18n_dir =os .path .join (os .path .dirname (__file__ ),'Assets','resources','i18n')
    with open (os .path .join (i18n_dir ,'en_US.json'),'r',encoding ='utf-8')as f :en_data =json .load (f )
    missing_translations ={}
    for lang in ['de_DE','es_ES','fr_FR','ja_JP','ko_KR','ru_RU','zh_CN']:
        try :
            with open (os .path .join (i18n_dir ,f"{lang }.json"),'r',encoding ='utf-8')as f :l_data =json .load (f )
        except :l_data ={}
        m ={k :v for k ,v in en_data .items ()if k not in l_data }
        if m :missing_translations [lang ]=m 
    return missing_translations 
def main ():
    print ("🌐 Palworld Save Tools - Multi-Core Translation & Cleanup")
    missing =scan_missing_translations ()
    if not missing :
        print ("✓ Everything translated!")
        sort_all_jsons ()
        return 
    temp_dir ,venv_path =create_temp_venv ()
    if temp_dir :
        try :
            print ("📦 Setting up environment (argostranslate, tqdm)...")
            py_exe =install_packages_in_venv (venv_path ,['argostranslate','tqdm'])
            if py_exe :
                run_translation_in_venv (py_exe ,missing )
                sort_all_jsons ()
                print ("\n✅ All translations synced and sorted!")
        finally :shutil .rmtree (temp_dir ,ignore_errors =True )
if __name__ =="__main__":
    main ()