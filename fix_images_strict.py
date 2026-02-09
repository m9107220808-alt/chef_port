import asyncio
import os
import re
import difflib
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from api.config import settings

# Manual Transliteration Map
TRANS = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
    'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
    'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
    'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
    'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya'
}

def normalize(s):
    s = str(s).lower().strip()
    res = []
    for char in s:
        if char in TRANS:
            res.append(TRANS[char])
        elif 'a' <= char <= 'z' or '0' <= char <= '9':
            res.append(char)
        else:
            res.append('_')
    return "".join(res)

def get_filename_from_url(url):
    if not url: return ""
    return url.split('/')[-1]

async def main():
    db_url = settings.database_url.replace("postgresql://", "postgresql+asyncpg://")
    engine = create_async_engine(db_url)

    # 1. Get all files
    img_dir = "/root/chefport-bot/web/images/products"
    try:
        files = os.listdir(img_dir)
        # Filter for valid images
        files = [f for f in files if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
        print(f"Found {len(files)} files in {img_dir}")
    except FileNotFoundError:
        print(f"Directory {img_dir} not found!")
        return

    async with engine.begin() as conn:
        # 2. Get all products
        result = await conn.execute(text("SELECT id, name, image_url FROM products"))
        products = result.fetchall()
        
        updates = 0
        cleared = 0
        
        for pid, name, current_url in products:
            slug = normalize(name)
            
            # --- VALIDATION OF CURRENT IMAGE ---
            current_filename = get_filename_from_url(current_url)
            keep_current = False
            ratio = 0.0
            
            if current_filename:
                # Calculate similarity between slug and current filename
                # We strip extension from filename for comparison
                fname_no_ext = os.path.splitext(current_filename)[0]
                fname_slug = normalize(fname_no_ext) 
                
                # Simple check: does the filename contain the product name parts?
                # Or use difflib
                ratio = difflib.SequenceMatcher(None, slug, fname_slug).ratio()
                
                # Strict check for short names or very different strings
                if ratio > 0.8: # STRICT KEEP
                    keep_current = True
                elif slug in fname_slug: # Exact slug inside filename
                    keep_current = True
            
            # --- FINDING BETTER MATCH ---
            
            # Helper to clean string for comparison (remove all separators)
            def clean(s): return re.sub(r'[^a-z0-9]', '', s)
            
            slug_clean = clean(slug)
            
            matches = []
            for f in files:
                f_no_ext = os.path.splitext(f)[0]
                f_base_clean = clean(normalize(f_no_ext))
                
                # Score
                if slug_clean == f_base_clean:
                    score = 1.0
                elif slug_clean in f_base_clean:
                    score = 0.9 # Product name is substring of filename
                elif f_base_clean in slug_clean:
                    score = 0.8 # Filename is substring of product name (less ideal)
                else:
                    score = difflib.SequenceMatcher(None, slug, normalize(f_no_ext)).ratio()
                
                if score > 0.8: # Strict candidate threshold
                    matches.append((score, f))
            
            # Sort by score
            matches.sort(key=lambda x: x[0], reverse=True)
            
            new_url = None
            best_score = 0
            if matches:
                best_score, best_file = matches[0]
                if best_score > 0.85: # Very strict match required to REPLACE
                    new_url = f"/web/images/products/{best_file}"
            
            # --- APPLY ACTION ---
            
            action = None
            val = None
            
            if new_url and new_url != current_url:
                action = "UPDATE"
                val = new_url
            elif not new_url and current_url and not keep_current:
                 # Strict clear: if we dont have a better match and current is not good enough -> Clear
                 print(f"[CLEAR] ID {pid}: '{name}' -> NULL (was '{current_filename}' score {ratio:.2f})")
                 action = "CLEAR"
                 val = None
            
            if action == "UPDATE":
                print(f"[UPDATE] ID {pid}: '{name}' -> '{val}' (score {best_score:.2f})")
                await conn.execute(
                    text("UPDATE products SET image_url = :url WHERE id = :id"),
                    {"url": val, "id": pid}
                )
                updates += 1
            elif action == "CLEAR":
                await conn.execute(
                    text("UPDATE products SET image_url = NULL WHERE id = :id"),
                    {"id": pid}
                )
                cleared += 1
                
    print(f"Finished. Updated: {updates}, Cleared: {cleared}")

if __name__ == "__main__":
    asyncio.run(main())
