from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["UI"])
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
def home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("calendar.html", {"request": request})


@router.get("/calendar", response_class=HTMLResponse)
def calendar_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("calendar.html", {"request": request})
