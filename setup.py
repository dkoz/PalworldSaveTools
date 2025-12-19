#!/usr/bin/env python3
from __future__ import annotations
import os
import sys
import shutil
import subprocess
import threading
import queue
import argparse
import re
from pathlib import Path
from typing import Optional

# ---------------------------
# Config
# ---------------------------
PROJECT_DIR = Path(__file__).resolve().parent
VENV_DIR = PROJECT_DIR / "pst_venv"
USE_ANSI = True

if os.name == "nt":
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 5)
    except Exception:
        pass

def ansi(code: str) -> str:
    return code if USE_ANSI else ""

RESET = ansi("\x1b[0m")
BOLD = ansi("\x1b[1m")
GREEN = ansi("\x1b[32m")
YELLOW = ansi("\x1b[33m")
RED = ansi("\x1b[31m")
CYAN = ansi("\x1b[36m")
DIM = ansi("\x1b[2m")

def step_label(n: int, total: int, text: str) -> str:
    return f"[{n}/{total}] {text}"

def print_step_working(label: str):
    sys.stdout.write(f"{BOLD}{label}...{RESET}\r")
    sys.stdout.flush()

def print_ok(label: str):
    sys.stdout.write("\r" + " " * 120 + "\r")
    print(f"{BOLD}{label} {GREEN}OK{RESET}")

def print_fail(label: str):
    sys.stdout.write("\r" + " " * 120 + "\r")
    print(f"{BOLD}{label} {RED}FAILED{RESET}")

def print_info(label: str):
    print(f"{BOLD}{label}{RESET}")

def print_small(msg: str):
    print(f"{DIM}{msg}{RESET}")

# ---------------------------
# Subprocess streaming helper
# ---------------------------
def reader_thread(proc: subprocess.Popen, q: queue.Queue):
    assert proc.stdout is not None
    try:
        for raw in proc.stdout:
            q.put(raw.rstrip("\n"))
    except Exception:
        pass
    finally:
        try:
            proc.stdout.close()
        except Exception:
            pass
        q.put(None)

def progress_bar(pct: int, width: int = 30) -> str:
    filled = int((pct / 100.0) * width)
    empty = width - filled
    return "[" + "#" * filled + "-" * empty + "]"

def run_and_watch(cmd, cwd=None, env=None, filter_keys=None, update_callback=None, info_logs=False):
    if filter_keys is None:
        filter_keys = ("Collecting", "Downloading", "%", "Building wheel for",
                       "Installing collected packages", "Successfully installed", "ERROR", "Failed", "Cloning")

    cmd_list = list(map(str, cmd))
    if info_logs:
        print_info(f"Running: {' '.join(cmd_list)}")
        if cwd:
            print_small(f" cwd: {cwd}")
        if env:
            try:
                shown = {k: env[k] for k in ("PATH", "VIRTUAL_ENV", "PYTHONPATH") if k in env}
                print_small(f" env (subset): {shown}")
            except Exception:
                pass

    proc = subprocess.Popen(
        cmd_list,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        cwd=cwd,
        env=env,
    )
    q: queue.Queue = queue.Queue()
    t = threading.Thread(target=reader_thread, args=(proc, q), daemon=True)
    t.start()

    progress_pct = None
    last_shown_msg = None

    try:
        while True:
            try:
                line = q.get(timeout=0.08)
            except queue.Empty:
                line = None
            if line is None:
                if proc.poll() is not None and q.empty():
                    break
                continue
            s = line.rstrip()
            m = re.search(r"(\d{1,3})\s*%+", s)
            pct = int(m.group(1)) if m else None
            if pct is not None:
                progress_pct = max(0, min(100, pct))

            if info_logs:
                if progress_pct is not None:
                    bar = progress_bar(progress_pct, width=28)
                    sys.stdout.write(f"\r{CYAN}{bar} {progress_pct:3d}%{RESET}\n")
                    sys.stdout.flush()
                    progress_pct = None
                else:
                    print_small(f"> {s}")
                last_shown_msg = s
                continue

            show = any(key in s for key in filter_keys)
            if (show or progress_pct is not None) and s != last_shown_msg:
                if update_callback:
                    update_callback(s, progress_pct)
                else:
                    if progress_pct is not None:
                        bar = progress_bar(progress_pct, width=28)
                        sys.stdout.write(f"\r{CYAN}{bar} {progress_pct:3d}%{RESET}")
                        sys.stdout.flush()
                        if "Downloading" not in s and "Collecting" not in s:
                            progress_pct = None
                    else:
                        sys.stdout.write("\r" + " " * 120 + "\r")
                        print(f"{CYAN}> {s}{RESET}")
                last_shown_msg = s
    finally:
        if not update_callback:
            sys.stdout.write("\r" + " " * 120 + "\r")
            sys.stdout.flush()

    rc = proc.wait()
    if info_logs:
        print_small(f"Command exit code: {rc}")
    return rc

# ---------------------------
# Python discovery + validation
# ---------------------------
def _probe_python_command(cmd_list, timeout: float = 3.0) -> Optional[dict]:
    """
    Try to run the candidate python command (list form) with:
      -c "import sys, json; print(json.dumps([sys.executable, sys.version]))"
    and parse results. Returns dict {'exe': path, 'version': version_str} on success,
    otherwise None.
    """
    try:
        probe_cmd = list(map(str, cmd_list)) + ["-c", "import sys, json; print(json.dumps([sys.executable, sys.version]))"]
        # capture output, short timeout (avoid hang)
        res = subprocess.run(probe_cmd, capture_output=True, text=True, timeout=timeout, check=False)
    except Exception:
        return None
    if res.returncode != 0:
        return None
    out = (res.stdout or "").strip()
    # expecting a JSON array like ["C:\\...\\python.exe", "3.x.y ..."]
    try:
        import json
        arr = json.loads(out.splitlines()[-1])
        exe_path, version_full = arr[0], arr[1]
        # ensure it's python 3.8+
        ver_match = re.match(r"\s*([0-9]+)\.([0-9]+)\.", version_full)
        if ver_match and int(ver_match.group(1)) >= 3 and int(ver_match.group(2)) >= 8:
            return {"exe": exe_path, "version": version_full.strip()}
    except Exception:
        return None
    return None

def find_system_python(info_logs: bool = False) -> str:
    """
    Robust search for a usable Python executable that can create venvs.
    Preference order:
      1. sys.executable (if valid Python 3)
      2. 'python3' from PATH
      3. 'python' from PATH
      4. 'py -3' launcher on Windows (if present)
    The function probes each candidate and accepts the first that runs successfully and reports a 3.x interpreter.
    """
    candidates = []

    # prefer current interpreter if it's a real python 3
    candidates.append([sys.executable])

    # check common names on PATH
    for name in ("python3", "python"):
        p = shutil.which(name)
        if p:
            candidates.append([p])

    # on Windows, also try the py launcher with -3
    if os.name == "nt":
        if shutil.which("py"):
            candidates.append(["py", "-3"])

    # de-duplicate while preserving order
    seen = set()
    uniq_candidates = []
    for c in candidates:
        key = tuple(c)
        if key not in seen:
            seen.add(key)
            uniq_candidates.append(c)

    if info_logs:
        print_info("Probing Python candidates (this avoids using the WindowsApps store stub)...")
        for c in uniq_candidates:
            print_small(f" candidate: {' '.join(map(str,c))}")

    for cand in uniq_candidates:
        probe = _probe_python_command(cand, timeout=3.0)
        if probe:
            exe = probe["exe"]
            version = probe["version"]
            if info_logs:
                print_small(f"Accepting candidate {' '.join(cand)} -> exe={exe!r}, version={version!r}")
            return exe

        if info_logs:
            # explain quickly why candidate failed
            try:
                display = shutil.which(cand[0]) or cand[0]
            except Exception:
                display = cand[0]
            print_small(f"Candidate {display!s} is not usable (probe failed).")

    # last resort: return sys.executable even if probe failed (so caller can still try)
    if info_logs:
        print_small("No usable candidate found via probing; falling back to sys.executable")
    return sys.executable

# ---------------------------
# Helpers for venv & packages
# ---------------------------
def venv_python_path() -> Path:
    if os.name == "nt":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"

def check_package_installed(venv_py: Path, package_name: str, info_logs: bool = False) -> bool:
    try:
        cmd = [str(venv_py), "-m", "pip", "show", package_name]
        if info_logs:
            print_info(f"Checking installed package: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if info_logs:
            print_small("=== pip show stdout ===")
            for line in (result.stdout or "").splitlines():
                print_small(line)
            print_small("=== pip show stderr ===")
            for line in (result.stderr or "").splitlines():
                print_small(line)
            print_small(f"pip show exit code: {result.returncode}")
        return result.returncode == 0
    except FileNotFoundError:
        if info_logs:
            print_small("venv python not found while checking installed packages")
        return False

# ---------------------------
# Steps
# ---------------------------
def create_venv(info_logs: bool = False) -> bool:
    print_step_working(step_label(1, 4, "Initializing Virtual Environment"))
    if VENV_DIR.exists():
        print_small(f"Venv exists: {VENV_DIR}")
        print_ok(step_label(1, 4, "Virtual environment already exists"))
        return True

    creator = find_system_python(info_logs=info_logs)
    if info_logs:
        print_small(f"Creating venv with: {creator}")
        print_small(f"Target venv dir: {VENV_DIR}")

    rc = run_and_watch([creator, "-m", "venv", str(VENV_DIR)], info_logs=info_logs)
    if rc != 0:
        print_fail(step_label(1, 4, "Venv creation"))
        return False
    print_ok(step_label(1, 4, "Venv created"))
    return True

def ensure_packaging_tools(venv_py: Path, info_logs: bool = False):
    print_step_working(step_label(2, 4, "Upgrading pip / setuptools / wheel"))
    run_and_watch([str(venv_py), "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"],
                  filter_keys=("Installing collected packages", "Successfully installed", "ERROR", "Failed", "%"),
                  info_logs=info_logs)
    print_ok(step_label(2, 4, "Pip / tools upgraded"))

def install_required_packages(venv_py: Path, info_logs: bool = False) -> bool:
    print_step_working(step_label(3, 4, "Installing required packages"))

    pkgs = ["pyside6", "shiboken6", "packaging"]
    installed = []
    for p in pkgs:
        if check_package_installed(venv_py, p, info_logs=info_logs):
            installed.append(p)
    if installed:
        print_small(f"Already installed: {', '.join(installed)}")
    to_install = [p for p in pkgs if p not in installed]
    if not to_install:
        print_ok(step_label(3, 4, "PySide6 & Shiboken6 present"))
        return True

    cmd = [str(venv_py), "-m", "pip", "install"] + to_install
    rc = run_and_watch(cmd, filter_keys=("Installing collected packages", "Successfully installed", "ERROR", "Failed", "%"),
                       info_logs=info_logs)
    if rc == 0:
        print_ok(step_label(3, 4, "PySide6 & Shiboken6 installed"))
        return True
    else:
        print_fail(step_label(3, 4, "Installing PySide6 & Shiboken6"))
        return False

# ---------------------------
# Main
# ---------------------------
def main():
    parser = argparse.ArgumentParser(description="Setup script (installs only pyside6 + shiboken6).")
    parser.add_argument('--infologs', action='store_true', help='Show full subprocess output and extra diagnostics')
    args = parser.parse_args()
    info_logs = args.infologs

    print()
    print(f"{BOLD}##################################{RESET}")
    print(f"{BOLD}#   Palworld Save Tools Setup    #{RESET}")
    print(f"{BOLD}##################################{RESET}")
    print()

    if info_logs:
        try:
            print_info("Environment diagnostics (infologs enabled):")
            print_small(f"  Platform: {sys.platform} / os.name={os.name}")
            print_small(f"  Python running this script: {sys.executable}")
            print_small(f"  Python version: {sys.version.replace(os.linesep, ' ')}")
            print_small(f"  Project dir: {PROJECT_DIR}")
            print_small(f"  Venv dir: {VENV_DIR}")
            print_small(f"  PATH entries: {len(os.environ.get('PATH', '').split(os.pathsep))}")
        except Exception:
            pass

    ok = create_venv(info_logs=info_logs)
    if not ok:
        sys.exit(1)

    venv_py = venv_python_path()
    if info_logs:
        print_small(f"Computed venv python path: {venv_py}")
        print_small(f"Exists: {venv_py.exists()}")

    if not venv_py.exists():
        creator = find_system_python(info_logs=info_logs)
        if info_logs:
            print_small("venv python not found after creation — attempting recreate with explicit creator")
            print_small(f"Attempting creator: {creator}")
        rc = run_and_watch([creator, "-m", "venv", str(VENV_DIR)], info_logs=info_logs)
        if rc != 0:
            print_fail("Failed to create venv with system python")
            sys.exit(2)

    ensure_packaging_tools(venv_py, info_logs=info_logs)

    ok = install_required_packages(venv_py, info_logs=info_logs)
    if not ok:
        print_small("Dependency installation failed; re-run the script to retry.")
        sys.exit(3)

    start_py = PROJECT_DIR / "start.py"
    if start_py.exists():
        print_info("Launching start.py...")
        rc = subprocess.call([str(venv_py), str(start_py)])
        sys.exit(rc)
    else:
        print_small(f"No start.py found at {start_py}; setup finished.")
        sys.exit(0)

if __name__ == "__main__":
    main()
