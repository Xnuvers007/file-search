# app/gui/main_window.py
import os
import string
import time
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from datetime import datetime
import queue
import re

from .theme_editor import ThemeEditorWindow
from .analytics_window import AnalyticsWindow
from ..core.search_engine import SearchEngine
from ..utils.settings_manager import SettingsManager
from .donation_window import DonationWindow

class FileSearchGUI:
    def __init__(self, root, icon_path=None):
        self.root = root
        self.all_found_files = {}
        self.icon_path = icon_path
        self.themes = self.get_themes()
        self.search_history = []
        self.selected_theme = "Light"
        self.current_theme_dict = self.themes["Light"]

        self.settings_manager = SettingsManager()
        self.result_queue = queue.Queue()
        
        self.setup_window()
        self.setup_variables()
        self.setup_styles()
        self.create_widgets()
        self.load_settings()

        self.search_running = False
        self.cancel_event = threading.Event()
        self.found_files_count = 0
        self.collecting_overlay = None

    def get_themes(self):
        return {
            "Light": {"bg": "#F0F0F0", "fg": "#000000", "entry_bg": "#FFFFFF", "accent": "#E1E1E1", "select_bg": "#0078D7", "select_fg": "#FFFFFF", "highlight": "yellow"},
            "Dark": {"bg": "#2E2E2E", "fg": "#EAEAEA", "entry_bg": "#3C3C3C", "accent": "#3C3C3C", "select_bg": "#5A9CF8", "select_fg": "#000000", "highlight": "#F9A825"},
            "Ocean Blue": {"bg": "#EAF6FF", "fg": "#003B6E", "entry_bg": "#FFFFFF", "accent": "#D4EFFF", "select_bg": "#005A9E", "select_fg": "#FFFFFF", "highlight": "#FFD700"}
        }

    def setup_window(self):
        self.root.title("File Content Search Pro - Xnuvers007 | Indra Dwi A")
        
        try:
            self.root.state('zoomed')
        except tk.TclError:
            self.root.attributes('-zoomed', True)

        if self.icon_path and os.path.exists(self.icon_path):
            self.root.iconbitmap(self.icon_path)
        self.root.minsize(1200, 750)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

    def setup_variables(self):
        self.keyword_var = tk.StringVar()
        self.search_path_var = tk.StringVar()
        self.case_sensitive_var = tk.BooleanVar(value=False)
        self.whole_word_var = tk.BooleanVar(value=False)
        self.regex_var = tk.BooleanVar(value=False)
        self.max_workers_var = tk.IntVar(value=os.cpu_count() or 4)
        self.save_results_var = tk.BooleanVar(value=True)
        self.size_filter_var = tk.StringVar(value="any")
        self.size_value_var = tk.DoubleVar(value=0)
        self.size_unit_var = tk.StringVar(value="MB")
        self.date_after_var = tk.StringVar()
        self.date_before_var = tk.StringVar()
        self.ignore_folders_var = tk.StringVar(value=".git, .svn, .vscode, .idea, __pycache__, node_modules, venv, env, build, dist, temp, tmp, $RECYCLE.BIN, System Volume Information")
        self.ignore_files_var = tk.StringVar(value="*.log, *.tmp, *.bak, .DS_Store, thumbs.db")
        self.status_var = tk.StringVar(value="Ready")

    def setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
    def create_widgets(self):
        menubar = tk.Menu(self.root); self.root.config(menu=menubar)
        
        # Menu File
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open Search Location", command=self.browse_folder)
        file_menu.add_command(label="Save Results", command=self.auto_save_results)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_close)
        
        # Menu Settings
        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Settings", menu=settings_menu)
        self.theme_menu = tk.Menu(settings_menu, tearoff=0)
        settings_menu.add_cascade(label="Theme", menu=self.theme_menu)
        self.rebuild_theme_menu()

        settings_menu.add_separator()
        settings_menu.add_command(label="Donate / Support", command=self.show_donation_window)
        
        # Menu Help
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)

        main_h_pane = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_h_pane.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10,0))
        self.left_frame = ttk.Frame(main_h_pane, padding=10); main_h_pane.add(self.left_frame, weight=1); self.left_frame.columnconfigure(0, weight=1)
        config_frame = ttk.LabelFrame(self.left_frame, text="Search Configuration", padding=10)
        config_frame.grid(row=0, column=0, sticky="ew"); config_frame.columnconfigure(1, weight=1)
        ttk.Label(config_frame, text="Keyword:", style='Heading.TLabel').grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.keyword_combo = ttk.Combobox(config_frame, textvariable=self.keyword_var, font=('Segoe UI', 10))
        self.keyword_combo.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=2)
        options_frame = ttk.Frame(config_frame); options_frame.grid(row=2, column=0, columnspan=2, sticky="w", padx=5, pady=5)
        ttk.Checkbutton(options_frame, text="Case Sensitive", variable=self.case_sensitive_var).pack(side=tk.LEFT)
        ttk.Checkbutton(options_frame, text="Whole Word", variable=self.whole_word_var).pack(side=tk.LEFT, padx=10)
        ttk.Checkbutton(options_frame, text="Regex", variable=self.regex_var).pack(side=tk.LEFT)
        ttk.Label(config_frame, text="Path:", style='Heading.TLabel').grid(row=3, column=0, sticky="w", padx=5, pady=2)
        path_frame = ttk.Frame(config_frame); path_frame.grid(row=4, column=0, columnspan=2, sticky="ew", padx=5, pady=2); path_frame.columnconfigure(0, weight=1)
        self.path_entry = ttk.Entry(path_frame, textvariable=self.search_path_var); self.path_entry.grid(row=0, column=0, sticky="ew")
        ttk.Button(path_frame, text="Browse", command=self.browse_folder, width=8).grid(row=0, column=1, padx=(5,2))
        ttk.Button(path_frame, text="All Drives", command=lambda: self.search_path_var.set("all"), width=8).grid(row=0, column=2)
        filters_frame = ttk.LabelFrame(self.left_frame, text="Filters & Performance", padding=10)
        filters_frame.grid(row=1, column=0, sticky="ew", pady=10); filters_frame.columnconfigure(1, weight=1)
        ttk.Label(filters_frame, text="Size:", style='Heading.TLabel').grid(row=0, column=0, sticky="w", padx=5, pady=2)
        size_frame = ttk.Frame(filters_frame); size_frame.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        ttk.Combobox(size_frame, textvariable=self.size_filter_var, values=["any", "greater than", "less than"], width=12, state='readonly').pack(side=tk.LEFT)
        ttk.Entry(size_frame, textvariable=self.size_value_var, width=8).pack(side=tk.LEFT, padx=(5,0))
        ttk.Combobox(size_frame, textvariable=self.size_unit_var, values=["KB", "MB", "GB"], width=5, state='readonly').pack(side=tk.LEFT)
        ttk.Label(filters_frame, text="Date Modified:", style='Heading.TLabel').grid(row=1, column=0, sticky="w", padx=5, pady=2)
        date_frame = ttk.Frame(filters_frame); date_frame.grid(row=1, column=1, sticky="ew", padx=5, pady=2)
        ttk.Label(date_frame, text="After:").pack(side=tk.LEFT); ttk.Entry(date_frame, textvariable=self.date_after_var, width=12).pack(side=tk.LEFT, padx=(0,5))
        ttk.Label(date_frame, text="Before:").pack(side=tk.LEFT); ttk.Entry(date_frame, textvariable=self.date_before_var, width=12).pack(side=tk.LEFT)
        ttk.Label(date_frame, text="(Y-M-D)").pack(side=tk.LEFT, padx=5)
        ttk.Label(filters_frame, text="Ignore Folders:", style='Heading.TLabel').grid(row=2, column=0, sticky="w", padx=5, pady=2)
        ttk.Entry(filters_frame, textvariable=self.ignore_folders_var).grid(row=2, column=1, sticky="ew", padx=5, pady=2)
        ttk.Label(filters_frame, text="Ignore Files:", style='Heading.TLabel').grid(row=3, column=0, sticky="w", padx=5, pady=2)
        ttk.Entry(filters_frame, textvariable=self.ignore_files_var).grid(row=3, column=1, sticky="ew", padx=5, pady=2)
        perf_frame = ttk.Frame(filters_frame); perf_frame.grid(row=4, column=0, columnspan=2, sticky='w', padx=5, pady=5)
        ttk.Label(perf_frame, text="Max Workers:").pack(side=tk.LEFT)
        ttk.Spinbox(perf_frame, from_=1, to=(os.cpu_count() or 1) * 2, width=5, textvariable=self.max_workers_var).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(perf_frame, text="Auto-save Results", variable=self.save_results_var).pack(side=tk.LEFT, padx=20)
        control_frame = ttk.Frame(self.left_frame); control_frame.grid(row=2, column=0, pady=10, sticky='w')
        self.search_button = ttk.Button(control_frame, text="Start Search", command=self.start_search); self.search_button.pack(side=tk.LEFT)
        self.cancel_button = ttk.Button(control_frame, text="Cancel", command=self.cancel_search, state=tk.DISABLED); self.cancel_button.pack(side=tk.LEFT, padx=5)
        self.analytics_button = ttk.Button(control_frame, text="Show Analytics", command=self.show_analytics, state=tk.DISABLED); self.analytics_button.pack(side=tk.LEFT)

        right_v_pane = ttk.PanedWindow(main_h_pane, orient=tk.VERTICAL); main_h_pane.add(right_v_pane, weight=3)
        results_frame_container = ttk.Frame(right_v_pane, padding=(10,0,0,0)); right_v_pane.add(results_frame_container, weight=3)
        results_frame_container.rowconfigure(0, weight=1); results_frame_container.columnconfigure(0, weight=1)
        self.results_tree = ttk.Treeview(results_frame_container, columns=('Path', 'Size', 'Modified'), show='headings', selectmode="extended")
        self.results_tree.grid(row=0, column=0, sticky="nsew"); yscroll = ttk.Scrollbar(results_frame_container, orient=tk.VERTICAL, command=self.results_tree.yview)
        yscroll.grid(row=0, column=1, sticky='ns'); self.results_tree.configure(yscrollcommand=yscroll.set)
        self.results_tree.heading('#0', text='File Name'); self.results_tree.heading('Path', text='Full Path'); self.results_tree.heading('Size', text='Size'); self.results_tree.heading('Modified', text='Last Modified')
        self.results_tree.column('#0', width=250, stretch=tk.NO); self.results_tree.column('Path', width=500); self.results_tree.column('Size', width=100, stretch=tk.NO, anchor='e'); self.results_tree.column('Modified', width=150, stretch=tk.NO, anchor='center')
        self.results_tree.bind('<<TreeviewSelect>>', self.show_preview)
        preview_container = ttk.LabelFrame(right_v_pane, text="Content Preview", padding=5); right_v_pane.add(preview_container, weight=2)
        preview_container.rowconfigure(0, weight=1); preview_container.columnconfigure(0, weight=1)
        self.preview_pane = scrolledtext.ScrolledText(preview_container, wrap=tk.WORD, state="disabled", font=('Calibri', 10))
        self.preview_pane.grid(row=0, column=0, sticky="nsew")
        self.results_menu = tk.Menu(self.root, tearoff=0)
        self.results_menu.add_command(label="Copy Selected Path(s)", command=self.copy_selected_paths)
        self.results_menu.add_command(label="Open File Location", command=self.open_selected_folder)
        self.results_tree.bind("<Button-3>", self.show_context_menu)
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor='w', padding=(5, 2))
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def apply_theme(self, theme_name, custom_theme_dict=None):
        if custom_theme_dict:
            theme = custom_theme_dict; self.selected_theme = "Custom"
        elif theme_name in self.themes:
            theme = self.themes[theme_name]; self.selected_theme = theme_name
        else: return
            
        self.current_theme_dict = theme
        bg, fg, entry_bg, accent, select_bg, select_fg, highlight_bg = theme.values()
        self.root.config(bg=bg)
        self.style.configure('.', background=bg, foreground=fg, fieldbackground=entry_bg, bordercolor=fg)
        self.style.map('.', background=[('active', accent)])
        self.style.configure('TFrame', background=bg); self.style.configure('TLabel', background=bg, foreground=fg)
        self.style.configure('Title.TLabel', background=bg, foreground=fg, font=('Segoe UI', 16, 'bold'))
        self.style.configure('Heading.TLabel', background=bg, foreground=fg, font=('Segoe UI', 11, 'bold'))
        self.style.configure('TCheckbutton', background=bg, foreground=fg)
        self.style.map('TCheckbutton', indicatorbackground=[('selected', select_bg)], indicatorforeground=[('selected', select_fg)])
        self.style.configure('TLabelframe', background=bg, foreground=fg); self.style.configure('TLabelframe.Label', background=bg, foreground=fg)
        self.style.configure('TButton', foreground=fg); self.style.map('TButton', background=[('active', select_bg)], foreground=[('active', select_fg)])
        self.style.configure('TEntry', fieldbackground=entry_bg, foreground=fg, insertcolor=fg)
        self.style.configure('TCombobox', fieldbackground=entry_bg, foreground=fg)
        self.style.map('TCombobox', fieldbackground=[('readonly', bg)])
        self.style.configure("Treeview", background=entry_bg, foreground=fg, fieldbackground=entry_bg)
        self.style.map('Treeview', background=[('selected', select_bg)], foreground=[('selected', select_fg)])
        if hasattr(self, 'preview_pane'):
            self.preview_pane.config(bg=entry_bg, fg=fg, insertbackground=fg, selectbackground=select_bg, selectforeground=select_fg)
            self.preview_pane.tag_configure("highlight", background=highlight_bg, foreground="black")

    def rebuild_theme_menu(self):
        self.theme_menu.delete(0, tk.END)
        for theme_name in self.themes.keys():
            self.theme_menu.add_command(label=theme_name, command=lambda t=theme_name: self.apply_theme(t))
        self.theme_menu.add_separator()
        self.theme_menu.add_command(label="Custom...", command=self.open_theme_editor)

    def open_theme_editor(self):
        ThemeEditorWindow(self.root, self, self.icon_path)

    def show_analytics(self):
        if not self.results_tree.get_children():
            messagebox.showinfo("No Data", "Tidak ada hasil pencarian untuk dianalisis.", parent=self.root)
            return

        # ### PERBAIKAN DI SINI: Kumpulkan semua data yang dibutuhkan ###
        results_data = []
        for item_id in self.results_tree.get_children():
            item = self.results_tree.item(item_id)
            # Dapatkan data dari dictionary asli yang disimpan saat file ditemukan
            # atau ambil langsung dari Treeview jika sudah di-cache di sana
            file_info = self.all_found_files.get(item_id)
            if file_info:
                 results_data.append(file_info)

        if not results_data:
             messagebox.showinfo("Data Error", "Gagal mengumpulkan data untuk analitik.", parent=self.root)
             return

        AnalyticsWindow(self.root, results_data, self.current_theme_dict, self.icon_path)

    def start_search(self):
        if not self.keyword_var.get().strip(): messagebox.showerror("Error", "Keyword is required.", parent=self.root); return
        if not self.search_path_var.get().strip(): messagebox.showerror("Error", "Search path is required.", parent=self.root); return
        
        self.found_files_count = 0; self.search_running = True
        self.start_time = time.time()
        self.cancel_event = threading.Event()
        self.search_button.config(state=tk.DISABLED); self.cancel_button.config(state=tk.NORMAL)
        self.analytics_button.config(state=tk.DISABLED)
        self.clear_results()
        self.update_search_history(self.keyword_var.get())
        
        search_paths = [f"{d}:\\" for d in string.ascii_uppercase if os.path.exists(f"{d}:\\")] if self.search_path_var.get().lower() == 'all' else [self.search_path_var.get()]
        
        try:
            size_filters = self._get_size_filters(); date_filters = self._get_date_filters()
        except ValueError as e:
            messagebox.showerror("Invalid Filter", str(e), parent=self.root); self.finish_search(was_cancelled=False); return

        search_params = {
            'keyword': self.keyword_var.get().strip(), 'search_paths': search_paths,
            'case_sensitive': self.case_sensitive_var.get(), 'whole_word': self.whole_word_var.get(),
            'regex': self.regex_var.get(), 'max_workers': self.max_workers_var.get(),
            'ignore_folders': {name.strip() for name in self.ignore_folders_var.get().split(',') if name.strip()},
            'ignore_files': [pat.strip() for pat in self.ignore_files_var.get().split(',') if pat.strip()],
            'size_filters': size_filters, 'date_filters': date_filters
        }
        
        self.search_engine_thread = threading.Thread(target=self._run_search_engine, args=(search_params,), daemon=True)
        self.search_engine_thread.start()
        self.check_result_queue()

    def _run_search_engine(self, search_params):
        engine = SearchEngine(search_params, self.cancel_event)
        engine.run_search(
            progress_callback=lambda msg: self.result_queue.put(("progress", msg)),
            result_callback=lambda res: self.result_queue.put(("result", res)),
            finish_callback=lambda: self.result_queue.put(("finished", None))
        )

    def check_result_queue(self):
        try:
            while not self.result_queue.empty():
                msg_type, data = self.result_queue.get_nowait()
                if msg_type == "progress":
                    self.status_var.set(f"{data} | Found: {self.found_files_count}")
                elif msg_type == "result":
                    self.found_files_count += 1
                    self.add_result_to_tree(data)
                elif msg_type == "finished":
                    self.finish_search(was_cancelled=self.cancel_event.is_set())
                    return
        except queue.Empty:
            pass
        if self.search_running:
            self.root.after(100, self.check_result_queue)

    def finish_search(self, was_cancelled):
        self.search_running = False
        self.cancel_event.clear() ### PERBAIKAN: Reset event di akhir
        self.search_button.config(state=tk.NORMAL); self.cancel_button.config(state=tk.DISABLED)
        if self.found_files_count > 0: self.analytics_button.config(state=tk.NORMAL)
        
        duration = time.time() - self.start_time
        if was_cancelled:
            final_msg = f"Search cancelled. Found {self.found_files_count} file(s) in {duration:.2f}s."
        else:
            final_msg = f"Search complete. Found {self.found_files_count} file(s) in {duration:.2f}s."
            if self.save_results_var.get() and self.found_files_count > 0:
                self.auto_save_results()
                return # auto_save_results akan mengatur statusnya sendiri
                
        self.status_var.set(final_msg)
    
    ### PERBAIKAN: Logika cancel disederhanakan ###
    def cancel_search(self):
        if self.search_running:
            self.status_var.set("Cancelling...")
            self.cancel_event.set()
    
    def on_close(self):
        if self.search_running:
             if messagebox.askyesno("Confirm Exit", "A search is running. Are you sure you want to quit?", parent=self.root):
                self.cancel_event.set()
             else:
                return
        self.save_settings()
        self.root.destroy()
        
    def add_result_to_tree(self, file_info):
        size_str = f"{file_info['size']/1024:,.1f} KB" if file_info['size'] > 1024 else f"{file_info['size']} B"
        mod_time_str = time.strftime("%Y-%m-%d %H:%M", time.localtime(file_info['modified']))
        
        # Simpan ID item saat dimasukkan
        item_id = self.results_tree.insert('', tk.END, text=file_info['name'], values=(file_info['path'], size_str, mod_time_str))
        
        # Simpan info lengkap menggunakan ID sebagai kunci
        self.all_found_files[item_id] = file_info

    def _highlight_keyword(self, keyword):
        if not keyword or not self.preview_pane.get(1.0, tk.END).strip(): return
        self.preview_pane.tag_remove("highlight", 1.0, tk.END)
        start_idx = 1.0
        while True:
            start_idx = self.preview_pane.search(keyword, start_idx, tk.END, nocase=not self.case_sensitive_var.get(), regexp=self.regex_var.get())
            if not start_idx: break
            end_idx = f"{start_idx}+{len(keyword)}c"
            self.preview_pane.tag_add("highlight", start_idx, end_idx)
            start_idx = end_idx

    def update_search_history(self, keyword):
        if keyword in self.search_history: self.search_history.remove(keyword)
        self.search_history.insert(0, keyword)
        self.search_history = self.search_history[:20]
        self.keyword_combo['values'] = self.search_history

    ### PERBAIKAN: Logika auto-save yang lebih aman ###
    def _slugify(self, text):
        # Mengubah teks menjadi nama file yang aman
        text = re.sub(r'[^\w\s-]', '', text).strip().lower()
        text = re.sub(r'[-\s]+', '-', text)
        return text

    def auto_save_results(self):
        """Menyimpan hasil pencarian ke file teks."""
        if not self.results_tree.get_children():
            messagebox.showinfo("No Results", "No search results to save.", parent=self.root)
            return
            
        # Kumpulkan path dari semua hasil di tree view
        paths = [self.results_tree.item(item, 'values')[0] for item in self.results_tree.get_children()]
        keyword = self.keyword_var.get().strip()
        
        # Buat nama file yang aman
        safe_keyword = self._slugify(keyword)
        filename = f"search_{safe_keyword}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"Search Results for: '{keyword}'\n")
                f.write(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total Results: {len(paths)}\n\n")
                for path in sorted(paths):
                    f.write(f"{path}\n")
            
            self.status_var.set(f"Results saved to {os.path.abspath(filename)}")
            messagebox.showinfo("Save Results", f"Results saved to {os.path.abspath(filename)}", parent=self.root)
            return True
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save results: {e}", parent=self.root)
            return False

    def load_settings(self):
        settings = self.settings_manager.load()
        self.search_history = settings.get('history', []); self.keyword_combo['values'] = self.search_history
        self.case_sensitive_var.set(settings.get('case', False))
        self.whole_word_var.set(settings.get('whole', False))
        self.regex_var.set(settings.get('regex', False))
        self.save_results_var.set(settings.get('autosave', True))
        self.ignore_folders_var.set(settings.get('ignore_folders', '.git, .svn, .vscode, .idea, __pycache__, node_modules, venv, env, build, dist'))
        self.ignore_files_var.set(settings.get('ignore_files', '*.log, *.tmp, *.bak'))
        
        theme_to_load = settings.get('theme', 'Light')
        if theme_to_load == "Custom" and 'custom_theme' in settings:
            self.themes['Custom'] = settings['custom_theme']
            self.rebuild_theme_menu()
            self.apply_theme("Custom", custom_theme_dict=settings['custom_theme'])
        else:
            self.apply_theme(theme_to_load)

    def save_settings(self):
        settings = {
            'theme': self.selected_theme, 'history': self.search_history,
            'case': self.case_sensitive_var.get(), 'whole': self.whole_word_var.get(), 
            'regex': self.regex_var.get(), 'autosave': self.save_results_var.get(),
            'ignore_folders': self.ignore_folders_var.get(), 'ignore_files': self.ignore_files_var.get()
        }
        if self.selected_theme == "Custom":
            settings['custom_theme'] = self.current_theme_dict
        
        self.settings_manager.save(settings)
        
    def browse_folder(self):
        folder = filedialog.askdirectory(title="Select a Folder to Search", parent=self.root)
        if folder:
            self.search_path_var.set(folder)

    def _get_size_filters(self):
        if self.size_filter_var.get() == 'any': return None
        multipliers = {"KB": 1024, "MB": 1024**2, "GB": 1024**3}
        return {"op": self.size_filter_var.get(), "val": self.size_value_var.get() * multipliers[self.size_unit_var.get()]}

    def _get_date_filters(self):
        after_str, before_str = self.date_after_var.get(), self.date_before_var.get()
        if not after_str and not before_str: return None
        try:
            return {"after": datetime.strptime(after_str, "%Y-%m-%d") if after_str else None, "before": datetime.strptime(before_str, "%Y-%m-%d") if before_str else None}
        except ValueError:
            raise ValueError("Invalid date format. Please use YYYY-MM-DD.")

    # Tambahkan metode show_donation_window
    def show_donation_window(self):
        DonationWindow(self.root, self.icon_path)

    # Tambahkan metode show_about
    def show_about(self):
        messagebox.showinfo(
            "About File Content Search Pro",
            "File Content Search Pro v2.0\n\n"
            "A powerful utility for searching file contents across your system.\n\n"
            "Developed by: Xnuvers007 | Indra Dwi A\n\n"
            f"© {datetime.now().year} Xnuvers007 | All rights reserved\n\n"
            "For more information, visit our GitHub repository or contact us at:\n"
        )
            
    def copy_selected_paths(self):
        selection = self.results_tree.selection()
        if not selection: return
        paths = [self.results_tree.item(item, 'values')[0] for item in selection]
        self.root.clipboard_clear(); self.root.clipboard_append("\n".join(paths))
        self.status_var.set(f"Copied {len(paths)} path(s) to clipboard.")

    def open_selected_folder(self):
        selection = self.results_tree.selection()
        if not selection: return
        file_path = self.results_tree.item(selection[0], 'values')[0]
        try:
            os.startfile(os.path.dirname(file_path))
        except Exception as e:
            messagebox.showerror("Error", f"Could not open folder: {e}", parent=self.root)
            
    def show_context_menu(self, event):
        item_id = self.results_tree.identify_row(event.y)
        if item_id:
            if item_id not in self.results_tree.selection():
                self.results_tree.selection_set(item_id)
                self.results_tree.focus(item_id)
            self.results_menu.post(event.x_root, event.y_root)

    def clear_results(self):
        self.all_found_files.clear()
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        self.preview_pane.config(state="normal")
        self.preview_pane.delete(1.0, tk.END)
        self.preview_pane.config(state="disabled")
        self.status_var.set("Ready")

    def show_preview(self, event=None):
        selection = self.results_tree.selection()
        if not selection: return
        item = selection[0]
        file_path = self.results_tree.item(item, 'values')[0]
        
        content = SearchEngine({}, None)._get_file_content(file_path)
        
        self.preview_pane.config(state="normal")
        self.preview_pane.delete(1.0, tk.END)
        self.preview_pane.insert(tk.END, content if content else "Cannot preview this file type or file is empty.")
        if content:
            self._highlight_keyword(self.keyword_var.get())
        self.preview_pane.config(state="disabled")