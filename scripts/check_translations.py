#!/usr/bin/env python3
"""
Translation Sync Checker
========================
This script compares en.json and tr.json to ensure that both
language files have exactly the same keys. It warns if any keys
are missing in either translation file.
"""

import json
import sys
from pathlib import Path

def get_flattened_keys(d, parent_key=''):
    items = []
    for k, v in d.items():
        if k == '_meta':
            continue
        new_key = f"{parent_key}.{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(get_flattened_keys(v, new_key).items())
        else:
            items.append((new_key, v))
    return dict(items)

def main():
    repo_root = Path(__file__).parent.parent
    locales_dir = repo_root / "src" / "assets" / "locales"
    
    en_file = locales_dir / "en.json"
    tr_file = locales_dir / "tr.json"
    
    if not en_file.exists() or not tr_file.exists():
        print("Error: Could not find en.json or tr.json in src/assets/locales/", file=sys.stderr)
        sys.exit(1)
        
    with open(en_file, "r", encoding="utf-8") as f:
        en_data = json.load(f)
        
    with open(tr_file, "r", encoding="utf-8") as f:
        tr_data = json.load(f)
        
    en_keys = set(get_flattened_keys(en_data).keys())
    tr_keys = set(get_flattened_keys(tr_data).keys())
    
    missing_in_tr = en_keys - tr_keys
    missing_in_en = tr_keys - en_keys
    
    has_errors = False
    
    if missing_in_tr:
        has_errors = True
        print(f"❌ Missing in Turkish (tr.json):")
        for key in sorted(missing_in_tr):
            print(f"   - {key}")
            
    if missing_in_en:
        has_errors = True
        print(f"\n❌ Missing in English (en.json):")
        for key in sorted(missing_in_en):
            print(f"   - {key}")
            
    if not has_errors:
        print("✅ Translations are perfectly synced!")
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
