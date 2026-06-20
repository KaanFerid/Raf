import os
import tarfile
import io

def inspect_deb(filename):
    with open(filename, 'rb') as f:
        data = f.read()
    
    # Verify global header
    if not data.startswith(b"!<arch>\n"):
        print("Invalid ar archive format.")
        return
        
    offset = 8
    while offset < len(data):
        # Read header (60 bytes)
        if offset + 60 > len(data):
            break
        header = data[offset:offset+60]
        
        name = header[0:16].decode('ascii').strip().rstrip('/')
        size = int(header[48:58].decode('ascii').strip())
        
        print(f"Entry found: {name} ({size} bytes)")
        
        file_data = data[offset+60:offset+60+size]
        
        if name == "data.tar.gz" or name == "data.tar.xz":
            print("\nFiles in data.tar.gz:")
            tar = tarfile.open(fileobj=io.BytesIO(file_data), mode="r:gz")
            for member in tar.getmembers():
                print(f" - {member.name} (mode: {oct(member.mode)}, size: {member.size} bytes)")
                
        elif name == "control.tar.gz":
            print("\nFiles in control.tar.gz:")
            tar = tarfile.open(fileobj=io.BytesIO(file_data), mode="r:gz")
            for member in tar.getmembers():
                print(f" - {member.name} (mode: {oct(member.mode)}, size: {member.size} bytes)")
            
        # Move to next entry, aligning to even bytes
        offset += 60 + size
        if size % 2 != 0:
            offset += 1

if __name__ == "__main__":
    filename = "etkilesimli-kitap-kutuphanesi_1.0.0_all.deb"
    if not os.path.exists(filename):
        # Check parent directory
        parent_filename = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), filename)
        if os.path.exists(parent_filename):
            filename = parent_filename
            
    print(f"Inspecting package: {filename}")
    inspect_deb(filename)
