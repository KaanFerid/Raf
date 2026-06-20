#!/usr/bin/env python3
import os
import sys
import subprocess

# 1. Force Simulator/Developer Mode
os.environ["KITAPMARKT_DEV"] = "1"

print("==================================================")
print("     KİTAPMARKT - ARCH LINUX ÇALIŞTIRICI / SİMÜLATÖRÜ     ")
print("==================================================")
print("Bu çalıştırıcı:")
print(" - Sisteminizde hiçbir kalıcı değişiklik yapmaz.")
print(" - Herhangi bir global sistem paketi veya program kurmaz.")
print(" - Eğer gerekli kütüphaneler yoksa, proje klasöründe izole bir")
print("   sanal ortam (.venv) oluşturup kütüphaneleri oraya kurar.")
print(" - Kitap indirmelerini yerel 'mock_system/cache/' dizinine yapar.")
print(" - Kurulum durumlarını 'mock_system/installed.json' içinde simüle eder.")
print("==================================================\n")

def check_dependencies():
    """Checks if requests and a Qt library are importable in the current python context."""
    try:
        import requests
    except ImportError:
        return False
        
    try:
        # Check if qt_compat can import successfully
        from src import qt_compat
        return True
    except ImportError:
        return False
    except SystemExit:
        # If qt_compat exits because no library is found
        return False

def run_in_venv():
    venv_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".venv")
    venv_python = os.path.join(venv_dir, "bin", "python")
    venv_pip = os.path.join(venv_dir, "bin", "pip")
    
    if not os.path.exists(venv_python):
        print("-> Gerekli Python kütüphaneleri sisteminizde bulunamadı.")
        print("-> Proje klasöründe izole bir sanal ortam (.venv) oluşturuluyor...")
        try:
            subprocess.run([sys.executable, "-m", "venv", venv_dir], check=True)
            print("-> Sanal ortam oluşturuldu. Kütüphaneler kuruluyor (pip install PySide6 requests)...")
            
            # Upgrade pip first to avoid issues
            subprocess.run([venv_pip, "install", "--upgrade", "pip"], check=False)
            
            # Install requirements
            subprocess.run([venv_pip, "install", "PySide6", "requests"], check=True)
            print("-> Kurulum tamamlandı.\n")
        except Exception as e:
            print(f"\nHATA: Sanal ortam oluşturulurken veya kütüphaneler kurulurken hata oluştu: {e}")
            print("Lütfen sisteminizde 'python-virtualenv' paketinin kurulu olduğundan emin olun.")
            sys.exit(1)
            
    print("-> Uygulama sanal ortam (.venv) üzerinden başlatılıyor...")
    
    # Run the application using the venv python
    cmd = [
        venv_python, 
        "-c", 
        "import os; os.environ['KITAPMARKT_DEV'] = '1'; from src.main import main; main()"
    ]
    
    # Forward the arguments as well
    if len(sys.argv) > 1:
        cmd.extend(sys.argv[1:])
        
    try:
        result = subprocess.run(cmd)
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        print("\nUygulama kullanıcı tarafından sonlandırıldı.")
        sys.exit(0)

def main():
    if check_dependencies():
        print("-> Gerekli kütüphaneler sisteminizde mevcut. Uygulama başlatılıyor...")
        try:
            from src.main import main as app_main
            app_main()
        except KeyboardInterrupt:
            print("\nUygulama kullanıcı tarafından sonlandırıldı.")
            sys.exit(0)
    else:
        run_in_venv()

if __name__ == "__main__":
    main()
