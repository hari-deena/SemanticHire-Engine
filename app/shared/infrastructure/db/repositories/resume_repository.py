from sqlalchemy.orm import Session
from app.shared.infrastructure.db.models.resume_model import Resume
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from ..models.resume_model import Resume
from datetime import datetime
from typing import Optional

class ResumeRepository:

    def __init__(self, db: Session):
        self.db = db

    def create(self, data: dict):
        resume = Resume(**data)
        self.db.add(resume)
        self.db.commit()
        self.db.refresh(resume)
        return resume.id

    def update_status(self, resume_id: int, status: str, error: str = None):
        resume = self.db.query(Resume).filter(Resume.id == resume_id).first()
        if resume:
            resume.status = status
            if error:
                resume.error = error
            self.db.commit()

    def get_status(self, resume_id: int):
        resume = self.db.query(Resume).filter(Resume.id == resume_id).first()
        return resume.status if resume else None
    
# app/shared/infrastructure/db/repositories/resume_skill_repository.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, and_
from typing import List, Optional, Set
from ..models.resume_model import ResumeSkill

class ResumeSkillRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    def add_skill(self, resume_id: int, skill_name: str) -> ResumeSkill:
        """Adds a single skill (no duplicate check at DB level)."""
        new_skill = ResumeSkill(resume_id=resume_id, skill=skill_name.strip().lower())
        self.db.add(new_skill)
        self.db.commit()
        self.db.refresh(new_skill)
        return new_skill

    def add_skills_if_not_exists(self, resume_id: int, skills: List[str]) -> List[ResumeSkill]:
        """
        Adds only skills that are NOT already present for the resume_id.
        Returns list of newly added skills.
        """
        if not skills:
            return []

        # Normalize input skills
        normalized_skills = list(set(s.strip().lower() for s in skills if s.strip()))
        if not normalized_skills:
            return []

        # Fetch existing skills for this resume
        existing = self.get_skills_by_resume_id(resume_id)
        existing_skill_names = {s.skill.lower() for s in existing}

        # Filter out duplicates
        new_skills = [s for s in normalized_skills if s not in existing_skill_names]
        if not new_skills:
            return []  # Nothing to add

        # Insert new skills
        skill_instances = [ResumeSkill(resume_id=resume_id, skill=skill) for skill in new_skills]
        self.db.add_all(skill_instances)
        self.db.commit()

        for skill in skill_instances:
            self.db.refresh(skill)

        return skill_instances

    def has_any_skills(self, resume_id: int) -> bool:
        """
        Quick check: returns True if resume already has any skills.
        More efficient than fetching all skills when you only need existence check.
        """
        stmt = select(ResumeSkill.id).where(ResumeSkill.resume_id == resume_id).limit(1)
        result = self.db.execute(stmt)
        return result.scalar_one_or_none() is not None

    def get_skills_by_resume_id(self, resume_id: int) -> List[ResumeSkill]:
        """Retrieves all skills for a resume."""
        stmt = select(ResumeSkill).where(ResumeSkill.resume_id == resume_id)
        result = self.db.execute(stmt)
        return result.scalars().all()

    def get_skill_names_by_resume_id(self, resume_id: int) -> Set[str]:
        """Returns a set of skill names (lowercase) for quick lookup."""
        skills = self.get_skills_by_resume_id(resume_id)
        return {s.skill.lower() for s in skills}

    def delete_skills_by_resume_id(self, resume_id: int) -> None:
        """Deletes all skills for a resume (use with caution)."""
        stmt = delete(ResumeSkill).where(ResumeSkill.resume_id == resume_id)
        self.db.execute(stmt)
        self.db.commit()

# repository/resume_repo.py
# repository/resume_repository.py

from sqlalchemy import select, func
from sqlalchemy.orm import Session
# from app.models import Resume, ResumeSkill


# repository

from sqlalchemy import select, func

def get_resumes_by_skills(db: Session, skills: list[str]):

    skills = [s.lower().strip() for s in skills]

    query = (
        select(
            Resume.id,
            Resume.file_name,
            func.count(ResumeSkill.skill).label("skill_count")
        )
        .join(ResumeSkill, Resume.id == ResumeSkill.resume_id)
        .where(func.lower(ResumeSkill.skill).in_(skills))  # ✅ FIX
        .group_by(Resume.id)
    )

    result = db.execute(query)
    return result.fetchall()



