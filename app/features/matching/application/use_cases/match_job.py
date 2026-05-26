# from fastapi import UploadFile, HTTPException
# import os
# import aiofiles
# from sqlalchemy.orm import Session
# import logging

# from app.features.resume.application.pipelines.resume_pipeline import safe_extract_skills
# from app.features.resume.processing.skill_extractor import extract_skills
# from app.shared.ai.embeddings.embedding_service import generate_embeddings
# from app.shared.ai.vector_db.chroma_client import get_client, get_collection
# from app.shared.infrastructure.db.repositories.resume_repository import get_resumes_by_skills
# logger = logging.getLogger(__name__)



# def calculate_score(distance, skill_count, total_skills):
#     skill_score = skill_count / total_skills if total_skills else 0
#     semantic_score = 1 - distance  # invert distance

#     final = (semantic_score * 0.6) + (skill_score * 0.4)
#     return round(final * 100, 2)
  

# from app.shared.ai.vector_db.chroma_client import get_collection



# async def match_resumes_from_jd(db: Session, description: str):
    
#     try:
#         logger.info("Matching started")

#         # ✅ 1. Extract skills
#         # skills = extract_skills(description)
#         # skills = [s.lower().strip() for s in skills]
#         # print(f"Extracted skills from job description: {skills}")
#         # print("-----------------> type", type(skills))
        
#         # 1. Extract skills
#         # ✅ 1. Extract skills (ONLY ONCE)
#         skills = safe_extract_skills(description)
#         skills = [s.lower().strip() for s in skills]
        
#         print(f"Extracted skills from job description: {skills}")
#         print("-----------------> type", type(skills))


#         if not skills:
#             return {"matches": [], "message": "No skills extracted"}

#         # ✅ 2. SQL filter (SYNC CALL)
#         sql_results = get_resumes_by_skills(db, skills)

#         skill_map = {
#             row.id: row.skill_count
#             for row in sql_results
#         }
        
#         print(f"SQL skill map: {skill_map}")

#         if not skill_map:
#             return {"matches": [], "message": "No skill match"}

#         # ✅ 3. Chroma search
#         collection = get_collection()

#         query_vector = generate_embeddings([description])[0]

#         results = collection.query(
#             query_embeddings=[query_vector],   # ✅ FIX
#             n_results=50
#         )
        
#         print(f"Chroma results: {results}")  # ✅ DEBUGGING LOG

#         documents = results.get("documents", [[]])[0]
#         metadatas = results.get("metadatas", [[]])[0]
#         distances = results.get("distances", [[]])[0]

#         # ✅ SAFETY CHECK
#         if not (documents and metadatas and distances):
#             return {"matches": [], "message": "No semantic results"}

#         min_len = min(len(documents), len(metadatas), len(distances))

#         # ✅ 4. Merge safely
#         final_results = []

#         for i in range(min_len):

#             metadata = metadatas[i] or {}
#             distance = distances[i]

#             resume_id = metadata.get("resume_id")

#             if not resume_id:
#                 continue

#             if resume_id not in skill_map:
#                 continue

#             skill_count = skill_map[resume_id]

#             score = calculate_score(
#                 distance,
#                 skill_count,
#                 len(skills)
#             )

#             final_results.append({
#                 "resume_id": resume_id,
#                 "file_name": metadata.get("file_name", "unknown"),
#                 "score": score,
#                 "skill_matches": skill_count
#             })

#         final_results.sort(key=lambda x: x["score"], reverse=True)

#         return {
#             "skills": skills,
#             "total": len(final_results),
#             "matches": final_results[:10]
#         }

#     except Exception as e:
#         logger.exception(f"Matching failed: {str(e)}")  # ✅ IMPORTANT FIX
#         raise HTTPException(status_code=500, detail=str(e))    
    
    
# match_job.py

from fastapi import HTTPException
from sqlalchemy.orm import Session
import logging

from app.shared.ai.vector_db.chroma_client import get_collection
from app.shared.ai.embeddings.embedding_service import generate_embeddings
from app.shared.infrastructure.db.repositories.resume_repository import get_resumes_by_skills
from app.features.resume.application.pipelines.resume_pipeline import safe_extract_skills

logger = logging.getLogger(__name__)


def calculate_score(distance, skill_count, total_skills):
    skill_score = skill_count / total_skills if total_skills else 0
    semantic_score = 1 - distance

    return round(((semantic_score * 0.6) + (skill_score * 0.4)) * 100, 2)


async def match_resumes_from_jd(db: Session, description: str):

    try:
        logger.info("Matching started")

        # 1. Skills
        skills = safe_extract_skills(description)
        skills = [s.lower().strip() for s in skills]

        if not skills:
            return {"matches": [], "message": "No skills extracted"}

        # 2. SQL filter
        sql_results = get_resumes_by_skills(db, skills)

        skill_map = {
            row.id: row.skill_count
            for row in sql_results
        }

        if not skill_map:
            return {"matches": [], "message": "No skill match"}

        # 3. Embedding
        query_vector = generate_embeddings([description])[0]

        # 4. Chroma query
        collection = get_collection()

        results = collection.query(
            query_embeddings=[query_vector],
            n_results=50
        )

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]
        
        
        collection = get_collection()
        print("🔥 VECTOR COUNT:", collection.count())

        if not documents:
            return {"matches": [], "message": "No semantic results"}

        # ✅ 5. Aggregate per resume (IMPORTANT FIX)
        resume_scores = {}

        for i in range(len(documents)):

            metadata = metadatas[i] or {}
            distance = distances[i]

            resume_id = metadata.get("resume_id")

            if not resume_id or resume_id not in skill_map:
                continue

            skill_count = skill_map[resume_id]

            score = calculate_score(
                distance,
                skill_count,
                len(skills)
            )

            # keep best score per resume
            if resume_id not in resume_scores:
                resume_scores[resume_id] = score
            else:
                resume_scores[resume_id] = max(resume_scores[resume_id], score)

        final_results = [
            {
                "resume_id": rid,
                "score": score,
                "skill_matches": skill_map[rid]
            }
            for rid, score in resume_scores.items()
        ]

        final_results.sort(key=lambda x: x["score"], reverse=True)
        
        

        return {
            "skills": skills,
            "total": len(final_results),
            "matches": final_results[:10]
        }

    except Exception as e:
        logger.exception(f"Matching failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
    
    