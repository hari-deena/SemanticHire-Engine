from fastapi import APIRouter, Depends, UploadFile, File
from pydantic import BaseModel
from app.features.matching.application.use_cases.match_job import match_resumes_from_jd
from app.features.resume.application.use_cases.upload_resume import upload_resume_use_case
from sqlalchemy.orm import Session

from app.shared.infrastructure.db.session import get_db

router = APIRouter()


# api/matching.py

class JobRequest(BaseModel):
    description: str


@router.post("/match")
async def match_api(payload: JobRequest, session=Depends(get_db)):
    results = await match_resumes_from_jd(session, payload.description)
    return {"matches": results}