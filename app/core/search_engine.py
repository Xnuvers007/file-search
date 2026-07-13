import os
import fnmatch
import string
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
import queue
import textwrap
import logging
import threading

logger = logging.getLogger(__name__)

try:
    import fitz
    import docx
    import zipfile
except ImportError:
    fitz = None
    docx = None
    zipfile = None

try:
    import pytesseract
    from PIL import Image
    from PIL.ExifTags import TAGS
except ImportError:
    pytesseract = None
    Image = None

try:
    from whoosh.index import create_in, open_dir
    from whoosh.fields import Schema, TEXT, ID, NUMERIC
    from whoosh.qparser import QueryParser
except ImportError:
    create_in = None

try:
    from sentence_transformers import SentenceTransformer, util
    semantic_model = None  # Lazy load
except ImportError:
    SentenceTransformer = None

try:
    import mutagen
except ImportError:
    mutagen = None

try:
    import extract_msg
except ImportError:
    extract_msg = None

try:
    import ebooklib
    from ebooklib import epub
    from bs4 import BeautifulSoup
except ImportError:
    ebooklib = None
    
import email
from email.policy import default

class SearchEngine:
    def __init__(self, search_params, cancel_event):
        self.params = search_params
        self.cancel_event = cancel_event
        self.index_dir_base = os.path.join(os.path.expanduser("~"), ".file_search_pro_index")

    def _get_index_dir_for_path(self, search_path):
        import hashlib
        normalized_path = os.path.normpath(search_path).lower()
        path_hash = hashlib.md5(normalized_path.encode('utf-8')).hexdigest()
        return os.path.join(self.index_dir_base, path_hash)

    def build_index_for_path(self, search_path, ignore_folders, ignore_files, progress_callback):
        if not create_in:
            raise Exception("Whoosh is not installed. Please pip install Whoosh")
        
        index_dir = self._get_index_dir_for_path(search_path)
        if not os.path.exists(index_dir):
            os.makedirs(index_dir)
            
        schema = Schema(path=ID(stored=True, unique=True), name=TEXT(stored=True), content=TEXT, size=NUMERIC(stored=True), modified=NUMERIC(stored=True))
        ix = create_in(index_dir, schema)
        writer = ix.writer()
        
        # Temporary overwrite self.params for _collect_files to work
        old_params = getattr(self, 'params', None)
        self.params = {
            'search_paths': [search_path],
            'ignore_folders': ignore_folders,
            'ignore_files': ignore_files,
            'size_filters': None,
            'date_filters': None
        }
        
        # We need a cancel event if not provided
        old_cancel = getattr(self, 'cancel_event', None)
        if old_cancel is None:
            self.cancel_event = type('obj', (object,), {'is_set': lambda: False})
            
        try:
            all_files = self._collect_files(progress_callback)
            total = len(all_files)
            
            for i, file_path in enumerate(all_files):
                progress_callback(f"Indexing... {i+1}/{total}")
                try:
                    content = self._get_file_content(file_path)
                    if content:
                        stat = os.stat(file_path)
                        writer.add_document(path=file_path, name=os.path.basename(file_path), content=content, size=stat.st_size, modified=stat.st_mtime)
                except Exception as e:
                    logger.debug(f"Error indexing {file_path}: {e}")
                    continue
                    
            progress_callback("Committing index...")
            writer.commit()
            
        finally:
            # Restore state
            if old_params: self.params = old_params
            if old_cancel: self.cancel_event = old_cancel

    def run_search(self, progress_callback, result_callback, finish_callback):
        # 1. Cek apakah ada index untuk path yang dicari
        indexed_results_returned = False
        if len(self.params.get('search_paths', [])) == 1:
            search_path = self.params['search_paths'][0]
            index_dir = self._get_index_dir_for_path(search_path)
            
            # Jika indexing tersedia, tidak menggunakan regex, ocr, semantic (karena Whoosh berbasis teks murni)
            if os.path.exists(index_dir) and create_in and not self.params.get('regex') and not self.params.get('ocr') and not self.params.get('semantic'):
                try:
                    ix = open_dir(index_dir)
                    with ix.searcher() as searcher:
                        query_parser = QueryParser("content", ix.schema)
                        query = query_parser.parse(self.params['keyword'])
                        progress_callback(f"Searching index for {search_path}...")
                        results = searcher.search(query, limit=None)
                        for hit in results:
                            if self.cancel_event.is_set(): break
                            if not self._check_size(hit['size'], self.params.get('size_filters')): continue
                            if not self._check_date(hit['modified'], self.params.get('date_filters')): continue
                            
                            result_callback({"name": hit['name'], "path": hit['path'], "size": hit['size'], "modified": hit['modified']})
                    
                    if not self.cancel_event.is_set():
                        finish_callback()
                        return
                except Exception as e:
                    print(f"Index search failed, falling back to live search: {e}")

        all_files = self._collect_files(progress_callback)
        if self.cancel_event.is_set():
            finish_callback()
            return
            
        # Semantic Lazy Load
        if self.params.get('semantic') and SentenceTransformer is not None:
            global semantic_model
            if semantic_model is None:
                progress_callback("Loading AI Model (Mengunduh ~1GB pada pertama kali, mohon tunggu beberapa menit)...")
                semantic_model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')
            self.keyword_embedding = semantic_model.encode(self.params['keyword'], convert_to_tensor=True)
            
        use_ai_ocr = self.params.get('semantic') or self.params.get('ocr')
        
        if use_ai_ocr:
            ai_queue = queue.Queue()
            ai_worker_thread = threading.Thread(target=self._ai_worker, args=(ai_queue, progress_callback, result_callback))
            ai_worker_thread.start()
            
            with ThreadPoolExecutor(max_workers=self.params.get('max_workers', 4)) as executor:
                total = len(all_files)
                for i, file_path in enumerate(all_files):
                    if self.cancel_event.is_set():
                        break
                    progress_callback(f"Reading... {i+1}/{total}")
                    executor.submit(self._read_and_enqueue, file_path, ai_queue)
                    
            ai_queue.put(None) # Sentinel to stop worker
            ai_worker_thread.join()
        else:
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

    def _read_and_enqueue(self, file_path, q):
        if self.cancel_event.is_set(): return
        content = self._get_file_content(file_path)
        if content is not None:
            q.put((file_path, content))
            
    def _ai_worker(self, q, progress_callback, result_callback):
        while not self.cancel_event.is_set():
            item = q.get()
            if item is None:
                break
            file_path, content = item
            result = self._process_file_content(file_path, content)
            if result:
                result_callback(result)
            q.task_done()

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
        return self._process_file_content(file_path, content)

    def _process_file_content(self, file_path, content):
        if content is None: return None

        keyword = self.params['keyword']
        k, c = (keyword, content) if self.params.get('case_sensitive') else (keyword.lower(), content.lower())
        
        match = False
        try:
            if self.params.get('semantic') and SentenceTransformer is not None:
                # Limit to first 10,000 characters to prevent OOM
                c_limit = content[:10000]
                # Better chunking for long text using textwrap
                chunks = textwrap.wrap(c_limit, width=500, break_long_words=False) if len(c_limit) > 500 else [c_limit]
                chunk_embeddings = semantic_model.encode(chunks, convert_to_tensor=True)
                cos_scores = util.cos_sim(self.keyword_embedding, chunk_embeddings)[0]
                if max(cos_scores) > 0.65: # Threshold dinaikkan untuk akurasi > 90%
                    match = True
            elif self.params.get('regex'):
                match = bool(re.search(k, c, re.IGNORECASE if not self.params.get('case_sensitive') else 0))
            elif self.params.get('fuzzy'):
                try:
                    from thefuzz import fuzz
                    if fuzz.partial_ratio(keyword.lower(), content.lower()) >= 80:
                        match = True
                except ImportError:
                    pass
            elif self.params.get('whole_word'):
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
            if ext == ".zip" and self.params.get('archive'):
                import zipfile
                with zipfile.ZipFile(file_path, 'r') as zf:
                    for name in zf.infolist():
                        if not name.is_dir():
                            try: content += zf.read(name).decode('utf-8', 'ignore') + "\n"
                            except Exception as e:
                                logger.debug(f"Error reading zip entry {name} in {file_path}: {e}")
                                continue
            elif ext == ".tar" and self.params.get('archive'):
                import tarfile
                with tarfile.open(file_path, 'r:*') as tf:
                    for member in tf.getmembers():
                        if member.isreg():
                            f = tf.extractfile(member)
                            if f:
                                try: content += f.read().decode('utf-8', 'ignore') + "\n"
                                except Exception as e:
                                    logger.debug(f"Error reading tar member {member.name} in {file_path}: {e}")
                                    continue
            elif ext == ".pdf" and fitz:
                with fitz.open(file_path) as doc: content = "".join(page.get_text() for page in doc)
                if self.params.get('ocr') and pytesseract and not content.strip():
                     # if no text found, try OCR on the first page
                     with fitz.open(file_path) as doc:
                         if doc.page_count > 0:
                             pix = doc[0].get_pixmap()
                             img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                             content = pytesseract.image_to_string(img)
            elif ext == ".docx" and docx:
                doc = docx.Document(file_path)
                content = "\n".join(para.text for para in doc.paragraphs)
            elif ext in [".png", ".jpg", ".jpeg"] and self.params.get('ocr') and pytesseract:
                img = Image.open(file_path)
                content = pytesseract.image_to_string(img)
                # also extract EXIF
                exif_data = img.getexif()
                if exif_data:
                    for tag_id in exif_data:
                        tag = TAGS.get(tag_id, tag_id)
                        data = exif_data.get(tag_id)
                        if isinstance(data, bytes):
                            data = data.decode(errors='ignore')
                        content += f"\n{tag}: {data}"
            elif ext == ".mp3" and mutagen:
                audio = mutagen.File(file_path, easy=True)
                if audio:
                    for k, v in audio.items():
                        content += f"{k}: {', '.join(v)}\n"
            elif ext == ".eml":
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    msg = email.message_from_file(f, policy=default)
                    content = msg.get_body(preferencelist=('plain')).get_content() if msg.get_body(preferencelist=('plain')) else ""
                    content += f"\nSubject: {msg.get('subject', '')}\nFrom: {msg.get('from', '')}\nTo: {msg.get('to', '')}"
            elif ext == ".msg" and extract_msg:
                msg = extract_msg.Message(file_path)
                content = msg.body
                content += f"\nSubject: {msg.subject}\nFrom: {msg.sender}\nTo: {msg.to}"
                msg.close()
            elif ext == ".epub" and ebooklib:
                book = epub.read_epub(file_path)
                for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
                    soup = BeautifulSoup(item.get_body_content(), 'html.parser')
                    content += soup.get_text() + "\n"
            else:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read(10*1024*1024) # Read up to 10MB
            return content
        except Exception as e:
            logger.debug(f"Error reading {file_path}: {e}")
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