from __future__ import annotations

from datetime import date
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.application import ConflictError, NotFoundError, ReservationService
from app.domain import Creneau, FlexibleCancellationPolicy, Strict24hCancellationPolicy

from .deps import get_reservation_service
from .schemas import ReservationCreate, ReservationRead, ReservationUpdate

router = APIRouter(prefix="/m2", tags=["M2 - Reservation et conflits"])


class CancelPolicy(str, Enum):
    FLEXIBLE = "FLEXIBLE"
    STRICT_24H = "STRICT_24H"


@router.post("/reservations", response_model=ReservationRead, status_code=status.HTTP_201_CREATED)
def create_reservation(
    payload: ReservationCreate,
    service: ReservationService = Depends(get_reservation_service),
) -> ReservationRead:
    try:
        reservation = service.create_reservation(
            plateau_id=payload.plateau_id,
            utilisateur=payload.utilisateur,
            reservation_date=payload.date_reservation,
            slot=Creneau(debut=payload.creneau.debut, fin=payload.creneau.fin),
            nb_personnes=payload.nb_personnes,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return ReservationRead(
        id=reservation.id or 0,
        plateau_id=reservation.plateau_id,
        utilisateur=reservation.utilisateur,
        date_reservation=reservation.date_reservation,
        creneau={"debut": reservation.creneau.debut, "fin": reservation.creneau.fin},
        statut=reservation.statut,
        nb_personnes=reservation.nb_personnes,
        created_at=reservation.created_at,
    )


@router.put("/reservations/{reservation_id}", response_model=ReservationRead)
def update_reservation(
    reservation_id: int,
    payload: ReservationUpdate,
    service: ReservationService = Depends(get_reservation_service),
) -> ReservationRead:
    try:
        reservation = service.update_reservation(
            reservation_id=reservation_id,
            plateau_id=payload.plateau_id,
            utilisateur=payload.utilisateur,
            reservation_date=payload.date_reservation,
            slot=Creneau(debut=payload.creneau.debut, fin=payload.creneau.fin),
            nb_personnes=payload.nb_personnes,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return ReservationRead(
        id=reservation.id or 0,
        plateau_id=reservation.plateau_id,
        utilisateur=reservation.utilisateur,
        date_reservation=reservation.date_reservation,
        creneau={"debut": reservation.creneau.debut, "fin": reservation.creneau.fin},
        statut=reservation.statut,
        nb_personnes=reservation.nb_personnes,
        created_at=reservation.created_at,
    )


@router.get("/reservations", response_model=list[ReservationRead])
def list_reservations(
    plateau_id: int | None = Query(default=None),
    date_reservation: str | None = Query(default=None),
    service: ReservationService = Depends(get_reservation_service),
) -> list[ReservationRead]:
    parsed_date = None
    if date_reservation is not None:
        parsed_date = date.fromisoformat(date_reservation)

    reservations = service.list_reservations(plateau_id=plateau_id, reservation_date=parsed_date)
    return [
        ReservationRead(
            id=item.id or 0,
            plateau_id=item.plateau_id,
            utilisateur=item.utilisateur,
            date_reservation=item.date_reservation,
            creneau={"debut": item.creneau.debut, "fin": item.creneau.fin},
            statut=item.statut,
            nb_personnes=item.nb_personnes,
            created_at=item.created_at,
        )
        for item in reservations
    ]


@router.post("/reservations/{reservation_id}/cancel", response_model=ReservationRead)
def cancel_reservation(
    reservation_id: int,
    policy: CancelPolicy = Query(default=CancelPolicy.FLEXIBLE),
    service: ReservationService = Depends(get_reservation_service),
) -> ReservationRead:
    cancellation_policy = (
        Strict24hCancellationPolicy() if policy == CancelPolicy.STRICT_24H else FlexibleCancellationPolicy()
    )

    try:
        reservation = service.cancel_reservation(reservation_id, cancellation_policy)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return ReservationRead(
        id=reservation.id or 0,
        plateau_id=reservation.plateau_id,
        utilisateur=reservation.utilisateur,
        date_reservation=reservation.date_reservation,
        creneau={"debut": reservation.creneau.debut, "fin": reservation.creneau.fin},
        statut=reservation.statut,
        nb_personnes=reservation.nb_personnes,
        created_at=reservation.created_at,
    )
