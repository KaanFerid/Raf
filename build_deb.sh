#!/bin/bash
# KitapMarkt debian package builder script
set -e

echo "=== KitapMarkt Debian Paketi Hazırlanıyor ==="

if command -v dpkg-deb >/dev/null 2>&1; then
    echo "Sistemde dpkg-deb bulundu, standart yöntemle paketleniyor..."
    
    # Define directories
    PKG_DIR="build/kitapmarkt-pkg"
    rm -rf "$PKG_DIR"
    mkdir -p "$PKG_DIR/DEBIAN"
    mkdir -p "$PKG_DIR/usr/bin"
    mkdir -p "$PKG_DIR/usr/share/applications"
    mkdir -p "$PKG_DIR/usr/share/pixmaps"
    mkdir -p "$PKG_DIR/usr/share/kitapmarkt"

    # 1. Copy python source files
    echo "Kaynak dosyaları kopyalanıyor..."
    cp -r src "$PKG_DIR/usr/share/kitapmarkt/"

    # 2. Create the executable launcher script
    echo "Çalıştırıcı script oluşturuluyor..."
    cat << 'EOF' > "$PKG_DIR/usr/bin/kitapmarkt"
#!/bin/bash
export PYTHONPATH="/usr/share/kitapmarkt:$PYTHONPATH"
exec python3 -m src.main "$@"
EOF
    chmod +x "$PKG_DIR/usr/bin/kitapmarkt"

    # 3. Copy desktop entry
    echo "Masaüstü kısayolu kopyalanıyor..."
    cp kitapmarkt.desktop "$PKG_DIR/usr/share/applications/"

    # 4. Copy logo/icon
    echo "Uygulama logosu kopyalanıyor..."
    cp src/assets/kitapmarkt.png "$PKG_DIR/usr/share/pixmaps/"

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
Package: kitapmarkt
Version: 1.0.0
Section: utils
Priority: optional
Architecture: all
Depends: python3, python3-pyside6, python3-requests, policykit-1
Maintainer: KitapMarkt Team <info@kitapmarkt.org>
Description: Pardus Akilli Tahta Kitap ve Uygulama Marketi
 Pardus tabanli akilli tahtalarda interaktif kitap kütüphanelerinin
 hizlica aranmasi, indirilmesi, kurulmasi ve silinmesini saglar.
EOF
    fi

    # Ensure files have correct permissions
    echo "İzinler ayarlanıyor..."
    find "$PKG_DIR" -type d -exec chmod 755 {} \;
    find "$PKG_DIR" -type f -exec chmod 644 {} \;
    chmod 755 "$PKG_DIR/usr/bin/kitapmarkt"
    chmod 755 "$PKG_DIR/DEBIAN"

    # Build the debian package
    echo "Paket derleniyor (dpkg-deb)..."
    dpkg-deb --build "$PKG_DIR" "kitapmarkt_1.0.0_all.deb"
    echo "=== Başarılı! Paket kitapmarkt_1.0.0_all.deb olarak oluşturuldu. ==="

else
    echo "Sistemde dpkg-deb bulunamadı, Python tabanlı paketleyici (build_deb.py) çalıştırılıyor..."
    python3 build_deb.py
fi
