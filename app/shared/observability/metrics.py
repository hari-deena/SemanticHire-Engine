# from prometheus_client import Counter, Histogram

# REQUEST_COUNT = Counter(
#     "api_requests_total",
#     "Total API requests"
# )

# PIPELINE_TIME = Histogram(
#     "resume_pipeline_duration_seconds",
#     "Pipeline execution time"
# )


# app/shared/observability/metrics.py
from prometheus_client import Counter, Histogram, Gauge
import structlog

# Metrics
RESUME_UPLOADS = Counter("resume_uploads_total", "Total uploads", ["status"])
PROCESSING_DURATION = Histogram("resume_processing_seconds", "Processing time")
SKILL_EXTRACTION_ERRORS = Counter("skill_extraction_errors_total", "Extraction failures")

# Structured logging
logger = structlog.get_logger()

# In pipeline
def run_pipeline(file_path: str, resume_id: int, idempotency_key: str):
    with PROCESSING_DURATION.time():
        try:
            logger.info("pipeline_start", resume_id=resume_id, idempotency_key=idempotency_key)
            
            # ... processing steps ...
            
            RESUME_UPLOADS.labels(status="success").inc()
            logger.info("pipeline_success", resume_id=resume_id, chunks=len(chunks))
            
        except Exception as e:
            RESUME_UPLOADS.labels(status="failed").inc()
            SKILL_EXTRACTION_ERRORS.inc()
            logger.exception("pipeline_failed", resume_id=resume_id, error=str(e))
            raise