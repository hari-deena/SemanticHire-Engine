from fastapi import APIRouter, Depends, UploadFile, File
from app.features.resume.application.use_cases.upload_resume import upload_resume_use_case
from sqlalchemy.orm import Session

from app.shared.infrastructure.db.session import get_db

router = APIRouter()

@router.post("/upload")
async def upload(file: UploadFile = File(...), db: Session = Depends(get_db)):
    return await upload_resume_use_case(file=file, db=db)