from fastapi import APIRouter

from app.features.resume.api.resume import router as resume_router

from app.features.matching.api.matching import router as match_router

# from app.api.routes.health import router as health_router

api_router = APIRouter()

api_router.include_router(
    resume_router,
    tags=["Resume"]
)

api_router.include_router(
    match_router,
    tags=["Match"]
)

# api_router.include_router(
#     health_router,
#     tags=["Health"]
# )