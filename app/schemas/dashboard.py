from app.schemas.common import APIModel
from uuid import UUID

class DashboardResponse(APIModel):
    event_id: UUID
    sold_count: int
    locked_count: int
    available_count: int
    revenue: float


class DemographicsResponse(APIModel):
    event_id: UUID
    age_distribution: dict[str, int]
    gender_distribution: dict[str, int]
