
from fastapi import UploadFile, HTTPException
import os
import aiofiles
from sqlalchemy.orm import Session

from app.shared.ai.llm.providers import LLMProvider
from app.shared.utils.file_service import FileService
from app.shared.infrastructure.db.session import get_db
from app.shared.infrastructure.db.repositories.resume_repository import ResumeRepository
from app.features.resume.workers.resume_tasks import process_resume_task
import logging
logger = logging.getLogger(__name__)
UPLOAD_DIR = "uploads"


async def upload_resume_use_case(file: UploadFile, db:Session):
    
    logger.info("Received file upload request: %s", file.filename)  
    

    if not file.filename:
        raise HTTPException(status_code=400, detail="Invalid file")

    os.makedirs(UPLOAD_DIR, exist_ok=True)

    filename = FileService.generate_secure_filename(file.filename)
    path = os.path.join(UPLOAD_DIR, filename)
    
    logger.info("Saving file to: %s", path)  # Debug log

    try:
        async with aiofiles.open(path, "wb") as f:
            while chunk := await file.read(1024 * 1024):
                await f.write(chunk)
    except Exception:
        raise HTTPException(status_code=500, detail="File save failed")
    
    logger.info("File saved successfully: %s", path)  # Debug log

    file_hash = FileService.calculate_hash(path)
    
    logger.info("Calculated file hash: %s", file_hash)  # Debug log

    # ✅ db is already a Session object passed from the API layer
    repo = ResumeRepository(db)
    
    try:
        resume_id = repo.create({
            "file_name": filename,
            "file_path": path,
            # "file_hash": file_hash,
            "status": "pending"
        })
        
        db.commit()  # ✅ Commit the transaction
    
    except Exception as e:
        db.rollback()
        logger.error(f"DB Error: {e}")
        raise HTTPException(status_code=500, detail="Database error")


    # ✅ USE QUEUE PROPERLY
    process_resume_task.apply_async(
        args=[path, resume_id],
        queue="high_priority"
    )
    
    return {
        "message": "uploaded",
        "resume_id": resume_id,
        "hash": file_hash
    }
