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

        if not self.books:
            print("No books could be loaded from the database.")

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
