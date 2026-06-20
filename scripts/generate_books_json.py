import os
import json
import re

# Resolve paths relative to this script's directory
script_dir = os.path.dirname(os.path.abspath(__file__))
drive_files_path = os.path.join(script_dir, 'drive_files.json')
books_json_path = os.path.join(os.path.dirname(script_dir), 'src', 'assets', 'books.json')

with open(drive_files_path, 'r', encoding='utf-8') as f:
    files = json.load(f)

# Helper function to split camel case
def split_camel_case(s):
    return re.sub(r'(?<!^)(?=[A-Z])', ' ', s)

# Mappings to beautify titles and publishers
turkish_map = {
    "AkademikBasariYayinlari": "Akademik Başarı Yayınları",
    "Ankara": "Ankara Yayıncılık",
    "Ari": "Arı Yayıncılık",
    "Ata": "Ata Yayıncılık",
    "AvantajPerakende": "Avantaj Perakende",
    "BerkayYayinlari": "Berkay Yayınları",
    "Bilfen": "Bilfen Yayıncılık",
    "BirikimYayinlari": "Birikim Yayınları",
    "CaliskanAriYayinlari": "Çalışkan Arı Yayınları",
    "Canta": "Çanta Yayıncılık",
    "DataYayinlari": "Data Yayınları",
    "DuyuYayinlari": "Duyu Yayınları",
    "EkspertYayinlari": "Ekspert Yayınları",
    "Endemik": "Endemik Yayınları",
    "EsenYayinlari": "Esen Yayınları",
    "FatihAyYayinlari": "Fatih Ay Yayınları",
    "Fenomen": "Fenomen Yayıncılık",
    "FiYayinlari": "Fi Yayınları",
    "Gizli": "Gizli Yayıncılık",
    "Gunay": "Günay Yayınları",
    "HiperZeka": "Hiper Zeka Yayınları",
    "Hiz": "Hız Yayınları",
    "İslerYayinGurubu": "İşler Yayın Grubu",
    "Key": "Key Yayınları",
    "KondisyonYayinlari": "Kondisyon Yayınları",
    "Kurmay": "Kurmay Yayınları",
    "LimitPerakende": "Limit Perakende",
    "MatsevYayinlari": "Matsev Yayınları",
    "MaviDeniz": "Mavi Deniz Yayınları",
    "Model": "Model Yayınları",
    "Mozaik": "Mozaik Yayınları",
    "Muba": "Muba Yayınları",
    "NetizYayinlari": "Netiz Yayınları",
    "NFTYayinlari": "NFT Yayınları",
    "OksijenYayinlari": "Oksijen Yayınları",
    "Okyanus": "Okyanus Yayıncılık",
    "OptikYayinlari": "Optik Yayınları",
    "Ordinat": "Ordinat Yayınları",
    "OrnekYayinlari": "Örnek Yayınları",
    "PatYayinlari": "Pat Yayınları",
    "PaylasimYayinlari": "Paylaşım Yayınları",
    "PeksenYayinlari": "Pekşen Yayınları",
    "PruvaYayinlari": "Pruva Yayınları",
    "PuzaYayinlari": "Puza Yayınları",
    "Rasyonel": "Rasyonel Yayınları",
    "TammatYayinlari": "Tammat Yayınları",
    "TestYayinlari": "Test Yayınları",
    "ToprakYayinlari": "Toprak Yayınları",
    "Ucgen": "Üçgen Yayıncılık",
    "UcRenkYayinlari": "Üç Renk Yayınları"
}

rich_books = []
for f in files:
    name = f['name']
    file_id = f['id']
    
    # Extract base name and extension
    if name.endswith('.deb'):
        base_name = name[:-4]
        file_type = 'deb'
    elif name.endswith('.fernus'):
        base_name = name[:-7]
        file_type = 'fernus'
    else:
        base_name = name
        file_type = 'unknown'
        
    # Clean the "Kutuphane" suffix
    pub_key = base_name
    if pub_key.endswith('Kutuphane'):
        pub_key = pub_key[:-9]
    elif pub_key.endswith('Kutuphane-v2-23'):
        pub_key = pub_key[:-15]
        
    publisher = turkish_map.get(pub_key, split_camel_case(pub_key))
    title = f"{publisher} Kütüphanesi"
    
    book_id = base_name.lower().replace('_', '-').replace('.', '-')
    
    rich_books.append({
        "id": book_id,
        "title": title,
        "publisher": publisher,
        "version": "1.0.0",
        "description": f"{publisher} interaktif akıllı tahta kitap kütüphanesi uygulaması.",
        "file_name": name,
        "download_url": f"https://drive.google.com/uc?export=download&id={file_id}",
        "file_type": file_type
    })

with open(books_json_path, 'w', encoding='utf-8') as f_out:
    json.dump(rich_books, f_out, ensure_ascii=False, indent=2)

print(f"Generated {len(rich_books)} rich books into {books_json_path}")
