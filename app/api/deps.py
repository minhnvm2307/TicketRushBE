from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.redis import RedisKey, get_redis_client, redis_is_enabled
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.enums import UserRole
from app.repositories.user import UserRepository

DbSession = Annotated[Session, Depends(get_db)]


def get_current_user(
    db: DbSession, authorization: Annotated[str | None, Header(alias="Authorization")] = None
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing bearer token")
    token = authorization.removeprefix("Bearer ").strip()
    try:
        payload = decode_access_token(token)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    session_id = payload.get("sid")
    if session_id and redis_is_enabled():
        redis = get_redis_client()
        session_user_id = redis.get(RedisKey.auth_session(session_id))
        if session_user_id != str(payload["sub"]):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="session has expired")
    user = UserRepository(db).get_by_id(payload["sub"])
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="user not found")
    setattr(user, "_token_payload", payload)
    return user


CurrentUser = Annotated[object, Depends(get_current_user)]


def require_admin(user: CurrentUser):
    if user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="admin only")
    return user


AdminUser = Annotated[object, Depends(require_admin)]
