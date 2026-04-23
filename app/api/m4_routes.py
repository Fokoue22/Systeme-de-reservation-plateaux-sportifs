from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.application import NotificationService
from app.application.m1_services import NotFoundError
from app.domain.notifications import NotificationEventType

from .deps import get_notification_service
from .schemas import (
    NotificationPreferenceRead,
    NotificationPreferenceUpsert,
    NotificationRead,
    ReminderRunResult,
    WeeklySummaryRunResult,
)

router = APIRouter(prefix="/m4", tags=["M4 - Notifications"])


@router.get("/preferences/{utilisateur}", response_model=NotificationPreferenceRead)
def get_notification_preferences(
    utilisateur: str,
    service: NotificationService = Depends(get_notification_service),
) -> NotificationPreferenceRead:
    pref = service.get_or_create_preferences(utilisateur)
    return NotificationPreferenceRead(**pref.__dict__)


@router.put("/preferences/{utilisateur}", response_model=NotificationPreferenceRead)
def upsert_notification_preferences(
    utilisateur: str,
    payload: NotificationPreferenceUpsert,
    service: NotificationService = Depends(get_notification_service),
) -> NotificationPreferenceRead:
    pref = service.update_preferences(
        utilisateur=utilisateur,
        email=payload.email,
        telephone=payload.telephone,
        email_enabled=payload.email_enabled,
        sms_enabled=payload.sms_enabled,
        weekly_summary_enabled=payload.weekly_summary_enabled,
        is_admin=payload.is_admin,
    )
    return NotificationPreferenceRead(**pref.__dict__)


@router.get("/notifications", response_model=list[NotificationRead])
def list_user_notifications(
    utilisateur: str = Query(..., min_length=1),
    limit: int = Query(default=100, ge=1, le=500),
    service: NotificationService = Depends(get_notification_service),
) -> list[NotificationRead]:
    items = service.list_notifications_for_user(utilisateur, limit=limit)
    return [NotificationRead(**item.__dict__) for item in items]


@router.post("/reservations/{reservation_id}/emit", response_model=list[NotificationRead])
def emit_reservation_notification(
    reservation_id: int,
    event_type: NotificationEventType = Query(default=NotificationEventType.RESERVATION_CONFIRMED),
    service: NotificationService = Depends(get_notification_service),
) -> list[NotificationRead]:
    try:
        items = service.notify_reservation_event(event_type=event_type, reservation_id=reservation_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return [NotificationRead(**item.__dict__) for item in items]


@router.post("/reminders/run", response_model=ReminderRunResult)
def run_due_reminders(
    now_utc: str | None = Query(default=None),
    service: NotificationService = Depends(get_notification_service),
) -> ReminderRunResult:
    now = datetime.fromisoformat(now_utc) if now_utc else None
    items = service.process_due_reminders(now_utc=now)
    return ReminderRunResult(processed=len(items))


@router.post("/weekly-summary/run", response_model=WeeklySummaryRunResult)
def run_weekly_summary(
    service: NotificationService = Depends(get_notification_service),
) -> WeeklySummaryRunResult:
    items = service.send_weekly_summary_for_admins()
    return WeeklySummaryRunResult(sent=len(items))
