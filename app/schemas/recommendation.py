from pydantic import BaseModel


class RecommendationItem(BaseModel):
    event_id: str
    title: str
    score: float
    reasons: list[str]
