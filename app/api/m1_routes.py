from __future__ import annotations

from datetime import time

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.application import ConflictError, DisponibiliteService, NotFoundError, PlateauService
from app.domain.models import Creneau, WeekDay

from .deps import get_disponibilite_service, get_plateau_service

from .schemas import (
    DisponibiliteCreate,
    DisponibiliteRead,
    PlateauCreate,
    PlateauRead,
    PlateauUpdate,
)

router = APIRouter(prefix="/m1", tags=["M1 - Gestion des plateaux"])

_DEFAULT_WEEK_DAYS = [
    WeekDay.MONDAY,
    WeekDay.TUESDAY,
    WeekDay.WEDNESDAY,
    WeekDay.THURSDAY,
    WeekDay.FRIDAY,
    WeekDay.SATURDAY,
    WeekDay.SUNDAY,
]


@router.post("/plateaux", response_model=PlateauRead, status_code=status.HTTP_201_CREATED)
def create_plateau(
    payload: PlateauCreate,
    service: PlateauService = Depends(get_plateau_service),
    disponibilite_service: DisponibiliteService = Depends(get_disponibilite_service),
) -> PlateauRead:
    plateau = service.create_plateau(
        nom=payload.nom,
        type_sport=payload.type_sport,
        capacite=payload.capacite,
        emplacement=payload.emplacement,
    )

    # Provision default weekly availability at creation time so the plateau is immediately bookable.
    for day in _DEFAULT_WEEK_DAYS:
        try:
            disponibilite_service.add_disponibilite(
                plateau_id=plateau.id or 0,
                jour=day,
                creneau=Creneau(debut=time(8, 0), fin=time(22, 0)),
            )
        except ConflictError:
            # Idempotent behavior if defaults already exist.
            continue

    return PlateauRead(**plateau.__dict__)


@router.get("/plateaux", response_model=list[PlateauRead])
def list_plateaux(service: PlateauService = Depends(get_plateau_service)) -> list[PlateauRead]:
    return [PlateauRead(**p.__dict__) for p in service.list_plateaux()]


@router.get("/plateaux/{plateau_id}", response_model=PlateauRead)
def get_plateau(
    plateau_id: int,
    service: PlateauService = Depends(get_plateau_service),
) -> PlateauRead:
    try:
        plateau = service.get_plateau(plateau_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return PlateauRead(**plateau.__dict__)


@router.put("/plateaux/{plateau_id}", response_model=PlateauRead)
def update_plateau(
    plateau_id: int,
    payload: PlateauUpdate,
    service: PlateauService = Depends(get_plateau_service),
) -> PlateauRead:
    try:
        plateau = service.update_plateau(
            plateau_id=plateau_id,
            nom=payload.nom,
            type_sport=payload.type_sport,
            capacite=payload.capacite,
            emplacement=payload.emplacement,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return PlateauRead(**plateau.__dict__)


@router.delete("/plateaux/{plateau_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_plateau(
    plateau_id: int,
    service: PlateauService = Depends(get_plateau_service),
) -> Response:
    try:
        service.delete_plateau(plateau_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/plateaux/{plateau_id}/disponibilites",
    response_model=DisponibiliteRead,
    status_code=status.HTTP_201_CREATED,
)
def add_disponibilite(
    plateau_id: int,
    payload: DisponibiliteCreate,
    service: DisponibiliteService = Depends(get_disponibilite_service),
) -> DisponibiliteRead:
    try:
        disponibilite = service.add_disponibilite(
            plateau_id=plateau_id,
            jour=payload.jour,
            creneau=Creneau(debut=payload.creneau.debut, fin=payload.creneau.fin),
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return DisponibiliteRead(
        id=disponibilite.id,
        plateau_id=disponibilite.plateau_id,
        jour=disponibilite.jour,
        creneau={
            "debut": disponibilite.creneau.debut,
            "fin": disponibilite.creneau.fin,
        },
    )


@router.get("/plateaux/{plateau_id}/disponibilites", response_model=list[DisponibiliteRead])
def list_disponibilites(
    plateau_id: int,
    service: DisponibiliteService = Depends(get_disponibilite_service),
) -> list[DisponibiliteRead]:
    try:
        items = service.list_disponibilites(plateau_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return [
        DisponibiliteRead(
            id=item.id,
            plateau_id=item.plateau_id,
            jour=item.jour,
            creneau={"debut": item.creneau.debut, "fin": item.creneau.fin},
        )
        for item in items
    ]
