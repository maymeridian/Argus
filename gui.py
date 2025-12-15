"""
gui.py

Author: maymeridian
Description: The graphical user interface for Argus. Built with CustomTkinter, it handles
             user interaction, settings configuration, taskbar integration, and visual feedback.
             Includes logic for injecting local GPU dependencies.
"""

import os
import sys
import threading
import ctypes
import logging
from pathlib import Path
from typing import List

# ==========================================
# DLL INJECTION (GPU SUPPORT)
# ==========================================
# This block must execute before importing 'onnxruntime' or 'main'
# to ensure Windows finds the local NVIDIA DLLs.

def _inject_gpu_libraries():
    """
    Forces the local 'libraries' folder into the Windows DLL search path.
    """
    if sys.platform != "win32":
        return

    base_path = Path(__file__).resolve().parent
    libs_path = base_path / "libraries"

    if libs_path.exists():
        # 1. Force into Environment PATH (The "Aggressive" Fix)
        # This allows DLLs to find *other* DLLs in the same folder
        os.environ["PATH"] = str(libs_path) + os.pathsep + os.environ["PATH"]
        
        # 2. The Standard Python 3.8+ Fix
        try:
            os.add_dll_directory(str(libs_path))
        except Exception:
            pass
            
        print(f"✅ Injected GPU libraries from: {libs_path}")
    else:
        print(f"❌ WARNING: 'libraries' folder missing at: {libs_path}")

_inject_gpu_libraries()

# ==========================================
# IMPORTS
# ==========================================

from tkinter import filedialog, PhotoImage
import customtkinter as ctk

# Application Modules
import main
import file_manager as fm
import config

# ==========================================
# APP CONFIGURATION
# ==========================================

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class ArgusApp(ctk.CTk):
    """
    Main Application Window.
    Inherits from CustomTkinter's CTk class to provide a modern UI.
    """
    
    def __init__(self):
        # 1. WINDOWS TASKBAR ICON FIX
        # Explicit AppUserModelID allows the app to have its own icon in the taskbar
        myappid = 'propabilia.argus.sorter.2.0'
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except Exception:
            pass 

        super().__init__()

        # 2. WINDOW CONFIGURATION
        self.title("Argus")
        self.geometry("1200x900")
        self.resizable(False, False)
        
        self.base_path = fm.get_application_path()

        # 3. ICON LOADING
        ico_path = self.base_path / "icon.ico"
        png_path = self.base_path / "icon.png"

        try:
            if ico_path.exists():
                # Best for Windows Taskbar
                self.iconbitmap(str(ico_path))
            elif png_path.exists():
                # Fallback for Window decoration
                img = PhotoImage(file=str(png_path))
                self.iconphoto(True, img)
                self.after(200, lambda: self.iconphoto(True, img))
        except Exception as e:
            print(f"Warning: Could not load icon: {e}")

        # 4. STATE INITIALIZATION
        config.load()
        self.is_running = False
        self.stop_event = threading.Event()

        # 5. UI FRAME SETUP
        self.home_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.settings_frame = ctk.CTkFrame(self, fg_color="transparent")

        self.setup_home_ui()
        self.setup_settings_ui()

        # Start on Home Page
        self.show_home()

    # ==========================================
    # NAVIGATION METHODS
    # ==========================================
    
    def show_home(self) -> None:
        """Switches view to the Home/Run dashboard."""
        self.settings_frame.pack_forget()
        self.home_frame.pack(fill="both", expand=True)

    def show_settings(self) -> None:
        """Switches view to the Settings configuration panel."""
        if self.is_running: return
        self.home_frame.pack_forget()
        self.settings_frame.pack(fill="both", expand=True)

    def save_and_go_home(self) -> None:
        """Persists all settings from UI inputs to config file and returns home."""
        # 1. Update Toggles & Folder Paths
        config.APPEND_ORIGINAL_NAME = self.var_append.get()
        config.DISCARD_COA = self.var_discard_coa.get()
        config.SAVE_DEBUG_LOGS = self.var_debug_logs.get()
        config.USE_GPU = self.var_use_gpu.get()
        config.GROUP_FOLDERS = self.var_group_folders.get()
        config.OUTPUT_FOLDER = self.entry_output.get()
        
        # 2. Update Lists (Helper to parse textbox content)
        def get_list(textbox: ctk.CTkTextbox) -> List[str]:
            raw = textbox.get("1.0", "end").strip()
            return [l.strip().upper() for l in raw.split('\n') if l.strip()]

        config.STRONG_INDICATORS = get_list(self.txt_strong)
        config.WEAK_INDICATORS = get_list(self.txt_weak)
        config.FORCE_UPPERCASE = get_list(self.txt_force)
        
        # 3. Save & Navigate
        config.save()
        self.show_home()

    def browse_output_folder(self) -> None:
        """Opens directory picker for Output Folder."""
        folder = filedialog.askdirectory(initialdir=config.OUTPUT_FOLDER)
        if folder:
            self.entry_output.delete(0, "end")
            self.entry_output.insert(0, folder)

    # ==========================================
    # UI CONSTRUCTION: HOME
    # ==========================================
    
    def setup_home_ui(self) -> None:
        # Settings Button (Top Right)
        btn_settings = ctk.CTkButton(
            self.home_frame, text="⚙️ Settings", width=100, height=30, 
            fg_color="transparent", border_width=1, border_color="gray", 
            text_color="gray", hover_color="#333333", command=self.show_settings
        )
        btn_settings.place(relx=0.95, rely=0.03, anchor="ne")

        # Hero Title
        lbl_title = ctk.CTkLabel(self.home_frame, text="Argus", font=("Roboto", 96, "bold"), text_color="#FFFFFF")
        lbl_title.pack(pady=(80, 20)) 
        
        # Description (Updated Text)
        lbl_desc = ctk.CTkLabel(self.home_frame, text="Automated Image Renaming & Sorting", font=("Roboto", 24), text_color="#AAAAAA")
        lbl_desc.pack(pady=(0, 40)) 

        # Main Action Button
        self.btn_run = ctk.CTkButton(
            self.home_frame, text="UPLOAD PHOTOS", font=("Roboto", 20, "bold"), 
            height=80, width=400, fg_color="#2CC985", hover_color="#229A65", 
            corner_radius=40, command=self.handle_button_click
        )
        self.btn_run.pack(pady=10)

        # Progress Bar
        self.progress = ctk.CTkProgressBar(self.home_frame, width=600, height=15)
        self.progress.pack(pady=(50, 20))
        self.progress.set(0)

        # Console Output Log
        self.textbox = ctk.CTkTextbox(
            self.home_frame, width=1000, height=300, corner_radius=10, 
            font=("Consolas", 13), fg_color="#181818", text_color="#D0D0D0"
        )
        self.textbox.pack(pady=10)
        self.log("Welcome to Argus. System initialized and ready.")

    # ==========================================
    # UI CONSTRUCTION: SETTINGS
    # ==========================================
    
    def setup_settings_ui(self) -> None:
        # Header Section
        header_frame = ctk.CTkFrame(self.settings_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=40)

        btn_back = ctk.CTkButton(
            header_frame, text="← Back", width=80, fg_color="transparent", 
            border_width=1, border_color="gray", command=self.save_and_go_home
        )
        btn_back.place(relx=0.05, rely=0.5, anchor="w")

        lbl_title = ctk.CTkLabel(header_frame, text="Configuration", font=("Roboto Medium", 32))
        lbl_title.pack(side="top")

        # Main Content Container
        content = ctk.CTkFrame(self.settings_frame, fg_color="#2B2B2B", corner_radius=15)
        content.pack(fill="both", expand=True, padx=100, pady=(0, 60))

        # 1. Output Folder
        ctk.CTkLabel(content, text="Default Output Folder:", font=("Roboto Medium", 16)).pack(pady=(20, 5), padx=40, anchor="w")
        
        folder_frame = ctk.CTkFrame(content, fg_color="transparent")
        folder_frame.pack(fill="x", padx=40, pady=(0, 10))
        
        self.entry_output = ctk.CTkEntry(folder_frame, height=35)
        self.entry_output.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.entry_output.insert(0, config.OUTPUT_FOLDER)
        
        btn_browse = ctk.CTkButton(folder_frame, text="Browse...", width=100, height=35, command=self.browse_output_folder)
        btn_browse.pack(side="right")

        # --- UPDATED: Professional Grid Layout for Toggles ---
        
        toggles_frame = ctk.CTkFrame(content, fg_color="transparent")
        toggles_frame.pack(fill="x", padx=40, pady=20)

        # Configure 3 equal columns for perfect alignment
        toggles_frame.grid_columnconfigure(0, weight=1)
        toggles_frame.grid_columnconfigure(1, weight=1)
        toggles_frame.grid_columnconfigure(2, weight=1)
        
        # Define Switches
        self.var_append = ctk.BooleanVar(value=config.APPEND_ORIGINAL_NAME)
        sw1 = ctk.CTkSwitch(toggles_frame, text="Append Original Filename", variable=self.var_append, font=("Roboto", 14), button_color="#2CC985", progress_color="#555555")
        
        self.var_discard_coa = ctk.BooleanVar(value=config.DISCARD_COA)
        sw2 = ctk.CTkSwitch(toggles_frame, text="Discard COA Image", variable=self.var_discard_coa, font=("Roboto", 14), button_color="#2CC985", progress_color="#555555")
        
        self.var_use_gpu = ctk.BooleanVar(value=config.USE_GPU)
        sw_gpu = ctk.CTkSwitch(toggles_frame, text="Use GPU Acceleration", variable=self.var_use_gpu, font=("Roboto", 14), button_color="#2CC985", progress_color="#555555")
        
        self.var_group_folders = ctk.BooleanVar(value=config.GROUP_FOLDERS)
        sw_group = ctk.CTkSwitch(toggles_frame, text="Group into Folders", variable=self.var_group_folders, font=("Roboto", 14), button_color="#2CC985", progress_color="#555555")
        
        self.var_debug_logs = ctk.BooleanVar(value=config.SAVE_DEBUG_LOGS)
        sw3 = ctk.CTkSwitch(toggles_frame, text="Save Text Logs (.md)", variable=self.var_debug_logs, font=("Roboto", 14), button_color="#2CC985", progress_color="#555555")

        # Place them in a clean 2-row Grid
        # Row 1
        sw1.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        sw2.grid(row=0, column=1, padx=10, pady=10, sticky="w")
        sw_gpu.grid(row=0, column=2, padx=10, pady=10, sticky="w")

        # Row 2
        sw_group.grid(row=1, column=0, padx=10, pady=10, sticky="w")
        sw3.grid(row=1, column=1, padx=10, pady=10, sticky="w")

        # Divider
        ctk.CTkFrame(content, height=2, fg_color="#444444").pack(fill="x", padx=40, pady=15)

        # 3. Detection Lists
        lists_frame = ctk.CTkFrame(content, fg_color="transparent")
        lists_frame.pack(fill="both", expand=True, padx=40, pady=(0, 20))

        def create_list_col(parent, title, data_list):
            frame = ctk.CTkFrame(parent, fg_color="transparent")
            frame.pack(side="left", fill="both", expand=True, padx=5)
            ctk.CTkLabel(frame, text=title, font=("Roboto Medium", 14)).pack(anchor="w", pady=(0, 5))
            textbox = ctk.CTkTextbox(frame, font=("Consolas", 12), height=150)
            textbox.pack(fill="both", expand=True)
            textbox.insert("1.0", "\n".join(data_list))
            return textbox

        self.txt_strong = create_list_col(lists_frame, "Strong Indicators (Match 1):", config.STRONG_INDICATORS)
        self.txt_weak = create_list_col(lists_frame, "Weak Indicators (Match 3):", config.WEAK_INDICATORS)
        self.txt_force = create_list_col(lists_frame, "Force Uppercase Acronyms:", config.FORCE_UPPERCASE)

    # ==========================================
    # CORE LOGIC
    # ==========================================
    
    def log(self, message: str) -> None:
        """Appends message to the console textbox."""
        self.textbox.insert("end", message + "\n")
        self.textbox.see("end")

    def update_progress(self, val: float) -> None:
        """Updates the progress bar (0.0 to 1.0)."""
        self.progress.set(val)

    def handle_button_click(self) -> None:
        """Toggles between starting selection and stopping operation."""
        if self.is_running:
            self.stop_event.set()
            self.log("🛑 Stopping... Please wait.")
            self.btn_run.configure(text="STOPPING...", state="disabled")
        else:
            self.start_selection()

    def start_selection(self) -> None:
        """Opens file dialog and starts the processing thread."""
        files = filedialog.askopenfilenames(
            title="Select Photos to Sort", 
            filetypes=[("Images", "*.jpg *.jpeg *.png *.JPG *.PNG")]
        )
        if not files: return 

        output_dir = Path(config.OUTPUT_FOLDER)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        self.is_running = True
        self.stop_event.clear()
        
        self.btn_run.configure(text="CANCEL OPERATION", fg_color="#D94040", hover_color="#A32424")
        self.progress.set(0)
        self.textbox.delete("1.0", "end")
        
        # Start processing in background thread to keep GUI responsive
        threading.Thread(target=self.run_process, args=(files, output_dir)).start()

    def run_process(self, file_list: List[str], output_path: Path) -> None:
        """Wrapper for the main processing logic."""
        try:
            main.run_sorter(file_list, output_path, self.log, self.update_progress, self.stop_event)
        except Exception as e:
            self.log(f"CRITICAL ERROR: {e}")
            import traceback
            traceback.print_exc()
        
        self.is_running = False
        self.btn_run.configure(state="normal", text="RENAME PHOTOS", fg_color="#2CC985", hover_color="#229A65")

if __name__ == "__main__":
    app = ArgusApp()
    app.mainloop()