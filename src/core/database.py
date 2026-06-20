import os
import json
import requests

class Database:
    def __init__(self, remote_url=None):
        self.remote_url = remote_url
        self.local_json_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'assets',
            'books.json'
        )
        self.books = []
        self.load_books()

    def load_books(self):
        # Attempt to load from remote url first if specified
        if self.remote_url:
            try:
                response = requests.get(self.remote_url, timeout=5)
                if response.status_code == 200:
                    self.books = response.json()
                    # Cache it locally
                    with open(self.local_json_path, 'w', encoding='utf-8') as f:
                        json.dump(self.books, f, ensure_ascii=False, indent=2)
                    return
            except Exception as e:
                print(f"Error loading remote database: {e}. Falling back to local.")

        # Fallback to local books.json
        if os.path.exists(self.local_json_path):
            try:
                with open(self.local_json_path, 'r', encoding='utf-8') as f:
                    self.books = json.load(f)
            except Exception as e:
                print(f"Error loading local books.json: {e}")
                self.books = []
        else:
            print("Local books.json not found.")
            self.books = []

        # Dynamically assign category to each book
        for book in self.books:
            title = book.get('title', '').lower()
            publisher = book.get('publisher', '').lower()
            desc = book.get('description', '').lower()
            
            # Keywords matching
            if any(k in title or k in publisher or k in desc for k in [
                "ilkokul", "4. sınıf", "3. sınıf", "2. sınıf", "1. sınıf", "okul öncesi",
                "mavi deniz", "çalışkan arı", "berkay", "key yayın", "üçgen"
            ]):
                book['category'] = "İlkokul"
            elif any(k in title or k in publisher or k in desc for k in [
                "ortaokul", "lgs", "8. sınıf", "7. sınıf", "6. sınıf", "5. sınıf",
                "hız", "çanta", "fenomen", "arı yayın", "günay", "mozaik", "ata"
            ]):
                book['category'] = "Ortaokul"
            elif any(k in title or k in publisher or k in desc for k in [
                "lise", "yks", "ayt", "tyt", "12. sınıf", "11. sınıf", "10. sınıf", "9. sınıf",
                "endemik", "esen", "limit", "kondisyon", "ordinat", "tammat", "puza", "toprak", "rasyonel", "fi yayın"
            ]):
                book['category'] = "Lise"
            else:
                book['category'] = "Genel"

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
