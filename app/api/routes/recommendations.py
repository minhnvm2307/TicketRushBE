from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.core.responses import success_response
from app.schemas.recommendation import RecommendationItem
from app.services.recommendation import RecommendationService

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("/me")
def recommendations(db: DbSession, user: CurrentUser):
    return success_response(RecommendationService(db).recommend_for_user(user.id))
