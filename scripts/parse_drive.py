import os
import sys
from html.parser import HTMLParser
import json

class DriveHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.files = []
        self.current_tr_id = None
        self.in_strong_name = False
        self.current_name = []
        
    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag == 'tr' and 'data-id' in attrs_dict:
            self.current_tr_id = attrs_dict['data-id']
        elif tag == 'strong' and attrs_dict.get('class') == 'DNoYtb':
            if self.current_tr_id:
                self.in_strong_name = True
                self.current_name = []

    def handle_data(self, data):
        if self.in_strong_name:
            self.current_name.append(data)

    def handle_endtag(self, tag):
        if tag == 'strong' and self.in_strong_name:
            self.in_strong_name = False
            name = "".join(self.current_name).strip()
            if name:
                self.files.append({
                    "id": self.current_tr_id,
                    "name": name
                })
        elif tag == 'tr':
            self.current_tr_id = None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Fallback to the original step 44 log if it exists, otherwise print usage
        default_input = '/home/kaan/.gemini/antigravity/brain/81bf2e77-42f0-44f8-98bd-14fbd70773d2/.system_generated/steps/44/content.md'
        if os.path.exists(default_input):
            input_file = default_input
        else:
            print("Usage: python3 parse_drive.py <input_html_file>")
            sys.exit(1)
    else:
        input_file = sys.argv[1]

    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    parser = DriveHTMLParser()
    parser.feed(content)

    print(f"Parsed {len(parser.files)} files:")
    for f in parser.files:
        print(f"ID: {f['id']} | Name: {f['name']}")

    # Save as JSON next to this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_file = os.path.join(script_dir, 'drive_files.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(parser.files, f, ensure_ascii=False, indent=2)
    print(f"Saved database to {output_file}")
