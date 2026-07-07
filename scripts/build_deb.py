import os
import sys
import tarfile
import io
import time
import hashlib


def create_ar_header(name, size, mode=0o100644):
    # ar header is 60 bytes:
    # name (16 chars), timestamp (12), owner (6), group (6), mode (8), size (10), magic (2)
    name_field = f"{name:<16}"[:16].encode("ascii")
    ts_field = f"{int(time.time()):<12}"[:12].encode("ascii")
    owner_field = f"{0:<6}"[:6].encode("ascii")  # root
    group_field = f"{0:<6}"[:6].encode("ascii")  # root
    mode_field = f"{oct(mode)[2:]:<8}"[:8].encode("ascii")
    size_field = f"{size:<10}"[:10].encode("ascii")
    magic = b"`\n"
    return (
        name_field
        + ts_field
        + owner_field
        + group_field
        + mode_field
        + size_field
        + magic
    )


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
    # Resolve project root and import version
    sys.path.insert(0, os.getcwd())
    from src.core.version import __version__

    print(f"=== Raf Pure-Python Debian Paketi Derleyici (v{__version__}) ===")

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
            "usr/share/doc/raf",
            "usr/share/raf",
            "usr/share/raf/src",
            "usr/share/raf/src/core",
            "usr/share/raf/src/ui",
            "usr/share/raf/src/assets",
        ]
        added_dirs = set()
        for d in dirs_to_create:
            add_dir(tar, d)
            added_dirs.add(d)

        # Add launcher script
        launcher_content = """#!/bin/bash
export PYTHONPATH="/usr/share/raf:$PYTHONPATH"
exec python3 -u -m src.main "$@"
""".encode("utf-8")

        tarinfo = tarfile.TarInfo(name="usr/bin/raf")
        tarinfo.size = len(launcher_content)
        tarinfo.mtime = int(time.time())
        tarinfo.mode = 0o755
        tarinfo.uname = "root"
        tarinfo.gname = "root"
        tar.addfile(tarinfo, io.BytesIO(launcher_content))
        md5_list.append(f"{get_md5(launcher_content)}  usr/bin/raf\n")

        # Add desktop file
        with open("data/raf.desktop", "rb") as f:
            desktop_content = f.read()
        tarinfo = tarfile.TarInfo(name="usr/share/applications/raf.desktop")
        tarinfo.size = len(desktop_content)
        tarinfo.mtime = int(time.time())
        tarinfo.mode = 0o644
        tarinfo.uname = "root"
        tarinfo.gname = "root"
        tar.addfile(tarinfo, io.BytesIO(desktop_content))
        md5_list.append(
            f"{get_md5(desktop_content)}  usr/share/applications/raf.desktop\n"
        )

        # Add icon file
        with open("src/assets/raf.png", "rb") as f:
            icon_content = f.read()
        tarinfo = tarfile.TarInfo(name="usr/share/pixmaps/raf.png")
        tarinfo.size = len(icon_content)
        tarinfo.mtime = int(time.time())
        tarinfo.mode = 0o644
        tarinfo.uname = "root"
        tarinfo.gname = "root"
        tar.addfile(tarinfo, io.BytesIO(icon_content))
        md5_list.append(f"{get_md5(icon_content)}  usr/share/pixmaps/raf.png\n")

        # Add copyright file
        copyright_content = b""
        if os.path.exists("debian/copyright"):
            with open("debian/copyright", "rb") as f:
                copyright_content = f.read()
        else:
            copyright_content = """Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
Upstream-Name: raf
Copyright: 2026 Kaan Ferid Altundaş <kaanferidaltundas@protonmail.com>
License: GPL-3.0+
""".encode(
                "utf-8"
            )

        tarinfo = tarfile.TarInfo(name="usr/share/doc/raf/copyright")
        tarinfo.size = len(copyright_content)
        tarinfo.mtime = int(time.time())
        tarinfo.mode = 0o644
        tarinfo.uname = "root"
        tarinfo.gname = "root"
        tar.addfile(tarinfo, io.BytesIO(copyright_content))
        md5_list.append(f"{get_md5(copyright_content)}  usr/share/doc/raf/copyright\n")

        # Recursively add src and database directory contents
        for base_dir in ["src", "database"]:
            for root, dirs, files in os.walk(base_dir):
                if "__pycache__" in root:
                    continue
                # Ensure the directory itself is added to the tar archive
                tarpath_dir = os.path.normpath(os.path.join("usr/share/raf", root))
                if tarpath_dir not in added_dirs:
                    add_dir(tar, tarpath_dir)
                    added_dirs.add(tarpath_dir)
                for file in files:
                    if (
                        file.endswith(".pyc")
                        or file.endswith(".pyo")
                        or file.startswith(".")
                    ):
                        continue
                    filepath = os.path.join(root, file)
                    tarpath = os.path.join("usr/share/raf", filepath)

                    tarinfo = tar.gettarinfo(filepath, arcname=tarpath)
                    tarinfo.uname = "root"
                    tarinfo.gname = "root"
                    tarinfo.uid = 0
                    tarinfo.gid = 0

                    # Make sure directories and python files have proper execution/reading modes
                    if file.endswith(".py") or file.endswith(".sh") or "." not in file:
                        tarinfo.mode = 0o755 if file.endswith(".sh") else 0o644
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
    with tarfile.open(
        fileobj=control_data, mode="w:gz", format=tarfile.GNU_FORMAT
    ) as tar:
        # Create control content
        control_content = f"""Package: raf
Version: {__version__}
Section: utils
Priority: optional
Architecture: all
Depends: python3, python3-gi, gir1.2-gtk-4.0, gir1.2-adw-1, python3-requests, policykit-1
Maintainer: Kaan Ferid Altundaş <kaanferidaltundas@protonmail.com>
Description: Pardus Akilli Tahta Raf Uygulamasi
 Pardus tabanli akilli tahtalarda interaktif kitap raflarinin
 hizlica aranmasi, indirilmesi, kurulmasi ve silinmesini saglar.
""".encode("utf-8")

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
        md5sums_content = "".join(md5_list).encode("utf-8")
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
    output_filename = f"raf_{__version__}_all.deb"
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

    print(
        f"=== Başarılı! {output_filename} paketi pure-python kullanılarak oluşturuldu. ==="
    )


if __name__ == "__main__":
    # Change working directory to project root (parent of scripts/)
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    build_deb()
