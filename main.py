# main.py
import tkinter as tk
from tkinter import ttk, messagebox
from app.gui.main_window import FileSearchGUI

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

    splash_width, splash_height = 400, 250 # Perbesar sedikit untuk logo
    screen_width, screen_height = root.winfo_screenwidth(), root.winfo_screenheight()
    x = (screen_width // 2) - (splash_width // 2)
    y = (screen_height // 2) - (splash_height // 2)
    splash.geometry(f'{splash_width}x{splash_height}+{x}+{y}')

    splash_frame = tk.Frame(splash, bg="#2E2E2E", relief="ridge", borderwidth=2)
    splash_frame.pack(expand=True, fill="both")
    
    # ### PERUBAHAN DI SINI: Menambahkan logo ke splash screen ###
    icon_path = 'assets/search_icon.ico'
    try:
        splash.iconbitmap(icon_path) # Set ikon untuk jendela splash
        img = Image.open(icon_path).resize((64, 64), Image.Resampling.LANCZOS)
        logo = ImageTk.PhotoImage(img)
        logo_label = tk.Label(splash_frame, image=logo, bg="#2E2E2E")
        logo_label.image = logo # Simpan referensi agar tidak di-garbage collect
        logo_label.pack(pady=(20, 10))
    except Exception as e:
        print(f"Gagal memuat logo: {e}")
        # Tetap tampilkan label teks jika logo gagal dimuat
        tk.Label(splash_frame, text="🔍", font=("Segoe UI", 36, "bold"), bg="#2E2E2E", fg="#FFFFFF").pack(pady=(20,10))

    tk.Label(splash_frame, text="File Content Search Pro", font=("Segoe UI", 16, "bold"), bg="#2E2E2E", fg="#FFFFFF").pack()
    tk.Label(splash_frame, text="Loading application...", font=("Segoe UI", 9), bg="#2E2E2E", fg="#CCCCCC").pack(pady=5)
    progress = ttk.Progressbar(splash_frame, mode='indeterminate')
    progress.pack(pady=10, padx=40, fill="x")
    progress.start(15)

    def main_app_setup():
        splash.destroy()
        root.deiconify()
        app = FileSearchGUI(root, icon_path) # Kirim path ikon ke aplikasi utama
        root.protocol("WM_DELETE_WINDOW", app.on_close)

    root.after(3000, main_app_setup)
    root.mainloop()

if __name__ == "__main__":
    main()