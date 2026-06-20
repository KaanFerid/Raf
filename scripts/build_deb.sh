#!/bin/bash
# Etkileşimli Kitap Kütüphanesi debian package builder script
set -e

# Change directory to the project root (parent of the scripts directory)
cd "$(dirname "$0")/.."

echo "=== Etkileşimli Kitap Kütüphanesi Debian Paketi Hazırlanıyor ==="

if command -v dpkg-deb >/dev/null 2>&1; then
    echo "Sistemde dpkg-deb bulundu, standart yöntemle paketleniyor..."
    
    # Define directories
    PKG_DIR="build/etkilesimli-kitap-kutuphanesi-pkg"
    rm -rf "$PKG_DIR"
    mkdir -p "$PKG_DIR/DEBIAN"
    mkdir -p "$PKG_DIR/usr/bin"
    mkdir -p "$PKG_DIR/usr/share/applications"
    mkdir -p "$PKG_DIR/usr/share/pixmaps"
    mkdir -p "$PKG_DIR/usr/share/etkilesimli-kitap-kutuphanesi"

    # 1. Copy python source files
    echo "Kaynak dosyaları kopyalanıyor..."
    cp -r src "$PKG_DIR/usr/share/etkilesimli-kitap-kutuphanesi/"

    # 2. Create the executable launcher script
    echo "Çalıştırıcı script oluşturuluyor..."
    cat << 'EOF' > "$PKG_DIR/usr/bin/etkilesimli-kitap-kutuphanesi"
#!/bin/bash
export PYTHONPATH="/usr/share/etkilesimli-kitap-kutuphanesi:$PYTHONPATH"
exec python3 -u -m src.main "$@"
EOF
    chmod +x "$PKG_DIR/usr/bin/etkilesimli-kitap-kutuphanesi"

    # 3. Copy desktop entry
    echo "Masaüstü kısayolu kopyalanıyor..."
    cp etkilesimli-kitap-kutuphanesi.desktop "$PKG_DIR/usr/share/applications/"

    # 4. Copy logo/icon
    echo "Uygulama logosu kopyalanıyor..."
    cp src/assets/etkilesimli-kitap-kutuphanesi.png "$PKG_DIR/usr/share/pixmaps/"

    # 4b. Copy copyright
    echo "Telif hakkı (copyright) dosyası kopyalanıyor..."
    mkdir -p "$PKG_DIR/usr/share/doc/etkilesimli-kitap-kutuphanesi"
    if [ -f debian/copyright ]; then
        cp debian/copyright "$PKG_DIR/usr/share/doc/etkilesimli-kitap-kutuphanesi/"
    else
        cat << EOF > "$PKG_DIR/usr/share/doc/etkilesimli-kitap-kutuphanesi/copyright"
Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
Upstream-Name: etkilesimli-kitap-kutuphanesi

Files: *
Copyright: 2026 Kaan Ferid Altundaş <info@kitapmarkt.org>
License: GPL-3.0+
EOF
    fi

    # 5. Create control file
    echo "Paket control dosyası hazırlanıyor..."
    if [ -f debian/control ]; then
        # Extract package metadata from debian/control, removing source fields
        grep -v "^Source:" debian/control | \
        grep -v "^Build-Depends:" | \
        grep -v "^Standards-Version:" > "$PKG_DIR/DEBIAN/control"
        
        # Append Version dynamically if not defined
        if ! grep -q "^Version:" "$PKG_DIR/DEBIAN/control"; then
            echo "Version: 1.0.0" >> "$PKG_DIR/DEBIAN/control"
        fi
    else
        # Fallback default control
        cat << EOF > "$PKG_DIR/DEBIAN/control"
Package: etkilesimli-kitap-kutuphanesi
Version: 1.0.0
Section: utils
Priority: optional
Architecture: all
Depends: python3, python3-pyside6 | python3-pyqt5, python3-requests, policykit-1
Maintainer: Kaan Ferid Altundaş <info@kitapmarkt.org>
Description: Pardus Akilli Tahta Etkilesimli Kitap Kutuphanesi
 Pardus tabanli akilli tahtalarda interaktif kitap kütüphanelerinin
 hizlica aranmasi, indirilmesi, kurulmasi ve silinmesini saglar.
EOF
    fi

    # 5b. Generate md5sums
    echo "MD5 kontrol toplamları oluşturuluyor..."
    (cd "$PKG_DIR" && find usr -type f -exec md5sum {} \;) > "$PKG_DIR/DEBIAN/md5sums"

    # Ensure files have correct permissions
    echo "İzinler ayarlanıyor..."
    find "$PKG_DIR" -type d -exec chmod 755 {} \;
    find "$PKG_DIR" -type f -exec chmod 644 {} \;
    chmod 755 "$PKG_DIR/usr/bin/etkilesimli-kitap-kutuphanesi"
    chmod 755 "$PKG_DIR/DEBIAN"

    # Build the debian package
    echo "Paket derleniyor (dpkg-deb)..."
    dpkg-deb --build "$PKG_DIR" "etkilesimli-kitap-kutuphanesi_1.0.0_all.deb"
    echo "=== Başarılı! Paket etkilesimli-kitap-kutuphanesi_1.0.0_all.deb olarak oluşturuldu. ==="

else
    echo "Sistemde dpkg-deb bulunamadı, Python tabanlı paketleyici (build_deb.py) çalıştırılıyor..."
    python3 scripts/build_deb.py
fi
