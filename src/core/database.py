import os
import json
import requests

class Database:
    def __init__(self):
        # We don't take remote_url in init anymore, sync is handled by sync worker
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        # Check if installed system-wide or running from dev directory
        if os.path.exists('/usr/share/raf/database'):
            self.database_dir = '/usr/share/raf/database'
        else:
            self.database_dir = os.path.join(base_dir, 'database')
            
        self.books = []
        self.load_books()

    def load_books(self):
        self.books = []
        
        # 1. Load fernus_drive.json
        fernus_path = os.path.join(self.database_dir, 'fernus_drive.json')
        if os.path.exists(fernus_path):
            try:
                with open(fernus_path, 'r', encoding='utf-8') as f:
                    self.books.extend(json.load(f))
            except Exception as e:
                print(f"Error loading fernus_drive.json: {e}")
                
        # 2. Load publishers.json
        pubs_path = os.path.join(self.database_dir, 'publishers.json')
        if os.path.exists(pubs_path):
            try:
                with open(pubs_path, 'r', encoding='utf-8') as f:
                    self.books.extend(json.load(f))
            except Exception as e:
                print(f"Error loading publishers.json: {e}")

        # 3. Load user sideloaded apps
        from src.core.config import CONFIG_PATH
        self.sideload_path = os.path.join(os.path.dirname(CONFIG_PATH), 'sideloaded.json')
        if os.path.exists(self.sideload_path):
            try:
                with open(self.sideload_path, 'r', encoding='utf-8') as f:
                    sideloaded = json.load(f)
                    self.books.extend(sideloaded)
            except Exception as e:
                print(f"Error loading sideloaded.json: {e}")

        if not self.books:
            print("No books could be loaded from the database.")

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
