from __future__ import annotations

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status

from app.application import AuthConflictError, AuthNotFoundError, AuthService, AuthUnauthorizedError, NotificationService

from .deps import get_auth_service, get_notification_service
from .schemas import (
    AuthAccountDeleteRequest,
    AuthLoginRequest,
    AuthPasswordChangeRequest,
    AuthProfileUpdateRequest,
    AuthRegisterRequest,
    UserAccountRead,
)

router = APIRouter(prefix="/auth", tags=["M5 - Authentification"])

SESSION_COOKIE_NAME = "reservation_session"


def _set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=False,
        samesite="lax",
        path="/",
        max_age=60 * 60 * 24 * 14,
    )


def _clear_session_cookie(response: Response) -> None:
    response.delete_cookie(key=SESSION_COOKIE_NAME, path="/")


@router.post("/register", response_model=UserAccountRead, status_code=status.HTTP_201_CREATED)
def register(
    payload: AuthRegisterRequest,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
    notification_service: NotificationService = Depends(get_notification_service),
) -> UserAccountRead:
    try:
        account, session = auth_service.register(
            full_name=payload.full_name,
            username=payload.username,
            password=payload.password,
            email=payload.email,
            telephone=payload.telephone,
            is_admin=payload.is_admin,
        )
    except AuthConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    _set_session_cookie(response, session.token)

    notification_service.update_preferences(
        utilisateur=account.username,
        email=account.email,
        telephone=account.telephone,
        email_enabled=True,
        sms_enabled=bool(account.telephone),
        weekly_summary_enabled=False,
        is_admin=account.is_admin,
    )

    return UserAccountRead(
        id=account.id or 0,
        full_name=account.full_name,
        username=account.username,
        email=account.email,
        telephone=account.telephone,
        is_admin=account.is_admin,
        created_at=account.created_at,
    )


@router.post("/login", response_model=UserAccountRead)
def login(
    payload: AuthLoginRequest,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
) -> UserAccountRead:
    try:
        account, session = auth_service.login(username=payload.username, password=payload.password)
    except AuthUnauthorizedError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    _set_session_cookie(response, session.token)

    return UserAccountRead(
        id=account.id or 0,
        full_name=account.full_name,
        username=account.username,
        email=account.email,
        telephone=account.telephone,
        is_admin=account.is_admin,
        created_at=account.created_at,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    session_token: str | None = Cookie(default=None, alias=SESSION_COOKIE_NAME),
    auth_service: AuthService = Depends(get_auth_service),
) -> Response:
    auth_service.logout(session_token)
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    _clear_session_cookie(response)
    return response


@router.get("/me", response_model=UserAccountRead)
def me(
    session_token: str | None = Cookie(default=None, alias=SESSION_COOKIE_NAME),
    auth_service: AuthService = Depends(get_auth_service),
) -> UserAccountRead:
    user = auth_service.get_user_from_session(session_token)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Utilisateur non authentifie.")
    return UserAccountRead(
        id=user.id or 0,
        full_name=user.full_name,
        username=user.username,
        email=user.email,
        telephone=user.telephone,
        is_admin=user.is_admin,
        created_at=user.created_at,
    )


@router.put("/me/profile", response_model=UserAccountRead)
def update_my_profile(
    payload: AuthProfileUpdateRequest,
    session_token: str | None = Cookie(default=None, alias=SESSION_COOKIE_NAME),
    auth_service: AuthService = Depends(get_auth_service),
    notification_service: NotificationService = Depends(get_notification_service),
) -> UserAccountRead:
    user = auth_service.get_user_from_session(session_token)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Utilisateur non authentifie.")

    try:
        updated = auth_service.update_profile(
            user_id=user.id or 0,
            full_name=payload.full_name,
            email=payload.email,
            telephone=payload.telephone,
        )
    except AuthConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except AuthNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    notification_service.update_preferences(
        utilisateur=updated.username,
        email=updated.email,
        telephone=updated.telephone,
        email_enabled=True,
        sms_enabled=bool(updated.telephone),
        weekly_summary_enabled=False,
        is_admin=updated.is_admin,
    )

    return UserAccountRead(
        id=updated.id or 0,
        full_name=updated.full_name,
        username=updated.username,
        email=updated.email,
        telephone=updated.telephone,
        is_admin=updated.is_admin,
        created_at=updated.created_at,
    )


@router.put("/me/password", response_model=UserAccountRead)
def change_my_password(
    payload: AuthPasswordChangeRequest,
    session_token: str | None = Cookie(default=None, alias=SESSION_COOKIE_NAME),
    auth_service: AuthService = Depends(get_auth_service),
) -> UserAccountRead:
    user = auth_service.get_user_from_session(session_token)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Utilisateur non authentifie.")

    try:
        updated = auth_service.change_password(
            user_id=user.id or 0,
            current_password=payload.current_password,
            new_password=payload.new_password,
        )
    except AuthConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except AuthUnauthorizedError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    except AuthNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return UserAccountRead(
        id=updated.id or 0,
        full_name=updated.full_name,
        username=updated.username,
        email=updated.email,
        telephone=updated.telephone,
        is_admin=updated.is_admin,
        created_at=updated.created_at,
    )


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_account(
    payload: AuthAccountDeleteRequest,
    session_token: str | None = Cookie(default=None, alias=SESSION_COOKIE_NAME),
    auth_service: AuthService = Depends(get_auth_service),
) -> Response:
    user = auth_service.get_user_from_session(session_token)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Utilisateur non authentifie.")

    try:
        auth_service.delete_account(user_id=user.id or 0, current_password=payload.current_password)
    except AuthUnauthorizedError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    except AuthNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    _clear_session_cookie(response)
    return response


def get_optional_authenticated_username(
    session_token: str | None = Cookie(default=None, alias=SESSION_COOKIE_NAME),
    auth_service: AuthService = Depends(get_auth_service),
) -> str | None:
    user = auth_service.get_user_from_session(session_token)
    return user.username if user is not None else None
