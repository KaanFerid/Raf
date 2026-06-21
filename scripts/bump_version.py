#!/usr/bin/env python3
import os
import re
import subprocess
import sys

def bump_version():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    version_file_path = os.path.join(project_root, "src", "core", "version.py")
    
    if not os.path.exists(version_file_path):
        print(f"Error: version file not found at {version_file_path}", file=sys.stderr)
        sys.exit(1)
        
    with open(version_file_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    match = re.search(r'__version__\s*=\s*"([^"]+)"', content)
    if not match:
        print("Error: could not find __version__ in version.py", file=sys.stderr)
        sys.exit(1)
        
    current_version = match.group(1)
    parts = current_version.split('.')
    if len(parts) < 3:
        # Pad with zeros if less than 3 parts (e.g. "1.0" -> "1.0.0")
        parts.extend(['0'] * (3 - len(parts)))
        
    try:
        parts[-1] = str(int(parts[-1]) + 1)
    except ValueError:
        print(f"Error: version patch part '{parts[-1]}' is not an integer", file=sys.stderr)
        sys.exit(1)
        
    new_version = ".".join(parts)
    print(f"Bumping version: {current_version} -> {new_version}")
    
    new_content = re.sub(
        r'__version__\s*=\s*"[^"]+"',
        f'__version__ = "{new_version}"',
        content
    )
    
    with open(version_file_path, "w", encoding="utf-8") as f:
        f.write(new_content)
        
    # Auto-stage the version file change so it gets committed
    try:
        subprocess.run(["git", "add", version_file_path], check=True, cwd=project_root)
    except Exception as e:
        print(f"Warning: failed to stage version file: {e}", file=sys.stderr)

if __name__ == "__main__":
    bump_version()
