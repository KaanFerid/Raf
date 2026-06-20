#!/usr/bin/env python3
import os
import sys

# Enable developer/simulator mode
os.environ["ETKILESIMLI_KITAP_KUTUPHANESI_DEV"] = "1"

print("==================================================")
print("  ETKİLEŞİMLİ KİTAP KÜTÜPHANESİ - SİMÜLATÖR MODU   ")
print("==================================================")
print("Bu modda:")
print(" - Paket indirmeleri local 'mock_system/cache/' klasörüne yapılır.")
print(" - Kurulumlar, sisteminizi etkilemeden simüle edilir.")
print(" - Kurulu paket listesi 'mock_system/installed.json' içinde tutulur.")
print(" - Çalıştır butonu, bir bilgi iletişim kutusu açar.")
print(" - Sisteminizde HİÇBİR değişiklik veya paket kurulumu yapılmaz.")
print("==================================================\n")

# Run the main application
try:
    from src.main import main
    main()
except ImportError as e:
    print(f"Hata: Uygulama başlatılamadı. Detay: {e}")
