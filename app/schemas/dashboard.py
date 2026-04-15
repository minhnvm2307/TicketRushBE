from app.schemas.common import APIModel


class DashboardResponse(APIModel):
    event_id: str
    sold_count: int
    locked_count: int
    available_count: int
    revenue: float


class DemographicsResponse(APIModel):
    event_id: str
    age_distribution: dict[str, int]
    gender_distribution: dict[str, int]
