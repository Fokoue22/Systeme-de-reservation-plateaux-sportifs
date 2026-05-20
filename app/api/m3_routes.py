from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response

from app.application.m3_calendar_service import CalendarService
from app.infrastructure.pdf_exporter import WeasyPrintExporter

router = APIRouter()


def get_calendar_service() -> CalendarService:
	from app.infrastructure.repositories import SQLiteReservationRepository
	from app.infrastructure.sqlite import SQLiteManager

	return CalendarService(SQLiteReservationRepository(SQLiteManager()))


def get_pdf_exporter() -> WeasyPrintExporter:
	return WeasyPrintExporter()


@router.get("/api/m3/calendar/html")
def calendar_html(
	year: int = Query(...),
	month: int = Query(...),
	plateau_id: Optional[int] = None,
	service: CalendarService = Depends(get_calendar_service),
):
	html = service.generate_month_calendar(year, month, plateau_id)
	return Response(content=html, media_type="text/html")


@router.get("/api/m3/calendar/pdf")
def calendar_pdf(
	year: int = Query(...),
	month: int = Query(...),
	plateau_id: Optional[int] = None,
	service: CalendarService = Depends(get_calendar_service),
	exporter: WeasyPrintExporter = Depends(get_pdf_exporter),
):
	html = service.generate_month_calendar(year, month, plateau_id)
	try:
		pdf_bytes = exporter.export_html_to_pdf(html)
	except ImportError as exc:
		raise HTTPException(status_code=501, detail=str(exc)) from exc
	return Response(content=pdf_bytes, media_type="application/pdf")
