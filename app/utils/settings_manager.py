import json
import os

class SettingsManager:
    def __init__(self, filename="search_settings.json"):
        self.filepath = filename

    def load(self):
        """Memuat pengaturan dari file JSON."""
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def save(self, settings_data):
        """Menyimpan pengaturan ke file JSON."""
        try:
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(settings_data, f, indent=4)
            return True
        except IOError as e:
            print(f"Error saving settings: {e}")
            return False