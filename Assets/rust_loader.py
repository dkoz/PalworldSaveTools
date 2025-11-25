from import_libs import *
def rust_parse_save(path_to_sav):
    with open(path_to_sav,"rb") as f:
        data=f.read()
    raw_gvas,_=decompress_sav_to_gvas(data)
    if raw_gvas is None or len(raw_gvas)<32:
        raise ValueError("Corrupted save: decompressed data too small")
    with tempfile.TemporaryDirectory() as tmp:
        gvas_path=os.path.join(tmp,"decompressed.gvas")
        with open(gvas_path,"wb") as g:
            g.write(raw_gvas)
        out_json=os.path.join(tmp,"save.json")
        base=os.path.dirname(os.path.abspath(__file__))
        exe=os.path.join(base,"uesave.exe")
        print("Using exe:",exe)
        cmd=[exe,"to-json","--input",gvas_path,"--output",out_json]
        r=subprocess.run(cmd,capture_output=True,text=True)
        if r.returncode!=0:
            print("STDERR:",r.stderr)
            print("STDOUT:",r.stdout)
            raise ValueError("Rust parser failed")
        with open(out_json,"r",encoding="utf-8") as f:
            return json.load(f)