import pandas as pd
import sys
import json

try:
    df = pd.read_excel("Заказ ИП Город (2).xlsx")
    print("Columns:", list(df.columns))
    print("First 3 rows:")
    print(df.head(3).to_markdown())
    
    # Пытаемся найти колонку с фото
    photo_col = next((c for c in df.columns if 'фото' in c.lower() or 'ссылка' in c.lower() or 'image' in c.lower()), None)
    if photo_col:
        print(f"\nFound photo column: {photo_col}")
        print("Sample photos:", df[photo_col].head(3).tolist())
    else:
        print("\nPhoto column not found automatically.")

except ImportError:
    print("Pandas or openpyxl not installed. Please install: pip install pandas openpyxl tabulate")
except Exception as e:
    print(f"Error: {e}")
