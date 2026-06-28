import os
import json
import requests
from src.core.translation import tr

class Database:
    def __init__(self):
        # We don't take remote_url in init anymore, sync is handled by sync worker
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        # Determine where the initial default databases are located
        if os.path.exists('/usr/share/raf/database'):
            system_db_dir = '/usr/share/raf/database'
        else:
            system_db_dir = os.path.join(base_dir, 'database')
            
        # Always use a user-writable directory for dynamic database syncs
        self.database_dir = os.path.expanduser("~/.local/share/raf/database")
        os.makedirs(self.database_dir, exist_ok=True)
        
        # Copy default databases to user directory if they don't exist yet, or if the packaged system database is newer
        import shutil
        for file_name in ["fernus_drive.json", "publishers.json"]:
            user_file = os.path.join(self.database_dir, file_name)
            system_file = os.path.join(system_db_dir, file_name)
            
            should_copy = False
            if not os.path.exists(user_file) and os.path.exists(system_file):
                should_copy = True
            elif os.path.exists(user_file) and os.path.exists(system_file):
                # If system file is newer than the user's local synced copy, overwrite it
                if os.path.getmtime(system_file) > os.path.getmtime(user_file):
                    should_copy = True
                    
            if should_copy:
                try:
                    shutil.copy2(system_file, user_file)
                except Exception as e:
                    print(f"Failed to copy {file_name}: {e}")
            
        self.books = []
        self.load_books()

    def load_books(self):
        self.books = []
        
        # 1. Load fernus_drive.json
        fernus_path = os.path.join(self.database_dir, 'fernus_drive.json')
        if os.path.exists(fernus_path):
            try:
                with open(fernus_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, dict) and "books" in data:
                        self.books.extend(data["books"])
                    elif isinstance(data, list):
                        self.books.extend(data)
            except Exception as e:
                print(tr("log.error_fernus", error=e))
                
        # 2. Load publishers.json
        pubs_path = os.path.join(self.database_dir, 'publishers.json')
        if os.path.exists(pubs_path):
            try:
                with open(pubs_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, dict) and "books" in data:
                        self.books.extend(data["books"])
                    elif isinstance(data, list):
                        self.books.extend(data)
            except Exception as e:
                print(tr("log.error_publishers", error=e))

        # 3. Load user sideloaded apps
        from src.core.config import CONFIG_PATH
        self.sideload_path = os.path.join(os.path.dirname(CONFIG_PATH), 'sideloaded.json')
        if os.path.exists(self.sideload_path):
            try:
                with open(self.sideload_path, 'r', encoding='utf-8') as f:
                    sideloaded = json.load(f)
                    self.books.extend(sideloaded)
            except Exception as e:
                print(tr("log.error_sideloaded", error=e))

        if not self.books:
            print(tr("log.no_books_loaded"))

    def add_sideloaded_book(self, book):
        """Appends a new sideloaded book to the local sideloaded.json file and current session."""
        self.books.append(book)
        
        # Load existing
        sideloaded = []
        if hasattr(self, 'sideload_path') and os.path.exists(self.sideload_path):
            try:
                with open(self.sideload_path, 'r', encoding='utf-8') as f:
                    sideloaded = json.load(f)
            except Exception:
                pass
                
        # Update or append
        existing = next((b for b in sideloaded if b['id'] == book['id']), None)
        if existing:
            existing.update(book)
        else:
            sideloaded.append(book)
            
        # Save
        if hasattr(self, 'sideload_path'):
            os.makedirs(os.path.dirname(self.sideload_path), exist_ok=True)
            with open(self.sideload_path, 'w', encoding='utf-8') as f:
                json.dump(sideloaded, f, indent=2)

    def remove_sideloaded_book(self, book_id):
        """Removes a sideloaded book from the local sideloaded.json file and current session."""
        self.books = [b for b in self.books if b['id'] != book_id]
        
        sideloaded = []
        if hasattr(self, 'sideload_path') and os.path.exists(self.sideload_path):
            try:
                with open(self.sideload_path, 'r', encoding='utf-8') as f:
                    sideloaded = json.load(f)
            except Exception:
                pass
                
        new_sideloaded = [b for b in sideloaded if b['id'] != book_id]
        
        if hasattr(self, 'sideload_path'):
            with open(self.sideload_path, 'w', encoding='utf-8') as f:
                json.dump(new_sideloaded, f, indent=2)

    def get_all_books(self):
        return self.books

    def search_books(self, query):
        if not query:
            return self.books
        query = query.lower()
        results = []
        for book in self.books:
            if (query in book['title'].lower() or 
                query in book['publisher'].lower() or 
                query in book.get('description', '').lower()):
                results.append(book)
        return results
