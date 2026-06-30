import os
import subprocess
import hashlib
from typing import Optional
from docx import Document
from fpdf import FPDF
from qdrant_client import QdrantClient
from qdrant_client.http import models as rest
from sentence_transformers import SentenceTransformer

import configs
import core.parsers as parsers
import core.creators as creators



WORKSPACE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'workspace')
MODEL = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

PARSERS = {".txt": parsers.parse_txt, ".pdf": parsers.parse_pdf, ".docx": parsers.parse_docx}
CREATORS = {".txt": creators.create_txt_file, ".docx": creators.create_docx_file, ".pdf": creators.create_pdf_file}

def open_file_on_computer(filepath):
    try:
        os.startfile(filepath) if os.name == 'nt' else subprocess.run(['xdg-open', filepath])
        return True
    except: return False

class FileDescriptionManager:
    def __init__(self, folder_path: str):
        self.folder_path = folder_path
        self.qdrant = QdrantClient(":memory:")
        self.qdrant.recreate_collection("files", rest.VectorParams(size=384, distance=rest.Distance.COSINE))
        self._index_all_filenames()

    def _index_all_filenames(self):
        #Индексирует все файлы в папке при запуске
        self.file_names = {}
        for fname in os.listdir(self.folder_path):
            if (ext := os.path.splitext(fname)[1].lower()) in PARSERS:
                path = os.path.join(self.folder_path, fname)
                if os.path.isfile(path):  # Убедимся, что это файл
                    self.file_names[fname] = fname
                    vector = MODEL.encode(fname).tolist()  # Только имя файла
                    file_id = hashlib.md5(fname.encode()).hexdigest()
                    self.qdrant.upsert("files", [rest.PointStruct(id=file_id,
                                                                  vector=vector, payload={"filename": fname})])
        print(f"[INFO] Проиндексировано {len(self.file_names)} имён файлов.")

    def add_file_to_index(self, filename: str):
        #Добавляет один файл в индекс (для отслеживания новых)
        if (ext := os.path.splitext(filename)[1].lower()) in PARSERS:
            vector = MODEL.encode(filename).tolist()
            file_id = hashlib.md5(filename.encode()).hexdigest()
            self.qdrant.upsert("files", [rest.PointStruct(id=file_id,
                                                          vector=vector, payload={"filename": filename})])
            self.file_names[filename] = filename
            print(f"[INFO] Индексирован новый файл: {filename}")

    def remove_file_from_index(self, filename: str):
        #Удаляет один файл из индекса (для отслеживания удалений)
        if filename in self.file_names:
            # Удаляем из Qdrant по ID (как мы его генерировали)
            file_id = hashlib.md5(filename.encode()).hexdigest()
            # QdrantClient.delete() удаляет точки по списку ID
            self.qdrant.delete(collection_name="files", points_selector=[file_id]) #даляем из словаря
            del self.file_names[filename]
            print(f"[INFO] Удалён из индекса файл: {filename}")
        else: print(f"[WARNING] Файл {filename} не найден в индексе для удаления.")

    def find_file_by_description(self, description: str) -> Optional[str]:
        query_vec = MODEL.encode(description).tolist()
        res = self.qdrant.search("files", query_vec, limit=1)
        return res[0].payload["filename"] if res and res[0].score > 0.1 else None


class FileManager:
    def __init__(self):
        self.desc_manager = FileDescriptionManager(WORKSPACE)
        # Запускаем отслеживание файлов
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler

        class Handler(FileSystemEventHandler):
            def __init__(self, fm):
                self.fm = fm

            def on_created(self, event):
                if not event.is_directory:
                    _, ext = os.path.splitext(event.src_path)
                    if ext.lower() in PARSERS:
                        # Извлекаем имя файла из пути
                        filename = os.path.basename(event.src_path)
                        self.fm.desc_manager.add_file_to_index(filename)
                        
            def on_deleted(self, event):
                if not event.is_directory:
                    _, ext = os.path.splitext(event.src_path)
                    if ext.lower() in PARSERS:
                        filename = os.path.basename(event.src_path)
                        self.fm.desc_manager.remove_file_from_index(filename)

        self.observer = Observer()
        self.observer.schedule(Handler(self), WORKSPACE, recursive=False)
        self.observer.start()


    def run(self, params: dict, chat_id: str):

        if params.get("action") == "open_file":
            name = params.get("name")
            # Если name не указан, ищем по описанию
            if not name:
                description = params.get("description", "")
                if description: filename = self.desc_manager.find_file_by_description(description)
                else: return {"error": "Не указано ни имя, ни описание файла для открытия"}
            else:
                # Если указано name, используем его напрямую (если extension не указано, ищем любой)
                ext = params.get("extension", "")
                if ext:
                    if not ext.startswith('.'): ext = '.' + ext
                    filename = name + ext
                else:
                    # Если extension не указан, ищем файл с любым подходящим расширением
                    found = False
                    for allowed_ext in PARSERS.keys():
                        potential_name = name + allowed_ext
                        if os.path.exists(os.path.join(WORKSPACE, potential_name)):
                            filename = potential_name
                            found = True
                            break
                    if not found: return {"error": f"Файл с именем {name} и допустимым расширением не найден"}
            
            if not filename: return {"error": "Файл не найден по описанию"}
            filepath = os.path.join(WORKSPACE, filename)
            if not os.path.exists(filepath): return {"error": "Файл не существует"}
            open_file_on_computer(filepath)
            return {"status": "ok", "filename": filename, "content": PARSERS[os.path.splitext(filename)[1].lower()](filepath)}
        
        elif params.get("action") == "create_file":
            name = params.get("name")
            ext = params.get("extension", "")
            if not name or not ext: return {"error": "Не указано имя файла или расширение"}
            if not ext.startswith('.'): ext = '.' + ext
            filename = name + ext
            filepath = os.path.join(WORKSPACE, filename)
            if os.path.exists(filepath): return {"error": "Файл уже существует"}
            creator_func = CREATORS.get(ext.lower())
            if not creator_func: return {"error": f"Неподдерживаемое расширение: {ext}"}
            creator_func(filepath, params.get("content", ""))
            # Добавляем созданный файл в индекс
            self.desc_manager(filename)
            return {"status": "ok", "filename": filename}
        return {"error": "Неизвестное действие"}


    def stop(self):
        """Останавливает отслеживание файлов."""
        self.observer.stop()
        self.observer.join()