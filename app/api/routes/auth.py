from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser, DbSession
from app.core.responses import success_response
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
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


@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordRequest, db: DbSession):
    try:
        AuthService(db).request_password_reset(payload)
        return success_response({"message": "If the email exists, a verification code has been sent."})
    except ConnectionError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="unable to send email") from exc


@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest, db: DbSession):
    try:
        AuthService(db).reset_password(payload)
        return success_response({"message": "Password has been reset."})
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/me")
def me(user: CurrentUser):
    return success_response(UserResponse.model_validate(user))
