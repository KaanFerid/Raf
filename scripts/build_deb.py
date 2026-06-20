import os
import tarfile
import io
import time
import hashlib

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

def add_dir(tar, dir_path):
    tarinfo = tarfile.TarInfo(name=dir_path)
    tarinfo.type = tarfile.DIRTYPE
    tarinfo.mode = 0o755
    tarinfo.uname = "root"
    tarinfo.gname = "root"
    tarinfo.uid = 0
    tarinfo.gid = 0
    tarinfo.mtime = int(time.time())
    tar.addfile(tarinfo)

def build_deb():
    print("=== Etkileşimli Kitap Kütüphanesi Pure-Python Debian Paketi Derleyici ===")
    
    # 1. Prepare debian-binary content
    debian_binary = b"2.0\n"
    
    md5_list = []
    
    def get_md5(content_bytes):
        return hashlib.md5(content_bytes).hexdigest()
    
    # 2. Prepare data.tar.gz
    print("data.tar.gz hazırlanıyor...")
    data_data = io.BytesIO()
    with tarfile.open(fileobj=data_data, mode="w:gz", format=tarfile.GNU_FORMAT) as tar:
        # Add parent directories first so dpkg can extract files into them
        dirs_to_create = [
            "usr",
            "usr/bin",
            "usr/share",
            "usr/share/applications",
            "usr/share/pixmaps",
            "usr/share/doc",
            "usr/share/doc/etkilesimli-kitap-kutuphanesi",
            "usr/share/etkilesimli-kitap-kutuphanesi",
            "usr/share/etkilesimli-kitap-kutuphanesi/src",
            "usr/share/etkilesimli-kitap-kutuphanesi/src/core",
            "usr/share/etkilesimli-kitap-kutuphanesi/src/ui",
            "usr/share/etkilesimli-kitap-kutuphanesi/src/assets"
        ]
        for d in dirs_to_create:
            add_dir(tar, d)
            
        # Add launcher script
        launcher_content = """#!/bin/bash
export PYTHONPATH="/usr/share/etkilesimli-kitap-kutuphanesi:$PYTHONPATH"
exec python3 -u -m src.main "$@"
""".encode('utf-8')
        
        tarinfo = tarfile.TarInfo(name="usr/bin/etkilesimli-kitap-kutuphanesi")
        tarinfo.size = len(launcher_content)
        tarinfo.mtime = int(time.time())
        tarinfo.mode = 0o755
        tarinfo.uname = "root"
        tarinfo.gname = "root"
        tar.addfile(tarinfo, io.BytesIO(launcher_content))
        md5_list.append(f"{get_md5(launcher_content)}  usr/bin/etkilesimli-kitap-kutuphanesi\n")

        # Add desktop file
        with open("data/etkilesimli-kitap-kutuphanesi.desktop", "rb") as f:
            desktop_content = f.read()
        tarinfo = tarfile.TarInfo(name="usr/share/applications/etkilesimli-kitap-kutuphanesi.desktop")
        tarinfo.size = len(desktop_content)
        tarinfo.mtime = int(time.time())
        tarinfo.mode = 0o644
        tarinfo.uname = "root"
        tarinfo.gname = "root"
        tar.addfile(tarinfo, io.BytesIO(desktop_content))
        md5_list.append(f"{get_md5(desktop_content)}  usr/share/applications/etkilesimli-kitap-kutuphanesi.desktop\n")

        # Add icon file
        with open("src/assets/etkilesimli-kitap-kutuphanesi.png", "rb") as f:
            icon_content = f.read()
        tarinfo = tarfile.TarInfo(name="usr/share/pixmaps/etkilesimli-kitap-kutuphanesi.png")
        tarinfo.size = len(icon_content)
        tarinfo.mtime = int(time.time())
        tarinfo.mode = 0o644
        tarinfo.uname = "root"
        tarinfo.gname = "root"
        tar.addfile(tarinfo, io.BytesIO(icon_content))
        md5_list.append(f"{get_md5(icon_content)}  usr/share/pixmaps/etkilesimli-kitap-kutuphanesi.png\n")

        # Add copyright file
        copyright_content = b""
        if os.path.exists("debian/copyright"):
            with open("debian/copyright", "rb") as f:
                copyright_content = f.read()
        else:
            copyright_content = """Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
Upstream-Name: etkilesimli-kitap-kutuphanesi
Copyright: 2026 Kaan Ferid Altundaş <info@kitapmarkt.org>
License: GPL-3.0+
""".encode('utf-8')
        
        tarinfo = tarfile.TarInfo(name="usr/share/doc/etkilesimli-kitap-kutuphanesi/copyright")
        tarinfo.size = len(copyright_content)
        tarinfo.mtime = int(time.time())
        tarinfo.mode = 0o644
        tarinfo.uname = "root"
        tarinfo.gname = "root"
        tar.addfile(tarinfo, io.BytesIO(copyright_content))
        md5_list.append(f"{get_md5(copyright_content)}  usr/share/doc/etkilesimli-kitap-kutuphanesi/copyright\n")

        # Recursively add src directory contents
        for root, dirs, files in os.walk("src"):
            if "__pycache__" in root:
                continue
            for file in files:
                if file.endswith('.pyc') or file.endswith('.pyo') or file.startswith('.'):
                    continue
                filepath = os.path.join(root, file)
                tarpath = os.path.join("usr/share/etkilesimli-kitap-kutuphanesi", filepath)
                
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
                    content = f.read()
                md5_hash = hashlib.md5(content).hexdigest()
                md5_list.append(f"{md5_hash}  {tarpath}\n")
                tar.addfile(tarinfo, io.BytesIO(content))

    data_tar_gz = data_data.getvalue()

    # 3. Prepare control.tar.gz
    print("control.tar.gz hazırlanıyor...")
    control_data = io.BytesIO()
    with tarfile.open(fileobj=control_data, mode="w:gz", format=tarfile.GNU_FORMAT) as tar:
        # Create control content
        control_content = """Package: etkilesimli-kitap-kutuphanesi
Version: 1.0.0
Section: utils
Priority: optional
Architecture: all
Depends: python3, python3-pyside6 | python3-pyqt5, python3-requests, policykit-1
Maintainer: Kaan Ferid Altundaş <info@kitapmarkt.org>
Description: Pardus Akilli Tahta Etkilesimli Kitap Kutuphanesi
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

        # Add md5sums file
        md5sums_content = "".join(md5_list).encode('utf-8')
        tarinfo = tarfile.TarInfo(name="md5sums")
        tarinfo.size = len(md5sums_content)
        tarinfo.mtime = int(time.time())
        tarinfo.mode = 0o644
        tarinfo.uname = "root"
        tarinfo.gname = "root"
        tarinfo.uid = 0
        tarinfo.gid = 0
        tar.addfile(tarinfo, io.BytesIO(md5sums_content))
    
    control_tar_gz = control_data.getvalue()

    # 4. Write to ar archive (.deb file)
    output_filename = "etkilesimli-kitap-kutuphanesi_1.0.0_all.deb"
    print(f"Bileşenler {output_filename} dosyasına birleştiriliyor...")
    
    with open(output_filename, "wb") as deb:
        # ar global header
        deb.write(b"!<arch>\n")
        
        # 1. Write debian-binary
        deb.write(create_ar_header("debian-binary/", len(debian_binary)))
        deb.write(debian_binary)
        if len(debian_binary) % 2 != 0:
            deb.write(b"\n")
            
        # 2. Write control.tar.gz
        deb.write(create_ar_header("control.tar.gz/", len(control_tar_gz)))
        deb.write(control_tar_gz)
        if len(control_tar_gz) % 2 != 0:
            deb.write(b"\n")
            
        # 3. Write data.tar.gz
        deb.write(create_ar_header("data.tar.gz/", len(data_tar_gz)))
        deb.write(data_tar_gz)
        if len(data_tar_gz) % 2 != 0:
            deb.write(b"\n")

    print(f"=== Başarılı! {output_filename} paketi pure-python kullanılarak oluşturuldu. ===")

if __name__ == "__main__":
    # Change working directory to project root (parent of scripts/)
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    build_deb()
