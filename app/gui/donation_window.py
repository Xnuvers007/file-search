# app/gui/donation_window.py
import tkinter as tk
from tkinter import ttk
import webbrowser
import os

class DonationWindow(tk.Toplevel):
    def __init__(self, parent, icon_path=None):
        super().__init__(parent)
        self.title("Support the Project")
        self.geometry("500x400")
        
        # Set ikon jendela
        if icon_path and os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except tk.TclError:
                pass
        
        self.transient(parent)
        self.grab_set()
        
        # Main container dengan scrollbar
        main_container = ttk.Frame(self)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(main_container)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Canvas untuk scrolling
        canvas = tk.Canvas(main_container, yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar.config(command=canvas.yview)
        
        # Frame untuk konten
        content_frame = ttk.Frame(canvas)
        canvas_window = canvas.create_window((0, 0), window=content_frame, anchor=tk.NW)
        
        # Header
        header_frame = ttk.Frame(content_frame, padding=10)
        header_frame.pack(fill=tk.X)
        
        title_label = ttk.Label(header_frame, text="Support the Development", 
                              font=("Arial", 16, "bold"))
        title_label.pack(pady=(10, 5))
        
        msg_label = ttk.Label(header_frame, 
                            text="If you find this tool helpful, please consider supporting its development.",
                            wraplength=450, justify="center")
        msg_label.pack(pady=(0, 15))
        
        # Main Content
        donations_frame = ttk.Frame(content_frame, padding=20)
        donations_frame.pack(fill=tk.X, expand=True)
        
        # Trakteer
        trakteer_frame = ttk.LabelFrame(donations_frame, text="Trakteer", padding=10)
        trakteer_frame.pack(fill=tk.X, pady=10)
        
        trakteer_label = ttk.Label(trakteer_frame, 
                                text="Support via Trakteer, platform donasi lokal Indonesia.",
                                wraplength=450)
        trakteer_label.pack(pady=5)
        
        ttk.Button(trakteer_frame, text="Dukung di Trakteer", 
                  command=lambda: webbrowser.open("https://trakteer.id/Xnuvers007")).pack(pady=5)
        
        # GitHub Sponsors
        github_frame = ttk.LabelFrame(donations_frame, text="GitHub Sponsors", padding=10)
        github_frame.pack(fill=tk.X, pady=10)
        
        github_label = ttk.Label(github_frame, 
                               text="Become a GitHub sponsor and support the project on a monthly basis.",
                               wraplength=450)
        github_label.pack(pady=5)
        
        ttk.Button(github_frame, text="Become a Sponsor", 
                  command=lambda: webbrowser.open("https://github.com/sponsors/xnuvers007")).pack(pady=5)
        
        # Saweria
        saweria_frame = ttk.LabelFrame(donations_frame, text="Saweria", padding=10)
        saweria_frame.pack(fill=tk.X, pady=10)
        
        saweria_label = ttk.Label(saweria_frame, 
                             text="Dukung lewat Saweria, platform crowdfunding lokal Indonesia.",
                             wraplength=450)
        saweria_label.pack(pady=5)
        
        ttk.Button(saweria_frame, text="Dukung di Saweria", 
                  command=lambda: webbrowser.open("https://saweria.co/Xnuvers007")).pack(pady=5)
        
        # Footer
        footer_frame = ttk.Frame(content_frame, padding=10)
        footer_frame.pack(fill=tk.X)
        
        thanks_label = ttk.Label(footer_frame, 
                               text="Terima kasih atas dukungan Anda!",
                               font=("Arial", 10, "bold"))
        thanks_label.pack(pady=5)
        
        close_btn = ttk.Button(footer_frame, text="Close", command=self.destroy)
        close_btn.pack(pady=10)
        
        # Mengatur scrolling
        def _on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        content_frame.bind("<Configure>", _on_frame_configure)
        
        # Menyesuaikan lebar konten dengan canvas
        def _on_canvas_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)
        
        canvas.bind("<Configure>", _on_canvas_configure)
        
        # Bind mousewheel untuk scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind_all("<MouseWheel>", _on_mousewheel)