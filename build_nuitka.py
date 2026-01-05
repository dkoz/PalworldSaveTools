#!/usr/bin/env python3
"""
PalworldSaveTools - Nuitka Build Script
Compiles the application into a single standalone executable with all resources embedded.

Based on setup_freeze.py configuration for cx_Freeze compatibility.

Usage:
    python build_nuitka.py [--debug] [--clean-only]

Options:
    --debug      Enable debug mode (console visible, verbose output)
    --clean-only Only clean build artifacts without building
    --no-archive Skip creating distribution archive
"""

import os
import sys
import shutil
import subprocess
import argparse
from pathlib import Path

# =============================================================================
# Configuration
# =============================================================================

# Project paths
PROJECT_ROOT = Path(__file__).parent.resolve()
ASSETS_DIR = PROJECT_ROOT / "Assets"
MAIN_SCRIPT = ASSETS_DIR / "palworld_aio" / "main.py"
ICON_PATH = ASSETS_DIR / "resources" / "pal.ico"
BUILD_DIR = PROJECT_ROOT / "PST_build"  # Temporary build directory
OUTPUT_NAME = "PalworldSaveTools"
FINAL_EXE = PROJECT_ROOT / f"{OUTPUT_NAME}.exe"  # Final exe location in root

# Get version from common.py (same as setup_freeze.py)
def get_version():
    """Extract version from Assets/common.py"""
    common_file = ASSETS_DIR / "common.py"
    if common_file.exists():
        with open(common_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip().startswith("APP_VERSION"):
                    # Extract version string
                    version = line.split("=")[1].strip().strip('"\'')
                    return version
    # Fallback to pyproject.toml version
    return "1.1.48"

VERSION = get_version()

# Directories/files to clean before build
CLEAN_TARGETS = [
    "PST_build",
    "main.build",
    "main.dist",
    "main.onefile-build",
    "*.build",
    "*.dist",
    "*.onefile-build",
    "__pycache__",
]

# =============================================================================
# Data Files to Include (matching setup_freeze.py include_files)
# =============================================================================

# Format: (source_path, destination_in_package)
DATA_INCLUDES = [
    # Main Assets directory (entire directory like setup_freeze.py)
    ("Assets/", "Assets/"),
    
    # Documentation and license
    ("readme.md", "readme.md"),
    ("license", "license"),
]

# =============================================================================
# Python Packages to Include (matching setup_freeze.py packages list)
# =============================================================================

# Packages that need explicit inclusion (non-standard, from setup_freeze.py)
INCLUDE_PACKAGES = [
    # i18n (local, handled via data inclusion)
    # Multimedia
    "pygame",

    # Logging
    "loguru",

    # Data Processing
    "matplotlib",
    "pandas",

    # GUI - Tkinter
    "customtkinter",

    # Utilities
    "cityhash",

    # Image Processing
    "PIL",

    # Numerical
    "numpy",

    # Oodle Compression (critical for save files)
    "ooz",

    # Font handling
    "fontTools",

    # Qt/PySide6 GUI
    "PySide6.QtCore",
    "PySide6.QtGui",
    "PySide6.QtWidgets",
    "PySide6.QtSvg",
    "PySide6.QtSvgWidgets",

    # Nerd fonts
    "nerdfont",

    # Testing
    "unittest",
    "unittest.mock",
]

# Packages to explicitly exclude (matching setup_freeze.py excludes)
EXCLUDE_PACKAGES = [
    "test",
    "pdb",
    "tkinter.test",
    "lib2to3",
    "distutils",
    "setuptools",
    "pip",
    "wheel",
    "venv",
    "ensurepip",
    "msgpack",
    # Additional exclusions to reduce size
    "pytest",
    "doctest",
    "profile",
    "pstats",
    "cProfile",
    "timeit",
    "trace",
    "idlelib",
    # Anti-bloat exclusions (previously handled by anti-bloat plugin)
    "pydoc",  # Main conflict source with pyside6
    "pydoc_data",
    "turtle",
    "turtledemo",
    "xmlrpc",
    "http",
    "urllib",
    "email",
    "json.tool",
    "ctypes",
    "multiprocessing",
    "concurrent",
    "asyncio",
    "ssl",
    "hashlib",
    "hmac",
    "socketserver",
    "http.server",
    "http.cookiejar",
    "http.cookies",
    "html",
    "html.parser",
    "html.entities",
    "cgi",
    "cgitb",
    "wsgiref",
]

# =============================================================================
# Nuitka Plugins
# =============================================================================

NUITKA_PLUGINS = [
    "pyside6",
    "tk-inter",
    # Removed "anti-bloat" due to plugin conflict with pyside6
    # The anti-bloat functionality will be handled through explicit exclusions
]

# =============================================================================
# Helper Functions for Finding Assets (matching setup_freeze.py)
# =============================================================================

def find_customtkinter_assets():
    """Find customtkinter assets directory (from setup_freeze.py)"""
    try:
        import customtkinter
        p = os.path.dirname(customtkinter.__file__)
        a = os.path.join(p, "assets")
        if os.path.exists(a):
            return (a, "lib/customtkinter/assets")
    except Exception:
        pass
    return None

def find_ooz_library():
    """Find ooz library directory (from setup_freeze.py)"""
    try:
        import ooz
        return (os.path.dirname(ooz.__file__), "lib/ooz")
    except Exception:
        pass
    return None

def find_pyside6_plugins():
    """Find PySide6 plugins directory (from setup_freeze.py)"""
    try:
        import PySide6
        p = os.path.dirname(PySide6.__file__)
        a = os.path.join(p, "plugins")
        if os.path.exists(a):
            return (a, "lib/PySide6/plugins")
    except Exception:
        pass
    return None

# =============================================================================
# Build Functions
# =============================================================================

def clean_build_artifacts():
    """Remove previous build artifacts"""
    print("\n" + "=" * 60)
    print("Cleaning build artifacts...")
    print("=" * 60)
    
    for pattern in CLEAN_TARGETS:
        if "*" in pattern:
            # Glob pattern
            for path in PROJECT_ROOT.glob(pattern):
                remove_path(path)
            for path in PROJECT_ROOT.glob(f"**/{pattern}"):
                remove_path(path)
        else:
            path = PROJECT_ROOT / pattern
            remove_path(path)
    
    print("Clean complete!")

def remove_path(path):
    """Remove a file or directory"""
    if path.exists():
        try:
            if path.is_dir():
                shutil.rmtree(path)
                print(f"  Removed directory: {path}")
            else:
                path.unlink()
                print(f"  Removed file: {path}")
        except Exception as e:
            print(f"  Warning: Could not remove {path}: {e}")

def check_nuitka_installed():
    """Check if Nuitka is installed, install if not"""
    print("\n" + "=" * 60)
    print("Checking Nuitka installation...")
    print("=" * 60)

    try:
        import nuitka
        # Try to get version from importlib.metadata
        try:
            from importlib.metadata import version
            nuitka_version = version("nuitka")
            print(f"  Nuitka version: {nuitka_version}")
        except Exception:
            print("  Nuitka found (version unknown)")
        return True
    except ImportError:
        print("  Nuitka not found. Installing...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install",
            "nuitka", "ordered-set", "zstandard"
        ])
        print("  Nuitka installed successfully!")
        return True

def check_dependencies():
    """Verify all required dependencies are available"""
    print("\n" + "=" * 60)
    print("Checking dependencies...")
    print("=" * 60)
    
    # Core dependencies from pyproject.toml
    deps = [
        ("loguru", "loguru"),
        ("matplotlib", "matplotlib"),
        ("pandas", "pandas"),
        ("customtkinter", "customtkinter"),
        ("cityhash", "cityhash"),
        ("PIL", "pillow"),
        ("numpy", "numpy"),
        ("pygame", "pygame"),
        ("PySide6", "pyside6-essentials"),
        ("ooz", "pyooz"),
        ("nerdfont", "nerdfont"),
    ]
    
    missing = []
    for import_name, pkg_name in deps:
        try:
            __import__(import_name)
            print(f"  ✓ {pkg_name}")
        except ImportError:
            print(f"  ✗ {pkg_name} - MISSING")
            missing.append(pkg_name)
    
    if missing:
        print(f"\nWarning: Missing packages: {', '.join(missing)}")
        print("Install them with: pip install -r req.txt")
        return False
    
    return True

def build_nuitka_command(debug=False, no_console=False):
    """Build the Nuitka command line arguments"""
    cmd = [
        sys.executable,
        "-m", "nuitka",

        # Output settings
        "--onefile",
        f"--output-dir={BUILD_DIR}",
        f"--output-filename={OUTPUT_NAME}.exe",

        # Windows metadata
        f"--windows-icon-from-ico={ICON_PATH}",
        f"--windows-product-name=PalworldSaveTools",
        f"--windows-product-version={VERSION}",
        f"--windows-file-version={VERSION}",
        "--windows-company-name=Pylar",
        "--windows-file-description=All-in-one tool for fixing/transferring/editing Palworld saves",

    # Compilation settings
    "--standalone",
    "--follow-imports",
    "--assume-yes-for-downloads",
    ]

    # Console mode
    if no_console:
        cmd.append("--windows-console-mode=disable")
    elif debug:
        cmd.append("--windows-console-mode=force")
    else:
        cmd.append("--windows-console-mode=attach")
    
    # Optimization settings (matching setup_freeze.py optimize=0)
    if not debug:
        cmd.extend([
            "--lto=yes",
            "--jobs=auto",
        ])
    else:
        cmd.extend([
            "--debug",
            "--no-debug-immortal-assumptions",  # Required for PySide6 compatibility
        ])
    
    # Enable plugins
    for plugin in NUITKA_PLUGINS:
        cmd.append(f"--enable-plugin={plugin}")
    
    # Include packages
    for pkg in INCLUDE_PACKAGES:
        cmd.append(f"--include-package={pkg}")
    
    # Exclude packages
    for pkg in EXCLUDE_PACKAGES:
        cmd.append(f"--nofollow-import-to={pkg}")
    
    # Include main data directories and files
    for source, dest in DATA_INCLUDES:
        source_path = PROJECT_ROOT / source
        if source_path.exists():
            if source_path.is_dir():
                cmd.append(f"--include-data-dir={source_path}={dest}")
            else:
                cmd.append(f"--include-data-files={source_path}={dest}")
    
    # Include customtkinter assets (like setup_freeze.py)
    ctk_assets = find_customtkinter_assets()
    if ctk_assets:
        src, dest = ctk_assets
        cmd.append(f"--include-data-dir={src}={dest}")
        print(f"  Including customtkinter assets: {src}")
    
    # Include ooz library (critical for save file compression)
    ooz_lib = find_ooz_library()
    if ooz_lib:
        src, dest = ooz_lib
        cmd.append(f"--include-data-dir={src}={dest}")
        print(f"  Including ooz library: {src}")

    # Include package data for specific packages
    cmd.append("--include-package-data=customtkinter")
    cmd.append("--include-package-data=PySide6")
    cmd.append("--include-package-data=matplotlib")
    cmd.append("--include-package-data=pygame")
    cmd.append("--include-package-data=nerdfont")

    # Include Qt plugins to fix QML warnings
    cmd.append("--include-qt-plugins=qml")

    # Add the main script
    cmd.append(str(MAIN_SCRIPT))

    return cmd

def run_build(debug=False, no_console=False):
    """Execute the Nuitka build"""
    print("\n" + "=" * 60)
    print(f"Building PalworldSaveTools v{VERSION} with Nuitka")
    print("=" * 60)
    print(f"  Main script: {MAIN_SCRIPT}")
    print(f"  Build dir:   {BUILD_DIR}")
    print(f"  Final exe:   {FINAL_EXE}")
    print(f"  Debug mode:  {debug}")
    print(f"  No console:  {no_console}")
    print("=" * 60 + "\n")

    # Verify main script exists
    if not MAIN_SCRIPT.exists():
        print(f"ERROR: Main script not found: {MAIN_SCRIPT}")
        return False

    # Verify icon exists
    if not ICON_PATH.exists():
        print(f"WARNING: Icon not found: {ICON_PATH}")

    # Create build directory
    BUILD_DIR.mkdir(parents=True, exist_ok=True)

    # Build command
    cmd = build_nuitka_command(debug, no_console)
    
    # Print command for debugging
    print("Nuitka command:")
    print("-" * 60)
    for i, arg in enumerate(cmd):
        if i == 0:
            print(f"  {arg} \\")
        elif i == len(cmd) - 1:
            print(f"    {arg}")
        else:
            print(f"    {arg} \\")
    print("-" * 60 + "\n")
    
    # Run Nuitka
    try:
        result = subprocess.run(cmd, cwd=PROJECT_ROOT)
        if result.returncode != 0:
            print(f"\nERROR: Nuitka build failed with code {result.returncode}")
            return False
    except KeyboardInterrupt:
        print("\nBuild cancelled by user.")
        return False
    except Exception as e:
        print(f"\nERROR: Build failed: {e}")
        return False
    
    return True

def extract_exe_to_root():
    """Move the built exe from build dir to project root"""
    print("\n" + "=" * 60)
    print("Extracting executable to project root...")
    print("=" * 60)
    
    built_exe = BUILD_DIR / f"{OUTPUT_NAME}.exe"
    
    if not built_exe.exists():
        print(f"  ERROR: Built executable not found: {built_exe}")
        return False
    
    # Remove existing exe in root if present
    if FINAL_EXE.exists():
        print(f"  Removing existing: {FINAL_EXE}")
        FINAL_EXE.unlink()
    
    # Move exe to root
    print(f"  Moving: {built_exe}")
    print(f"      -> {FINAL_EXE}")
    shutil.move(str(built_exe), str(FINAL_EXE))
    
    print("  Executable extracted successfully!")
    return True

def post_build_cleanup():
    """Clean up all build files after successful build"""
    print("\n" + "=" * 60)
    print("Post-build cleanup...")
    print("=" * 60)
    
    # Remove the entire PST_build directory
    if BUILD_DIR.exists():
        remove_path(BUILD_DIR)
    
    # Remove any stray build directories in project root
    for pattern in ["*.build", "*.onefile-build", "*.dist"]:
        for path in PROJECT_ROOT.glob(pattern):
            remove_path(path)
    
    print("Cleanup complete!")

def create_archive():
    """Create a compressed archive of the executable"""
    print("\n" + "=" * 60)
    print("Creating distribution archive...")
    print("=" * 60)
    
    archive_name = f"PalworldSaveTools_v{VERSION}"
    
    # Check if executable exists in root
    if not FINAL_EXE.exists():
        print(f"  WARNING: Executable not found at {FINAL_EXE}")
        return
    
    # Try 7-Zip first (better compression)
    try:
        result = subprocess.run(
            ["7z", "a", "-t7z", "-mx=9", f"{archive_name}.7z", str(FINAL_EXE)],
            cwd=PROJECT_ROOT,
            capture_output=True
        )
        if result.returncode == 0:
            print(f"  Created: {archive_name}.7z")
            return
    except FileNotFoundError:
        pass
    
    # Fallback to Python's zipfile
    try:
        import zipfile
        zip_path = PROJECT_ROOT / f"{archive_name}.zip"
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.write(FINAL_EXE, FINAL_EXE.name)
        print(f"  Created: {archive_name}.zip")
    except Exception as e:
        print(f"  WARNING: Could not create archive: {e}")

def print_summary():
    """Print build summary"""
    print("\n" + "=" * 60)
    print("BUILD COMPLETE!")
    print("=" * 60)
    
    if FINAL_EXE.exists():
        size_mb = FINAL_EXE.stat().st_size / (1024 * 1024)
        print(f"  Executable: {FINAL_EXE}")
        print(f"  Size: {size_mb:.2f} MB")
        print(f"  Version: {VERSION}")
    else:
        print("  WARNING: Executable not found!")
    
    print("=" * 60)

# =============================================================================
# Main Entry Point
# =============================================================================

def main():
    """Main build script entry point"""
    parser = argparse.ArgumentParser(
        description="Build PalworldSaveTools with Nuitka"
    )
    parser.add_argument(
        "--debug", 
        action="store_true",
        help="Build in debug mode (verbose output, no optimization)"
    )
    parser.add_argument(
        "--clean-only",
        action="store_true", 
        help="Only clean build artifacts, don't build"
    )
    parser.add_argument(
        "--no-archive",
        action="store_true",
        help="Don't create distribution archive"
    )
    parser.add_argument(
        "--no-console",
        action="store_true",
        help="Hide console window (GUI-only mode)"
    )
    
    args = parser.parse_args()
    
    print("\n" + "=" * 60)
    print("  PalworldSaveTools - Nuitka Build Script")
    print(f"  Version: {VERSION}")
    print("=" * 60)
    
    # Clean previous builds
    clean_build_artifacts()
    
    if args.clean_only:
        print("\nClean-only mode. Exiting.")
        return 0
    
    # Check prerequisites
    if not check_nuitka_installed():
        return 1
    
    if not check_dependencies():
        print("\nContinuing despite missing dependencies...")
    
    # Run the build
    success = run_build(debug=args.debug, no_console=args.no_console)
    
    if success:
        # Extract exe to project root
        if not extract_exe_to_root():
            print("\nFailed to extract executable!")
            return 1
        
        # Clean up build directory
        post_build_cleanup()
        
        # Create archive
        if not args.no_archive:
            create_archive()
        
        # Print summary
        print_summary()
        return 0
    else:
        print("\nBuild failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
