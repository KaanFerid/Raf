#!/usr/bin/env python3
import os
import sys
import subprocess

# Enable developer/simulator mode
os.environ["RAF_DEV"] = "1"

print("==================================================")
print("              RAF - SİMÜLATÖR MODU                ")
print("==================================================")
print("Bu modda:")
print(" - Paket indirmeleri local 'mock_system/cache/' klasörüne yapılır.")
print(" - Kurulumlar, sisteminizi etkilemeden simüle edilir.")
print(" - Kurulu paket listesi 'mock_system/installed.json' içinde tutulur.")
print(" - Eğer gerekli kütüphaneler yoksa, proje klasöründe izole bir")
print("   sanal ortam (.venv) oluşturup kütüphaneleri oraya kurar.")
print(" - Sisteminizde HİÇBİR kalıcı değişiklik veya global paket kurulumu yapılmaz.")
print("==================================================\n")

def check_dependencies():
    """Checks if requests and PyQt5 are importable."""
    try:
        import requests
    except ImportError:
        return False
        
    try:
        import PyQt5
        return True
    except ImportError:
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
            print("-> Sanal ortam oluşturuldu. Kütüphaneler kuruluyor (pip install PyQt5 requests)...")
            
            # Upgrade pip first to avoid issues
            subprocess.run([venv_pip, "install", "--upgrade", "pip"], check=False)
            
            # Install requirements
            subprocess.run([venv_pip, "install", "PyQt5", "requests"], check=True)
            print("-> Kurulum tamamlandı.\n")
        except Exception as e:
            print(f"\nHATA: Sanal ortam oluşturulurken veya kütüphaneler kurulurken hata oluştu: {e}")
            print("Lütfen sisteminizde 'python3-venv' paketinin kurulu olduğundan emin olun.")
            sys.exit(1)
            
    print("-> Uygulama sanal ortam (.venv) üzerinden başlatılıyor...")
    
    # Run the application using the venv python
    cmd = [
        venv_python, 
        "-c", 
        "import sys, os; sys.path.insert(0, os.path.abspath(os.path.dirname('__file__'))); os.environ['RAF_DEV'] = '1'; from src.main import main; main()"
    ]
    
    # Forward the arguments as well
    if len(sys.argv) > 1:
        cmd.extend(sys.argv[1:])
        
    try:
        # Pass the environment variables
        env = os.environ.copy()
        result = subprocess.run(cmd, env=env)
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
