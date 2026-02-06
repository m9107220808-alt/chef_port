"""
Скрипт для скачивания всех фотографий из папки Google Drive
Использует библиотеку gdown для работы с Google Drive
"""
import subprocess
import sys
from pathlib import Path

# Папка куда скачиваем
OUTPUT_DIR = Path(__file__).parent.parent / "web" / "images" / "products"

# ID папки Google Drive из ссылки
# https://drive.google.com/drive/folders/19DSNmigpdhXl3IU12wfOn2Fmnb0480S5
FOLDER_ID = "19DSNmigpdhXl3IU12wfOn2Fmnb0480S5"


def install_gdown():
    """Устанавливает библиотеку gdown если её нет"""
    print("📦 Проверяю наличие библиотеки gdown...")
    try:
        import gdown
        print("✅ gdown уже установлена")
        return True
    except ImportError:
        print("⬇️ Устанавливаю gdown...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "gdown"])
            print("✅ gdown установлена успешно")
            return True
        except Exception as e:
            print(f"❌ Ошибка установки gdown: {e}")
            return False


def download_folder():
    """Скачивает папку с Google Drive"""
    try:
        import gdown
    except ImportError:
        print("❌ gdown не установлена!")
        return False
    
    # Создаём папку для изображений
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"📁 Папка для сохранения: {OUTPUT_DIR}\n")
    
    # URL папки
    folder_url = f"https://drive.google.com/drive/folders/{FOLDER_ID}"
    
    print(f"🔗 Скачиваю из: {folder_url}")
    print("⏳ Это может занять несколько минут...\n")
    
    try:
        # Скачиваем всю папку
        gdown.download_folder(
            url=folder_url,
            output=str(OUTPUT_DIR),
            quiet=False,
            use_cookies=False
        )
        print("\n✅ Скачивание завершено!")
        return True
    except Exception as e:
        print(f"\n❌ Ошибка скачивания: {e}")
        return False


def main():
    print("=" * 70)
    print("🚀 СКАЧИВАНИЕ ФОТОГРАФИЙ ТОВАРОВ ИЗ GOOGLE DRIVE")
    print("=" * 70)
    print()
    
    # Шаг 1: Установка gdown
    if not install_gdown():
        print("\n❌ Не удалось установить gdown. Попробуйте вручную:")
        print("   pip install gdown")
        return
    
    print()
    
    # Шаг 2: Скачивание папки
    if download_folder():
        # Подсчитываем файлы
        image_files = list(OUTPUT_DIR.glob("**/*"))
        image_files = [f for f in image_files if f.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp']]
        
        print(f"\n📊 Скачано файлов: {len(image_files)}")
        
        if len(image_files) > 0:
            print("\n✨ Примеры скачанных файлов:")
            for img in image_files[:5]:
                print(f"  - {img.name}")
            if len(image_files) > 5:
                print(f"  ... и ещё {len(image_files) - 5} файлов")
        
        print("\n" + "=" * 70)
        print("✅ ГОТОВО! Следующий шаг:")
        print("   python scripts\\create_image_mapping.py")
        print("=" * 70)
    else:
        print("\n" + "=" * 70)
        print("❌ Скачивание не удалось!")
        print("\nВозможные причины:")
        print("  1. Папка не имеет публичного доступа 'Все, у кого есть ссылка'")
        print("  2. Отсутствует подключение к интернету")
        print("  3. Google Drive временно недоступен")
        print("\nАльтернативное решение:")
        print("  1. Откройте папку в браузере")
        print("  2. Выделите все фото (Ctrl+A)")
        print("  3. Скачайте как ZIP")
        print(f"  4. Распакуйте в: {OUTPUT_DIR}")
        print("=" * 70)


if __name__ == "__main__":
    main()
