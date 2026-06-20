import os
import tarfile
import io
import time

def create_ar_header(name, size, mode=0o100644):
    # ar header is 60 bytes:
    # name (16 chars), timestamp (12), owner (6), group (6), mode (8), size (10), magic (2)
    name_field = f"{name:<16}"[:16].encode('ascii')
    ts_field = f"{int(time.time()):<12}"[:12].encode('ascii')
    owner_field = f"{0:<6}"[:6].encode('ascii')  # root
    group_field = f"{0:<6}"[:6].encode('ascii')  # root
    mode_field = f"{oct(mode)[2:]:<8}"[:8].encode('ascii')
    size_field = f"{size:<10}"[:10].encode('ascii')
    magic = b"`\n"
    return name_field + ts_field + owner_field + group_field + mode_field + size_field + magic

def build_deb():
    print("=== KitapMarkt Pure-Python Debian Paketi Derleyici ===")
    
    # 1. Prepare debian-binary content
    debian_binary = b"2.0\n"
    
    # 2. Prepare control.tar.gz
    print("control.tar.gz hazırlanıyor...")
    control_data = io.BytesIO()
    with tarfile.open(fileobj=control_data, mode="w:gz") as tar:
        # Create control content
        control_content = """Package: kitapmarkt
Version: 1.0.0
Section: utils
Priority: optional
Architecture: all
Depends: python3, python3-pyside6, python3-requests, policykit-1
Maintainer: KitapMarkt Team <info@kitapmarkt.org>
Description: Pardus Akilli Tahta Kitap ve Uygulama Marketi
 Pardus tabanli akilli tahtalarda interaktif kitap kütüphanelerinin
 hizlica aranmasi, indirilmesi, kurulmasi ve silinmesini saglar.
""".encode('utf-8')
        
        tarinfo = tarfile.TarInfo(name="control")
        tarinfo.size = len(control_content)
        tarinfo.mtime = int(time.time())
        tarinfo.mode = 0o644
        tarinfo.uname = "root"
        tarinfo.gname = "root"
        tarinfo.uid = 0
        tarinfo.gid = 0
        tar.addfile(tarinfo, io.BytesIO(control_content))
    
    control_tar_gz = control_data.getvalue()
    
    # 3. Prepare data.tar.gz
    print("data.tar.gz hazırlanıyor...")
    data_data = io.BytesIO()
    with tarfile.open(fileobj=data_data, mode="w:gz") as tar:
        # Add launcher script
        launcher_content = """#!/bin/bash
export PYTHONPATH="/usr/share/kitapmarkt:$PYTHONPATH"
exec python3 -m src.main "$@"
""".encode('utf-8')
        
        tarinfo = tarfile.TarInfo(name="usr/bin/kitapmarkt")
        tarinfo.size = len(launcher_content)
        tarinfo.mtime = int(time.time())
        tarinfo.mode = 0o755
        tarinfo.uname = "root"
        tarinfo.gname = "root"
        tar.addfile(tarinfo, io.BytesIO(launcher_content))

        # Add desktop file
        with open("kitapmarkt.desktop", "rb") as f:
            desktop_content = f.read()
        tarinfo = tarfile.TarInfo(name="usr/share/applications/kitapmarkt.desktop")
        tarinfo.size = len(desktop_content)
        tarinfo.mtime = int(time.time())
        tarinfo.mode = 0o644
        tarinfo.uname = "root"
        tarinfo.gname = "root"
        tar.addfile(tarinfo, io.BytesIO(desktop_content))

        # Add icon file
        with open("src/assets/kitapmarkt.png", "rb") as f:
            icon_content = f.read()
        tarinfo = tarfile.TarInfo(name="usr/share/pixmaps/kitapmarkt.png")
        tarinfo.size = len(icon_content)
        tarinfo.mtime = int(time.time())
        tarinfo.mode = 0o644
        tarinfo.uname = "root"
        tarinfo.gname = "root"
        tar.addfile(tarinfo, io.BytesIO(icon_content))

        # Recursively add src directory contents
        for root, dirs, files in os.walk("src"):
            for file in files:
                filepath = os.path.join(root, file)
                tarpath = os.path.join("usr/share/kitapmarkt", filepath)
                
                tarinfo = tar.gettarinfo(filepath, arcname=tarpath)
                tarinfo.uname = "root"
                tarinfo.gname = "root"
                tarinfo.uid = 0
                tarinfo.gid = 0
                
                # Make sure directories and python files have proper execution/reading modes
                if file.endswith('.py') or file.endswith('.sh') or '.' not in file:
                    tarinfo.mode = 0o755 if file.endswith('.sh') else 0o644
                else:
                    tarinfo.mode = 0o644
                
                with open(filepath, "rb") as f:
                    tar.addfile(tarinfo, f)

    data_tar_gz = data_data.getvalue()

    # 4. Write to ar archive (.deb file)
    output_filename = "kitapmarkt_1.0.0_all.deb"
    print(f"Bileşenler {output_filename} dosyasına birleştiriliyor...")
    
    with open(output_filename, "wb") as deb:
        # ar global header
        deb.write(b"!<arch>\n")
        
        # 1. Write debian-binary
        deb.write(create_ar_header("debian-binary", len(debian_binary)))
        deb.write(debian_binary)
        if len(debian_binary) % 2 != 0:
            deb.write(b"\n")
            
        # 2. Write control.tar.gz
        deb.write(create_ar_header("control.tar.gz", len(control_tar_gz)))
        deb.write(control_tar_gz)
        if len(control_tar_gz) % 2 != 0:
            deb.write(b"\n")
            
        # 3. Write data.tar.gz
        deb.write(create_ar_header("data.tar.gz", len(data_tar_gz)))
        deb.write(data_tar_gz)
        if len(data_tar_gz) % 2 != 0:
            deb.write(b"\n")

    print(f"=== Başarılı! {output_filename} paketi pure-python kullanılarak oluşturuldu. ===")

if __name__ == "__main__":
    build_deb()
