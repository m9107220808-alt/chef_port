#!/usr/bin/env python3
"""
Fix image paths in database:
- Convert Google Drive URLs to local paths
- Match products with downloaded images
"""
import sqlite3
import os
import re
from pathlib import Path

DB_PATH = "chefport.db"
IMAGES_DIR = "web/images/products"

def normalize_name(name):
    """Normalize product name for matching"""
    # Remove special chars, lowercase, strip spaces
    name = re.sub(r'[^\w\s]', '', name.lower())
    name = re.sub(r'\s+', '_', name.strip())
    return name

def main():
    print("🔧 Fixing image paths in database...")
    
    # Get all image files
    image_files = {}
    for f in Path(IMAGES_DIR).glob("*"):
        if f.is_file() and f.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp']:
            # Store both full name and normalized name
            image_files[f.name] = f"/web/images/products/{f.name}"
    
    print(f"📁 Found {len(image_files)} local images")
    
    # Connect to database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get all products with Google Drive URLs
    cursor.execute("""
        SELECT id, name, image_url 
        FROM products 
        WHERE image_url LIKE '%drive.google.com%' OR image_url IS NULL
    """)
    
    products = cursor.fetchall()
    print(f"📦 Found {len(products)} products with Google Drive or missing images")
    
    updated = 0
    not_found = []
    
    for product_id, name, old_url in products:
        # Try to find matching image
        normalized = normalize_name(name)
        
        # Strategy 1: Exact match by normalized name
        found_image = None
        for img_name, img_path in image_files.items():
            img_normalized = normalize_name(Path(img_name).stem)
            if normalized in img_normalized or img_normalized in normalized:
                found_image = img_path
                break
        
        if found_image:
            cursor.execute("""
                UPDATE products 
                SET image_url = ? 
                WHERE id = ?
            """, (found_image, product_id))
            updated += 1
            print(f"✅ {name[:40]:40} -> {Path(found_image).name}")
        else:
            not_found.append(name)
            # Set to placeholder or keep Google Drive URL
            print(f"⚠️  {name[:40]:40} -> No local image found")
    
    conn.commit()
    conn.close()
    
    print(f"\n📊 Summary:")
    print(f"   Updated: {updated}")
    print(f"   Not found: {len(not_found)}")
    
    if not_found and len(not_found) < 20:
        print(f"\n⚠️  Products without local images:")
        for name in not_found[:10]:
            print(f"   - {name}")

if __name__ == "__main__":
    main()
