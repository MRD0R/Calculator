import subprocess
import sys

def install_packages():
    packages = [
        'flask==2.0.1',
        'sympy==1.9',
        'numpy==1.21.2',
        'pip',
        'setuptools',
        'wheel'
    ]
    
    print("Начинаем установку пакетов...")
    
    for package in packages:
        print(f"\nУстановка {package}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✓ {package} успешно установлен")
        except subprocess.CalledProcessError as e:
            print(f"✗ Ошибка при установке {package}: {str(e)}")
    
    print("\nУстановка завершена!")

if __name__ == "__main__":
    install_packages() 