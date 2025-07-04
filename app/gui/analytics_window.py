# app/gui/analytics_window.py
import tkinter as tk
from tkinter import ttk, messagebox
import os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
import numpy as np
from matplotlib.colors import LinearSegmentedColormap

# Perubahan untuk memindahkan tombol Close ke bagian atas

class AnalyticsWindow(tk.Toplevel):
    def __init__(self, parent, results_data, theme_dict, icon_path=None):
        super().__init__(parent)
        self.title("Search Analytics Dashboard")
        self.geometry("1200x700")
        self.state('zoomed')

        # Set ikon jendela
        if icon_path and os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except tk.TclError:
                pass
        
        self.transient(parent)
        self.grab_set()
        
        if not results_data:
            self.destroy()
            messagebox.showinfo("No Data", "No results to analyze.", parent=parent)
            return
        
        # Konfigurasi tema untuk jendela
        self.configure(bg=theme_dict['bg'])
        
        # Persiapkan data
        df = pd.DataFrame(results_data)
        df['ext'] = df['path'].apply(lambda x: os.path.splitext(x)[1].lower() if os.path.splitext(x)[1] else '.no_ext')
        df['folder'] = df['path'].apply(lambda x: os.path.dirname(x))
        df['filename'] = df['path'].apply(lambda x: os.path.basename(x))
        df['size_kb'] = df['size'].apply(lambda x: x/1024 if x else 0)
        
        # Konfigurasi warna untuk plot
        is_dark = self._is_dark_color(theme_dict['bg'])
        fig_bg_color = theme_dict['bg']
        fig_fg_color = theme_dict['fg']
        
        # Custom colormap berdasarkan tema
        if is_dark:
            cmap_colors = ['#1e88e5', '#26c6da', '#8e24aa', '#43a047', '#ffb300', '#d81b60', '#5e35b1', '#00acc1', '#7cb342', '#fb8c00']
            accent_color = '#00bcd4'
        else:
            cmap_colors = ['#2196f3', '#00bcd4', '#673ab7', '#4caf50', '#ffc107', '#e91e63', '#3f51b5', '#009688', '#8bc34a', '#ff9800']
            accent_color = '#1976d2'
        
        custom_cmap = LinearSegmentedColormap.from_list('custom_cmap', cmap_colors)
        
        # Set parameter global matplotlib
        plt.rcParams.update({
            'text.color': fig_fg_color,
            'axes.labelcolor': fig_fg_color,
            'xtick.color': fig_fg_color,
            'ytick.color': fig_fg_color,
            'figure.facecolor': fig_bg_color,
            'axes.facecolor': fig_bg_color,
            'font.family': 'Arial',
            'font.size': 10
        })
        
        # --- PERUBAHAN: Header dengan tombol Close di atas ---
        header_frame = ttk.Frame(self)
        header_frame.pack(fill=tk.X, padx=15, pady=(15, 5))
        
        # Judul dashboard
        title_label = ttk.Label(header_frame, text="Search Results Analytics", style="DashboardTitle.TLabel")
        title_label.pack(side=tk.LEFT, padx=5)
        
        # Tombol Close di kanan atas
        close_btn = ttk.Button(header_frame, text="Close", command=self.destroy, style="Accent.TButton", width=10)
        close_btn.pack(side=tk.RIGHT, padx=5)
        
        # --- Stats row ---
        stats_frame = ttk.Frame(self)
        stats_frame.pack(fill=tk.X, padx=15, pady=(10, 15))
        
        total_files = len(df)
        total_size = df['size'].sum() / (1024*1024)  # MB
        unique_exts = df['ext'].nunique()
        
        stats = [
            {"label": "Total Files", "value": f"{total_files:,}"},
            {"label": "Total Size", "value": f"{total_size:.2f} MB"},
            {"label": "File Types", "value": f"{unique_exts}"},
            {"label": "Folders", "value": f"{df['folder'].nunique()}"}
        ]
        
        for i, stat in enumerate(stats):
            stat_frame = ttk.Frame(stats_frame)
            stat_frame.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=10)
            
            ttk.Label(stat_frame, text=stat["label"], style="Dashboard.TLabel").pack(anchor=tk.CENTER)
            ttk.Label(stat_frame, text=stat["value"], style="DashboardValue.TLabel").pack(anchor=tk.CENTER)
        
        # Frame utama untuk grafik
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # --- Grafik Distribusi Ekstensi File ---
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        fig1 = plt.Figure(figsize=(6, 5), dpi=100, facecolor=fig_bg_color)
        ax1 = fig1.add_subplot(111)
        
        ext_counts = df['ext'].value_counts().nlargest(8)
        wedges, texts, autotexts = ax1.pie(
            ext_counts, 
            autopct='%1.1f%%', 
            startangle=90,
            textprops={'color': 'white' if is_dark else 'black', 'fontweight': 'bold'},
            wedgeprops={'width': 0.5, 'edgecolor': fig_bg_color},
            colors=cmap_colors[:len(ext_counts)]
        )
        
        # Doughnut chart dengan lingkaran di tengah
        centre_circle = plt.Circle((0, 0), 0.25, fc=fig_bg_color)
        ax1.add_patch(centre_circle)
        
        # Tambahkan legenda dengan kotak warna
        legend_labels = [f"{ext} ({count:,})" for ext, count in zip(ext_counts.index, ext_counts.values)]
        ax1.legend(
            wedges, 
            legend_labels, 
            title="File Extensions", 
            loc="center left",
            bbox_to_anchor=(0.9, 0, 0.5, 1),
            fontsize=9,
            frameon=True,
            facecolor=fig_bg_color,
            labelcolor=fig_fg_color,
            title_fontsize=10
        )
        
        ax1.set_title("File Type Distribution", fontsize=12, fontweight='bold', pad=20)
        
        # Tambahkan teks di tengah doughnut
        ax1.text(0, 0, f"{total_files}\nFiles", 
                ha='center', va='center', fontsize=11, fontweight='bold',
                color=fig_fg_color)
        
        fig1.tight_layout()
        canvas1 = FigureCanvasTkAgg(fig1, master=left_frame)
        canvas1.draw()
        canvas1.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # --- Grafik Folder ---
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        fig2 = plt.Figure(figsize=(6, 5), dpi=100, facecolor=fig_bg_color)
        ax2 = fig2.add_subplot(111)
        
        folder_counts = df['folder'].value_counts().nlargest(8)
        folder_short_names = [os.path.basename(folder) or folder for folder in folder_counts.index]
        
        # Horizontal bar chart dengan warna gradient
        bars = ax2.barh(
            range(len(folder_counts)), 
            folder_counts.values,
            color=cmap_colors[:len(folder_counts)],
            alpha=0.8,
            height=0.6,
            edgecolor=fig_bg_color,
            linewidth=1
        )
        
        # Tambahkan nilai di sebelah kanan bar
        for i, (bar, value) in enumerate(zip(bars, folder_counts.values)):
            ax2.text(
                bar.get_width() + (max(folder_counts.values) * 0.02),
                bar.get_y() + bar.get_height()/2,
                f"{value:,}",
                va='center',
                fontweight='bold',
                color=fig_fg_color,
                fontsize=9
            )
        
        # Custom y-tick labels dengan tooltips
        ax2.set_yticks(range(len(folder_counts)))
        ax2.set_yticklabels(folder_short_names)
        
        # Simpan path folder lengkap sebagai properti untuk tooltip
        for i, full_path in enumerate(folder_counts.index):
            bars[i].full_path = full_path
        
        # Tambahkan grid horizontal
        ax2.grid(axis='x', linestyle='--', alpha=0.3)
        
        # Hapus border spines
        ax2.spines['top'].set_visible(False)
        ax2.spines['right'].set_visible(False)
        ax2.spines['bottom'].set_visible(True)
        ax2.spines['left'].set_visible(True)
        
        ax2.set_title("Files per Folder", fontsize=12, fontweight='bold', pad=20)
        ax2.set_xlabel("Number of Files", fontweight='bold', labelpad=10)
        
        fig2.tight_layout()
        canvas2 = FigureCanvasTkAgg(fig2, master=right_frame)
        canvas2.draw()
        canvas2.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Konfigurasi gaya untuk widget
        self._configure_styles(theme_dict, accent_color)
    
    def _is_dark_color(self, hex_color):
        """Menentukan apakah warna latar termasuk gelap atau terang"""
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        brightness = (r * 299 + g * 587 + b * 114) / 1000
        return brightness < 128
    
    def _configure_styles(self, theme_dict, accent_color):
        """Konfigurasi gaya untuk widget"""
        style = ttk.Style()
        
        # Gaya untuk judul dashboard
        style.configure("DashboardTitle.TLabel", 
                        font=("Arial", 18, "bold"),
                        background=theme_dict['bg'],
                        foreground=theme_dict['fg'])
        
        # Gaya untuk label dashboard
        style.configure("Dashboard.TLabel", 
                        font=("Arial", 10),
                        background=theme_dict['bg'],
                        foreground=theme_dict['fg'])
        
        # Gaya untuk nilai dashboard
        style.configure("DashboardValue.TLabel", 
                        font=("Arial", 14, "bold"),
                        background=theme_dict['bg'],
                        foreground=accent_color)
        
        # Gaya untuk tombol
        style.configure("Accent.TButton",
                        font=("Arial", 10, "bold"),
                        background=accent_color,
                        foreground="white")