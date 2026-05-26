# from celery.utils.log import get_task_logger
# from app.shared.infrastructure.messaging.celery_app import celery_app
# from app.features.resume.application.pipelines.resume_pipeline import run_pipeline
# from app.shared.infrastructure.db.session import SessionLocal
# from app.shared.infrastructure.db.repositories.resume_repository import ResumeRepository

# import os

# logger = get_task_logger(__name__)


# @celery_app.task(
#     bind=True,
#     autoretry_for=(ConnectionError, TimeoutError),
#     retry_backoff=True,
#     retry_kwargs={"max_retries": 3},
#     time_limit=300,
#     soft_time_limit=240
# )
# def process_resume_task(self, file_path: str, resume_id: int):

#     # db = SessionLocal()
#     # repo = ResumeRepository(db)

#     try:
#         print(f"Processing resume {resume_id} from file {file_path}")  # Debug log
#         # 🔥 Idempotency check
#         # if repo.get_by_idempotency_key(resume_id) == "completed":
#         #     return

#         # repo.update_status(resume_id, "processing")

#         run_pipeline(file_path, resume_id)
        
#         print(f"Completed processing resume {resume_id}")  # Debug log

#         # repo.update_status(resume_id, "completed")

#     except Exception as e:
#         logger.exception(
#             "Resume processing failed",
#             extra={"resume_id": resume_id, "file_path": file_path}
#         )

#         # repo.update_status(resume_id, "failed", error=str(e))

#         raise self.retry(exc=e)

#     finally:
#         # db.close()

#         # cleanup file
#         if os.path.exists(file_path):
#             os.remove(file_path)



from celery.utils.log import get_task_logger
from app.shared.ai.vector_db.chroma_client import get_collection
from app.shared.infrastructure.db.repositories.resume_repository import ResumeRepository
from app.shared.infrastructure.db.session import SessionLocal
from app.shared.infrastructure.messaging.celery_app import celery_app
from app.features.resume.application.pipelines.resume_pipeline import run_pipeline
import os
from celery.exceptions import Ignore

logger = get_task_logger(__name__)


@celery_app.task(
    bind=True,
    autoretry_for=(ConnectionError, TimeoutError),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
    time_limit=300,
    soft_time_limit=240
)
def process_resume_task(self, file_path: str, resume_id: int):

    success = False
    
    # ✅ FIX: Create a new session instance directly
    db = SessionLocal()
    repo = ResumeRepository(db)

    try:
        logger.warning("processing resume id: %s from file: %s", resume_id, file_path)  
              
        if repo.get_status(resume_id) == "completed":
            return

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        run_pipeline(file_path, resume_id, db)
        
        logger.info("completed processing resume id: %s", resume_id)
        
        repo.update_status(resume_id, "completed")
        db.commit()  # ✅ Commit the status update

        success = True

        logger.warning(f"[TASK SUCCESS] resume_id={resume_id}")
        
        collection = get_collection()
        logger.warning(f"[VECTOR COUNT] ------------------> {collection.count()}")

    except Exception as e:
        logger.exception("[TASK FAILED]")
        db.rollback()  # ✅ Rollback on failure

        # ❌ don't retry for config errors
        if "Not Found" in str(e) or "invalid_api_key" in str(e):
            raise Ignore()
        
        repo.update_status(resume_id, "failed", error=str(e))
        db.commit()  # ✅ Commit the failure status update

        raise self.retry(exc=e)
    finally:
        db.close()  # ✅ Ensure the session is closed

        # cleanup file - ✅ FIX: delete only if success
        # if success and os.path.exists(file_path):
        #     os.remove(file_path)
        #     logger.warning(f"[FILE DELETED] {file_path}")

 
            
            