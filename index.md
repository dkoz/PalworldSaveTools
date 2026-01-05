# PalworldSaveTools (PST) - Project Index

## Project Overview

PalworldSaveTools (PST) is a comprehensive tool for managing and editing Palworld game save files. It provides a graphical user interface for parsing, viewing, and modifying save data, including player information, guilds, pals, bases, and more. The tool supports transferring saves between different game modes (host/co-op to dedicated server and vice versa), fixing host save issues, and performing various cleanup and optimization operations.

**Version:** 1.1.48  
**Game Version:** 0.7.0  
**License:** MIT  
**Contact:** Pylar1991 on Discord

### Key Features

- **Fast Save Parsing:** One of the quickest available tools for reading Palworld saves
- **Player/Guild/Pal Management:** View and edit player details, guild information, and pal collections
- **Base Map Viewer:** Interactive map showing base locations and structures
- **Save Transfer:** Convert saves between host/co-op and dedicated server modes
- **Host Save Fixes:** Repair corrupted or incompatible save files
- **Steam ↔ GamePass Conversion:** Convert saves between different game platforms
- **Slot Injection:** Increase player inventory slots (compatible with Bigger PalBox mod)
- **All-in-One Tools:** Batch operations for cleaning up saves (delete players, bases, guilds, etc.)
- **Automated Backups:** Automatic backup creation before modifications

## Project Structure

### Root Directory Files

- `README.md` - Main project documentation with features, installation, and usage guides
- `pyproject.toml` - Python project configuration with dependencies and metadata
- `requirements.txt` - List of Python dependencies
- `setup_freeze.py` - cx_Freeze configuration for building standalone executable
- `build.py` - Main build script for creating distributable packages
- `build.cmd` - Windows batch file to run the build process
- `setup_pst.py` - Bootstrapper script that sets up virtual environment and dependencies
- `start.py` - Launcher script that checks dependencies and starts the GUI application
- `start_win.cmd` / `start_linux.sh` - Platform-specific startup scripts
- `clean_code.cmd` / `clean_code.py` - Code cleaning utilities
- `license` - MIT license file
- `pst_venv/` - Virtual environment directory (created automatically)
- `Assets/` - Main application code and resources
- `Assets/__init__.py` - Package initialization
- `Assets/common.py` - Shared constants and utility functions (APP_VERSION, APP_NAME, etc.)
- `Assets/import_libs.py` - Library imports and common utilities
- `Assets/loading_manager.py` - Loading screen and progress management
- `Assets/ui_theme.py` - UI theming and styling

### Assets/palworld_aio/ - Main GUI Application

- `main.py` - Application entry point, handles command-line arguments and GUI initialization
- `ui/` - User interface components
  - `main_window.py` - Main application window
  - `header_widget.py` - Application header
  - `map_tab.py` - Map visualization tab
  - `tools_tab.py` - Tools and utilities tab
  - `results_widget.py` - Results display widget
  - `menus.py` - Menu bar and context menus
  - `custom_floating_tab.py` / `custom_tab_bar.py` - Custom UI components
- `widgets/` - Custom widget components
  - `base_hover_overlay.py` - Hover effect overlays
  - `collapsible_splitter.py` - Collapsible panel splitters
  - `loading_popup.py` - Loading progress popups
  - `menu_popup.py` - Context menus
  - `search_panel.py` - Search and filter panels
  - `stats_panel.py` - Statistics display panels
  - `tree_widgets.py` - Tree view components
- `constants.py` - Application constants and configuration
- `save_manager.py` - Save file loading and management
- `data_manager.py` - Data processing and manipulation
- `func_manager.py` - Core functionality (cleanup, validation, etc.)
- `guild_manager.py` - Guild-related operations
- `player_manager.py` - Player data management
- `utils.py` - Utility functions for save processing

### Assets/palworld_save_tools/ - Core Save Processing Library

- `palsav.py` - Main save file parser
- `gvas.py` - GVAS (Godot Variant Archive System) format handling
- `json_tools.py` - JSON conversion utilities
- `paltypes.py` - Palworld data type definitions
- `archive.py` - Archive/compression handling
- `compressor/` - Compression algorithms
  - `zlib.py` - ZLIB compression
  - `oozlib.py` - Oodle compression (via pyooz)
  - `enums.py` - Compression-related enumerations
- `rawdata/` - Raw data structure definitions
  - `character.py` - Character/player data structures
  - `guild.py` - Guild data structures
  - `base_camp.py` / `base_camp_module.py` - Base camp data
  - `map_object.py` - Map object definitions
  - `item_container.py` - Inventory/item containers
  - `work.py` / `worker_director.py` - Work assignment systems
  - `foliage_model.py` - Foliage and environmental objects
  - And many more data structure files...
- `commands/` - Command-line utilities
  - `convert.py` - Save conversion tools
  - `resave_test.py` - Save integrity testing

### Assets/palworld_coord/ - Coordinate System Handling

- Coordinate conversion utilities for different game modes and platforms

### Assets/palworld_xgp_import/ - Xbox Game Pass Import Tools

- Utilities for importing saves from Xbox Game Pass version

### Assets/resources/ - Static Resources

- `pal.ico` - Application icon
- `PalworldSaveTools_*.png` - Logo variants
- `game_data/` - Game data files (items, pals, skills, etc.)
- `i18n/` - Internationalization files
  - `en_US.json`, `de_DE.json`, etc. - Language files
  - `icon/` - UI icons
- `readme/` - Localized README files
- `gui/` - GUI theme files (darkmode.qss, lightmode.qss, palmode.qss)
- `LocalData.sav` - Template save file for map unlocking

### Assets/data/ - Configuration and Data

- `configs/` - Configuration files
- `gui/` - GUI layout and theme data

## How the Project Works

### Application Startup Process

1. **Bootstrapper (setup_pst.py)**: Creates virtual environment and installs basic dependencies (pip, setuptools, wheel, numpy, PySide6)

2. **Launcher (start.py)**: 
   - Checks if all required dependencies are installed
   - Shows splash screen with progress bar
   - Installs/upgrades pip and dependencies as needed
   - Handles git-based dependencies (like pyooz)
   - Launches the main application

3. **Main Application (Assets/palworld_aio/main.py)**:
   - Initializes PySide6 GUI framework
   - Sets up logging and error handling
   - Can run in GUI mode or command-line mode (with save file path argument)
   - Loads internationalization (i18n) settings
   - Initializes main window and UI components

### Save Processing Workflow

1. **Save Loading**:
   - User selects Level.sav file and Players/ directory
   - `sav_to_json()` converts binary save to JSON format
   - `MappingCacheObject` builds internal data structures
   - Guild mappings and base lookups are created

2. **Data Analysis**:
   - Player counts and pal ownership statistics
   - Guild structure validation
   - Base and structure analysis
   - Item and pal validation

3. **Operations**:
   - Various tools modify the JSON data structure
   - Cleanup operations remove invalid data
   - Transfer operations adjust GUIDs and references

4. **Save Writing**:
   - `json_to_sav()` converts JSON back to binary format
   - Automatic backup creation
   - File integrity verification

### Key Technologies

- **Python 3.11+** - Core language
- **PySide6** - GUI framework (Qt bindings)
- **cx_Freeze** - Standalone executable creation
- **NumPy** - Numerical computations
- **Pandas** - Data manipulation
- **Matplotlib** - Chart generation
- **CustomTkinter** - Enhanced Tkinter components
- **Oodle Compression** - Game-specific compression (via pyooz)
- **CityHash** - Fast hashing algorithm

## Build Scripts Step-by-Step

### Development/Running (Normal Usage)

1. **start_win.cmd** (Windows) or **start_linux.sh** (Linux):
   - Calls `setup_pst.py` to prepare environment
   - Passes `--infologs` flag if requested for verbose logging

2. **setup_pst.py**:
   - Checks for existing virtual environment (`pst_venv/.ready`)
   - If not ready: Creates venv and installs basic dependencies
   - Creates sentinel file to mark environment as ready
   - Calls `start.py` with venv Python

3. **start.py**:
   - Loads configuration and checks GUI availability
   - Builds splash screen UI if GUI enabled
   - Starts background worker thread for dependency installation
   - Worker upgrades pip/setuptools/wheel
   - Checks all requirements from `requirements.txt`
   - Installs missing packages (handles git dependencies specially)
   - Handles PySide6-Essentials separately
   - Upon completion, launches main application

### Standalone Executable Build Process

1. **build.cmd** (Windows):
   - Calls `python build.py build`
   - Simple wrapper for the main build script

2. **build.py** (Main Build Script):
   - **Clean Environment**: Removes old build artifacts (`build/`, `PST_standalone/`, `__pycache__/`, etc.)
   - **Create Virtual Environment**: Sets up `pst_venv/` if not exists
   - **Install Dependencies**: Installs build requirements including cx_Freeze
   - **Sync Versions**: Updates version numbers in `pyproject.toml` and `setup_freeze.py` from `Assets/common.py`
   - **cx_Freeze Build**: Runs `setup_freeze.py` to create frozen executable
     - Includes all Python packages and data files
     - Embeds Assets/ directory and resources
     - Creates `PST_standalone/` directory with executable
   - **Create Archive**: Uses 7z to create compressed archive `PST_standalone_v{version}.7z`
   - **Final Clean**: Removes build artifacts again

3. **setup_freeze.py** (cx_Freeze Configuration):
   - Defines packages to include/exclude
   - Specifies data files to bundle (Assets/, readme.md, license)
   - Finds and includes customtkinter assets, PySide6 plugins, ooz library
   - Sets executable properties (icon, base, target name)
   - Outputs to `PST_standalone/PalworldSaveTools.exe`

### Code Cleaning Scripts

- **clean_code.cmd** / **clean_code.py**:
  - Removes `__pycache__` directories recursively
  - Cleans build artifacts and temporary files
  - Helps maintain clean repository state

## Dependencies Management

### Core Dependencies (requirements.txt)

- **loguru** - Advanced logging
- **matplotlib** - Plotting and visualization
- **pandas** - Data analysis
- **customtkinter** - Modern Tkinter components
- **cityhash** - Fast hashing
- **pillow** - Image processing
- **numpy** - Numerical arrays
- **pygame** - Multimedia library
- **pyside6-essentials** - Qt GUI framework
- **cx-freeze** - Executable freezing
- **nerdfont** - Icon fonts
- **pyooz** (git) - Oodle compression library

### Build-Time Dependencies (pyproject.toml)

Additional dependencies for packaging and distribution.

### Virtual Environment

- Isolated Python environment in `pst_venv/`
- Prevents conflicts with system Python
- Allows multiple versions/projects on same machine
- Automatically managed by bootstrap scripts

## Configuration and Localization

- **Config Files**: `Assets/data/configs/config.json` for application settings
- **User Config**: `Assets/data/configs/user.cfg` for user preferences (theme, etc.)
- **Themes**: Multiple GUI themes (dark, light, pal mode) in `Assets/data/gui/`
- **Languages**: Support for multiple languages via i18n system
- **Game Data**: Static game data files for item/pal/skill lookups

## Distribution

- **GitHub Releases**: Standalone `.7z` archives containing executable and all dependencies
- **Self-Contained**: No installation required, runs from any directory
- **Cross-Platform**: Windows executable, source code works on Linux/macOS
- **Version Management**: Automatic version syncing from source code

This comprehensive tool enables Palworld players and server administrators to manage their game saves effectively, with a focus on user-friendly operation and robust error handling.
