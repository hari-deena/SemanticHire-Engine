# import logging
# import time

# from app.features.resume.processing.loader import load_document
# from app.features.resume.processing.splitter import split_text
# from app.features.resume.processing.skill_extractor import extract_skills
# from app.shared.security.pii_handler import mask_pii
# from app.shared.ai.embeddings.embedding_service import generate_embeddings
# # from app.shared.ai.vector_db.chroma_client import store_vectors
# from app.shared.ai.vector_db.vector_store_service import store_vectors
# from app.shared.infrastructure.db.session import SessionLocal
# from app.shared.infrastructure.db.repositories.resume_repository import ResumeRepository
# from app.shared.ai.embeddings.validation import validate_embeddings

# logger = logging.getLogger(__name__)

# MAX_CHUNKS = 200
# MAX_TEXT_LENGTH = 3000


# def safe_extract_skills(text: str):
#     for attempt in range(2):
#         try:
#             return extract_skills(text)
#         except Exception as e:
#             logger.warning("skill_extraction_failed", extra={"error": str(e), "attempt": attempt + 1})
#     return []




# def run_pipeline(file_path: str, resume_id: int):

#     start_time = time.time()

#     db = SessionLocal()
#     # repo = ResumeRepository(db)

#     try:
#         # 🔥 Idempotency check
#         # if repo.get_status(resume_id) == "completed":
#         #     logger.info("already_processed", extra={"resume_id": resume_id})
#         #     return

#         logger.info("pipeline_started", extra={"resume_id": resume_id})

#         # 1. Load
#         text = load_document(file_path)

#         if not text or len(text.strip()) < 50:
#             raise ValueError("Invalid resume content")

#         # 2. Mask PII
#         text = mask_pii(text)

#         # 3. Split
#         chunks = split_text(text)

#         if not chunks:
#             raise ValueError("No chunks generated")

#         if len(chunks) > MAX_CHUNKS:
#             logger.warning("chunk_limit_exceeded", extra={"resume_id": resume_id})
#             chunks = chunks[:MAX_CHUNKS]

#         # 4. Skills
#         skills = safe_extract_skills(text[:MAX_TEXT_LENGTH])

#         # 5. Embeddings
#         vectors = generate_embeddings(chunks)

#         validate_embeddings(chunks, vectors)

#         # 6. Metadata
#         metadatas = [
#             {
#                 "resume_id": resume_id,
#                 "chunk_index": i,
#                 "skills": skills
#             }
#             for i in range(len(chunks))
#         ]

#         ids = [f"{resume_id}_{i}" for i in range(len(chunks))]

#         # 🔥 Deduplication check (optional improvement)
#         # if vector already exists → skip

#         # 7. Store
#         store_vectors(vectors, metadatas, ids)

#         total_time = time.time() - start_time

#         logger.info(
#             "pipeline_completed",
#             extra={
#                 "resume_id": resume_id,
#                 "chunks": len(chunks),
#                 "time": round(total_time, 2)
#             }
#         )

#     except Exception as e:
#         logger.exception(
#             "pipeline_failed",
#             extra={"resume_id": resume_id, "error": str(e)}
#         )
#         raise

#     finally:
#         db.close()


import logging
import time

from sqlalchemy.orm import Session

from app.features.resume.processing.loader import load_document
from app.features.resume.processing.splitter import split_text
from app.features.resume.processing.skill_extractor import extract_skills
from app.shared.infrastructure.db.repositories.resume_repository import ResumeRepository, ResumeSkillRepository
from app.shared.security.pii_handler import mask_pii
from app.shared.ai.embeddings.embedding_service import generate_embeddings
from app.shared.ai.vector_db.vector_store_service import store_vectors
from app.shared.infrastructure.db.session import SessionLocal, get_db
from app.shared.ai.embeddings.validation import validate_embeddings
import re
logger = logging.getLogger(__name__)

MAX_CHUNKS = 200
MAX_TEXT_LENGTH = 3000


def safe_extract_skills(text: str):

    for attempt in range(3):
        try:
            return extract_skills(text)

        except Exception as e:
            logger.warning(f"skill_extraction_failed_attempt_{attempt+1}: {e}")

            time.sleep(1)

    # 🔥 HARD FALLBACK (IMPORTANT)
    logger.error("skill_extraction_fallback_rule_based")

    return list(set(re.findall(r"\b(python|java|sql|fastapi|django|aws)\b", text.lower())))


def run_pipeline(file_path: str, resume_id: int, db: Session):

    start_time = time.time()
    
    repo = ResumeRepository(db)
    skill_repo = ResumeSkillRepository(db)
    
    try:
        
        # 🔥 Idempotency check
        if repo.get_status(resume_id) == "completed":
            logger.info("already_processed", extra={"resume_id": resume_id})
            return
        
        logger.warning(f"[PIPELINE START] resume_id={resume_id}")

        # ✅ 1. Load
        pages = load_document(file_path)

        if not pages:
            raise ValueError("Empty document")

        text = "\n".join(pages)
        logger.warning(f"[LOAD DONE] length={len(text)}")

        if len(text.strip()) < 50:
            raise ValueError("Invalid resume content")

        # ✅ 2. Mask PII
        text = mask_pii(text)
        logger.warning("[PII MASKED]")

        # ✅ 3. Split
        chunks = split_text(text)
        if not chunks:
            raise ValueError("No chunks generated")

        if len(chunks) > MAX_CHUNKS:
            chunks = chunks[:MAX_CHUNKS]

        logger.warning(f"[CHUNKS CREATED] count={len(chunks)}")

        # ✅ 4. Skills
        skills = safe_extract_skills(text[:MAX_TEXT_LENGTH])
        logger.warning(f"[SKILLS EXTRACTED] {skills}")
        
        
        if skills:
            has_skills = skill_repo.has_any_skills(resume_id)
            if not has_skills:
                added = skill_repo.add_skills_if_not_exists(resume_id, skills)
                logger.info(f"Added {len(added)} new skills for resume {resume_id}")
        db.commit()  # ✅ Commit skill updates before embeddings


        # ✅ 5. Embeddings
        # embeddings
        vectors = generate_embeddings(chunks)
        if not vectors or len(vectors) != len(chunks):
            raise RuntimeError("Embedding generation failed")

        validate_embeddings(chunks, vectors)
        logger.warning("[EMBEDDINGS GENERATED]")

        # ✅ 6. Metadata
        metadatas = [
            {
                "resume_id": resume_id,
                "chunk_index": i,
                "skills": skills,
                "file_name": f"resume_{resume_id}"
            }
            for i in range(len(chunks))
        ]

        ids = [f"{resume_id}_{i}" for i in range(len(chunks))]

        # ✅ 7. Store
        store_vectors(vectors, metadatas, ids, chunks)

        total_time = time.time() - start_time

        logger.warning(f"[PIPELINE SUCCESS] resume_id={resume_id}, time={round(total_time,2)}s")

    except Exception as e:
        logger.exception("[PIPELINE FAILED]")
        db.rollback()  # ✅ Rollback on failure
        raise
