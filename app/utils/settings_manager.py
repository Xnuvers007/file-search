import json
import os

class SettingsManager:
    def __init__(self, filename="search_settings.json"):
        # Menyimpan pengaturan di home directory (AppData) agar tidak terkena blokir hak akses di Program Files
        home_dir = os.path.join(os.path.expanduser("~"), ".file_search_pro")
        if not os.path.exists(home_dir):
            os.makedirs(home_dir, exist_ok=True)
        self.filepath = os.path.join(home_dir, filename)

    def load(self):
        """Memuat pengaturan dari file JSON."""
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {
            'theme': 'Light',
            'history': [],
            'case': False,
            'whole': False,
            'regex': False,
            'ocr': False,
            'semantic': False,
            'ai_queue_size': 50,
            'autosave': True,
            'ignore_folders': '.git, .svn, .vscode, .idea, __pycache__, node_modules, venv, env, build, dist, temp, tmp, $RECYCLE.BIN, System Volume Information',
            'ignore_files': '*.log, *.tmp, *.bak, .DS_Store, thumbs.db',
            'saved_searches': {},
            'language': 'en'
        }
        return {
            'theme': 'Light',
            'history': [],
            'case': False,
            'whole': False,
            'regex': False,
            'ocr': False,
            'semantic': False,
            'ai_queue_size': 50,
            'autosave': True,
            'ignore_folders': '.git, .svn, .vscode, .idea, __pycache__, node_modules, venv, env, build, dist, temp, tmp, $RECYCLE.BIN, System Volume Information',
            'ignore_files': '*.log, *.tmp, *.bak, .DS_Store, thumbs.db',
            'saved_searches': {},
            'language': 'en'
        }

    def save(self, settings_data):
        """Menyimpan pengaturan ke file JSON."""
        try:
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(settings_data, f, indent=4)
            return True
        except IOError as e:
            print(f"Error saving settings: {e}")
            return False