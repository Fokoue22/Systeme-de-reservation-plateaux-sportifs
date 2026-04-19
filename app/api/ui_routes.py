from __future__ import annotations

from fastapi import APIRouter, Cookie, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.application import AuthService

from .deps import get_auth_service
from .m5_auth_routes import SESSION_COOKIE_NAME

router = APIRouter(tags=["UI"])
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
def home(
    request: Request,
    session_token: str | None = Cookie(default=None, alias=SESSION_COOKIE_NAME),
    auth_service: AuthService = Depends(get_auth_service),
):
    user = auth_service.get_user_from_session(session_token)
    if user is not None:
        return RedirectResponse(url="/calendar", status_code=302)
    return templates.TemplateResponse("auth_login.html", {"request": request})


@router.get("/login", response_class=HTMLResponse)
def login_page(
    request: Request,
    session_token: str | None = Cookie(default=None, alias=SESSION_COOKIE_NAME),
    auth_service: AuthService = Depends(get_auth_service),
):
    user = auth_service.get_user_from_session(session_token)
    if user is not None:
        return RedirectResponse(url="/calendar", status_code=302)
    return templates.TemplateResponse("auth_login.html", {"request": request})


@router.get("/register", response_class=HTMLResponse)
def register_page(
    request: Request,
    session_token: str | None = Cookie(default=None, alias=SESSION_COOKIE_NAME),
    auth_service: AuthService = Depends(get_auth_service),
):
    user = auth_service.get_user_from_session(session_token)
    if user is not None:
        return RedirectResponse(url="/calendar", status_code=302)
    return templates.TemplateResponse("auth_register.html", {"request": request})


@router.get("/calendar", response_class=HTMLResponse)
def calendar_page(
    request: Request,
    session_token: str | None = Cookie(default=None, alias=SESSION_COOKIE_NAME),
    auth_service: AuthService = Depends(get_auth_service),
):
    user = auth_service.get_user_from_session(session_token)
    if user is None:
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse(
        "calendar.html",
        {
            "request": request,
            "current_user": user.full_name or user.username,
        },
    )
