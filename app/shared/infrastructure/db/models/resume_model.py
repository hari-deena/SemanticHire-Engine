from sqlalchemy import create_engine, Column, Integer, String, Text, TIMESTAMP, ForeignKey, BIGINT, func
from sqlalchemy.orm import relationship
from datetime import datetime
from ..session import Base


class Resume(Base):
    __tablename__ = 'resumes'

    id = Column(BIGINT, primary_key=True, autoincrement=True)
    file_name = Column(String(255))
    file_path = Column(Text)
    status = Column(String(50), default='PROCESSED')
    created_at = Column(TIMESTAMP, server_default=func.now())

    skills = relationship("ResumeSkill", back_populates="resume")

class ResumeSkill(Base):
    __tablename__ = 'resume_skills'

    id = Column(BIGINT, primary_key=True, autoincrement=True)
    resume_id = Column(BIGINT, ForeignKey('resumes.id'), nullable=False)
    skill = Column(String(100), nullable=False)

    resume = relationship("Resume", back_populates="skills")