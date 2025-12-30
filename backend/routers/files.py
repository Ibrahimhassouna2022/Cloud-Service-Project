from fastapi import APIRouter, UploadFile, File, HTTPException
import shutil
import os
import uuid
from typing import List
from config import STORAGE_PATH

router = APIRouter(prefix="/files", tags=["Files"])

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        # Use original filename for user friendliness
        # In a real production app, we would sanitize this or use a DB mapping
        file_location = os.path.join(STORAGE_PATH, file.filename)
        
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        return {
            "filename": file.filename,
            "path": file_location,
            "message": "File uploaded successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/")
def list_files():
    try:
        files = []
        if os.path.exists(STORAGE_PATH):
            for filename in os.listdir(STORAGE_PATH):
                file_path = os.path.join(STORAGE_PATH, filename)
                if os.path.isfile(file_path):
                    files.append({
                        "filename": filename,
                        "size": os.path.getsize(file_path)
                    })
        return files
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
