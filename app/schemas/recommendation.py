from pydantic import BaseModel
from uuid import UUID


class RecommendationItem(BaseModel):
    event_id: UUID
    title: str
    score: float
    reasons: list[str]
