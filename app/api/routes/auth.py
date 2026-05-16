from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser, DbSession
from app.core.responses import success_response
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UpdateProfileRequest,
    UserProfileResponse,
    UserResponse,
)
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: DbSession):
    try:
        user = AuthService(db).register(payload)
        token = AuthService(db).login(LoginRequest(email=payload.email, password=payload.password))
        return success_response(TokenResponse(access_token=token, user=UserResponse.model_validate(user)), status_code=status.HTTP_201_CREATED)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/login")
def login(payload: LoginRequest, db: DbSession):
    try:
        auth_service = AuthService(db)
        token = auth_service.login(payload)
        user = auth_service.users.get_by_email(payload.email)
        return success_response(TokenResponse(access_token=token, user=UserResponse.model_validate(user)))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


@router.get("/me")
def me(user: CurrentUser):
    return success_response(UserProfileResponse.model_validate(user))


@router.patch("/me")
def update_me(payload: UpdateProfileRequest, user: CurrentUser, db: DbSession):
    try:
        updated_user = AuthService(db).update_profile(user.id, payload)
        return success_response(UserProfileResponse.model_validate(updated_user))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
