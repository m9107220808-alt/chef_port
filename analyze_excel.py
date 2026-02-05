import pandas as pd
import os

files = ["Заказ ИП Город (2).xlsx", "АВС анализ продаж.xls"]

for f in files:
    if not os.path.exists(f):
        print(f"❌ Файл не найден: {f}")
        continue
        
    with open("analysis_log.txt", "a", encoding="utf-8") as log:
        log.write(f"\n--- File: {f} ---\n")
        try:
            # Skip first 7 rows to likely hit the header
            if f.endswith('.xlsx'):
                df = pd.read_excel(f, engine='openpyxl', skiprows=7, nrows=5)
            else:
                df = pd.read_excel(f, engine='xlrd', skiprows=7, nrows=5)
                
            log.write(f"Columns: {list(df.columns)}\n")
            if not df.empty:
                log.write(f"Row 0: {df.iloc[0].to_dict()}\n")
        except Exception as e:
            log.write(f"Error: {e}\n")
