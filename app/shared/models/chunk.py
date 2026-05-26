# app/shared/models/chunk.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
import hashlib

class ResumeSection(str, Enum):
    SKILLS = "skills"
    EXPERIENCE = "experience"
    EDUCATION = "education"
    PROJECTS = "projects"
    CERTIFICATIONS = "certifications"
    SUMMARY = "summary"
    UNKNOWN = "unknown"

class ChunkMetadata(BaseModel):
    resume_id: int
    chunk_index: int
    section: ResumeSection
    page_number: Optional[int] = None
    char_start: int
    char_end: int
    token_count: Optional[int] = None
    context_window: Optional[str] = None  # ±2 sentences for skill linking
    skills_mentioned: List[str] = Field(default_factory=list)
    entities: Dict[str, Any] = Field(default_factory=dict)  # companies, dates, roles
    embedding_cache_key: Optional[str] = None
    
    def generate_cache_key(self, content: str) -> str:
        """Deterministic key for embedding cache"""
        payload = f"{self.resume_id}:{self.chunk_index}:{content}:{self.section}"
        return hashlib.sha256(payload.encode()).hexdigest()