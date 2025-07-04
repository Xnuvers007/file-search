import os
import fnmatch
import string
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import re

try:
    import fitz
    import docx
    import zipfile
except ImportError:
    pass

class SearchEngine:
    def __init__(self, search_params, cancel_event):
        self.params = search_params
        self.cancel_event = cancel_event

    def run_search(self, progress_callback, result_callback, finish_callback):
        all_files = self._collect_files(progress_callback)
        if self.cancel_event.is_set():
            finish_callback()
            return
            
        with ThreadPoolExecutor(max_workers=self.params.get('max_workers', 4)) as executor:
            future_to_file = {executor.submit(self._process_file, f): f for f in all_files}
            
            total = len(all_files)
            for i, future in enumerate(as_completed(future_to_file)):
                if self.cancel_event.is_set():
                    break
                
                progress_callback(f"Scanning... {i+1}/{total}")
                result = future.result()
                if result:
                    result_callback(result)
        
        finish_callback()

    def _collect_files(self, progress_callback):
        files_to_scan = []
        search_paths = self.params['search_paths']
        
        for path in search_paths:
            if not os.path.isdir(path): continue
            try:
                for root, dirs, filenames in os.walk(path, topdown=True):
                    if self.cancel_event.is_set(): return []
                    
                    progress_callback(f"Collecting in: {os.path.basename(root)}")
                    
                    dirs[:] = [d for d in dirs if d not in self.params['ignore_folders']]
                    
                    for filename in filenames:
                        if any(fnmatch.fnmatch(filename, pattern) for pattern in self.params['ignore_files']):
                            continue
                        
                        file_path = os.path.join(root, filename)
                        try:
                            stat_info = os.stat(file_path)
                            if not self._check_size(stat_info.st_size, self.params['size_filters']): continue
                            if not self._check_date(stat_info.st_mtime, self.params['date_filters']): continue
                            files_to_scan.append(file_path)
                        except OSError:
                            continue
            except Exception:
                continue # Skip inaccessible drives/folders
        return files_to_scan

    def _process_file(self, file_path):
        content = self._get_file_content(file_path)
        if content is None: return None

        keyword = self.params['keyword']
        k, c = (keyword, content) if self.params['case_sensitive'] else (keyword.lower(), content.lower())
        
        match = False
        try:
            if self.params['regex']:
                match = bool(re.search(k, c, re.IGNORECASE if not self.params['case_sensitive'] else 0))
            elif self.params['whole_word']:
                match = bool(re.search(r'\b' + re.escape(k) + r'\b', c))
            elif k in c:
                match = True
        except Exception:
            return None
            
        if match:
            stat = os.stat(file_path)
            return {"name": os.path.basename(file_path), "path": file_path, "size": stat.st_size, "modified": stat.st_mtime}
        return None

    def _get_file_content(self, file_path):
        ext = os.path.splitext(file_path)[1].lower()
        content = ""
        try:
            if ext == ".zip":
                with zipfile.ZipFile(file_path, 'r') as zf:
                    for name in zf.infolist():
                        if not name.is_dir():
                            try: content += zf.read(name).decode('utf-8', 'ignore') + "\n"
                            except (zipfile.BadZipFile, UnicodeDecodeError): continue
            elif ext == ".pdf" and fitz:
                with fitz.open(file_path) as doc: content = "".join(page.get_text() for page in doc)
            elif ext == ".docx" and docx:
                doc = docx.Document(file_path)
                content = "\n".join(para.text for para in doc.paragraphs)
            else:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read(10*1024*1024) # Read up to 10MB
            return content
        except Exception:
            return None

    def _check_size(self, file_size, filters):
        if not filters: return True
        op, val = filters['op'], filters['val']
        if op == 'greater than': return file_size > val
        if op == 'less than': return file_size < val
        return True

    def _check_date(self, mod_timestamp, filters):
        if not filters: return True
        mod_dt = datetime.fromtimestamp(mod_timestamp)
        after_ok = not filters['after'] or mod_dt > filters['after']
        before_ok = not filters['before'] or mod_dt < filters['before']
        return after_ok and before_ok