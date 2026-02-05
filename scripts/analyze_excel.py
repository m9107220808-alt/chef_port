import pandas as pd
import sys

try:
    # Заголовок найден на 11 строке (индекс 11)
    df = pd.read_excel("Заказ ИП Город (2).xlsx", header=11)
    
    print("\n--- Columns found ---")
    print(list(df.columns))
    
    print("\n--- First 20 rows of data ---")
    # Выводим первые 20 строк, чтобы понять где категории
    print(df.head(20).to_string())
    
    print("\n--- Photo Links Analysis ---")
    # Проверяем колонку Фото
    if 'Фото' in df.columns:
        print(df['Фото'].head(10).tolist())

except Exception as e:
    print(f"Error: {e}")
