from fastapi import APIRouter, UploadFile, File, HTTPException
from pathlib import Path
import uuid
import shutil

router = APIRouter(prefix="/upload", tags=["upload"])

UPLOAD_DIR = Path("/root/chefport-bot/web/images/products")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@router.post("/product-image")
async def upload_product_image(file: UploadFile = File(...)):
    """Upload product image"""
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Generate unique filename
        ext = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
        filename = f"{uuid.uuid4()}.{ext}"
        file_path = UPLOAD_DIR / filename
        
        # Save file
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Return URL path
        return {
            "success": True,
            "url": f"/images/products/{filename}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
