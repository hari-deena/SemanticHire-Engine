# app/main.py

from fastapi import FastAPI
from app.api.v1.router import api_router
from app.shared.logging.logger import setup_logger

# from app.shared.observability.tracing import setup_tracing

# tracer = setup_tracing(app)

setup_logger()

app = FastAPI()

# app.include_router(resume.router, prefix="/resume", tags=["Resume"])

app.include_router(api_router, prefix="/api/v1")

