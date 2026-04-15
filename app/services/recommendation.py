from collections import Counter

from sqlalchemy.orm import Session

from app.models.enums import InteractionType
from app.repositories.event import EventRepository
from app.repositories.interaction import InteractionRepository


class RecommendationService:
    INTERACTION_WEIGHT = {
        InteractionType.VIEW.value: 1.0,
        InteractionType.HOLD.value: 2.0,
        InteractionType.PURCHASE.value: 4.0,
    }

    def __init__(self, db: Session) -> None:
        self.events = EventRepository(db)
        self.interactions = InteractionRepository(db)

    def recommend_for_user(self, user_id: str, limit: int = 10) -> list[dict]:
        interactions = self.interactions.list_by_user(user_id)
        if not interactions:
            return []

        interacted_event_ids = {item.event_id for item in interactions}
        all_events = {event.id: event for event in self.events.list_recommendable()}

        profile = Counter()
        for item in interactions:
            event = all_events.get(item.event_id)
            if not event:
                continue
            weight = self.INTERACTION_WEIGHT[item.interaction_type.value]
            for category in event.categories:
                profile[f"category:{category.name}"] += weight
            for tag in event.tags:
                profile[f"tag:{tag.name}"] += weight * float(tag.weight)

        recommendations = []
        for event_id, event in all_events.items():
            if event_id in interacted_event_ids:
                continue
            score = 0.0
            reasons = []
            for category in event.categories:
                contribution = profile.get(f"category:{category.name}", 0)
                score += contribution
                if contribution:
                    reasons.append(f"matches category '{category.name}'")
            for tag in event.tags:
                contribution = profile.get(f"tag:{tag.name}", 0)
                score += contribution
                if contribution:
                    reasons.append(f"similar tag '{tag.name}'")
            if score > 0:
                recommendations.append(
                    {"event_id": event.id, "title": event.title, "score": round(score, 2), "reasons": reasons[:3]}
                )

        recommendations.sort(key=lambda item: item["score"], reverse=True)
        return recommendations[:limit]
