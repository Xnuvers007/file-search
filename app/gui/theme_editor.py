# app/gui/theme_editor.py
import tkinter as tk
from tkinter import ttk, colorchooser, messagebox
import os

class ThemeEditorWindow(tk.Toplevel):
    def __init__(self, parent, main_app, icon_path=None):
        super().__init__(parent)
        self.main_app = main_app
        self.title("Custom Theme Editor")
        self.geometry("450x350")
        
        # ### PERUBAHAN DI SINI: Atur ikon jendela ###
        if icon_path and os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except tk.TclError:
                pass # Abaikan jika format ikon tidak didukung
        
        self.transient(parent)
        self.grab_set()

        self.theme_vars = {}
        self.color_labels = {}
        
        current_theme = main_app.current_theme_dict
        
        frame = ttk.Frame(self, padding=20)
        frame.pack(expand=True, fill=tk.BOTH)
        frame.columnconfigure(2, weight=1)
        
        theme_elements = {
            "bg": "Background", "fg": "Foreground (Text)",
            "entry_bg": "Entry Background", "accent": "Accent / Hover",
            "select_bg": "Selection Background", "select_fg": "Selection Text",
            "highlight": "Highlight Color"
        }
        
        for i, (key, text) in enumerate(theme_elements.items()):
            var = tk.StringVar(value=current_theme.get(key, "#FFFFFF"))
            self.theme_vars[key] = var
            
            ttk.Label(frame, text=f"{text}:").grid(row=i, column=0, sticky="w", pady=5)
            
            color_swatch = tk.Label(frame, text="    ", bg=var.get(), relief="sunken")
            color_swatch.grid(row=i, column=1, padx=5)
            self.color_labels[key] = color_swatch

            ttk.Entry(frame, textvariable=var).grid(row=i, column=2, sticky="ew")
            ttk.Button(frame, text="...", command=lambda k=key: self.choose_color(k), width=3).grid(row=i, column=3, padx=5)

        button_frame = ttk.Frame(frame)
        button_frame.grid(row=len(theme_elements), column=0, columnspan=4, pady=20)
        ttk.Button(button_frame, text="Apply", command=self.apply_changes).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Save & Apply", command=self.save_and_apply).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Close", command=self.destroy).pack(side=tk.LEFT, padx=10)

    def choose_color(self, key):
        var = self.theme_vars[key]
        initial_color = var.get()
        color_code = colorchooser.askcolor(title="Choose color", initialcolor=initial_color, parent=self)
        
        if color_code and color_code[1]:
            hex_color = color_code[1]
            var.set(hex_color)
            self.color_labels[key].config(bg=hex_color)

    def get_theme_dict(self):
        return {key: var.get() for key, var in self.theme_vars.items()}
        
    def apply_changes(self):
        custom_theme = self.get_theme_dict()
        self.main_app.apply_theme("Custom", custom_theme_dict=custom_theme)

    def save_and_apply(self):
        self.apply_changes()
        custom_theme = self.get_theme_dict()
        self.main_app.themes['Custom'] = custom_theme
        self.main_app.rebuild_theme_menu()
        self.main_app.save_settings()
        messagebox.showinfo("Saved", "Custom theme saved. It will be available in the theme menu.", parent=self)