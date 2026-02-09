import asyncio
import os
import re
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from api.config import settings

# Manual Transliteration Map (approximate for standard RU->EN mappings used in filenames)
TRANS = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
    'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
    'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
    'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
    'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya'
}

def normalize(s):
    s = s.lower().strip()
    res = []
    for char in s:
        if char in TRANS:
            res.append(TRANS[char])
        elif 'a' <= char <= 'z' or '0' <= char <= '9':
            res.append(char)
        else:
            res.append('_')
    # Collapse multiple underscores
    return re.sub(r'_+', '_', "".join(res)).strip('_')

async def main():
    db_url = settings.database_url
    # Use asyncpg
    engine = create_async_engine(db_url)
    
    img_dir = "/root/chefport-bot/web/images/products"
    if not os.path.exists(img_dir):
        print(f"Error: {img_dir} does not exist.")
        return

    files = os.listdir(img_dir)
    print(f"Found {len(files)} files in {img_dir}.")

    # Pre-process filenames for faster matching
    # Map normalized_filename -> actual_filename
    file_map = {}
    for f in files:
        name_part = os.path.splitext(f)[0]
        norm = normalize(name_part)
        file_map[norm] = f

    # Also keep a list for fuzzy matching
    norm_files_list = list(file_map.keys())

    async with engine.begin() as conn:
        result = await conn.execute(text("SELECT id, name, image_url FROM products"))
        products = result.fetchall()
        
        updated_count = 0
        
        for pid, name, current_url in products:
            # Transliterate product name
            slug = normalize(name)
            
            # 1. Exact Match
            match = None
            if slug in file_map:
                match = file_map[slug]
            
            # 2. Contains Match (Filename contains slug)
            if not match:
                for nf in norm_files_list:
                    if slug in nf:
                        match = file_map[nf]
                        break
            
            # 3. Reverse Contains (Slug contains filename - unlikely but possible for short filenames)
            if not match:
                for nf in norm_files_list:
                    if nf in slug and len(nf) > 5: # avoid matching short random strings
                        match = file_map[nf]
                        break

            # Special case for "pl.b." vs "plb" etc
            if not match:
                # Try replacing spaces with nothing instead of underscore
                pass 

            if match:
                new_url = f"/web/images/products/{match}"
                if current_url != new_url:
                    print(f"[UPDATE] ID={pid}: {name} -> {match}")
                    await conn.execute(text("UPDATE products SET image_url = :url WHERE id = :id"), {"url": new_url, "id": pid})
                    updated_count += 1
                else:
                    # print(f"[OK] ID={pid}: {name}")
                    pass
            else:
                pass
                # print(f"[NO MATCH] ID={pid}: {name} (slug: {slug})")

        print(f"Total updated: {updated_count}")

if __name__ == "__main__":
    asyncio.run(main())
