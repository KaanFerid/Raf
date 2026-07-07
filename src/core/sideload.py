import os
from src.core.translation import tr

SUPPORTED_EXTENSIONS = {".deb", ".zip", ".appimage", ".fernus"}


def process_local_path(target_path):
    """
    Scans the given path (file or folder).
    Returns a tuple: (list of valid book dictionaries, list of unsupported filenames)
    """
    valid_books = []
    unsupported_files = []

    if not os.path.exists(target_path):
        return valid_books, unsupported_files

    if os.path.isfile(target_path):
        _process_single_file(target_path, valid_books, unsupported_files)
    elif os.path.isdir(target_path):
        for entry in os.listdir(target_path):
            full_path = os.path.join(target_path, entry)
            if os.path.isfile(full_path):
                _process_single_file(full_path, valid_books, unsupported_files)

    return valid_books, unsupported_files


def _process_single_file(file_path, valid_books, unsupported_files):
    filename = os.path.basename(file_path)
    ext = os.path.splitext(filename)[1].lower()

    if ext in SUPPORTED_EXTENSIONS:
        # Create a book dictionary for the local file
        # ID is prefixed to prevent collision and identify as local
        import re

        safe_name = re.sub(r"[^a-zA-Z0-9-]", "_", os.path.splitext(filename)[0].lower())
        book_id = f"local_{safe_name}"

        book = {
            "id": book_id,
            "title": os.path.splitext(filename)[0],
            "publisher": tr("cli.local_publisher"),
            "file_name": filename,
            "file_type": ext.lstrip("."),
            "download_url": "",  # Empty since it's local
            "is_local": True,
            "absolute_path": file_path,
        }
        valid_books.append(book)
    else:
        unsupported_files.append(filename)
