import customtkinter as ctk
import threading
import ctypes
from pathlib import Path
from tkinter import filedialog, PhotoImage
import main
import file_manager as fm
import config

# --- THEME ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class ArgusApp(ctk.CTk):
    def __init__(self):
        # 1. FIX TASKBAR ICON
        myappid = 'propabilia.argus.sorter.2.0'
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except Exception:
            pass 

        super().__init__()

        # WINDOW SETUP
        self.title("Argus")
        self.geometry("1200x900")
        self.resizable(False, False)
        
        self.base_path = fm.get_application_path()

        # 2. SET ICON
        icon_path = self.base_path / "icon.png"
        if icon_path.exists():
            try:
                img = PhotoImage(file=str(icon_path))
                self.iconphoto(True, img)
                self.after(200, lambda: self.iconphoto(True, img))
            except Exception as e:
                print(f"Warning: Could not load icon: {e}")

        # --- LOAD SETTINGS ---
        config.load()
        
        self.is_running = False
        self.stop_event = threading.Event()

        # --- SETUP PAGES ---
        self.home_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.settings_frame = ctk.CTkFrame(self, fg_color="transparent")

        self.setup_home_ui()
        self.setup_settings_ui()

        self.show_home()

    # ==========================================
    # NAVIGATION METHODS
    # ==========================================
    def show_home(self):
        self.settings_frame.pack_forget()
        self.home_frame.pack(fill="both", expand=True)

    def show_settings(self):
        if self.is_running: return
        self.home_frame.pack_forget()
        self.settings_frame.pack(fill="both", expand=True)

    def save_and_go_home(self):
        # 1. Update Toggles & Folder
        config.APPEND_ORIGINAL_NAME = self.var_append.get()
        config.DISCARD_COA = self.var_discard_coa.get()
        config.SAVE_DEBUG_LOGS = self.var_debug_logs.get()
        config.OUTPUT_FOLDER = self.entry_output.get()
        
        # 2. Update Strong Indicators
        raw_strong = self.txt_strong.get("1.0", "end").strip()
        if raw_strong:
            config.STRONG_INDICATORS = [l.strip().upper() for l in raw_strong.split('\n') if l.strip()]
            
        # 3. Update Weak Indicators
        raw_weak = self.txt_weak.get("1.0", "end").strip()
        if raw_weak:
            config.WEAK_INDICATORS = [l.strip().upper() for l in raw_weak.split('\n') if l.strip()]

        # 4. Update Force Uppercase (NEW)
        raw_force = self.txt_force.get("1.0", "end").strip()
        if raw_force:
            config.FORCE_UPPERCASE = [l.strip().upper() for l in raw_force.split('\n') if l.strip()]
        
        # 5. Save to File
        config.save()
        self.show_home()

    def browse_output_folder(self):
        folder = filedialog.askdirectory(initialdir=config.OUTPUT_FOLDER)
        if folder:
            self.entry_output.delete(0, "end")
            self.entry_output.insert(0, folder)

    # ==========================================
    # PAGE 1: HOME UI
    # ==========================================
    def setup_home_ui(self):
        btn_settings = ctk.CTkButton(self.home_frame, text="⚙️ Settings", width=100, height=30, fg_color="transparent", border_width=1, border_color="gray", text_color="gray", hover_color="#333333", command=self.show_settings)
        btn_settings.place(relx=0.95, rely=0.03, anchor="ne")

        lbl_title = ctk.CTkLabel(self.home_frame, text="Argus", font=("Roboto", 96, "bold"), text_color="#FFFFFF")
        lbl_title.pack(pady=(100, 5)) 
        
        lbl_desc = ctk.CTkLabel(self.home_frame, text="Automated Image Renaming & Sorting", font=("Roboto", 24), text_color="#AAAAAA")
        lbl_desc.pack(pady=(10, 60)) 

        self.btn_run = ctk.CTkButton(self.home_frame, text="SORT PHOTOS", font=("Roboto", 20, "bold"), height=80, width=400, fg_color="#2CC985", hover_color="#229A65", corner_radius=40, command=self.handle_button_click)
        self.btn_run.pack(pady=10)

        self.progress = ctk.CTkProgressBar(self.home_frame, width=600, height=15)
        self.progress.pack(pady=(50, 20))
        self.progress.set(0)

        self.textbox = ctk.CTkTextbox(self.home_frame, width=1000, height=300, corner_radius=10, font=("Consolas", 13), fg_color="#181818", text_color="#D0D0D0")
        self.textbox.pack(pady=10)
        self.log("Welcome to Argus. System initialized and ready.")

    # ==========================================
    # PAGE 2: SETTINGS UI
    # ==========================================
    def setup_settings_ui(self):
        header_frame = ctk.CTkFrame(self.settings_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=40)

        btn_back = ctk.CTkButton(header_frame, text="← Back", width=80, fg_color="transparent", border_width=1, border_color="gray", command=self.save_and_go_home)
        btn_back.place(relx=0.05, rely=0.5, anchor="w")

        lbl_title = ctk.CTkLabel(header_frame, text="Configuration", font=("Roboto Medium", 32))
        lbl_title.pack(side="top")

        content = ctk.CTkFrame(self.settings_frame, fg_color="#2B2B2B", corner_radius=15)
        content.pack(fill="both", expand=True, padx=100, pady=(0, 60))

        # 1. OUTPUT FOLDER
        ctk.CTkLabel(content, text="Default Output Folder:", font=("Roboto Medium", 16)).pack(pady=(20, 5), padx=40, anchor="w")
        folder_frame = ctk.CTkFrame(content, fg_color="transparent")
        folder_frame.pack(fill="x", padx=40, pady=(0, 10))
        self.entry_output = ctk.CTkEntry(folder_frame, height=35)
        self.entry_output.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.entry_output.insert(0, config.OUTPUT_FOLDER)
        btn_browse = ctk.CTkButton(folder_frame, text="Browse...", width=100, height=35, command=self.browse_output_folder)
        btn_browse.pack(side="right")

        # 2. TOGGLES
        toggles_frame = ctk.CTkFrame(content, fg_color="transparent")
        toggles_frame.pack(fill="x", padx=40, pady=10)
        
        self.var_append = ctk.BooleanVar(value=config.APPEND_ORIGINAL_NAME)
        sw1 = ctk.CTkSwitch(toggles_frame, text="Append Original Filename", variable=self.var_append, font=("Roboto", 14), button_color="#2CC985", progress_color="#555555")
        sw1.pack(side="left", padx=(0, 20))
        
        self.var_discard_coa = ctk.BooleanVar(value=config.DISCARD_COA)
        sw2 = ctk.CTkSwitch(toggles_frame, text="Discard COA Image", variable=self.var_discard_coa, font=("Roboto", 14), button_color="#2CC985", progress_color="#555555")
        sw2.pack(side="left", padx=20)

        self.var_debug_logs = ctk.BooleanVar(value=config.SAVE_DEBUG_LOGS)
        sw3 = ctk.CTkSwitch(toggles_frame, text="Save Text Logs (.md)", variable=self.var_debug_logs, font=("Roboto", 14), button_color="#2CC985", progress_color="#555555")
        sw3.pack(side="left", padx=20)

        ctk.CTkFrame(content, height=2, fg_color="#444444").pack(fill="x", padx=40, pady=15)

        # 3. LIST EDITORS (3 Columns)
        lists_frame = ctk.CTkFrame(content, fg_color="transparent")
        lists_frame.pack(fill="both", expand=True, padx=40, pady=(0, 20))

        # Helper to create column
        def create_list_col(parent, title, data_list):
            frame = ctk.CTkFrame(parent, fg_color="transparent")
            frame.pack(side="left", fill="both", expand=True, padx=5)
            ctk.CTkLabel(frame, text=title, font=("Roboto Medium", 14)).pack(anchor="w", pady=(0, 5))
            textbox = ctk.CTkTextbox(frame, font=("Consolas", 12), height=150)
            textbox.pack(fill="both", expand=True)
            textbox.insert("1.0", "\n".join(data_list))
            return textbox

        # Create 3 Columns
        self.txt_strong = create_list_col(lists_frame, "Strong Indicators (Match 1):", config.STRONG_INDICATORS)
        self.txt_weak = create_list_col(lists_frame, "Weak Indicators (Match 3):", config.WEAK_INDICATORS)
        self.txt_force = create_list_col(lists_frame, "Force Uppercase Acronyms:", config.FORCE_UPPERCASE)

    # ==========================================
    # LOGIC METHODS
    # ==========================================
    def log(self, message):
        self.textbox.insert("end", message + "\n")
        self.textbox.see("end")

    def update_progress(self, val):
        self.progress.set(val)

    def handle_button_click(self):
        if self.is_running:
            self.stop_event.set()
            self.log("🛑 Stopping... Please wait.")
            self.btn_run.configure(text="STOPPING...", state="disabled")
        else:
            self.start_selection()

    def start_selection(self):
        files = filedialog.askopenfilenames(title="Select Photos to Sort", filetypes=[("Images", "*.jpg *.jpeg *.png *.JPG *.PNG")])
        if not files: return 

        output_dir = Path(config.OUTPUT_FOLDER)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        self.is_running = True
        self.stop_event.clear()
        
        self.btn_run.configure(text="CANCEL OPERATION", fg_color="#D94040", hover_color="#A32424")
        self.progress.set(0)
        self.textbox.delete("1.0", "end")
        
        threading.Thread(target=self.run_process, args=(files, output_dir)).start()

    def run_process(self, file_list, output_path):
        try:
            main.run_sorter(file_list, output_path, self.log, self.update_progress, self.stop_event)
        except Exception as e:
            self.log(f"CRITICAL ERROR: {e}")
            import traceback
            traceback.print_exc()
        
        self.is_running = False
        self.btn_run.configure(state="normal", text="SORT PHOTOS", fg_color="#2CC985", hover_color="#229A65")

if __name__ == "__main__":
    app = ArgusApp()
    app.mainloop()