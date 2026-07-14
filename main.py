# main.py
import tkinter as tk
from tkinter import ttk, messagebox
from app.gui.main_window import FileSearchGUI
from app.utils.settings_manager import SettingsManager
from app.utils.i18n import set_language

# ### PERUBAHAN DI SINI: Import Pillow ###
try:
    from PIL import Image, ImageTk
except ImportError:
    ImageTk = None

def main():
    """Fungsi utama untuk menjalankan aplikasi dengan splash screen."""
    # ... (Pengecekan library lain tetap sama)
    if ImageTk is None:
        messagebox.showerror("Dependency Error", "Library Pillow tidak ditemukan.\n\nSilakan instal dengan menjalankan:\npip install Pillow")
        return

    root = tk.Tk()
    root.withdraw()

    splash = tk.Toplevel(root)
    splash.overrideredirect(True)

    splash_width, splash_height = 600, 400

    screen_width, screen_height = root.winfo_screenwidth(), root.winfo_screenheight()
    x = (screen_width // 2) - (splash_width // 2)
    y = (screen_height // 2) - (splash_height // 2)
    splash.geometry(f'{splash_width}x{splash_height}+{x}+{y}')

    splash_frame = tk.Frame(splash, bg="#2E2E2E", relief="ridge", borderwidth=2)
    splash_frame.pack(expand=True, fill="both")
    
    # ### PERUBAHAN DI SINI: Menambahkan logo ke splash screen ###
    icon_path = 'assets/search_icon.ico'
    splash_bg = 'assets/splash.png'
    try:
        if os.path.exists(icon_path):
            splash.iconbitmap(icon_path) # Set ikon untuk jendela splash
        if os.path.exists(splash_bg):
            img = Image.open(splash_bg).resize((splash_width, splash_height), Image.Resampling.LANCZOS)
            bg_image = ImageTk.PhotoImage(img)
            bg_label = tk.Label(splash_frame, image=bg_image, borderwidth=0)
            bg_label.image = bg_image
            bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        else:
            tk.Label(splash_frame, text="File Content Search Pro", font=("Segoe UI", 24, "bold"), bg="#2E2E2E", fg="#FFFFFF").pack(pady=(150, 10))
            tk.Label(splash_frame, text="Loading application...", font=("Segoe UI", 10), bg="#2E2E2E", fg="#CCCCCC").pack(pady=5)
    except Exception as e:
        print(f"Gagal memuat splash background: {e}")
        tk.Label(splash_frame, text="File Content Search Pro", font=("Segoe UI", 24, "bold"), bg="#2E2E2E", fg="#FFFFFF").pack(pady=(150, 10))

    progress = ttk.Progressbar(splash_frame, mode='indeterminate')
    progress.place(relx=0.5, rely=0.85, anchor="center", relwidth=0.7)
    progress.start(15)

    # Inisialisasi Settings & Bahasa
    settings = SettingsManager().load()
    set_language(settings.get('language', 'en'))

    def main_app_setup():
        splash.destroy()
        root.deiconify()
        app = FileSearchGUI(root, icon_path) # Kirim path ikon ke aplikasi utama
        root.protocol("WM_DELETE_WINDOW", app.on_close)

    root.after(3000, main_app_setup)
    root.mainloop()

if __name__ == "__main__":
    main()