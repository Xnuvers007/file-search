# app/utils/i18n.py

class I18n:
    def __init__(self):
        self.languages = {
            'en': 'English',
            'id': 'Bahasa Indonesia'
        }
        self.current_lang = 'en'
        self.translations = {
            'en': {},
            'id': {
                'Search Configuration': 'Konfigurasi Pencarian',
                'Keyword:': 'Kata Kunci:',
                'Path:': 'Lokasi:',
                'Case Sensitive': 'Peka Huruf',
                'Whole Word': 'Kata Utuh',
                'Regex': 'Reguler Ekspresi',
                'OCR (Images)': 'OCR (Gambar)',
                'Semantic (AI)': 'Semantik (AI)',
                'Fuzzy': 'Samar (Fuzzy)',
                'Archives': 'Arsip (ZIP)',
                'Browse': 'Cari...',
                'All Drives': 'Semua Drive',
                'Filters & Performance': 'Filter & Performa',
                'Size:': 'Ukuran:',
                'Date Modified:': 'Tgl Diubah:',
                'After:': 'Setelah:',
                'Before:': 'Sebelum:',
                'Ignore Folders:': 'Abaikan Folder:',
                'Ignore Files:': 'Abaikan File:',
                'Max Workers:': 'Pekerja Maks:',
                'AI Queue Size:': 'Antrean AI:',
                'Auto-save Results': 'Simpan Otomatis',
                'Start Search': 'Mulai Pencarian',
                'Build Index': 'Bangun Indeks',
                'Cancel': 'Batal',
                'Show Analytics': 'Lihat Analitik',
                'Export CSV': 'Ekspor CSV',
                'Saved Searches:': 'Pencarian Tersimpan:',
                'Save Current': 'Simpan Saat Ini',
                'Delete': 'Hapus',
                'File Name': 'Nama File',
                'Full Path': 'Lokasi Penuh',
                'Size': 'Ukuran',
                'Last Modified': 'Terakhir Diubah',
                'Content Preview': 'Pratinjau Konten',
                'Find Next': 'Cari Berikutnya',
                'Close': 'Tutup',
                'Ready': 'Siap',
                'File': 'Berkas',
                'Open Search Location': 'Buka Lokasi Pencarian',
                'Save Results': 'Simpan Hasil',
                'Exit': 'Keluar',
                'Settings': 'Pengaturan',
                'Theme': 'Tema',
                'Language (Requires Restart)': 'Bahasa (Butuh Restart)',
                'Donate / Support': 'Donasi / Dukungan',
                'Help': 'Bantuan',
                'Check for Updates': 'Periksa Pembaruan',
                'About': 'Tentang',
                'Open File Location': 'Buka Lokasi File',
                'Copy Selected Path(s)': 'Salin Path Terpilih',
                'Move to...': 'Pindahkan ke...',
                'Copy to...': 'Salin ke...',
                'Compress to ZIP': 'Kompres ke ZIP',
                'Delete Permanently': 'Hapus Permanen',
                'Custom...': 'Kustom...',
                'Membaca dan merender teks dari file...': 'Membaca dan merender teks dari file...',
                'Cannot preview this file type or file is empty.': 'Tidak dapat mempratinjau jenis file ini atau file kosong.',
                'Error': 'Galat',
                'Search cancelled. Found {} file(s) in {:.2f}s.': 'Pencarian dibatalkan. Menemukan {} file dalam {:.2f}d.',
                'Search complete. Found {} file(s) in {:.2f}s.': 'Pencarian selesai. Menemukan {} file dalam {:.2f}d.',
                'No files found matching your criteria.': 'Tidak ada file yang sesuai kriteria.',
                'Search Complete': 'Pencarian Selesai'
            }
        }
    
    def set_language(self, lang_code):
        if lang_code in self.languages:
            self.current_lang = lang_code
            
    def get(self, text, *args):
        if self.current_lang == 'en':
            translated = text
        else:
            translated = self.translations.get(self.current_lang, {}).get(text, text)
            
        if args:
            try:
                return translated.format(*args)
            except:
                return translated
        return translated

# Global instance
_i18n_instance = I18n()

def _(text, *args):
    return _i18n_instance.get(text, *args)

def set_language(lang):
    _i18n_instance.set_language(lang)
    
def get_languages():
    return _i18n_instance.languages
def get_current_language():
    return _i18n_instance.current_lang
